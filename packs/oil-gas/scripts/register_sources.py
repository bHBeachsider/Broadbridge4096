"""Validate a local CSV/JSON source registry and optionally upsert it with --db.

Original register fields are retained. This command does not acquire content or
grant permissions. Without --db it validates only and writes no files.
"""
import argparse
import csv
import json
from pathlib import Path
import sys


def validate_identifier(value, field):
    """Require an explicit natural ID, without silently changing its value."""
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be a nonblank string without surrounding whitespace")


def require_actor(use_db, actor):
    if use_db and (not isinstance(actor, str) or not actor.strip()):
        raise ValueError("--actor is required with --db")


def load_registry(source):
    """Read every row and validate all IDs before a database transaction starts."""
    if "://" in str(source):
        raise ValueError("Registry must be a local .csv or .json file")
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix not in {".csv", ".json"}:
        raise ValueError("Registry must be a local .csv or .json file")
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            if suffix == ".json":
                rows = json.load(handle)
            else:
                reader = csv.DictReader(handle, strict=True)
                fields = reader.fieldnames
                if (not fields or "source_id" not in fields or any(not field for field in fields)
                        or len(fields) != len(set(fields))):
                    raise ValueError("CSV requires unique column names including source_id")
                rows = list(reader)
                if any(None in row or any(value is None for value in row.values()) for row in rows):
                    raise ValueError("CSV row has a different number of cells than its header")
    except UnicodeError as exc:
        raise ValueError("Registry must be UTF-8") from exc
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV registry: {exc}") from exc
    if not isinstance(rows, list):
        raise ValueError("JSON registry must be an array of source records")
    seen = set()
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Source row {number} must be an object")
        identifier = row.get("source_id")
        validate_identifier(identifier, f"source_id in row {number}")
        if identifier.casefold() in seen:
            raise ValueError(f"Duplicate source_id (case insensitive): {identifier}")
        seen.add(identifier.casefold())
    return rows


def register_sources(source, *, use_db=False, actor=None):
    require_actor(use_db, actor)
    rows = load_registry(source)
    if use_db:
        try:
            import db
            with db.connection() as conn:
                for record in rows:
                    db.upsert_source(conn, record, actor)
        except Exception as exc:
            # Connection/SQL diagnostics can contain credentials or record content.
            raise RuntimeError(f"Source registration failed ({type(exc).__name__}); "
                               "verify database commit outcome before retrying") from None
    return {"source_count": len(rows), "database_written": use_db}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("register", help="Local UTF-8 CSV or JSON source registry")
    parser.add_argument("--db", action="store_true", help="Upsert all validated rows in one database transaction")
    parser.add_argument("--actor", metavar="EMAIL", help="Explicit audit actor, required with --db")
    args = parser.parse_args(argv)
    try:
        result = register_sources(args.register, use_db=args.db, actor=args.actor)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"SOURCE REGISTRY REJECTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
