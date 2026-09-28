# FQ-07 v4: SiliconFlow same-model amendment

Prepared 28 September 2026. **Offline amendment only; live use remains blocked
on provider terms and the existing preflight requirements.** The implementation
can prepare and rehearse a SiliconFlow packet. It does not change any deployed
provider, authorize inference or admit outputs to training.

## Exact change

[The v4 protocol](../packs/oil-gas-public-intake/eval/public-v4/protocol.json)
changes four values from frozen v3: schema version, protocol version, Qwen provider
display name (`Nebius` to `SiliconFlow`) and exact route (`nebius/fp8` to
`siliconflow/fp8`). All other protocol values remain equal. V1 sample, v2 prompt
and v2/v3 protocols retain their hashes. Select v4 explicitly; the CLI default
remains v2. Existing approvals cannot authorize v4. V4 Stage B requires reviewed
v4 Stage A, never an earlier provider's results.

Qwen remains `qwen/qwen3-30b-a3b-instruct-2507`. Mistral remains
`mistralai/mistral-small-24b-instruct-2501` on `deepinfra/fp8`. These hosted helpers
are being evaluated for public-material preparation; the domain-training target
remains Qwen3-8B. A matching model ID and FP8 label do not prove matching hosted
weights, tokenizer, template or numerical behavior. Undisclosed revisions stay null.

## Price and routing evidence

Public GETs at **19:22 UTC, 28 September 2026** observed:

| Arm | Route | Status | Context | Advertised input / output per million | Retained price ceilings | Reservation per call |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Mistral | `deepinfra/fp8` | 0 | 32,768 | $0.05 / $0.08 | $0.06 / $0.10 | $0.00206608 |
| Qwen | `siliconflow/fp8` | 0 | 262,144 | $0.09 / $0.30 | $0.12 / $0.36 | $0.03181728 |

Both rows advertise schema output, temperature and output-token controls. The
SiliconFlow row appears in OpenRouter's ZDR catalogue. These are metadata checks,
not successful live requests. Exact URLs, capture times, raw response hashes and
selected rows are in the [evidence directory](verification/helper-siliconflow-20260928/metadata.json).
The same refresh found Nebius back at status **0**, with $0.10 / $0.30 pricing.
The earlier degraded/down observations remain valid historical evidence; neither
recovery nor this amendment automatically chooses a route for a live run.

The pair reservation remains **$0.03388336**. Caps remain **A $0.10, B $0.15,
combined $0.25**. Lower advertised prices do not reduce the conservative ceilings.
Reservations use full context plus 1,000 output tokens, zero non-token fee
allowance, and reconcile reported charges before starting the next pair.
Unknown costs retain the attempted arm's reservation and stop execution. Twenty
Stage-A responses are not guaranteed to fit. See the [v3 reservation policy](HELPER_COMPARISON_V3.md).

V4 retains no retries/fallbacks, serial calls, required parameter support,
`data_collection: deny`, `zdr: true`, `enforce_distillable_text: true`, native
non-reasoning behavior and disabled context compression. The request pins
`provider.only: ["siliconflow/fp8"]`; the returned provider must be `SiliconFlow`.
A Nebius response is rejected. No private cases, archives or client drawings are
part of this public development sample.

## Material terms issue found during review

SiliconFlow's [Terms of Use](https://docs.siliconflow.com/en/legals/terms-of-service),
dated 9 September 2026, contain restrictions in **3.4(b)** on using service content
for ML/AI training or development, **3.4(l)** on benchmarking and **3.4(p)** on
commercial uses; **3.4(j)** also addresses competing products. This comparison
supports a commercial AI project. Applicability or an override for the OpenRouter
route has not been established. **Do not mark rights/cloud acceptance true until
applicable written terms resolve these uses.** This is an unresolved contract
question, not a conclusion that the route can never be used.

OpenRouter's [distillable-text filter](https://openrouter.ai/docs/guides/routing/provider-selection#enforcing-distillable-text)
checks the **model author's** distillation setting. It is not evidence of a waiver
of a hosting provider's terms. Its [ZDR documentation](https://openrouter.ai/docs/guides/features/zdr)
also distinguishes endpoint-specific policies from general provider policies.
SiliconFlow's [privacy policy](https://docs.siliconflow.com/en/legals/privacy-policy)
describes interaction data and personal-data handling separately; it is not a
blanket proof of endpoint retention behavior. Preserve ZDR enforcement and record
the terms applicable to this exact OpenRouter route before live use.

Draft clarification for Brad to send, if needed (not sent):

> For OpenRouter's siliconflow/fp8 route serving
> qwen/qwen3-30b-a3b-instruct-2507, please identify the governing customer terms
> and any override of SiliconFlow Terms 3.4(b), (j), (l) and (p). Is a private,
> commercial engineering answer-quality comparison permitted? Separately, may
> reviewed outputs be used later to develop or fine-tune our own model? Please
> confirm the prompt/output retention and training policy for this endpoint.

## Offline preparation and rehearsal

Use the existing Python runtime and the Foundry checkout containing commit
`82904854503381a7082a0c13231c9d4a9a8d9748`. No key is needed. The following creates
new directories, two packets, incomplete approval worksheets, fabricated answers
and blank scoring sheets. It makes no HTTP requests.

```powershell
$Domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
$Foundry = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-plan'
$Python = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\slm-foundry-worktrees\codex-foundry-ingestion-live-http\outputs\geometry-venv\Scripts\python.exe'
$Root = Join-Path $Domain ('tmp\helper-v4-' + (Get-Date -Format yyyyMMdd-HHmmss))
foreach ($Stage in @('stage_a', 'stage_b')) {
    $StageRoot = Join-Path $Root $Stage
    & $Python "$Domain\scripts\research\prepare_helper_comparison.py" --protocol-version v4 --stage $Stage --out "$StageRoot\packet"
    if ($LASTEXITCODE) { throw 'Preparation failed' }
    & $Python "$Domain\scripts\research\run_helper_comparison.py" plan --packet "$StageRoot\packet" --foundry $Foundry --out "$StageRoot\proposal"
    if ($LASTEXITCODE) { throw 'Proposal failed' }
    & $Python "$Domain\scripts\research\run_helper_comparison.py" run --mode mock --packet "$StageRoot\packet" --foundry $Foundry --out "$StageRoot\run"
    if ($LASTEXITCODE) { throw 'Rehearsal failed' }
    & $Python "$Domain\scripts\research\run_helper_comparison.py" score --run "$StageRoot\run" --scores "$StageRoot\run\scores.csv" --out "$StageRoot\unreviewed"
    if ($LASTEXITCODE) { throw 'Score summary failed' }
}
```

Expected: 20 A and 40 B fabricated responses, all unreviewed. Mock B is software
verification, not satisfaction of the live Stage-A dependency. Do not present
synthetic costs, scores or test approvals as engineering evidence.

## Requirements before a live comparison

1. Brad records the applicable provider terms and permissions, including resolution
   of the restrictions above, in the hash-bound rights/cloud evidence. No approval
   is inferred from a model licence or public availability.
2. The technical reviewer accepts source/reference correctness and quality rules.
   Keep public-v1 families and derivatives out of training and held-out claims.
3. Refresh both endpoint snapshots within 24 hours of execution. Require status 0,
   exact routes/models/context and prices within ceilings. Complete the existing
   schema, native non-reasoning, context enforcement, truncation and billing/fee
   evidence. Catalogue support alone does not verify hosted behavior.
4. Verify account spending controls and record exact-run approval. Regenerate the
   worksheet after clean committed code, because code commits and exact wire
   hashes are bound to it. Leave unknown revisions explicit.
5. Only then run bounded A under the [execution procedure](HELPER_COMPARISON_EXECUTION.md).
   Review its complete paired results and billing before separately authorizing B.
   Do not substitute Nebius or another endpoint into either packet.

## Verification

The targeted v4/v3 run passed **37 tests** (11 new). The full offline Python
recheck passed **463 tests**, with **103 database-dependent skips** and the
existing requests dependency warning. The initial run had four WinError 5
rename/replace failures; unchanged code passed after moving test output to a fresh
Windows temporary directory. The access-error root cause is not established.
Both runs are recorded in [the verification receipt](verification/helper-comparison-v4.json),
alongside hashes and saved mock rehearsals. Independent read-only review found
no actionable amendment-code defects. Software review
does not resolve the provider terms or authorize inference. Both related PRs
remain drafts: [Broadbridge #24](https://github.com/bHBeachsider/Broadbridge4096/pull/24)
and [Foundry #20](https://github.com/bHBeachsider/slm-foundry/pull/20).
