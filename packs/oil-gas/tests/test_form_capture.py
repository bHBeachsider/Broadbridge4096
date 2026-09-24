"""DOCX intake tests use a filled copy of the actual interview guide."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys

from docx import Document
import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))
FIXTURE = PACK / "tests/fixtures/Synthetic_Filled_Interview_Guide.docx"


def parse(**kwargs):
    return importlib.import_module("case_from_form").parse_form(FIXTURE, family_id="FORM-FAMILY-001", **kwargs)


def test_filled_actual_guide_maps_every_b_item_and_part_c():
    case, questions, review = parse()
    assert case["case_id"] == "FORM-SYN-001"
    assert case["status"] == "pending_review"
    assert case["identity"]["unit_service"] == "Synthetic vacuum wash section"
    assert case["identity"]["record_type"] == "hypothetical"
    assert case["decision_time"]["b1_trigger"] == "Synthetic differential pressure increased; establish which checks are needed."
    assert case["decision_time"]["b4_observations"] == [
        {"time": "T-0", "variable_location": "Bed differential pressure", "value_units_basis": "18 kPa differential", "source": "Synthetic PDT-101", "quality": "unknown"}]
    assert case["hindsight"]["b7_hypotheses"][0]["discriminator"] == "POST-EVENT discriminating inspection"
    assert case["hindsight"]["b13_lesson_and_limits"] == "POST-EVENT lesson limited to this synthetic example."
    assert len(case["b14_evidence"]) == 5
    assert case["b14_evidence"][0]["format"] == "Synthetic drawing"
    assert len(questions) == 3
    assert questions[0]["type"] == "missing_data"
    assert questions[0]["evidence_ids"] == ["B1", "B4"]
    assert questions[0]["hard_fail_criteria"] == ["Invents a measurement", "Recommends an unverified operating change"]
    assert questions[2]["split"] == "locked_test"
    assert review["workflow"]["A1"] == "Synthetic workflow: collect facts, check instruments, compare mechanisms."
    assert review["consent"]["reviewer_signature"] == "SYNTHETIC REVIEWER ONLY / 2026-09-24"
    assert review["empty_boxes"] == []
    assert case["questions"] == questions


def test_empty_box_is_null_and_flagged_not_invented(tmp_path):
    document = Document(FIXTURE)
    for table in document.tables:
        if table.cell(0, 0).text.startswith("Synthetic differential pressure"):
            table.cell(0, 0).text = ""
            break
    path = tmp_path / "empty.docx"
    document.save(path)
    module = importlib.import_module("case_from_form")
    case, _, review = module.parse_form(path, family_id="FORM-FAMILY-001")
    assert case["decision_time"]["b1_trigger"] is None
    assert "decision_time.b1_trigger" in review["empty_boxes"]
    assert case["status"] == "pending_review"
    with pytest.raises(ValueError, match="empty"):
        module.parse_form(path, family_id="FORM-FAMILY-001", case_signed_off=True)


def test_explicit_unknown_is_preserved_without_empty_flag(tmp_path):
    document = Document(FIXTURE)
    for table in document.tables:
        if table.cell(0, 0).text.startswith("Synthetic differential pressure"):
            table.cell(0, 0).text = "Unknown"
            break
    path = tmp_path / "unknown.docx"
    document.save(path)
    case, _, review = importlib.import_module("case_from_form").parse_form(path, family_id="FORM-FAMILY-001")
    assert case["decision_time"]["b1_trigger"] == "unknown"
    assert "decision_time.b1_trigger" not in review["empty_boxes"]


def test_signatures_do_not_automatically_approve_case():
    case, _, _ = parse()
    assert case["reviewer_signoff"]["signed"] is False
    signed, _, _ = parse(case_signed_off=True)
    assert signed["status"] == "signed"
    assert signed["reviewer_signoff"]["signed"] is True
    assert signed["reviewer_signoff"]["approval_basis"] == "operator_attestation"


@pytest.mark.parametrize("missing", ["case_id", "signature", "decision", "reference", "criteria", "family"])
def test_hand_edited_signed_form_cannot_bypass_completeness(missing):
    module = importlib.import_module("form_contract")
    case, _, _ = parse(case_signed_off=True)
    for question in case["questions"]: question["split"] = "train"
    if missing == "case_id": case["case_id"] = None
    if missing == "signature": case["reviewer_signoff"]["reviewer_signature"] = "  "
    if missing == "decision": case["decision_time"]["b1_trigger"] = None
    if missing == "reference": case["questions"][0]["reference_answer"] = None
    if missing == "criteria": case["questions"][0]["hard_fail_criteria"] = []
    if missing == "family": case["family_id"] = " unknown "
    with pytest.raises(ValueError): module.validate_form_case(case, training=True)


def test_missing_family_is_pending_and_cannot_be_signed():
    module = importlib.import_module("case_from_form")
    case, _, review = module.parse_form(FIXTURE)
    assert case["family_id"] is None
    assert "family_id" in review["empty_boxes"]
    with pytest.raises(ValueError, match="empty"):
        module.parse_form(FIXTURE, case_signed_off=True)


def test_unknown_captured_scalars_validate_even_in_enums():
    module = importlib.import_module("form_contract")
    case, _, _ = parse()
    def unknowns(value):
        if isinstance(value, str) or value is None: return "unknown"
        if isinstance(value, list): return [unknowns(v) for v in value]
        if isinstance(value, dict): return {k: unknowns(v) for k, v in value.items()}
        return value
    case["identity"] = unknowns(case["identity"])
    case["decision_time"] = unknowns(case["decision_time"])
    case["hindsight"] = unknowns(case["hindsight"])
    case["b14_evidence"] = unknowns(case["b14_evidence"])
    case["questions"] = unknowns(case["questions"])
    module.validate_form_case(case)


@pytest.mark.parametrize("change", ["b_missing", "unknown_key", "wrong_enum", "criteria_string", "observations_object"])
def test_form_schema_rejects_shape_drift(change):
    module = importlib.import_module("form_contract")
    case, _, _ = parse()
    if change == "b_missing": del case["hindsight"]["b13_lesson_and_limits"]
    if change == "unknown_key": case["decision_time"]["hindsight"] = "bad"
    if change == "wrong_enum": case["questions"][0]["type"] = "invented"
    if change == "criteria_string": case["questions"][0]["hard_fail_criteria"] = "bad"
    if change == "observations_object": case["decision_time"]["b4_observations"] = {}
    with pytest.raises(ValueError): module.validate_form_case(case)


def test_prompt_from_form_uses_only_decision_time_and_service():
    brief = importlib.import_module("run_brief")
    case, _, _ = parse()
    messages = brief.run_case(case, dry_run=True)
    payload = json.loads(messages[1]["content"])
    assert set(payload) == {"identity", "decision_time"}
    assert payload["identity"] == {"unit_service": "Synthetic vacuum wash section"}
    assert "POST-EVENT" not in str(messages)
    assert "SCORING ANSWER" not in str(messages)
    assert "b14_evidence" not in str(messages)
    assert "SYNTHETIC REVIEWER" not in str(messages)


def test_unknown_is_not_misclassified_as_retrospective_leak():
    brief = importlib.import_module("run_brief")
    case, _, _ = parse()
    case["decision_time"]["b6_distrusted_or_missing"] = "unknown"
    case["hindsight"]["b11_confidence"] = "unknown"
    case["questions"][0]["reference_answer"] = "unknown"
    brief.run_case(case, dry_run=True)


def test_real_hindsight_leak_in_form_is_blocked():
    brief = importlib.import_module("run_brief")
    case, _, _ = parse()
    case["decision_time"]["b2_operating_context"] = case["hindsight"]["b8_turning_point"]
    with pytest.raises(AssertionError, match="leak"):
        brief.run_case(case, dry_run=True)


def test_import_cli_outputs_schema_valid_records_and_brief_accepts_file(tmp_path):
    result = subprocess.run([sys.executable, str(PACK / "scripts/case_from_form.py"), str(FIXTURE),
        str(tmp_path / "parsed"), "--family-id", "FORM-FAMILY-001", "--case-signed-off"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = tmp_path / "parsed"
    case = json.loads((output / "case_record.json").read_text(encoding="utf-8"))
    questions = json.loads((output / "eval_questions.json").read_text(encoding="utf-8"))
    assert case["status"] == "signed"
    assert len(questions) == 3
    module = importlib.import_module("form_contract")
    module.validate_form_case(case)
    for question in questions: module.validate_question(question)
    result = subprocess.run([sys.executable, str(PACK / "run_brief.py"),
        str(output / "case_record.json"), "--dry-run"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "POST-EVENT" not in str(json.loads(result.stdout))


def test_parser_rejects_duplicate_case_sections_and_unknown_layout(tmp_path):
    module = importlib.import_module("case_from_form")
    doc = Document(FIXTURE)
    identity = next(t for t in doc.tables if len(t.rows) > 1 and t.cell(1, 0).text == "Case ID (Brad assigns)")
    doc.element.body.insert(-1, copy.deepcopy(identity._element))
    path = tmp_path / "duplicate.docx"
    doc.save(path)
    with pytest.raises(ValueError): module.parse_form(path)
    doc = Document()
    doc.add_paragraph("Unrelated document")
    path = tmp_path / "unrelated.docx"
    doc.save(path)
    with pytest.raises(ValueError): module.parse_form(path)
