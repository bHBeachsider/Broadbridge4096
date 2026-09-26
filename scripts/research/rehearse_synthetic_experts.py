"""Offline SD-02 rehearsal. Embedded fictitious records only; never calls a model."""
import argparse
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    foundry = Path(args.foundry)
    if not foundry.is_absolute() or not (foundry / "src/ingestion/synthetic_review.py").is_file():
        raise ValueError("Choose an absolute Foundry checkout with SD-02 installed")
    output = Path(args.out)
    if not output.is_absolute() or output.exists():
        raise ValueError("Choose a new absolute output directory")
    sys.path.insert(0, str(foundry.resolve()))
    modules = {name: importlib.import_module("src.ingestion." + name)
               for name in ("contracts", "extract", "curate", "datasets", "synthetic_review")}
    if any(not Path(m.__file__).resolve().is_relative_to(foundry.resolve()) for m in modules.values()):
        raise ValueError("Loaded modules do not belong to the selected absolute Foundry checkout")
    digest = modules["contracts"].content_hash
    build = modules["synthetic_review"].build_review_packet
    validate = modules["synthetic_review"].validate_review_packet
    check_names = ["source_support", "arithmetic", "units_basis", "physical_assumptions",
                   "completeness", "unsupported_action_handling"]
    inputs, packets, documents = [], [], []
    for number, (text, question, answer) in enumerate([
        ("Fictitious pump P-001: suction pressure basis is unknown. No operating change is authorized.",
         "Can the suction pressure be used in a calculation?",
         "No. Request the pressure value, units and absolute or gauge basis before calculating."),
        ("Fictitious exchanger E-002: both outlet temperatures are missing. No duty is established.",
         "Is the exchanger duty established by this record?",
         "No. The record provides no duty and lacks outlet temperatures; request the missing data."),
    ], 1):
        identity = f"SYN-EXPERT-{number:03}"
        payload = text.encode("utf-8")
        source = {
            "schema": "foundry.source_revision/1", "project_id": "broadbridge-synthetic-rehearsal",
            "source_id": identity, "revision_id": "fixture-v1", "family_id": identity,
            "object_key": f"incoming/synthetic/{identity}.txt", "original_filename": identity + ".txt",
            "content_sha256": hashlib.sha256(payload).hexdigest(), "size_bytes": len(payload),
            "media_type": "text/plain", "confidentiality": "public", "relationships": [],
            "permission": {"status": "approved", "permitted_use": "training",
                           "rights_basis": "Embedded fabricated software fixture; not expert-approved training data.",
                           "reviewed_by": "synthetic-fixture-author", "reviewed_at": "2026-09-26T00:00:00Z"},
        }
        doc = modules["extract"].extract_document(source, payload, recipe_version="synthetic-review-v1")
        candidate = {
            "schema": "foundry.training_example/1", "example_id": identity + "-Q1", "family_id": identity,
            "split": "train", "task_type": "missing_data", "quality_flags": [],
            "source_refs": [{"source_id": identity, "revision_id": "fixture-v1",
                             "content_sha256": source["content_sha256"],
                             "block_ids": [b["block_id"] for b in doc["blocks"]]}],
            "messages": [{"role": "user", "content": question}, {"role": "assistant", "content": answer}],
            "review": {"status": "pending", "reviewer": None, "reviewed_at": None,
                       "reason": "Fabricated rehearsal; no engineering approval."},
        }
        candidate = modules["curate"].curate_examples([candidate], [doc])[0]
        recipe = {"recipe_id": "synthetic-missing-data", "version": "1", "task_type": "missing_data",
                  "author_id": "synthetic-fixture-author", "prompt_sha256": digest(question),
                  "rubric_sha256": digest("Flag missing evidence; no operating advice."),
                  "applicable_checks": [n for n in check_names if n != "arithmetic"]}
        receipt = {
            "mode": "mock", "model": "fixture/no-model", "provider": "offline",
            "generated_at": "2026-09-26T00:00:00Z", "settings": {"temperature": 0, "think": False},
            "candidate_sha256": digest(candidate), "recipe_sha256": digest(recipe),
            "document_sha256s": [digest(doc)],
            "evidence": [{"source_id": identity, "revision_id": "fixture-v1", "block_id": b["block_id"],
                          "quote": b["text"]} for b in doc["blocks"]],
        }
        checks = {n: {"status": "needs_review", "evidence": [], "limitation": "Requires independent expert review."}
                  for n in check_names}
        checks["arithmetic"] = {"status": "not_applicable", "evidence": [], "limitation": "No calculation requested."}
        data = dict(candidate=candidate, normalized_documents=[doc], family_history=[], recipe=recipe,
                    generation_receipt=receipt, checks=checks)
        packet = build(**data)
        assert validate(packet, normalized_documents=[doc], family_history=[]) == packet
        inputs.append(data)
        packets.append(packet)
        documents.append(doc)

    rejections = {}
    for name in ("historical_holdout", "revoked_rights", "changed_answer", "invented_quote", "missing_check", "generated_approval"):
        data = deepcopy(inputs[0])
        if name == "historical_holdout":
            past = deepcopy(data["candidate"])
            past.update(example_id="historical-question", split="locked_test")
            data["family_history"] = [past]
        elif name == "revoked_rights":
            data["normalized_documents"][0]["source"]["permission"]["status"] = "revoked"
        elif name == "changed_answer":
            data["candidate"]["messages"][-1]["content"] = "An unrecorded edit"
        elif name == "invented_quote":
            data["generation_receipt"]["evidence"][0]["quote"] = "Not present in the source"
        elif name == "missing_check":
            del data["checks"]["units_basis"]
        else:
            data["candidate"]["review"].update(status="approved", reviewer="synthetic-fixture-author",
                                               reviewed_at="2026-09-26T00:00:00Z")
        try:
            build(**data)
        except modules["synthetic_review"].SyntheticReviewError as error:
            rejections[name] = str(error)
        else:
            raise AssertionError(f"Expected rejection: {name}")
    try:
        modules["datasets"].prepare_release_candidate(
            [p["candidate"] for p in packets], documents,
            pack_name="synthetic-expert-rehearsal", recipe_version="synthetic-review-v1")
    except modules["datasets"].DatasetError:
        blocked = True
    else:
        raise AssertionError("Pending candidates must not become a release")
    report = {"packet_count": len(packets), "model_calls": 0, "training_approved": False,
              "release_blocked_without_review": blocked, "rejections": rejections,
              "limitation": "Software rehearsal only. No model quality or technical correctness claim."}
    output.mkdir(parents=True, exist_ok=False)
    for packet, doc in zip(packets, documents):
        identity = doc["source"]["source_id"]
        for suffix, value in (("packet", packet), ("document", doc)):
            (output / f"{identity}.{suffix}.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
