"""Fixed arithmetic vectors; these are software fixtures, not engineer acceptance."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def checker():
    path = Path(__file__).resolve().parents[1] / "scripts/synthetic_checks.py"
    assert path.exists(), "SD-04 calculation checker is not implemented"
    spec = importlib.util.spec_from_file_location("synthetic_checks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(suction="30", discharge="60", result="2"):
    return ({"suction": {"value": suction, "unit": "bar", "basis": "absolute"},
             "discharge": {"value": discharge, "unit": "bar", "basis": "absolute"}},
            {"quantity": "pressure_ratio", "value": result, "unit": "1"})


@pytest.mark.parametrize("suction,discharge,result,status", [
    ("30", "60", "2", "pass"), ("30", "60", "0.5", "fail"),
    ("0", "60", "2", "fail"), ("-1", "60", "2", "fail"),
    ("30", "0", "0", "fail"), ("0.1", "0.3", "3", "pass"),
    ("60", "30", "0.5", "pass"), ("7", "21", "3", "pass"),
    ("30", "60", "2.000001", "pass"), ("30", "60", "2.000003", "fail"),
    ("1000000000000", "0.000000000001", "0", "fail"),
    ("1000000000000", "0.000000000001", "-0.000000000001", "fail"),
])
def test_independent_fixed_vectors(suction, discharge, result, status):
    givens, proposed = inputs(suction, discharge, result)
    check = checker().check_calculation("absolute_pressure_ratio_v1", givens, proposed)
    assert set(check) == {"status", "evidence", "limitation"}
    assert check["status"] == status
    assert check["evidence"] and "review" in check["limitation"].lower()


@pytest.mark.parametrize("mutation", ["gauge", "unknown_basis", "mixed_unit", "unknown_unit", "power", "result_unit"])
def test_unsupported_basis_units_and_target_never_pass(mutation):
    givens, proposed = inputs()
    if mutation == "gauge": givens["suction"]["basis"] = "gauge"
    elif mutation == "unknown_basis": givens["suction"]["basis"] = "unknown"
    elif mutation == "mixed_unit": givens["discharge"]["unit"] = "kPa"
    elif mutation == "unknown_unit": givens["suction"]["unit"] = "barg"
    elif mutation == "power": proposed.update(quantity="power", unit="kW")
    else: proposed["unit"] = "bar"
    module = checker()
    result = module.build_calculation_artifact("absolute_pressure_ratio_v1", givens, proposed)
    assert result["check"]["status"] == "needs_review"
    assert result["calculation"] is None
    assert result["training_approved"] is False


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "1e999999", "1e-999999", "unknown", True, None, 30, "30 bar", "9" * 50])
def test_invalid_numbers_fail_without_echoing_input(bad):
    givens, proposed = inputs(suction=bad)
    result = checker().check_calculation("absolute_pressure_ratio_v1", givens, proposed)
    assert result["status"] == "fail"
    assert result["evidence"] == ["invalid_decimal_input"]


@pytest.mark.parametrize("mutation", ["missing", "extra", "basis_missing", "bad_proposal", "tolerance_override"])
def test_unexpected_input_shape_is_rejected(mutation):
    givens, proposed = inputs()
    if mutation == "missing": del givens["suction"]
    elif mutation == "extra": givens["flow"] = "unknown"
    elif mutation == "basis_missing": del givens["suction"]["basis"]
    elif mutation == "bad_proposal": proposed = "2"
    else: proposed["tolerance"] = "999"
    assert checker().check_calculation("absolute_pressure_ratio_v1", givens, proposed)["status"] == "fail"


def test_hashed_artifact_is_deterministic_pending_and_does_not_mutate_inputs():
    givens, proposed = inputs()
    snapshot = deepcopy(givens)
    module = checker()
    artifact = module.build_calculation_artifact("absolute_pressure_ratio_v1", givens, proposed)
    assert artifact == module.build_calculation_artifact("absolute_pressure_ratio_v1", givens, proposed)
    assert givens == snapshot
    assert artifact["calculation"]["result"] == "2"
    assert artifact["calculation"]["formula"] == "discharge_absolute / suction_absolute"
    assert artifact["technical_review"]["status"] == "pending"
    assert artifact["technical_review"]["reviewer"] is None
    assert artifact["template"]["status"] == "awaiting_independent_method_review"
    assert artifact["training_approved"] is False
    body = {k: v for k, v in artifact.items() if k != "artifact_sha256"}
    assert artifact["artifact_sha256"] == hashlib.sha256(json.dumps(body, sort_keys=True,
        ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    proposed["value"] = "0.5"
    assert artifact["artifact_sha256"] != module.build_calculation_artifact("absolute_pressure_ratio_v1", givens, proposed)["artifact_sha256"]


def test_no_dynamic_template_execution():
    givens, proposed = inputs()
    assert checker().check_calculation("__import__('os')", givens, proposed)["status"] == "needs_review"
