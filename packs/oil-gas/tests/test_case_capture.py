"""Admission, family holdouts and prompt isolation using the live-page fixture."""
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))


@pytest.fixture
def seed():
    return json.loads((PACK / "tests/fixtures/SYN-001.json").read_text(encoding="utf-8"))


@pytest.fixture
def signed_cases(seed):
    return [json.loads((PACK / "tests/fixtures" / (name + ".json")).read_text(encoding="utf-8"))
            for name in ("SYN-TRAIN-001", "SYN-TRAIN-002")]


def write_export(tmp_path, cases):
    path = tmp_path / "export.json"
    path.write_text(json.dumps({"exported_at": "2026-09-24T00:00:00Z", "workflow": {
        "schema": "broadbridge.workflow/1", "updated_at": "", "answers": {}}, "cases": cases}), encoding="utf-8")
    return path


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_schemas_accept_actual_seed_and_export_metadata(seed):
    contract = importlib.import_module("case_contract")
    contract.validate_case(seed)
    contract.validate_export(json.loads((PACK / "tests/fixtures/capture_export.json").read_text()))


@pytest.mark.parametrize("mutation", ["unknown", "missing", "bad_split", "bad_record_type", "hard_fail_array"])
def test_schema_rejects_contract_drift(seed, mutation):
    contract = importlib.import_module("case_contract")
    if mutation == "unknown": seed["hindsight"]["new_field"] = "unexpected"
    if mutation == "missing": del seed["decision_time"]["b1_trigger"]
    if mutation == "bad_split": seed["questions"][0]["split"] = "val"
    if mutation == "bad_record_type": seed["identity"]["record_type"] = "unknown"
    if mutation == "hard_fail_array": seed["questions"][0]["hard_fail_criteria"] = ["wrong"]
    with pytest.raises(ValueError): contract.validate_case(seed)


def test_export_rejects_unknown_workflow_answer(seed):
    contract = importlib.import_module("case_contract")
    export = {"exported_at": "2026-09-24T00:00:00Z", "workflow": {"schema": "broadbridge.workflow/1",
              "updated_at": "", "answers": {"A11": "unknown"}}, "cases": [seed]}
    with pytest.raises(ValueError): contract.validate_export(export)


@pytest.mark.parametrize("split", ["dev", "locked_test", "no_questions"])
def test_training_validator_does_not_certify_holdouts(signed_cases, split):
    contract = importlib.import_module("case_contract")
    case = signed_cases[0]
    if split == "no_questions": case["questions"] = []
    else: case["questions"][0]["split"] = split
    with pytest.raises(ValueError, match="split"):
        contract.validate_case(case, training=True)


@pytest.mark.parametrize("answer", ['Known "retrospective" finding', "Retrospective\nfinding"])
def test_escaped_hindsight_string_still_triggers_guard(seed, answer):
    brief = importlib.import_module("run_brief")
    seed["hindsight"]["b8_turning_point"] = answer
    seed["decision_time"]["b1_trigger"] += " " + answer
    with pytest.raises(AssertionError, match="leak"):
        brief.run_case(seed, dry_run=True)


def test_import_seed_plus_two_signed_training_cases(tmp_path, seed, signed_cases):
    importer = importlib.import_module("import_cases")
    output = tmp_path / "output"
    report = importer.import_export(write_export(tmp_path, [seed, *signed_cases]), output)
    assert [(r["case_id"], r["disposition"]) for r in report["cases"]] == [
        ("SYN-001", "eval-only"), ("SYN-TRAIN-001", "imported"), ("SYN-TRAIN-002", "imported")]
    assert json.loads((output / "data/cases/SYN-001.json").read_text(encoding="utf-8")) == seed
    questions = rows(output / "eval/questions.jsonl")
    assert [(r["case_id"], r["split"], r["permitted_use"], r["type"]) for r in questions] == [
        ("SYN-001", "dev", "reference_only", "missing_data"),
        ("SYN-TRAIN-001", "train", "training", "missing_data"),
        ("SYN-TRAIN-002", "train", "training", "missing_data")]
    assert questions[0]["evidence_ids"] == "B1, B2, observations"
    candidates = rows(output / "data/train_candidates.jsonl")
    assert [r["case_id"] for r in candidates] == ["SYN-TRAIN-001", "SYN-TRAIN-002"]
    assert candidates[0]["messages"][-1]["content"] == signed_cases[0]["questions"][0]["reference_answer"]


@pytest.mark.parametrize("strictest", ["dev", "locked_test"])
def test_family_moves_together_and_holdout_never_becomes_training(tmp_path, signed_cases, strictest):
    importer = importlib.import_module("import_cases")
    for case in signed_cases: case["family_id"] = "shared-family"
    signed_cases[1]["questions"][0]["split"] = strictest
    output = tmp_path / "output"
    importer.import_export(write_export(tmp_path, signed_cases), output)
    assert [r["split"] for r in rows(output / "eval/questions.jsonl")] == [strictest, strictest]
    assert rows(output / "data/train_candidates.jsonl") == []


@pytest.mark.parametrize("status,permission", [("draft", "training"), ("complete", "training"),
                                                ("signed", "testing_only"), ("signed", "reference_only")])
def test_nontraining_cases_are_eval_only(tmp_path, signed_cases, status, permission):
    importer = importlib.import_module("import_cases")
    case = signed_cases[0]
    case["status"] = status
    case["identity"]["permitted_use"] = permission
    output = tmp_path / "output"
    report = importer.import_export(write_export(tmp_path, [case]), output)
    assert report["cases"][0]["disposition"] == "eval-only"
    assert rows(output / "data/train_candidates.jsonl") == []


def test_removed_permission_rejects_whole_export_without_defaulting(tmp_path, signed_cases):
    importer = importlib.import_module("import_cases")
    signed_cases[0]["identity"]["permitted_use"] = "undecided"
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="permitted_use.*undecided"):
        importer.import_export(write_export(tmp_path, signed_cases), output)
    assert not output.exists()


def test_missing_permission_is_not_filled_from_page_default(tmp_path, signed_cases):
    importer = importlib.import_module("import_cases")
    del signed_cases[0]["identity"]["permitted_use"]
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="permitted_use"):
        importer.import_export(write_export(tmp_path, signed_cases), output)
    assert not output.exists()


def test_new_draft_with_page_training_default_never_becomes_candidate(tmp_path, seed):
    importer = importlib.import_module("import_cases")
    seed["identity"]["permitted_use"] = "training"
    seed["questions"][0]["split"] = "train"
    output = tmp_path / "output"
    report = importer.import_export(write_export(tmp_path, [seed]), output)
    assert report["cases"][0]["disposition"] == "eval-only"
    assert report["cases"][0]["effective_split"] == "train"
    assert rows(output / "data/train_candidates.jsonl") == []
    assert rows(output / "eval/questions.jsonl")[0]["permitted_use"] == "training"


@pytest.mark.parametrize("field,value", [("signed", False), ("name", " "), ("date", ""),
                                         ("name", "unknown"), ("date", " unknown ")])
def test_signed_status_requires_signoff_for_training(tmp_path, signed_cases, field, value):
    importer = importlib.import_module("import_cases")
    signed_cases[0]["reviewer_signoff"][field] = value
    output = tmp_path / "output"
    report = importer.import_export(write_export(tmp_path, [signed_cases[0]]), output)
    assert report["cases"][0]["disposition"] == "rejected"
    assert rows(output / "data/train_candidates.jsonl") == []


def test_rejected_family_member_still_protects_locked_test(tmp_path, seed, signed_cases):
    importer = importlib.import_module("import_cases")
    seed["status"] = "signed"  # Incomplete signoff rejects this structurally valid case.
    seed["family_id"] = signed_cases[0]["family_id"]
    seed["questions"][0]["split"] = "locked_test"
    output = tmp_path / "output"
    report = importer.import_export(write_export(tmp_path, [seed, signed_cases[0]]), output)
    assert report["cases"][0]["disposition"] == "rejected"
    assert rows(output / "eval/questions.jsonl")[0]["split"] == "locked_test"
    assert rows(output / "data/train_candidates.jsonl") == []


@pytest.mark.parametrize("damage", ["case_duplicate", "question_duplicate", "traversal", "windows_reserved", "invalid"])
def test_bad_exports_fail_before_any_outputs(tmp_path, signed_cases, damage):
    importer = importlib.import_module("import_cases")
    if damage == "case_duplicate": signed_cases[1]["case_id"] = signed_cases[0]["case_id"].lower()
    if damage == "question_duplicate": signed_cases[1]["questions"][0]["question_id"] = signed_cases[0]["questions"][0]["question_id"]
    if damage == "traversal": signed_cases[0]["case_id"] = "../escape"
    if damage == "windows_reserved": signed_cases[0]["case_id"] = "CON"
    if damage == "invalid": signed_cases[1]["questions"][0]["type"] = "unknown"
    output = tmp_path / "output"
    with pytest.raises(ValueError): importer.import_export(write_export(tmp_path, signed_cases), output)
    assert not output.exists()


def test_import_refuses_to_mix_previous_run(tmp_path, signed_cases):
    importer = importlib.import_module("import_cases")
    output = tmp_path / "output"
    importer.import_export(write_export(tmp_path, signed_cases), output)
    before = (output / "eval/questions.jsonl").read_bytes()
    with pytest.raises(ValueError): importer.import_export(write_export(tmp_path, signed_cases), output)
    assert (output / "eval/questions.jsonl").read_bytes() == before


def test_brief_seed_dry_run_has_only_predecision_fields(seed):
    brief = importlib.import_module("run_brief")
    result = brief.run_case(seed, dry_run=True)
    payload = json.loads(result[1]["content"])
    assert set(payload) == {"decision_time", "identity"}
    assert payload["identity"] == {"unit_service": "Vacuum distillation column, wash section"}
    assert payload["decision_time"]["observations"][1]["value_units_basis"] == "18 kPa (differential, DCS)"
    assert "hindsight" not in result[1]["content"]


@pytest.mark.parametrize("leak", ["hindsight", "reference_answer", "extra_field", "system"])
def test_runtime_leak_assertion_runs_before_model_call(signed_cases, monkeypatch, leak):
    brief = importlib.import_module("run_brief")
    case = signed_cases[0]
    if leak == "hindsight":
        case["decision_time"]["b1_trigger"] += " " + case["hindsight"]["b8_turning_point"]
    elif leak == "reference_answer":
        case["decision_time"]["b2_operating_context"] += " " + case["questions"][0]["reference_answer"]
    else:
        original = brief.build_messages
        def corrupted(record):
            messages = original(record)
            if leak == "system": messages[0]["content"] += record["hindsight"]["b8_turning_point"]
            else:
                payload = json.loads(messages[1]["content"])
                payload["questions"] = record["questions"]
                messages[1]["content"] = json.dumps(payload)
            return messages
        monkeypatch.setattr(brief, "build_messages", corrupted)
    def no_call(*a, **k): pytest.fail("leaked input reached model transport")
    with pytest.raises(AssertionError, match="leak"):
        brief.run_case(case, chat_fn=no_call)


def test_live_call_receives_guarded_payload(signed_cases):
    brief = importlib.import_module("run_brief")
    sent = []
    def fake_chat(messages, **kwargs):
        sent.append((messages, kwargs))
        return "synthetic result"
    assert brief.run_case(signed_cases[0], chat_fn=fake_chat) == "synthetic result"
    assert set(json.loads(sent[0][0][1]["content"])) == {"decision_time", "identity"}
    assert sent[0][1]["think"] is False


def test_validator_cli_seed_valid_but_not_training():
    command = [sys.executable, str(PACK / "scripts/validate_cases.py"), str(PACK / "tests/fixtures/SYN-001.json")]
    assert subprocess.run(command, capture_output=True).returncode == 0
    rejected = subprocess.run(command + ["--purpose", "training"], capture_output=True, text=True)
    assert rejected.returncode == 2
    assert "reference_only" in rejected.stderr


def test_run_brief_cli_dry_run_needs_no_foundry_or_model():
    result = subprocess.run([sys.executable, str(PACK / "run_brief.py"),
                             str(PACK / "tests/fixtures/SYN-001.json"), "--dry-run"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "hindsight" not in json.loads(result.stdout)[1]["content"]
