"""Broadbridge ingestion binding and additive PostgreSQL contract tests."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

import psycopg
from psycopg.types.json import Jsonb
import pytest


PACK = Path(__file__).resolve().parents[2]
ROOT = PACK.parents[1]
SCRIPTS = PACK / "scripts"
FIXTURES = PACK / "tests" / "fixtures"
sys.path.insert(0, str(SCRIPTS))


def _adapter():
    path = SCRIPTS / "ingestion_adapter.py"
    assert path.is_file(), "ingestion adapter implementation is missing"
    spec = importlib.util.spec_from_file_location("broadbridge_ingestion_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_case_adapter_requires_absolute_foundry_and_preserves_family_holdout():
    adapter = _adapter()
    with pytest.raises(ValueError, match="absolute"):
        adapter.load_foundry(Path("relative-foundry"))

    foundry = Path(os.environ.get("FOUNDRY_INGESTION_PATH", ""))
    if not foundry.is_absolute() or not (foundry / "src/ingestion/contracts.py").is_file():
        pytest.skip("Set FOUNDRY_INGESTION_PATH to the pinned local Foundry checkout")

    signed = _fixture("SYN-TRAIN-001.json")
    signed["questions"][0]["hard_fail_criteria"] = "SCORING-ONLY-MARKER"
    signed["questions"][0]["tolerance"] = "TOLERANCE-ONLY-MARKER"
    held = copy.deepcopy(signed)
    held.update(case_id="SYN-HOLDOUT", status="draft")
    held["family_id"] = signed["family_id"]
    held["identity"]["permitted_use"] = "reference_only"
    held["questions"][0].update(question_id="SYN-HOLDOUT-Q1", split="locked_test")
    held["reviewer_signoff"] = {"signed": False, "name": "", "date": ""}
    export = {
        "exported_at": "2026-09-25T12:00:00Z",
        "workflow": {"schema": "broadbridge.workflow/1", "answers": {}, "updated_at": ""},
        "cases": [signed, held],
    }

    result = adapter.adapt_case_export(export, foundry=foundry, pack=PACK)

    assert len(result["documents"]) == 1
    assert len(result["examples"]) == 1
    example = result["examples"][0]
    assert example["split"] == "test"
    assert example["messages"][-1] == {
        "role": "assistant",
        "content": signed["questions"][0]["reference_answer"],
    }
    user_text = example["messages"][-2]["content"]
    assert signed["decision_time"]["b1_trigger"] in user_text
    assert signed["hindsight"]["b8_turning_point"] not in user_text
    assert signed["identity"]["unit_service"] in user_text
    assert "SCORING-ONLY-MARKER" not in user_text
    assert "TOLERANCE-ONLY-MARKER" not in user_text
    payload = json.loads(user_text)
    assert set(payload["decision_context"]) == {"decision_time", "unit_service"}
    assert result["dispositions"] == [
        {
            "case_id": "SYN-HOLDOUT",
            "status": "excluded",
            "reason": "status=draft; permitted_use=reference_only; excluded from training",
        },
        {"case_id": "SYN-TRAIN-001", "status": "adapted", "example_count": 1},
    ]


@pytest.mark.parametrize("label", ["not public", "confidential; public excerpt", "public only after permission"])
def test_freeform_case_confidentiality_never_downgrades_by_substring(label):
    assert _adapter()._case_confidentiality(label) == "confidential"


def test_registered_source_adapter_keeps_case_optional_and_never_invents_review():
    adapter = _adapter()
    foundry = Path(os.environ.get("FOUNDRY_INGESTION_PATH", ""))
    if not foundry.is_absolute() or not (foundry / "src/ingestion/contracts.py").is_file():
        pytest.skip("Set FOUNDRY_INGESTION_PATH to the pinned local Foundry checkout")
    revision = {
        "schema": "foundry.source_revision/1",
        "project_id": "broadbridge-oil-gas",
        "source_id": "SRC-1",
        "revision_id": "REV-1",
        "family_id": "FAMILY-1",
        "object_key": "raw/broadbridge-oil-gas/SRC-1/REV-1/report.txt",
        "original_filename": "report.txt",
        "content_sha256": "a" * 64,
        "size_bytes": 14,
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
    source = {"source_id": "SRC-1", "title": "Independent report"}
    evidence = [{"evidence_id": "EV-1", "source_id": "SRC-1", "text": "Observed vibration", "page": 3}]

    document = adapter.adapt_registered_source(
        source, evidence, revision=revision, foundry=foundry
    )

    assert document["source"]["permission"]["status"] == "pending"
    assert document["blocks"][0]["location"] == {"page": 3}
    assert "case_id" not in document["blocks"][0]
    assert document["classification"]["review_required"] is True


def test_external_pack_policy_loads_single_taxonomy_source():
    adapter = _adapter()
    foundry = Path(os.environ.get("FOUNDRY_INGESTION_PATH", ""))
    if not foundry.is_absolute() or not (foundry / "src/ingestion/contracts.py").is_file():
        pytest.skip("Set FOUNDRY_INGESTION_PATH to the pinned local Foundry checkout")

    policy = adapter.load_policy(PACK, foundry=foundry)

    assert policy["project_id"] == "broadbridge-oil-gas"
    assert policy["taxonomy"]["practice"]["downstream"]
    assert policy["admission_policy"]["classification_grants_rights"] is False
    assert policy["review"]["rights_role"] != policy["review"]["technical_role"]
    assert policy["database"] == {
        "url_env": "BROADBRIDGE_DATABASE_URL",
        "schema": "broadbridge",
        "generic_environment": {
            "INGESTION_DB_ENV": "BROADBRIDGE_DATABASE_URL",
            "INGESTION_DB_SCHEMA": "broadbridge",
        },
        "migration_url_env": "DATABASE_URL_UNPOOLED",
        "constructors_run_ddl": False,
    }


@pytest.fixture(scope="session")
def ingestion_database_url():
    value = os.environ.get("BROADBRIDGE_INGESTION_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("Set BROADBRIDGE_INGESTION_TEST_DATABASE_URL for the owned disposable database")
    target = urlsplit(value)
    if target.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("ingestion tests only accept an owned loopback PostgreSQL database")
    if not target.path.lstrip("/").startswith("broadbridge_test_ingestion_") or target.query:
        raise RuntimeError("ingestion tests require a dedicated broadbridge_test_ingestion_* database")
    return value


@pytest.fixture(scope="session")
def migrated_database(ingestion_database_url):
    migrations = sorted((PACK / "db/migrations").glob("[0-9][0-9][0-9][0-9]_*.sql"))
    assert migrations[-1].name == "0005_ingestion.sql"
    with psycopg.connect(ingestion_database_url, autocommit=True) as connection:
        for migration in migrations:
            connection.execute(migration.read_text(encoding="utf-8-sig"))
    return ingestion_database_url


@pytest.fixture
def conn(migrated_database):
    with psycopg.connect(migrated_database, autocommit=False) as connection:
        yield connection
        connection.rollback()


def _source_revision():
    return {
        "schema": "foundry.source_revision/1",
        "project_id": "broadbridge-oil-gas",
        "source_id": "SRC-DB-1",
        "revision_id": "REV-1",
        "family_id": "FAMILY-DB-1",
        "object_key": "raw/broadbridge-oil-gas/SRC-DB-1/REV-1/report.txt",
        "original_filename": "report.txt",
        "content_sha256": "b" * 64,
        "size_bytes": 15,
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


def test_migration_has_exact_generic_job_columns_and_additive_tables(conn):
    columns = conn.execute(
        """SELECT column_name FROM information_schema.columns
           WHERE table_schema='broadbridge' AND table_name='ingestion_jobs'
           ORDER BY ordinal_position"""
    ).fetchall()
    assert [row[0] for row in columns] == [
        "job_id", "source_json", "recipe_version", "state", "attempts",
        "max_attempts", "backoff_seconds", "max_backoff_seconds", "available_at",
        "lease_token", "lease_expires_at", "worker_id", "result_json", "error_code",
        "created_at", "updated_at",
    ]
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='broadbridge'"
        )
    }
    assert {
        "source_revisions", "source_rights_reviews", "candidate_records",
        "candidate_reviews", "candidate_artifact_bindings", "dataset_releases", "model_runs",
    } <= tables


def test_source_revision_is_immutable_and_rights_review_is_stale_safe(conn):
    source = _source_revision()
    conn.execute(
        "INSERT INTO broadbridge.sources(source_id,record,updated_by) VALUES (%s,%s,%s)",
        (source["source_id"], Jsonb({"source_id": source["source_id"]}), "intake@example.com"),
    )
    saved = conn.execute(
        "SELECT broadbridge.register_source_revision(%s,%s,%s)",
        (Jsonb(source), source["source_id"], "intake@example.com"),
    ).fetchone()[0]
    assert saved["permission_status"] == "pending"
    assert saved["source_ref"] == source["source_id"]
    with pytest.raises(psycopg.errors.CheckViolation, match="immutable"):
        with conn.transaction():
            conn.execute("UPDATE broadbridge.source_revisions SET registry_ref='other'")

    review = conn.execute(
        "SELECT broadbridge.review_source_rights(%s,%s,%s,%s,%s,%s,%s,%s)",
        (source["source_id"], source["revision_id"], source["content_sha256"],
         "approved", "training", "documented owner grant", None, "rights@example.com"),
    ).fetchone()[0]
    assert review["review_id"] > 0
    current = conn.execute(
        "SELECT status,permitted_use,reviewed_by FROM broadbridge.current_source_permissions"
    ).fetchone()
    assert current == ("approved", "training", "rights@example.com")
    with pytest.raises(psycopg.errors.SerializationFailure, match="stale"):
        with conn.transaction():
            conn.execute(
                "SELECT broadbridge.review_source_rights(%s,%s,%s,%s,%s,%s,%s,%s)",
                (source["source_id"], source["revision_id"], source["content_sha256"],
                 "revoked", "reference_only", "withdrawn", None, "rights@example.com"),
            )
    revoked = conn.execute(
        "SELECT broadbridge.review_source_rights(%s,%s,%s,%s,%s,%s,%s,%s)",
        (source["source_id"], source["revision_id"], source["content_sha256"],
         "revoked", "reference_only", "withdrawn grant", review["review_id"], "rights@example.com"),
    ).fetchone()[0]
    assert conn.execute(
        "SELECT status,permitted_use FROM broadbridge.current_source_permissions"
    ).fetchone() == ("revoked", "reference_only")
    replayed = conn.execute(
        "SELECT broadbridge.register_source_revision(%s,%s,%s)",
        (Jsonb(source), source["source_id"], "intake@example.com"),
    ).fetchone()[0]
    assert replayed["current_rights_review_id"] == revoked["review_id"]


def test_candidate_dataset_and_model_records_are_hash_bound_and_stale_safe(conn):
    candidate_hash = "c" * 64
    candidate = {
        "schema": "foundry.training_example/1",
        "example_id": "EX-1",
        "family_id": "FAMILY-1",
        "split": "train",
        "source_refs": [{
            "source_id": "SRC-1", "revision_id": "REV-1",
            "content_sha256": "a" * 64, "block_ids": ["block-1"],
        }],
        "messages": [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}],
        "review": {"status": "pending", "reviewer": None, "reviewed_at": None, "reason": "review required"},
        "task_type": "troubleshooting",
        "quality_flags": [],
    }
    conn.execute(
        "SELECT broadbridge.register_candidate(%s,%s,%s)",
        (Jsonb(candidate), candidate_hash, "builder@example.com"),
    )
    review = conn.execute(
        "SELECT broadbridge.review_candidate(%s,%s,%s,%s,%s,%s)",
        (candidate["example_id"], candidate_hash, "approved", "supported", None, "bill@example.com"),
    ).fetchone()[0]
    assert review["reviewed_by"] == "bill@example.com"
    with pytest.raises(psycopg.errors.SerializationFailure, match="stale"):
        with conn.transaction():
            conn.execute(
                "SELECT broadbridge.review_candidate(%s,%s,%s,%s,%s,%s)",
                (candidate["example_id"], candidate_hash, "rejected", "changed", None, "bill@example.com"),
            )

    release_id = "d" * 64
    manifest = {
        "schema": "foundry.dataset_release/1",
        "release_id": release_id,
        "pack_name": "broadbridge-oil-gas",
        "recipe_version": "oil-gas-v1",
        "sources": [], "examples": [], "artifacts": {}, "dispositions": [], "exclusions": [],
        "review": {
            "status": "approved", "reviewer": "release@example.com",
            "reviewed_at": "2026-09-25T12:00:00Z", "candidate_content_hash": release_id,
        },
        "created_at": "2026-09-25T12:00:00Z",
    }
    stored = conn.execute(
        "SELECT broadbridge.record_dataset_release(%s,%s)",
        (Jsonb(manifest), "release@example.com"),
    ).fetchone()[0]
    assert stored["release_id"] == release_id
    untrusted = copy.deepcopy(manifest)
    untrusted["release_id"] = "f" * 64
    untrusted["review"]["candidate_content_hash"] = "f" * 64
    untrusted["review"]["reviewer"] = "claimed@example.com"
    with pytest.raises(psycopg.errors.CheckViolation, match="actor"):
        with conn.transaction():
            conn.execute(
                "SELECT broadbridge.record_dataset_release(%s,%s)",
                (Jsonb(untrusted), "caller@example.com"),
            )
    manifest["review"]["candidate_content_hash"] = "e" * 64
    with pytest.raises(psycopg.errors.CheckViolation, match="hash"):
        with conn.transaction():
            conn.execute(
                "SELECT broadbridge.record_dataset_release(%s,%s)",
                (Jsonb(manifest), "release@example.com"),
            )

    run = {
        "schema": "foundry.model_run/1", "run_id": "RUN-1", "release_id": release_id,
        "status": "queued", "dataset_release_hash": release_id,
    }
    recorded = conn.execute(
        "SELECT broadbridge.record_model_run(%s,%s,%s)",
        (Jsonb(run), None, "trainer@example.com"),
    ).fetchone()[0]
    assert recorded["run_id"] == "RUN-1"
    assert recorded["revision"] == 1
    failed = {**run, "status": "failed", "error_code": "TRAINER_EXITED"}
    updated = conn.execute(
        "SELECT broadbridge.record_model_run(%s,%s,%s)",
        (Jsonb(failed), 1, "trainer@example.com"),
    ).fetchone()[0]
    assert updated["revision"] == 2
    assert conn.execute(
        "SELECT state FROM broadbridge.current_model_runs WHERE run_id='RUN-1'"
    ).fetchone()[0] == "failed"
    assert conn.execute("SELECT count(*) FROM broadbridge.runs").fetchone()[0] == 0
