"""FQ-02: local review packet for one fixed DOE original and pages 35-37.

This domain-specific acquisition rehearsal is not a new Foundry parser or a
training adapter. Original glyphs, parser output and proposed interpretations
remain separate. No network, OCR/model download, database write or QA generation.
"""
import argparse
from copy import deepcopy
import csv
import hashlib
from importlib import metadata
import io
import json
from pathlib import Path

PDF_SHA256 = "3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9"
PDF_BYTES = 1_910_060
PAGES = (35, 36, 37)
VERSIONS = {"pypdf": "6.10.0", "pdfplumber": "0.11.9", "pypdfium2": "5.13.0"}
SOURCE_URL = "https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf"
EXCEPTIONS = [
    ("figure", 35, "Figure 2 is vector artwork; text extraction does not capture diagram relationships. Read the page image."),
    ("subscripts", 36, "The layout parser separates subscripts from P; raw text and glyph coordinates are retained. Equation proposals require review."),
    ("symbol", 36, "Poppler trial omitted rho; PDFium preserves it. The layout text parser can emit r for rho. Verify original glyphs and image."),
    ("mass-force", 36, "The hydrostatic example uses lbm notation; reviewer must establish weight-density/gravity conventions before deriving calculations."),
    ("assumptions", 37, "Atmospheric pressure and column conversions are the handbook's rounded examples, not universal site conditions or exact property data."),
    ("exponent", 37, "10 superscript 3 can become separate lines in extracted text. Proposed value 1000 is an unaccepted interpretation of the original image."),
    ("table", 37, "Conversions are a typeset list, not a detected table. Proposed rows are manual normalization, separate from parser table candidates."),
    ("scope", 35, "The June 1992 handbook is nuclear-facility fundamentals material. Review applicability and limitations for petrochemical tasks."),
    ("rights", 5, "Foreword credits DOE Training Coordination Program managed by EG&G Idaho. Public distribution does not settle every contribution's training rights."),
]


def assemble_packet(pages, versions, frontmatter):
    if ([p.get("pdf_page") for p in pages] != list(PAGES)
            or any(not isinstance(p.get("text"), str) or not p["text"].strip() for p in pages)):
        raise ValueError("Missing, substituted or empty selected page")
    equations = [{"id": name, "pdf_page": 36, "printed_page": "HT-01 10",
        "expression_proposed": expression, "method": "assistant_transcription_from_page_image",
        "status": "needs_review", "reviewer": None}
        for name, expression in [("1-9", "P_abs = P_atm + P_gauge"), ("1-10", "P_abs = P_atm - P_vac")]]
    conversions = [{"pdf_page": 37, "printed_page": "HT-01 11", "left_value": lv, "left_unit": lu,
        "right_value": rv, "right_unit": ru, "status": "needs_review", "reviewer": None,
        "note": "Proposed transcription of original image; conditions/rounding and applicability are unreviewed."}
        for lv, lu, rv, ru in [("14.7", "psia", "408", "inch water"), ("14.7", "psia", "29.9", "inch mercury"),
            ("1", "inch mercury", "25.4", "millimeter mercury"), ("1", "millimeter mercury", "1000", "micron mercury")]]
    return {"schema": "broadbridge.source_review_packet/1", "status": "pending_review",
        "source": {"source_id": "DOE-HDBK-1012-1-92", "family_id": "DOE-HDBK-1012", "sha256": PDF_SHA256,
            "size_bytes": PDF_BYTES, "url": SOURCE_URL, "version": "June 1992 / Rev. 0 / Volume 1",
            "title": "DOE Fundamentals Handbook: Thermodynamics, Heat Transfer, and Fluid Flow",
            "family_note": "Treat related volumes, revisions and derivatives as one provisional family; historical split audit still required."},
        "section": "Pressure and pressure scales; PDF pages 35-37 / printed HT-01 pages 9-11",
        "parser_versions": versions, "frontmatter_text": frontmatter,
        "pages": deepcopy(pages), "equation_proposals": equations, "conversion_rows_proposed": conversions,
        "exceptions": [{"id": name, "pdf_page": page, "issue": issue, "status": "needs_review"}
                       for name, page, issue in EXCEPTIONS],
        "rights_review": {"status": "pending", "reviewer": None, "decision": None},
        "technical_review": {"status": "pending", "reviewer": None, "decision": None},
        "split": None, "training_approved": False,
        "limitations": "No OCR, model inference, source admission, family allocation or training examples created. Parser agreement is not technical acceptance."}


def review_markdown(packet):
    lines = ["# DOE pressure evidence review", "", packet["section"], "",
        "No questions or answers have been admitted to training. This is an extraction and source-admission packet.", "",
        "Reviewer: ______  Date: ______  Relevant competence: ______", "",
        "Review `packet.json` for both text extractions, glyph positions, proposed equations/conversion rows and frontmatter credits.",
        "The original PDF remains authoritative. Equations and table rows below are unaccepted transcriptions.", "",
        "## Decisions to record", "",
        "- Intended engineering task and users: ______",
        "- Extraction corrections, symbols/units and applicable assumptions: ______",
        "- Rights/credit decision and supporting evidence (Brad): ______",
        "- Source-family/history check and proposed split (before generation): ______",
        "- Technical applicability and exclusions (qualified reviewer): ______",
        "- Disposition: accept for a specified use / revise / exclude: ______", "",
        "## Unresolved extraction and applicability issues", ""]
    for row in packet["exceptions"]:
        lines.append(f"- [ ] {row['id']} (PDF {row['pdf_page']}): {row['issue']} Correction/evidence: ______")
    lines += ["", "## Proposed equation transcription", ""]
    for row in packet["equation_proposals"]:
        lines.append(f"- Equation {row['id']}, PDF 36: `{row['expression_proposed']}`. Reviewer decision: ______")
    lines += ["", "## Original page renders", "",
        "PDFium renders are provided for comparison; preserve the original PDF for final verification.", ""]
    for page in packet["pages"]:
        lines += [f"### PDF {page['pdf_page']} / {page['printed_page']}", "",
            f"[Page text](page-{page['pdf_page']:03}.txt) | [Page render]({page['image']})", "",
            f"![Original PDF page {page['pdf_page']}]({page['image']})", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.out.is_absolute() or args.out.exists():
        raise ValueError("Choose a new absolute output directory")
    if not args.pdf.is_absolute() or args.pdf.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("Choose the local bounded original PDF")
    payload = args.pdf.read_bytes()
    if hashlib.sha256(payload).hexdigest() != PDF_SHA256 or len(payload) != PDF_BYTES:
        raise ValueError("Original DOE source hash does not match the acquired revision")
    versions = {key: metadata.version(key) for key in VERSIONS}
    if versions != VERSIONS:
        raise ValueError("Use the pinned evidence-review dependencies")
    from pypdf import PdfReader
    import pdfplumber
    reader = PdfReader(io.BytesIO(payload))
    if len(reader.pages) != 138:
        raise ValueError("Unexpected original page count")
    frontmatter = "\n\n".join(f"PDF PAGE {n}\n{reader.pages[n-1].extract_text()}" for n in (1, 2, 5, 7))
    pages = []
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        for n in PAGES:
            page = pdf.pages[n-1]
            glyphs = [{k: c[k] for k in ("text", "x0", "top", "x1", "bottom", "fontname", "size")} for c in page.chars]
            pages.append({"pdf_page": n, "printed_page": f"HT-01 {n-26}", "width": page.width, "height": page.height,
                "text": reader.pages[n-1].extract_text(), "layout_text": page.extract_text(layout=True),
                "glyphs": glyphs, "table_candidates": page.extract_tables(), "image": f"page-{n:03}.png"})
        packet = assemble_packet(pages, versions, frontmatter)
        args.out.mkdir(parents=True, exist_ok=False)
        for n in PAGES:
            pdf.pages[n-1].to_image(resolution=150).save(args.out / f"page-{n:03}.png")
    for page in pages:
        (args.out / f"page-{page['pdf_page']:03}.txt").write_text(page["text"], encoding="utf-8")
        (args.out / f"page-{page['pdf_page']:03}.layout.txt").write_text(page["layout_text"], encoding="utf-8")
    (args.out / "packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out / "REVIEW.md").write_text(review_markdown(packet), encoding="utf-8")
    with (args.out / "review.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["issue_id", "pdf_page", "disposition", "correction", "evidence", "reviewer", "date"])
        writer.writeheader()
        writer.writerows({"issue_id": row["id"], "pdf_page": row["pdf_page"]} for row in packet["exceptions"])
    files = [{"path": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
             for p in sorted(args.out.iterdir()) if p.is_file()]
    receipt = {"schema": "broadbridge.doe_extraction_receipt/1", "source_sha256": PDF_SHA256,
        "pdf_pages": list(PAGES), "printed_pages": [9, 10, 11], "parser_versions": versions,
        "detected_tables": sum(len(p["table_candidates"]) for p in pages),
        "equation_proposals": 2, "conversion_row_proposals": 4, "review_issues": len(EXCEPTIONS),
        "model_calls": 0, "training_examples": 0, "training_approved": False, "files": files}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "files"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
