# SD-03: offline synthetic batch rehearsal

The generic runner lives in Foundry; this repository supplies draft recipes,
prompts, rubric and a fabricated rehearsal. Bill has not selected these topics
or approved the recipes. Start with [Bill's priority/case handoff](BILL_START_HERE.md).

From the Broadbridge working checkout, choose the explicit Foundry checkout and
a **new** private output directory:

```powershell
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http'
$Python = 'C:\Python313\python.exe'
$env:SLM_FOUNDRY_PATH = $Foundry
$Run = Join-Path $PWD ('packs\oil-gas\outputs\synthetic-mock-' + [guid]::NewGuid().ToString('N'))
& $Python scripts/research/rehearse_synthetic_batch.py --mock --foundry $Foundry --out $Run
if ($LASTEXITCODE -ne 0) { throw 'Mock rehearsal failed' }
Get-Content (Join-Path $Run 'report.json')
& $Python -m pytest scripts/research/test_rehearse_synthetic_batch.py -q
if ($LASTEXITCODE -ne 0) { throw 'Mock rehearsal tests failed' }
```

The paths above are the reviewed local checkouts and CPU Python used for this
delivery. Another operator selects their Python with the existing Foundry test
dependencies and domain PyYAML installed, and their absolute Foundry checkout.
It must contain SD-02 and SD-03. The script verifies imported
module locations and rejects an existing output directory. It has no live mode,
accepts no real case export, loads no credentials and makes no network request.

Expected: two pending packets, four mock role calls, zero external model calls,
`priority_decision=awaiting_bill`, and `release_blocked_without_review=true`.
The seed directory contains the existing SD-02 fabricated evidence; the batch
directory adds call-intent, receipt, packet and provenance artifacts.

The rehearsal tests missing pressure basis and missing exchanger evidence. It
does not assess engineering-model accuracy, select a helper or authorize those
topics for training. Arithmetic/calculation coverage remains SD-04; no new
numeric answer bypasses Foundry's existing numerical-claim guard.

## Human input before a real batch

1. Bill ranks important areas/tasks in Case Capture Part A/A8 (or the private
   [priority worksheet](templates/EXPERT_PRIORITY_INPUT.md)), identifies exclusions
   and helps select representative cases.
2. Bill scores the public development packet and confirms failure categories.
   Existing public-v1 families remain testing_only/dev, including derivatives.
3. Brad and the qualified reviewer record chosen recipe versions, required
   evidence, allowed variations, hard-fail criteria, source rights and processing
   location. Independent reviewers do not accept their own authored answers.
4. The operator prepares a bounded plan with source/history snapshots, prompt,
   rubric, policy and model settings; uses Foundry's offline `--check`; and records
   the separate plan-hash approval. The draft curriculum file is not that approval.
5. Only a separately authorized job may use live public adapters. Confidential
   expert material remains held for a tested local route. There is no automatic
   external fallback or training trigger.

Every candidate remains pending until independent technical acceptance, rights
and release decisions. Gate 0, S0-cases, the later retrieval comparison and
compute authorization are unchanged. No EC2, database migration, production
deployment or live model call is part of this rehearsal.

## Verification on 26 September 2026

| Check | Result |
| --- | --- |
| Foundry batch/packet/helper/transport tests | 136 passed, including 42 batch tests |
| Full Foundry Python CPU suite | 609 passed, 2 skipped |
| Both domain synthetic rehearsal test files | 5 passed |
| Full Broadbridge Python suite, explicit Foundry path, database URLs unset | 314 passed, 106 gated tests skipped |
| Direct mock command and offline plan CLI | Two pending packets, four mock calls, zero external calls; release blocked |
| New handoff/runbook relative links and Git whitespace checks | Passed |

The initial full domain run exposed an existing smoke-test stub missing its
caller's keyword arguments; the stub now asserts the default flags and tests
environment restoration again. Two Windows rename-permission failures did not
recur in fresh directories or the final full run; no importer runtime was changed.
Existing Requests dependency and Foundry SWIG deprecation warnings remain.
Skipped integration tests are not claimed as database/deployment validation.

Single-lane review added failing tests for escaped multiline private labels,
nonfinite response/usage values retaining known cost, and fabricated numerical
givens in a generated question. They pass after fixes. These are software checks,
not expert endorsement or measured model quality.
