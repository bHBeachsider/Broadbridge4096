"""Render an isolated decision-time brief; inference is opt-in and tunnel-only."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys

from case_contract import read_json, validate_case

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
    forbidden = list(_strings(case["hindsight"])) + [q["reference_answer"] for q in case["questions"] if q["reference_answer"].strip()]
    if any(value in text for value in forbidden for text in haystacks):
        raise AssertionError("Prompt leak: a hindsight string or reference answer appears in decision-time input; review the case")


def run_case(case, *, dry_run=False, chat_fn=None, foundry=None):
    validate_case(case)
    messages = build_messages(case)
    assert_no_leak(case, messages)
    if dry_run:
        return messages
    if chat_fn is None:
        if case["identity"]["permitted_use"] == "undecided":
            raise ValueError("Inference refused: permitted_use=undecided")
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
    return chat_fn(messages, think=False, temperature=0.2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("--dry-run", action="store_true", help="Print messages locally; do not load or call any model")
    parser.add_argument("--foundry", default=os.environ.get("SLM_FOUNDRY_PATH"))
    args = parser.parse_args(argv)
    try:
        result = run_case(read_json(args.case), dry_run=args.dry_run, foundry=args.foundry)
        print(json.dumps(result, ensure_ascii=True, indent=2) if args.dry_run else result)
        return 0
    except (ValueError, OSError, RuntimeError, AssertionError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
