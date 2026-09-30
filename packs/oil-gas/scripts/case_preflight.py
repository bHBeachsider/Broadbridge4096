"""Report first-case gaps offline; never import data, call a model or grant approval."""
import argparse
from collections import Counter
import hashlib
from importlib import metadata
import json
from pathlib import Path
import sys

from case_contract import disposition, parse_json, read_json, validate_export
from import_cases import SPLITS, _validate_ids
from run_brief import assert_no_leak, build_messages, digest, require_signed_case
from score_brief import RUBRICS

PACK = Path(__file__).resolve().parents[1]
REVISION = "946bc9ac74a6c1f8cf012497c503a119b2fcf2eb"
TOKENIZER_FILES = {"config.json", "special_tokens_map.json", "tokenizer_config.json", "tokenizer.json"}


def missing(value):
    return not isinstance(value, str) or value.strip().casefold() in {"", "unknown", "undecided"}


def fixture_marker(case):
    # This detects our known conventions, not every possible synthetic record.
    # Absence of a marker never proves real provenance or authenticated signoff.
    return case["case_id"].upper().startswith("SYN-") or any(
        "synthetic" in value.casefold() for value in (
            case["identity"]["title"], case["identity"]["confidentiality"], case["reviewer_signoff"]["name"]))


def token_count(tokenizer, messages):
    tokens = tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, enable_thinking=False, return_dict=False)
    if not isinstance(tokens, list) or not tokens or any(type(t) is not int for t in tokens):
        raise ValueError("Expected nonempty flat token IDs from the local tokenizer")
    return len(tokens)


def artifact_matches(payload, record):
    if len(payload) != record["size_bytes"]:
        return False
    if record["hash_algorithm"] == "git-blob-sha1":
        actual = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
    elif record["hash_algorithm"] == "sha256":
        actual = hashlib.sha256(payload).hexdigest()
    else:
        return False
    return actual == record["hash"]


def load_token_counter(directory):
    directory = Path(directory)
    revision = read_json(directory / "revision.json")
    if revision != {"repo": "unsloth/Qwen3-8B", "revision": REVISION}:
        raise ValueError("Wrong pinned tokenizer revision")
    if directory.is_symlink() or (hasattr(directory, "is_junction") and directory.is_junction()):
        raise ValueError("Linked tokenizer directory refused")
    inventory = read_json(PACK.parents[1] / "docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json")
    if inventory["repo_id"] != "unsloth/Qwen3-8B" or inventory["revision"] != REVISION:
        raise ValueError("Wrong tokenizer inventory")
    # A stray chat_template.jinja or tokenizer sidecar could change rendering.
    if {p.name for p in directory.iterdir()} - TOKENIZER_FILES - {"revision.json", ".cache"}:
        raise ValueError("Unexpected tokenizer sidecar; use the verified four-file local snapshot")
    expected = {r["path"]: r for r in inventory["files"] if r["path"] in TOKENIZER_FILES}
    if set(expected) != TOKENIZER_FILES:
        raise ValueError("Incomplete tokenizer inventory")
    verified = []
    for name in sorted(TOKENIZER_FILES):
        path = directory / name
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError("Linked tokenizer artifact refused")
        payload = path.read_bytes()
        record = expected[name]
        if not artifact_matches(payload, record):
            raise ValueError("Tokenizer artifact differs from pinned inventory")
        verified.append({"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)})
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(directory.resolve()), local_files_only=True,
                                               trust_remote_code=False, use_fast=True)
    if not tokenizer.chat_template:
        raise ValueError("Pinned tokenizer has no chat template")
    return lambda messages: token_count(tokenizer, messages), {
        "repo": "unsloth/Qwen3-8B", "revision": REVISION, "files": verified,
        "transformers": metadata.version("transformers"), "tokenizers": metadata.version("tokenizers"),
        "enable_thinking": False, "add_generation_prompt": True,
        "scope": "HF template estimate, not verified equivalence to the live Ollama template or its schema overhead"}


def assess(export, *, count_tokens=None, context_limit=4096, output_reserve=1024,
           margin=256, fixture_export=False):
    if (any(type(v) is not int for v in (context_limit, output_reserve, margin))
            or context_limit <= 0 or output_reserve <= 0 or margin < 0
            or output_reserve + margin >= context_limit):
        raise ValueError("Invalid context budget")
    try:
        validate_export(export)
    except ValueError:
        raise ValueError("Canonical export schema validation failed") from None
    _validate_ids(export["cases"])
    families = {}
    for case in export["cases"]:
        for q in case["questions"]:
            family = case["family_id"]
            if SPLITS[q["split"]] > SPLITS.get(families.get(family), -1):
                families[family] = q["split"]
    by_type = Counter({kind: 0 for kind in RUBRICS})
    rows = []
    for case in export["cases"]:
        issues = []
        state, _ = disposition(case)
        if state == "rejected":
            issues.append("case_admission_rejected")
        try:
            require_signed_case(case)
        except ValueError:
            issues.append("signed_case_preflight_failed")
        good_questions = []
        for q in case["questions"]:
            required = ["question", "reference_answer", "hard_fail_criteria"]
            if q["type"] == "calculation":
                required.append("tolerance")
            if q["type"] == "grounded_explanation":
                required.append("evidence_ids")
            absent = [key for key in required if missing(q[key])]
            issues.extend(f"question:{q['question_id']}:{key}_missing" for key in absent)
            if not absent:
                good_questions.append(q)
        messages = build_messages(case)
        context = {"status": "not_measured", "prompt_tokens": None,
                   "context_limit": context_limit, "output_reserve": output_reserve, "margin": margin}
        try:
            assert_no_leak(case, messages)
        except AssertionError:
            issues.append("prompt_leak")
            context["status"] = "blocked_by_prompt_leak"
        else:
            if count_tokens is not None:
                count = count_tokens(messages)
                if type(count) is not int or count <= 0:
                    raise ValueError("Tokenizer returned invalid token count")
                context.update(prompt_tokens=count, remaining_for_output=context_limit-count-margin,
                    status="fits_local_estimate" if count+output_reserve+margin <= context_limit else "over_budget")
                if context["status"] == "over_budget":
                    issues.append("context_over_budget")
        fixture = fixture_export or fixture_marker(case)
        # Coverage of structurally complete signed references, not proof of quality,
        # distinct questions, actual provenance, source rights or authenticated identity.
        if not fixture and not any(s in issues for s in (
                "case_admission_rejected", "signed_case_preflight_failed", "prompt_leak")):
            by_type.update(q["type"] for q in good_questions)
        rows.append({"case_id": case["case_id"], "family_id": case["family_id"],
            "case_sha256": digest(case), "prompt_sha256": digest(messages), "status": case["status"],
            "permitted_use": case["identity"]["permitted_use"], "fixture": fixture,
            "effective_split": families.get(case["family_id"]), "question_count": len(case["questions"]),
            "complete_scoring_questions": len(good_questions), "issues": issues, "context": context})
    total = sum(by_type.values())
    return {"schema": "broadbridge.case_preflight/1", "export_sha256_canonical": digest(export),
        "mode": "offline_report", "model_calls": 0, "gate_0_verified": False,
        "execution_authorized": False, "training_approved": False, "cases": rows,
        "family_splits": families, "coverage": {"signed_nonfixture_questions": total,
            "by_type": dict(by_type), "questions_needed_for_30": max(0, 30-total),
            "missing_types": [kind for kind, n in by_type.items() if n == 0]},
        "remaining_human_checks": ["Authenticated reviewer signoff and actual case provenance",
            "Rights, approved storage and completeness of the export/family history",
            "Engineering correctness, question distinctness, evidence mapping, calculation units/basis/tolerances",
            "Decision-time facts reviewed for paraphrased hindsight; exact-string guard is not sufficient"],
        "remaining_runtime_checks": ["Live model digest/template, think=false and actual context/output settings",
            "Ollama rendering/schema overhead and actual token use; no truncation is proved by this estimate",
            "Approved session ownership, pinned host identity and fixed shutdown controls"],
        "limitations": ["No credential or database read; this describes the supplied export only",
            "Known fixture markers are excluded; absence of a marker does not establish real provenance",
            "The local HF prompt count is an estimate for S0-cases; model and schema overhead may differ",
            "No data import, model response, scorecard review, dataset release or approval is produced"]}


def markdown(report):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    lines = ["# Offline first-case preflight", "",
        "**No execution authorized. Gate 0 and training acceptance are not established.**", "",
        "| Case | Fixture | Status | Family split | Prompt tokens (local estimate) | Context | Issues |",
        "| --- | --- | --- | --- | ---: | --- | --- |"]
    for row in report["cases"]:
        c = row["context"]
        lines.append("| " + " | ".join(map(cell, [row["case_id"], row["fixture"], row["status"],
            row["effective_split"], c["prompt_tokens"], c["status"], "; ".join(row["issues"]) or "none detected"])) + " |")
    coverage = report["coverage"]
    lines += ["", "## Signed reference coverage", "",
        "Counts exclude recognized fixtures and incomplete question fields. They are a structural inventory, not engineering acceptance.", "",
        "| Type | Questions |", "| --- | ---: |"]
    lines += [f"| {kind} | {count} |" for kind, count in coverage["by_type"].items()]
    lines += ["", f"Questions still needed for 30: **{coverage['questions_needed_for_30']}**. "
        "A minimum count alone does not close Gate 0.", ""]
    for label, key in [("Human checks", "remaining_human_checks"),
                       ("Before a live run", "remaining_runtime_checks"), ("Limits", "limitations")]:
        lines += [f"## {label}", ""] + [f"- {v}" for v in report[key]] + [""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tokenizer-dir", type=Path)
    parser.add_argument("--fixture-export", action="store_true", help="Exclude this entire software-test export from real coverage")
    parser.add_argument("--context-limit", type=int, default=4096)
    parser.add_argument("--output-reserve", type=int, default=1024)
    parser.add_argument("--margin", type=int, default=256)
    args = parser.parse_args(argv)
    if not args.out.is_absolute() or args.out.exists():
        raise ValueError("Choose a new absolute output directory")
    source_bytes = args.export.read_bytes()
    export = parse_json(source_bytes.decode("utf-8-sig"))
    counter, token_info = (None, None) if args.tokenizer_dir is None else load_token_counter(args.tokenizer_dir)
    report = assess(export, count_tokens=counter, context_limit=args.context_limit,
        output_reserve=args.output_reserve, margin=args.margin, fixture_export=args.fixture_export)
    report["tokenizer"] = token_info
    report["source_file_sha256"] = hashlib.sha256(source_bytes).hexdigest()
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "preflight.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    (args.out / "PREFLIGHT.md").write_text(markdown(report), encoding="utf-8", newline="\n")
    print(json.dumps({"report_written": True, "cases": len(report["cases"]),
        "coverage": report["coverage"], "execution_authorized": False}, indent=2))
    return 0  # Report generation succeeded; never interpret this as run approval.


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"PREFLIGHT REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
