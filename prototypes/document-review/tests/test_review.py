"""Behavior tests: seeded defects, clean controls, provenance, and CLI boundaries."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("document_demo_review", ROOT / "review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


@pytest.fixture
def package(tmp_path):
    target = tmp_path / "package"
    shutil.copytree(ROOT / "fixtures", target)
    return target


def edit_csv(path, transform):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    transform(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def identities(report):
    return {(f["rule"], f["tag"], f["field"]) for f in report["findings"]}


def test_finds_all_hand_seeded_defects_without_extra_findings(package):
    expected = json.loads((ROOT / "tests/expected_findings.json").read_text())
    report = review.analyze(package)
    assert identities(report) == {tuple(row) for row in expected["findings"]}
    assert report["summary"]["assets"] == 12
    assert report["summary"]["findings"] == 10
    assert all(f["disposition"] == "pending" for f in report["findings"])


def test_preserves_operating_vs_design_as_not_comparable(package):
    report = review.analyze(package)
    assert not [f for f in report["findings"] if f["tag"] == "E-203"]
    note = next(n for n in report["not_compared"] if n["tag"] == "E-203")
    assert note["reason"] == "different_conditions"
    assert [e["values"]["condition"] for e in note["evidence"]] == ["operating", "design"]


def test_equivalent_pressure_and_temperature_do_not_raise_conflict(package):
    edit_csv(package / "datasheets_B.csv", lambda rows: rows[0].update(temperature="77", temperature_unit="degF"))
    assert not [f for f in review.analyze(package)["findings"] if f["tag"] == "P-101"]


def test_detects_real_disagreement_after_unit_conversion(package):
    edit_csv(package / "datasheets_B.csv", lambda rows: rows[0].update(pressure="1100"))
    assert ("value_conflict", "P-101", "pressure") in identities(review.analyze(package))


def test_gauge_absolute_comparison_does_not_invent_atmospheric_pressure(package):
    report = review.analyze(package)
    flags = [f for f in report["findings"] if f["tag"] == "V-302"]
    assert [f["rule"] for f in flags] == ["basis_mismatch"]
    assert flags[0]["category"] == "needs_review"


def test_all_evidence_resolves_to_exact_source_hash_revision_and_row(package):
    report = review.analyze(package)
    docs = {d["document_key"]: d for d in report["documents"]}
    for finding in report["findings"]:
        assert finding["evidence"]
        for evidence in finding["evidence"]:
            doc = docs[evidence["document_key"]]
            assert evidence["sha256"] == hashlib.sha256((package / doc["file"]).read_bytes()).hexdigest()
            assert evidence["revision"] == doc["revision"]
            assert any(r["locator"] == evidence["locator"] and r["values"] == evidence["values"] for r in doc["records"])
    assert not any(d["revision"] == "A" for d in report["documents"] if d["status"] == "approved")


def test_superseded_numeric_changes_cannot_create_current_value_findings(package):
    before = review.analyze(package)
    edit_csv(package / "datasheets_A.csv", lambda rows: rows[0].update(pressure="222"))
    after = review.analyze(package)
    assert identities(before) == identities(after)
    assert before["report_id"] != after["report_id"]


def test_duplicate_records_are_not_silently_selected_for_comparison(package):
    edit_csv(package / "equipment_B.csv", lambda rows: rows[2].update(pressure="987"))
    flags = [f["rule"] for f in review.analyze(package)["findings"] if f["tag"] == "P-102"]
    assert flags == ["duplicate_tag"]


def test_ambiguous_datasheet_does_not_generate_fabricated_missing_links(package):
    report = review.analyze(package)
    assert not any(f["rule"] == "missing_datasheet" and f["tag"] in ["P-103", "P-104"] for f in report["findings"])


def test_missing_datasheet_is_visible(package):
    edit_csv(package / "datasheets_B.csv", lambda rows: rows.__setitem__(slice(None), [r for r in rows if r["asset_tags"] != "F-601"]))
    assert ("missing_datasheet", "F-601", "datasheet_id") in identities(review.analyze(package))


@pytest.mark.parametrize("value", ["", "unknown", "NaN", "Infinity", "bad"])
def test_missing_or_nonfinite_pressure_is_never_compared_as_a_number(package, value):
    edit_csv(package / "datasheets_B.csv", lambda rows: rows[0].update(pressure=value))
    flags = [f for f in review.analyze(package)["findings"] if f["tag"] == "P-101"]
    assert len(flags) == 1 and flags[0]["rule"] == "unusable_value"
    assert flags[0]["category"] == "needs_review"


@pytest.mark.parametrize("status", ["approved", "superseded"])
def test_multiple_or_zero_approved_revisions_refuses_package(package, status):
    edit_csv(package / "revision_index.csv", lambda rows: [r.update(status=status) for r in rows if r["document_id"] == "REG-001"])
    with pytest.raises(ValueError, match="approved revision"):
        review.analyze(package)


def test_unknown_referenced_revision_is_not_called_superseded(package):
    edit_csv(package / "equipment_B.csv", lambda rows: [r.update(datasheet_revision="Z") for r in rows if r["tag"] == "T-401"])
    flags = [f["rule"] for f in review.analyze(package)["findings"] if f["tag"] == "T-401"]
    assert flags == ["unknown_revision"]


@pytest.mark.parametrize("filename", ["../outside.csv", "/absolute.csv", "C:\\outside.csv"])
def test_source_paths_must_stay_inside_package(package, filename):
    edit_csv(package / "revision_index.csv", lambda rows: rows[0].update(file=filename))
    with pytest.raises(ValueError, match="file"):
        review.analyze(package)


def test_malformed_csv_and_unknown_headers_refused(package):
    with (package / "equipment_B.csv").open("a") as f:
        f.write("too,many,columns,1,2,3,4,5,6,7,8,9,10,11,12\n")
    with pytest.raises(ValueError, match="CSV"):
        review.analyze(package)


def test_svg_entities_refused_before_parsing(package):
    (package / "drawing_B.svg").write_text('<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///C:/private">]><svg>&x;</svg>')
    with pytest.raises(ValueError, match="SVG"):
        review.analyze(package)


def test_source_text_cannot_become_executable_report_markup(package):
    attack = '</script><script>alert("source")</script>'
    edit_csv(package / "equipment_B.csv", lambda rows: rows[0].update(service=attack))
    report = review.analyze(package)
    html = review.render_html(report)
    assert attack not in html
    assert "\\u003c/script" in html


def test_report_deterministic_and_ignores_unindexed_answer_key(package):
    before = review.analyze(package)
    (package / "answer_key.json").write_text('{"always_accept":true}')
    assert review.analyze(package) == before
    assert "always_accept" not in json.dumps(before)


def test_cli_writes_report_without_changing_sources_and_refuses_overwrite(package, tmp_path):
    before = {p.name: p.read_bytes() for p in package.iterdir()}
    out = tmp_path / "out"
    command = [sys.executable, str(ROOT / "review.py"), "--package", str(package), "--out", str(out)]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    assert {"report.html", "report.json", "normalized.json", "review.css", "review.js"} <= {p.name for p in out.iterdir()}
    assert json.loads((out / "report.json").read_text())["summary"]["findings"] == 10
    assert {p.name: p.read_bytes() for p in package.iterdir()} == before
    again = subprocess.run(command, capture_output=True, text=True)
    assert again.returncode != 0
    assert "exists" in again.stderr


def test_output_inside_input_is_refused(package):
    result = subprocess.run([sys.executable, str(ROOT / "review.py"), "--package", str(package), "--out", str(package / "out")], capture_output=True, text=True)
    assert result.returncode != 0
    assert not (package / "out").exists()


def test_datasheet_only_asset_is_reported(package):
    def add_orphan(rows):
        rows.append(dict(rows[0], row_id="D99", asset_tags="X-999"))
    edit_csv(package / "datasheets_B.csv", add_orphan)
    assert ("unmatched_datasheet_tag", "X-999", "asset_tags") in identities(review.analyze(package))


def test_missing_datasheet_reference_does_not_guess_the_document(package):
    edit_csv(package / "equipment_B.csv", lambda rows: rows[0].update(datasheet_id=""))
    edit_csv(package / "datasheets_B.csv", lambda rows: rows[0].update(pressure="9999"))
    flags = [f["rule"] for f in review.analyze(package)["findings"] if f["tag"] == "P-101"]
    assert flags == ["missing_required_field"]


def test_generated_artifacts_use_lf_bytes_for_cross_platform_reproduction(package, tmp_path):
    out = tmp_path / "portable"
    assert review.main(["--package", str(package), "--out", str(out)]) == 0
    for name in ["report.json", "normalized.json", "report.html"]:
        assert b"\r\n" not in (out / name).read_bytes(), name
