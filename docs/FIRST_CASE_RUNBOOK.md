# First signed case: export, brief and reviewer scorecard

Owner: Brad / Broadbridge Oil & Gas. Technical acceptance: Bill Hurt, the named Broadbridge reviewer. Updated 26 September 2026.

Bill enters as many cases as he chooses directly in [Broadbridge Case Capture](https://broadbridge-capture.vercel.app), without a call first, and signs off the written records. Brad exports **All records as JSON**. The page and its `broadbridge.case_record/1` export are the primary, canonical intake. The Interview Guide is a pre-read/call script; `case_from_form_fallback.py` is available for a reviewer who cannot use the page and emits the same contract. The dedicated Broadbridge Neon project stores case records and workflow answers. Originals/supporting documents use the approved private R2 storage and source-admission process; an evidence description in a case is not an attachment upload or rights grant. Preserve the old Claude export for migration reconciliation under the [cutover procedure](CAPTURE_APP.md). Domain tooling and restricted working snapshots belong to Broadbridge4096; the shared client stays in slm-foundry.

Bill first uses **A · Your workflow**, including A8, to identify priority areas and tasks. See [Bill's starting guide](BILL_START_HERE.md). Those answers guide case selection and the proposed synthetic curriculum; they do not become model input or automatically approve a training recipe.

The result is one structured stock-model brief and an **unscored** `eval/scorecard_<case_id>.md` for a human reviewer. The model receives only `identity.unit_service` and `decision_time`, with a fixed system instruction and the brief output schema. Questions, reference answers, hindsight, workflow and evidence attachments are not sent to it.

This is **S0-cases**, the first baseline stage, runnable per signed case with no documents or index. **S0-retrieval** follows after approximately 20 documents are admitted; it must beat S0-cases on the same case-derived questions and scorecard without new critical errors before training is considered. Use the stock Ollama Qwen3 template with `think:false` and matching inference settings for both. Later base-versus-adapter comparisons still require matched templates and settings.

Gate 0 closes when rights/storage are recorded, Bill Hurt is named as reviewer (done), and signed cases supply at least 30 Section C questions with reference answers covering all five types. Questions come from cases. Per-case runs can proceed after their rights/storage and signoff are recorded while coverage accumulates; a single run does not close Gate 0.

## 1. Before the signed case arrives (no GPU)

Read the adjacent Foundry repository's [serving brief](../../slm-foundry/docs/SLM_SERVING_BRIEF.md). Its verified instance is `i-0e5e1cbc7b1367566` in `us-east-1`. It already has stock `qwen3:8b` and an auto-starting Ollama service. No model download, training bootstrap or S3 profile is required for this inference-only exercise.

Use PowerShell. Set up the local Python environment once; no model packages are needed. The paths below match Brad's machine. A second operator changes only these local paths and their authorized SSH key location.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Users\bradu\Documents\Broadbridge4096'
$Foundry = 'C:\Users\bradu\Documents\slm-foundry'
$Pack = Join-Path $Repo 'packs\oil-gas'
Set-Location $Repo
& 'C:\Python313\python.exe' -m venv "$Repo\venv\first-case"
if ($LASTEXITCODE -ne 0) { throw 'Local venv creation failed' }
$Python = "$Repo\venv\first-case\Scripts\python.exe"
& $Python -m pip install -r "$Pack\requirements-first-case.txt"
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
```

On later days, set `$Repo`, `$Foundry`, `$Pack`, `$Python` and `$ErrorActionPreference` again in Terminal A; skip installation if this environment is already ready. Keep the two repositories' revisions with the run. AWS CLI credentials, SSH access and the named reviewer must already be available.

## 2. Recommended command for one case or a batch

Use `scripts/first_case.ps1` when signed cases arrive together. It imports the complete export once and checks every selected case before starting the existing box. `-CaseId` accepts a single ID, a quoted comma list, a PowerShell string array, or `all-signed`. `all-signed` selects signed cases only, including signed testing-only/reference-only cases; unsigned records are never selected automatically. No question set, document index or training host setup is needed.

Before running live, Brad checks rights/storage, reviewer signoff, the selected cases' decision-time text and context length as described below. Every selected case must pass signoff, schema and prompt-leak preflight. Any importer rejection stops the batch, including a rejected family member outside the selection. An explicit bad/duplicate ID, an empty selection or a selected unsigned case also stops before AWS. The SSH key and current host key must already be trusted; first-time/changed-host-key verification remains a manual operator step. Port 11434 remains closed.

After setting the local variables in section 1, use **either this command or the manual sections 3–7**, not both:

```powershell
$Export = Read-Host 'Full path to the complete All records as JSON export'
$RunId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$Run = Join-Path $Pack "outputs\first-case\$RunId"
# Replace all-signed with an explicit list such as 'CASE-001,CASE-002' if needed.
& "$Repo\scripts\first_case.ps1" -Export $Export -CaseId 'all-signed' -RunRoot $Run -Python $Python -Foundry $Foundry
if ($LASTEXITCODE -ne 0) { throw 'Batch needs attention; inspect the printed run root and teardown status' }
```

Each invocation creates a fresh ignored `packs/oil-gas/outputs/first-case/<run_id>/`. `-RunRoot <fresh-path>` overrides that location. The live path requires the box to be stopped and local port 11435 free, then starts EC2 once, discovers its current IP, opens one hidden SSH tunnel and saves the stock model digest/template once. The N briefs use the shared client with `think:false`, temperature 0.2 and `schema=brief`. The script stops EC2 once in `finally`, confirms stopped, and closes its own tunnel. No key checks are bypassed and no models are downloaded.

Each valid response yields `cases/<case_id>/brief_run.json` and `eval/scorecard_<case_id>.md`. `batch_summary.md` prints **case_id, status, brief valid y/n, elapsed**; `batch_results.json` retains error details. One failed case does not discard successful cases or prevent later cases from running. Failed responses cannot receive a valid scorecard; they remain visible in the summary and count as unreviewed. No automatic retries or overwriting: retry explicitly in a fresh run. A session failure before inference leaves the selected cases as `not-run`. `session_error.txt`/`teardown_error.txt` record failures; absence of `instance_stopped.txt` after a start requires operator attention and the recovery block in section 6. Abrupt process termination or loss of power still requires manual teardown.

The run also retains `batch_manifest.json`, both repository revisions (Broadbridge only for mock runs), the full family-aware import, and live-only model/session records. All review occurs after shutdown. A valid brief is only a schema result, not engineering acceptance.

## 3. Manual alternative: export and import (Terminal A, no GPU)

Brad confirms the written case is signed, its permitted use covers this internal exercise, the export/storage location is approved, and the reviewer and brief schema are agreed. A typed signature is not automatically authenticated by these scripts. Resolve missing reference answers, evidence IDs, tolerance for numerical questions and hard-fail criteria with the reviewer before scoring. If the rest of Gate 0 remains open, record that fact rather than declaring the full benchmark ready.

Export **all records**, including related families. Save the JSON in the approved local intake folder. Do not assemble a partial export, silently change a split, or paste the full case into a model. The importer archives hindsight/reference answers for review and separately derives family-aware question rows and training candidates. This runbook never consumes those training candidates.

```powershell
$Export = Read-Host 'Full path to All records as JSON export'
$CaseId = Read-Host 'Signed case_id to run'
if ($CaseId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$') { throw 'Invalid case_id' }
if (-not (Test-Path -LiteralPath $Export -PathType Leaf)) { throw 'Export not found' }
$RunId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$Run = Join-Path $Pack "outputs\first-case\$RunId"
& $Python "$Pack\scripts\import_cases.py" $Export $Run
if ($LASTEXITCODE -ne 0) { throw 'Review importer rejection(s); resolve and re-export before continuing' }
$Case = Join-Path $Run "data\cases\$CaseId.json"
if (-not (Test-Path -LiteralPath $Case -PathType Leaf)) { throw 'Chosen case was not admitted' }
Get-Content -LiteralPath "$Run\import_report.json"
& $Python "$Pack\run_brief.py" $Case --dry-run --require-signed --schema brief
if ($LASTEXITCODE -ne 0) { throw 'Signoff/schema/prompt-leak preflight failed; review before starting EC2' }
git -C $Repo rev-parse HEAD | Set-Content -LiteralPath "$Run\broadbridge_revision.txt"
if ($LASTEXITCODE -ne 0) { throw 'Cannot record Broadbridge revision' }
git -C $Foundry rev-parse HEAD | Set-Content -LiteralPath "$Run\foundry_revision.txt"
if ($LASTEXITCODE -ne 0) { throw 'Cannot record Foundry revision' }
```

Review the printed prompt: it must contain only information actually available at decision time. The runtime assertion catches exact hindsight/reference-answer strings, including JSON-escaped text, but cannot detect paraphrased hindsight. A legitimate exact overlap also blocks the run; resolve it through reviewed source correction, not by disabling the guard.

The page defaults new cases to `permitted_use=training`; unsigned cases still import as **eval-only** and never become training candidates. Import success alone is insufficient. The first live brief command enforces signed status, complete named/dated signoff, a permitted-use value of `training`, `testing_only` or `reference_only`, and at least one question. Missing permissions and legacy `undecided` values fail schema validation: the entire export is rejected before any snapshot is written. The importer never supplies the page default for an omitted field. For schema-valid cases with inconsistent signoff, individual rejections produce exit 2 and other admitted cases may be written, but this runbook still stops for review. Correct the capture-page record and re-export into a fresh run directory.

`locked_test > dev > train` applies to the entire family. The case archive preserves the original question split; `eval/questions.jsonl` and `import_report.json` hold the **effective family split**. Never tune on a locked-test answer or merge snapshots with different family assignments. Real run outputs are under the already ignored `packs/oil-gas/outputs/` directory.

## 4. Manual alternative: start EC2 and open the tunnel (Terminal B)

These are the serving brief's instance, region, port mapping and key. The fresh IP is obtained directly from EC2. This replaces `infra/status.ps1` here because that helper also uses the saved SSH alias and probes unrelated training/S3 state.

Run the following in a **second PowerShell window**. If bring-up fails after the instance starts, run the teardown block in section 6 before leaving. Check SSH host-key prompts normally; do not disable host-key verification.

```powershell
$ErrorActionPreference = 'Stop'
$Instance = 'i-0e5e1cbc7b1367566'
$Region = 'us-east-1'
$Key = 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem'
aws ec2 start-instances --region $Region --instance-ids $Instance
if ($LASTEXITCODE -ne 0) { throw 'EC2 start failed' }
aws ec2 wait instance-running --region $Region --instance-ids $Instance
if ($LASTEXITCODE -ne 0) { throw 'EC2 did not reach running; perform teardown' }
aws ec2 wait instance-status-ok --region $Region --instance-ids $Instance
if ($LASTEXITCODE -ne 0) { throw 'EC2 health check failed; perform teardown' }
$PublicIp = aws ec2 describe-instances --region $Region --instance-ids $Instance --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PublicIp) -or $PublicIp -eq 'None') { throw 'No current public IP; perform teardown' }
ssh -i $Key -o ExitOnForwardFailure=yes -N -L 11435:localhost:11434 "ec2-user@$($PublicIp.Trim())"
```

Keep Terminal B open while Terminal A calls the model. If Brad's home IP changed, an authorized operator updates **SSH port 22** in `slm-foundry-sg` (`sg-00c7894c78785b6c3`) to the current home IP/32. Keep port **11434 closed** in the security group. Windows Ollama on local port 11434 is not the remote model and must not be used.

## 5. Manual alternative: generate the stock brief (Terminal A)

The brief runner loads `schemas/brief.schema.json` and calls the shared client with `schema=<that JSON Schema object>`, `think=False`, `temperature=0.2`. The client sends POST `/api/chat`, `stream:false`, and the schema in Ollama's `format` field. The local validator rejects malformed JSON, duplicate keys, non-JSON numeric values and schema violations before publishing `brief_run.json`.

```powershell
$env:OLLAMA_URL = 'http://localhost:11435'
$env:OLLAMA_MODEL = 'qwen3:8b'
try {
    $Tags = Invoke-RestMethod -Uri "$env:OLLAMA_URL/api/tags" -Method Get -TimeoutSec 15
    if (-not ($Tags.models | Where-Object { $_.name -eq 'qwen3:8b' })) { throw 'Remote qwen3:8b is missing; do not switch endpoints' }
    $ShowBody = @{ model = 'qwen3:8b' } | ConvertTo-Json
    $ModelInfo = Invoke-RestMethod -Uri "$env:OLLAMA_URL/api/show" -Method Post -ContentType 'application/json' -Body $ShowBody -TimeoutSec 15
    $Utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText("$Run\ollama_tags.json", ($Tags | ConvertTo-Json -Depth 30), $Utf8)
    [System.IO.File]::WriteAllText("$Run\ollama_model_info.json", ($ModelInfo | ConvertTo-Json -Depth 30), $Utf8)
    & $Python "$Pack\run_brief.py" $Case --foundry $Foundry --schema brief --output "$Run\brief_run.json"
    if ($LASTEXITCODE -ne 0) { throw 'Brief failed; inspect error and preserve this run directory' }
} finally {
    aws ec2 stop-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
    if ($LASTEXITCODE -ne 0) { Write-Warning 'STOP FAILED: use section 6 and confirm stopped in AWS before leaving' }
}
```

The saved tag digest and model-info/template snapshot identify the stock build; a mutable tag alone is insufficient for later reproducibility. Record any uncommitted code changes separately or run from reviewed, committed code. The run envelope binds the case, prompt and brief schema with canonical JSON hashes, labels live versus mock, records settings and elapsed time, and contains the validated draft. It is not a signed audit record or a technical correctness check.

The client timeout is 120 seconds. Cold-start latency and live schema-constrained generation have not been measured in this first-case workflow. A timeout or invalid reply fails the run; diagnose before an explicit retry in a fresh run directory. Do not repeatedly retry unattended. The serving brief reports a 4096-token default context. Review long cases against that limit before inference; this harness does not measure token counts or prove that the server avoided truncation. Do not silently trim a signed case to fit.

## 6. Confirm teardown / recovery (Terminal A)

Stop the GPU before the reviewer starts reading. This block is also the recovery path if Terminal B startup, health checks or inference failed before the `finally` block ran.

```powershell
aws ec2 stop-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
if ($LASTEXITCODE -ne 0) { throw 'Stop failed: resolve in AWS; do not leave the box running' }
aws ec2 wait instance-stopped --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
if ($LASTEXITCODE -ne 0) { throw 'Stopped state not confirmed; check AWS console' }
```

Press Ctrl+C in Terminal B if SSH has not already exited. No `bootstrap.sh`, IAM profile change, S3 transfer or deployment script is part of this run.

## 7. Generate and complete the reviewer scorecard (no GPU)

```powershell
& $Python "$Pack\scripts\score_brief.py" $Case "$Run\brief_run.json" "$Run\eval"
if ($LASTEXITCODE -ne 0) { throw 'Scorecard failed; check that case and brief come from the same run' }
$Scorecard = Join-Path $Run "eval\scorecard_$CaseId.md"
Get-Content -LiteralPath $Scorecard -Encoding UTF8
```

Open that Markdown file in an editor for the appointed reviewer. It embeds the draft, exact question/reference/tolerance/evidence fields, the capture signoff and run identity. Live-page `hard_fail_criteria` is kept as its original **string**, not split or rewritten. Each question has a 0/1/2 score, a separate critical-error flag and space for quoted evidence. Type-specific anchors cover `brief`, `missing_data`, `calculation`, `grounded_explanation` and `abstention`; absent types are N/A. No automated judge fills a score.

The reviewer checks numerical tolerance/units, claim grounding, unavailable evidence and each hard-fail criterion. Any matched hard fail gives score 0 and critical error YES regardless of other points. Unsafe or fabricated material recommendations also trigger a critical flag. Blank criteria need clarification. Required answers missing from the brief score 0; use N/A only with a documented reason that the question cannot fairly be assessed from this brief and the supplied decision-time information. The model did not see the question text, so this is an assessment of the brief as written, not a question-by-question prompted benchmark.

The sheet starts **UNREVIEWED / HOLD**. Record reviewer name/date, quotations, per-type totals, critical-error count and corrections. Do not average away a critical error. Source capture signoff is distinct from acceptance of the model's draft. Do not overwrite a completed sheet: the generator refuses existing filenames; use a fresh run for a changed case or response. Human edits to the scorecard are expected. Review records contain withheld answers and must never enter a retrieval index or subsequent model prompt.

The expected run folder is:

```text
packs/oil-gas/outputs/first-case/<run_id>/
  data/cases/<case_id>.json
  data/train_candidates.jsonl            # generated, never consumed by this runbook
  eval/questions.jsonl                  # effective family splits
  eval/scorecard_<case_id>.md             # reviewer completes
  workflow.json
  import_report.json
  broadbridge_revision.txt
  foundry_revision.txt
  ollama_tags.json                       # live only
  ollama_model_info.json                 # live only
  brief_run.json
```

## 8. Offline rehearsal on SYN-001 (no EC2, no model connection)

Use this block instead of sections 2–7. It exercises the same importer, prompt guard, structured output validation and scorecard generator. The response is a clearly labelled authored fixture; `--mock-response` never loads the Foundry client. SYN-001 stays draft/reference_only and eval-only, with zero training candidates. `--dry-run` alone only prints the prompt and does not exercise response/scoring output.

After local setup in section 1, run:

```powershell
$RunId = 'SYN-001-' + [guid]::NewGuid().ToString('N')
$Run = Join-Path $Pack "outputs\first-case\$RunId"
& $Python "$Pack\scripts\import_cases.py" "$Pack\tests\fixtures\capture_export.json" $Run
if ($LASTEXITCODE -ne 0) { throw 'Mock import failed' }
$Case = Join-Path $Run 'data\cases\SYN-001.json'
& $Python "$Pack\run_brief.py" $Case --dry-run --schema brief
if ($LASTEXITCODE -ne 0) { throw 'Mock prompt guard failed' }
& $Python "$Pack\run_brief.py" $Case --schema brief --mock-response "$Pack\tests\fixtures\SYN-001.mock_brief.json" --output "$Run\brief_run.json"
if ($LASTEXITCODE -ne 0) { throw 'Mock brief failed' }
& $Python "$Pack\scripts\score_brief.py" $Case "$Run\brief_run.json" "$Run\eval"
if ($LASTEXITCODE -ne 0) { throw 'Mock scorecard failed' }
Get-Content -LiteralPath "$Run\eval\scorecard_SYN-001.md" -Encoding UTF8
```

The tracked seed/export fixtures reproduce the page export stored under `output/expert-capture/`. The committed [example scorecard](../eval/scorecard_SYN-001.md) was generated by this offline flow. Its blank scores and UNASSESSED flags intentionally do not imply Bill has reviewed it. Its one seeded question is `missing_data`; the other four types are shown as N/A until cases actually supply those questions.

Delivery verification on 24 September 2026: the PowerShell rehearsal above completed in **1.99 seconds** using the installed `C:\Python313\python.exe` with the local capture dependencies (no dependency installation in that measurement). The importer reported **1 case, 1 question, 0 training candidates**; SYN-001 was **eval-only**. The prompt guard passed and the generated brief/scorecard were explicitly marked MOCK. No AWS or model endpoint was contacted. Repeated runs will have different timestamps and timings.

## 9. Offline three-case batch rehearsal

This combines the unmodified SYN-001 seed and the two existing SYN-TRAIN fixtures in a temporary export. SYN-001 remains draft/reference_only and eval-only. Its explicit inclusion is allowed only because this invocation uses `-MockResponse`; a live invocation would refuse it. The three cases share the same synthetic decision-time scenario, so one authored mock response is suitable for this transport rehearsal. None is a real case or a human-reviewed result.

```powershell
$FixtureDir = Join-Path $Pack 'tests\fixtures'
$RunId = 'batch-mock-' + [guid]::NewGuid().ToString('N')
$Intake = Join-Path $Repo "tmp\$RunId"
New-Item -ItemType Directory -Path $Intake | Out-Null
$Example = Get-Content -LiteralPath "$FixtureDir\capture_export.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$Example.cases = @($Example.cases) + @(
    (Get-Content -LiteralPath "$FixtureDir\SYN-TRAIN-001.json" -Raw -Encoding UTF8 | ConvertFrom-Json),
    (Get-Content -LiteralPath "$FixtureDir\SYN-TRAIN-002.json" -Raw -Encoding UTF8 | ConvertFrom-Json)
)
$Export = Join-Path $Intake 'capture_export.json'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Export, ($Example | ConvertTo-Json -Depth 100), $Utf8)
$Run = Join-Path $Pack "outputs\first-case\$RunId"
& "$Repo\scripts\first_case.ps1" -Export $Export -CaseId 'SYN-001,SYN-TRAIN-001,SYN-TRAIN-002' -RunRoot $Run -Python $Python -MockResponse "$FixtureDir\SYN-001.mock_brief.json"
if ($LASTEXITCODE -ne 0) { throw 'Offline batch failed' }
& $Python "$Repo\scripts\aggregate_scores.py" $Run
if ($LASTEXITCODE -ne 0) { throw 'Aggregate structural checks failed' }
Get-Content -LiteralPath "$Run\batch_summary.md" -Encoding UTF8
Get-Content -LiteralPath "$Run\scores_summary.md" -Encoding UTF8
```

Expected: three completed, schema-valid MOCK briefs, three UNREVIEWED scorecards, zero reviewed / three unreviewed cases, no live means. The importer derives two synthetic training candidates; this workflow never reads or trains on them. A separate mock invocation with `-CaseId 'all-signed'` selects only SYN-TRAIN-001 and SYN-TRAIN-002. The mock path never probes AWS, SSH, Foundry, ports or HTTP.

The three-case rehearsal on 24 September 2026 completed in **1.344 seconds** after local setup: all three briefs passed the schema, three scorecards were written, and the aggregate reported **0 reviewed / 3 unreviewed**. SYN-001's draft/reference-only record was unchanged. This timing covers fixture replay and local processing only.

## 10. Reviewer aggregate and S0-cases report

After review, refresh the derived report:

```powershell
& $Python "$Repo\scripts\aggregate_scores.py" $Run
if ($LASTEXITCODE -ne 0) { throw 'Resolve reported scorecard/manifest structural errors' }
```

This reads `scorecard_*.md` recursively under the run root and replaces only `scores_summary.md`. It calculates each type's mean from the actual 0/1/2 question scores, excludes reasoned N/A from the denominator, counts critical YES flags separately, and reports reviewed/unreviewed cases. Missing scorecards for selected batch cases count as unreviewed. Duplicate case sheets, conflicting identities or malformed structures produce a visible error and nonzero exit; do not silently pick a preferred rerun. For a report spanning several batch roots, use their common parent with one selected scorecard per case; resolve duplicate reruns explicitly before aggregation.

A completed review requires the existing Reviewer, Review date and Reviewer acceptance signature/date lines, plus every question's score, assessed YES/NO critical flag, supporting quotation/evidence and matched criterion or explanation for NO. N/A needs its reason; critical YES requires score 0. These are the same fields already on the sheet. A completed **HOLD** with critical errors counts as reviewed, not accepted. ACCEPT with a critical YES is inconsistent and stays unreviewed until corrected. Partial reviews contribute no averages. The printed UNREVIEWED banner and handwritten points totals are not grading inputs. Keep the original section headings, question metadata and static question counts intact. Case/question IDs follow the importer's case-insensitive duplicate rule; identity spelling is preserved. Signed capture does not itself complete model-output review.

Live and MOCK scores appear separately. Mock averages demonstrate the reporting workflow only. At Gate 0 close, this report supplies S0-cases results from completed live reviews; absent question types remain N/A, never zero. Bill and Brad still verify case coverage, source rights, authenticity of signoff and engineering acceptance. Gate 3 and S0-retrieval remain deferred until the first scored briefs identify the actual failures to address.

## Expected wall time and human handoffs

These are planning estimates for a short case, not measured GPU performance. Allow 30–65 minutes after a reviewed export is ready; Python dependency setup is a separate one-time task.

| Step | Expected time | Human responsibility |
| --- | --- | --- |
| Export, rights/reviewer confirmation, import and prompt review | 5–10 min | Bill signs the case; Brad exports all records and resolves rejected or ambiguous fields. |
| EC2 boot, health checks and SSH tunnel | 3–8 min | Brad/operator handles credentials, host-key verification and any home-IP change. |
| Tags/template snapshot and brief generation | 0.5–3 min | Operator observes one bounded request; investigates failure before retrying. |
| Stop and confirm stopped | 1–3 min | Operator verifies teardown, including failure paths. |
| Generate scorecard and technical review | 20–40 min | Named reviewer scores, flags critical errors and accepts or returns corrections. |
| Offline synthetic rehearsal | Usually under 30 sec after setup | No EC2 or engineering acceptance; inspect dispositions and MOCK label. |

Expected instance running time is roughly 5–15 minutes, with review performed after shutdown. Only the offline rehearsal is verified with this delivery. Full Gate 0 scope/reviewer acceptance, source rights, appropriate question coverage, live inference behavior and technical grading still require their respective human checks.

For a batch of N short cases, budget one 3–8 minute bring-up, approximately N × 0.5–3 minutes for inference/validation, and one 1–3 minute teardown. Reviewer time still scales per case. These live timings are estimates; batch tests and rehearsal use only mocked services/responses.
