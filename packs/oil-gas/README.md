# Broadbridge Oil and Gas domain pack

Scaffolded by copying slm-foundry/packs/_template, then replacing its example
identity and adding proposed configs/train.yaml, schemas/answer.schema.json,
prompts/system.txt and rubrics/engineering-v0.md. Gate 0 remains open in pack.yaml.
These drafts grant no source permissions or technical acceptance. Do not put
Broadbridge domain assets in slm-foundry.

From the Foundry root, use python -m src.train --pack /absolute/domain/pack
--dry-run --tokenizer-dir /local/tokenizer. Preparation and evaluation accept
the same --pack directory or pack.yaml path. Relative asset/config paths resolve
from the pack root; output_dir defaults to outputs/<name> under that pack.

This pack includes synthetic Case Capture fixtures and offline intake tools.
It has no approved production corpus, benchmark or reviewer appointment.
Gate 0 remains open. See the canonical brief under output/foundry-infrastructure
for the v0 sequence and Post-v0 roadmap.

## Case Capture JSON intake

Bill Hurt enters cases directly in the database-backed Broadbridge Case Capture
page. Brad exports **All records as JSON**. The live page contract is
`broadbridge.case_record/1`; Part A is `workflow/main`, exported as
`workflow {schema, answers {A1..A10}, updated_at}`. The Interview Guide DOCX is
only a pre-read and call script. The DOCX parser task is cancelled; do not build
or run `scripts/case_from_form.py`.

The two Draft 2020-12 schemas preserve the live field names, enums and string
types, including `evidence_ids`, `tolerance` and `hard_fail_criteria`. Empty Part A
answers and draft signoff strings validate structurally. Unknown fields fail.
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
| rejected | permitted_use=undecided, or signed status with a false/blank reviewer signoff. |

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

Future authorized inference uses `--foundry /absolute/slm-foundry` (or
SLM_FOUNDRY_PATH), its shared requests client and explicitly configured loopback
OLLAMA_URL. It passes think=False. The script never starts EC2, opens a tunnel,
or changes the security group. This task only exercises local dry runs and
mocked model boundaries.
