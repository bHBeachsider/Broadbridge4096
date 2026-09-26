"""CPU-only fictional document consistency demo. No model, database or network."""
import argparse
from collections import defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
VERSION = "document-checks/1"
REG_FIELDS = ["tag", "service", "condition", "pressure", "pressure_unit", "pressure_basis",
              "temperature", "temperature_unit", "datasheet_id", "datasheet_revision"]
DS_FIELDS = ["row_id", "asset_tags", "condition", "pressure", "pressure_unit",
             "pressure_basis", "temperature", "temperature_unit"]
INDEX_FIELDS = ["document_id", "revision", "status", "kind", "file"]
TAG = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]+$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
PRESSURE = {"Pa": Decimal(1), "kPa": Decimal(1000), "MPa": Decimal(1000000),
            "bar": Decimal(100000), "psi": Decimal("6894.757293168")}
TEMPERATURE = {"degC", "degF", "K"}
# Numerical conversion rounding only; not an engineering acceptance tolerance.
CONVERSION_EPSILON = Decimal("0.000000001")


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_bytes(root, name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", name):
        raise ValueError("Invalid source file name")
    path = root / name
    if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
        raise ValueError("Source file must remain inside package")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Source file exceeds the 1 MiB demo limit")
    return path.read_bytes()


def csv_records(data, fields):
    try:
        reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != fields:
            raise ValueError("CSV columns do not match the documented contract")
        records = []
        for number, row in enumerate(reader, 2):
            if len(records) >= 5000 or None in row or any(v is None or len(v) > 4000 for v in row.values()):
                raise ValueError("Invalid CSV record shape or size")
            records.append({"locator": f"CSV record {number}", "values": dict(row)})
        if not records:
            raise ValueError("CSV contains no records")
        return records
    except (csv.Error, UnicodeError) as exc:
        raise ValueError("Invalid CSV encoding or syntax") from exc


def clean_tag(value):
    result = value.strip().upper()
    if not TAG.fullmatch(result):
        raise ValueError("Invalid equipment tag")
    return result


def svg_records(data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("SVG declarations are not allowed")
    try:
        tree = ET.fromstring(data)
        if tree.tag.split("}")[-1] != "svg":
            raise ValueError("Expected SVG root")
        rows, ids = [], set()
        for node in tree.iter():
            if node.tag.split("}")[-1] not in {"svg", "title", "desc", "g", "text", "rect", "line", "path"}:
                raise ValueError("Unsupported SVG element")
            if any(k.lower().startswith("on") or k.split("}")[-1] in {"href", "style"} for k in node.attrib):
                raise ValueError("Active SVG attributes are not allowed")
            if "data-tag" in node.attrib:
                element_id = node.get("id", "")
                if not IDENT.fullmatch(element_id) or element_id in ids:
                    raise ValueError("SVG asset IDs must be unique")
                ids.add(element_id)
                rows.append({"locator": f"SVG element {element_id}",
                             "values": {"tag": clean_tag(node.get("data-tag")), "element_id": element_id}})
        if not rows:
            raise ValueError("SVG has no labelled assets")
        return rows
    except ET.ParseError as exc:
        raise ValueError("Invalid SVG") from exc


def load_package(directory):
    root = Path(directory).resolve()
    raw = source_bytes(root, "package.json")
    package = json.loads(raw)
    if (package.get("schema") != "broadbridge.document_demo/1"
            or package.get("synthetic") is not True
            or not IDENT.fullmatch(package.get("package_id", ""))
            or not isinstance(package.get("title"), str) or len(package["title"]) > 160
            or package.get("revision_index") != "revision_index.csv"):
        raise ValueError("Only the documented synthetic package contract is accepted")
    index_raw = source_bytes(root, "revision_index.csv")
    records = csv_records(index_raw, INDEX_FIELDS)
    if len(records) > 50:
        raise ValueError("Too many revisions for the demo")
    index = dict(document_key="INDEX", document_id="INDEX", revision="package",
                 status="control", kind="index", file="revision_index.csv",
                 sha256=digest(index_raw), records=records)
    docs, keys, files = [index], set(), set()
    kinds = defaultdict(set)
    for row in records:
        entry = row["values"]
        if (not IDENT.fullmatch(entry["document_id"]) or not IDENT.fullmatch(entry["revision"])
                or entry["status"] not in {"approved", "superseded"}
                or entry["kind"] not in {"equipment", "datasheets", "drawing"}):
            raise ValueError("Invalid revision index")
        key = entry["document_id"] + "@" + entry["revision"]
        if key in keys or entry["file"] in files:
            raise ValueError("Duplicate revision or source file")
        keys.add(key)
        files.add(entry["file"])
        kinds[entry["kind"]].add(entry["document_id"])
        data = source_bytes(root, entry["file"])
        parsed = svg_records(data) if entry["kind"] == "drawing" else csv_records(
            data, REG_FIELDS if entry["kind"] == "equipment" else DS_FIELDS)
        docs.append(dict(entry, document_key=key, sha256=digest(data), records=parsed))
    current = {}
    for kind in ["equipment", "datasheets", "drawing"]:
        selected = [d for d in docs if d["kind"] == kind and d["status"] == "approved"]
        if len(selected) != 1 or len(kinds[kind]) != 1:
            raise ValueError("Exactly one approved revision per document kind is required")
        current[kind] = selected[0]
    return package, digest(raw), docs, current


def evidence(doc, row):
    return {k: doc[k] for k in ["document_key", "document_id", "revision", "file", "sha256"]} | row


def quantity(value, unit, field):
    try:
        if len(value) > 40:
            raise ValueError()
        number = Decimal(value)
        if not number.is_finite() or abs(number) > Decimal("1e12"):
            raise ValueError()
    except (InvalidOperation, ValueError):
        return None, "unusable_value"
    if field == "pressure":
        if unit in TEMPERATURE:
            return None, "unit_dimension_mismatch"
        if unit not in PRESSURE:
            return None, "unsupported_unit"
        return number * PRESSURE[unit], None
    if unit in PRESSURE:
        return None, "unit_dimension_mismatch"
    if unit not in TEMPERATURE:
        return None, "unsupported_unit"
    if unit == "degF":
        number = (number - 32) * Decimal(5) / Decimal(9)
    return number + Decimal("273.15") if unit != "K" else number, None


def analyze(package_dir):
    package, manifest_hash, docs, current = load_package(package_dir)
    findings, not_compared = [], []
    def add(rule, tag, field, message, refs, category="discrepancy"):
        signature = [rule, tag, field, [(e["document_key"], e["locator"]) for e in refs]]
        findings.append(dict(id="F-" + digest(encoded(signature).encode())[:12],
            rule=rule, rule_version=VERSION, tag=tag, field=field, message=message,
            category=category, disposition="pending", evidence=refs))
    reg, ds, drawing = [current[k] for k in ["equipment", "datasheets", "drawing"]]
    assets, sheets, drawn = defaultdict(list), defaultdict(list), defaultdict(list)
    for row in reg["records"]:
        assets[clean_tag(row["values"]["tag"])].append(evidence(reg, row))
    for row in ds["records"]:
        tags = [clean_tag(t) for t in row["values"]["asset_tags"].split("|")]
        if len(tags) != len(set(tags)):
            raise ValueError("Repeated tag in datasheet association")
        ref = evidence(ds, row)
        for tag in tags:
            sheets[tag].append(ref)
        if len(tags) > 1:
            add("ambiguous_asset_link", "|".join(sorted(tags)), "asset_tags",
                "One datasheet row names several assets. Confirm which values belong to each asset.",
                [ref], "needs_review")
    for tag, refs in sorted(sheets.items()):
        if tag not in assets:
            add("unmatched_datasheet_tag", tag, "asset_tags",
                "Datasheet tag has no current equipment-register entry.", refs)
    for row in drawing["records"]:
        drawn[row["values"]["tag"]].append(evidence(drawing, row))
    for tag, refs in sorted(drawn.items()):
        if tag not in assets:
            add("unmatched_drawing_tag", tag, "tag", "Drawing tag has no current equipment-register entry.", refs)
        elif len(refs) > 1:
            add("duplicate_drawing_tag", tag, "tag", "Drawing repeats this tag; confirm whether the repeated depiction is intentional.", refs, "needs_review")
    index = docs[0]
    for tag, refs in sorted(assets.items()):
        if len(refs) > 1:
            add("duplicate_tag", tag, "tag", "Register repeats this tag. Comparison is held until the identity is resolved.", refs)
            continue
        ref = refs[0]
        values = ref["values"]
        for field in ["service", "datasheet_id", "datasheet_revision"]:
            if values[field].strip().lower() in {"", "unknown"}:
                add("missing_required_field", tag, field, f"Required register field '{field}' is missing.", [ref])
        if tag not in drawn:
            add("missing_drawing_tag", tag, "tag", "Current drawing has no labelled entry for this register asset.", [ref])
        if values["datasheet_id"].strip().lower() in {"", "unknown"}:
            continue
        if values["datasheet_id"] != ds["document_id"]:
            add("unknown_document", tag, "datasheet_id", "Referenced datasheet document is not in this package.", [ref], "needs_review")
            continue
        requested = values["datasheet_revision"]
        if requested and requested != ds["revision"]:
            old = next((r for r in index["records"] if r["values"]["document_id"] == ds["document_id"]
                        and r["values"]["revision"] == requested), None)
            add("superseded_reference" if old else "unknown_revision", tag, "datasheet_revision",
                f"Register cites revision {requested}; the index designates {ds['revision']} as approved.",
                [ref] + ([evidence(index, old)] if old else []))
        matches = sheets.get(tag, [])
        if not matches:
            add("missing_datasheet", tag, "datasheet_id", "No current datasheet row identifies this asset.", [ref])
            continue
        if len(matches) != 1:
            add("ambiguous_asset_link", tag, "asset_tags", "Several current datasheet rows identify this asset.", [ref] + matches, "needs_review")
            continue
        match = matches[0]
        other = match["values"]
        if "|" in other["asset_tags"]:
            continue
        if values["condition"] not in {"operating", "design", "test"} or other["condition"] not in {"operating", "design", "test"} or values["condition"] != other["condition"]:
            not_compared.append(dict(tag=tag, reason="different_conditions", evidence=[ref, match]))
            continue
        for field in ["pressure", "temperature"]:
            left, left_error = quantity(values[field], values[field + "_unit"], field)
            right, right_error = quantity(other[field], other[field + "_unit"], field)
            error = left_error or right_error
            if error:
                category = "discrepancy" if error == "unit_dimension_mismatch" else "needs_review"
                add(error, tag, field, f"Cannot compare {field}: a value or unit needs correction/clarification.",
                    [ref, match], category)
                continue
            if field == "pressure" and (values["pressure_basis"] not in {"absolute", "gauge"}
                    or values["pressure_basis"] != other["pressure_basis"]):
                add("basis_mismatch", tag, field, "Pressure bases differ or are unspecified. No atmospheric-pressure conversion was assumed.",
                    [ref, match], "needs_review")
                continue
            if abs(left - right) > CONVERSION_EPSILON:
                add("value_conflict", tag, field, f"Different stated {field} values under the same condition after unit conversion. An engineer must resolve the difference.",
                    [ref, match])
    findings.sort(key=lambda f: (f["tag"], f["rule"], f["field"], f["id"]))
    report = dict(schema="broadbridge.document_review/1", rules_version=VERSION,
        package=package, manifest_sha256=manifest_hash, synthetic=True,
        limits=["CSV tables and explicitly tagged SVG only; no PDF/OCR or CAD interpretation.",
                "Approved revisions come from the supplied index, not engineering authorization.",
                "No engineering sign-off, training admission, model calls or operating instructions."],
        documents=docs, findings=findings, not_compared=not_compared,
        summary=dict(assets=len(assets), findings=len(findings), needs_review=sum(f["category"] == "needs_review" for f in findings),
                     not_compared=len(not_compared), current_documents=3, document_versions=len(docs)-1))
    report["report_id"] = digest(encoded(report).encode())
    return report


def render_html(report):
    payload = encoded(report).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    title = html.escape(report["package"]["title"])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title} — Broadbridge document review</title><link rel="stylesheet" href="review.css"></head>
<body><header><div class="brand">Broadbridge <span>Engineering document review</span></div><span class="sample">Fictional demonstration</span></header>
<main><section class="intro"><div><h1>Find the disagreement.<br>Keep the evidence.</h1><p>Compare the equipment register, datasheets and drawing for {title.lower()}. Every finding points back to the exact source record.</p></div><div class="run-meta" id="run-meta"></div></section>
<p class="boundary">Local demonstration with invented records. Review notes are saved in this browser and can be exported; they are not engineering sign-off or SLM training approval.</p>
<section class="overview" aria-label="Package overview"><div><h2>Equipment reference drawing</h2><p>Labels only; no process connectivity or physical layout is asserted. Select a tag to filter findings.</p><div id="diagram" class="diagram"></div></div><aside><h2>Package checks</h2><dl id="metrics"></dl><div id="conditions"></div></aside></section>
<section class="review-toolbar" aria-label="Review controls"><div><label for="search">Find tag, field or rule</label><input id="search" type="search" placeholder="For example E-202"></div><div><label for="category">Finding category</label><select id="category"><option value="all">All categories</option><option value="discrepancy">Document discrepancy</option><option value="needs_review">Needs clarification</option></select></div><div><label for="disposition">Review status</label><select id="disposition"><option value="all">All statuses</option><option value="pending">Pending</option><option value="confirmed">Confirmed discrepancy</option><option value="dismissed">Dismissed</option><option value="needs_information">Needs information</option></select></div><button id="clear" type="button">Clear filters</button></section>
<section aria-labelledby="findings-title"><div class="section-title"><h2 id="findings-title">Discrepancy register</h2><p id="result-count" aria-live="polite"></p></div><div id="findings"></div></section>
<section class="review-export"><div><h2>Keep your review</h2><p>Download notes before changing browser or computer. A changed source package starts a separate review.</p></div><div><label for="reviewer">Reviewer name</label><input id="reviewer" maxlength="160" placeholder="Your name"></div><button id="export" type="button">Export review notes</button><p id="storage-status" role="status"></p></section>
<section aria-labelledby="sources-title"><h2 id="sources-title">Source documents and revisions</h2><p>CSV record numbers count the header as record 1. Source SHA-256 values bind each quoted record to its original bytes.</p><div id="sources"></div></section>
<footer>Broadbridge Oil &amp; Gas · Software fixture, not an issued engineering deliverable.</footer></main>
<script id="report-data" type="application/json">{payload}</script><script src="review.js"></script></body></html>"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=HERE / "fixtures")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    temp = None
    try:
        source = args.package.resolve()
        out = args.out.resolve()
        if out.exists():
            raise ValueError("Output directory already exists; choose a fresh directory")
        if out == source or source in out.parents:
            raise ValueError("Output must be outside the input package")
        report = analyze(source)
        # Build privately, publish complete output in a same-filesystem rename.
        out.parent.mkdir(parents=True, exist_ok=True)
        temp = Path(tempfile.mkdtemp(prefix=".document-review-", dir=out.parent))
        (temp / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (temp / "normalized.json").write_text(json.dumps({"report_id": report["report_id"], "documents": report["documents"]},
            indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        (temp / "report.html").write_text(render_html(report), encoding="utf-8", newline="\n")
        for name in ["review.css", "review.js"]:
            shutil.copyfile(HERE / "web" / name, temp / name)
        temp.rename(out)
        temp = None
        print(json.dumps({"report_id": report["report_id"], **report["summary"], "output": str(out), "synthetic": True}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Document review failed: {exc}", file=sys.stderr)
        return 2
    finally:
        if temp is not None:
            shutil.rmtree(temp)


if __name__ == "__main__":
    sys.exit(main())
