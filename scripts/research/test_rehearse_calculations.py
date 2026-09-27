"""No real data, network, human approval or release in the SD-04 rehearsal."""
import importlib.util
import json
import os
from pathlib import Path
import socket

import pytest


def module():
    path = Path(__file__).with_name("rehearse_calculations.py")
    assert path.exists(), "Calculation admission rehearsal not implemented"
    spec = importlib.util.spec_from_file_location("rehearse_calculations", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_calculation_artifact_admission_remains_pending(tmp_path, monkeypatch):
    foundry = os.environ.get("SLM_FOUNDRY_PATH")
    if not foundry:
        pytest.skip("Select Foundry with SLM_FOUNDRY_PATH")
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("No network permitted"))
    out = tmp_path / "calculation"
    assert module().main(["--mock", "--foundry", foundry, "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text())
    assert report["model_calls"] == 0
    assert report["fixed_vector_statuses"] == ["pass", "needs_review", "fail", "fail", "needs_review"]
    assert report["release_blocked_without_review"] is True
    assert set(report["rejections"]) == {"pending_artifact_rights", "revoked_artifact_rights", "historical_holdout", "changed_artifact_bytes"}
    packet = json.loads((out / "ratio.packet.json").read_text())
    assert packet["checks"]["arithmetic"]["status"] == "pass"
    assert packet["checks"]["physical_assumptions"]["status"] == "needs_review"
    assert packet["status"] == "pending" and packet["training_approved"] is False
    assert len(packet["candidate"]["source_refs"]) == 2
    assert packet["candidate"]["family_id"] == "SYN-RATIO-FAMILY"
    with pytest.raises(ValueError, match="new absolute"):
        module().main(["--mock", "--foundry", foundry, "--out", str(out)])


def test_rehearsal_requires_explicit_mock():
    with pytest.raises(SystemExit):
        module().main(["--foundry", "relative", "--out", "relative"])
