"""First-case transport settings, artifact integrity and reviewer handoff (offline)."""
import importlib
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))


@pytest.fixture
def case():
    return json.loads((PACK / "tests/fixtures/SYN-001.json").read_text(encoding="utf-8"))


@pytest.fixture
def mock_brief():
    return json.loads((PACK / "tests/fixtures/SYN-001.mock_brief.json").read_text(encoding="utf-8"))


def test_schema_reaches_transport_with_thinking_disabled(case, mock_brief):
    runner = importlib.import_module("run_brief")
    schema = {"type": "object", "required": ["observations"]}
    sent = []
    def transport(messages, **kwargs):
        sent.append((messages, kwargs))
        return json.dumps(mock_brief)
    result = runner.run_case(case, chat_fn=transport, schema=schema)
    assert json.loads(result)["numeric"] is None
    assert sent[0][1] == {"think": False, "temperature": 0.2, "schema": schema}
    assert set(json.loads(sent[0][0][1]["content"])) == {"identity", "decision_time"}


@pytest.mark.parametrize("reply", ['{"wrong": 1}', 'not JSON', '{"observations": [], "observations": []}', '{"observations": NaN}', '{"observations": [], "numeric": 1e400}'])
def test_invalid_structured_reply_is_refused(case, reply):
    runner = importlib.import_module("run_brief")
    with pytest.raises(ValueError):
        runner.run_case(case, chat_fn=lambda *a, **k: reply,
                        schema={"type": "object", "required": ["observations"]})


def test_mock_run_never_opens_network_and_records_mock_status(case, mock_brief, monkeypatch):
    runner = importlib.import_module("run_brief")
    def no_network(*args, **kwargs):
        pytest.fail("offline rehearsal opened a socket")
    monkeypatch.setattr(socket, "socket", no_network)
    record = runner.create_run(case, mock_response=mock_brief)
    assert record["mode"] == "mock"
    assert record["model"] is None
    assert record["settings"]["think"] is False
    assert record["settings"]["schema"] == "brief"
    assert record["brief"]["missing_information"]


@pytest.mark.parametrize("damage", ["draft", "unsigned", "empty_name", "unknown_name", "unknown_date", "undecided", "no_questions"])
def test_first_live_run_refuses_unreviewed_case_before_foundry_access(case, damage):
    runner = importlib.import_module("run_brief")
    case["status"] = "signed"
    case["reviewer_signoff"] = {"signed": True, "name": "Synthetic reviewer", "date": "2026-09-24"}
    if damage == "draft": case["status"] = "draft"
    if damage == "unsigned": case["reviewer_signoff"]["signed"] = False
    if damage == "empty_name": case["reviewer_signoff"]["name"] = " "
    if damage == "unknown_name": case["reviewer_signoff"]["name"] = "unknown"
    if damage == "unknown_date": case["reviewer_signoff"]["date"] = "unknown"
    if damage == "undecided": case["identity"]["permitted_use"] = "undecided"
    if damage == "no_questions": case["questions"] = []
    # Removed permission values now fail schema validation before signoff preflight.
    expected = "permitted_use" if damage == "undecided" else "First-case preflight"
    with pytest.raises(ValueError, match=expected):
        runner.create_run(case, foundry="does-not-exist")


def test_scorecard_keeps_exact_criteria_and_does_not_invent_review(case, mock_brief):
    runner = importlib.import_module("run_brief")
    scorer = importlib.import_module("score_brief")
    card = scorer.render_scorecard(case, runner.create_run(case, mock_response=mock_brief))
    assert case["questions"][0]["hard_fail_criteria"] in card
    assert case["questions"][0]["reference_answer"] in card
    assert "MOCK" in card
    assert "UNREVIEWED" in card
    assert "Score (0 / 1 / 2 / N/A): ______" in card
    assert "Critical error (YES / NO / UNASSESSED): UNASSESSED" in card
    assert "Reviewer: ______" in card
    for kind in ("brief", "missing_data", "calculation", "grounded_explanation", "abstention"):
        assert f"| {kind} |" in card
    assert "| missing_data | 1 |" in card
    assert "| calculation | 0 | N/A" in card


@pytest.mark.parametrize("damage", ["case_id", "case_changed", "brief_shape", "prompt_hash"])
def test_scorecard_refuses_mismatched_or_invalid_run(case, mock_brief, damage):
    runner = importlib.import_module("run_brief")
    scorer = importlib.import_module("score_brief")
    record = runner.create_run(case, mock_response=mock_brief)
    if damage == "case_id": record["case_id"] = "another-case"
    if damage == "case_changed": case["questions"][0]["hard_fail_criteria"] += " additional criterion"
    if damage == "brief_shape": record["brief"] = {"observations": "bad shape"}
    if damage == "prompt_hash": record["prompt_sha256"] = "not-the-prompt"
    with pytest.raises(ValueError): scorer.render_scorecard(case, record)


def test_no_automatic_overwrite_of_completed_review(tmp_path, case, mock_brief):
    runner = importlib.import_module("run_brief")
    scorer = importlib.import_module("score_brief")
    output = tmp_path / "eval"
    path = scorer.write_scorecard(case, runner.create_run(case, mock_response=mock_brief), output)
    path.write_text("Reviewer completed this sheet.", encoding="utf-8")
    with pytest.raises(FileExistsError):
        scorer.write_scorecard(case, runner.create_run(case, mock_response=mock_brief), output)
    assert path.read_text(encoding="utf-8") == "Reviewer completed this sheet."


def test_full_cli_rehearsal_import_brief_scorecard(tmp_path):
    output = tmp_path / "first-case"
    def command(*args):
        result = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout
    disposition = command(PACK / "scripts/import_cases.py", PACK / "tests/fixtures/capture_export.json", output)
    assert "SYN-001 | eval-only" in disposition
    assert (output / "data/train_candidates.jsonl").read_text() == ""
    case_file = output / "data/cases/SYN-001.json"
    artifact = output / "brief_run.json"
    command(PACK / "run_brief.py", case_file, "--schema", "brief", "--mock-response",
            PACK / "tests/fixtures/SYN-001.mock_brief.json", "--output", artifact)
    command(PACK / "scripts/score_brief.py", case_file, artifact, output / "eval")
    card = (output / "eval/scorecard_SYN-001.md").read_text(encoding="utf-8")
    assert "SYN-001-Q1" in card
    assert "MOCK" in card
    assert "proposes a corrective action before requesting wash-oil rate" in card


def test_null_mock_file_never_falls_back_to_live_inference(tmp_path, case, monkeypatch, capsys):
    runner = importlib.import_module("run_brief")
    case["status"] = "signed"
    case["reviewer_signoff"] = {"signed": True, "name": "Synthetic reviewer", "date": "2026-09-24"}
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(case), encoding="utf-8")
    response = tmp_path / "null.json"
    response.write_text("null", encoding="utf-8")
    def refuse_live(*args, **kwargs):
        pytest.fail("invalid replay reached inference")
    monkeypatch.setattr(runner, "create_run", refuse_live)
    assert runner.main([str(case_file), "--mock-response", str(response)]) == 2
    assert "Brief schema" in capsys.readouterr().err


def test_existing_brief_output_is_preserved_before_inference(tmp_path, case, monkeypatch):
    runner = importlib.import_module("run_brief")
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps(case), encoding="utf-8")
    output = tmp_path / "brief_run.json"
    output.write_text("previous run", encoding="utf-8")
    def refuse_call(*args, **kwargs):
        pytest.fail("existing output should refuse before inference")
    monkeypatch.setattr(runner, "create_run", refuse_call)
    assert runner.main([str(case_file), "--output", str(output)]) == 2
    assert output.read_text(encoding="utf-8") == "previous run"


def test_signed_fallback_uses_the_same_complete_signoff_as_the_page():
    runner = importlib.import_module("run_brief")
    forms = importlib.import_module("case_from_form_fallback")
    case, _, _ = forms.parse_form(PACK / "tests/fixtures/Synthetic_Filled_Interview_Guide.docx",
                                  case_id="FORM-SYN-001", family_id="FORM-FAMILY-001", case_signed_off=True)
    assert case["reviewer_signoff"] == {"signed": True, "name": "SYNTHETIC REVIEWER ONLY", "date": "2026-09-24"}
    runner.require_signed_case(case)
    assert runner.run_case(case, dry_run=True)[1]["role"] == "user"
