"""Migration URL routing policy; all environment values and connections are fake."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / "scripts"))
SPEC = importlib.util.spec_from_file_location("capture_db_configuration", PACK / "scripts/db.py")
db = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(db)

POOLED = "postgresql://capture:pooled-secret@ep-quiet-cloud-pooler.us-east-1.aws.neon.tech/broadbridge?sslmode=require"
DIRECT = "postgresql://capture:direct-secret@ep-quiet-cloud.us-east-1.aws.neon.tech/broadbridge?sslmode=require&channel_binding=require"


@pytest.fixture
def configured(monkeypatch):
    environment = {"BROADBRIDGE_DATABASE_URL": POOLED, "DATABASE_URL_UNPOOLED": DIRECT,
                   "DATABASE_URL": "postgresql://unrelated:never-used@other.example/other"}
    monkeypatch.setattr(db.os, "environ", environment)
    calls = []

    class FakeConnection:
        def __init__(self, url):
            self.url = url
            self.exit_kind = None

        def __enter__(self):
            return self

        def __exit__(self, kind, *_):
            self.exit_kind = kind

    def connect(url, **options):
        result = FakeConnection(url)
        calls.append((url, options, result))
        return result

    monkeypatch.setattr(db.psycopg, "connect", connect)
    return environment, calls


def test_migration_selects_matching_neon_direct_url(configured):
    _, calls = configured
    with db.connection(migration=True) as conn:
        assert conn.url == DIRECT
    assert calls[0][1] == {"autocommit": False, "prepare_threshold": None, "connect_timeout": 10}


def test_normal_connection_ignores_unpooled_and_generic_urls(configured):
    environment, calls = configured
    environment["DATABASE_URL_UNPOOLED"] = "invalid-other-target"
    with db.connection() as conn:
        assert conn.url == POOLED
    assert calls[0][0] == POOLED


@pytest.mark.parametrize("missing", ["BROADBRIDGE_DATABASE_URL", "DATABASE_URL_UNPOOLED"])
def test_migration_requires_both_explicit_variables(configured, missing):
    environment, calls = configured
    environment.pop(missing)
    with pytest.raises(RuntimeError, match=missing):
        with db.connection(migration=True):
            pass
    assert not calls


@pytest.mark.parametrize("target", [
    DIRECT.replace("ep-quiet-cloud.", "ep-other-branch."),
    DIRECT.replace("us-east-1", "eu-west-1"),
    DIRECT.replace("/broadbridge?", "/other-database?"),
    DIRECT.replace("capture:", "other-user:"),
    DIRECT.replace(".tech/broadbridge", ".tech:6432/broadbridge"),
    POOLED,
    "postgresql://capture:direct-secret@ep-quiet-cloud-pooler.us-east-1.aws.neon.tech/broadbridge",
    "postgresql://capture:direct-secret@ep-quiet-cloud.us-east-1.aws.neon.tech.attacker.test/broadbridge",
])
def test_migration_refuses_mismatch_or_pooled_target(configured, target):
    environment, calls = configured
    environment["DATABASE_URL_UNPOOLED"] = target
    with pytest.raises(RuntimeError):
        with db.connection(migration=True):
            pass
    assert not calls


@pytest.mark.parametrize("variable", ["BROADBRIDGE_DATABASE_URL", "DATABASE_URL_UNPOOLED"])
@pytest.mark.parametrize("override", ["host=other.example", "hostaddr=203.0.113.1", "user=other", "dbname=other", "port=6543", "service=other", "options=endpoint%3Dep-other"])
def test_migration_refuses_url_routing_overrides(configured, variable, override):
    environment, calls = configured
    environment[variable] += "&" + override
    with pytest.raises(RuntimeError):
        with db.connection(migration=True):
            pass
    assert not calls


@pytest.mark.parametrize("override", ["PGHOSTADDR", "PGSERVICE", "PGPORT", "PGOPTIONS"])
def test_migration_refuses_inherited_libpq_routing_overrides(configured, override):
    environment, calls = configured
    environment[override] = "must-not-affect-routing"
    with pytest.raises(RuntimeError):
        with db.connection(migration=True):
            pass
    assert not calls


@pytest.mark.parametrize("target", [
    "host=ep-quiet-cloud.us-east-1.aws.neon.tech dbname=broadbridge user=capture",
    DIRECT.replace("postgresql:", "https:"),
    DIRECT.replace("capture:direct-secret@", ""),
    DIRECT.replace("/broadbridge?", "/?"),
    DIRECT.replace(".tech/broadbridge", ".tech:invalid/broadbridge"),
    DIRECT + "#hidden-fragment",
])
def test_malformed_migration_configuration_is_sanitized(configured, target):
    environment, calls = configured
    environment["DATABASE_URL_UNPOOLED"] = target
    with pytest.raises(RuntimeError) as error:
        with db.connection(migration=True):
            pass
    assert "direct-secret" not in str(error.value)
    assert "pooled-secret" not in str(error.value)
    assert target not in str(error.value)
    assert not calls


def test_migration_compares_decoded_identity_and_default_port(configured):
    environment, calls = configured
    environment["BROADBRIDGE_DATABASE_URL"] = POOLED.replace("capture:", "capt%75re:").replace("/broadbridge?", "/broad%62ridge?")
    environment["DATABASE_URL_UNPOOLED"] = DIRECT.replace(".tech/broadbridge", ".tech:5432/broadbridge")
    with db.connection(migration=True):
        pass
    assert calls[0][0] == environment["DATABASE_URL_UNPOOLED"]


def test_migration_accepts_matching_explicit_local_direct_urls(configured):
    environment, calls = configured
    local = "postgresql://capture@127.0.0.1:46547/broadbridge_test"
    environment.update(BROADBRIDGE_DATABASE_URL=local, DATABASE_URL_UNPOOLED=local)
    with db.connection(migration=True):
        pass
    assert calls[0][0] == local


def test_local_migration_does_not_guess_hostname_alias_equivalence(configured):
    environment, calls = configured
    environment["BROADBRIDGE_DATABASE_URL"] = "postgresql://capture@localhost:46547/broadbridge_test"
    environment["DATABASE_URL_UNPOOLED"] = "postgresql://capture@127.0.0.1:46547/broadbridge_test"
    with pytest.raises(RuntimeError):
        with db.connection(migration=True):
            pass
    assert not calls


def test_local_socket_paths_are_compared_case_sensitively(configured):
    environment, calls = configured
    environment["BROADBRIDGE_DATABASE_URL"] = "postgresql://capture@%2Ftmp%2FBroadbridge/broadbridge_test"
    environment["DATABASE_URL_UNPOOLED"] = "postgresql://capture@%2Ftmp%2Fbroadbridge/broadbridge_test"
    with pytest.raises(RuntimeError):
        with db.connection(migration=True):
            pass
    assert not calls


@pytest.mark.parametrize("command,expected", [("migrate", DIRECT), ("status", POOLED), ("reset-dev", POOLED)])
def test_cli_selects_migration_connection_only_for_migrate(configured, monkeypatch, command, expected):
    _, calls = configured
    monkeypatch.setattr(db, "migrate", lambda conn: {"used": conn.url == expected})
    monkeypatch.setattr(db, "status", lambda conn: {"used": conn.url == expected})
    monkeypatch.setattr(db, "_reset_schema", lambda conn: None)
    monkeypatch.setattr(db, "_check_reset_target", lambda *args: None)
    monkeypatch.setattr(db.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="codex/test"))
    args = [command] + (["--branch", "test"] if command == "reset-dev" else [])
    assert db.main(args) == 0
    assert calls[0][0] == expected


def test_migration_connection_failure_does_not_expose_url(configured, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise db.psycopg.OperationalError("connection failed: " + DIRECT)
    monkeypatch.setattr(db.psycopg, "connect", fail)
    assert db.main(["migrate"]) == 2
    output = capsys.readouterr().err
    assert "Unable to connect" in output
    assert "direct-secret" not in output and DIRECT not in output


def test_migration_preserves_transaction_rollback_context(configured):
    _, calls = configured
    with pytest.raises(ValueError, match="caller failed"):
        with db.connection(migration=True):
            raise ValueError("caller failed")
    assert calls[0][2].exit_kind is ValueError
