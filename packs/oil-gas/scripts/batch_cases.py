"""Prepare and execute a case batch; EC2 lifecycle belongs to first_case.ps1."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

from case_contract import read_json
from import_cases import import_export, print_dispositions
from run_brief import create_run, digest, require_signed_case, run_case, validate_brief
from score_brief import write_scorecard


def write_json(path, value, *, fresh=True):
    with Path(path).open("x" if fresh else "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def prepare_batch(export, run_root, selection, *, mock_response=None):
    root = Path(run_root).resolve()
    replay = None
    if mock_response is not None:
        replay = read_json(mock_response)
        validate_brief(replay)  # null or malformed mock must never fall back to live.
    report = import_export(export, root)
    print_dispositions(report)
    if any(row["disposition"] == "rejected" for row in report["cases"]):
        raise ValueError("Import contains rejected cases; resolve and re-export into a fresh run")
    cases = {row["case_id"]: read_json(root / "data/cases" / (row["case_id"] + ".json"))
             for row in report["cases"]}
    if selection.strip() == "all-signed":
        identifiers = sorted(key for key, case in cases.items() if case["status"] == "signed")
    else:
        identifiers = [value.strip() for value in selection.split(",")]
    if (not identifiers or len({value.casefold() for value in identifiers}) != len(identifiers)
            or any(value not in cases for value in identifiers)):
        raise ValueError("Choose existing unique case IDs, or all-signed with at least one signed case")
    selected = []
    for identifier in identifiers:
        case = cases[identifier]
        if replay is None or case["status"] == "signed":
            require_signed_case(case)
        run_case(case, dry_run=True)  # All prompt/signoff checks precede any bring-up.
        selected.append({"case_id": identifier, "case_sha256": digest(case)})
    manifest = {"schema": "broadbridge.case_batch/1", "mode": "mock" if replay is not None else "live",
                "created_at": datetime.now(timezone.utc).isoformat(), "selected_cases": selected}
    if replay is not None:
        write_json(root / "mock_response.json", replay)
        manifest["mock_sha256"] = digest(replay)
    write_json(root / "batch_manifest.json", manifest)
    rows = [{"case_id": row["case_id"], "status": "not-run", "brief_valid": False,
             "elapsed_seconds": 0.0, "error": ""} for row in selected]
    write_summary(root, manifest, rows)
    return manifest


def write_summary(root, manifest, rows):
    write_json(root / "batch_results.json", rows, fresh=False)
    lines = ["# Case batch summary", "", f"Mode: **{manifest['mode'].upper()}**", "",
             "Elapsed time is per-case brief generation, validation and scorecard creation. "
             "MOCK timing is local fixture replay, not GPU latency.", "",
             "| case_id | status | brief valid y/n | elapsed (s) |",
             "| --- | --- | --- | ---: |"]
    lines.extend(f"| {r['case_id']} | {r['status']} | {'y' if r['brief_valid'] else 'n'} | {r['elapsed_seconds']:.3f} |" for r in rows)
    if any(row["error"] for row in rows):
        lines += ["", "Failure details are in batch_results.json. Successful cases are preserved; retry in a fresh run."]
    lines += ["", "Scorecards remain UNREVIEWED until the reviewer completes them. No training or retrieval runs here.", ""]
    (root / "batch_summary.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def run_batch(run_root, *, foundry=None):
    root = Path(run_root).resolve()
    manifest = read_json(root / "batch_manifest.json")
    if manifest.get("schema") != "broadbridge.case_batch/1" or manifest.get("mode") not in ("live", "mock"):
        raise ValueError("Invalid batch manifest")
    replay = None
    if manifest["mode"] == "mock":
        replay = read_json(root / "mock_response.json")
        validate_brief(replay)
        if digest(replay) != manifest["mock_sha256"]:
            raise ValueError("Mock snapshot changed; prepare a fresh run")
    cases = []
    seen = set()
    for row in manifest["selected_cases"]:
        identifier = row["case_id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", identifier) or identifier.casefold() in seen:
            raise ValueError("Invalid or duplicate batch case_id")
        seen.add(identifier.casefold())
        case = read_json(root / "data/cases" / (identifier + ".json"))
        if case["case_id"] != identifier or digest(case) != row["case_sha256"]:
            raise ValueError(f"{identifier}: case snapshot changed; prepare a fresh run")
        if replay is None or case["status"] == "signed":
            require_signed_case(case)
        run_case(case, dry_run=True)
        if ((root / "cases" / identifier).exists()
                or (root / "eval" / f"scorecard_{identifier}.md").exists()):
            raise ValueError(f"{identifier}: existing brief/review output; prepare a fresh run")
        cases.append(case)
    if not cases:
        raise ValueError("Empty batch")
    # An exclusive marker prevents rerunning model calls or replacing reviewed outputs.
    with (root / "batch_started.txt").open("x", encoding="utf-8") as handle:
        handle.write(datetime.now(timezone.utc).isoformat() + "\n")
    rows = [{"case_id": case["case_id"], "status": "not-run", "brief_valid": False,
             "elapsed_seconds": 0.0, "error": ""} for case in cases]
    for case, row in zip(cases, rows):
        started = time.perf_counter()
        try:
            destination = root / "cases" / case["case_id"]
            destination.mkdir(parents=True, exist_ok=False)
            record = create_run(case, foundry=foundry, mock_response=replay)
            row["brief_valid"] = True
            write_json(destination / "brief_run.json", record)
            write_scorecard(case, record, root / "eval")
            row["status"] = "completed"
        except (ValueError, OSError, RuntimeError, AssertionError) as exc:
            row["status"] = "failed"
            row["error"] = str(exc)
        finally:
            row["elapsed_seconds"] = round(time.perf_counter() - started, 6)
            write_summary(root, manifest, rows)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Import and preflight before any EC2 activity")
    prepare.add_argument("export")
    prepare.add_argument("run_root")
    prepare.add_argument("--case-id", required=True)
    prepare.add_argument("--mock-response")
    execute = commands.add_parser("run", help="Use the already configured session, or replay a mock snapshot")
    execute.add_argument("run_root")
    execute.add_argument("--foundry")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            manifest = prepare_batch(args.export, args.run_root, args.case_id, mock_response=args.mock_response)
            print(f"{manifest['mode'].upper()} batch ready: {len(manifest['selected_cases'])} cases")
            return 0
        rows = run_batch(args.run_root, foundry=args.foundry)
        print(f"Processed {len(rows)} cases; summary saved: {Path(args.run_root) / 'batch_summary.md'}")
        return 2 if any(row["status"] != "completed" for row in rows) else 0
    except (ValueError, OSError, RuntimeError, AssertionError, KeyError, TypeError) as exc:
        print(f"BATCH REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
