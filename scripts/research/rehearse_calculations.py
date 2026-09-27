"""SD-04 fixed synthetic arithmetic and source-admission rehearsal. No model calls."""
import argparse
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", required=True, action="store_true")
    parser.add_argument("--foundry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.foundry.is_absolute() or not (args.foundry / "src/ingestion/synthetic_review.py").is_file():
        raise ValueError("Choose an absolute Foundry checkout with SD-02 installed")
    if not args.out.is_absolute() or args.out.exists():
        raise ValueError("Choose a new absolute output directory")
    sys.path.insert(0, str(args.foundry.resolve()))
    modules = {n: importlib.import_module("src.ingestion." + n)
               for n in ("contracts", "extract", "curate", "datasets", "synthetic_review")}
    if any(not Path(m.__file__).resolve().is_relative_to(args.foundry.resolve()) for m in modules.values()):
        raise ValueError("Foundry import does not match selected checkout")
    path = Path(__file__).resolve().parents[2] / "packs/oil-gas/scripts/synthetic_checks.py"
    spec = importlib.util.spec_from_file_location("synthetic_checks", path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    givens = {"suction": {"value": "30", "unit": "bar", "basis": "absolute"},
              "discharge": {"value": "60", "unit": "bar", "basis": "absolute"}}
    proposed = {"quantity": "pressure_ratio", "value": "2", "unit": "1"}
    artifacts = []
    for mode in ("positive", "gauge", "zero", "inverse", "power"):
        g, p = deepcopy(givens), deepcopy(proposed)
        if mode == "gauge": g["suction"]["basis"] = "gauge"
        elif mode == "zero": g["suction"]["value"] = "0"
        elif mode == "inverse": p["value"] = "0.5"
        elif mode == "power": p.update(quantity="power", unit="kW")
        artifacts.append(checker.build_calculation_artifact(checker.TEMPLATE_ID, g, p))
    artifact = artifacts[0]
    digest = modules["contracts"].content_hash
    payloads = [b"Synthetic fixture: suction 30 bar absolute; discharge 60 bar absolute. No compressor power data.",
        ("Synthetic calculation artifact, not an original measurement or source quotation.\n"
         + json.dumps(artifact, sort_keys=True, ensure_ascii=False)).encode("utf-8")]
    documents = []
    for identity, payload in zip(("SYN-RATIO-GIVENS", "SYN-RATIO-ARTIFACT"), payloads):
        source = {"schema": "foundry.source_revision/1", "project_id": "broadbridge-calculation-rehearsal",
            "source_id": identity, "revision_id": "fixture-v1", "family_id": "SYN-RATIO-FAMILY",
            "object_key": f"incoming/synthetic/{identity}.txt", "original_filename": identity + ".txt",
            "content_sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
            "media_type": "text/plain", "confidentiality": "public", "relationships": [],
            "permission": {"status": "approved", "permitted_use": "training",
                "rights_basis": "Fabricated software fixture only; no real training grant or expert acceptance.",
                "reviewed_by": "synthetic-fixture-author", "reviewed_at": "2026-09-27T00:00:00Z"}}
        documents.append(modules["extract"].extract_document(source, payload, recipe_version="sd04-rehearsal-v1"))
    candidate = {"schema": "foundry.training_example/1", "example_id": "SYN-RATIO-Q1",
        "family_id": "SYN-RATIO-FAMILY", "split": "train", "task_type": "calculation",
        "quality_flags": ["fabricated_rehearsal", "calculation_method_review_pending"],
        "source_refs": [{"source_id": d["source"]["source_id"], "revision_id": "fixture-v1",
            "content_sha256": d["source"]["content_sha256"], "block_ids": [b["block_id"] for b in d["blocks"]]}
            for d in documents],
        "messages": [{"role": "user", "content": "Using the synthetic absolute pressures, compute discharge/suction."},
            {"role": "assistant", "content": "60 / 30 = 2, dimensionless. This does not establish compressor power or sizing."}],
        "review": {"status": "pending", "reviewer": None, "reviewed_at": None,
                   "reason": "Independent engineering acceptance has not occurred."}}
    candidate = modules["curate"].curate_examples([candidate], documents)[0]
    names = ("source_support", "arithmetic", "units_basis", "physical_assumptions", "completeness", "unsupported_action_handling")
    checks = {n: {"status": "needs_review", "evidence": [], "limitation": "Requires independent engineering review."} for n in names}
    checks["arithmetic"] = deepcopy(artifact["check"])
    checks["arithmetic"]["evidence"].append("calculation_artifact_sha256=" + artifact["artifact_sha256"])
    recipe = {"recipe_id": checker.TEMPLATE_ID, "version": "draft-1", "task_type": "calculation",
        "author_id": "synthetic-fixture-author", "prompt_sha256": digest("Fixed vectors; no model"),
        "rubric_sha256": digest(checker.LIMITATION), "applicable_checks": list(names)}
    receipt = {"mode": "mock", "model": "fixture/no-model", "provider": "offline", "generated_at": "2026-09-27T00:00:00Z",
        "settings": {"temperature": 0, "think": False}, "candidate_sha256": digest(candidate),
        "recipe_sha256": digest(recipe), "document_sha256s": [digest(d) for d in documents],
        "evidence": [{"source_id": d["source"]["source_id"], "revision_id": "fixture-v1",
            "block_id": b["block_id"], "quote": b["text"]} for d in documents for b in d["blocks"]]}
    values = dict(candidate=candidate, normalized_documents=documents, family_history=[], recipe=recipe,
                  generation_receipt=receipt, checks=checks)
    review = modules["synthetic_review"]
    packet = review.build_review_packet(**values)
    review.validate_review_packet(packet, normalized_documents=documents, family_history=[])
    rejections = {}
    for label in ("pending_artifact_rights", "revoked_artifact_rights", "historical_holdout", "changed_artifact_bytes"):
        data = deepcopy(values)
        try:
            if label == "changed_artifact_bytes":
                modules["extract"].extract_document(documents[1]["source"], payloads[1] + b"edited", recipe_version="sd04-rehearsal-v1")
            else:
                if label == "historical_holdout":
                    past = deepcopy(candidate)
                    past.update(example_id="SYN-RATIO-OLD", split="test")
                    data["family_history"] = [past]
                else:
                    data["normalized_documents"][1]["source"]["permission"]["status"] = label.split("_")[0]
                    data["generation_receipt"]["document_sha256s"] = [digest(d) for d in data["normalized_documents"]]
                review.build_review_packet(**data)
        except ValueError:
            rejections[label] = "blocked"
        else:
            raise AssertionError("Expected rejection: " + label)
    try:
        modules["datasets"].prepare_release_candidate([candidate], documents,
            pack_name="synthetic-calculation-rehearsal", recipe_version="draft-1")
    except modules["datasets"].DatasetError:
        blocked = True
    else:
        raise AssertionError("Pending calculation answer must not be released")
    report = {"schema": "broadbridge.calculation_rehearsal/1", "model_calls": 0,
        "fixed_vector_statuses": [a["check"]["status"] for a in artifacts],
        "rejections": rejections, "release_blocked_without_review": blocked, "training_approved": False,
        "artifact_sha256": artifact["artifact_sha256"], "packet_sha256": packet["packet_sha256"],
        "limitation": "Software rehearsal only; template, tolerance and real candidate admission await independent review."}
    args.out.mkdir(parents=True, exist_ok=False)
    outputs = {"report": report, "ratio.packet": packet, "documents": documents, "fixed-vectors": artifacts}
    for name, value in outputs.items():
        (args.out / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
