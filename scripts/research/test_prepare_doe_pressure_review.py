import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).with_name("prepare_doe_pressure_review.py")
    assert path.exists(), "DOE evidence packet builder not implemented"
    spec = importlib.util.spec_from_file_location("prepare_doe_pressure_review", path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def pages():
    return [{"pdf_page": n, "printed_page": f"HT-01 {n-26}", "text": "Synthetic extraction (1-9) (1-10)",
             "layout_text": "Synthetic layout", "glyphs": [], "table_candidates": [],
             "image": f"page-{n:03}.png"} for n in [35, 36, 37]]


def test_assembly_retains_locators_exceptions_and_blank_review():
    m = module()
    p = m.assemble_packet(pages(), {"pypdf": "fixture"}, "fixture frontmatter")
    assert p["source"]["sha256"] == m.PDF_SHA256
    assert p["source"]["family_id"] == "DOE-HDBK-1012"
    assert [r["pdf_page"] for r in p["pages"]] == [35, 36, 37]
    assert p["training_approved"] is False
    assert p["rights_review"]["status"] == "pending"
    assert p["technical_review"]["reviewer"] is None
    assert p["split"] is None and "candidates" not in p
    assert all(r["status"] == "needs_review" for r in p["exceptions"])
    assert len(p["equation_proposals"]) == 2
    assert len(p["conversion_rows_proposed"]) == 4
    assert p["conversion_rows_proposed"][-1]["right_value"] == "1000"
    assert "original" in p["conversion_rows_proposed"][-1]["note"]
    assert all(r["reviewer"] is None for r in p["equation_proposals"])
    assert json.loads(json.dumps(p)) == p


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "wrong_page", "empty_text"])
def test_page_loss_or_substitution_stops_packet(mutation):
    p = pages()
    if mutation == "missing": p.pop()
    elif mutation == "duplicate": p[1] = p[0]
    elif mutation == "wrong_page": p[1]["pdf_page"] = 55
    else: p[1]["text"] = ""
    with pytest.raises(ValueError):
        module().assemble_packet(p, {}, "frontmatter")


def test_wrong_original_is_rejected_without_creating_output(tmp_path):
    original = tmp_path / "wrong.pdf"
    original.write_bytes(b"%PDF-1.4 wrong original")
    out = tmp_path / "result"
    with pytest.raises(ValueError, match="source hash"):
        module().main(["--pdf", str(original), "--out", str(out)])
    assert not out.exists()


def test_existing_output_is_never_overwritten(tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    with pytest.raises(ValueError, match="new absolute"):
        module().main(["--pdf", str(tmp_path / "does-not-exist.pdf"), "--out", str(out)])


def test_blank_worksheet_asks_for_acceptance_instead_of_scoring_itself():
    m = module()
    p = m.assemble_packet(pages(), {}, "frontmatter")
    md = m.review_markdown(p)
    assert "No questions or answers have been admitted to training" in md
    assert all(f"page-{n:03}.png" in md for n in [35, 36, 37])
    assert "Reviewer: ______" in md
    assert "P_abs = P_atm + P_gauge" in md
    assert "Unresolved" in md
