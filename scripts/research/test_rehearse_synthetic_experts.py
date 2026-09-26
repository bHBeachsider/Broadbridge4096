import importlib.util
import json
import os
from pathlib import Path
import socket

import pytest


def load_script():
    path = Path(__file__).with_name("rehearse_synthetic_experts.py")
    assert path.is_file(), "offline synthetic expert rehearsal is not implemented"
    spec = importlib.util.spec_from_file_location("synthetic_expert_rehearsal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rehearsal_keeps_all_examples_pending_and_rejects_bad_inputs(tmp_path, monkeypatch):
    foundry = os.environ.get("SLM_FOUNDRY_PATH")
    if not foundry:
        pytest.skip("SLM_FOUNDRY_PATH must select the explicit Foundry checkout")
    def no_network(*args, **kwargs):
        raise AssertionError("rehearsal must not connect")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    output = tmp_path / "run"
    module = load_script()
    assert module.main(["--foundry", foundry, "--out", str(output)]) == 0
    report = json.loads((output / "report.json").read_text())
    assert report["packet_count"] == 2
    assert report["model_calls"] == 0
    assert report["training_approved"] is False
    assert report["release_blocked_without_review"] is True
    assert set(report["rejections"]) == {"historical_holdout", "revoked_rights", "changed_answer", "invented_quote", "missing_check", "generated_approval"}
    assert all(report["rejections"].values())
    for file in output.glob("*.packet.json"):
        packet = json.loads(file.read_text())
        assert packet["status"] == "pending"
        assert packet["generation_receipt"]["mode"] == "mock"
    before = (output / "report.json").read_bytes()
    with pytest.raises(ValueError, match="new absolute output"):
        module.main(["--foundry", foundry, "--out", str(output)])
    assert (output / "report.json").read_bytes() == before


def test_rehearsal_rejects_relative_checkout_before_import(tmp_path):
    with pytest.raises(ValueError, match="absolute Foundry"):
        load_script().main(["--foundry", "relative", "--out", str(tmp_path / "run")])
