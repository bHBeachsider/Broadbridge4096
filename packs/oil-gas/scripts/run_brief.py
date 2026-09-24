"""Render an isolated decision-time brief; inference is opt-in and tunnel-only."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from jsonschema import Draft202012Validator

from case_contract import complete_reviewer_signoff, parse_json, read_json, validate_case

SYSTEM = "Prepare an engineering decision brief from the supplied operating information. Identify uncertainty, missing measurements and discriminating checks. Do not invent facts or prescribe unverified operating changes."


def decision_payload(case):
    return {"identity": {"unit_service": case["identity"]["unit_service"]},
            "decision_time": copy.deepcopy(case["decision_time"])}


def build_messages(case):
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(decision_payload(case), ensure_ascii=False)}]


def _strings(value):
    if isinstance(value, str):
        if value.strip():
            yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def assert_no_leak(case, messages):
    # Explicit raises remain effective under python -O.
    try:
        if (len(messages) != 2 or messages[0] != {"role": "system", "content": SYSTEM}
                or set(messages[1]) != {"role", "content"} or messages[1]["role"] != "user"
                or json.loads(messages[1]["content"]) != decision_payload(case)):
            raise AssertionError("Prompt leak: only the approved decision-time projection is allowed")
    except (KeyError, TypeError, ValueError) as exc:
        raise AssertionError("Prompt leak: malformed prompt envelope") from exc
    # Check raw field strings too, so JSON escaping cannot hide a quoted/newline answer.
    haystacks = [m["content"] for m in messages] + list(_strings(decision_payload(case)))
    forbidden = list(_strings(case["hindsight"])) + [value for q in case["questions"] for value in _strings(q["reference_answer"])]
    # An explicit unknown marker carries no retrospective knowledge, regardless of intake.
    forbidden = [value for value in forbidden if value.strip().casefold() != "unknown"]
    if any(value in text for value in forbidden for text in haystacks):
        raise AssertionError("Prompt leak: a hindsight string or reference answer appears in decision-time input; review the case")


def brief_schema():
    return read_json(Path(__file__).resolve().parents[1] / "schemas/brief.schema.json")


def digest(value):
    """Hash canonical JSON, independent of file whitespace or newline style."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validate_brief(value, schema=None):
    contract = brief_schema() if schema is None else schema
    Draft202012Validator.check_schema(contract)
    errors = list(Draft202012Validator(contract).iter_errors(value))
    if errors:
        raise ValueError("Brief schema rejected response: " + "; ".join(error.message for error in errors))


def require_signed_case(case):
    validate_case(case)
    signoff = case["reviewer_signoff"]
    if (case["status"] != "signed" or not complete_reviewer_signoff(signoff)
            or case["identity"]["permitted_use"] not in ("training", "testing_only", "reference_only")
            or not case["questions"]):
        raise ValueError("First-case preflight: a signed case, complete reviewer signoff, decided permitted_use and questions are required")


def run_case(case, *, dry_run=False, chat_fn=None, foundry=None, schema=None):
    validate_case(case)
    messages = build_messages(case)
    assert_no_leak(case, messages)
    if dry_run:
        return messages
    if chat_fn is None:
        if case["identity"]["permitted_use"] in (None, "unknown", "undecided"):
            raise ValueError("Inference refused: permitted_use is unknown or undecided")
        if not foundry:
            raise ValueError("Supply --foundry /absolute/slm-foundry for inference, or use --dry-run")
        root = Path(foundry).resolve()
        if not (root / "src/llm_client.py").is_file():
            raise ValueError("--foundry must contain src/llm_client.py")
        sys.path.insert(0, str(root))
        from src.llm_policy import require_local_for_pack
        from src.llm_client import chat
        # Domain capture is confidential; never route a live request to a public endpoint.
        require_local_for_pack({"confidential": True})
        chat_fn = chat
    kwargs = {"think": False, "temperature": 0.2}
    if schema is not None:
        kwargs["schema"] = schema
    result = chat_fn(messages, **kwargs)
    if schema is not None:
        validate_brief(parse_json(result), schema)
    return result


def create_run(case, *, foundry=None, mock_response=None):
    """Produce a validated brief and an audit envelope; no automatic grading."""
    if mock_response is None:
        require_signed_case(case)
    schema = brief_schema()
    # Replay uses the same projection, leak guard and output validation as live inference.
    transport = None if mock_response is None else lambda *a, **k: json.dumps(mock_response, allow_nan=False)
    started = time.perf_counter()
    result = run_case(case, foundry=foundry, chat_fn=transport, schema=schema)
    elapsed = time.perf_counter() - started
    return {
        "schema": "broadbridge.brief_run/1", "case_id": case["case_id"], "family_id": case["family_id"],
        "case_sha256": digest(case), "prompt_sha256": digest(build_messages(case)),
        "brief_schema_sha256": digest(schema), "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if mock_response is None else "mock",
        "model": os.environ.get("OLLAMA_MODEL", "qwen3:8b") if mock_response is None else None,
        "endpoint": os.environ.get("OLLAMA_URL") if mock_response is None else None,
        "settings": {"think": False, "temperature": 0.2, "schema": "brief", "stream": False},
        "elapsed_seconds": round(elapsed, 6), "brief": parse_json(result),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("--dry-run", action="store_true", help="Print messages locally; do not load or call any model")
    parser.add_argument("--foundry", default=os.environ.get("SLM_FOUNDRY_PATH"))
    parser.add_argument("--schema", choices=["brief"], default="brief", help="Pass brief.schema.json to the shared client's schema= argument")
    parser.add_argument("--require-signed", action="store_true", help="Also enforce first-case signoff during --dry-run (live runs always enforce it)")
    parser.add_argument("--mock-response", help="Offline rehearsal: replay a JSON brief; never import the client or call a model")
    parser.add_argument("--output", help="Write a new brief_run.json audit envelope; refuse to overwrite")
    args = parser.parse_args(argv)
    try:
        if args.dry_run and (args.output or args.mock_response):
            raise ValueError("--dry-run prints the prompt only; use --mock-response without --dry-run to rehearse the whole flow")
        case = read_json(args.case)
        if args.require_signed:
            require_signed_case(case)
        if args.dry_run:
            print(json.dumps(run_case(case, dry_run=True), ensure_ascii=True, indent=2))
            return 0
        if args.output and Path(args.output).exists():
            raise FileExistsError("Output already exists; choose a new run file")
        replay = None
        if args.mock_response:
            replay = read_json(args.mock_response)
            validate_brief(replay)  # In particular, JSON null must never select live mode.
        record = create_run(case, foundry=args.foundry, mock_response=replay)
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
            print(f"{record['mode'].upper()} brief saved: {output}")
        else:
            print(json.dumps(record, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, AssertionError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
