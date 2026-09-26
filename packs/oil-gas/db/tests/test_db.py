"""Real PostgreSQL contract tests; require an empty disposable database."""
import copy
from concurrent.futures import ThreadPoolExecutor
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit

import psycopg
from psycopg.types.json import Jsonb
import pytest

PACK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACK / "scripts"))


def test_database_module_is_present():
    assert (PACK / "scripts/db.py").is_file(), "database helper implementation is missing"


@pytest.fixture(scope="session")
def database():
    assert (PACK / "scripts/db.py").is_file(), "database helper implementation is missing"
    module = importlib.import_module("db")
    value = os.environ.get("BROADBRIDGE_DATABASE_URL", "")
    if not value:
        pytest.skip("Set BROADBRIDGE_DATABASE_URL or use db/test.ps1 for disposable PostgreSQL")
    target = urlsplit(value)
    local = target.hostname in ("127.0.0.1", "localhost", "::1")
    if local:
        if not target.path.lstrip("/").startswith("broadbridge_test") or target.query:
            raise RuntimeError("Local tests require a broadbridge_test database without connection overrides")
    else:
        verified_host = os.environ.get("BROADBRIDGE_TEST_DATABASE_HOST", "")
        if not verified_host or target.hostname != verified_host:
            raise RuntimeError("Remote tests require an operator-verified disposable dev endpoint in BROADBRIDGE_TEST_DATABASE_HOST")
        if set(parse_qs(target.query)) - {"sslmode", "channel_binding", "connect_timeout"}:
            raise RuntimeError("Remote tests refuse connection-target overrides")
    with module.connection() as conn:
        if any(module.status(conn)["counts"].values()):
            raise RuntimeError("Database tests require empty capture tables; use a fresh disposable branch")
        module.migrate(conn)
    return module


@pytest.fixture
def conn(database):
    with database.connection() as value:
        yield value
        value.rollback()


@pytest.fixture
def case():
    return json.loads((PACK / "tests/fixtures/SYN-TRAIN-001.json").read_text(encoding="utf-8"))


def test_migrations_idempotent_vector_and_checksum(database, conn):
    before = database.status(conn)
    database.migrate(conn)
    assert database.status(conn) == before
    assert before["version"] == sorted(path.name for path in database.MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql"))[-1]
    assert conn.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()
    assert set(before["counts"]) >= {"cases", "questions", "sources", "evidence", "runs", "scorecards", "review_log", "workflow"}
    conn.execute("UPDATE broadbridge.schema_migrations SET checksum=%s WHERE version=%s", ("0" * 64, "0001_init.sql"))
    with pytest.raises(RuntimeError, match="checksum"):
        database.migrate(conn)


def test_case_json_roundtrip_idempotence_and_actor(database, conn, case):
    saved = database.upsert_case(conn, case, "first@example.com")
    assert saved["record"] == case
    assert database.upsert_case(conn, case, "first@example.com") == saved
    assert conn.execute("SELECT count(*) FROM broadbridge.review_log").fetchone()[0] == 1
    assert conn.execute("SELECT record, updated_by, signed FROM broadbridge.cases").fetchone() == (case, "first@example.com", True)
    second = database.upsert_case(conn, case, "second@example.com")
    assert second["revision"] != saved["revision"]
    assert conn.execute("SELECT updated_by FROM broadbridge.cases").fetchone()[0] == "second@example.com"
    assert conn.execute("SELECT count(*) FROM broadbridge.review_log").fetchone()[0] == 1


def test_expected_revision_rejects_stale_edit(database, conn, case):
    first = database.upsert_case(conn, case, "first@example.com")
    case["status"] = "complete"
    case["reviewer_signoff"]["signed"] = False
    second = database.upsert_case(conn, case, "second@example.com", first["revision"])
    with pytest.raises(psycopg.errors.SerializationFailure):
        with conn.transaction():
            database.upsert_case(conn, case, "stale@example.com", first["revision"])
    assert conn.execute("SELECT updated_by FROM broadbridge.cases").fetchone()[0] == "second@example.com"
    assert second["revision"] != first["revision"]


@pytest.mark.parametrize("path,value", [
    (("status",), "approved"), (("identity", "permitted_use"), "unknown"),
    (("identity", "record_type"), "invented"), (("questions", 0, "split"), "test"),
    (("questions", 0, "type"), "other"), (("reviewer_signoff", "signed"), "true"),
    (("reviewer_signoff", "name"), "unknown"), (("reviewer_signoff", "date"), "  "),
    (("family_id",), ""), (("case_id",), " x "),
])
def test_shared_sql_rejects_invalid_records(conn, case, path, value):
    target = case
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(psycopg.Error):
        conn.execute("SELECT broadbridge.save_case(%s, %s)", (Jsonb(case), "a@example.com"))


def test_direct_index_column_mismatch_is_rejected(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE broadbridge.cases SET permitted_use='testing_only'")


def test_case_and_question_ids_are_case_insensitive(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    duplicate = copy.deepcopy(case)
    duplicate["case_id"] = case["case_id"].lower()
    duplicate["questions"][0]["question_id"] = "different-question"
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():
            database.upsert_case(conn, duplicate, "a@example.com")
    duplicate["case_id"] = "new-case"
    duplicate["questions"][0]["question_id"] = case["questions"][0]["question_id"].lower()
    with pytest.raises(psycopg.errors.UniqueViolation):
        with conn.transaction():
            database.upsert_case(conn, duplicate, "a@example.com")


def test_audit_permission_signoff_changes_and_append_only(database, conn, case):
    database.upsert_case(conn, case, "first@example.com")
    case["identity"]["permitted_use"] = "reference_only"
    case["reviewer_signoff"]["name"] = "NEW REVIEWER"
    case["reviewer_signoff"]["date"] = "2026-09-25"
    database.upsert_case(conn, case, "reviewer@example.com")
    rows = conn.execute("SELECT actor, old_record, new_record FROM broadbridge.review_log ORDER BY review_id").fetchall()
    assert len(rows) == 2
    assert rows[0][0:2] == ("first@example.com", None)
    assert rows[1][0] == "reviewer@example.com"
    assert rows[1][1]["identity"]["permitted_use"] == "training"
    assert rows[1][2]["reviewer_signoff"]["name"] == "NEW REVIEWER"
    for statement in ("UPDATE broadbridge.review_log SET actor='forged'", "DELETE FROM broadbridge.review_log", "TRUNCATE broadbridge.review_log"):
        with pytest.raises(psycopg.Error):
            with conn.transaction():
                conn.execute(statement)


def test_signed_content_edit_requires_renewed_signoff(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    case["decision_time"]["b1_trigger"] = "Changed evidence"
    with pytest.raises(psycopg.errors.CheckViolation):
        with conn.transaction():
            database.upsert_case(conn, case, "a@example.com")
    case["status"] = "complete"
    case["reviewer_signoff"]["signed"] = False
    database.upsert_case(conn, case, "a@example.com")
    assert conn.execute("SELECT count(*) FROM broadbridge.train_candidates").fetchone()[0] == 0


def test_family_promotion_demotion_movement_and_removal(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    held = copy.deepcopy(case)
    held.update(case_id="HELD", status="draft")
    held["questions"][0].update(question_id="HELD-Q1", split="locked_test")
    held["reviewer_signoff"]["signed"] = False
    database.upsert_case(conn, held, "b@example.com")
    assert conn.execute("SELECT DISTINCT effective_split FROM broadbridge.questions").fetchall() == [("locked_test",)]
    assert conn.execute("SELECT count(*) FROM broadbridge.train_candidates").fetchone()[0] == 0
    held["questions"][0]["split"] = "dev"
    database.upsert_case(conn, held, "b@example.com")
    assert conn.execute("SELECT DISTINCT effective_split FROM broadbridge.questions").fetchall() == [("dev",)]
    held["family_id"] = "another-family"
    database.upsert_case(conn, held, "b@example.com")
    assert conn.execute("SELECT question_id FROM broadbridge.train_candidates").fetchall() == [("SYN-TRAIN-001-Q1",)]
    held["questions"] = []
    database.upsert_case(conn, held, "b@example.com")
    assert conn.execute("SELECT count(*) FROM broadbridge.questions").fetchone()[0] == 1


def test_direct_question_changes_are_refused(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    for statement in ("UPDATE broadbridge.questions SET effective_split='locked_test'", "DELETE FROM broadbridge.questions", "TRUNCATE broadbridge.questions"):
        with pytest.raises(psycopg.Error):
            with conn.transaction():
                conn.execute(statement)


@pytest.mark.parametrize("permission,status,signed", [("reference_only", "signed", True), ("testing_only", "signed", True), ("training", "complete", False), ("training", "draft", False)])
def test_training_revocation_is_immediate(database, conn, case, permission, status, signed):
    database.upsert_case(conn, case, "a@example.com")
    assert conn.execute("SELECT count(*) FROM broadbridge.train_candidates").fetchone()[0] == 1
    case["identity"]["permitted_use"] = permission
    case["status"] = status
    case["reviewer_signoff"]["signed"] = signed
    database.upsert_case(conn, case, "b@example.com")
    assert conn.execute("SELECT count(*) FROM broadbridge.train_candidates").fetchone()[0] == 0


def test_transaction_failure_rolls_back_all_case_rows(database, conn, case):
    with pytest.raises(RuntimeError):
        with conn.transaction():
            database.upsert_case(conn, case, "a@example.com")
            raise RuntimeError("publication failed")
    for table in ("cases", "questions", "review_log"):
        assert conn.execute(f"SELECT count(*) FROM broadbridge.{table}").fetchone()[0] == 0


def test_workflow_source_and_evidence_upserts_keep_records(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    workflow = {"schema": "broadbridge.workflow/1", "answers": {"A1": "free text"}, "updated_at": "capture timestamp"}
    source = {"source_id": "S-1", "title": "source", "restriction": "as captured"}
    evidence = {"evidence_id": "E-1", "source_id": "S-1", "case_id": case["case_id"], "text": "evidence"}
    for _ in range(2):
        database.upsert_workflow(conn, workflow, "Author@Example.com")
        database.upsert_source(conn, source, "a@example.com")
        database.upsert_evidence(conn, evidence, "a@example.com")
    assert conn.execute("SELECT author_email, record FROM broadbridge.workflow").fetchall() == [("author@example.com", workflow)]
    assert conn.execute("SELECT record FROM broadbridge.sources").fetchall() == [(source,)]
    assert conn.execute("SELECT record FROM broadbridge.evidence").fetchall() == [(evidence,)]
    evidence["source_id"] = "MISSING"
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database.upsert_evidence(conn, evidence, "a@example.com")


def test_run_scorecard_stability_and_case_binding(database, conn, case):
    from run_brief import create_run
    database.upsert_case(conn, case, "a@example.com")
    brief = json.loads((PACK / "tests/fixtures/SYN-001.mock_brief.json").read_text(encoding="utf-8"))
    record = create_run(case, mock_response=brief)
    run_id = database.upsert_run(conn, record, "a@example.com")
    assert len(run_id) == 64
    assert database.upsert_run(conn, copy.deepcopy(record), "a@example.com") == run_id
    assert database.upsert_scorecard(conn, case, record, "# Unreviewed", "a@example.com") == run_id
    database.upsert_scorecard(conn, case, record, "# Updated", "b@example.com")
    assert conn.execute("SELECT markdown, updated_by FROM broadbridge.scorecards").fetchall() == [("# Updated", "b@example.com")]
    assert conn.execute("SELECT count(*) FROM broadbridge.runs").fetchone()[0] == 1
    changed = copy.deepcopy(case)
    changed["updated_at"] = "changed capture timestamp"
    with pytest.raises(ValueError):
        database.upsert_scorecard(conn, changed, record, "wrong snapshot", "a@example.com")


def test_generated_sheet_cannot_replace_existing_review(database, conn, case):
    from run_brief import create_run
    from score_brief import render_scorecard
    database.upsert_case(conn, case, "a@example.com")
    brief = json.loads((PACK / "tests/fixtures/SYN-001.mock_brief.json").read_text(encoding="utf-8"))
    record = create_run(case, mock_response=brief)
    template = render_scorecard(case, record)
    reviewed = template.replace("Reviewer: ______", "Reviewer: Test Reviewer")
    database.upsert_scorecard(conn, case, record, reviewed, "a@example.com")
    with pytest.raises(ValueError, match="preserve"):
        database.upsert_scorecard(conn, case, record, template, "a@example.com")
    assert conn.execute("SELECT markdown FROM broadbridge.scorecards").fetchone()[0] == reviewed


def test_connection_uses_dedicated_env_and_sanitizes_errors(monkeypatch, database):
    monkeypatch.delenv("BROADBRIDGE_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://sensitive:secret@127.0.0.1:1/other")
    with pytest.raises(RuntimeError, match="BROADBRIDGE_DATABASE_URL"):
        with database.connection():
            pass
    monkeypatch.setenv("BROADBRIDGE_DATABASE_URL", "postgres://sensitive:secret@127.0.0.1:1/other?connect_timeout=1")
    with pytest.raises(RuntimeError) as result:
        with database.connection():
            pass
    assert "secret" not in str(result.value)
    assert "sensitive" not in str(result.value)


@pytest.mark.parametrize("url,branch,git_branch", [
    ("postgres://u@localhost/broadbridge_test_core", "main", "feature"),
    ("postgres://u@localhost/broadbridge_test_core", "test", "main"),
    ("postgres://u@localhost/broadbridge_test_core", "test", "master"),
    ("postgres://u@production.neon.tech/broadbridge_test_core", "test", "feature"),
    ("postgres://u@localhost/production", "dev", "feature"),
    ("postgres://u@localhost/broadbridge_test_core?host=production.neon.tech", "test", "feature"),
])
def test_reset_refuses_unverified_or_primary_target(database, url, branch, git_branch):
    with pytest.raises(ValueError):
        database._check_reset_target(url, branch, git_branch)


def test_reset_accepts_explicit_loopback_test(database):
    database._check_reset_target("postgres://u@127.0.0.1:5432/broadbridge_test_core", "test", "codex/db")


def test_reset_checks_client_peer_and_only_drops_capture_schema(database, conn):
    if conn.info.hostaddr not in ("127.0.0.1", "::1"):
        pytest.skip("Destructive reset verification is restricted to disposable loopback PostgreSQL")
    with pytest.raises(RuntimeError, match="roll back reset"):
        with conn.transaction():
            database._reset_schema(conn)
            assert conn.execute("SELECT to_regnamespace('broadbridge')").fetchone()[0] is None
            assert conn.execute("SELECT 1 FROM pg_extension WHERE extname='vector'").fetchone() == (1,)
            raise RuntimeError("roll back reset")
    assert database.status(conn)["version"] == sorted(path.name for path in database.MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql"))[-1]


def test_historical_run_keeps_current_capture_and_effective_family(database, conn, case):
    from run_brief import create_run
    original = copy.deepcopy(case)
    brief = json.loads((PACK / "tests/fixtures/SYN-001.mock_brief.json").read_text(encoding="utf-8"))
    record = create_run(original, mock_response=brief)
    case.update(status="draft")
    case["reviewer_signoff"]["signed"] = False
    case["decision_time"]["b1_trigger"] = "New capture"
    case["questions"][0]["split"] = "locked_test"
    database.upsert_case(conn, case, "new@example.com")
    database.upsert_run(conn, record, "historic@example.com")
    database.upsert_scorecard(conn, original, record, "old run", "historic@example.com")
    assert conn.execute("SELECT record FROM broadbridge.cases").fetchone()[0] == case
    assert database.effective_splits(conn, [case["family_id"], "absent"]) == {case["family_id"]: "locked_test"}


def test_case_delete_releases_family_holdout(database, conn, case):
    database.upsert_case(conn, case, "a@example.com")
    held = copy.deepcopy(case)
    held.update(case_id="HELD")
    held["questions"][0].update(question_id="HELD-Q1", split="locked_test")
    database.upsert_case(conn, held, "a@example.com")
    conn.execute("DELETE FROM broadbridge.cases WHERE case_id='HELD'")
    assert conn.execute("SELECT question_id FROM broadbridge.train_candidates").fetchall() == [("SYN-TRAIN-001-Q1",)]
    assert conn.execute("SELECT operation FROM broadbridge.review_log ORDER BY review_id DESC LIMIT 1").fetchone() == ("DELETE",)


def test_concurrent_save_waits_and_rechecks_revision(database, conn, case):
    saved = database.upsert_case(conn, case, "first@example.com")
    ready = threading.Event()
    state = {}

    def contender():
        try:
            with database.connection() as other:
                other.execute("SET statement_timeout = '15s'")
                # Pooled Neon reports the proxy PID via libpq; pg_locks contains
                # the actual server PID pinned to this open transaction.
                state["pid"] = other.execute("SELECT pg_backend_pid()").fetchone()[0]
                ready.set()
                database.upsert_case(other, case, "second@example.com", saved["revision"])
                other.rollback()
        except psycopg.errors.SerializationFailure:
            return "conflict"
        return "saved"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(contender)
        try:
            assert ready.wait(10), "Concurrent connection was not established"
            deadline = time.monotonic() + 10
            waiting = False
            while time.monotonic() < deadline:
                waiting = conn.execute("SELECT EXISTS (SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)", (state["pid"],)).fetchone()[0]
                if waiting or pending.done():
                    break
                time.sleep(0.02)
            assert waiting, "A second case writer did not wait for the first transaction"
        finally:
            conn.rollback()
        assert pending.result(timeout=20) == "conflict"
    assert conn.execute("SELECT count(*) FROM broadbridge.cases").fetchone()[0] == 0


def test_browser_workflow_save_waits_for_importer_and_rechecks_revision(database, conn):
    actor = "workflow-race@example.com"
    imported = {"schema": "broadbridge.workflow/1", "answers": {"A1": "Imported answer"}, "updated_at": "import timestamp"}
    saved = database.upsert_workflow(conn, imported, actor)
    edited = copy.deepcopy(imported)
    edited["answers"]["A1"] = "Browser answer"
    ready = threading.Event()
    state = {}

    def browser_writer():
        try:
            with database.connection() as other:
                other.execute("SET statement_timeout = '15s'")
                state["pid"] = other.execute("SELECT pg_backend_pid()").fetchone()[0]
                ready.set()
                other.execute("SELECT broadbridge.capture_save_workflow(%s,%s,%s)", (Jsonb(edited), actor, saved["revision"]))
                other.rollback()
        except psycopg.errors.SerializationFailure:
            return "conflict"
        return "saved"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(browser_writer)
        try:
            assert ready.wait(10), "Concurrent connection was not established"
            deadline = time.monotonic() + 10
            waiting = False
            while time.monotonic() < deadline:
                waiting = conn.execute("SELECT EXISTS (SELECT 1 FROM pg_locks WHERE pid=%s AND locktype='advisory' AND NOT granted)", (state["pid"],)).fetchone()[0]
                if waiting or pending.done():
                    break
                time.sleep(0.02)
            assert waiting, "Browser workflow save did not wait for the importer transaction"
        finally:
            # Releasing the import transaction changes the visible revision back
            # to NULL; the waiting browser must recheck it and reject its edit.
            conn.rollback()
        assert pending.result(timeout=20) == "conflict"
    assert conn.execute("SELECT count(*) FROM broadbridge.workflow WHERE author_email=%s", (actor,)).fetchone()[0] == 0


@pytest.mark.parametrize("problem", ["missing_section", "array_hardfail", "extra_property", "tab_name", "newline_date"])
def test_shared_sql_requires_canonical_shape_and_real_signoff(conn, case, problem):
    if problem == "missing_section":
        del case["decision_time"]
    elif problem == "array_hardfail":
        case["questions"][0]["hard_fail_criteria"] = ["not a string"]
    elif problem == "extra_property":
        case["identity"]["unexpected"] = "not canonical"
    elif problem == "tab_name":
        case["reviewer_signoff"]["name"] = "\t"
    else:
        case["reviewer_signoff"]["date"] = "\n"
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("SELECT broadbridge.save_case(%s,%s)", (Jsonb(case), "a@example.com"))


@pytest.mark.parametrize("key,marker", [("case_id", "unknown"), ("family_id", "undecided")])
def test_training_excludes_unknown_identity_markers(database, conn, case, key, marker):
    case[key] = marker
    database.upsert_case(conn, case, "a@example.com")
    assert conn.execute("SELECT count(*) FROM broadbridge.train_candidates").fetchone()[0] == 0


def test_sql_embedded_schema_is_exact_canonical_contract(conn):
    canonical = json.loads((PACK / "schemas/case_record.schema.json").read_text(encoding="utf-8"))
    assert conn.execute("SELECT broadbridge.case_contract()").fetchone()[0] == canonical


def test_sql_schema_validator_fails_closed_on_unsupported_keywords(conn):
    assert conn.execute("SELECT broadbridge.matches_schema(%s,%s)", (Jsonb("abc"), Jsonb({"type": "string", "pattern": "^x"}))).fetchone() == (False,)
