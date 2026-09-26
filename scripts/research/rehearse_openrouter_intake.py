"""Rehearse embedded synthetic fixtures only. Default is offline; live is four calls.

No arbitrary source path, database, bucket or expert case is accepted. Results
remain pending. Requires the companion Foundry helper branch and openpyxl.
"""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
from email.message import EmailMessage
import hashlib
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
import zipfile
from xml.sax.saxutils import escape

import requests

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs/oil-gas-public-intake"
TEXT = ("SYNTHETIC refinery pump inspection report. Pump inlet pressure: 3 bar absolute. "
        "Temperature: 45 degC. No diagnosis or operating action is established.")


def fixtures():
    from openpyxl import Workbook
    message = EmailMessage()
    message["From"] = "synthetic@example.invalid"
    message["To"] = "reviewer@example.invalid"
    message["Subject"] = "Synthetic refinery pump inspection"
    message.set_content(TEXT)
    docx = io.BytesIO()
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + escape(TEXT) + '</w:t></w:r></w:p></w:body></w:document>')
    workbook = Workbook()
    workbook.active.append(["Synthetic report", "Observation"])
    workbook.active.append(["Refinery pump", TEXT])
    xlsx = io.BytesIO()
    workbook.save(xlsx)
    return [("txt", "text/plain", TEXT.encode()),
            ("csv", "text/csv", ('report,observation\nrefinery pump,"' + TEXT + '"\n').encode()),
            ("eml", "message/rfc822", message.as_bytes()),
            ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx.getvalue()),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", xlsx.getvalue())]


def mock_http(url, **kwargs):
    assert url == "https://openrouter.ai/api/v1/chat/completions"
    payload = kwargs["json"]
    blocks = json.loads(payload["messages"][1]["content"])["evidence_blocks"]
    block = next(b for b in blocks if "3 bar absolute" in b["text"])
    evidence = [{"block_id": block["block_id"], "quote": TEXT}]
    if payload["response_format"]["json_schema"]["name"] == "foundry_classify":
        value = {"labels": {"practice": ["downstream"], "document_role": ["report"], "equipment": ["pump"]},
                 "confidence": 0.8, "notes": "Synthetic offline fixture response", "evidence": evidence}
    else:
        value = {"question": "What readings and limitations are recorded?", "answer":
                 "The inlet pressure is 3 bar absolute and temperature is 45 degC. No diagnosis or operating action is established.",
                 "task_type": "grounded_explanation", "evidence": evidence}
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps({"model": payload["model"], "provider": payload["provider"]["only"][0],
        "choices": [{"finish_reason": "stop", "message": {"content": json.dumps(value)}}],
        "usage": {"prompt_tokens": 120, "completion_tokens": 80, "cost": 0.00001}}).encode()
    response._content_consumed = True
    return response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundry", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.foundry.is_absolute() or not args.out.is_absolute() or args.out.exists():
        raise ValueError("Use an absolute Foundry checkout and a new absolute output directory")
    if not (args.foundry / "src/ingestion/assist.py").is_file():
        raise ValueError("The specified Foundry checkout lacks the ingestion helper")
    sys.path.insert(0, str(args.foundry))
    from src.ingestion.assist import assist_document, load_policy, AssistError
    from src.ingestion.contracts import content_hash, canonical_json
    from src.ingestion.extract import extract_document
    from src.ingestion.datasets import prepare_release_candidate, DatasetError
    from src.openrouter_client import OpenRouterError
    args.out.mkdir(parents=True)
    def write(name, value):
        (args.out / name).write_bytes(canonical_json(value) + b"\n")
    report = {"synthetic_only": True, "network_used": args.live, "fixture_count": 0, "candidate_count": 0,
              "model_quality_evaluated": False, "rows": [], "reported_cost_usd": 0,
              "receipt_costs_are_mocked": not args.live, "cost_receipts_complete": True,
              "calls_attempted": 0, "ec2_started": False}
    policy = load_policy(PACK)
    documents, candidates = [], []
    selected = fixtures()[:2] if args.live else fixtures()
    for extension, media, data in selected:
        identity = "SYN-HELPER-" + extension.upper()
        filename = identity + "." + extension
        (args.out / filename).write_bytes(data)
        source = {"schema": "foundry.source_revision/1", "project_id": "broadbridge-public-trial",
            "source_id": identity, "revision_id": "synthetic-v1", "family_id": "SYN-HELPER-PUMP",
            "object_key": "incoming/synthetic/" + filename, "original_filename": filename,
            "content_sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data), "media_type": media,
            "confidentiality": "public", "permission": {"status": "approved", "permitted_use": "training",
                "rights_basis": "Embedded synthetic fixture authored for Brad-authorized dev testing only",
                "reviewed_by": "synthetic-fixture-author", "reviewed_at": "2026-09-25T12:00:00Z"}, "relationships": []}
        doc = extract_document(source, data, recipe_version="synthetic-helper-v1")
        if doc["status"] != "complete":
            raise ValueError("Synthetic extraction incomplete: " + extension)
        write(identity + ".normalized.json", doc)
        grant = {"schema": "foundry.cloud_processing_approval/1", "document_sha256": content_hash(doc),
                 "policy_sha256": policy["sha256"], "provider": "openrouter", "tasks": ["classify", "draft"],
                 "approved_by": "synthetic-fixture-author", "approved_at": datetime.now(timezone.utc).isoformat(),
                 "reason": "Embedded synthetic fixture only; Brad-authorized dev trial; no expert acceptance"}
        write(identity + ".approval.json", grant)
        results = {}
        for task in ("classify", "draft"):
            if args.live and report["reported_cost_usd"] >= 0.02:
                raise ValueError("Synthetic rehearsal reported-cost stop")
            context = nullcontext() if args.live else patch("requests.post", mock_http)
            # Offline mode uses no real credential. Never load .env or access secrets here.
            key_context = nullcontext() if args.live else patch.dict("os.environ", {"OPENROUTER_API_KEY": "mock-only"})
            try:
                report["calls_attempted"] += 1
                with context, key_context:
                    result = assist_document(doc, PACK, grant, task=task)
            except OpenRouterError as exc:
                write(identity + "." + task + ".failed.json", exc.receipt)
                if exc.receipt.get("cost_usd") is None:
                    report["cost_receipts_complete"] = False
                else:
                    report["reported_cost_usd"] += exc.receipt["cost_usd"]
                # Known receipts are a subtotal. A timeout can still be billed.
                report["total_cost_usd"] = (report["reported_cost_usd"]
                                            if report["cost_receipts_complete"] else None)
                report["error"] = str(exc)
                write("report.json", report)
                raise
            results[task] = result
            write(identity + "." + task + ".json", result)
            report["reported_cost_usd"] += result["receipt"]["cost_usd"]
        candidate = results["draft"]["candidate"]
        assert candidate["review"]["status"] == "pending"
        documents.append(doc)
        candidates.append(candidate)
        report["rows"].append({"format": extension, "source_id": identity, "extraction": doc["status"],
            "review": candidate["review"]["status"], "classification_valid": True, "candidate_valid": True,
            "quoted_basis_preserved": any("3 bar absolute" in e["quote"] for e in results["draft"]["evidence"])})
        report["fixture_count"] += 1
        report["candidate_count"] += 1
        write("report.json", report)
    try:
        prepare_release_candidate(candidates, documents, pack_name="synthetic-helper", recipe_version="synthetic-helper-v1")
    except DatasetError:
        report["release_blocked_without_technical_review"] = True
    else:
        raise AssertionError("Pending drafts must not be released")
    try:
        load_policy(ROOT / "packs/oil-gas")
    except AssistError:
        report["confidential_pack_blocked"] = True
    else:
        raise AssertionError("Oil-gas confidential pack must remain blocked")
    write("candidates.json", candidates)
    write("report.json", report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, AssertionError):
        print("Rehearsal stopped. Inspect the sanitized report/receipt; no admission or training occurred.")
        raise SystemExit(2) from None
