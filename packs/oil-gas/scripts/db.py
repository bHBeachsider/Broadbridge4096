"""Dedicated Broadbridge PostgreSQL access; helpers participate in the caller transaction."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qsl, unquote, urlsplit

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from case_contract import validate_case, validate_export

PACK = Path(__file__).resolve().parents[1]
ROOT = PACK.parents[1]
MIGRATIONS = PACK / "db/migrations"
TABLES = ("sources", "evidence", "cases", "questions", "workflow", "runs", "scorecards", "review_log")


def _database_url():
    value = os.environ.get("BROADBRIDGE_DATABASE_URL")
    if not value or not value.strip():
        raise RuntimeError("Set BROADBRIDGE_DATABASE_URL explicitly for the dedicated Broadbridge database")
    return value


def _migration_target(value, *, unpooled=False):
    """Compare explicit URI identities without DNS guesses or libpq routing overrides."""
    try:
        target = urlsplit(value)
        overrides = {"host", "hostaddr", "port", "dbname", "user", "service", "options"}
        if (target.scheme not in ("postgres", "postgresql") or target.fragment
                or any(ord(char) <= 32 for char in value)
                or any(key.lower() in overrides for key, _ in parse_qsl(target.query, keep_blank_values=True))):
            raise ValueError
        # libpq parses the URI exactly as the eventual connection will, without connecting.
        parameters = psycopg.conninfo.conninfo_to_dict(value)
        host, user, database = (parameters.get(key, "") for key in ("host", "user", "dbname"))
        port = int(parameters.get("port") or 5432)
        if (not host or not user or not database or "," in host
                or not 1 <= port <= 65535 or any("\x00" in item for item in (host, user, database))):
            raise ValueError
    except (ValueError, TypeError, psycopg.Error):
        raise RuntimeError("Migration URLs must explicitly name a PostgreSQL host, user and database without routing overrides") from None
    if host.startswith(("/", "@")):  # Unix socket paths and abstract names are case-sensitive.
        return host, port, database, user
    host = host.lower()
    if host.endswith(".neon.tech"):
        endpoint, separator, domain = host.partition(".")
        if unpooled and "pooler" in endpoint:
            raise RuntimeError("DATABASE_URL_UNPOOLED must use the direct Neon endpoint; pooled endpoints are refused")
        if endpoint.endswith("-pooler"):
            host = endpoint.removesuffix("-pooler") + separator + domain
    return host, port, database, user


def _migration_database_url():
    broadbridge_url = _database_url()
    direct_url = os.environ.get("DATABASE_URL_UNPOOLED")
    if not direct_url or not direct_url.strip():
        raise RuntimeError("Set DATABASE_URL_UNPOOLED explicitly for Broadbridge migrations")
    # These libpq defaults could otherwise bypass the endpoint/port comparison below.
    if any(os.environ.get(key) for key in ("PGHOSTADDR", "PGSERVICE", "PGPORT", "PGOPTIONS")):
        raise RuntimeError("Unset PGHOSTADDR, PGSERVICE, PGPORT and PGOPTIONS routing overrides before migrating")
    if _migration_target(broadbridge_url) != _migration_target(direct_url, unpooled=True):
        raise RuntimeError("DATABASE_URL_UNPOOLED must match the Broadbridge endpoint, port, database and user")
    return direct_url


@contextmanager
def connection(*, migration=False):
    """Commit/rollback the caller transaction; migration mode verifies its separate direct URL."""
    value = _migration_database_url() if migration else _database_url()
    try:
        conn = psycopg.connect(value, autocommit=False, prepare_threshold=None, connect_timeout=10)
    except (psycopg.Error, ValueError):
        raise RuntimeError("Unable to connect to the configured Broadbridge database; check configuration and connectivity") from None
    with conn:
        yield conn


def migrate(conn):
    """Apply versioned SQL atomically in the caller's transaction, verifying all existing hashes."""
    conn.execute("SELECT pg_advisory_xact_lock(1947014096, 2)")
    conn.execute("CREATE SCHEMA IF NOT EXISTS broadbridge")
    conn.execute("""CREATE TABLE IF NOT EXISTS broadbridge.schema_migrations (
        version text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT clock_timestamp())""")
    paths = sorted(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    if not paths:
        raise RuntimeError("No Broadbridge migration files found")
    scripts = {p.name: (p.read_bytes(), hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
    applied = dict(conn.execute("SELECT version, checksum FROM broadbridge.schema_migrations").fetchall())
    for version, checksum in applied.items():
        if version not in scripts or scripts[version][1] != checksum:
            raise RuntimeError(f"Migration checksum mismatch or missing migration: {version}")
    for version, (content, checksum) in scripts.items():
        if version not in applied:
            conn.execute(content.decode("utf-8-sig"))
            conn.execute("INSERT INTO broadbridge.schema_migrations(version, checksum) VALUES (%s, %s)", (version, checksum))
    return status(conn)


def status(conn):
    """Return database version, applied migration versions and exact capture row counts."""
    present = conn.execute("SELECT to_regclass('broadbridge.schema_migrations')").fetchone()[0]
    if present is None:
        return {"version": None, "migrations": [], "counts": {}}
    versions = [row[0] for row in conn.execute("SELECT version FROM broadbridge.schema_migrations ORDER BY version")]
    counts = {}
    for name in TABLES:
        present = conn.execute("SELECT to_regclass(%s)", (f"broadbridge.{name}",)).fetchone()[0]
        if present:
            counts[name] = conn.execute(sql.SQL("SELECT count(*) FROM broadbridge.{}").format(sql.Identifier(name))).fetchone()[0]
    return {"version": versions[-1] if versions else None, "migrations": versions, "counts": counts}


def _actor(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("An explicit nonblank actor is required")
    return value.strip()


def _identifier(record, key):
    if not isinstance(record, dict):
        raise ValueError("A JSON object is required")
    value = record.get(key)
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{key} must be a nonblank string without surrounding whitespace")
    return value


def _json(value):
    # Reject NaN/Infinity before handing data to a driver or database.
    return Jsonb(value, dumps=lambda v: json.dumps(v, ensure_ascii=True, allow_nan=False))


def upsert_case(conn, case, actor, expected_revision=None):
    validate_case(case)
    _identifier(case, "case_id")
    _identifier(case, "family_id")
    for question in case["questions"]:
        _identifier(question, "question_id")
    return conn.execute("SELECT broadbridge.save_case(%s, %s, %s)",
                        (_json(case), _actor(actor), expected_revision)).fetchone()[0]


def upsert_workflow(conn, workflow, actor):
    validate_export({"exported_at": "", "workflow": workflow, "cases": []})
    return conn.execute("SELECT broadbridge.save_workflow(%s, %s)", (_json(workflow), _actor(actor))).fetchone()[0]


def upsert_source(conn, record, actor):
    identifier, who = _identifier(record, "source_id"), _actor(actor)
    conn.execute("""INSERT INTO broadbridge.sources(source_id, record, updated_by) VALUES (%s, %s, %s)
        ON CONFLICT (source_id) DO UPDATE SET record=EXCLUDED.record, updated_by=EXCLUDED.updated_by,
            updated_at=greatest(clock_timestamp(), broadbridge.sources.updated_at + interval '1 microsecond')
        WHERE broadbridge.sources.record IS DISTINCT FROM EXCLUDED.record
            OR broadbridge.sources.updated_by IS DISTINCT FROM EXCLUDED.updated_by""", (identifier, _json(record), who))
    return identifier


def upsert_evidence(conn, record, actor):
    identifier, source_id = _identifier(record, "evidence_id"), _identifier(record, "source_id")
    case_id = record.get("case_id")
    if case_id is not None:
        _identifier(record, "case_id")
    conn.execute("""INSERT INTO broadbridge.evidence(evidence_id, source_id, case_id, record, updated_by)
        VALUES (%s, %s, %s, %s, %s) ON CONFLICT (evidence_id) DO UPDATE
        SET source_id=EXCLUDED.source_id, case_id=EXCLUDED.case_id, record=EXCLUDED.record,
            updated_by=EXCLUDED.updated_by,
            updated_at=greatest(clock_timestamp(), broadbridge.evidence.updated_at + interval '1 microsecond')
        WHERE broadbridge.evidence.record IS DISTINCT FROM EXCLUDED.record
            OR broadbridge.evidence.updated_by IS DISTINCT FROM EXCLUDED.updated_by""",
        (identifier, source_id, case_id, _json(record), _actor(actor)))
    return identifier


def upsert_run(conn, brief_run, actor):
    """Store an immutable historical run; the current case must already exist."""
    from run_brief import digest, validate_brief
    case_id = _identifier(brief_run, "case_id")
    required = {"schema", "case_id", "family_id", "case_sha256", "prompt_sha256", "brief_schema_sha256",
                "created_at", "mode", "model", "endpoint", "settings", "elapsed_seconds", "brief"}
    if (not required.issubset(brief_run) or brief_run["schema"] != "broadbridge.brief_run/1"
            or brief_run["mode"] not in ("live", "mock")):
        raise ValueError("Invalid brief run envelope")
    for key in ("case_sha256", "prompt_sha256", "brief_schema_sha256"):
        if not isinstance(brief_run[key], str) or not re.fullmatch(r"[0-9a-f]{64}", brief_run[key]):
            raise ValueError("Invalid brief run digest")
    try:
        created_at = datetime.fromisoformat(brief_run["created_at"].replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Brief run created_at must be an ISO timestamp with timezone") from None
    validate_brief(brief_run["brief"])
    run_id = digest(brief_run)
    conn.execute("""INSERT INTO broadbridge.runs(run_id, case_id, mode, case_sha256, prompt_sha256, record, created_at, updated_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (run_id) DO UPDATE
        SET updated_by=EXCLUDED.updated_by WHERE broadbridge.runs.updated_by IS DISTINCT FROM EXCLUDED.updated_by""",
        (run_id, case_id, brief_run["mode"], brief_run["case_sha256"], brief_run["prompt_sha256"],
         _json(brief_run), created_at, _actor(actor)))
    return run_id


def upsert_scorecard(conn, case, brief_run, markdown, actor):
    from score_brief import render_scorecard
    from run_brief import digest
    if not isinstance(markdown, str):
        raise ValueError("Scorecard markdown must be text")
    template = render_scorecard(case, brief_run)  # Historical case/prompt/schema validation.
    # Serialize review writes, including the first INSERT, so a repeated template
    # cannot erase a reviewer edit written concurrently for the same run.
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 1947014096))", (digest(brief_run),))
    current = conn.execute("SELECT markdown FROM broadbridge.scorecards WHERE run_id=%s", (digest(brief_run),)).fetchone()
    if current and current[0] != template and markdown == template:
        raise ValueError("Existing reviewer changes are preserved; do not replace them with an unreviewed template")
    run_id = upsert_run(conn, brief_run, actor)
    conn.execute("""INSERT INTO broadbridge.scorecards(run_id, case_id, markdown, updated_by)
        VALUES (%s, %s, %s, %s) ON CONFLICT (run_id) DO UPDATE
        SET markdown=EXCLUDED.markdown, updated_by=EXCLUDED.updated_by,
            updated_at=greatest(clock_timestamp(), broadbridge.scorecards.updated_at + interval '1 microsecond')
        WHERE broadbridge.scorecards.markdown IS DISTINCT FROM EXCLUDED.markdown
            OR broadbridge.scorecards.updated_by IS DISTINCT FROM EXCLUDED.updated_by""",
        (run_id, case["case_id"], markdown, _actor(actor)))
    return run_id


def effective_splits(conn, family_ids):
    """Read complete database family closure inside the import/publish transaction."""
    rows = conn.execute("""SELECT c.family_id,
        CASE max(CASE q.effective_split WHEN 'locked_test' THEN 2 WHEN 'dev' THEN 1 ELSE 0 END)
          WHEN 2 THEN 'locked_test' WHEN 1 THEN 'dev' ELSE 'train' END
        FROM broadbridge.cases c JOIN broadbridge.questions q USING (case_id)
        WHERE c.family_id = ANY(%s) GROUP BY c.family_id""", (list(family_ids),)).fetchall()
    return dict(rows)


def _check_reset_target(value, branch, git_branch):
    if branch not in ("dev", "test"):
        raise ValueError("reset-dev requires explicit --branch dev or --branch test")
    if not git_branch or git_branch.lower() in ("main", "master", "head"):
        raise ValueError("reset-dev refuses main/master and detached or unverified Git branches")
    try:
        target = urlsplit(value)
        valid = (target.scheme in ("postgres", "postgresql")
                 and target.hostname in ("127.0.0.1", "localhost", "::1")
                 and not target.query and not target.fragment
                 and re.fullmatch(r"broadbridge_(?:test|dev)(?:_[A-Za-z0-9_]+)?", unquote(target.path.lstrip("/"))))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("reset-dev supports only explicit loopback broadbridge_test/broadbridge_dev databases; remote Neon branches require a verified project/endpoint binding and are refused")


def _reset_schema(conn):
    # The connected client address is loopback even when Docker's server interface is private.
    # Verify libpq's actual resolved peer, not only the hostname supplied in a URL.
    name = conn.execute("SELECT current_database()").fetchone()[0]
    if conn.info.hostaddr not in ("127.0.0.1", "::1") or not re.fullmatch(r"broadbridge_(?:test|dev)(?:_[A-Za-z0-9_]+)?", name):
        raise ValueError("reset-dev could not verify the connected loopback test database")
    conn.execute("DROP SCHEMA IF EXISTS broadbridge CASCADE")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("migrate", "status", "reset-dev"))
    parser.add_argument("--branch", choices=("dev", "test"), help="Required explicit database branch intent for reset-dev")
    args = parser.parse_args(argv)
    try:
        if args.command == "reset-dev":
            branch = subprocess.run(["git", "branch", "--show-current"], cwd=ROOT,
                                    capture_output=True, text=True, check=True).stdout.strip()
            _check_reset_target(_database_url(), args.branch, branch)
        database_connection = connection(migration=True) if args.command == "migrate" else connection()
        with database_connection as conn:
            if args.command == "reset-dev":
                _reset_schema(conn)
                result = {"reset": "broadbridge", "branch": args.branch}
            elif args.command == "migrate":
                result = migrate(conn)
            else:
                result = status(conn)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, RuntimeError) as exc:
        print(f"DB REFUSED: {exc}", file=sys.stderr)
        return 2
    except (psycopg.Error, OSError, subprocess.SubprocessError) as exc:
        # Driver details can contain connection strings or captured records; do not echo them.
        print(f"DB REFUSED: operation failed ({type(exc).__name__}); no database credentials are displayed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
