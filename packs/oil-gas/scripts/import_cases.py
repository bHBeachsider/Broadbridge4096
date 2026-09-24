"""Import a complete Case Capture export into a fresh, reviewable snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

from case_contract import disposition, read_json, validate_export
from run_brief import decision_payload

SPLITS = {"train": 0, "dev": 1, "locked_test": 2}


def _json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def _validate_ids(cases):
    seen_cases, seen_questions = set(), set()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    for case in cases:
        identifier = case["case_id"]
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", identifier)
                or identifier.endswith(".") or identifier.split(".")[0].upper() in reserved):
            raise ValueError(f"Unsafe case_id filename: {identifier!r}")
        if identifier.casefold() in seen_cases:
            raise ValueError(f"Duplicate case_id (case insensitive): {identifier}")
        seen_cases.add(identifier.casefold())
        if not case["family_id"].strip():
            raise ValueError(f"{identifier}: family_id cannot be blank")
        for question in case["questions"]:
            qid = question["question_id"]
            if not qid.strip() or qid.casefold() in seen_questions:
                raise ValueError(f"Missing/duplicate question_id: {qid!r}")
            seen_questions.add(qid.casefold())


def import_export(source, output):
    source, output = Path(source).resolve(), Path(output).absolute()
    export = read_json(source)
    # A malformed export is rejected as a whole: no ambiguous family can be dropped.
    validate_export(export)
    cases = export["cases"]
    _validate_ids(cases)
    families = {}
    for case in cases:
        family = case["family_id"]
        for question in case["questions"]:
            split = question["split"]
            if SPLITS[split] > SPLITS.get(families.get(family), -1):
                families[family] = split
    questions, candidates, accepted, dispositions = [], [], [], []
    for case in cases:
        state, reason = disposition(case)
        split = families.get(case["family_id"])
        if state == "imported" and split != "train":
            state, reason = "eval-only", f"family split={split or 'no questions'}; excluded from training"
        dispositions.append({"case_id": case["case_id"], "disposition": state, "reason": reason,
                             "family_id": case["family_id"], "effective_split": split})
        if state == "rejected":
            continue
        accepted.append(case)
        for question in case["questions"]:
            row = {**question, "case_id": case["case_id"], "family_id": case["family_id"],
                   "split": split, "requested_split": question["split"],
                   "permitted_use": case["identity"]["permitted_use"], "status": case["status"]}
            questions.append(row)
            if state == "imported":
                candidates.append({**row, "messages": [
                    {"role": "user", "content": json.dumps({**decision_payload(case), "question": question["question"]}, ensure_ascii=False)},
                    {"role": "assistant", "content": question["reference_answer"]}]})
    report = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "exported_at": export["exported_at"], "cases": dispositions,
              "counts": {"case_files": len(accepted), "questions": len(questions), "train_candidates": len(candidates)},
              "family_splits": families, "complete": True}
    # Fresh snapshots prevent stale training rows surviving a later holdout promotion.
    # Permit an existing empty destination, but never merge into a previous snapshot.
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError("out_dir must be new or empty; import a complete export into a fresh snapshot")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".case-import-", dir=output.parent) as stage_name:
        stage = Path(stage_name)
        snapshot = stage / "snapshot"
        (snapshot / "data/cases").mkdir(parents=True)
        (snapshot / "eval").mkdir()
        for case in accepted:
            (snapshot / "data/cases" / (case["case_id"] + ".json")).write_text(_json(case), encoding="utf-8", newline="\n")
        (snapshot / "eval/questions.jsonl").write_text(_jsonl(questions), encoding="utf-8", newline="\n")
        (snapshot / "data/train_candidates.jsonl").write_text(_jsonl(candidates), encoding="utf-8", newline="\n")
        (snapshot / "workflow.json").write_text(_json(export["workflow"]), encoding="utf-8", newline="\n")
        (snapshot / "import_report.json").write_text(_json(report), encoding="utf-8", newline="\n")
        if output.exists():
            output.rmdir()  # Empty destination only; never recursive.
        snapshot.rename(output)
    return report


def print_dispositions(report):
    print("case_id | disposition | reason")
    print("--- | --- | ---")
    for row in report["cases"]:
        print(f"{row['case_id']} | {row['disposition']} | {row['reason']}")
    print(json.dumps(report["counts"], sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export")
    parser.add_argument("out_dir")
    args = parser.parse_args(argv)
    try:
        report = import_export(args.export, args.out_dir)
        print_dispositions(report)
        return 2 if any(row["disposition"] == "rejected" for row in report["cases"]) else 0
    except (ValueError, OSError) as exc:
        # Whole-export failures are explicit and produce no partial datasets.
        print(f"EXPORT REJECTED; no snapshot published: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
