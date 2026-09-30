"""Prepare a local DOE pressure review proposal, never a training release.

This is an authored worksheet, not model-generated data or a new case contract.
No network, credentials, model, database or training calls are made. A checksum
binds the extraction evidence; it does not confer technical or rights approval.
"""
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

SOURCE = "DOE-HDBK-1012-1-92"
FAMILY = "DOE-HDBK-1012"
SOURCE_SHA = "3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9"
PAGES = [35, 36, 37]
TOLERANCE = "Proposed +/-0.05 psi for the rounded one-decimal answer; not instrument accuracy. Reviewer acceptance pending."
EXCLUSIONS = [
    "Hydrostatic numerical examples: resolve mass density, weight density and g/g_c conventions first.",
    "Universal use of 14.7 psia or rounded water/mercury column conversions without stated reference conditions.",
    "Figure 2 connectivity, native vision training, equipment design, set points or operating recommendations.",
    "General claims that negative absolute liquid pressure is physically impossible in every context.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pressure_result(mode, atmospheric, reading):
    """Illustrative same-psi pressure-basis conversion, with explicit inputs."""
    if mode not in {"gauge", "vacuum"}:
        raise ValueError("Unknown pressure basis")
    try:
        a, r = Decimal(atmospheric), Decimal(reading)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Supply numeric atmospheric pressure and reading") from None
    if not a.is_finite() or not r.is_finite() or a <= 0:
        raise ValueError("Supply finite inputs and positive atmospheric pressure")
    if mode == "vacuum" and r < 0:
        raise ValueError("Vacuum depression is a nonnegative magnitude")
    result = a + r if mode == "gauge" else a - r
    if result < 0:
        raise ValueError("Inputs imply negative absolute pressure outside this recipe")
    return format(result, "f")


def question_prompt(question):
    """Question-only projection for inspection; does not execute a baseline."""
    return {key: question[key] for key in
            ("question_id", "question", "source_id", "evidence_ids")}


def build_proposal(packet_sha):
    if len(packet_sha) != 64 or any(c not in "0123456789abcdef" for c in packet_sha):
        raise ValueError("Bind the exact extraction packet SHA-256")
    questions = []

    def add(kind, question, answer, fail, pages=(35, 36), calculation=None):
        row = {"question_id": f"DOE-PRESSURE-DRAFT-{len(questions)+1:02}",
            "type": kind, "question": question, "reference_answer": answer,
            "hard_fail_criteria": fail, "tolerance": TOLERANCE if calculation else "not applicable",
            "source_id": SOURCE, "family_id": FAMILY,
            "evidence_ids": [f"{SOURCE}:pdf-{n:03}" for n in pages],
            "split": None, "author": "assistant-authored review proposal",
            "review": {"status": "pending", "reviewer": None, "date": None, "decision": None},
            "training_approved": False}
        if calculation:
            row["calculation"] = calculation
        questions.append(row)

    add("brief", "An illustrative pressure log mixes psia, psig and a positive vacuum-depression reading. Give a short checking plan before comparing the entries.",
        "Identify the reference basis and units for each reading. Absolute pressure is relative to vacuum; gauge is relative to local atmospheric pressure. Obtain the relevant atmospheric pressure, confirm the vacuum sign convention, convert onto one basis and retain the original readings. These definitions alone do not establish operating acceptability.",
        "Treating psia and psig as interchangeable; silently assuming 14.7 psia; declaring the process safe from these data.")
    add("brief", "An illustrative log contains a negative psig reading. Explain briefly what it means and which extra value is required to express it in psia.",
        "It is below the gauge's atmospheric reference, not automatically a negative absolute pressure. With consistent psi units and the applicable local atmospheric pressure, P_abs = P_atm + P_gauge. Confirm the measurement basis before using it.",
        "Equating negative gauge pressure with negative absolute pressure; inventing atmospheric pressure.")
    add("brief", "Summarize what equations 1-9 and 1-10 on PDF page 36 can and cannot establish for an engineer reading a pressure report.",
        "They relate absolute pressure to atmospheric pressure plus gauge pressure, or atmospheric pressure minus a positive vacuum-depression magnitude. They require compatible units and known reference conditions. They do not by themselves establish flow, equipment capacity or a permissible operating limit.",
        "Reversing either sign; claiming these equations alone establish equipment limits.")
    add("missing_data", "A note says only 'pressure = 35 psi'. What must be clarified before converting it to absolute pressure?",
        "Ask whether the value is absolute, gauge or a vacuum depression; confirm units and sign convention. If gauge or vacuum, obtain the atmospheric reference applicable to the reading. Preserve uncertainty rather than assigning a basis.",
        "Assuming gauge or absolute without evidence; adding a default atmosphere.")
    add("missing_data", "An illustrative instrument log says '5 inches vacuum'. What is missing for a defensible conversion to absolute pressure in psi?",
        "Clarify whether this is a fluid-column pressure unit, which fluid/reference conditions the calibration assumes, the vacuum magnitude/sign convention and the atmospheric reference. A validated unit conversion is required; the handbook's rounded column examples alone do not supply site conditions.",
        "Treating inches as psi; choosing water or mercury without evidence; presenting an exact absolute result.", pages=(35, 36, 37))
    add("missing_data", "A report gives a psig reading from a remote site but no atmospheric pressure. Which specific reference input is missing, and why does it matter?",
        "The atmospheric pressure applicable to the gauge reference at the site/time is missing. It is the additive term needed to compute absolute pressure from gauge pressure; 14.7 psia is a handbook example, not evidence of the site's pressure.",
        "Inventing a site atmosphere or a precise absolute answer.")
    for mode, atm, reading in [("gauge", "14.2", "36.8"), ("gauge", "14.5", "-2.1"), ("vacuum", "14.7", "5.0")]:
        result = pressure_result(mode, atm, reading)
        label = f"gauge pressure {reading} psig" if mode == "gauge" else f"positive vacuum depression {reading} psi below atmosphere"
        sign = "+" if mode == "gauge" else "-"
        add("calculation", f"Illustrative arithmetic only: given local atmospheric pressure {atm} psia and {label}, compute absolute pressure in psia to one decimal. Treat supplied inputs as exact for this exercise.",
            f"P_abs = P_atm {sign} P_{'gauge' if mode == 'gauge' else 'vac'}. {atm} {sign} ({reading}) = {result} psia. This is a pressure-basis conversion, not an operating-limit assessment.",
            "Wrong reference basis or sign; reporting the result in psig; replacing the supplied atmospheric pressure; claiming instrument accuracy or process safety.",
            pages=(36,), calculation={"method": "illustrative_pressure_basis_v1", "mode": mode,
                "atmospheric_psia": atm, "reading_psi": reading, "result": result,
                "unit": "psia", "verification": "Python Decimal arithmetic; method acceptance pending"})
    add("grounded_explanation", "Using PDF page 36, explain why gauge pressure is added in equation 1-9 while a positive vacuum depression is subtracted in equation 1-10.",
        "Gauge pressure is a signed difference from atmosphere, so adding that difference gives absolute pressure. In the sub-atmospheric convention used here, vacuum depression is a positive amount below atmosphere, so it is subtracted. A negative gauge reading must not also be subtracted as though it were a positive depression. Cite equations 1-9 and 1-10.",
        "Double-negating a negative gauge reading; reversing a sign; citing a formula absent from the evidence.", pages=(36,))
    add("grounded_explanation", "Explain, using the pressure definitions on PDF page 35, why two equal numerical psi readings need not represent the same pressure.",
        "The reference bases can differ: psia is referenced to vacuum and psig to atmosphere. Equal numerical values with different bases describe different absolute pressures. The units and reference must accompany the number; cite the page's absolute/gauge definitions.",
        "Saying equal numerical psi values are always interchangeable.", pages=(35,))
    add("grounded_explanation", "Why should an answer using this handbook distinguish a stated atmospheric input from its 14.7 psia example? Ground the answer in the pressure equations and worked-example assumptions.",
        "P_atm is an explicit term in equations 1-9 and 1-10; the examples assume 14.7 psia. A calculation with a different supplied atmospheric pressure must use that input. A missing site value remains missing; the example does not measure the site.",
        "Using the example's atmospheric value despite a different supplied value; treating it as universally exact.", pages=(36, 37))
    add("abstention", "For an illustrative vessel, all you have is '80 psia'. Can you determine its maximum safe operating pressure from PDF pages 35-37?",
        "No. These pages define pressure and show elementary conversions; they do not provide this vessel's allowable pressure, design conditions, condition assessment or applicable design basis. Do not turn a measured value or worked-example watch limit into a vessel limit.",
        "Giving a vessel safe operating limit or adopting the handbook's watch rating.")
    add("abstention", "Can the first candidate set use the page-36 diver example's density 64 lbm/ft3 and P = rho H directly as a dimensionally explicit hydrostatic recipe?",
        "Not without resolving the source's implicit mass/force and gravity convention. The equation as transcribed with mass density needs that convention made explicit by a qualified reviewer. Exclude numerical hydrostatic examples from this first set rather than silently rewriting the source.",
        "Accepting a dimensionally incomplete mass-density formula as a verified general recipe; silently changing lbm to force units.", pages=(36,))
    add("abstention", "Can the handbook's pressure-scale Figure 2 establish pipe connections or flow direction in a plant P&ID?",
        "No. It illustrates pressure reference levels, not plant piping topology. No plant connectivity or flow direction can be inferred from it. Request the relevant approved drawing/model and use the separate connectivity-verification process.",
        "Inferring a plant connection or flow direction from the pressure-scale sketch.", pages=(35,))

    proposals = [
        ("figure", "Exclude graph/topology use; use definitions and equations for text questions only."),
        ("subscripts", "Page-image transcription: P_abs = P_atm + P_gauge and P_abs = P_atm - P_vac. Reviewer must confirm symbols/sign conventions."),
        ("symbol", "PDFium image retains rho; preserve raw parser disagreement. Do not substitute r or silently repair the hydrostatic recipe."),
        ("mass-force", "Exclude both hydrostatic numeric examples until mass/force/gravity conventions are explicitly accepted."),
        ("assumptions", "Use explicitly supplied atmospheric inputs. Exclude rounded fluid-column conversions from numerical candidates."),
        ("exponent", "Image shows 10^3, proposed transcription 1000. Retain as a review finding; do not admit the column-conversion recipe."),
        ("table", "Conversions are manually normalized typeset rows; detected-table count remains zero. Do not relabel them parser-extracted tables."),
        ("scope", "Propose pressure-basis education only. No process-design, equipment-limit or site-operation claims; reviewer decides applicability."),
        ("rights", "Brad records exact pages/credits/permission basis. Distribution Statement A and contractor credits are evidence to inspect, not an automatic training decision."),
    ]
    return {"schema": "broadbridge.first_dataset_review_proposal/1",
        "status": "pending_independent_review", "training_approved": False,
        "source_id": SOURCE, "source_sha256": SOURCE_SHA, "extraction_packet_sha256": packet_sha,
        "family_id": FAMILY, "split": None,
        "intended_use": "Task/method/question review only; family allocation precedes any admitted generation, baseline or release.",
        "rights_review": {"status": "pending", "reviewer": None, "decision": None},
        "family_review": {"status": "pending", "note": "Related volumes, revisions and derivatives stay together; inspect historical allocation before admitting examples."},
        "gate_0_case_questions_added": 0, "model_calls": 0, "excluded_scope": EXCLUSIONS,
        "exception_proposals": [{"issue_id": key, "proposed_action": action,
            "status": "pending_independent_review", "reviewer": None} for key, action in proposals],
        "questions": questions}


def verify_extraction(directory):
    directory = directory.resolve(strict=True)
    receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
    required = {"packet.json", "REVIEW.md", "review.csv"} | {
        f"page-{n:03}{suffix}" for n in PAGES for suffix in (".png", ".txt", ".layout.txt")}
    if (receipt.get("schema") != "broadbridge.doe_extraction_receipt/1"
            or receipt.get("source_sha256") != SOURCE_SHA or receipt.get("pdf_pages") != PAGES
            or receipt.get("training_approved") is not False or receipt.get("model_calls") != 0):
        raise ValueError("Wrong or incomplete extraction receipt")
    files = receipt.get("files", [])
    names = [row.get("path") for row in files]
    if len(names) != len(required) or set(names) != required:
        raise ValueError("Missing, repeated or unexpected extraction file")
    for row in files:
        path = directory / row["path"]
        if path.is_symlink() or path.resolve().parent != directory or not path.is_file():
            raise ValueError("Unsafe extraction file")
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError("Extraction artifact changed")
    packet_path = directory / "packet.json"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("schema") != "broadbridge.source_review_packet/1"
            or packet.get("source", {}).get("sha256") != SOURCE_SHA
            or packet.get("source", {}).get("family_id") != FAMILY
            or [p.get("pdf_page") for p in packet.get("pages", [])] != PAGES
            or packet.get("training_approved") is not False):
        raise ValueError("Wrong source packet")
    return digest(packet_path)


def review_markdown(proposal, evidence_dir):
    lines = ["# First dataset: pressure-basis review proposal", "",
        "**Pending independent engineering and rights review. No training release or baseline run.**", "",
        "Fifteen assistant-authored drafts, three per question type, using one DOE handbook family. "
        "These are educational review proposals, not signed case questions or an evaluation sample. "
        "Splits remain unassigned; do not split this family by page or paraphrase.", "",
        f"Extraction packet SHA-256: `{proposal['extraction_packet_sha256']}`.",
        f"Source PDF SHA-256: `{SOURCE_SHA}`.", "",
        "[DOE original PDF, starting at page 35](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35). "
        "The page numbers here are PDF pages, not printed handbook pages. Compare pages 35-37, printed HT-01 pages 9-11.", "",
        f"[Local extraction review and page renders](<{(evidence_dir / 'REVIEW.md').as_posix()}>). "
        "This local link is specific to Brad's workstation; another operator can recreate it with the commands in docs/FIRST_DATASET_REVIEW.md.", "",
        "## Reviewer actions", "",
        "1. Bill or an appointed engineer: choose whether pressure-basis checking is a useful first task; suggest a higher-priority task if needed.",
        "2. Check each correction proposal and each draft answer, assumptions, tolerance and hard-fail criteria. Record accept/revise/exclude, correction, evidence, name and date in review.csv. Blank rows remain pending.",
        "3. Brad: separately record rights/credits/permission evidence for the precise source and pages. This worksheet records no permission grant.",
        "4. Before admission, check all related-family history and allocate the entire family to one split. Independent validation/test families are still needed; these 15 drafts are not 15 independent test cases.",
        "5. Pass signed decisions and exact proposal hash through the existing acceptance/release workflow; editing this worksheet does not produce a release.", "",
        "## Excluded from this first scope", ""]
    lines.extend(f"- {item}" for item in proposal["excluded_scope"])
    lines += ["", "## Nine proposed exception dispositions", ""]
    for item in proposal["exception_proposals"]:
        lines += [f"- **{item['issue_id']}** — {item['proposed_action']} Independent decision: ______"]
    lines += ["", "## Draft questions and references", ""]
    for q in proposal["questions"]:
        lines += [f"### {q['question_id']} — {q['type']}", "", q["question"], "",
            f"**Draft reference:** {q['reference_answer']}", "",
            f"**Critical errors:** {q['hard_fail_criteria']}", "",
            f"**Tolerance:** {q['tolerance']}", "",
            f"**Evidence:** {', '.join(q['evidence_ids'])}.", "",
            "**Decision / correction / reviewer / date:** ______", ""]
    lines += ["## What this does not complete", "",
        "Gate 0 still requires recorded rights/storage and at least 30 signed case-derived questions across all five types. "
        "This proposal contributes zero to that count. Production case status is not checked here. "
        "S0-cases, scored retrieval comparison, accepted family-separated release, exact-release token audit and "
        "a bounded GPU run decision remain prerequisites in the current plan. No model answer or score is fabricated.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.out.is_absolute() or args.out.exists():
        raise ValueError("Choose a new absolute output directory")
    sha = verify_extraction(args.packet_dir)
    proposal = build_proposal(sha)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "proposal.json").write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8", newline="\n")
    (args.out / "REVIEW.md").write_text(review_markdown(proposal, args.packet_dir.resolve()), encoding="utf-8", newline="\n")
    with (args.out / "review.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["item_id", "disposition", "correction", "evidence", "reviewer", "date"], lineterminator="\n")
        writer.writeheader()
        writer.writerows({"item_id": item} for item in ["task-and-scope", "rights-and-credits", "family-allocation"]
            + [f"exception:{r['issue_id']}" for r in proposal["exception_proposals"]]
            + [q["question_id"] for q in proposal["questions"]])
    receipt = {"schema": "broadbridge.first_dataset_review_receipt/1", "source_sha256": SOURCE_SHA,
        "extraction_packet_sha256": sha, "questions": 15, "question_types": 5, "families": 1,
        "exception_proposals": 9, "model_calls": 0, "training_examples_admitted": 0,
        "gate_0_case_questions_added": 0, "training_approved": False,
        "files": [{"path": p.name, "bytes": p.stat().st_size, "sha256": digest(p)} for p in sorted(args.out.iterdir())]}
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "files"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
