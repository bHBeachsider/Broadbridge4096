# First-case preflight while review is pending

30 September 2026 UTC. Brad confirmed that no new expert review or signed case is available. Continue offline preparation; do not substitute fixture signatures for review.

Brad subsequently approved the separate [pressure diagnostic test/scoring set](../packs/oil-gas/eval/pressure-diagnostic-v1/README.md) with Bill's agreement assumed for that purpose and rights TBD. This changes that exercise's planning status, not the signed-case count or fixture classification below.

`packs/oil-gas/scripts/case_preflight.py` reads a complete canonical export and writes an offline gap report before any import or GPU session. It reuses the existing case schema, ID validation, family-split rule, signed-case check and decision-time prompt/leak guard. It does not modify the export, create training rows, load model weights, read credentials or call a database/model/cloud service.

## Use on the next export

Run in the existing local CPU environment. Supply an absolute **new** output directory, preferably under the pack's ignored `outputs/`. The preflight writes `PREFLIGHT.md` and `preflight.json`; identifiers and hashes can still be sensitive, so preserve them with the restricted export.

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$Export = Read-Host 'Full path to the complete canonical export JSON'
$out = Join-Path $domain ('packs\oil-gas\outputs\case-preflight-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$tokenizer = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\foundry-gate1\qwen-tokenizer'
& C:\Python313\python.exe "$domain\packs\oil-gas\scripts\case_preflight.py" $Export --out $out --tokenizer-dir $tokenizer --context-limit 4096 --output-reserve 1024 --margin 256
if ($LASTEXITCODE -ne 0) { throw 'Preflight could not produce a valid report' }
Get-Content -LiteralPath "$out\PREFLIGHT.md"
```

Omit `--tokenizer-dir` if the local tokenizer is unavailable; context then says `not_measured`. No download is attempted. Token counting requires the already installed Transformers/tokenizers packages; the rest uses the existing first-case requirements. The command's zero exit code means **report written**, never “start EC2” or “approved.” Review the report and the remaining human/runtime checks. This tool is not an enforcement layer for the legacy PowerShell live launcher.

## What the report checks

- The complete `broadbridge.case_record/1` export, unique IDs, status and complete named/dated signoff. The strictest question split applies to the whole family, including questions from unsigned family members. Historical family records outside this export still need reconciliation.
- Missing question text, reference answers or hard-fail criteria; missing calculation tolerance; missing grounding evidence IDs. An exact `unknown` marker is missing scoring information, though it remains legal in the capture schema. The tool does not decide answer correctness, infer units/tolerances or verify that an evidence description names a real attachment.
- The decision-time-only model projection and existing exact-string hindsight/reference-answer leak guard. Prompt text and reference answers are not copied into the report. Paraphrased hindsight still requires human review.
- Five-type counts for structurally complete signed questions outside recognized fixtures. `SYN-` IDs and explicit synthetic markers are excluded; `--fixture-export` excludes the entire file. An absent marker does not establish real provenance, and a hypothetical case is not automatically rejected merely for being hypothetical. A count of 30 never closes Gate 0 automatically.
- Local prompt-token estimate plus a proposed answer reserve and rendering margin. Over-budget cases are flagged and never truncated. The reserve is a planning choice, not an enforced inference setting.

## Context estimate: precise scope

The four existing tokenizer files are verified against the pinned Qwen3-8B inventory at revision `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb`. The verifier supports the inventory's Git blob SHA-1 and SHA-256 formats; added sidecars that could override the template are rejected. Tokenization is local-only with remote code disabled, `enable_thinking=False`, generation prefix included and an explicit flat token-ID result. A dictionary/nested/empty result is rejected rather than counted incorrectly.

This uses the Hugging Face template. It does **not** prove equivalence with the installed Ollama template, account exactly for live structured-output overhead, enforce server output settings or establish that the server avoided truncation. A live baseline still needs its actual model digest/template/context/settings captured. The A10G load check established an NF4 checkpoint, not an Ollama service. Do not silently switch the baseline host or reuse the load-only packet as inference authorization.

The actual local rehearsal used Transformers **5.9.0** and tokenizers **0.22.2**, both already installed on the PC. No package was upgraded. AWS's qualified training stack remains on its recorded versions, including Transformers 5.5.0; this CPU estimate does not requalify that stack.

## Completed offline rehearsal

The supplied three-case fixture export produced **340 prompt tokens per case** with the pinned local tokenizer. All fit the proposed 4,096-token context with a 1,024-token output reserve and 256-token margin. `SYN-001` remains unsigned and fails the signed-case check; both SYN-TRAIN records pass that mechanical check. All three are fixtures, so real signed reference coverage remains **zero**, and all five types are still needed for Gate 0.

Separately, the existing `scripts/first_case.ps1` **mock** path imported the three fixtures, replayed the saved mock response, wrote three valid `brief_run.json` files and three unreviewed scorecards, and generated a batch summary. `scripts/aggregate_scores.py` reported **zero reviewed / three unreviewed**. No model generated those answers, and no model accuracy or GPU latency was measured. The importer's two synthetic training-candidate rows remain fixture artifacts only; no release was created.

Reproduce the mock workflow with a fresh run root:

```powershell
$run = Join-Path $domain ('packs\oil-gas\outputs\case-mock-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$fixtures = Join-Path $domain 'packs\oil-gas\tests\fixtures'
& "$domain\scripts\first_case.ps1" -Export "$fixtures\three_cases_export.json" -CaseId 'SYN-001,SYN-TRAIN-001,SYN-TRAIN-002' -MockResponse "$fixtures\SYN-001.mock_brief.json" -Python C:\Python313\python.exe -RunRoot $run
if ($LASTEXITCODE -ne 0) { throw 'Mock batch failed' }
& C:\Python313\python.exe "$domain\scripts\aggregate_scores.py" $run
if ($LASTEXITCODE -ne 0) { throw 'Score aggregation failed' }
```

Local outputs are `packs/oil-gas/outputs/first-case-preflight-20260930-v2/` and `packs/oil-gas/outputs/first-case-rehearsal-20260930/`. The earlier unversioned preflight output is superseded: it exposed a new-code token-count bug and must not be used. It was preserved, not overwritten; v2 uses the corrected flat token-ID count and explicit regression tests. [Validation receipt](evidence/first-case-preflight-2026-09-30.json).

**106 offline tests passed**, no failures/skips: preflight, batch lifecycle with mocked AWS/HTTP, brief/scorecard integrity and score aggregation. This is software validation, not a live baseline or independent engineering review.

## Next action when a signed case arrives

Run this preflight on the whole export, resolve the flagged fields and review the decision-time projection, rights/storage and actual signoff. Then use the [first-case workflow](FIRST_CASE_RUNBOOK.md) under a separately approved, bounded session with current ownership/host/shutdown checks. The older PowerShell launcher does not itself provide the later 80/85/90-minute controls; its mock path remains useful offline. Live session integration must be reviewed before use. Score S0-cases before building retrieval; retain the existing dataset and training gates in [AWS_TRAINING_READINESS.md](AWS_TRAINING_READINESS.md).
