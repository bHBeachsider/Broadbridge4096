"""Owned local PostgreSQL + transport fixtures for the real capture browser smoke.

No .env is loaded, no provider is contacted, and no existing database is used.
R2 and Neon HTTP transports are local test doubles; PostgreSQL, authentication,
the ingestion engine, parser subprocess and browser application are real.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import unquote, urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server

import psycopg
import yaml


def command(args, **kwargs):
    result = subprocess.run(args, capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f"Local command failed: {Path(args[0]).name}")
    return result.stdout.strip()


def raw_text(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return "t" if value else "f"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, bytes):
        return "\\x" + value.hex()
    return str(value)


def sql_handler(dsn):
    class SQL(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            status = 400
            response = {"message": "Local SQL fixture rejected request", "code": "08006"}
            try:
                if self.path != "/sql" or not hmac.compare_digest(self.headers.get("Neon-Connection-String", ""), dsn):
                    raise ValueError("local target mismatch")
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 1024 * 1024:
                    raise ValueError("request size")
                body = json.loads(self.rfile.read(size))
                with psycopg.connect(dsn, cursor_factory=psycopg.RawCursor,
                                     connect_timeout=5, options="-c statement_timeout=15000") as conn:
                    def query(item):
                        with conn.cursor() as cursor:
                            cursor.execute(item["query"], item.get("params", []))
                            fields = [{"name": col.name, "dataTypeID": col.type_code, "format": "text"} for col in cursor.description or []]
                            rows = [[raw_text(value) for value in row] for row in cursor.fetchall()] if fields else []
                            return {"fields": fields, "rows": rows, "rowCount": cursor.rowcount, "command": (cursor.statusmessage or "").split(" ")[0], "rowAsArray": True}
                    response = {"results": [query(item) for item in body["queries"]]} if "queries" in body else query(body)
                status = 200
            except psycopg.Error as exc:
                response["code"] = exc.sqlstate or "08006"
            except Exception:
                pass
            payload = json.dumps(response).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    return SQL


def object_handler(store, bucket, origin):
    metadata = {}
    lock = threading.Lock()

    class Objects(BaseHTTPRequestHandler):
        # No access log: request targets contain temporary signing parameters.
        def log_message(self, *_args):
            pass

        def reply(self, status, payload=b"", headers=None):
            self.send_response(status)
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "PUT, GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "content-type,if-none-match,x-amz-meta-sha256,x-amz-meta-source-id,x-amz-meta-revision-id")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)

        def key(self):
            path = unquote(urlsplit(self.path).path)
            prefix = f"/{bucket}/"
            if not path.startswith(prefix):
                raise ValueError("bucket mismatch")
            return path[len(prefix):]

        def do_OPTIONS(self):
            self.reply(204)

        def do_PUT(self):
            try:
                key = self.key()
                size = int(self.headers.get("Content-Length", "0"))
                if not key.startswith("incoming/broadbridge-oil-gas/") or not 0 < size <= 50 * 1024 * 1024 or self.headers.get("If-None-Match") != "*":
                    raise ValueError("invalid upload")
                data = self.rfile.read(size)
                if len(data) != size:
                    raise ValueError("incomplete upload")
                with lock:
                    if store.exists(key):
                        self.reply(412)
                        return
                    store.put_immutable(key, data)
                    metadata[key] = {name: self.headers.get(name, "") for name in ("Content-Type", "x-amz-meta-sha256", "x-amz-meta-source-id", "x-amz-meta-revision-id")}
                self.reply(200, headers={"ETag": '"' + hashlib.md5(data, usedforsecurity=False).hexdigest() + '"'})
            except Exception:
                self.reply(400)

        def do_GET(self):
            try:
                key = self.key()
                self.reply(200, store.get(key), metadata.get(key, {"Content-Type": "application/json"}))
            except Exception:
                self.reply(404)

        do_HEAD = do_GET
    return Objects


def serve_http(stack, handler):
    class OwnedHTTPServer(ThreadingHTTPServer):
        # No request may outlive the libpq isolation context, including a client
        # that disconnects late. server_close joins these bounded handlers.
        daemon_threads = False
        block_on_close = True

        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(15)
            return connection, address
    server = OwnedHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def close():
        server.shutdown()
        server.server_close()
        thread.join(5)
    stack.callback(close)
    return f"http://127.0.0.1:{server.server_port}"


@contextmanager
def isolated_libpq_environment():
    """Keep libpq environment routing/credentials out of the parent and threads."""
    inherited = {key: value for key, value in os.environ.items() if key.upper().startswith("PG")}
    for key in inherited:
        os.environ.pop(key)
    try:
        yield
    finally:
        os.environ.update(inherited)


def run(foundry, repo, output, *, public_review=False, review_only=False):
    with isolated_libpq_environment():
        return _run_local(foundry, repo, output, public_review=public_review or review_only, review_only=review_only)


def _run_local(foundry, repo, output, *, public_review=False, review_only=False):
    output.mkdir(parents=True, exist_ok=False)
    # Ignore inherited service credentials and routing variables entirely.
    safe_names = {"PATH", "SYSTEMROOT", "WINDIR", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "COMSPEC", "PATHEXT", "USERPROFILE"}
    env = {key: value for key, value in os.environ.items() if key.upper() in safe_names}
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_DATASETS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", NEXT_TELEMETRY_DISABLED="1")
    token = secrets.token_hex(16)
    name = f"broadbridge-ingestion-test-{token}"
    image = "pgvector/pgvector:pg17"
    command(["docker", "image", "inspect", image], env=env)
    container = command(["docker", "run", "--pull", "never", "--rm", "-d", "--name", name, "--label", f"broadbridge.ingestion-test={token}", "-e", "POSTGRES_HOST_AUTH_METHOD=trust", "-e", "POSTGRES_USER=broadbridge_test", "-e", "POSTGRES_DB=broadbridge_test", "-p", "127.0.0.1::5432", image], env=env)
    if not re.fullmatch(r"[a-f0-9]{64}", container):
        raise RuntimeError("Could not verify owned container identity")
    try:
        for _ in range(60):
            probe = subprocess.run(["docker", "exec", container, "pg_isready", "-U", "broadbridge_test"], env=env, capture_output=True)
            if probe.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Owned database not ready")
        port = command(["docker", "port", container, "5432/tcp"], env=env)
        if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", port):
            raise RuntimeError("Database binding is not loopback")
        dsn = f"postgresql://broadbridge_test:local-only@{port}/broadbridge_test"
        sys.path[:0] = [str(repo / "packs/oil-gas/scripts"), str(foundry)]
        import db
        from src.ingestion.storage import LocalObjectStore
        from src.ingestion.jobs import PostgresJobStore
        from src.ingestion.cli import IngestionRunner
        from src.ingestion.service import create_app
        from src.ingestion.curate import load_pack_taxonomy
        with psycopg.connect(dsn) as conn:
            migration = db.migrate(conn)
            if public_review:
                sys.path.insert(0, str(repo / "scripts/research"))
                from public_review_packet import build_packet, register
                register(conn, build_packet(repo / "output/openrouter-public-evaluation/public-v1-live", "public-v1"))
        store = LocalObjectStore(output / "objects")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            app_port = sock.getsockname()[1]
        origin = f"http://127.0.0.1:{app_port}"
        stop = threading.Event()
        worker_errors = []
        with ExitStack() as stack:
            api_conn = stack.enter_context(psycopg.connect(dsn))
            worker_conn = stack.enter_context(psycopg.connect(dsn))
            taxonomy = load_pack_taxonomy(repo / "packs/oil-gas")
            policy = yaml.safe_load((repo / "packs/oil-gas/ingestion.yaml").read_text(encoding="utf-8"))
            def runner(conn):
                return IngestionRunner(store, PostgresJobStore(conn, "broadbridge"), "broadbridge-oil-gas", policy["recipe_version"], lease_seconds=6, parser_timeout=45, taxonomy=taxonomy)
            api_runner, worker_runner = runner(api_conn), runner(worker_conn)
            sql_url = serve_http(stack, sql_handler(dsn)) + "/sql"
            object_url = serve_http(stack, object_handler(store, "local-broadbridge", origin))
            class QuietWSGI(WSGIRequestHandler):
                def log_message(self, *_args):
                    pass
            api = make_server("127.0.0.1", 0, create_app(api_runner, token), handler_class=QuietWSGI)
            api_thread = threading.Thread(target=api.serve_forever, daemon=True)
            api_thread.start()
            stack.callback(api.server_close)
            stack.callback(api.shutdown)
            def worker():
                while not stop.is_set():
                    try:
                        worker_runner.process_one("local-browser-smoke")
                    except Exception as exc:
                        worker_errors.append(type(exc).__name__)
                    stop.wait(0.2)
            worker_thread = threading.Thread(target=worker, daemon=True)
            worker_thread.start()
            def stop_worker():
                stop.set()
                worker_thread.join(55)
            stack.callback(stop_worker)
            env.update(
                NODE_ENV="development", BROADBRIDGE_DATABASE_URL=dsn,
                DATABASE_URL_UNPOOLED=dsn, CAPTURE_LOCAL_INGESTION_TEST="1",
                CAPTURE_TEST_SQL_ENDPOINT=sql_url, AUTH_URL=origin,
                AUTH_SECRET=secrets.token_hex(32), CAPTURE_TEST_EMAIL="reviewer@example.invalid",
                CAPTURE_ALLOWED_EMAILS="reviewer@example.invalid",
                CAPTURE_TEST_OUTBOX=str(output / "auth-outbox.jsonl"),
                RESEND_API_KEY="local-outbox-only", CAPTURE_EMAIL_FROM="capture@example.invalid",
                R2_ENDPOINT=object_url, R2_BUCKET="local-broadbridge",
                R2_ACCESS_KEY_ID="local-test-only", R2_SECRET_ACCESS_KEY="local-test-only",
                INGESTION_API_URL=f"http://127.0.0.1:{api.server_port}", INGESTION_API_TOKEN=token,
                CAPTURE_TEST_FOUNDRY=str(foundry), CAPTURE_TEST_PYTHON=sys.executable,
                CAPTURE_TEST_OBJECT_ROOT=str(output / "objects"), CAPTURE_TEST_RUN_ROOT=str(output),
            )
            app = repo / "apps/capture"
            executions = {}
            checks = [
                ("browser", ["node", "node_modules/@playwright/test/cli.js", "test", "e2e/ingestion.spec.ts"]),
                ("repository", ["node", "node_modules/vitest/vitest.mjs", "run", "tests/ingestion-repository.test.ts"]),
            ]
            if review_only:
                checks = []
            if public_review:
                checks += [
                    ("public-review-repository", ["node", "node_modules/vitest/vitest.mjs", "run", "tests/public-review-repository.test.ts"]),
                    ("public-review-browser", ["node", "node_modules/@playwright/test/cli.js", "test", "e2e/public-review.spec.ts"]),
                ]
            for label, args in checks:
                child_env = dict(env)
                if label == "public-review-browser":
                    # Separate authenticated test actor: do not bypass the real
                    # 60-second email issuance cooldown from the ingestion smoke.
                    child_env.update(CAPTURE_TEST_EMAIL="public-reviewer@example.invalid",
                                     CAPTURE_ALLOWED_EMAILS="public-reviewer@example.invalid")
                with (output / f"{label}.log").open("w", encoding="utf-8") as log:
                    result = subprocess.run(args, cwd=app, env=child_env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                executions[label] = result.returncode
                print(f"{label}: exit {result.returncode}", flush=True)
                if result.returncode:
                    break
            with psycopg.connect(dsn) as conn:
                counts = {table: conn.execute(f"SELECT count(*) FROM broadbridge.{table}").fetchone()[0] for table in ("source_revisions", "source_rights_reviews", "ingestion_jobs", "candidate_records", "candidate_artifact_bindings", "candidate_reviews", "dataset_releases")}
                job_states = conn.execute("SELECT state,count(*) FROM broadbridge.ingestion_jobs GROUP BY state").fetchall()
            report = {"synthetic_only": True, "database": "owned_local_postgresql_17", "migrations": migration["migrations"], "transport": "local_S3_and_Neon_HTTP_fixtures", "live_cloud": "not_run", "gpu": "not_run", "executions": executions, "counts": counts, "job_states": job_states, "worker_error_types": sorted(set(worker_errors))}
            (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            required_browser = "public-review-browser" if review_only else "browser"
            if any(executions.values()) or required_browser not in executions or worker_errors:
                raise RuntimeError("Local smoke failed; inspect sanitized local logs")
            return report
    finally:
        owner = command(["docker", "inspect", "--format", '{{ index .Config.Labels "broadbridge.ingestion-test" }}', container], env=env)
        if owner != token:
            raise RuntimeError("Container ownership changed; cleanup refused")
        command(["docker", "rm", "--force", container], env=env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--public-review", action="store_true", help="Include frozen public packet and isolated reviewer URL tests")
    parser.add_argument("--review-only", action="store_true", help="Only reviewer SQL/browser acceptance, on a new disposable database")
    args = parser.parse_args()
    try:
        run(args.foundry.resolve(), args.repo.resolve(), args.output.resolve(), public_review=args.public_review, review_only=args.review_only)
    except Exception as exc:
        print(f"Local smoke failed ({type(exc).__name__}); no existing database was used.", file=sys.stderr)
        raise SystemExit(1)
