"""Disposable local PostgreSQL and real-auth questionnaire acceptance. No cloud or .env reads."""
from contextlib import ExitStack, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse, hashlib, hmac, json, os, re, secrets, socket, subprocess, sys, threading, time
from pathlib import Path
import psycopg


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


def run(repo, output):
    from questionnaire_packet import register
    output.mkdir(parents=True, exist_ok=False)
    safe = {"PATH", "SYSTEMROOT", "SYSTEMDRIVE", "PROGRAMDATA", "WINDIR", "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "COMSPEC", "PATHEXT", "USERPROFILE"}
    env = {k:v for k,v in os.environ.items() if k.upper() in safe}
    env.update(NEXT_TELEMETRY_DISABLED="1", PYTHONDONTWRITEBYTECODE="1")
    token = secrets.token_hex(12)
    image = "pgvector/pgvector:pg17"
    command(["docker", "image", "inspect", image], env=env)
    container = command(["docker","run","--pull","never","--rm","-d","--name",f"broadbridge-questionnaire-{token}","--label",f"broadbridge.questionnaire-test={token}","-e","POSTGRES_HOST_AUTH_METHOD=trust","-e","POSTGRES_USER=broadbridge_test","-e","POSTGRES_DB=broadbridge_test","-p","127.0.0.1::5432",image], env=env)
    if not re.fullmatch(r"[a-f0-9]{64}", container): raise RuntimeError("Unknown container identity")
    try:
        for _ in range(60):
            if subprocess.run(["docker","exec",container,"pg_isready","-U","broadbridge_test"],env=env,capture_output=True).returncode == 0: break
            time.sleep(.5)
        else: raise RuntimeError("Local database did not start")
        port = command(["docker","port",container,"5432/tcp"],env=env)
        if not re.fullmatch(r"127\.0\.0\.1:[0-9]+",port): raise RuntimeError("Local database must bind loopback")
        dsn = f"postgresql://broadbridge_test:local-only@{port}/broadbridge_test"
        sys.path.insert(0,str(repo / "packs/oil-gas/scripts"))
        import db
        with psycopg.connect(dsn) as conn:
            migrations = db.migrate(conn)["migrations"]
            registration = register(conn,repo)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0)); app_port = sock.getsockname()[1]
        with ExitStack() as stack:
            endpoint = serve_http(stack,sql_handler(dsn)) + "/sql"
            env.update(NODE_ENV="development", BROADBRIDGE_DATABASE_URL=dsn, DATABASE_URL_UNPOOLED=dsn,
                       CAPTURE_LOCAL_INGESTION_TEST="1",CAPTURE_TEST_SQL_ENDPOINT=endpoint, AUTH_URL=f"http://127.0.0.1:{app_port}",
                       AUTH_SECRET=secrets.token_hex(32),CAPTURE_TEST_EMAIL="questionnaire-browser@example.invalid",
                       CAPTURE_ALLOWED_EMAILS="questionnaire-browser@example.invalid",CAPTURE_DB_TEST_HOST="127.0.0.1",
                       CAPTURE_TEST_OUTBOX=str(output / "auth-outbox.jsonl"),CAPTURE_TEST_RUN_ROOT=str(output))
            checks = [
                ("repository",["node","node_modules/vitest/vitest.mjs","run","tests/questionnaire-repository.test.ts"]),
                ("browser",["node","node_modules/@playwright/test/cli.js","test","e2e/questionnaire.spec.ts"]),
            ]
            results = {}
            for label,args in checks:
                with (output / f"{label}.log").open("w",encoding="utf-8") as log:
                    result = subprocess.run(args,cwd=repo / "apps/capture",env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240)
                results[label] = result.returncode
                print(f"{label}: exit {result.returncode}",flush=True)
                if result.returncode: break
            with psycopg.connect(dsn) as conn:
                responses = conn.execute("SELECT count(*) FROM broadbridge.current_questionnaire_responses").fetchone()[0]
                revisions = conn.execute("SELECT count(*) FROM broadbridge.questionnaire_responses").fetchone()[0]
            report = {"synthetic_only":True,"database":"disposable_local_postgresql_17","migrations":migrations,"packet":registration,"checks":results,"reviewers":responses,"revisions":revisions,"cloud_calls":False}
            (output / "report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
            if any(results.values()) or "browser" not in results: raise RuntimeError("Local acceptance failed; inspect local logs")
            return report
    finally:
        outbox = output / "auth-outbox.jsonl"
        if outbox.exists(): outbox.unlink()
        owner = command(["docker","inspect","--format",'{{ index .Config.Labels "broadbridge.questionnaire-test" }}',container],env=env)
        if owner != token: raise RuntimeError("Container ownership changed; refusing cleanup")
        command(["docker","rm","--force",container],env=env)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    args = parser.parse_args()
    try:
        with isolated_libpq_environment():
            print(json.dumps(run(Path(__file__).resolve().parents[1],args.output.resolve()),indent=2))
    except Exception as exc:
        print(f"Local acceptance failed ({type(exc).__name__}); no existing database was used.",file=sys.stderr)
        sys.exit(1)
