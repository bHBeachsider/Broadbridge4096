"""Form-specific schema contract; independent of the live-page JSON version."""
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from case_contract import SCHEMAS, read_json


def _check(value, name):
    schemas = {key: read_json(SCHEMAS / filename) for key, filename in
               (("case", "case_record.json"), ("question", "eval_question.json"))}
    registry = Registry().with_resources([(s["$id"], Resource.from_contents(s)) for s in schemas.values()])
    schema = schemas[name]
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, registry=registry).iter_errors(value))
    if errors:
        raise ValueError("; ".join(f"{'.'.join(map(str, e.absolute_path))}: {e.message}" for e in errors))


def validate_question(question):
    _check(question, "question")


def _empty_paths(value, path="case"):
    if value is None or (isinstance(value, str) and not value.strip()) or value == []:
        yield path
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _empty_paths(item, path + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _empty_paths(item, f"{path}[{index}]")


def _unknown(value):
    return value is None or (isinstance(value, str) and value.strip().casefold() in ("", "unknown", "undecided"))


def validate_form_case(case, *, training=False):
    _check(case, "case")
    signoff = case["reviewer_signoff"]
    if case["status"] == "signed":
        empty = list(_empty_paths(case))
        if empty:
            raise ValueError("Signed form has empty answers: " + ", ".join(empty))
        required = [case["case_id"], case["family_id"], signoff["reviewer_signature"], case["identity"]["permitted_use"]]
        if (not signoff["signed"] or signoff["approval_basis"] != "operator_attestation" or any(map(_unknown, required))):
            raise ValueError("Signed form requires known identity, family, permission, reviewer signature and explicit case approval")
    if training and (case["status"] != "signed" or case["identity"]["permitted_use"] != "training"
            or _unknown(case["family_id"]) or not case["questions"]
            or any(q["split"] != "train" for q in case["questions"])):
        raise ValueError("Training requires signed approval, training permission, family_id and all question splits=train")
