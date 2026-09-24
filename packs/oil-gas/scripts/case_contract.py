"""Offline validation and admission policy for the canonical Case Capture contract."""
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

PACK = Path(__file__).resolve().parents[1]
SCHEMAS = PACK / "schemas"


def parse_json(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError(f"Non-JSON numeric constant: {value}")
    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"JSON number exceeds finite float range: {value}")
        return result
    return json.loads(text,
                      object_pairs_hook=unique_object, parse_constant=invalid_constant,
                      parse_float=finite_float)


def read_json(path):
    return parse_json(Path(path).read_text(encoding="utf-8-sig"))


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


def complete_reviewer_signoff(signoff):
    """An unknown marker is captured text, not a reviewer's identity or date."""
    return signoff["signed"] is True and all(
        signoff[key].strip().casefold() not in ("", "unknown", "undecided") for key in ("name", "date"))


def disposition(case):
    """Classify schema-valid page records; family holdouts are applied by the importer."""
    permission = case["identity"]["permitted_use"]
    signoff = case["reviewer_signoff"]
    if any(case[key].strip().casefold() in ("", "unknown", "undecided") for key in ("case_id", "family_id")):
        return "rejected", "reviewed case_id and family_id are required"
    if case["status"] == "signed" and not complete_reviewer_signoff(signoff):
        return "rejected", "status=signed conflicts with incomplete reviewer_signoff"
    if case["status"] != "signed" or permission != "training":
        return "eval-only", f"status={case['status']}; permitted_use={permission}; excluded from training"
    return "imported", "signed; permitted_use=training; subject to family split"


def validate_case(case, *, training=False):
    _validate(case, "case")
    if training:
        state, reason = disposition(case)
        if state != "imported":
            raise ValueError(f"{case['case_id']}: {reason}")
        if not case["questions"] or any(q["split"] != "train" for q in case["questions"]):
            raise ValueError(f"{case['case_id']}: training requires questions with split=train; validate the complete export for family closure")


def validate_export(export):
    _validate(export, "export")
