from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


def api():
    path = Path(__file__).with_name("public_review_packet.py")
    assert path.exists(), "public review packet adapter is not implemented"
    spec = importlib.util.spec_from_file_location("public_review_packet", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_answers_and_labels_are_preserved_without_model_names():
    mod = api()
    root = Path(__file__).resolve().parents[2] / "output/openrouter-public-evaluation/public-v1-live"
    packet = mod.build_packet(root, "public-v1")
    assert len(packet["items"]) == 60
    assert sum(item["answer"] is not None for item in packet["items"]) == 30
    first = next(item for item in packet["items"] if item["question_id"] == "PUB-001" and item["response_label"] == "B")
    raw = json.loads((root / "results.json").read_text(encoding="utf-8"))
    original = next(r for r in raw if r["source_id"] == "EIA-REFINING" and r["model_key"] == "qwen")["response"]["answers"][0]
    assert first["answer"] == original
    for word in ("model_key", "provider", "model_mapping_by_source", "receipt"):
        assert word not in json.dumps(packet)
    assert packet["training_approved"] is False
    assert all(i["split"] == "dev" and i["permitted_use"] == "testing_only" for i in packet["items"])


def test_changed_frozen_inputs_are_refused(tmp_path):
    mod = api()
    root = Path(__file__).resolve().parents[2] / "output/openrouter-public-evaluation/public-v1-live"
    for name in mod.FROZEN:
        (tmp_path / name).write_bytes((root / name).read_bytes())
    results = json.loads((tmp_path / "results.json").read_text())
    results[0]["status"] = "changed"
    (tmp_path / "results.json").write_text(json.dumps(results))
    with pytest.raises(ValueError, match="Frozen"):
        mod.build_packet(tmp_path, "public-v1")
