import importlib.util
import json
import os
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("rehearse_openrouter_intake.py")


def test_offline_multiformat_rehearsal(tmp_path):
    foundry = os.environ.get("SLM_FOUNDRY_PATH")
    if not foundry:
        pytest.skip("Set SLM_FOUNDRY_PATH to the explicit generic helper checkout")
    spec = importlib.util.spec_from_file_location("rehearse_helper", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out = tmp_path / "rehearsal"
    assert module.main(["--foundry", foundry, "--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text())
    assert report["network_used"] is False
    assert report["fixture_count"] == 5
    assert report["candidate_count"] == 5
    assert {row["format"] for row in report["rows"]} == {"txt", "csv", "eml", "docx", "xlsx"}
    assert all(row["extraction"] == "complete" and row["review"] == "pending" for row in report["rows"])
    assert report["release_blocked_without_technical_review"] is True
    assert report["confidential_pack_blocked"] is True
