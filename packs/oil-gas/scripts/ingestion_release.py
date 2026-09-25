"""Bridge reviewed Broadbridge ingestion state into immutable Foundry releases.

The bridge performs no migrations, infrastructure discovery, model calls, or
credential-file loading.  It requires an explicit Foundry checkout, pack path,
object store, and ``BROADBRIDGE_DATABASE_URL``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
import yaml


PROJECT_ID = "broadbridge-oil-gas"


class BridgeError(ValueError):
    """A DB identity, review, artifact, or explicit configuration is invalid."""


def _absolute_directory(value, label, *, create=False):
    path = Path(value)
    if not path.is_absolute():
        raise BridgeError(f"{label} path must be absolute")
    path = path.resolve()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise BridgeError(f"{label} directory does not exist")
    return path


def load_foundry(foundry):
    """Load only the generic ingestion implementation at an explicit path."""
    root = _absolute_directory(foundry, "foundry")
    contract_path = root / "src" / "ingestion" / "contracts.py"
    if not contract_path.is_file():
        raise BridgeError("foundry path does not contain ingestion contracts")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    contracts = importlib.import_module("src.ingestion.contracts")
    if Path(contracts.__file__).resolve() != contract_path.resolve():
        raise BridgeError("a different Foundry checkout is already imported")
    curate = importlib.import_module("src.ingestion.curate")
    datasets = importlib.import_module("src.ingestion.datasets")
    storage = importlib.import_module("src.ingestion.storage")
    return SimpleNamespace(
        canonical_json=contracts.canonical_json,
        content_hash=contracts.content_hash,
        validate_normalized_document=contracts.validate_normalized_document,
        validate_training_example=contracts.validate_training_example,
        curate_examples=curate.curate_examples,
        prepare_release_candidate=datasets.prepare_release_candidate,
        build_foundry_release=datasets.build_release,
        DatasetError=datasets.DatasetError,
        LocalObjectStore=storage.LocalObjectStore,
        R2ObjectStore=storage.R2ObjectStore,
        StorageError=storage.StorageError,
    )


def _policy(pack):
    pack = _absolute_directory(pack, "pack")
    path = pack / "ingestion.yaml"
    if not path.is_file():
        raise BridgeError("pack does not contain ingestion.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("project_id") != PROJECT_ID:
        raise BridgeError("pack ingestion policy has an unexpected project")
    recipe = value.get("recipe_version")
    if not isinstance(recipe, str) or not recipe:
        raise BridgeError("pack ingestion policy has no recipe version")
    return value


def _database_url(environ=None):
    env = os.environ if environ is None else environ
    value = env.get("BROADBRIDGE_DATABASE_URL", "")
    if not value:
        raise BridgeError("BROADBRIDGE_DATABASE_URL is required")
    return value


def _store(engine, local_root, environ=None):
    if local_root is not None:
        return engine.LocalObjectStore(_absolute_directory(local_root, "local object root", create=True))
    env = os.environ if environ is None else environ
    names = ("R2_ENDPOINT_URL", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    values = {name: env.get(name, "") for name in names}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise BridgeError("explicit R2 configuration is required: " + ", ".join(missing))
    return engine.R2ObjectStore(
        values["R2_ENDPOINT_URL"], values["R2_BUCKET"],
        access_key_id=values["R2_ACCESS_KEY_ID"],
        secret_access_key=values["R2_SECRET_ACCESS_KEY"],
    )


def _json_file(path, label):
    path = Path(path)
    if not path.is_absolute() or not path.is_file():
        raise BridgeError(f"{label} must be an absolute existing file")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise BridgeError(f"{label} is not valid UTF-8 JSON") from None


def _write_json(path, value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path is None:
        print(encoded, end="")
        return
    target = Path(path)
    if not target.is_absolute():
        raise BridgeError("output path must be absolute")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.pending")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(target)


def _candidates(value):
    if isinstance(value, dict) and set(value) == {"examples"}:
        value = value["examples"]
    elif isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or not value:
        raise BridgeError("candidate input must contain at least one example")
    return value


def _receipt(value):
    if not isinstance(value, dict) or set(value) != {"key", "sha256", "size_bytes"}:
        raise BridgeError("job normalized artifact receipt is invalid")
    if (not isinstance(value["key"], str)
            or not isinstance(value["sha256"], str) or len(value["sha256"]) != 64
            or not isinstance(value["size_bytes"], int) or isinstance(value["size_bytes"], bool)
            or value["size_bytes"] < 0):
        raise BridgeError("job normalized artifact receipt is invalid")
    return value


def _read_document(store, engine, receipt):
    receipt = _receipt(receipt)
    try:
        payload = store.get(receipt["key"])
    except Exception as exc:
        raise BridgeError("normalized artifact cannot be read") from exc
    if (len(payload) != receipt["size_bytes"]
            or hashlib.sha256(payload).hexdigest() != receipt["sha256"]):
        raise BridgeError("normalized artifact receipt does not match stored bytes")
    try:
        document = json.loads(payload)
        engine.validate_normalized_document(document)
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeError("normalized artifact does not satisfy the Foundry contract") from exc
    return document


def _job_document(connection, store, engine, identity, recipe_version):
    rows = connection.execute(
        """SELECT job_id,result_json::jsonb AS result
           FROM broadbridge.ingestion_jobs
           WHERE state='succeeded' AND recipe_version=%s
             AND source_json::jsonb->>'source_id'=%s
             AND source_json::jsonb->>'revision_id'=%s
             AND source_json::jsonb->>'content_sha256'=%s
           ORDER BY updated_at DESC,job_id DESC""",
        (recipe_version, identity[0], identity[1], identity[2]),
    ).fetchall()
    if not rows:
        raise BridgeError(f"no verified successful job for source {identity[0]}:{identity[1]}")
    job = rows[0]
    result = job["result"]
    if not isinstance(result, dict) or not isinstance(result.get("normalized"), dict):
        raise BridgeError("successful job has no normalized artifact receipt")
    receipt = _receipt(result["normalized"])
    document = _read_document(store, engine, receipt)
    source = document["source"]
    actual = (source["source_id"], source["revision_id"], source["content_sha256"])
    if actual != identity:
        raise BridgeError("normalized artifact source identity does not match candidate provenance")
    revision = connection.execute(
        """SELECT source_record FROM broadbridge.source_revisions
           WHERE source_id=%s AND revision_id=%s AND content_sha256=%s""", identity,
    ).fetchone()
    if revision is None or revision["source_record"] != source:
        raise BridgeError("normalized artifact source differs from the immutable source revision")
    return job["job_id"], receipt, document


def register_candidates(*, database_url, store, engine, candidates, actor, recipe_version="oil-gas-v1"):
    """Curate and bind pending examples to verified normalized job artifacts."""
    if not isinstance(actor, str) or not actor.strip():
        raise BridgeError("an explicit nonblank actor is required")
    try:
        candidates = [engine.validate_training_example(dict(item)) for item in candidates]
    except (TypeError, ValueError) as exc:
        raise BridgeError("candidate input does not satisfy the Foundry contract") from exc
    if any(item["review"] != {"status": "pending", "reviewer": None,
                               "reviewed_at": None, "reason": item["review"]["reason"]}
           for item in candidates):
        raise BridgeError("register-candidates accepts pending examples only")

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
        connection.execute(
            """LOCK TABLE broadbridge.ingestion_jobs,broadbridge.source_revisions,
                              broadbridge.candidate_records,broadbridge.candidate_artifact_bindings
               IN SHARE ROW EXCLUSIVE MODE"""
        )
        documents = {}
        bindings = {}
        for candidate in candidates:
            for ref in candidate["source_refs"]:
                identity = (ref["source_id"], ref["revision_id"], ref["content_sha256"])
                if identity not in documents:
                    job_id, receipt, document = _job_document(
                        connection, store, engine, identity, recipe_version
                    )
                    documents[identity] = document
                    bindings[identity] = (job_id, receipt, engine.content_hash(document))
        try:
            curated = engine.curate_examples(candidates, list(documents.values()))
        except (TypeError, ValueError) as exc:
            raise BridgeError("candidate curation failed: " + str(exc)) from exc

        registered = []
        for candidate in curated:
            if candidate["review"]["status"] != "pending":
                raise BridgeError("curated candidates must remain pending for technical review")
            candidate_hash = engine.content_hash(candidate)
            saved = connection.execute(
                "SELECT broadbridge.register_candidate(%s,%s,%s) AS value",
                (Jsonb(candidate), candidate_hash, actor.strip()),
            ).fetchone()["value"]
            source_bindings = []
            for ref in candidate["source_refs"]:
                identity = (ref["source_id"], ref["revision_id"], ref["content_sha256"])
                job_id, receipt, document_hash = bindings[identity]
                connection.execute(
                    """INSERT INTO broadbridge.candidate_artifact_bindings
                       (example_id,candidate_hash,source_id,revision_id,content_sha256,job_id,
                        artifact_key,artifact_sha256,artifact_size_bytes,normalized_document_hash,created_by)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT DO NOTHING""",
                    (candidate["example_id"], candidate_hash, *identity, job_id,
                     receipt["key"], receipt["sha256"], receipt["size_bytes"], document_hash,
                     actor.strip()),
                )
                stored = connection.execute(
                    """SELECT job_id,artifact_key,artifact_sha256,artifact_size_bytes,
                              normalized_document_hash
                       FROM broadbridge.candidate_artifact_bindings
                       WHERE example_id=%s AND candidate_hash=%s AND source_id=%s
                         AND revision_id=%s AND content_sha256=%s""",
                    (candidate["example_id"], candidate_hash, *identity),
                ).fetchone()
                expected = {
                    "job_id": job_id, "artifact_key": receipt["key"],
                    "artifact_sha256": receipt["sha256"],
                    "artifact_size_bytes": receipt["size_bytes"],
                    "normalized_document_hash": document_hash,
                }
                if stored != expected:
                    raise BridgeError("candidate artifact binding identity is immutable")
                source_bindings.append({"source_id": identity[0], "revision_id": identity[1],
                                        "content_sha256": identity[2], **expected})
            registered.append({
                "example_id": candidate["example_id"],
                "candidate_hash": candidate_hash,
                "candidate_sequence": saved["candidate_sequence"],
                "family_id": candidate["family_id"],
                "requested_split": candidate["split"],
                "quality_flags": candidate["quality_flags"],
                "source_bindings": source_bindings,
            })
        connection.commit()
    return {"registered": registered}


def _timestamp(value):
    if value is None:
        return None
    return value.isoformat().replace("+00:00", "Z")


def _snapshot(connection, store, engine):
    rows = connection.execute(
        "SELECT * FROM broadbridge.current_candidate_versions ORDER BY example_id"
    ).fetchall()
    if not rows:
        raise BridgeError("no registered candidate versions are available")
    candidates = []
    documents = {}
    for row in rows:
        candidate = dict(row["candidate_record"])
        candidate["review"] = {
            "status": row["status"],
            "reviewer": row["reviewed_by"],
            "reviewed_at": _timestamp(row["reviewed_at"]),
            "reason": row["reason"] or candidate["review"]["reason"],
        }
        bindings = connection.execute(
            """SELECT * FROM broadbridge.candidate_artifact_bindings
               WHERE example_id=%s AND candidate_hash=%s
               ORDER BY source_id,revision_id,content_sha256""",
            (row["example_id"], row["candidate_hash"]),
        ).fetchall()
        expected_identities = {
            (ref["source_id"], ref["revision_id"], ref["content_sha256"])
            for ref in candidate["source_refs"]
        }
        bound_identities = {
            (item["source_id"], item["revision_id"], item["content_sha256"])
            for item in bindings
        }
        if bound_identities != expected_identities:
            raise BridgeError("candidate source provenance does not match artifact bindings")
        for binding in bindings:
            identity = (binding["source_id"], binding["revision_id"], binding["content_sha256"])
            job = connection.execute(
                "SELECT state,result_json::jsonb AS result FROM broadbridge.ingestion_jobs WHERE job_id=%s",
                (binding["job_id"],),
            ).fetchone()
            expected_receipt = {
                "key": binding["artifact_key"], "sha256": binding["artifact_sha256"],
                "size_bytes": binding["artifact_size_bytes"],
            }
            if (job is None or job["state"] != "succeeded" or not isinstance(job["result"], dict)
                    or job["result"].get("normalized") != expected_receipt):
                raise BridgeError("bound job artifact receipt is no longer verified")
            document = _read_document(store, engine, expected_receipt)
            if engine.content_hash(document) != binding["normalized_document_hash"]:
                raise BridgeError("normalized artifact document hash differs from candidate binding")
            permission = connection.execute(
                """SELECT revision.source_record,permission.status,permission.permitted_use,
                          permission.rights_basis,permission.reviewed_by,permission.reviewed_at
                   FROM broadbridge.source_revisions revision
                   JOIN broadbridge.current_source_permissions permission
                     USING (source_id,revision_id,content_sha256)
                   WHERE revision.source_id=%s AND revision.revision_id=%s
                     AND revision.content_sha256=%s""", identity,
            ).fetchone()
            if permission is None or document["source"] != permission["source_record"]:
                raise BridgeError("artifact source differs from immutable source revision")
            if permission["status"] != "approved" or permission["permitted_use"] != "training":
                raise BridgeError("source is revoked or is not currently training-approved")
            overlaid = dict(document)
            overlaid["source"] = dict(document["source"])
            overlaid["source"]["permission"] = {
                "permitted_use": permission["permitted_use"],
                "status": permission["status"],
                "rights_basis": permission["rights_basis"],
                "reviewed_by": permission["reviewed_by"],
                "reviewed_at": _timestamp(permission["reviewed_at"]),
            }
            engine.validate_normalized_document(overlaid)
            previous = documents.get(identity)
            if previous is not None and previous != overlaid:
                raise BridgeError("one source identity resolved to different reviewed documents")
            documents[identity] = overlaid
        candidates.append(candidate)
    document_values = list(documents.values())
    try:
        globally_curated = engine.curate_examples(candidates, document_values)
    except (TypeError, ValueError) as exc:
        raise BridgeError("current candidate set fails global curation: " + str(exc)) from exc
    if globally_curated != sorted(candidates, key=lambda item: item["example_id"]):
        raise BridgeError(
            "current candidates changed under global quality/family curation; "
            "re-register the complete affected candidate family and review its new hashes"
        )
    return globally_curated, document_values


def _prepare(engine, candidates, documents, exclusions, recipe_version):
    try:
        return engine.prepare_release_candidate(
            candidates, documents, pack_name=PROJECT_ID,
            recipe_version=recipe_version, exclusions=exclusions,
        )
    except (TypeError, ValueError) as exc:
        raise BridgeError("candidate release preparation failed: " + str(exc)) from exc


def prepare_release(*, database_url, store, engine, exclusions=None, recipe_version="oil-gas-v1"):
    """Prepare the exact generic candidate from one repeatable DB snapshot."""
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        candidates, documents = _snapshot(connection, store, engine)
        prepared = _prepare(engine, candidates, documents, exclusions or [], recipe_version)
        connection.commit()
    return prepared


def build_release(*, database_url, store, engine, release_root, approval, actor,
                  exclusions=None, recipe_version="oil-gas-v1"):
    """Publish immutable bytes, then reference them while DB review rows are locked."""
    if not isinstance(actor, str) or not actor.strip():
        raise BridgeError("an explicit nonblank actor is required")
    if not isinstance(approval, dict) or approval.get("reviewer") != actor.strip():
        raise BridgeError("release approval reviewer must match the caller actor")
    release_root = _absolute_directory(release_root, "release root", create=True)
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        connection.execute(
            """LOCK TABLE broadbridge.ingestion_jobs,broadbridge.source_revisions,
                              broadbridge.source_rights_reviews,broadbridge.candidate_records,
                              broadbridge.candidate_reviews,broadbridge.candidate_artifact_bindings
               IN SHARE MODE"""
        )
        candidates, documents = _snapshot(connection, store, engine)
        prepared = _prepare(engine, candidates, documents, exclusions or [], recipe_version)
        if approval.get("candidate_content_hash") != prepared["candidate_content_hash"]:
            raise BridgeError("release approval is stale for the current candidate hash")
        try:
            manifest = engine.build_foundry_release(
                candidates, documents, release_root, pack_name=PROJECT_ID,
                recipe_version=recipe_version, approval=approval,
                exclusions=exclusions or [],
            )
        except (TypeError, ValueError) as exc:
            raise BridgeError("immutable release build failed: " + str(exc)) from exc
        connection.execute(
            "SELECT broadbridge.record_dataset_release(%s,%s)",
            (Jsonb(manifest), actor.strip()),
        )
        connection.commit()
    return manifest


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry", required=True, help="Absolute generic Foundry checkout")
    parser.add_argument("--pack", required=True, help="Absolute Broadbridge oil-gas pack")
    parser.add_argument("--local-object-root", help="Absolute local object root; otherwise explicit R2 env is required")
    sub = parser.add_subparsers(dest="command", required=True)
    register = sub.add_parser("register-candidates")
    register.add_argument("--input", required=True, help="Absolute candidate JSON file")
    register.add_argument("--actor", required=True)
    register.add_argument("--output")
    prepare = sub.add_parser("prepare-release")
    prepare.add_argument("--exclusions", help="Absolute generic exclusion acknowledgements JSON")
    prepare.add_argument("--output", required=True)
    build = sub.add_parser("build-release")
    build.add_argument("--approval", required=True, help="Absolute exact-hash approval JSON")
    build.add_argument("--release-root", required=True, help="Absolute immutable release root")
    build.add_argument("--actor", required=True)
    build.add_argument("--exclusions", help="Absolute generic exclusion acknowledgements JSON")
    build.add_argument("--output")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    engine = load_foundry(args.foundry)
    policy = _policy(args.pack)
    store = _store(engine, args.local_object_root)
    database_url = _database_url()
    exclusions = _json_file(args.exclusions, "exclusions") if getattr(args, "exclusions", None) else []
    if args.command == "register-candidates":
        value = register_candidates(
            database_url=database_url, store=store, engine=engine,
            candidates=_candidates(_json_file(args.input, "candidate input")),
            actor=args.actor, recipe_version=policy["recipe_version"],
        )
    elif args.command == "prepare-release":
        value = prepare_release(
            database_url=database_url, store=store, engine=engine,
            exclusions=exclusions, recipe_version=policy["recipe_version"],
        )
    else:
        value = build_release(
            database_url=database_url, store=store, engine=engine,
            release_root=args.release_root, approval=_json_file(args.approval, "approval"),
            actor=args.actor, exclusions=exclusions, recipe_version=policy["recipe_version"],
        )
    _write_json(args.output, value)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BridgeError as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2) from None
