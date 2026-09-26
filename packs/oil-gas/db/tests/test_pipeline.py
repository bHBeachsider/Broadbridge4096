"""Committed pipeline integration on the explicitly assigned disposable local DB.

Set BROADBRIDGE_PIPELINE_TEST_URL to a loopback PostgreSQL URL for database
broadbridge_test_pipeline and role broadbridge_test. These tests recreate only
that database's broadbridge schema for isolation. They never read a .env file.
"""
import copy
import importlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

import pytest

PACK = Path(__file__).resolve().parents[2]
FIXTURES = PACK / "tests/fixtures"
sys.path.insert(0, str(PACK / "scripts"))
ACTOR = "pipeline-reviewer@example.test"


@pytest.fixture(scope="module")
def pipeline_target():
    value = os.environ.get("BROADBRIDGE_PIPELINE_TEST_URL")
    if not value:
        pytest.skip("Set BROADBRIDGE_PIPELINE_TEST_URL to the disposable local pipeline database")
    target = urlsplit(value)
    assert target.scheme in ("postgres", "postgresql")
    assert target.hostname in ("127.0.0.1", "localhost", "::1"), "Pipeline tests require loopback"
    assert target.username == "broadbridge_test", "Pipeline tests require the explicit test role"
    assert target.path == "/broadbridge_test_pipeline", "Pipeline tests require their owned database"
    assert not target.query and not target.fragment, "Pipeline tests reject URL connection overrides"
    return value


@pytest.fixture
def pipeline_db(pipeline_target, monkeypatch):
    # Override only this test process; never inherit BROADBRIDGE_DATABASE_URL or .env.
    monkeypatch.setenv("BROADBRIDGE_DATABASE_URL", pipeline_target)
    database = importlib.import_module("db")
    with database.connection() as conn:
        assert conn.execute("SELECT current_database(), current_user").fetchone() == (
            "broadbridge_test_pipeline", "broadbridge_test")
        conn.execute("DROP SCHEMA IF EXISTS broadbridge CASCADE")
        database.migrate(conn)
    try:
        yield database
    finally:
        with database.connection() as conn:
            assert conn.execute("SELECT current_database(), current_user").fetchone() == (
                "broadbridge_test_pipeline", "broadbridge_test")
            conn.execute("DROP SCHEMA IF EXISTS broadbridge CASCADE")


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def _import(output):
    importer = importlib.import_module("import_cases")
    assert importer.main([str(FIXTURES / "three_cases_export.json"), str(output),
                          "--db", "--actor", ACTOR]) == 0
    return _json(output / "import_report.json")


def test_import_source_registry_and_evidence_commit_exact_records(pipeline_db, tmp_path):
    registry = importlib.import_module("register_sources")
    extractor = importlib.import_module("extract_evidence")
    source_fixture = FIXTURES / "db_sources.json"
    # Replaying the same register must not create additional rows or infer fields.
    for _ in range(2):
        assert registry.main([str(source_fixture), "--db", "--actor", ACTOR]) == 0
    snapshot = tmp_path / "snapshot"
    report = _import(snapshot)
    evidence_path = tmp_path / "evidence.json"
    assert extractor.main([str(FIXTURES / "evidence_sample.txt"),
                           "--source-id", "DB-TEST-001", "--evidence-id", "PIPELINE-EVIDENCE-001",
                           "--case-id", "SYN-001", "--output", str(evidence_path),
                           "--db", "--actor", ACTOR]) == 0
    assert report["counts"] == {"case_files": 3, "questions": 3, "train_candidates": 2}
    with pipeline_db.connection() as conn:
        assert pipeline_db.status(conn)["counts"] == {
            "sources": 5, "evidence": 1, "cases": 3, "questions": 3, "workflow": 1,
            "runs": 0, "scorecards": 0, "review_log": 3}
        sources = conn.execute("SELECT record, updated_by FROM broadbridge.sources ORDER BY source_id").fetchall()
        assert sources == [(record, ACTOR) for record in _json(source_fixture)]
        cases = conn.execute("SELECT record, updated_by FROM broadbridge.cases ORDER BY case_id").fetchall()
        assert cases == [(record, ACTOR) for record in _json(FIXTURES / "three_cases_export.json")["cases"]]
        assert conn.execute("SELECT source_id, case_id, record, updated_by FROM broadbridge.evidence").fetchall() == [
            ("DB-TEST-001", "SYN-001", _json(evidence_path), ACTOR)]
        assert conn.execute("SELECT author_email, record FROM broadbridge.workflow").fetchall() == [
            (ACTOR, _json(FIXTURES / "three_cases_export.json")["workflow"])]
        assert conn.execute("SELECT question_id FROM broadbridge.train_candidates ORDER BY question_id").fetchall() == [
            ("SYN-TRAIN-001-Q1",), ("SYN-TRAIN-002-Q1",)]


def test_second_import_is_idempotent_and_publishes_a_fresh_snapshot(pipeline_db, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    first_report = _import(first)
    with pipeline_db.connection() as conn:
        before_counts = pipeline_db.status(conn)["counts"]
        before_cases = conn.execute("SELECT case_id, record, updated_by, updated_at FROM broadbridge.cases ORDER BY case_id").fetchall()
        before_workflow = conn.execute("SELECT record, updated_at FROM broadbridge.workflow").fetchall()
    assert _import(second) == first_report
    assert second.is_dir() and first.is_dir()
    assert (second / "data/train_candidates.jsonl").read_bytes() == (first / "data/train_candidates.jsonl").read_bytes()
    with pipeline_db.connection() as conn:
        assert pipeline_db.status(conn)["counts"] == before_counts
        assert conn.execute("SELECT case_id, record, updated_by, updated_at FROM broadbridge.cases ORDER BY case_id").fetchall() == before_cases
        assert conn.execute("SELECT record, updated_at FROM broadbridge.workflow").fetchall() == before_workflow


def test_missing_source_fk_leaves_no_evidence_row_or_published_file(pipeline_db, tmp_path):
    extractor = importlib.import_module("extract_evidence")
    _import(tmp_path / "cases")
    output = tmp_path / "evidence.json"
    with pipeline_db.connection() as conn:
        before = pipeline_db.status(conn)["counts"]
    with pytest.raises(RuntimeError, match="ForeignKeyViolation"):
        extractor.extract_evidence(FIXTURES / "evidence_sample.txt", output,
                                   source_id="ABSENT-SOURCE", evidence_id="PIPELINE-MISSING-SOURCE",
                                   case_id="SYN-001", use_db=True, actor=ACTOR)
    assert not output.exists()
    assert not list(tmp_path.glob(".evidence-intake-*"))
    with pipeline_db.connection() as conn:
        assert pipeline_db.status(conn)["counts"] == before
        assert conn.execute("SELECT count(*) FROM broadbridge.evidence").fetchone() == (0,)


def test_database_family_holdout_survives_omission_from_new_export(pipeline_db, tmp_path):
    held = copy.deepcopy(_json(FIXTURES / "SYN-TRAIN-001.json"))
    held.update(case_id="PIPELINE-HELD-001", status="draft")
    held["reviewer_signoff"]["signed"] = False
    held["questions"][0].update(question_id="PIPELINE-HELD-001-Q1", split="locked_test")
    with pipeline_db.connection() as conn:
        pipeline_db.upsert_case(conn, held, ACTOR)
    snapshot = tmp_path / "snapshot"
    report = _import(snapshot)
    assert not (snapshot / "data/cases/PIPELINE-HELD-001.json").exists()
    assert report["counts"] == {"case_files": 3, "questions": 3, "train_candidates": 1}
    assert report["family_splits"]["SYN-TRAIN-001"] == "locked_test"
    imported = next(row for row in report["cases"] if row["case_id"] == "SYN-TRAIN-001")
    assert imported["disposition"] == "eval-only"
    assert imported["effective_split"] == "locked_test"
    candidates = _jsonl(snapshot / "data/train_candidates.jsonl")
    assert [row["question_id"] for row in candidates] == ["SYN-TRAIN-002-Q1"]
    question = next(row for row in _jsonl(snapshot / "eval/questions.jsonl") if row["case_id"] == "SYN-TRAIN-001")
    assert (question["requested_split"], question["split"]) == ("train", "locked_test")
    with pipeline_db.connection() as conn:
        assert conn.execute("SELECT case_id, effective_split FROM broadbridge.questions "
                            "WHERE case_id IN ('SYN-TRAIN-001', 'PIPELINE-HELD-001') ORDER BY case_id").fetchall() == [
            ("PIPELINE-HELD-001", "locked_test"), ("SYN-TRAIN-001", "locked_test")]
        assert conn.execute("SELECT question_id FROM broadbridge.train_candidates").fetchall() == [("SYN-TRAIN-002-Q1",)]


def test_mock_run_and_score_keep_newer_database_case(pipeline_db, tmp_path):
    runner = importlib.import_module("run_brief")
    scorer = importlib.import_module("score_brief")
    snapshot = tmp_path / "snapshot"
    _import(snapshot)
    case_path = snapshot / "data/cases/SYN-TRAIN-001.json"
    historical = _json(case_path)
    newer = copy.deepcopy(historical)
    newer["decision_time"]["b1_trigger"] = "Synthetic updated observation awaiting renewed review."
    newer["status"] = "complete"
    newer["reviewer_signoff"]["signed"] = False
    newer["updated_at"] = "2026-09-25T00:00:00Z"
    with pipeline_db.connection() as conn:
        pipeline_db.upsert_case(conn, newer, "newer-author@example.test")
        current_case = conn.execute("SELECT record, updated_by, updated_at FROM broadbridge.cases "
                                    "WHERE case_id='SYN-TRAIN-001'").fetchone()
        audit_count = conn.execute("SELECT count(*) FROM broadbridge.review_log").fetchone()[0]
    run_path = tmp_path / "run/brief_run.json"
    assert runner.main([str(case_path), "--mock-response", str(FIXTURES / "SYN-001.mock_brief.json"),
                        "--output", str(run_path), "--db", "--actor", ACTOR]) == 0
    score_dir = tmp_path / "run/eval"
    assert scorer.main([str(case_path), str(run_path), str(score_dir), "--db", "--actor", ACTOR]) == 0
    record = _json(run_path)
    assert record["mode"] == "mock"
    assert record["case_sha256"] == runner.digest(historical)
    assert record["case_sha256"] != runner.digest(newer)
    score_path = score_dir / "scorecard_SYN-TRAIN-001.md"
    score_text = score_path.read_text(encoding="utf-8")
    assert "MOCK / UNREVIEWED" in score_text
    with pipeline_db.connection() as conn:
        assert conn.execute("SELECT record, updated_by, updated_at FROM broadbridge.cases "
                            "WHERE case_id='SYN-TRAIN-001'").fetchone() == current_case
        assert conn.execute("SELECT count(*) FROM broadbridge.review_log").fetchone()[0] == audit_count
        assert conn.execute("SELECT run_id, case_id, mode, record, updated_by FROM broadbridge.runs").fetchall() == [
            (runner.digest(record), "SYN-TRAIN-001", "mock", record, ACTOR)]
        assert conn.execute("SELECT run_id, case_id, markdown, updated_by FROM broadbridge.scorecards").fetchall() == [
            (runner.digest(record), "SYN-TRAIN-001", score_text, ACTOR)]
        assert conn.execute("SELECT question_id FROM broadbridge.train_candidates").fetchall() == [("SYN-TRAIN-002-Q1",)]
