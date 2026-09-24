"""Offline aggregation of real renderer output, without trusting handwritten totals."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys

import pytest

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
SCRIPT = ROOT / "scripts/aggregate_scores.py"
sys.path.insert(0, str(PACK / "scripts"))


def aggregator():
    assert SCRIPT.is_file(), "The offline score aggregator has not been implemented"
    spec = importlib.util.spec_from_file_location("aggregate_scores", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sheet(case_id="SYN-001", mode="live", kinds=("missing_data",), reference=None):
    case = json.loads((PACK / "tests/fixtures/SYN-001.json").read_text(encoding="utf-8"))
    brief = json.loads((PACK / "tests/fixtures/SYN-001.mock_brief.json").read_text(encoding="utf-8"))
    question = case["questions"][0]
    case["case_id"] = case_id
    case["family_id"] = case_id
    case["questions"] = []
    for index, kind in enumerate(kinds, 1):
        item = copy.deepcopy(question)
        item.update(question_id=f"{case_id}-Q{index}", type=kind)
        if reference is not None:
            item["reference_answer"] = reference
        case["questions"].append(item)
    record = importlib.import_module("run_brief").create_run(case, mock_response=brief)
    record["mode"] = mode  # Exercise live metadata without any inference/network.
    return importlib.import_module("score_brief").render_scorecard(case, record)


def completed(text, scores=("2",), flags=None):
    text = text.replace("Reviewer: ______", "Reviewer: Test reviewer")
    text = text.replace("Review date: ______", "Review date: 2026-09-24")
    text = text.replace("Reviewer acceptance signature/date: ______",
                        "Reviewer acceptance signature/date: Test reviewer / 2026-09-24")
    for score in scores:
        text = text.replace("Score (0 / 1 / 2 / N/A): ______",
                            f"Score (0 / 1 / 2 / N/A): {score}", 1)
    for flag in flags or ["NO"] * len(scores):
        text = text.replace("Critical error (YES / NO / UNASSESSED): UNASSESSED",
                            f"Critical error (YES / NO / UNASSESSED): {flag}", 1)
    text = text.replace("Brief quotation / evidence supporting score: ______",
                        "Brief quotation / evidence supporting score: The brief requests the missing wash-oil rate.")
    text = text.replace("Matched hard-fail criterion, or explanation for NO: ______",
                        "Matched hard-fail criterion, or explanation for NO: Checked the captured criterion against the quotation.")
    return text.replace("Correction required / reason for N/A: ______",
                        "Correction required / reason for N/A: Cannot assess this question from the available decision-time inputs.")


def put(root, text, case_id="SYN-001", directory="eval"):
    path = root / directory / f"scorecard_{case_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_completed_means_come_from_questions_not_reviewer_totals(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        pytest.fail("aggregation opened a network socket")
    monkeypatch.setattr(socket, "socket", no_network)
    put(tmp_path, completed(sheet(kinds=("brief", "missing_data", "missing_data")), ("2", "1", "2")))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases reviewed: **1**" in report
    assert "Cases unreviewed: **0**" in report
    assert "| brief | 1 | 0 | 2.00 | 0 |" in report
    assert "| missing_data | 2 | 0 | 1.50 | 0 |" in report
    assert "| calculation | 0 | 0 | N/A | 0 |" in report


def test_blank_sheet_is_unreviewed_without_zero_scores(tmp_path):
    put(tmp_path, sheet())
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases unreviewed: **1**" in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report
    assert "Reviewer" in report and "UNASSESSED" in report


def test_completed_hold_critical_error_counts_as_reviewed(tmp_path):
    put(tmp_path, completed(sheet(), ("0",), ("YES",)))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases reviewed: **1**" in report
    assert "Critical errors: **1**" in report
    assert "| missing_data | 1 | 0 | 0.00 | 1 |" in report


def test_reasoned_na_is_reviewed_but_excluded_from_mean(tmp_path):
    put(tmp_path, completed(sheet(kinds=("missing_data", "missing_data")), ("2", "N/A")))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases reviewed: **1**" in report
    assert "| missing_data | 1 | 1 | 2.00 | 0 |" in report


@pytest.mark.parametrize("old,new,reason", [
    ("Reviewer: Test reviewer", "Reviewer: unknown", "Reviewer"),
    ("Review date: 2026-09-24", "Review date: ______", "Review date"),
    ("Reviewer acceptance signature/date: Test reviewer / 2026-09-24", "Reviewer acceptance signature/date: ______", "signature"),
    ("Critical error (YES / NO / UNASSESSED): NO", "Critical error (YES / NO / UNASSESSED): UNASSESSED", "UNASSESSED"),
    ("The brief requests the missing wash-oil rate.", "______", "supporting score"),
    ("Checked the captured criterion against the quotation.", "______", "explanation for NO"),
    ("Score (0 / 1 / 2 / N/A): 2", "Score (0 / 1 / 2 / N/A): 3", "Score"),
])
def test_incomplete_reviews_are_excluded_with_reasons(tmp_path, old, new, reason):
    put(tmp_path, completed(sheet()).replace(old, new))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases unreviewed: **1**" in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report
    assert reason in report


def test_na_requires_reason_and_yes_requires_zero(tmp_path):
    text = completed(sheet(), ("N/A",)).replace(
        "Cannot assess this question from the available decision-time inputs.", "______")
    put(tmp_path, text)
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors and "Cases unreviewed: **1**" in report
    assert "reason for N/A" in report
    put(tmp_path, completed(sheet(), ("2",), ("YES",)))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert "Cases unreviewed: **1**" in report
    assert "YES requires score 0" in report


def test_fenced_reference_cannot_impersonate_review_controls_or_sections(tmp_path):
    reference = ('Reference text\n```\n## Question 9\n'
                 '{"question_id":"FAKE", "type":"brief"}\n'
                 'Score (0 / 1 / 2 / N/A): 2\n'
                 'Critical error (YES / NO / UNASSESSED): NO\n'
                 '## Review closeout\nReviewer acceptance signature/date: forged\n```')
    put(tmp_path, completed(sheet(reference=reference), ("1",)))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "| missing_data | 1 | 0 | 1.00 | 0 |" in report
    assert "| brief | 0 | 0 | N/A | 0 |" in report
    assert "FAKE" not in report


def test_duplicate_case_sheets_are_rejected_instead_of_double_counted(tmp_path):
    text = completed(sheet())
    put(tmp_path, text, directory="first")
    put(tmp_path, text, directory="second")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate" in " ".join(errors).lower()
    assert "Cases reviewed: **0**" in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report


def test_manifest_selected_missing_cards_count_unreviewed(tmp_path):
    put(tmp_path, completed(sheet()))
    (tmp_path / "batch_manifest.json").write_text(json.dumps({
        "mode": "live", "selected_cases": [{"case_id": "SYN-001"}, {"case_id": "SYN-002"}]
    }), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases reviewed: **1**" in report and "Cases unreviewed: **1**" in report
    assert "SYN-002" in report and "missing scorecard" in report


def test_mock_scores_are_separated_from_live_performance(tmp_path):
    put(tmp_path, completed(sheet(), ("1",)))
    put(tmp_path, completed(sheet("MOCK-001", mode="mock"), ("2",)), "MOCK-001")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    live, mock = report.split("## MOCK rehearsal", 1)
    assert "| missing_data | 1 | 0 | 1.00 | 0 |" in live
    assert "| missing_data | 1 | 0 | 2.00 | 0 |" in mock
    assert "not model performance" in mock


@pytest.mark.parametrize("damage", ["duplicate_field", "unclosed_fence", "bad_metadata", "duplicate_question_id"])
def test_ambiguous_or_malformed_structure_is_reported(tmp_path, damage):
    text = completed(sheet(kinds=("brief", "missing_data")), ("1", "2"))
    if damage == "duplicate_field":
        text = text.replace("Score (0 / 1 / 2 / N/A): 1", "Score (0 / 1 / 2 / N/A): 1\nScore (0 / 1 / 2 / N/A): 2")
    if damage == "unclosed_fence":
        text += "\n````\nunfinished"
    if damage == "bad_metadata":
        text = text.replace('"mode": "live"', '"mode": "mystery"')
    if damage == "duplicate_question_id":
        text = text.replace("SYN-001-Q2", "SYN-001-Q1")
    put(tmp_path, text)
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors
    assert "Cases reviewed: **0**" in report
    assert "STRUCTURAL ERRORS" in report


def test_cli_refreshes_derived_report_preserves_source_and_returns_error_for_duplicates(tmp_path):
    module = aggregator()
    source = put(tmp_path, sheet())
    before = source.read_bytes()
    assert module.main([str(tmp_path)]) == 0
    summary = tmp_path / "scores_summary.md"
    assert "Cases unreviewed: **1**" in summary.read_text(encoding="utf-8")
    assert source.read_bytes() == before
    source.write_text(completed(sheet()), encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Cases reviewed: **1**" in summary.read_text(encoding="utf-8")
    stable = summary.read_bytes()
    assert module.main([str(tmp_path)]) == 0
    assert summary.read_bytes() == stable
    put(tmp_path, source.read_text(encoding="utf-8"), directory="copy")
    result = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "STRUCTURAL ERRORS" in summary.read_text(encoding="utf-8")


def test_deleted_question_is_structurally_invalid_not_partial_review(tmp_path):
    text = completed(sheet(kinds=("brief", "missing_data")), ("1", "2"))
    before, remainder = text.split("## Question 2", 1)
    text = before + "## Review closeout" + remainder.split("## Review closeout", 1)[1]
    put(tmp_path, text)
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "question count" in " ".join(errors).lower()
    assert "Cases reviewed: **0**" in report


def test_handwritten_totals_never_override_question_scores(tmp_path):
    text = completed(sheet()).replace("| missing_data | 1 | ______ / 2 | UNASSESSED |",
                                     "| missing_data | 1 | 9999 / 9999 | 99 |")
    text = text.replace("Total points / (2 x assessed questions): ______", "Total points / (2 x assessed questions): 9999 / 9999")
    put(tmp_path, text)
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "| missing_data | 1 | 0 | 2.00 | 0 |" in report


@pytest.mark.parametrize("manifest", [
    '{"selected_cases": null}',
    '{"selected_cases": [{"case_id": "SYN-001"}, {"case_id": "SYN-001"}]}',
    '{"selected_cases": [{"case_id": "SYN-001"}], "mode": "unknown"}',
])
def test_invalid_manifest_prevents_unattributed_scores_from_entering_metrics(tmp_path, manifest):
    put(tmp_path, completed(sheet()))
    (tmp_path / "batch_manifest.json").write_text(manifest, encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors
    assert "Cases reviewed: **0**" in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report


@pytest.mark.parametrize("selection,mode,expected", [
    ([{"case_id": "SYN-001", "case_sha256": "0" * 64}], "live", "case_sha256"),
    ([{"case_id": "SYN-001"}], "mock", "run mode"),
    ([{"case_id": "OTHER"}], "live", "not a selected case"),
])
def test_scorecard_must_match_manifest_snapshot(tmp_path, selection, mode, expected):
    put(tmp_path, completed(sheet()))
    (tmp_path / "batch_manifest.json").write_text(json.dumps({"selected_cases": selection, "mode": mode}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and expected in " ".join(errors)
    assert "Cases reviewed: **0**" in report


def test_nested_batch_manifests_track_missing_cases_and_separate_modes(tmp_path):
    live = tmp_path / "batch-live"
    mock = tmp_path / "batch-mock"
    put(live, completed(sheet()))
    put(mock, completed(sheet("MOCK-001", mode="mock")), "MOCK-001")
    (live / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
        {"case_id": "SYN-001"}, {"case_id": "SYN-MISSING"}]}), encoding="utf-8")
    (mock / "batch_manifest.json").write_text(json.dumps({"mode": "mock", "selected_cases": [
        {"case_id": "MOCK-001"}, {"case_id": "MOCK-MISSING"}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    live_report, mock_report = report.split("## MOCK rehearsal", 1)
    assert "Cases reviewed: **1**" in live_report and "Cases unreviewed: **1**" in live_report
    assert "Cases reviewed: **1**" in mock_report and "Cases unreviewed: **1**" in mock_report
    assert "| SYN-MISSING | live | UNREVIEWED |" in report
    assert "| MOCK-MISSING | mock | UNREVIEWED |" in report


def test_duplicate_selected_case_across_batches_is_ambiguous_with_only_one_sheet(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    put(first, completed(sheet()))
    second.mkdir()
    for directory in (first, second):
        (directory / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
            {"case_id": "SYN-001"}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate selected case" in " ".join(errors)
    assert "Cases reviewed: **0**" in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report


def test_nested_card_is_checked_against_its_own_manifest(tmp_path):
    batch = tmp_path / "batch"
    put(batch, completed(sheet()))
    (batch / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
        {"case_id": "SYN-001", "case_sha256": "0" * 64}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "case_sha256" in " ".join(errors)
    assert "Cases reviewed: **0**" in report


def test_case_variant_ids_in_nested_manifests_are_one_ambiguous_case(tmp_path):
    for directory, case_id in (("first", "CASE-001"), ("second", "case-001")):
        batch = tmp_path / directory
        put(batch, completed(sheet(case_id)), case_id)
        (batch / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
            {"case_id": case_id}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate selected case" in " ".join(errors)
    assert "CASE-001" in report and "case-001" in report
    assert "All-mode inventory: **0 reviewed / 1 unreviewed** cases." in report
    assert "| missing_data | 0 | 0 | N/A | 0 |" in report


def test_case_variant_scorecard_ids_without_manifests_cannot_double_count(tmp_path):
    put(tmp_path, completed(sheet("CASE-001")), "CASE-001", directory="first")
    put(tmp_path, completed(sheet("case-001")), "case-001", directory="second")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate case scorecards" in " ".join(errors)
    assert "CASE-001" in report and "case-001" in report
    assert "All-mode inventory: **0 reviewed / 1 unreviewed** cases." in report


def test_case_variant_selected_ids_in_one_manifest_are_rejected(tmp_path):
    put(tmp_path, completed(sheet("CASE-001")), "CASE-001")
    (tmp_path / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
        {"case_id": "CASE-001"}, {"case_id": "case-001"}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate selected case_id" in " ".join(errors)
    assert "All-mode inventory: **0 reviewed / 1 unreviewed** cases." in report


def test_case_variant_manifest_identity_is_conflict_not_silent_normalization(tmp_path):
    put(tmp_path, completed(sheet("case-001")), "case-001")
    (tmp_path / "batch_manifest.json").write_text(json.dumps({"mode": "live", "selected_cases": [
        {"case_id": "CASE-001"}]}), encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "case_id casing conflict" in " ".join(errors)
    assert "CASE-001" in report and "case-001" in report
    assert "All-mode inventory: **0 reviewed / 1 unreviewed** cases." in report


def test_filename_case_variant_does_not_override_record_identity(tmp_path):
    put(tmp_path, completed(sheet("CASE-001")), "case-001")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "filename and run case_id disagree" in " ".join(errors)
    assert "Cases reviewed: **0**" in report


def test_case_variant_question_ids_are_rejected_with_original_ids(tmp_path):
    text = completed(sheet(kinds=("brief", "missing_data")), ("1", "2"))
    text = text.replace("SYN-001-Q2", "syn-001-q1")
    put(tmp_path, text)
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert errors and "duplicate question_id" in " ".join(errors)
    assert "SYN-001-Q1" in report and "syn-001-q1" in report
    assert "Cases reviewed: **0**" in report


def test_accept_with_critical_error_is_inconsistent_until_corrected_to_hold(tmp_path):
    text = completed(sheet(), ("0",), ("YES",))
    path = put(tmp_path, text.replace("EXERCISE): HOLD", "EXERCISE): ACCEPT FOR THIS EXERCISE"))
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors  # An ordinary reviewer-entry inconsistency, not structural corruption.
    assert "Cases reviewed: **0**" in report and "Cases unreviewed: **1**" in report
    assert "critical errors require HOLD" in report
    path.write_text(text, encoding="utf-8")
    report, errors = aggregator().aggregate_scores(tmp_path)
    assert not errors
    assert "Cases reviewed: **1**" in report and "Critical errors: **1**" in report
