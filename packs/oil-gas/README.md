# Broadbridge Oil and Gas domain pack

For the first signed case from the capture page, follow
[FIRST_CASE_RUNBOOK.md](../../docs/FIRST_CASE_RUNBOOK.md). It covers export,
import, stock Qwen through the tunnel, a schema-validated brief and a reviewer
scorecard. The offline SYN-001 rehearsal uses a mocked response and no EC2.

Scaffolded by copying slm-foundry/packs/_template, then replacing its example
identity and adding proposed configs/train.yaml, schemas/answer.schema.json,
prompts/system.txt and rubrics/engineering-v0.md. Gate 0 remains open in pack.yaml.
These drafts grant no source permissions or technical acceptance. Do not put
Broadbridge domain assets in slm-foundry.

From the Foundry root, use python -m src.train --pack /absolute/domain/pack
--dry-run --tokenizer-dir /local/tokenizer. Preparation and evaluation accept
the same --pack directory or pack.yaml path. Relative asset/config paths resolve
from the pack root; output_dir defaults to outputs/<name> under that pack.

This pack includes synthetic DOCX and Case Capture JSON fixtures and offline intake tools.
It has no approved production corpus, benchmark or reviewer appointment.
Gate 0 remains open. See the canonical brief under output/foundry-infrastructure
for the v0 sequence and Post-v0 roadmap.

## Interview Guide DOCX intake

The current form workflow is Meet/Otter transcript, then Brad fills the
Interview Guide, then Bill reviews and signs off the written case. The latest
request reinstates DOCX parsing. It runs entirely inside Broadbridge4096;
there is no PermitHub PIFR/A22 or NeonDB integration. Only the sequence of
fixed questions, schema, pending review and sign-off is mirrored.

`schemas/case_record.json` and `schemas/eval_question.json` are Draft 2020-12
schemas for `broadbridge.case_form/1`. They map every identity-grid answer and
B1-B14: B1-B6 are in decision_time; B7-B13 are in hindsight; b14_evidence is a
separate array. B4 observation and B7 hypothesis rows are arrays. Part C uses
evidence_ids and hard_fail_criteria arrays. Enter one hard-fail criterion per
Word paragraph; evidence IDs may be separated by commas or line breaks.

Use one case per DOCX, with the supplied labels and answer tables intact.
The parser follows labels rather than fixed table numbers. Duplicated sections,
changed columns, unmapped tables and unknown choices are refused. It reads
typed table text; handwritten/image signatures require manual verification and
will not be invented by OCR. It never reads the transcript automatically.

An explicitly entered `unknown` is legal for every captured scalar, including
enumerated answers; containers remain objects/arrays. Empty boxes become null
or empty arrays and appear in form_review.json. Entirely blank spare rows or
question blocks are listed separately as unused. Unknown is not a retrospective
fact, so its shared occurrence does not trigger the form prompt leak guard.

From the repository root:

```powershell
python packs/oil-gas/scripts/case_from_form.py filled-guide.docx tmp/form-review --family-id FAMILY-001
# After Bill approves the written case, use a new output folder:
python packs/oil-gas/scripts/case_from_form.py filled-guide.docx tmp/form-approved --family-id FAMILY-001 --case-signed-off
python packs/oil-gas/run_brief.py tmp/form-approved/case_record.json --dry-run
```

The guide contains no family-ID box, so supply a reviewed --family-id; the parser
does not guess family membership from the case ID. Parsing defaults to
pending_review. Part D records recording/review consent, not explicit case
acceptance. --case-signed-off records the operator's attestation that Bill
approved this written case; it requires no unanswered boxes and known case ID,
family, reviewer signature and permitted use. It does not authenticate a typed
signature or establish source rights. The unsigned original is never changed.

Outputs are case_record.json, eval_questions.json and form_review.json. The
record also contains the same Part C questions so the direct brief runner can
guard reference answers without loading another file. Part A and consent are
retained in the review report. No workflow, consent, B14, hindsight or question
content is included in a brief prompt. The guide's introductory sentence
confuses Parts A/B with decision-time/hindsight; the harness follows the
explicit B1-B6 and B7-B13 item labels.

The existing JSON-page format remains separate and unchanged: it uses
broadbridge.case_record/1 with string hard_fail_criteria. Do not silently cast
between formats or feed form records into import_cases.py. The validator and
brief runner accept either case version. Form outputs are review/scoring
records, not automatic training admission. Holdout families and permissions
must remain enforced when approved records are later materialized.

## Case Capture JSON intake

The existing database-backed Broadbridge Case Capture page can also produce
**All records as JSON**. The live page contract is
`broadbridge.case_record/1`; Part A is `workflow/main`, exported as
`workflow {schema, answers {A1..A10}, updated_at}`. That page contract is retained
for compatibility alongside the newly reinstated form intake described above.

The two Draft 2020-12 schemas preserve the live field names, enums and string
types, including `evidence_ids`, `tolerance` and `hard_fail_criteria`. Empty Part A
answers and draft signoff strings validate structurally. Unknown fields fail.
The page's permitted-use enum is `training | testing_only | reference_only`;
new cases default to `training`. That page default does not approve a case:
training candidates still require signed status, complete reviewer signoff,
training permission and a train-family split. The schema default is an annotation;
the importer never fills a missing permission. Legacy `undecided` values now
fail schema validation and reject the whole export before any output is written.
Resolve those values on the page and re-export; do not silently convert them.
The seeded record has no evidence items; `available_at_decision_time` currently
accepts text or a Boolean so either page widget representation is preserved.
Verify that one type against a populated live export before tightening it.

From the Broadbridge4096 repository root:

```powershell
python -m pip install -r packs/oil-gas/requirements-capture.txt
python packs/oil-gas/scripts/validate_cases.py output/expert-capture/SYN-001.case_record.json
python packs/oil-gas/scripts/import_cases.py output/expert-capture/case_capture_export.example.json tmp/capture-example
python packs/oil-gas/run_brief.py output/expert-capture/SYN-001.case_record.json --dry-run
python -m pytest packs/oil-gas/tests -q
```

Use a **new or empty** `out_dir` for each complete export. Each snapshot contains:

```text
data/cases/<case_id>.json
data/train_candidates.jsonl
eval/questions.jsonl
workflow.json
import_report.json
```

Original case objects remain unchanged. `data/cases` is a restricted archive,
not a retrieval index or training input: it includes hindsight and gold answers.
Part A is preserved separately and never sent to the model. The importer prints
a disposition for every case and records counts, source hash and family splits.
Malformed schemas, unsafe/duplicate case IDs or duplicate question IDs reject
the entire export before writing a snapshot. This avoids silently dropping a
holdout family member. The CLI explains the failure and exits 2. Permission
rejections are listed individually; admitted records are still written, and the
CLI exits 2 when any case was rejected. Exit 0 means no rejections.

| Disposition | Rule |
| --- | --- |
| imported | Signed, permitted_use=training, complete reviewer signoff, family split=train. |
| eval-only | Draft/complete records or testing_only/reference_only; also signed training records held out by their family split. |
| rejected | Signed status with a false/blank reviewer signoff in an otherwise schema-valid case. |

This follows the latest capture instruction: **SYN-001 is eval-only**, despite
being draft/reference_only. It must never enter training candidates. Eval-only
records are provisional evaluation material; their presence is not benchmark
acceptance, a training grant, or approval for external transmission.

Family precedence is `locked_test > dev > train`, computed over every question
in the complete export, including permission-rejected records. Derived rows
carry the effective `split`, original `requested_split`, `case_id`, `family_id`,
`status` and `permitted_use`, plus every original question field. Families are
matched by their exact stored ID. Do not import partial families or combine
snapshots: re-export all records when a family or permission changes.

Only signed/training cases in train families create candidates. Candidates have
Foundry-style `messages` with question plus decision-time context as input and
the reference answer as the supervised target. These are review candidates,
not automatically approved training records. No config is repointed to them.
Keep dev/locked_test families out of training. During a separately reviewed
materialization step, map capture `dev` to Foundry `val` and `locked_test` to
Foundry `test`; preserve `family_id` and use `--group-key family_id` if preparing
new splits. Do not randomly repartition a frozen capture benchmark. Free-text
tolerances, evidence IDs and hard-fail criteria require reviewer interpretation
before they become executable engineering metrics.

## Brief prompt isolation

`run_brief.py --dry-run` prints the exact messages locally and never imports the
Foundry client or calls a model. Case content is limited to `identity.unit_service`
and `decision_time`. A static system instruction describes the brief task.
The runtime guard verifies the complete envelope and projection, then refuses
any nonempty string from `hindsight.*` or `questions[].reference_answer` found
in the prompt or selected raw values. Checking raw values also covers JSON
escaping. Explicit AssertionError checks remain active under `python -O`.
Empty strings are ignored because they match every prompt. Exact overlaps,
even legitimate short strings, fail closed and need human case review; the
guard cannot detect paraphrased retrospective knowledge.

Authorized inference uses `--foundry /absolute/slm-foundry` (or
SLM_FOUNDRY_PATH), its shared requests client and explicitly configured loopback
OLLAMA_URL. The CLI now requires a signed case for live inference, passes
think=False and the `--schema brief` JSON Schema to the client, and validates
the returned JSON. `--output <new-file>` saves a brief_run.json audit envelope.
`--mock-response <brief.json>` replays a local response through the same guards
and labels the result MOCK. `scripts/score_brief.py <case> <brief_run> <eval-dir>`
generates an unscored reviewer sheet and refuses to overwrite one. The script
never starts EC2, opens a tunnel, or changes the security group.
