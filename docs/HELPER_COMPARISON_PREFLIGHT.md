# FQ-07: provider preflight and Stage-A packet

Follow-up: [v3 context reservations](HELPER_COMPARISON_V3.md) now implements the
recommended reservation design below. This document preserves the earlier v2
preflight findings; neither version has performed a live comparison.

Checked 28 September 2026. **Public metadata checked; live execution remains unverified.**
The Stage-A packet contains ten questions, two of each type, paired across two
helpers: twenty requests. No inference requests, paid calls, EC2 activity,
training, database writes or production changes occurred. Qwen3-8B remains the
domain model; this compares hosted helpers for preparing public-material work.

The [machine-readable receipt](verification/helper-comparison-preflight-2026-09-28.json)
records retrieval times, hashes, endpoint observations and packet checks. Small
catalogue snapshots are retained beside it. Full public documentation and the
unfiltered ZDR response are in the ignored local working directory; their hashes
are recorded, but those files are not distributed with the repository.

## What was verified

Prices are the observed per-million-token rates, not quotes for future execution.

| Helper | Selected provider / observed variant | Input / output USD per million | Metadata result |
| --- | --- | --- | --- |
| `mistralai/mistral-small-24b-instruct-2501` | DeepInfra / `deepinfra/fp8` | $0.05 / $0.08 | Listed; structured output advertised; status `0` |
| `qwen/qwen3-30b-a3b-instruct-2507` | Nebius / `nebius/fp8` | $0.10 / $0.30 | Listed; structured output advertised; status `-2` on initial and repeat reads |

Both exact provider/model combinations appeared in OpenRouter's ZDR endpoint
catalogue and filtered distillable/ZDR model results. This is advertised
eligibility, not a successful live request or proof of data residency. The wire
requests retain `zdr:true`, `data_collection:deny`,
`enforce_distillable_text:true`, `require_parameters:true`, provider allowlists,
no fallback, temperature zero and 1,000 maximum output tokens. See the
[model endpoint API](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model)
and [routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).

The published endpoint schema lists `-2` as a legal status without defining its
meaning. **Do not translate it into a confirmed outage, deprecation or healthy
state.** Recheck before execution and resolve its meaning or verify the exact
route through a separately bounded capability run. Other Qwen providers were
listed, but none was substituted into the frozen comparison. These observations
also do not prove the requested JSON Schema subset will work end to end.

Neither selected endpoint advertises the `reasoning` parameter. The new wire
proposal therefore uses `native_nonreasoning` for both arms and omits that field.
Qwen's [official model card](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507)
explicitly describes this checkpoint as non-thinking. Mistral's
[model card](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501)
documents a conventional V7-Tekken instruction template; native non-reasoning
operation is the proposed interpretation of that checkpoint and endpoint metadata,
not a measured provider behavior. The runner will still reject reported reasoning
tokens/content. A successful metadata check is not a signed `controls_verified`
attestation.

Both upstream cards declare Apache-2.0. Upstream source revisions observed:

- Mistral: `9527884be6e5616bdd54de542f9ae13384489724`.
- Qwen: `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe`.

These are **upstream repository revisions**, not pins for the hosted provider's
weights, tokenizer, chat template or software. Those hosted revisions remain
undisclosed. FP8 is an observed quantization label, not a quantization-artifact
revision. No weights or tokenizer assets were downloaded.

## Public-source rights and allocation

This packet reuses the existing six EIA and four CSB public text sources.
The current [EIA reuse policy](https://www.eia.gov/about/copyrights_reuse.php)
permits reuse of EIA publications with acknowledgment and publication date, while
identifying protected third-party material and photographs as exceptions.
The [CSB policy](https://www.csb.gov/privacy-policy/) permits copying public
information unless otherwise specified. These policies support reviewing the
agency-authored text excerpts; they do not grant blanket rights to every linked
image, attachment or contributed work. Item-level exceptions and the actual frozen
excerpts still need to be included in the existing rights decision.

The original sample hash remains
`3407f8d2ea56e0cc8c379f9a84b5c1808b72d5dedd7c504d1badbcb423a0e736`.
The questions, source families and derivatives remain **testing-only / development
calibration**, even when a model or provider permits distillation. Nothing here
admits this evaluation sample into training. No expert approval was supplied on
Bill's behalf.

## Packet and remaining token limitation

Local prepared files, relative to this checkout:

```text
tmp/helper-v2-preflight-20260928/
  retrievals.json
  stage-a/
    packet/                  # fixed questions, evidence, rubric, checksums
    wire/
      wire_requests.jsonl    # twenty exact request bodies; no credentials
      approval.template.json # incomplete; approvals false, token counts null
```

Reproduce the proposal in a new output directory, using the existing Python and
Foundry paths from [the execution runbook](HELPER_COMPARISON_EXECUTION.md):

```powershell
$Root = Join-Path $Domain ('tmp\helper-preflight-' + (Get-Date -Format yyyyMMdd-HHmmss))
& $Python "$Domain\scripts\research\prepare_helper_comparison.py" --stage stage_a --out "$Root\packet"
& $Python "$Domain\scripts\research\run_helper_comparison.py" plan --packet "$Root\packet" --foundry $Foundry --out "$Root\wire" --mistral-reasoning native_nonreasoning --qwen-reasoning native_nonreasoning
```

The existing v2 runner requires a verified input bound of at most 8,192 tokens
for every request, including hosted template/schema overhead. No compatible
pre-request counting method was established in this review. The inspected
[Nebius OpenAPI specification](https://api.tokenfactory.nebius.com/openapi.json)
has completion/chat routes but no token-count route. OpenRouter's inspected
documentation index did not establish such a service for these models; this is a
finding about the reviewed interfaces, not proof that no provider offers one.
A local upstream tokenizer alone cannot verify undisclosed hosted additions.
Request bytes, estimated ratios and post-call usage are not substitutes for v2's
required preflight evidence.

Consequently the current $0.061152 Stage-A reservation calculation is still
**conditional**, not an established upper bound. The incomplete worksheet must
remain incomplete. Regenerate it after any repository commit or request change;
its commit bindings are tied to the checkouts used by `plan`.

## Recommended next implementation

Keep v2 intact. Prepare a separately versioned reservation policy that can operate
without pretending to know a hosted input-token count:

1. Pin the exact provider variant and its published maximum context. Validate
   provider identity, privacy controls and schema support separately. Retain all
   existing source, review and paired-stop rules.
2. Add per-arm price ceilings and reserve the **whole context at the ceiling**
   plus the configured maximum output before dispatch. This over-reserves input
   rather than asserting the request fits an 8,192-token bound. Confirm how the
   endpoint applies context limits, truncation and any non-token fees. Reject
   automatic prompt truncation; request-size failure stops the pair.
3. Reserve both members of a pair, execute serially, reconcile reported actual
   billing, and stop if the next pair cannot be reserved. Unknown billing retains
   the reservation and stops both arms. Keep A <=$0.10, B <=$0.15, combined <=$0.25;
   fewer completed pairs must remain an incomplete comparison, not a success.
4. Test context/price changes, unknown charges, failed first/second members and
   pair reservations before updating any live-run proposal. Check account/key
   spending controls and funding/other fees independently. API budget enforcement
   is not a refund mechanism or a guarantee against provider billing errors.

Illustrative ceilings below allow some headroom over the observed rates. They
are **a design proposal, not implemented, approved or an expected bill**:

| Arm | Context used for reservation | Proposed input / output ceiling per million | Maximum token-charge reservation per call |
| --- | ---: | ---: | ---: |
| Mistral | 32,768 | $0.06 / $0.10 | $0.00206608 |
| Qwen | 262,144 | $0.12 / $0.36 | $0.03181728 |
| Pair | | | **$0.03388336** |

Formula: `(context * input ceiling + 1,000 * output ceiling) / 1,000,000`.
Ten such pairs at their full reservations would exceed $0.10; the runner must
stop early unless reconciled actual charges leave room. Do not promise that all
twenty calls fit. This proposal avoids increasing the existing spending ceilings
or blocking on unavailable tokenizer metadata. It does require a new protocol,
code and tests; changing an approval JSON alone is insufficient.

Remaining live decisions are the endpoint/status resolution, the token/reservation
policy, source/reference and quality-screen acceptance, verified account spending
controls, and authorization of the concrete run. The account/key limit was not
inspected and no credentials were accessed in this preflight. The existing
runner enforces these requirements; this report grants no additional approval.

## Verification of this preflight

`SLM_FOUNDRY_PATH` was set to the helper-receipts checkout and
`python -m pytest scripts/research/test_helper_comparison_execution.py -q`
completed with **51 passed**, no skips, and the existing requests dependency
warning. The initial invocation omitted that path and skipped all 51 tests; that
was corrected before claiming a pass. All HTTP in the suite is mocked.
Nineteen saved retrieval files and all six retained evidence hashes matched;
twenty wire requests, the frozen packet recompilation, proposal arithmetic,
relative document links and the sixteen-row queue were checked. The wider suites
were not rerun for this documentation-only update.
