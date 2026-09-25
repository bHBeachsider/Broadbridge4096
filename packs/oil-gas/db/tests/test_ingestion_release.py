"""Executable DB-to-Foundry release bridge tests with synthetic records only."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
import uuid

import psycopg
from psycopg.types.json import Jsonb
import pytest


PACK = Path(__file__).resolve().parents[2]
ROOT = PACK.parents[1]
SCRIPT = PACK / "scripts" / "ingestion_release.py"
FOUNDRY = Path(os.environ.get("FOUNDRY_INGESTION_PATH", ""))


def _bridge_module():
    assert SCRIPT.is_file(), "ingestion release bridge implementation is missing"
    spec = importlib.util.spec_from_file_location("broadbridge_ingestion_release", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_bridge_module_is_present():
    bridge = _bridge_module()
    assert {"register_candidates", "prepare_release", "build_release"} <= set(dir(bridge))


@pytest.fixture(scope="session")
def release_database_url():
    value = os.environ.get("BROADBRIDGE_INGESTION_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("Set BROADBRIDGE_INGESTION_TEST_DATABASE_URL for the owned disposable database")
    target = urlsplit(value)
    if target.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("release tests only accept an owned loopback PostgreSQL database")
    if not target.path.lstrip("/").startswith("broadbridge_test_ingestion_") or target.query:
        raise RuntimeError("release tests require a dedicated broadbridge_test_ingestion_* database")
    return value


@pytest.fixture
def release_database(release_database_url):
    with psycopg.connect(release_database_url, autocommit=True) as connection:
        connection.execute("DROP SCHEMA IF EXISTS broadbridge CASCADE")
        for migration in sorted((PACK / "db/migrations").glob("[0-9][0-9][0-9][0-9]_*.sql")):
            connection.execute(migration.read_text(encoding="utf-8-sig"))
    return release_database_url


@pytest.fixture(scope="session")
def object_store_root(tmp_path_factory):
    # Every committed DB binding in this session must remain readable from the
    # same synthetic object store as later release snapshots.
    return tmp_path_factory.mktemp("object-store")


def _source(prefix: str) -> dict:
    payload_hash = (prefix[-1].lower() if prefix[-1].lower() in "abcdef" else "a") * 64
    return {
        "schema": "foundry.source_revision/1",
        "project_id": "broadbridge-oil-gas",
        "source_id": f"SRC-{prefix}",
        "revision_id": "REV-1",
        "family_id": f"FAMILY-{prefix}",
        "object_key": f"incoming/broadbridge-oil-gas/{prefix}/report.txt",
        "original_filename": "report.txt",
        "content_sha256": payload_hash,
        "size_bytes": 12,
        "media_type": "text/plain",
        "confidentiality": "internal",
        "permission": {
            "permitted_use": "reference_only",
            "status": "pending",
            "rights_basis": "awaiting rights review",
            "reviewed_by": None,
            "reviewed_at": None,
        },
        "relationships": [],
    }


def _document(source: dict) -> dict:
    return {
        "schema": "foundry.normalized_document/1",
        "source": source,
        "parser": {"name": "synthetic", "version": "1", "recipe_version": "oil-gas-v1"},
        "status": "complete",
        "labels": {"practice": ["downstream"], "topic": ["troubleshooting"]},
        "quality_flags": ["synthetic-document-check"],
        "blocks": [{
            "block_id": "block-1", "kind": "text", "text": "Synthetic pressure evidence.",
            "location": {"page": 1}, "asset_key": None, "measurements": [],
            "quality_flags": ["synthetic-block-check"],
        }],
        "attachments": [],
        "classification": {"method": "synthetic", "confidence": 1.0, "review_required": True},
    }


def _candidate(source: dict, suffix: str = "") -> dict:
    return {
        "schema": "foundry.training_example/1",
        "example_id": f"EX-{source['source_id']}{suffix}",
        "family_id": source["family_id"],
        "split": "train",
        "source_refs": [{
            "source_id": source["source_id"], "revision_id": source["revision_id"],
            "content_sha256": source["content_sha256"], "block_ids": ["block-1"],
        }],
        "messages": [
            {"role": "user", "content": f"What does the synthetic evidence show?{suffix}"},
            {"role": "assistant", "content": "It reports synthetic pressure evidence."},
        ],
        "review": {"status": "pending", "reviewer": None, "reviewed_at": None,
                   "reason": "technical review required"},
        "task_type": "grounded_explanation",
        "quality_flags": [],
    }


def _setup(release_database, tmp_path, *, suffix=None, approve_rights=True):
    if not FOUNDRY.is_absolute() or not (FOUNDRY / "src/ingestion/datasets.py").is_file():
        pytest.skip("Set FOUNDRY_INGESTION_PATH to the pinned local Foundry checkout")
    suffix = suffix or uuid.uuid4().hex[:8].upper()
    source = _source(suffix)
    document = _document(source)
    bridge = _bridge_module()
    engine = bridge.load_foundry(FOUNDRY)
    store = engine.LocalObjectStore(tmp_path / "objects")
    payload = engine.canonical_json(document)
    receipt = store.put_immutable(
        f"artifacts/broadbridge-oil-gas/JOB-{suffix}/lease-1/normalized.json", payload
    )
    registry_ref = f"registry/broadbridge-oil-gas/{suffix.lower()}.json"
    with psycopg.connect(release_database) as connection:
        connection.execute(
            "SELECT broadbridge.register_source_revision(%s,%s,%s)",
            (Jsonb(source), registry_ref, "intake@example.com"),
        )
        connection.execute(
            """INSERT INTO broadbridge.ingestion_jobs
               (job_id,source_json,recipe_version,state,attempts,max_attempts,backoff_seconds,
                max_backoff_seconds,available_at,lease_token,lease_expires_at,worker_id,
                result_json,error_code,created_at,updated_at)
               VALUES (%s,%s,%s,'succeeded',1,3,1,30,1,NULL,NULL,'worker-1',%s,NULL,1,2)""",
            (f"JOB-{suffix}", json.dumps(source), "oil-gas-v1",
             json.dumps({"normalized": receipt, "document_status": "complete", "attachments": []})),
        )
        if approve_rights:
            connection.execute(
                "SELECT broadbridge.review_source_rights(%s,%s,%s,'approved','training',%s,NULL,%s)",
                (source["source_id"], source["revision_id"], source["content_sha256"],
                 "synthetic owner grant", "rights@example.com"),
            )
        connection.commit()
    return bridge, engine, store, source


def _register_and_approve(bridge, engine, store, source, database_url, candidate=None):
    candidate = candidate or _candidate(source)
    result = bridge.register_candidates(
        database_url=database_url, store=store, engine=engine,
        candidates=[candidate], actor="builder@example.com",
    )
    registered = result["registered"][0]
    assert any(flag.endswith("synthetic-document-check") for flag in registered["quality_flags"])
    with psycopg.connect(database_url) as connection:
        review = connection.execute(
            "SELECT broadbridge.review_candidate(%s,%s,'approved',%s,NULL,%s)",
            (registered["example_id"], registered["candidate_hash"],
             "synthetic technical review", "reviewer@example.com"),
        ).fetchone()[0]
        connection.commit()
    return registered, review


def _approval(prepared):
    return {
        "status": "approved",
        "reviewer": "release@example.com",
        "reviewed_at": "2026-09-25T15:00:00Z",
        "candidate_content_hash": prepared["candidate_content_hash"],
    }


def test_ui_pending_records_become_a_positive_hash_bound_release(release_database, object_store_root, tmp_path):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    registered, review = _register_and_approve(bridge, engine, store, source, release_database)
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=[]
    )
    assert prepared["examples"] == [{
        "example_id": registered["example_id"], "family_id": source["family_id"], "split": "train"
    }]
    manifest = bridge.build_release(
        database_url=release_database, store=store, engine=engine,
        release_root=tmp_path / "releases", approval=_approval(prepared),
        actor="release@example.com", exclusions=[],
    )
    assert manifest["release_id"] == prepared["candidate_content_hash"]
    assert manifest["review"]["candidate_content_hash"] == manifest["release_id"]
    with psycopg.connect(release_database) as connection:
        row = connection.execute(
            "SELECT release_id FROM broadbridge.dataset_releases WHERE release_id=%s",
            (manifest["release_id"],),
        ).fetchone()
    assert row == (manifest["release_id"],)
    assert review["status"] == "approved"


def test_excluded_holdout_still_forces_strict_family_split(release_database, object_store_root):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    main = _candidate(source, "-MAIN")
    holdout = _candidate(source, "-HOLDOUT")
    holdout["split"] = "test"
    registered = bridge.register_candidates(
        database_url=release_database, store=store, engine=engine,
        candidates=[main, holdout], actor="builder@example.com",
    )["registered"]
    assert {item["requested_split"] for item in registered} == {"test"}
    by_id = {item["example_id"]: item for item in registered}
    with psycopg.connect(release_database) as connection:
        connection.execute(
            "SELECT broadbridge.review_candidate(%s,%s,'approved',%s,NULL,%s)",
            (main["example_id"], by_id[main["example_id"]]["candidate_hash"],
             "synthetic technical review", "reviewer@example.com"),
        )
        connection.execute(
            "SELECT broadbridge.review_candidate(%s,%s,'rejected',%s,NULL,%s)",
            (holdout["example_id"], by_id[holdout["example_id"]]["candidate_hash"],
             "synthetic holdout exclusion", "reviewer@example.com"),
        )
        connection.commit()
    exclusions = [{
        "example_id": holdout["example_id"],
        "reason": "synthetic rejected holdout remains in family closure",
        "acknowledged_by": "release@example.com",
        "acknowledged_at": "2026-09-25T14:00:00Z",
    }]
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=exclusions
    )
    assert prepared["examples"] == [{
        "example_id": main["example_id"], "family_id": source["family_id"], "split": "test"
    }]
    disposition = {item["example_id"]: item for item in prepared["dispositions"]}
    assert disposition[holdout["example_id"]]["status"] == "excluded"


def test_rights_revoked_after_prepare_blocks_build(release_database, object_store_root, tmp_path):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    _register_and_approve(bridge, engine, store, source, release_database)
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=[]
    )
    with psycopg.connect(release_database) as connection:
        current = connection.execute(
            "SELECT review_id FROM broadbridge.current_source_permissions WHERE source_id=%s",
            (source["source_id"],),
        ).fetchone()[0]
        connection.execute(
            "SELECT broadbridge.review_source_rights(%s,%s,%s,'revoked','reference_only',%s,%s,%s)",
            (source["source_id"], source["revision_id"], source["content_sha256"],
             "synthetic withdrawal", current, "rights@example.com"),
        )
        connection.commit()
    with pytest.raises(bridge.BridgeError, match="acknowledged exclusion"):
        bridge.build_release(
            database_url=release_database, store=store, engine=engine,
            release_root=tmp_path / "releases", approval=_approval(prepared),
            actor="release@example.com", exclusions=[],
        )


def test_changed_candidate_hash_after_review_blocks_old_approval(release_database, object_store_root, tmp_path):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    original, _ = _register_and_approve(bridge, engine, store, source, release_database)
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=[]
    )
    changed = _candidate(source)
    changed["messages"][0]["content"] += " Changed after review."
    changed_result = bridge.register_candidates(
        database_url=release_database, store=store, engine=engine,
        candidates=[changed], actor="builder@example.com",
    )["registered"][0]
    assert changed_result["candidate_hash"] != original["candidate_hash"]
    with pytest.raises(bridge.BridgeError, match="candidate|approval"):
        bridge.build_release(
            database_url=release_database, store=store, engine=engine,
            release_root=tmp_path / "releases", approval=_approval(prepared),
            actor="release@example.com", exclusions=[],
        )


def test_bound_normalized_artifact_tamper_blocks_release(release_database, object_store_root, tmp_path):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    _register_and_approve(bridge, engine, store, source, release_database)
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=[]
    )
    with psycopg.connect(release_database) as connection:
        key = connection.execute(
            "SELECT artifact_key FROM broadbridge.candidate_artifact_bindings WHERE source_id=%s",
            (source["source_id"],),
        ).fetchone()[0]
    store._path(key).write_bytes(b"tampered synthetic bytes")
    with pytest.raises(bridge.BridgeError, match="artifact"):
        bridge.build_release(
            database_url=release_database, store=store, engine=engine,
            release_root=tmp_path / "releases", approval=_approval(prepared),
            actor="release@example.com", exclusions=[],
        )


@pytest.mark.parametrize("holdout", ["test", "val"])
def test_replacement_and_new_family_members_keep_historical_holdout(
        release_database, object_store_root, holdout):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    original = _candidate(source)
    original["split"] = holdout
    registered, _ = _register_and_approve(
        bridge, engine, store, source, release_database, original
    )
    replacement = _candidate(source)
    replacement["messages"][0]["content"] += " Revised wording."
    updated, _ = _register_and_approve(
        bridge, engine, store, source, release_database, replacement
    )
    assert updated["candidate_hash"] != registered["candidate_hash"]
    assert updated["requested_split"] == holdout
    sibling, _ = _register_and_approve(
        bridge, engine, store, source, release_database, _candidate(source, "-NEW")
    )
    assert sibling["requested_split"] == holdout
    prepared = bridge.prepare_release(database_url=release_database, store=store, engine=engine)
    assert {item["split"] for item in prepared["examples"]} == {holdout}


@pytest.mark.parametrize("permission_state", ["revoked", "pending", "reference_only"])
def test_ineligible_source_can_be_acknowledged_without_blocking_unrelated_release(
        release_database, object_store_root, tmp_path, permission_state):
    bridge, engine, store, excluded_source = _setup(
        release_database, object_store_root, suffix="EXCLUDED", approve_rights=False
    )
    _, _, _, kept_source = _setup(release_database, object_store_root, suffix="KEPT")
    excluded = _candidate(excluded_source)
    excluded["messages"] = [
        {"role": "user", "content": "Which evidence is ineligible for release?"},
        {"role": "assistant", "content": "The excluded synthetic document."},
    ]
    _register_and_approve(bridge, engine, store, excluded_source, release_database, excluded)
    kept, _ = _register_and_approve(bridge, engine, store, kept_source, release_database)
    if permission_state != "pending":
        with psycopg.connect(release_database) as connection:
            connection.execute(
                "SELECT broadbridge.review_source_rights(%s,%s,%s,%s,'reference_only',%s,NULL,%s)",
                (excluded_source["source_id"], excluded_source["revision_id"],
                 excluded_source["content_sha256"],
                 "revoked" if permission_state == "revoked" else "approved",
                 "synthetic nontraining permission", "rights@example.com"),
            )
    with pytest.raises(bridge.BridgeError):
        bridge.prepare_release(database_url=release_database, store=store, engine=engine)
    exclusions = [{
        "example_id": excluded["example_id"], "reason": "Acknowledged nontraining source",
        "acknowledged_by": "release@example.com", "acknowledged_at": "2026-09-25T14:00:00Z",
    }]
    prepared = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=exclusions
    )
    assert [row["example_id"] for row in prepared["examples"]] == [kept["example_id"]]
    disposition = next(row for row in prepared["dispositions"] if row["example_id"] == excluded["example_id"])
    assert disposition["status"] == "excluded"
    assert "source_not_training_approved" in disposition["reasons"]
    manifest = bridge.build_release(
        database_url=release_database, store=store, engine=engine, release_root=tmp_path / "release",
        approval=_approval(prepared), actor="release@example.com", exclusions=exclusions,
    )
    assert manifest["release_id"] == prepared["candidate_content_hash"]


def test_snapshot_refuses_legacy_hash_that_dropped_historical_holdout(
        release_database, object_store_root):
    bridge, engine, store, source = _setup(release_database, object_store_root)
    held = _candidate(source)
    held["split"] = "test"
    registered, _ = _register_and_approve(bridge, engine, store, source, release_database, held)
    # Simulate a previously stored version that bypassed the Python bridge. It
    # keeps real artifact bindings and valid technical approval, so only the
    # historical split check prevents the contamination.
    with psycopg.connect(release_database) as connection:
        candidate = connection.execute(
            "SELECT candidate_record FROM broadbridge.candidate_records WHERE candidate_hash=%s",
            (registered["candidate_hash"],),
        ).fetchone()[0]
        candidate["split"] = "train"
        legacy_hash = engine.content_hash(candidate)
        connection.execute("SELECT broadbridge.register_candidate(%s,%s,%s)",
                           (Jsonb(candidate), legacy_hash, "legacy@example.com"))
        connection.execute(
            """INSERT INTO broadbridge.candidate_artifact_bindings
               (example_id,candidate_hash,source_id,revision_id,content_sha256,job_id,
                artifact_key,artifact_sha256,artifact_size_bytes,normalized_document_hash,created_by)
               SELECT example_id,%s,source_id,revision_id,content_sha256,job_id,
                      artifact_key,artifact_sha256,artifact_size_bytes,normalized_document_hash,created_by
               FROM broadbridge.candidate_artifact_bindings WHERE candidate_hash=%s""",
            (legacy_hash, registered["candidate_hash"]),
        )
        connection.execute("SELECT broadbridge.review_candidate(%s,%s,'approved',%s,NULL,%s)",
                           (candidate["example_id"], legacy_hash, "legacy technical approval", "reviewer@example.com"))
    with pytest.raises(bridge.BridgeError, match="re-register"):
        bridge.prepare_release(database_url=release_database, store=store, engine=engine)


def test_revocation_exclusion_requires_a_new_release_hash_approval(
        release_database, object_store_root, tmp_path):
    bridge, engine, store, source = _setup(release_database, object_store_root, suffix="BEFORE")
    _, _, _, kept_source = _setup(release_database, object_store_root, suffix="OTHER")
    candidate = _candidate(source)
    candidate["messages"] = [{"role": "user", "content": "Describe valve inspection."},
                             {"role": "assistant", "content": "Synthetic valve was open."}]
    _register_and_approve(bridge, engine, store, source, release_database, candidate)
    _register_and_approve(bridge, engine, store, kept_source, release_database)
    before = bridge.prepare_release(database_url=release_database, store=store, engine=engine)
    with psycopg.connect(release_database) as connection:
        current = connection.execute(
            "SELECT review_id FROM broadbridge.current_source_permissions WHERE source_id=%s",
            (source["source_id"],),
        ).fetchone()[0]
        connection.execute(
            "SELECT broadbridge.review_source_rights(%s,%s,%s,'revoked','reference_only',%s,%s,%s)",
            (source["source_id"], source["revision_id"], source["content_sha256"],
             "synthetic withdrawal", current, "rights@example.com"),
        )
    exclusions = [{"example_id": candidate["example_id"], "reason": "withdrawn source",
                   "acknowledged_by": "release@example.com", "acknowledged_at": "2026-09-25T14:00:00Z"}]
    after = bridge.prepare_release(
        database_url=release_database, store=store, engine=engine, exclusions=exclusions
    )
    assert after["candidate_content_hash"] != before["candidate_content_hash"]
    with pytest.raises(bridge.BridgeError, match="approval is stale"):
        bridge.build_release(
            database_url=release_database, store=store, engine=engine, release_root=tmp_path / "release",
            approval=_approval(before), actor="release@example.com", exclusions=exclusions,
        )
