"""Offline source parsing and local evidence intake; DB integrity has separate tests."""
import hashlib
import importlib
import json
from pathlib import Path
import socket
import subprocess
import sys
from types import SimpleNamespace

import pytest

PACK = Path(__file__).resolve().parents[1]
FIXTURES = PACK / "tests/fixtures"
SCRIPTS = PACK / "scripts"
sys.path.insert(0, str(SCRIPTS))


def intake(name):
    assert (SCRIPTS / f"{name}.py").is_file(), f"{name} implementation is missing"
    return importlib.import_module(name)


def test_five_synthetic_sources_preserve_original_json_fields():
    rows = intake("register_sources").load_registry(FIXTURES / "db_sources.json")
    assert [row["source_id"] for row in rows] == [
        "DB-TEST-001", "DB-TEST-002", "DB-TEST-003", "DB-TEST-004", "DB-TEST-005"]
    assert all(row["synthetic"] is True for row in rows)
    assert rows[0]["metadata"] == {"fixture_number": 1}
    assert all("permitted_use" not in row and "approval_status" not in row for row in rows)


def test_csv_preserves_all_source_fields_and_empty_cells(tmp_path):
    source = tmp_path / "sources.csv"
    source.write_text('source_id,name,observed_rights,custom_field\n'
                      'LOCAL-1,"Synthetic, quoted name",,Keep this text\n', encoding="utf-8-sig")
    assert intake("register_sources").load_registry(source) == [{
        "source_id": "LOCAL-1", "name": "Synthetic, quoted name", "observed_rights": "",
        "custom_field": "Keep this text"}]


@pytest.mark.parametrize("payload", [
    {}, ["not a record"], [{}], [{"source_id": None}], [{"source_id": 3}],
    [{"source_id": ""}], [{"source_id": "   "}], [{"source_id": " source-1"}],
    [{"source_id": "SOURCE-1"}, {"source_id": "source-1"}],
])
def test_invalid_json_registry_is_rejected_before_database_connection(tmp_path, monkeypatch, payload):
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    def forbidden_connection():
        pytest.fail("Invalid registry reached the database boundary")
    monkeypatch.setitem(sys.modules, "db", SimpleNamespace(connection=forbidden_connection))
    with pytest.raises(ValueError):
        intake("register_sources").register_sources(source, use_db=True, actor="reviewer@example.test")


@pytest.mark.parametrize("content", [
    "name\nSynthetic\n", "source_id,source_id\nONE,TWO\n",
    "source_id,name\nONE,Name,extra\n", "source_id,name\nONE\n",
])
def test_malformed_csv_registry_is_rejected(tmp_path, content):
    source = tmp_path / "invalid.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        intake("register_sources").load_registry(source)


def test_file_only_source_validation_has_no_network_or_database_access(monkeypatch, capsys):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("Intake opened a socket"))
    monkeypatch.setitem(sys.modules, "db", None)
    assert intake("register_sources").main([str(FIXTURES / "db_sources.json")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == {"source_count": 5, "database_written": False}


def test_source_cli_sanitizes_database_boundary_errors(monkeypatch, capsys):
    def failing_connection():
        raise RuntimeError("postgresql://reviewer:private-password@db.example.test/project")
    monkeypatch.setitem(sys.modules, "db", SimpleNamespace(connection=failing_connection))
    result = intake("register_sources").main([
        str(FIXTURES / "db_sources.json"), "--db", "--actor", "reviewer@example.test"])
    captured = capsys.readouterr()
    assert result == 2
    assert "private-password" not in captured.err + captured.out
    assert "RuntimeError" in captured.err


def test_evidence_cli_reports_publication_failure_without_output(tmp_path, monkeypatch, capsys):
    import db_publication
    def failed_publication(*args, **kwargs):
        raise RuntimeError("Database/file publication failed; staged output restored")
    monkeypatch.setattr(db_publication, "publish_staged", failed_publication)
    output = tmp_path / "evidence.json"
    result = intake("extract_evidence").main([
        str(FIXTURES / "evidence_sample.txt"), "--source-id", "DB-TEST-001",
        "--evidence-id", "EVIDENCE-TEST-001", "--output", str(output)])
    assert result == 2
    assert "publication failed" in capsys.readouterr().err
    assert not output.exists()
    assert not list(tmp_path.glob(".evidence-intake-*"))


@pytest.mark.parametrize("suffix,mime_type", [(".txt", "text/plain"), (".md", "text/markdown")])
def test_evidence_keeps_exact_text_and_hashes_original_bytes(tmp_path, monkeypatch, suffix, mime_type):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("Intake opened a socket"))
    monkeypatch.setitem(sys.modules, "db", None)
    original = tmp_path / ("original" + suffix)
    raw = "Synthetic observation: 12 °C.\r\nNo later outcome supplied.\r\n".encode("utf-8")
    original.write_bytes(raw)
    output = tmp_path / "evidence.json"
    record = intake("extract_evidence").extract_evidence(
        original, output, source_id="DB-TEST-001", evidence_id="EVIDENCE-TEST-001", case_id="SYN-001")
    assert record == {
        "evidence_id": "EVIDENCE-TEST-001", "source_id": "DB-TEST-001", "case_id": "SYN-001",
        "text": "Synthetic observation: 12 °C.\r\nNo later outcome supplied.\r\n",
        "sha256": hashlib.sha256(raw).hexdigest(), "original_path": str(original.resolve()),
        "mime_type": mime_type,
    }
    assert json.loads(output.read_text(encoding="utf-8")) == record
    assert original.read_bytes() == raw


def test_evidence_without_case_has_no_inferred_case_or_permissions(tmp_path):
    record = intake("extract_evidence").extract_evidence(
        FIXTURES / "evidence_sample.txt", tmp_path / "evidence.json",
        source_id="DB-TEST-001", evidence_id="EVIDENCE-TEST-001")
    assert set(record) == {"evidence_id", "source_id", "text", "sha256", "original_path", "mime_type"}


@pytest.mark.parametrize("filename", ["input.pdf", "input.docx", "input.html", "input.json"])
def test_evidence_refuses_unsupported_formats_without_output(tmp_path, filename):
    original = tmp_path / filename
    original.write_bytes(b"Synthetic content")
    output = tmp_path / "evidence.json"
    with pytest.raises(ValueError, match=r"\.txt.*\.md"):
        intake("extract_evidence").extract_evidence(
            original, output, source_id="DB-TEST-001", evidence_id="EVIDENCE-TEST-001")
    assert not output.exists()


def test_evidence_refuses_invalid_utf8_without_output(tmp_path):
    original = tmp_path / "invalid.txt"
    original.write_bytes(b"invalid: \xff")
    output = tmp_path / "evidence.json"
    with pytest.raises(ValueError, match="UTF-8"):
        intake("extract_evidence").extract_evidence(
            original, output, source_id="DB-TEST-001", evidence_id="EVIDENCE-TEST-001")
    assert not output.exists()


@pytest.mark.parametrize("field,value", [("source_id", ""), ("evidence_id", "  "), ("case_id", " SYN-001 ")])
def test_evidence_requires_explicit_clean_identifiers_before_output(tmp_path, field, value):
    identifiers = {"source_id": "DB-TEST-001", "evidence_id": "EVIDENCE-TEST-001"}
    identifiers[field] = value
    output = tmp_path / "evidence.json"
    with pytest.raises(ValueError, match=field):
        intake("extract_evidence").extract_evidence(FIXTURES / "evidence_sample.txt", output, **identifiers)
    assert not output.exists()


def test_evidence_does_not_overwrite_existing_file(tmp_path):
    output = tmp_path / "evidence.json"
    output.write_bytes(b"Keep the earlier evidence")
    with pytest.raises((ValueError, FileExistsError)):
        intake("extract_evidence").extract_evidence(
            FIXTURES / "evidence_sample.txt", output,
            source_id="DB-TEST-001", evidence_id="EVIDENCE-TEST-001")
    assert output.read_bytes() == b"Keep the earlier evidence"


def test_evidence_cli_writes_requested_output_and_requires_actor_for_db(tmp_path):
    assert (SCRIPTS / "extract_evidence.py").is_file(), "extract_evidence implementation is missing"
    output = tmp_path / "evidence.json"
    args = [sys.executable, str(SCRIPTS / "extract_evidence.py"), str(FIXTURES / "evidence_sample.txt"),
            "--source-id", "DB-TEST-001", "--evidence-id", "EVIDENCE-TEST-001", "--output", str(output)]
    rejected = subprocess.run(args + ["--db"], capture_output=True, text=True)
    assert rejected.returncode == 2
    assert "actor" in rejected.stderr.lower()
    assert not output.exists()
    accepted = subprocess.run(args, capture_output=True, text=True)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(output.read_text())["source_id"] == "DB-TEST-001"
