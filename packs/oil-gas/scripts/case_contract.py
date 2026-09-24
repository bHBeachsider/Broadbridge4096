"""Offline validation and admission policy for the live Case Capture contract."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

PACK = Path(__file__).resolve().parents[1]
SCHEMAS = PACK / "schemas"


def read_json(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError(f"Non-JSON numeric constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique_object, parse_constant=invalid_constant)


def validator(name):
    case = read_json(SCHEMAS / "case_record.schema.json")
    export = read_json(SCHEMAS / "export.schema.json")
    registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in (case, export)])
    schema = case if name == "case" else export
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry)


def _validate(value, name):
    errors = sorted(validator(name).iter_errors(value), key=lambda e: str(list(e.absolute_path)))
    if errors:
        details = "; ".join(f"{'.'.join(map(str, e.absolute_path)) or name}: {e.message}" for e in errors)
        raise ValueError(details)


def disposition(case):
    """Latest user policy: draft/reference records may be evaluation material."""
    permission = case["identity"]["permitted_use"]
    if permission == "undecided":
        return "rejected", "permitted_use=undecided; no dataset permission"
    signoff = case["reviewer_signoff"]
    if case["status"] == "signed" and (not signoff["signed"] or not signoff["name"].strip() or not signoff["date"].strip()):
        return "rejected", "status=signed conflicts with incomplete reviewer_signoff"
    if case["status"] != "signed" or permission != "training":
        return "eval-only", f"status={case['status']}; permitted_use={permission}; excluded from training"
    return "imported", "signed; permitted_use=training; subject to family split"


def validate_case(case, *, training=False):
    if isinstance(case, dict) and case.get("schema") == "broadbridge.case_form/1":
        from form_contract import validate_form_case
        return validate_form_case(case, training=training)
    _validate(case, "case")
    if training:
        state, reason = disposition(case)
        if state != "imported":
            raise ValueError(f"{case['case_id']}: {reason}")
        if not case["questions"] or any(q["split"] != "train" for q in case["questions"]):
            raise ValueError(f"{case['case_id']}: training requires questions with split=train; validate the complete export for family closure")


def validate_export(export):
    _validate(export, "export")
