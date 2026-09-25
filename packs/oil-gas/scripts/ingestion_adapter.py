"""Bind canonical Broadbridge records to the external Foundry ingestion contracts.

This adapter is offline and performs no database migration or network access.  A
caller must point ``--foundry`` at an explicit local Foundry checkout and
``--pack`` at this pack; neither path is inferred from environment variables.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

from case_contract import disposition, validate_export


PROJECT_ID = "broadbridge-oil-gas"
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SPLIT_MAP = {"train": "train", "dev": "val", "locked_test": "test"}
SPLIT_PRECEDENCE = {"train": 0, "val": 1, "test": 2}


def _absolute_directory(path, label):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    resolved = path.resolve()
    if not resolved.is_dir():
        raise ValueError(f"{label} directory does not exist")
    return resolved


def load_foundry(foundry):
    """Load the pinned generic contracts from an explicit absolute checkout."""
    root = _absolute_directory(foundry, "foundry")
    contract_path = root / "src" / "ingestion" / "contracts.py"
    if not contract_path.is_file():
        raise ValueError("foundry path does not contain ingestion contracts")
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    contracts = importlib.import_module("src.ingestion.contracts")
    if Path(contracts.__file__).resolve() != contract_path.resolve():
        raise ValueError("a different Foundry checkout is already imported")
    return SimpleNamespace(
        canonical_json=contracts.canonical_json,
        content_hash=contracts.content_hash,
        validate_source_revision=contracts.validate_source_revision,
        validate_normalized_document=contracts.validate_normalized_document,
        validate_training_example=contracts.validate_training_example,
    )


def load_policy(pack, *, foundry):
    """Load external policy while delegating taxonomy path checks to Foundry."""
    import yaml

    pack = _absolute_directory(pack, "pack")
    engine_root = _absolute_directory(foundry, "foundry")
    load_foundry(engine_root)
    curate = importlib.import_module("src.ingestion.curate")
    taxonomy = curate.load_pack_taxonomy(pack / "pack.yaml")
    policy = yaml.safe_load((pack / "ingestion.yaml").read_text(encoding="utf-8"))
    if not isinstance(policy, dict) or policy.get("taxonomy") != taxonomy:
        raise ValueError("ingestion policy taxonomy does not match Foundry pack loading")
    return policy


def _identifier(prefix, value):
    candidate = f"{prefix}-{value}"
    if IDENTIFIER.fullmatch(candidate):
        return candidate
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}-{digest}"


def _case_confidentiality(value):
    text = value.strip().casefold()
    if text in {"public", "internal", "confidential", "restricted"}:
        return text
    if "restrict" in text:
        return "restricted"
    return "confidential"


def _decision_payload(case):
    return {
        "decision_time": case["decision_time"],
        "unit_service": case["identity"]["unit_service"],
    }


def _family_splits(cases):
    """Compute strictest family split before excluding any case or question."""
    result = {}
    for case in cases:
        family_id = case["family_id"]
        for question in case["questions"]:
            split = SPLIT_MAP[question["split"]]
            current = result.get(family_id, "train")
            result[family_id] = max(current, split, key=SPLIT_PRECEDENCE.__getitem__)
    return result


def adapt_case_export(export, *, foundry, pack):
    """Convert eligible signed cases without exposing hindsight to user input."""
    pack = _absolute_directory(pack, "pack")
    if not (pack / "ingestion.yaml").is_file():
        raise ValueError("pack does not contain ingestion.yaml")
    validate_export(export)
    engine = load_foundry(foundry)
    family_splits = _family_splits(export["cases"])
    documents, examples, dispositions = [], [], []
    for case in sorted(export["cases"], key=lambda item: item["case_id"]):
        state, reason = disposition(case)
        if state != "imported":
            dispositions.append({"case_id": case["case_id"], "status": "excluded", "reason": reason})
            continue

        case_hash = engine.content_hash(case)
        source_id = _identifier("case", case["case_id"])
        family_id = _identifier("case-family", case["family_id"])
        revision_id = f"case-{case_hash[:24]}"
        block_id = "decision-time"
        source = {
            "schema": "foundry.source_revision/1",
            "project_id": PROJECT_ID,
            "source_id": source_id,
            "revision_id": revision_id,
            "family_id": family_id,
            "object_key": f"case-records/{source_id}/{revision_id}.json",
            "original_filename": f"{source_id}.json",
            "content_sha256": case_hash,
            "size_bytes": len(engine.canonical_json(case)),
            "media_type": "application/json",
            "confidentiality": _case_confidentiality(case["identity"]["confidentiality"]),
            "permission": {
                "permitted_use": "training",
                "status": "approved",
                "rights_basis": "canonical signed case with permitted_use=training",
                "reviewed_by": case["reviewer_signoff"]["name"],
                "reviewed_at": f"{case['reviewer_signoff']['date']}T00:00:00Z",
            },
            "relationships": [{"kind": "case_family", "target_id": family_id}],
        }
        decision_payload = _decision_payload(case)
        document = {
            "schema": "foundry.normalized_document/1",
            "source": engine.validate_source_revision(source),
            "parser": {"name": "broadbridge-case-adapter", "version": "1", "recipe_version": "oil-gas-v1"},
            "status": "complete",
            "labels": {"document_role": ["expert_case"], "practice": ["downstream"]},
            "quality_flags": [],
            "blocks": [{
                "block_id": block_id,
                "kind": "text",
                "text": json.dumps(decision_payload, ensure_ascii=False, sort_keys=True),
                "location": {},
                "asset_key": None,
                "measurements": [],
                "quality_flags": [],
            }],
            "attachments": [],
            "classification": {"method": "canonical-case", "confidence": 1.0, "review_required": False},
        }
        documents.append(engine.validate_normalized_document(document))

        for question in case["questions"]:
            user_payload = {
                "question": question["question"],
                "decision_context": decision_payload,
                "evidence_ids": question["evidence_ids"],
            }
            example = {
                "schema": "foundry.training_example/1",
                "example_id": _identifier("case-question", question["question_id"]),
                "family_id": family_id,
                "split": family_splits[case["family_id"]],
                "source_refs": [{
                    "source_id": source_id,
                    "revision_id": revision_id,
                    "content_sha256": case_hash,
                    "block_ids": [block_id],
                }],
                "messages": [
                    {"role": "system", "content": "Answer from the decision-time information only; identify missing evidence rather than using hindsight."},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True)},
                    {"role": "assistant", "content": question["reference_answer"]},
                ],
                "review": {
                    "status": "approved",
                    "reviewer": case["reviewer_signoff"]["name"],
                    "reviewed_at": f"{case['reviewer_signoff']['date']}T00:00:00Z",
                    "reason": "canonical signed case question and reference answer",
                },
                "task_type": question["type"],
                "quality_flags": [],
            }
            examples.append(engine.validate_training_example(example))
        dispositions.append({"case_id": case["case_id"], "status": "adapted", "example_count": len(case["questions"])})
    return {"documents": documents, "examples": examples, "dispositions": dispositions}


def adapt_registered_source(source_record, evidence_records, *, revision, foundry):
    """Convert an existing source/evidence register without inventing a case."""
    engine = load_foundry(foundry)
    if not isinstance(source_record, dict) or source_record.get("source_id") != revision.get("source_id"):
        raise ValueError("source register identity does not match revision")
    source = engine.validate_source_revision(dict(revision))
    if source["project_id"] != PROJECT_ID:
        raise ValueError("source revision belongs to a different project")
    blocks = []
    for evidence in sorted(evidence_records, key=lambda item: item.get("evidence_id", "")):
        if evidence.get("source_id") != source["source_id"]:
            raise ValueError("evidence belongs to a different source")
        text = evidence.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("evidence text must be nonblank")
        location = {}
        for key in ("page", "bbox", "start_seconds", "end_seconds"):
            if key in evidence:
                location[key] = evidence[key]
        evidence_id = evidence.get("evidence_id", "")
        block_id = evidence_id if IDENTIFIER.fullmatch(evidence_id) else _identifier("evidence", evidence_id)
        blocks.append({
            "block_id": block_id,
            "kind": evidence.get("kind", "text"),
            "text": text,
            "location": location,
            "asset_key": evidence.get("asset_key"),
            "measurements": evidence.get("measurements", []),
            "quality_flags": evidence.get("quality_flags", []),
        })
    document = {
        "schema": "foundry.normalized_document/1",
        "source": source,
        "parser": {"name": "broadbridge-evidence-adapter", "version": "1", "recipe_version": "oil-gas-v1"},
        "status": "complete" if blocks else "partial",
        "labels": {},
        "quality_flags": [] if blocks else ["no_registered_evidence"],
        "blocks": blocks,
        "attachments": [],
        "classification": {"method": "unclassified", "confidence": 0.0, "review_required": True},
    }
    return engine.validate_normalized_document(document)


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry", required=True, type=Path)
    parser.add_argument("--pack", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    cases = subparsers.add_parser("cases")
    cases.add_argument("--input", required=True, type=Path)
    cases.add_argument("--output", required=True, type=Path)
    source = subparsers.add_parser("source")
    source.add_argument("--source", required=True, type=Path)
    source.add_argument("--revision", required=True, type=Path)
    source.add_argument("--evidence", required=True, type=Path)
    source.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    _absolute_directory(args.foundry, "foundry")
    _absolute_directory(args.pack, "pack")
    if args.command == "cases":
        result = adapt_case_export(_read_json(args.input), foundry=args.foundry, pack=args.pack)
    else:
        result = adapt_registered_source(
            _read_json(args.source), _read_json(args.evidence),
            revision=_read_json(args.revision), foundry=args.foundry,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
