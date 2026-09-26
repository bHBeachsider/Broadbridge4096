"""Batch selection, failure isolation and one-session PowerShell orchestration, offline."""
import importlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys

import pytest

PACK = Path(__file__).resolve().parents[1]
REPO = PACK.parents[1]
FIXTURES = PACK / "tests/fixtures"
sys.path.insert(0, str(PACK / "scripts"))


@pytest.fixture
def export_file(tmp_path):
    export = json.loads((FIXTURES / "capture_export.json").read_text(encoding="utf-8"))
    export["cases"] += [json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
                        for name in ("SYN-TRAIN-001", "SYN-TRAIN-002")]
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(export), encoding="utf-8")
    return path


def batch():
    assert (PACK / "scripts/batch_cases.py").is_file(), "Batch implementation is missing"
    return importlib.import_module("batch_cases")


def test_mock_batch_runs_three_cases_without_network(export_file, tmp_path, monkeypatch):
    engine = batch()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("Mock opened a socket"))
    run = tmp_path / "run"
    manifest = engine.prepare_batch(export_file, run, "SYN-001,SYN-TRAIN-001,SYN-TRAIN-002",
                                    mock_response=FIXTURES / "SYN-001.mock_brief.json")
    assert manifest["mode"] == "mock"
    result = engine.run_batch(run)
    assert [row["case_id"] for row in result] == ["SYN-001", "SYN-TRAIN-001", "SYN-TRAIN-002"]
    assert all(row["status"] == "completed" and row["brief_valid"] for row in result)
    assert len(list((run / "eval").glob("scorecard_*.md"))) == 3
    assert all(json.loads(p.read_text())["mode"] == "mock" for p in run.glob("cases/*/brief_run.json"))
    assert "MOCK" in (run / "batch_summary.md").read_text()
    assert len((run / "data/train_candidates.jsonl").read_text().splitlines()) == 2
    with pytest.raises((ValueError, FileExistsError)):
        engine.run_batch(run)


def test_all_signed_excludes_draft_seed_even_in_mock_mode(export_file, tmp_path):
    manifest = batch().prepare_batch(export_file, tmp_path / "run", "all-signed",
                                    mock_response=FIXTURES / "SYN-001.mock_brief.json")
    assert [row["case_id"] for row in manifest["selected_cases"]] == ["SYN-TRAIN-001", "SYN-TRAIN-002"]


@pytest.mark.parametrize("selection", ["SYN-001", "missing", "SYN-TRAIN-001,", "SYN-TRAIN-001,SYN-TRAIN-001", "all-signed,SYN-001"])
def test_live_preflight_refuses_invalid_selection_before_session(export_file, tmp_path, selection):
    with pytest.raises(ValueError):
        batch().prepare_batch(export_file, tmp_path / "run", selection)


def test_any_rejected_case_stops_complete_export_before_session(export_file, tmp_path):
    data = json.loads(export_file.read_text())
    data["cases"][2]["reviewer_signoff"]["signed"] = False
    export_file.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="reject"):
        batch().prepare_batch(export_file, tmp_path / "run", "SYN-TRAIN-001")


def test_prompt_leak_is_caught_in_batch_preflight(export_file, tmp_path):
    data = json.loads(export_file.read_text())
    data["cases"][2]["decision_time"]["b1_trigger"] += data["cases"][2]["questions"][0]["reference_answer"]
    export_file.write_text(json.dumps(data))
    with pytest.raises(AssertionError, match="leak"):
        batch().prepare_batch(export_file, tmp_path / "run", "all-signed")


def test_bad_mock_never_selects_live_mode(export_file, tmp_path):
    response = tmp_path / "bad.json"
    response.write_text("null")
    with pytest.raises(ValueError):
        batch().prepare_batch(export_file, tmp_path / "run", "all-signed", mock_response=response)


def test_run_detects_case_change_before_model(export_file, tmp_path, monkeypatch):
    engine = batch()
    run = tmp_path / "run"
    engine.prepare_batch(export_file, run, "all-signed")
    path = run / "data/cases/SYN-TRAIN-002.json"
    data = json.loads(path.read_text())
    data["decision_time"]["b1_trigger"] += " changed"
    path.write_text(json.dumps(data))
    monkeypatch.setattr(engine, "create_run", lambda *a, **k: pytest.fail("Changed snapshot reached model"))
    with pytest.raises(ValueError, match="changed"):
        engine.run_batch(run)


def test_existing_review_blocks_batch_before_model(export_file, tmp_path, monkeypatch):
    engine = batch()
    run = tmp_path / "run"
    engine.prepare_batch(export_file, run, "all-signed")
    path = run / "eval/scorecard_SYN-TRAIN-002.md"
    path.write_text("Existing completed reviewer record")
    monkeypatch.setattr(engine, "create_run", lambda *a, **k: pytest.fail("Existing review reached model"))
    with pytest.raises(ValueError, match="existing"):
        engine.run_batch(run)
    assert path.read_text() == "Existing completed reviewer record"


def test_failure_does_not_discard_other_cases(export_file, tmp_path, monkeypatch):
    engine = batch()
    run = tmp_path / "run"
    engine.prepare_batch(export_file, run, "all-signed")
    real_create = engine.create_run
    response = json.loads((FIXTURES / "SYN-001.mock_brief.json").read_text())
    def model(case, **kwargs):
        if case["case_id"] == "SYN-TRAIN-001":
            raise ValueError("Brief schema rejected response")
        return real_create(case, mock_response=response)
    monkeypatch.setattr(engine, "create_run", model)
    rows = engine.run_batch(run)
    assert [(r["status"], r["brief_valid"]) for r in rows] == [("failed", False), ("completed", True)]
    assert "Brief schema rejected" in rows[0]["error"]
    assert (run / "eval/scorecard_SYN-TRAIN-002.md").exists()
    assert not (run / "eval/scorecard_SYN-TRAIN-001.md").exists()


def invoke_ps(script, tmp_path, export_file, selection, *extra):
    pwsh = shutil.which("pwsh")
    assert pwsh, "PowerShell is needed to verify the requested Windows runner"
    command = [pwsh, "-NoProfile", "-NonInteractive", "-File", str(script), "-Export", str(export_file),
               "-CaseId", selection, "-RunRoot", str(tmp_path / "run"), "-Python", sys.executable, *map(str, extra)]
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60)


def test_powershell_mock_entrypoint_never_invokes_aws_or_ssh(export_file, tmp_path):
    script = REPO / "scripts/first_case.ps1"
    assert script.exists(), "PowerShell batch entrypoint is missing"
    wrapper = tmp_path / "offline.ps1"
    wrapper.write_text('''param($Export,$CaseId,$RunRoot,$Python,$MockResponse)
function aws { throw 'Offline path called AWS' }
function ssh { throw 'Offline path called SSH' }
function Start-Process { throw 'Offline path launched a process' }
function Invoke-RestMethod { throw 'Offline path called HTTP' }
& 'SCRIPT' @PSBoundParameters
exit $LASTEXITCODE
'''.replace("SCRIPT", str(script).replace("'", "''")), encoding="utf-8")
    result = invoke_ps(wrapper, tmp_path, export_file, "SYN-001,SYN-TRAIN-001,SYN-TRAIN-002",
                       "-MockResponse", FIXTURES / "SYN-001.mock_brief.json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(list((tmp_path / "run/eval").glob("scorecard_*.md"))) == 3
    assert "SYN-TRAIN-002" in result.stdout


@pytest.mark.parametrize("failure", ["none", "wait", "model", "stop", "busy", "log"])
def test_powershell_uses_one_session_and_tears_down_on_failures(export_file, tmp_path, failure):
    script = REPO / "scripts/first_case.ps1"
    assert script.exists(), "PowerShell batch entrypoint is missing"
    foundry = tmp_path / "foundry"
    (foundry / "src").mkdir(parents=True)
    (foundry / "src/__init__.py").write_text("")
    (foundry / "src/llm_policy.py").write_text("def require_local_for_pack(pack): pass\n")
    response = str(FIXTURES / "SYN-001.mock_brief.json")
    log = tmp_path / "events.txt"
    (foundry / "src/llm_client.py").write_text(
        "import json\nfrom pathlib import Path\n"
        f"def chat(messages, **kwargs):\n    p=Path({str(log)!r})\n"
        "    with p.open('a') as f: f.write('model\\n')\n"
        + ("    raise RuntimeError('Synthetic model failure')\n" if failure == "model" else f"    return Path({response!r}).read_text(encoding='utf-8')\n"), encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(foundry)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(foundry), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "test"], check=True, capture_output=True)
    key = tmp_path / "test key.pem"
    key.write_text("synthetic unused key")
    wrapper = tmp_path / "session.ps1"
    wrapper.write_text('''param($Export,$CaseId,$RunRoot,$Python,$Foundry,$Key)
$EventLog = 'LOG'
function aws {
  $global:LASTEXITCODE = 0
  $a = $args -join ' '
  Add-Content -LiteralPath $EventLog -Value $a
  if ($a -match 'start-instances') { return '{}' }
  if ($a -match 'instance-running' -and 'FAILURE' -eq 'wait') { $global:LASTEXITCODE = 2; return }
  if ($a -match 'stop-instances' -and 'FAILURE' -in @('stop','log')) {
    if ('FAILURE' -eq 'log') { New-Item -ItemType Directory -Path (Join-Path $RunRoot 'teardown_error.txt') | Out-Null }
    $global:LASTEXITCODE = 2; return
  }
  if ($a -match 'State.Name') { if ('FAILURE' -eq 'busy') { return 'running' }; return 'stopped' }
  if ($a -match 'PublicIpAddress') { return '192.0.2.1' }
}
function Start-Process { param($FilePath,$ArgumentList,[switch]$PassThru,$WindowStyle,$RedirectStandardError,$RedirectStandardOutput)
  Add-Content -LiteralPath $EventLog -Value ('tunnel ' + ($ArgumentList -join ' '))
  return [pscustomobject]@{ Id = 999999; HasExited = $false }
}
function Stop-Process { param($Id,[switch]$Force,$ErrorAction) Add-Content -LiteralPath $EventLog -Value 'tunnel-stop' }
function Invoke-RestMethod { param($Uri,$Method,$TimeoutSec,$ContentType,$Body)
  if ($Uri -like '*/api/tags') { return @{ models = @(@{name='qwen3:8b';digest='synthetic'}) } }
  return @{ template = 'SYNTHETIC TEMPLATE' }
}
$env:OLLAMA_URL = 'original-url'
$env:OLLAMA_MODEL = 'original-model'
& 'SCRIPT' @PSBoundParameters
Add-Content -LiteralPath $EventLog -Value ('restored ' + $env:OLLAMA_URL + ' ' + $env:OLLAMA_MODEL)
exit $LASTEXITCODE
'''.replace("LOG", str(log).replace("'", "''")).replace("FAILURE", failure)
        .replace("SCRIPT", str(script).replace("'", "''")), encoding="utf-8")
    result = invoke_ps(wrapper, tmp_path, export_file, "all-signed", "-Foundry", foundry, "-Key", key)
    events = log.read_text().splitlines()
    assert sum("start-instances" in line for line in events) == (0 if failure == "busy" else 1)
    assert sum("stop-instances" in line for line in events) == (0 if failure == "busy" else 1)
    assert sum(line.startswith("tunnel ") for line in events) == (0 if failure in ("wait", "busy") else 1)
    assert result.returncode == (0 if failure == "none" else 2), result.stdout + result.stderr
    assert 'restored original-url original-model' in events
    if failure not in ("wait", "busy"):
        assert events.count("model") == 2
        assert events.count("tunnel-stop") == 1
    if failure == "none":
        assert len(list((tmp_path / "run/eval").glob("scorecard_*.md"))) == 2
    assert (tmp_path / "run/batch_summary.md").exists()
