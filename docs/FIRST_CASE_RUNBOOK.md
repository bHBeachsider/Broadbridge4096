# First signed case: export, brief and reviewer scorecard

Owner: Brad / Broadbridge Oil & Gas. Technical acceptance: the Broadbridge-appointed reviewer named for this exercise. Updated 24 September 2026.

Bill enters and signs off the case in the Broadbridge Case Capture page. Brad exports **All records as JSON**. This runbook uses that export directly, without DOCX parsing. The Interview Guide remains available as a pre-read/call script. Domain records and results stay in Broadbridge4096; the shared client stays in slm-foundry.

The result is one structured stock-model brief and an **unscored** `eval/scorecard_<case_id>.md` for a human reviewer. The model receives only `identity.unit_service` and `decision_time`, with a fixed system instruction and the brief output schema. Questions, reference answers, hindsight, workflow and evidence attachments are not sent to it.

This is a first-case exercise, not the complete S0 retrieval benchmark. It does not train a model, close Gate 0, or establish adapter superiority. Use the stock Ollama Qwen3 template with `think:false`; later base-versus-adapter comparisons still require matched templates and settings.

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

## 2. Export and import (Terminal A, no GPU)

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

## 3. Start EC2 and open the tunnel (Terminal B)

These are the serving brief's instance, region, port mapping and key. The fresh IP is obtained directly from EC2. This replaces `infra/status.ps1` here because that helper also uses the saved SSH alias and probes unrelated training/S3 state.

Run the following in a **second PowerShell window**. If bring-up fails after the instance starts, run the teardown block in section 5 before leaving. Check SSH host-key prompts normally; do not disable host-key verification.

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

## 4. Generate the stock brief (Terminal A)

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
    if ($LASTEXITCODE -ne 0) { Write-Warning 'STOP FAILED: use section 5 and confirm stopped in AWS before leaving' }
}
```

The saved tag digest and model-info/template snapshot identify the stock build; a mutable tag alone is insufficient for later reproducibility. Record any uncommitted code changes separately or run from reviewed, committed code. The run envelope binds the case, prompt and brief schema with canonical JSON hashes, labels live versus mock, records settings and elapsed time, and contains the validated draft. It is not a signed audit record or a technical correctness check.

The client timeout is 120 seconds. Cold-start latency and live schema-constrained generation have not been measured in this first-case workflow. A timeout or invalid reply fails the run; diagnose before an explicit retry in a fresh run directory. Do not repeatedly retry unattended. The serving brief reports a 4096-token default context. Review long cases against that limit before inference; this harness does not measure token counts or prove that the server avoided truncation. Do not silently trim a signed case to fit.

## 5. Confirm teardown (Terminal A)

Stop the GPU before the reviewer starts reading. This block is also the recovery path if Terminal B startup, health checks or inference failed before the `finally` block ran.

```powershell
aws ec2 stop-instances --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
if ($LASTEXITCODE -ne 0) { throw 'Stop failed: resolve in AWS; do not leave the box running' }
aws ec2 wait instance-stopped --region us-east-1 --instance-ids i-0e5e1cbc7b1367566
if ($LASTEXITCODE -ne 0) { throw 'Stopped state not confirmed; check AWS console' }
```

Press Ctrl+C in Terminal B if SSH has not already exited. No `bootstrap.sh`, IAM profile change, S3 transfer or deployment script is part of this run.

## 6. Generate and complete the reviewer scorecard (no GPU)

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

## 7. Offline rehearsal on SYN-001 (no EC2, no model connection)

Use this block instead of sections 2–6. It exercises the same importer, prompt guard, structured output validation and scorecard generator. The response is a clearly labelled authored fixture; `--mock-response` never loads the Foundry client. SYN-001 stays draft/reference_only and eval-only, with zero training candidates. `--dry-run` alone only prints the prompt and does not exercise response/scoring output.

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
