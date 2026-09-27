"""Offline SD-04 arithmetic checks. A pass never grants engineering acceptance."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re

TEMPLATE_ID = "absolute_pressure_ratio_v1"
LIMITATION = ("Arithmetic/basis check only. Method, tolerance and applicability require independent "
              "engineering review. This ratio establishes neither compressor power nor sizing; "
              "source rights, answer review and training admission remain separate.")
TEMPLATE = {
    "id": TEMPLATE_ID, "version": "1", "status": "awaiting_independent_method_review",
    "absolute_tolerance": "0.000000001", "relative_tolerance": "0.000001",
    "tolerance_rule": "max(absolute_tolerance, abs(expected) * relative_tolerance)",
    "units": ["Pa", "kPa", "MPa", "bar", "psi"],
    "scope": "Positive absolute pressures in the same explicit unit; no unit or gauge conversion.",
    "numeric_limits": "Decimal strings, <=28 significant digits and adjusted exponent -12..12; computational bounds only.",
}


def _decimal(value):
    if (not isinstance(value, str) or len(value) > 40
            or not re.fullmatch(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d{1,2})?", value)):
        raise ValueError("invalid_decimal_input")
    result = Decimal(value)
    if not result.is_finite() or len(result.as_tuple().digits) > 28 or not -12 <= result.adjusted() <= 12:
        raise ValueError("invalid_decimal_input")
    return result


def _check(status, *evidence):
    return {"status": status, "evidence": list(evidence), "limitation": LIMITATION}


def _evaluate(template_id, givens, proposed_result):
    if template_id != TEMPLATE_ID:
        return _check("needs_review", "unsupported_calculation_template"), None
    if (not isinstance(givens, dict) or set(givens) != {"suction", "discharge"}
            or any(not isinstance(p, dict) or set(p) != {"value", "unit", "basis"} for p in givens.values())
            or not isinstance(proposed_result, dict) or set(proposed_result) != {"quantity", "value", "unit"}):
        return _check("fail", "invalid_calculation_shape"), None
    try:
        suction, discharge = (_decimal(givens[k]["value"]) for k in ("suction", "discharge"))
        proposed = _decimal(proposed_result["value"])
    except (ValueError, InvalidOperation):
        return _check("fail", "invalid_decimal_input"), None
    if min(suction, discharge) <= 0:
        return _check("fail", "pressures_must_be_positive"), None
    if any(p["basis"] != "absolute" for p in givens.values()):
        return _check("needs_review", "explicit_absolute_basis_required_no_implicit_conversion"), None
    if (any(p["unit"] not in TEMPLATE["units"] for p in givens.values())
            or givens["suction"]["unit"] != givens["discharge"]["unit"]):
        return _check("needs_review", "same_supported_unit_required_no_implicit_conversion"), None
    if proposed_result["quantity"] != "pressure_ratio" or proposed_result["unit"] != "1":
        return _check("needs_review", "only_dimensionless_pressure_ratio_is_supported"), None
    if proposed <= 0:
        return _check("fail", "pressure_ratio_must_be_positive_even_within_tolerance"), None
    with localcontext() as ctx:
        ctx.prec = 50
        result = discharge / suction
        tolerance = max(Decimal(TEMPLATE["absolute_tolerance"]), abs(result) * Decimal(TEMPLATE["relative_tolerance"]))
        error = abs(proposed - result)
        calculation = {"formula": "discharge_absolute / suction_absolute", "method": "decimal_division_precision_50",
            "result": str(result), "unit": "1", "absolute_error": str(error), "allowed_error": str(tolerance)}
        check = _check("pass" if error <= tolerance else "fail",
                       f"computed_ratio={result}; absolute_error={error}; allowed_error={tolerance}")
    return check, calculation


def check_calculation(template_id, givens, proposed_result):
    """Return Foundry SD-02's status/evidence/limitation shape, with no side effects."""
    return _evaluate(template_id, givens, proposed_result)[0]


def build_calculation_artifact(template_id, givens, proposed_result):
    """Bind explicit JSON inputs, method and result; not a quotation or signed approval."""
    check, calculation = _evaluate(template_id, givens, proposed_result)
    body = {"schema": "broadbridge.calculation_artifact/1",
        "requested_template_id": template_id, "template": deepcopy(TEMPLATE) if template_id == TEMPLATE_ID else None,
        "givens": deepcopy(givens), "proposed_result": deepcopy(proposed_result),
        "calculation": calculation, "check": check,
        "technical_review": {"status": "pending", "reviewer": None, "reviewed_at": None},
        "training_approved": False}
    encoded = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {**body, "artifact_sha256": hashlib.sha256(encoded).hexdigest()}
