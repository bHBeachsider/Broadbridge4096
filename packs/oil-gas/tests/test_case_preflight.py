"""Offline first-case checks never confer engineering approval or call a model."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import socket
import sys

import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))
FIXTURES = PACK / "tests/fixtures"


def engine():
    return importlib.import_module("case_preflight")


@pytest.fixture
def export():
    return json.loads((FIXTURES / "three_cases_export.json").read_text())


def submitted(export):
    value = copy.deepcopy(export)
    case = value["cases"][1]
    case["case_id"] = "CASE-101"
    case["reviewer_signoff"]["name"] = "Test reviewer for unit testing"
    case["identity"]["title"] = "Unit-test case"
    case["identity"]["confidentiality"] = "internal"
    value["cases"] = [case]
    return value


def test_fixture_signatures_never_close_gate_zero(export, monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("Network forbidden"))
    report = engine().assess(export, count_tokens=lambda messages: 123)
    assert len(report["cases"]) == 3
    assert report["coverage"]["signed_nonfixture_questions"] == 0
    assert report["gate_0_verified"] is False and report["execution_authorized"] is False
    assert report["model_calls"] == 0
    assert all(row["fixture"] for row in report["cases"])


def test_valid_case_is_only_mechanically_checked(export):
    report = engine().assess(submitted(export), count_tokens=lambda messages: 123)
    row = report["cases"][0]
    assert row["issues"] == []
    assert row["context"]["status"] == "fits_local_estimate"
    assert report["coverage"]["by_type"]["missing_data"] == 1
    assert report["coverage"]["questions_needed_for_30"] == 29
    assert report["gate_0_verified"] is False
    assert report["execution_authorized"] is False


def test_thirty_complete_questions_still_do_not_grant_gate_zero_or_run_approval(export):
    data = submitted(export)
    base = data["cases"][0]["questions"][0]
    questions = []
    for i in range(30):
        q = copy.deepcopy(base)
        q.update(question_id=f"Q-{i}", type=list(engine().RUBRICS)[i % 5],
                 tolerance="Reviewer must check this fixture tolerance", evidence_ids="B1")
        questions.append(q)
    data["cases"][0]["questions"] = questions
    report = engine().assess(data)
    assert report["coverage"]["signed_nonfixture_questions"] == 30
    assert report["coverage"]["missing_types"] == []
    assert report["gate_0_verified"] is False and report["execution_authorized"] is False
    report = engine().assess(data, fixture_export=True)
    assert report["coverage"]["signed_nonfixture_questions"] == 0


@pytest.mark.parametrize("field,kind", [("reference_answer", "missing_data"), ("hard_fail_criteria", "missing_data"), ("tolerance", "calculation"), ("evidence_ids", "grounded_explanation")])
def test_unknown_scoring_input_flagged(export, field, kind):
    data = submitted(export)
    q = data["cases"][0]["questions"][0]
    q["type"] = kind
    q[field] = "unknown"
    report = engine().assess(data)
    assert f"question:{q['question_id']}:{field}_missing" in report["cases"][0]["issues"]
    assert report["coverage"]["signed_nonfixture_questions"] == 0


def test_hindsight_leak_prevents_tokenizer_call_and_does_not_print_content(export):
    data = submitted(export)
    secret = "RETROSPECTIVE-SENTINEL-SECRET"
    data["cases"][0]["hindsight"]["b8_turning_point"] = secret
    data["cases"][0]["decision_time"]["b1_trigger"] += secret
    report = engine().assess(data, count_tokens=lambda messages: pytest.fail("Leaked prompt tokenized"))
    assert "prompt_leak" in report["cases"][0]["issues"]
    assert secret not in json.dumps(report)


def test_reference_answers_never_reach_token_counter(export):
    data = submitted(export)
    seen = []
    def counter(messages):
        seen.append(messages)
        return 200
    engine().assess(data, count_tokens=counter)
    assert len(seen) == 1
    payload = json.loads(seen[0][1]["content"])
    assert set(payload) == {"identity", "decision_time"}
    assert set(payload["identity"]) == {"unit_service"}
    assert "reference_answer" not in json.dumps(seen)


def test_context_budget_includes_answer_and_margin_without_truncating(export):
    data = submitted(export)
    before = copy.deepcopy(data)
    report = engine().assess(data, count_tokens=lambda messages: 1100,
                             context_limit=2048, output_reserve=768, margin=256)
    assert report["cases"][0]["context"]["status"] == "over_budget"
    assert data == before


def test_no_tokenizer_means_unmeasured_not_pass(export):
    report = engine().assess(submitted(export))
    assert report["cases"][0]["context"]["status"] == "not_measured"


def test_family_holdout_comes_from_whole_export_including_unsigned_case(export):
    data = submitted(export)
    other = copy.deepcopy(data["cases"][0])
    other["case_id"] = "CASE-102"
    other["status"] = "draft"
    other["reviewer_signoff"]["signed"] = False
    other["questions"][0].update(question_id="Q-OTHER", split="locked_test")
    data["cases"].append(other)
    report = engine().assess(data)
    assert all(r["effective_split"] == "locked_test" for r in report["cases"])


def test_duplicate_question_id_rejected_before_output(export, tmp_path):
    export["cases"][1]["questions"][0]["question_id"] = export["cases"][2]["questions"][0]["question_id"]
    source = tmp_path / "input.json"
    source.write_text(json.dumps(export))
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="uplicate"):
        engine().main([str(source), "--out", str(out)])
    assert not out.exists()


def test_output_is_report_only_with_no_case_text(export, tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(export))
    out = tmp_path / "out"
    assert engine().main([str(source), "--out", str(out)]) == 0
    assert {p.name for p in out.iterdir()} == {"preflight.json", "PREFLIGHT.md"}
    contents = (out / "preflight.json").read_text()
    assert export["cases"][0]["decision_time"]["b1_trigger"] not in contents
    assert "train_candidates" not in contents
    with pytest.raises(ValueError, match="new absolute"):
        engine().main([str(source), "--out", str(out)])


def test_tokenizer_template_is_explicitly_non_thinking():
    calls = []
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls.append(kwargs)
            return [1, 2, 3]
    assert engine().token_count(Tokenizer(), [{"role": "user", "content": "hello"}]) == 3
    assert calls == [{"tokenize": True, "add_generation_prompt": True, "enable_thinking": False, "return_dict": False}]


@pytest.mark.parametrize("returned", [{"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}, [[1, 2, 3]], [], "rendered text"])
def test_token_counter_refuses_nonflat_or_empty_return(returned):
    class Tokenizer:
        def apply_chat_template(self, *args, **kwargs):
            return returned
    with pytest.raises(ValueError, match="flat token"):
        engine().token_count(Tokenizer(), [])


def test_wrong_tokenizer_metadata_refused_before_import(tmp_path):
    (tmp_path / "revision.json").write_text(json.dumps({"repo": "another/model", "revision": "a"*40}))
    with pytest.raises(ValueError, match="tokenizer"):
        engine().load_token_counter(tmp_path)


@pytest.mark.parametrize("algorithm", ["sha256", "git-blob-sha1"])
def test_both_pinned_inventory_hash_formats_are_checked(algorithm):
    blob = b"test tokenizer bytes"
    expected = hashlib.sha256(blob).hexdigest() if algorithm == "sha256" else hashlib.sha1(
        f"blob {len(blob)}\0".encode() + blob).hexdigest()
    record = {"size_bytes": len(blob), "hash_algorithm": algorithm, "hash": expected}
    assert engine().artifact_matches(blob, record)
    assert not engine().artifact_matches(blob + b"changed", record)
    record["hash"] = "0" * len(expected)
    assert not engine().artifact_matches(blob, record)


def test_unknown_hash_algorithm_not_accepted():
    assert not engine().artifact_matches(b"abc", {"size_bytes": 3, "hash_algorithm": "unchecked", "hash": "abc"})
