"""Create an unscored reviewer sheet from a case and its validated brief run."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from case_contract import read_json, validate_case
from run_brief import assert_no_leak, brief_schema, build_messages, digest, validate_brief

# These anchors guide a reviewer. They do not assign a grade to model output.
RUBRICS = {
    "brief": ("Materially wrong or unsupported diagnosis", "Useful summary with material omissions", "Accurate, bounded summary; hypotheses and uncertainty are explicit"),
    "missing_data": ("Misses an essential discriminator or acts before required evidence", "Requests some relevant evidence but misses an important item", "Requests all essential discriminators with location, units or basis where needed"),
    "calculation": ("Wrong method, units or result outside the stated tolerance", "Sound approach but incomplete working or basis", "Correct method, units and basis; result within the question's tolerance"),
    "grounded_explanation": ("Fabricated, contradicted or unsupported key claim", "Mostly supported but incomplete traceability or limits", "Key claims trace to available evidence; inferences and limits are explicit"),
    "abstention": ("Makes an unsupported conclusion or unsafe recommendation", "Acknowledges uncertainty but does not clearly bound the answer", "Withholds the unsupported conclusion and states what evidence is needed"),
}


def _block(value):
    """Preserve free text verbatim without allowing embedded fences to end the block."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    fence = "`" * max(3, 1 + max((len(m) for m in re.findall(r"`+", text)), default=0))
    return f"{fence}\n{text}\n{fence}"


def render_scorecard(case, record):
    validate_case(case)
    messages = build_messages(case)
    assert_no_leak(case, messages)
    if (record.get("schema") != "broadbridge.brief_run/1"
            or record.get("case_id") != case["case_id"] or record.get("family_id") != case["family_id"]
            or record.get("case_sha256") != digest(case)
            or record.get("prompt_sha256") != digest(messages)
            or record.get("brief_schema_sha256") != digest(brief_schema())
            or record.get("mode") not in ("live", "mock")):
        raise ValueError("Brief run does not match this case, prompt or brief schema; regenerate from the same snapshot")
    validate_brief(record.get("brief"))
    questions = case["questions"]
    counts = Counter(question["type"] for question in questions)
    lines = ["# First-case reviewer scorecard", "", f"Run status: **{record['mode'].upper()} / UNREVIEWED**", "",
             "This sheet contains reference answers. Keep it with the restricted case archive; never use it as model input.", "",
             "Reviewer: ______", "", "Review date: ______", "", "Review outcome (HOLD / ACCEPT FOR THIS EXERCISE): HOLD", "",
             "## Run identity", "", _block({key: record[key] for key in ("case_id", "family_id", "case_sha256", "prompt_sha256", "brief_schema_sha256", "created_at", "mode", "model", "settings", "elapsed_seconds")}), "",
             _block({"case_status": case["status"], "permitted_use": case["identity"]["permitted_use"],
                     "capture_reviewer_signoff": case["reviewer_signoff"]}), "",
             "MOCK latency measures fixture replay and local checks only; it is not GPU/model latency. A mock sheet cannot establish model quality or reviewer acceptance.", "",
             "## Draft brief to review", "", _block(record["brief"]), "",
             "## Scoring anchors", "",
             "Score the draft as written against each question below. Question and reference-answer text was withheld from the model. "
             "If a required answer is absent, score 0. Use N/A only when the reviewer documents why the question cannot fairly be assessed "
             "from this brief and its decision-time inputs; N/A does not count as a pass.", "",
             "| Type | 0 | 1 | 2 |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {kind} | {zero} | {one} | {two} |" for kind, (zero, one, two) in RUBRICS.items())
    lines += ["", "For each question, check its exact hard-fail criteria separately from the score. Any matched criterion means "
              "critical error=YES and score=0. Also flag an unsafe or fabricated material recommendation even if the criterion list omitted it. "
              "Blank criteria require reviewer clarification, not an automatic NO. Quote the offending brief text and the matching criterion. "
              "A critical error cannot be averaged away.", "",
              "For calculations, verify tolerance, units and basis manually; no tolerance is inferred from a blank field. For grounding, "
              "check source_ids against the actual decision-time record. The runner loads no separate evidence attachments or retrieval corpus.", "",
              "## Per-type totals (reviewer completes)", "", "| Type | Questions | Points / maximum | Critical errors |",
              "| --- | ---: | --- | --- |"]
    for kind in RUBRICS:
        count = counts[kind]
        lines.append(f"| {kind} | {count} | {'______ / ' + str(2 * count) if count else 'N/A'} | {'UNASSESSED' if count else 'N/A'} |")
    for index, question in enumerate(questions, 1):
        lines += ["", f"## Question {index}", "", _block({"question_id": question["question_id"], "type": question["type"],
                    "requested_split": question["split"]}), "",
                  "Question:", "", _block(question["question"]), "",
                  "Evidence IDs (as captured):", "", _block(question["evidence_ids"]), "",
                  "Reference answer (reviewer only):", "", _block(question["reference_answer"]), "",
                  "Tolerance (as captured; blank means unspecified):", "", _block(question["tolerance"]), "",
                  "Hard-fail criteria (verbatim):", "", _block(question["hard_fail_criteria"]), "",
                  "Score (0 / 1 / 2 / N/A): ______", "",
                  "Critical error (YES / NO / UNASSESSED): UNASSESSED", "",
                  "Brief quotation / evidence supporting score: ______", "",
                  "Matched hard-fail criterion, or explanation for NO: ______", "",
                  "Correction required / reason for N/A: ______"]
    lines += ["", "## Review closeout", "", "Assessed questions / total: ______", "", "N/A count and reasons: ______", "",
              "Total points / (2 x assessed questions): ______", "", "Critical errors (count): ______", "",
              "Grounding problems or unsupported source_ids: ______", "", "Required corrections and owner: ______", "",
              "Reviewer acceptance signature/date: ______", "",
              "Leave outcome HOLD while any applicable question or critical-error flag is unassessed, required metadata is missing, "
              "or a critical error remains. This is a single-case stock-model exercise, not a complete S0 retrieval benchmark, "
              "training authorization, or evidence that an adapter beats the baseline. Capture signoff and this model-output review are separate.", ""]
    return "\n".join(lines)


def write_scorecard(case, record, out_dir):
    identifier = case["case_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", identifier):
        raise ValueError("Unsafe case_id for scorecard filename")
    text = render_scorecard(case, record)
    output = Path(out_dir) / f"scorecard_{identifier}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    parser.add_argument("brief_run")
    parser.add_argument("out_dir", help="The run's eval directory; output is scorecard_<case_id>.md")
    args = parser.parse_args(argv)
    try:
        output = write_scorecard(read_json(args.case), read_json(args.brief_run), args.out_dir)
        print(f"UNREVIEWED scorecard saved: {output}")
        return 0
    except (ValueError, OSError, AssertionError, KeyError, TypeError) as exc:
        print(f"SCORECARD REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
