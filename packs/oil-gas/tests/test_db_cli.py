"""Existing CLI boundaries with optional transactional DB mirroring (no network)."""
import importlib
import json
from pathlib import Path
import sys
import types

import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))
FIXTURES = PACK / "tests/fixtures"


@pytest.fixture
def database(monkeypatch):
    events = []
    class Connection:
        def __enter__(self): events.append(("begin",)); return self
        def __exit__(self, kind, *args): events.append(("rollback" if kind else "commit",))
    module = types.SimpleNamespace(
        connection=Connection,
        upsert_case=lambda conn, record, actor: events.append(("case", record["case_id"], actor)),
        upsert_workflow=lambda conn, record, actor: events.append(("workflow", actor)),
        effective_splits=lambda conn, families: {},
        upsert_run=lambda conn, record, actor: events.append(("run", record["case_id"], actor)),
        upsert_scorecard=lambda conn, case, record, text, actor: events.append(("scorecard", case["case_id"], actor, text)),
    )
    monkeypatch.setitem(sys.modules, "db", module)
    return module, events


def test_import_mirrors_cases_and_workflow_in_one_transaction(tmp_path, database):
    _, events = database
    importer = importlib.import_module("import_cases")
    output = tmp_path / "import"
    assert importer.main([str(FIXTURES / "three_cases_export.json"), str(output), "--db", "--actor", "importer@example.invalid"]) == 0
    assert events[0] == ("begin",) and events[-1] == ("commit",)
    assert [event[1] for event in events if event[0] == "case"] == ["SYN-001", "SYN-TRAIN-001", "SYN-TRAIN-002"]
    assert ("workflow", "importer@example.invalid") in events
    assert len(list((output / "data/cases").glob("*.json"))) == 3


def test_import_db_error_rolls_back_and_leaves_no_snapshot(tmp_path, database):
    module, events = database
    def fail(conn, record, actor): raise RuntimeError("injected database rejection")
    module.upsert_case = fail
    output = tmp_path / "import"
    assert importlib.import_module("import_cases").main([
        str(FIXTURES / "capture_export.json"), str(output), "--db", "--actor", "importer@example.invalid"]) == 2
    assert events[-1] == ("rollback",)
    assert not output.exists()


def test_mock_brief_and_scorecard_db_modes_do_not_call_model(tmp_path, database):
    _, events = database
    runner, scorer = importlib.import_module("run_brief"), importlib.import_module("score_brief")
    case_file = FIXTURES / "SYN-001.json"
    output = tmp_path / "brief_run.json"
    assert runner.main([str(case_file), "--mock-response", str(FIXTURES / "SYN-001.mock_brief.json"),
                        "--output", str(output), "--db", "--actor", "operator@example.invalid"]) == 0
    assert ("run", "SYN-001", "operator@example.invalid") in events
    assert json.loads(output.read_text())["mode"] == "mock"
    assert scorer.main([str(case_file), str(output), str(tmp_path / "eval"), "--db", "--actor", "reviewer@example.invalid"]) == 0
    written = [event for event in events if event[0] == "scorecard"]
    assert len(written) == 1 and written[0][1:3] == ("SYN-001", "reviewer@example.invalid")
    assert "UNREVIEWED" in written[0][3]
    assert (tmp_path / "eval/scorecard_SYN-001.md").exists()


@pytest.mark.parametrize("script", ["import_cases", "run_brief", "score_brief"])
def test_db_requires_actor_before_any_writes(tmp_path, database, script):
    _, events = database
    args = {
        "import_cases": [str(FIXTURES / "capture_export.json"), str(tmp_path / "import")],
        "run_brief": [str(FIXTURES / "SYN-001.json"), "--mock-response", str(FIXTURES / "SYN-001.mock_brief.json"), "--output", str(tmp_path / "brief.json")],
        "score_brief": [str(FIXTURES / "SYN-001.json"), str(tmp_path / "nonexistent.json"), str(tmp_path / "eval")],
    }[script]
    assert importlib.import_module(script).main(args + ["--db"]) == 2
    assert not events


def test_db_brief_requires_output_and_disallows_dry_run(tmp_path, database):
    _, events = database
    runner = importlib.import_module("run_brief")
    assert runner.main([str(FIXTURES / "SYN-001.json"), "--db", "--actor", "operator@example.invalid", "--dry-run"]) == 2
    assert not events


@pytest.mark.parametrize("change", ["complete", "reference", "incomplete"])
def test_sync_existing_review_preserves_file_and_protected_content(tmp_path, database, change):
    _, events = database
    runner, scorer = importlib.import_module("run_brief"), importlib.import_module("score_brief")
    case_file = FIXTURES / "SYN-001.json"
    run_file = tmp_path / "brief.json"
    assert runner.main([str(case_file), "--mock-response", str(FIXTURES / "SYN-001.mock_brief.json"), "--output", str(run_file)]) == 0
    assert scorer.main([str(case_file), str(run_file), str(tmp_path)]) == 0
    card = tmp_path / "scorecard_SYN-001.md"
    text = card.read_text(encoding="utf-8")
    if change != "incomplete":
        for old, new in {
            "Reviewer: ______": "Reviewer: Test Reviewer",
            "Review date: ______": "Review date: 2026-09-24",
            "Reviewer acceptance signature/date: ______": "Reviewer acceptance signature/date: Test Reviewer / 2026-09-24",
            "Score (0 / 1 / 2 / N/A): ______": "Score (0 / 1 / 2 / N/A): 2",
            "Critical error (YES / NO / UNASSESSED): UNASSESSED": "Critical error (YES / NO / UNASSESSED): NO",
            "Brief quotation / evidence supporting score: ______": "Brief quotation / evidence supporting score: Synthetic replay reviewed.",
            "Matched hard-fail criterion, or explanation for NO: ______": "Matched hard-fail criterion, or explanation for NO: No listed criterion matched.",
        }.items():
            text = text.replace(old, new)
    if change == "reference":
        case = json.loads(case_file.read_text(encoding="utf-8"))
        text = text.replace(case["questions"][0]["reference_answer"], "Changed answer key")
    card.write_text(text, encoding="utf-8")
    before = card.read_bytes()
    result = scorer.main([str(case_file), str(run_file), str(tmp_path), "--db", "--actor", "reviewer@example.invalid", "--sync-existing"])
    assert result == (0 if change == "complete" else 2)
    assert card.read_bytes() == before
    assert len([e for e in events if e[0] == "scorecard"]) == (1 if change == "complete" else 0)
