"""Failure boundaries when file publication is coordinated with a database transaction."""
import importlib
from pathlib import Path
import sys
import types

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def publisher():
    assert (SCRIPTS / "db_publication.py").exists(), "Coordinated publisher missing"
    return importlib.import_module("db_publication")


class Transaction:
    def __init__(self, events, fail_commit=False):
        self.events, self.fail_commit = events, fail_commit

    def __enter__(self):
        self.events.append("begin")
        return self

    def __exit__(self, kind, value, traceback):
        self.events.append("rollback" if kind else "commit")
        if not kind and self.fail_commit:
            raise RuntimeError("injected commit failure")


def test_file_appears_inside_transaction_before_commit(tmp_path, monkeypatch):
    module = publisher()
    staged, destination = tmp_path / "staged.json", tmp_path / "published.json"
    staged.write_text('{"value": 1}')
    events = []
    class ObserveCommit(Transaction):
        def __exit__(self, *args):
            assert destination.read_text() == '{"value": 1}'
            return super().__exit__(*args)
    monkeypatch.setitem(sys.modules, "db", types.SimpleNamespace(connection=lambda: ObserveCommit(events)))
    module.publish_staged(staged, destination, db_write=lambda conn: events.append("upsert"))
    assert events == ["begin", "upsert", "commit"]
    assert destination.exists() and not staged.exists()


@pytest.mark.parametrize("failure", ["upsert", "rename", "commit"])
def test_failed_publication_restores_files_and_does_not_overwrite(tmp_path, monkeypatch, failure):
    module = publisher()
    staged, destination = tmp_path / "stage", tmp_path / "destination"
    staged.mkdir()
    (staged / "case.json").write_text("canonical content")
    events = []
    monkeypatch.setitem(sys.modules, "db", types.SimpleNamespace(connection=lambda: Transaction(events, failure == "commit")))
    def upsert(conn):
        if failure == "upsert":
            raise RuntimeError("injected write failure")
    if failure == "rename":
        original = Path.rename
        def fail_rename(path, target):
            if path == staged: raise OSError("injected filesystem failure")
            return original(path, target)
        monkeypatch.setattr(Path, "rename", fail_rename)
    with pytest.raises(RuntimeError, match="publication"):
        module.publish_staged(staged, destination, db_write=upsert)
    assert not destination.exists()
    assert (staged / "case.json").read_text() == "canonical content"
    assert events[-1] == ("commit" if failure == "commit" else "rollback")


def test_existing_output_refuses_before_opening_database(tmp_path, monkeypatch):
    module = publisher()
    staged, destination = tmp_path / "stage", tmp_path / "result"
    staged.write_text("new")
    destination.write_text("prior review")
    monkeypatch.setitem(sys.modules, "db", types.SimpleNamespace(connection=lambda: pytest.fail("Opened DB before output check")))
    with pytest.raises(ValueError):
        module.publish_staged(staged, destination, db_write=lambda conn: None)
    assert destination.read_text() == "prior review"


def test_file_only_path_never_loads_database(tmp_path, monkeypatch):
    staged, destination = tmp_path / "stage", tmp_path / "result"
    staged.write_text("local only")
    monkeypatch.setitem(sys.modules, "db", None)
    publisher().publish_staged(staged, destination)
    assert destination.read_text() == "local only"
