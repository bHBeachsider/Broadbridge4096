# Bill's engineering training questionnaire

Updated 30 September 2026. **Send Bill the [live questionnaire](https://broadbridge-capture.vercel.app/questionnaires/pressure-training-v1).** It has 16 questions in five categories and eight worked examples, focused on shaping the first DOE pressure demonstration. It uses the existing sign-in and saves versioned responses to the dedicated Broadbridge database. The files in this folder preserve the earlier **local draft**; the local-storage instructions below apply only to that draft.

## Open the draft

From this checkout, run:

```powershell
python -m http.server 8774 --bind 127.0.0.1 --directory docs/questionnaires/pressure-training-v1
```

Open [the local questionnaire](http://127.0.0.1:8774/). This address works only on the computer running the server; it is not the URL to email Bill. The server exposes only this draft folder. Stop that server with Ctrl+C when finished.

The complete text is in [QUESTIONS.md](QUESTIONS.md); [questionnaire.json](questionnaire.json) supplies the page content. The page uses inline SVG graphics and system fonts, with no external scripts or automatic external requests.

## What Bill reviews

| Category | Questions | Purpose |
| --- | ---: | --- |
| Where this would help | 3 | Choose a real task, useful output and practical priority |
| Numbers and pressure references | 3 | Review gauge, absolute and vacuum examples with explanatory graphics |
| Missing facts and judgment | 5 | Refine when to ask for evidence, correct a premise or withhold a conclusion |
| Exceptions, sources and Norm | 3 | Find unusual cases, nominate material and focus expert involvement |
| Your recommendation | 2 | Define acceptance criteria and capture issues the questions missed |

For each example, read the source notes and record the required answer before revealing the draft reference. Classify the reference, record corrections, flag potentially serious errors and identify essential checks. Use the task-selection field to include, revise or exclude a task. Suggested completion times are estimates, not measured interview durations.

The hydrostatic-depth example tests the boundary of this pressure recipe. Assess its relevance and propose a replacement if another petrochemical task would be more useful.

## Saving and interpreting responses

The preview autosaves after 1.2 seconds to local browser storage and offers a JSON download. It has no authentication, database writes, recording feature or server submission. Text and pasted transcripts are supported. The clear button removes only this questionnaire's local draft. Use Download responses before moving between browsers or computers.

Exports use `broadbridge.training_review_response_draft/1`, with questionnaire ID/version, the source-package manifest hash, original question IDs, optional reviewer name, answers, timestamps and whether a reference answer was revealed. An entered name is **not verified identity**. The export explicitly records `authenticated_reviewer: false`, `training_approved: false` and `rights_status: TBD`. These are draft comments, not Bill's sign-off, a model score or a source-use grant.

| Feedback | How it will be used |
| --- | --- |
| Task priorities and useful outputs | Choose the initial model behavior and training scope |
| Corrected reference answers and assumptions | Revise teaching examples while retaining earlier versions |
| Essential checks and serious errors | Refine the scoring rubric and acceptance criteria |
| Rare cases or unusual exceptions | Invite a canonical case record; keep initial evidence separate from hindsight |
| Norm suggestions | Prepare a focused interview/review agenda |
| Supporting material | Add nominations to the source register for separate rights review |
| Free-form notes/transcripts | Propose themes for the contributor to confirm; retain the original wording |

Nothing in this flow automatically admits material to a training batch. Same-family demonstration examples remain unsuitable as an independent generalization test.

## Connection to the existing application

The authenticated route `/questionnaires/pressure-training-v1` is live in the existing capture app. [Draft PR #26](https://github.com/bHBeachsider/Broadbridge4096/pull/26), commit `fe1c70e`, contains the deployed implementation and release evidence. It uses the existing email allowlist and dedicated Broadbridge database, with versioned responses attributed to the signed-in reviewer. Its contract is `broadbridge.training_questionnaire_response/1`, separate from the local draft export above and from model scores. The capture home page links to **Engineering training review**.

The `discovery_links` values remain proposed cross-references to the separate engineering-discovery questionnaire, not writes to it. Actual cases retain the existing `broadbridge.case_record/1` contract. Voice intake can later attach a reviewed transcript through the separate speech/interviewer workflow. Do not regenerate or replace the deployed version's content without versioning it; the production packet is immutable and checksum-bound.

## Regenerate the text and content

From this checkout, with the prepared local pressure-demo package present:

```powershell
python scripts/research/draft_bill_training_questionnaire.py
```

The generator verifies both input JSONL files against the demo manifest, preserves all eight original probe IDs and writes `questionnaire.json` and `QUESTIONS.md`. The HTML is maintained separately. Content changes should increment the questionnaire version once responses are collected; do not reinterpret an earlier response against a changed reference.

The eight references are authored expectations from the prepared package, **not generated Qwen answers**. The numbers, source notes, tolerances and critical-error rules remain available for Bill to challenge. See [the training demonstration brief](../../BILL_QWEN_TRAINING_DEMO.md) for scope and [the package runbook](../../DOE_TRAINING_DEMO_PACKAGE.md) for the pending training release decisions.

## Local verification

On 30 September, six browser smoke-check groups passed: content counts; autosave/reload; answer-reveal tracking without falsely incrementing response progress; JSON export and approval flags; negative-gauge graphic and mobile fit across all categories; and clear-draft behavior with no page errors or automatic external requests. Desktop light and mobile dark screenshots were visually inspected. The first smoke attempt missed opening the optional rubric disclosure; the corrected browser sequence passed. This was a local UI check, not an authenticated deployment or engineering validation.

Ignored screenshots and the smoke receipt are in `packs/oil-gas/outputs/questionnaire-review/`. No Bill responses, database writes, model calls or training runs were involved.
