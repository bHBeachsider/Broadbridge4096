"""Intake explicit local UTF-8 .txt/.md evidence into a fresh JSON record.

This command preserves the supplied text and hashes the original bytes. It does
not download, OCR, retrieve, infer permissions, or derive facts from outcomes.
With --db, the source (and optional case) must already exist in the database.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from register_sources import require_actor, validate_identifier


def extract_evidence(source, output, *, source_id, evidence_id, case_id=None, use_db=False, actor=None):
    require_actor(use_db, actor)
    validate_identifier(source_id, "source_id")
    validate_identifier(evidence_id, "evidence_id")
    if case_id is not None:
        validate_identifier(case_id, "case_id")
    if "://" in str(source):
        raise ValueError("Evidence must be an explicit local UTF-8 .txt or .md file")
    source = Path(source).resolve()
    mime_types = {".txt": "text/plain", ".md": "text/markdown"}
    if source.suffix.lower() not in mime_types:
        raise ValueError("Evidence must be an explicit local UTF-8 .txt or .md file; other formats are unsupported")
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Evidence must be UTF-8; no conversion was performed") from exc
    record = {"evidence_id": evidence_id, "source_id": source_id, "text": text,
              "sha256": hashlib.sha256(raw).hexdigest(), "original_path": str(source),
              "mime_type": mime_types[source.suffix.lower()]}
    if case_id is not None:
        record["case_id"] = case_id

    output = Path(output).absolute()
    if output.suffix.lower() != ".json":
        raise ValueError("--output must name a new .json file")
    if output.exists() or output.is_symlink():
        raise ValueError("--output must name a new .json file; existing paths are never overwritten")
    db_write = None
    if use_db:
        import db
        db_write = lambda conn: db.upsert_evidence(conn, record, actor)
    from db_publication import publish_staged
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".evidence-intake-", dir=output.parent) as stage_name:
        staged = Path(stage_name) / "evidence.json"
        staged.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        publish_staged(staged, output, db_write=db_write)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Explicit local UTF-8 .txt or .md file")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--case-id")
    parser.add_argument("--output", required=True, help="New evidence .json file; existing paths are refused")
    parser.add_argument("--db", action="store_true", help="Also upsert evidence in the database transaction")
    parser.add_argument("--actor", metavar="EMAIL", help="Explicit audit actor, required with --db")
    args = parser.parse_args(argv)
    try:
        record = extract_evidence(args.source, args.output, source_id=args.source_id,
                                  evidence_id=args.evidence_id, case_id=args.case_id,
                                  use_db=args.db, actor=args.actor)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"EVIDENCE REJECTED; no evidence published: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"evidence_id": record["evidence_id"], "source_id": record["source_id"],
                      "sha256": record["sha256"], "database_written": args.db}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
