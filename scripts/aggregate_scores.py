"""Aggregate completed reviewer scorecards into a refreshable offline S0-cases report."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys


QUESTION_TYPES = ("brief", "missing_data", "calculation", "grounded_explanation", "abstention")
SCORE = "Score (0 / 1 / 2 / N/A)"
CRITICAL = "Critical error (YES / NO / UNASSESSED)"
SUPPORT = "Brief quotation / evidence supporting score"
CRITERION = "Matched hard-fail criterion, or explanation for NO"
CORRECTION = "Correction required / reason for N/A"
SIGNATURE = "Reviewer acceptance signature/date"
OUTCOME = "Review outcome (HOLD / ACCEPT FOR THIS EXERCISE)"
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"invalid JSON constant {value}")
    return json.loads(text, object_pairs_hook=unique, parse_constant=invalid)


def _tokens(text):
    """Keep fenced prose opaque, including renderer fences longer than three backticks."""
    fence = None
    block = []
    for line in text.splitlines():
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*", line):
                yield "block", "\n".join(block)
                fence, block = None, []
            else:
                block.append(line)
        else:
            opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", line)
            if opening and (opening[1][0] != "`" or "`" not in opening[2]):
                fence = opening[1]
            else:
                yield "line", line
    if fence:
        raise ValueError("unclosed fenced block")


def _sections(text):
    sections = {"header": []}
    current = "header"
    for kind, value in _tokens(text):
        if kind == "line" and value.startswith("## "):
            current = value[3:].strip()
            if current in sections:
                raise ValueError(f"duplicate section {current}")
            sections[current] = []
        else:
            sections[current].append((kind, value))
    for required in ("Run identity", "Review closeout"):
        if required not in sections:
            raise ValueError(f"missing section {required}")
    return sections


def _metadata(tokens, label):
    content = [(kind, value) for kind, value in tokens if value.strip()]
    if not content or content[0][0] != "block":
        raise ValueError(f"missing fenced {label} metadata")
    data = _json(content[0][1])
    if not isinstance(data, dict):
        raise ValueError(f"invalid {label} metadata")
    return data


def _fields(tokens, labels):
    values = {}
    for kind, line in tokens:
        if kind != "line":
            continue
        for label in labels:
            if line.startswith(label + ":"):
                if label in values:
                    raise ValueError(f"duplicate field {label}")
                values[label] = line[len(label) + 1:].strip()
    return values


def _filled(value):
    value = value.strip().strip("_* .-").casefold()
    return bool(value) and value not in {"unknown", "n/a", "na", "none", "tbd", "todo", "unassessed"}


def _read_card(path):
    sections = _sections(path.read_text(encoding="utf-8-sig"))
    identity = _metadata(sections["Run identity"], "run")
    case_id, mode = identity.get("case_id"), identity.get("mode")
    if not isinstance(case_id, str) or not IDENTIFIER.fullmatch(case_id) or mode not in ("live", "mock"):
        raise ValueError("invalid case_id or mode in run metadata")
    if path.name != f"scorecard_{case_id}.md":
        raise ValueError(f"scorecard filename and run case_id disagree: {path.name} vs {case_id}")
    fields = _fields(sections["header"], ("Reviewer", "Review date", OUTCOME))
    fields.update(_fields(sections["Review closeout"], (SIGNATURE,)))
    reasons = [f"{label} missing or incomplete" for label in ("Reviewer", "Review date", SIGNATURE)
               if not _filled(fields.get(label, ""))]
    if fields.get(OUTCOME) not in ("HOLD", "ACCEPT FOR THIS EXERCISE"):
        reasons.append("Review outcome missing or invalid")
    questions = []
    seen = {}
    for section, tokens in sections.items():
        if not section.startswith("Question "):
            continue
        if section != f"Question {len(questions) + 1}":
            raise ValueError("question sections must be sequential from Question 1")
        data = _metadata(tokens, section)
        question_id, question_type = data.get("question_id"), data.get("type")
        if not isinstance(question_id, str) or not question_id.strip() or question_type not in QUESTION_TYPES:
            raise ValueError(f"invalid {section} metadata")
        question_key = question_id.casefold()
        if question_key in seen:
            raise ValueError(f"duplicate question_id {seen[question_key]} / {question_id}")
        seen[question_key] = question_id
        values = _fields(tokens, (SCORE, CRITICAL, SUPPORT, CRITERION, CORRECTION))
        score, critical = values.get(SCORE, ""), values.get(CRITICAL, "")
        if score not in ("0", "1", "2", "N/A"):
            reasons.append(f"{section}: Score missing or invalid")
        if critical not in ("YES", "NO"):
            reasons.append(f"{section}: critical flag UNASSESSED or invalid")
        if critical == "YES" and score != "0":
            reasons.append(f"{section}: critical YES requires score 0")
        for label in (SUPPORT, CRITERION):
            if not _filled(values.get(label, "")):
                reasons.append(f"{section}: {label} missing or incomplete")
        if score == "N/A" and not _filled(values.get(CORRECTION, "")):
            reasons.append(f"{section}: reason for N/A missing or incomplete")
        questions.append({"type": question_type, "score": score, "critical": critical})
    if not questions:
        raise ValueError("no question sections")
    if fields.get(OUTCOME) == "ACCEPT FOR THIS EXERCISE" and any(q["critical"] == "YES" for q in questions):
        reasons.append("Review outcome inconsistent: critical errors require HOLD")
    # The renderer prints immutable question counts beside the editable grade totals.
    # Check counts only to detect deleted sections; never use handwritten grades here.
    expected_counts = {}
    for token, line in sections.get("Per-type totals (reviewer completes)", []):
        if token == "line" and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[0] in QUESTION_TYPES:
                if cells[0] in expected_counts or len(cells) != 4 or not cells[1].isdigit():
                    raise ValueError("invalid or duplicate static question count row")
                expected_counts[cells[0]] = int(cells[1])
    actual_counts = {kind: sum(q["type"] == kind for q in questions) for kind in QUESTION_TYPES}
    if expected_counts != actual_counts:
        raise ValueError("static question counts disagree with question sections")
    return {"case_id": case_id, "mode": mode, "case_sha256": identity.get("case_sha256"),
            "outcome": fields.get(OUTCOME, ""), "questions": questions, "reasons": reasons}


def _manifest(root):
    path = root / "batch_manifest.json"
    if not path.exists():
        return None, None
    manifest = _json(path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("selected_cases"), list):
        raise ValueError("batch_manifest.json needs selected_cases objects with case_id")
    mode = manifest.get("mode")
    if mode is not None and mode not in ("live", "mock"):
        raise ValueError("batch_manifest.json mode must be live or mock")
    selected = {}
    for item in manifest["selected_cases"]:
        case_id = item.get("case_id") if isinstance(item, dict) else None
        if not isinstance(case_id, str) or not IDENTIFIER.fullmatch(case_id):
            raise ValueError("invalid selected case_id in batch_manifest.json")
        case_key = case_id.casefold()
        if case_key in selected:
            raise ValueError(f"duplicate selected case_id {selected[case_key]['case_id']} / {case_id} in batch_manifest.json")
        selected[case_key] = item
    return selected, mode


def _cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ")


def _manifests(root):
    """Inventory nested batches without silently merging repeated selected case IDs."""
    scopes, expected, errors = {}, defaultdict(list), []
    for path in sorted(root.rglob("batch_manifest.json")):
        try:
            selected, mode = _manifest(path.parent)
            scopes[path.parent] = {"selected": selected, "mode": mode, "error": None}
            for case_id in selected:
                expected[case_id].append(path.parent)
        except (ValueError, OSError) as exc:
            error = f"{path.relative_to(root).as_posix()}: {exc}"
            scopes[path.parent] = {"selected": {}, "mode": None, "error": error}
            errors.append(error)
    return scopes, expected, errors


def _mode_report(mode, cards):
    reviewed = [card for card in cards if not card["reasons"]]
    questions = [question for card in reviewed for question in card["questions"]]
    lines = ["## LIVE reviewed scores" if mode == "live" else "## MOCK rehearsal", ""]
    if mode == "mock":
        lines += ["These are fixture/reviewer workflow checks, not model performance or model acceptance.", ""]
    lines += [f"Cases reviewed: **{len(reviewed)}**", "", f"Cases unreviewed: **{len(cards) - len(reviewed)}**", "",
              f"Critical errors: **{sum(q['critical'] == 'YES' for q in questions)}**", "",
              "| Question type | Scored questions | N/A questions | Mean (0–2) | Critical errors |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for kind in QUESTION_TYPES:
        items = [q for q in questions if q["type"] == kind]
        scored = [int(q["score"]) for q in items if q["score"] != "N/A"]
        mean = f"{sum(scored) / len(scored):.2f}" if scored else "N/A"
        lines.append(f"| {kind} | {len(scored)} | {sum(q['score'] == 'N/A' for q in items)} | {mean} | {sum(q['critical'] == 'YES' for q in items)} |")
    return lines + [""]


def aggregate_scores(run_root):
    """Return (Markdown, structural errors); ordinary incomplete reviews are valid inputs."""
    root = Path(run_root).resolve()
    if not root.is_dir():
        raise ValueError("RUN_ROOT must be an existing directory")
    scopes, expected, errors = _manifests(root)
    paths = defaultdict(list)
    for path in sorted(root.rglob("scorecard_*.md")):
        paths[path.stem[len("scorecard_"):].casefold()].append(path)
    cards = []
    for case_key in sorted(set(paths) | set(expected)):
        files = paths.get(case_key, [])
        batches = expected.get(case_key, [])
        display_ids = {path.stem[len("scorecard_"):] for path in files}
        display_ids.update(scopes[batch]["selected"][case_key]["case_id"] for batch in batches)
        case_id = " / ".join(sorted(display_ids))
        modes = {scopes[batch]["mode"] for batch in batches}
        mode = next(iter(modes)) if len(modes) == 1 else None
        card = {"case_id": case_id, "mode": mode or "unknown", "questions": [],
                "outcome": "", "reasons": [], "paths": [str(p.relative_to(root)).replace("\\", "/") for p in files]}
        if len(batches) > 1:
            manifests = ", ".join((batch / "batch_manifest.json").relative_to(root).as_posix() for batch in batches)
            error = f"{case_id}: duplicate selected case across batches ({manifests})"
            card["reasons"] = [error]
            errors.append(error)
        elif not files:
            card["reasons"] = ["missing scorecard"]
        elif len(files) > 1:
            error = f"{case_id}: duplicate case scorecards ({', '.join(card['paths'])})"
            card["reasons"] = [error]
            errors.append(error)
        else:
            try:
                card.update(_read_card(files[0]))
                containing = [scope for scope in scopes if files[0].is_relative_to(scope)]
                owner = max(containing, key=lambda scope: len(scope.parts)) if containing else None
                if owner is not None:
                    scope = scopes[owner]
                    if scope["error"]:
                        raise ValueError("invalid batch_manifest.json prevents run attribution")
                    selected, manifest_mode = scope["selected"], scope["mode"]
                    if case_key not in selected:
                        raise ValueError("scorecard is not a selected case in batch_manifest.json")
                    expected_id = selected[case_key]["case_id"]
                    if expected_id != card["case_id"]:
                        raise ValueError(f"case_id casing conflict: manifest {expected_id} vs scorecard {card['case_id']}")
                    expected_hash = selected[case_key].get("case_sha256")
                    if expected_hash is not None and expected_hash != card["case_sha256"]:
                        raise ValueError("case_sha256 disagrees with batch_manifest.json")
                    if manifest_mode and card["mode"] != manifest_mode:
                        raise ValueError("run mode disagrees with batch_manifest.json")
                if batches and owner != batches[0]:
                    raise ValueError("scorecard is outside its selected batch manifest directory")
            except (ValueError, OSError) as exc:
                error = f"{case_id}: {exc}"
                card["reasons"] = [error]
                errors.append(error)
        cards.append(card)
    reviewed_count = sum(not card["reasons"] for card in cards)
    lines = ["# S0-cases reviewer score summary", "",
             "Derived from scorecard question fields and run metadata. Handwritten totals and the printed UNREVIEWED banner are not grading inputs.", "",
             f"All-mode inventory: **{reviewed_count} reviewed / {len(cards) - reviewed_count} unreviewed** cases.", "",
             "Batch manifests are discovered recursively; selected cases define expected coverage in each batch. Without an enclosing manifest, only discovered scorecards define the inventory; missing cards cannot be inferred. Repeated case IDs are compared case-insensitively and excluded as ambiguous; original identity spelling must still match exactly.", "",
             "Only completely reviewed cases contribute scores. Means weight scored questions equally; N/A and all questions in incomplete/invalid sheets are excluded. Critical errors cannot be averaged away. A completed HOLD review counts as reviewed, not accepted.", ""]
    if errors:
        lines += ["## STRUCTURAL ERRORS", "", "Resolve these errors before using this report at Gate0 close; affected cases are excluded.", ""]
        lines += [f"- {_cell(error)}" for error in errors]
        lines.append("")
    lines += _mode_report("live", [card for card in cards if card["mode"] == "live"])
    mock_cards = [card for card in cards if card["mode"] == "mock"]
    if mock_cards:
        lines += _mode_report("mock", mock_cards)
    unknown = sum(card["mode"] == "unknown" for card in cards)
    if unknown:
        lines += [f"Cases with unknown mode: **{unknown}** (unreviewed; excluded from both sections).", ""]
    lines += ["## Case review status", "", "| Case | Mode | Status | Outcome | Scorecard | Reason if unreviewed |",
              "| --- | --- | --- | --- | --- | --- |"]
    for card in cards:
        row = [card["case_id"], card["mode"], "UNREVIEWED" if card["reasons"] else "REVIEWED",
               card["outcome"], ", ".join(card["paths"]) or "missing", "; ".join(card["reasons"]) or "—"]
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    if not cards:
        lines += ["", "No selected cases or scorecards found; this is not evidence of review completion."]
    lines += ["", "## Reviewer completion", "",
              "Fill values on the existing labeled lines: Reviewer, Review date, and Reviewer acceptance signature/date. For every question, enter 0, 1, 2, or reasoned N/A; assess critical error YES/NO; provide the brief quotation/evidence and matched criterion or explanation for NO. Critical YES requires score 0. N/A requires a reason on Correction required / reason for N/A. Preserve section labels and the renderer's static Questions counts. Keep outcome HOLD while critical errors or required corrections remain. Rerun this script after review; it replaces only scores_summary.md.", "",
              "This derived report supports S0-cases at Gate0 close. It does not establish S0-retrieval, Gate3, training authorization, or adapter performance. Reviewer judgment and signoff authenticity require human verification.", ""]
    return "\n".join(lines), errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", help="Run directory containing scorecard_*.md and optional batch_manifest.json")
    args = parser.parse_args(argv)
    try:
        report, errors = aggregate_scores(args.run_root)
        output = Path(args.run_root) / "scores_summary.md"
        output.write_text(report, encoding="utf-8", newline="\n")
        print(f"Score summary saved: {output}")
        if errors:
            print("AGGREGATION HAS STRUCTURAL ERRORS: " + "; ".join(errors), file=sys.stderr)
        return 2 if errors else 0
    except (ValueError, OSError) as exc:
        print(f"AGGREGATION REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
