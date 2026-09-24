# Broadbridge Oil and Gas domain pack

The [canonical infrastructure brief](../../output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md) defines core v0. The [first-case runbook](../../docs/FIRST_CASE_RUNBOOK.md) implements S0-cases: capture export, import, stock Qwen through the tunnel and reviewer scorecard, with a complete offline SYN-001 rehearsal.

The pack was scaffolded from slm-foundry/packs/_template. Broadbridge4096 owns its domain schemas, prompts, rubrics, manifests and configs. Foundry owns the generic engine and accepts this pack through an absolute external --pack path. Relative asset/config paths and default outputs resolve inside the domain pack. Real records, gold answers and private run outputs are not repository fixtures.

## Primary intake and Gate 0

Bill Hurt fills the Broadbridge Case Capture web page directly, for as many cases as he chooses, without a call first. The page export is primary and canonical. Pilot case records live in the Claude artifact store (cases collection, workflow/main for Part A). Originals and any supporting documents live in the one approved S3 bucket. Brad records the exact artifact identifier, bucket/prefix and source rights; no new bucket is provisioned by these scripts.

Bill is the named technical reviewer, completing that Gate 0 requirement. Gate 0 remains open until rights/storage are recorded and signed cases supply at least 30 Section C questions with reference answers covering brief, missing_data, calculation, grounded_explanation and abstention. Questions are derived from the cases' questions arrays, not supplied separately. Accept the brief schema and scoring criteria with Bill before using results as benchmark evidence.

## One canonical contract

Use only broadbridge.case_record/1, validated by schemas/case_record.schema.json and schemas/export.schema.json (Draft 2020-12). The export wrapper is exported_at, workflow {schema, answers {A1..A10}, updated_at}, and cases[]. The retired form schema and its two schema files are removed; importer, run_brief and score_brief accept canonical case records only.

The same field names, containers and enums apply to both page and fallback intake:

- Status: draft, complete or signed.
- Record type: real_event, reconstructed or hypothetical.
- Permitted use: training, testing_only or reference_only. The page defaults new cases to training, but imports still require the field explicitly.
- Question type: brief, missing_data, calculation, grounded_explanation or abstention.
- Question split: train, dev or locked_test.
- evidence_ids, reference_answer, tolerance and hard_fail_criteria are strings. The last is preserved verbatim, never converted to an array.
- Decision-time observations and hindsight hypotheses are arrays. Evidence is the canonical top-level evidence array. Signoff has signed, name and date.

Unknown is ordinary narrative text where a string is allowed. It is not an enum escape. Missing permissions and legacy undecided values reject the whole export; no importer silently fills the page default. The canonical evidence available_at_decision_time currently accepts text or Boolean pending a populated page export confirming its widget representation.

## Import the complete page export

From the Broadbridge4096 root:

```powershell
python -m pip install -r packs/oil-gas/requirements-first-case.txt
python packs/oil-gas/scripts/validate_cases.py output/expert-capture/SYN-001.case_record.json
python packs/oil-gas/scripts/import_cases.py output/expert-capture/case_capture_export.example.json tmp/capture-example
python packs/oil-gas/run_brief.py tmp/capture-example/data/cases/SYN-001.json --dry-run
```

Use a fresh output directory for each complete export, including all related families. Original case objects remain unchanged; they contain hindsight and gold answers and are not a retrieval index. The snapshot contains:

```text
data/cases/<case_id>.json
data/train_candidates.jsonl
eval/questions.jsonl
workflow.json
import_report.json
```

The importer prints every case's disposition and records source hash, counts and family splits. Schema errors, unsafe/duplicate case IDs or duplicate question IDs reject the whole export before publishing. For schema-valid cases, incomplete signed signoff is an individual rejection; admitted cases may still be written, with CLI exit 2. Exit 0 means no rejected cases.

| Disposition | Rule |
| --- | --- |
| imported | Signed, permitted_use=training, complete named/dated signoff and family split=train. |
| eval-only | Unsigned cases, testing_only/reference_only records, or signed/training cases held out by their family split. |
| rejected | Signed status conflicts with false/blank reviewer signoff. |

Family precedence is locked_test > dev > train, calculated across all questions, including rejected family members. Derived question rows preserve requested_split and carry the effective split, case_id, family_id, permitted_use, status and original question fields. An unsigned case defaulted to training never creates training candidates. SYN-001 remains draft/reference_only and eval-only, not a training example.

Candidates are review material, not automatic training approval. The input uses decision-time context and the question; the assistant target is the reference answer. Keep benchmark families out of training. During reviewed materialization, map capture dev to Foundry val and locked_test to test without repartitioning. Use --group-key family_id for capture-derived families where preparing new splits. Never combine snapshots with inconsistent family assignments.

## DOCX fallback when a reviewer cannot use the page

The Interview Guide is a pre-read and optional call script. The fallback parser is scripts/case_from_form_fallback.py. It follows the guide's labels, supports one case per DOCX and emits the same canonical contract, not a separate form schema. The original guide and filled document remain unchanged.

Supply reviewed --case-id and --family-id (the guide has no family box). The case ID must match a populated guide ID. Use --base-export with the complete current page export so existing families and workflow answers are preserved; duplicate IDs, conflicting Part A answers and invalid records stop the merge. Use --standalone-family only when the operator can attest there are no related records outside this case. The flag is not a substitute for checking family membership.

```powershell
python packs/oil-gas/scripts/case_from_form_fallback.py filled-guide.docx tmp/fallback-review --case-id CASE-001 --family-id FAMILY-001 --base-export complete-page-export.json
# After the reviewer approves the written case, use a fresh output directory:
python packs/oil-gas/scripts/case_from_form_fallback.py filled-guide.docx tmp/fallback-signed --case-id CASE-001 --family-id FAMILY-001 --base-export complete-page-export.json --case-signed-off
python packs/oil-gas/scripts/import_cases.py tmp/fallback-signed/capture_export.json tmp/fallback-import
python packs/oil-gas/run_brief.py tmp/fallback-import/data/cases/CASE-001.json --dry-run --require-signed
```

Outputs are case_record.json, capture_export.json and form_review.json. Draft is the default. Blank narrative boxes remain schema-compatible empty strings with review flags; blank/unknown enum choices require correction before any canonical output is published. Spare rows are reported as unused. Canonical observation/hypothesis names and string question fields match the page exactly.

Reviewer signature text of Name / YYYY-MM-DD maps to name/date. If it cannot be parsed, supply both --reviewer-name and --reviewer-date YYYY-MM-DD explicitly after verifying the signature. --case-signed-off attests approval of the written case; Part D consent alone is insufficient. It refuses unanswered required boxes. Typed names are not authenticated signatures. created_at/updated_at record fallback capture time, not the historical event date. Source hash, consent, workflow and mapping details belong in form_review.json, outside the canonical case. Keep that report with approved source records.

A synthetic example needs no page or EC2:

```powershell
python packs/oil-gas/scripts/case_from_form_fallback.py packs/oil-gas/tests/fixtures/Synthetic_Filled_Interview_Guide.docx tmp/fallback-demo --case-id FORM-SYN-001 --family-id FORM-FAMILY-001 --standalone-family --case-signed-off
python packs/oil-gas/scripts/import_cases.py tmp/fallback-demo/capture_export.json tmp/fallback-demo-import
python packs/oil-gas/run_brief.py tmp/fallback-demo-import/data/cases/FORM-SYN-001.json --dry-run
```

## Brief isolation and two baseline stages

run_brief.py --dry-run prints messages locally without importing the Foundry client. Its case input is identity.unit_service plus decision_time only, with a fixed system instruction. Hindsight, question/reference answers, evidence inventory, workflow and consent are excluded. Runtime assertions verify the exact projection and block nonempty retrospective/reference strings, including JSON-escaped text. The literal unknown marker carries no retrospective fact and is handled consistently for canonical records. Actual overlaps still require source review; paraphrased hindsight needs human detection. The guard remains effective under python -O.

S0-cases is runnable per signed, permissioned case with no documents or index. The CLI uses --foundry /absolute/slm-foundry (or SLM_FOUNDRY_PATH), explicit loopback OLLAMA_URL, think=False and --schema brief passed to the shared client's schema= argument. Returned JSON is validated. --output <new-file> saves a bound brief_run.json record. --mock-response <brief.json> is an explicitly labelled offline replay.

scripts/score_brief.py <case> <brief_run> <eval-dir> generates an unscored scorecard_<case_id>.md, refusing overwrite. Bill fills 0/1/2 scores and critical-error flags against exact hard-fail criteria. The [SYN-001 example](../../eval/scorecard_SYN-001.md) is MOCK/UNREVIEWED.

S0-retrieval follows after about 20 documents are admitted and indexed on the existing box. It must use the same case-derived questions and scorecard, and improve over S0-cases without new critical errors before training is considered. The retrieval runner and its added evidence/prompt provenance are V04R work; the delivered case-only runner is not a retrieval implementation. Later base-versus-adapter comparisons must also match templates and settings.

## Offline validation

```powershell
python -m pytest packs/oil-gas/tests -q -p no:cacheprovider --basetemp <fresh-temporary-directory>
```

Tests cover canonical page/fallback validation, family holdouts, signoff, missing boxes, enum errors, prompt leakage and mock first-case scoring. Tools neither start EC2 nor configure its tunnel. No PermitHub PIFR/A22 or NeonDB integration is included.
