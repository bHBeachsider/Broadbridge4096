# FQ-07 v3: conservative reservations for hosted helpers

V3 implements the cost-reservation design in
[the provider preflight](HELPER_COMPARISON_PREFLIGHT.md). It removes the need to
claim an exact hosted input-token count before calling a provider. It does not
authorize calls or select a model. Qwen3-8B remains the domain-training target;
these hosted helpers are candidates for preparing public-material work.

The v2 protocol, original sample and prompt remain unchanged. Select v3 explicitly
when preparing a packet. The existing compiler, executor and scorecard tools
support both versions; an approval for one cannot authorize the other. Stage B
must use reviewed Stage A from the same protocol, with A's actual cost deducted
from the combined allowance. The v3 quality criteria and development-only source
allocation are unchanged.

## Reservation policy

| Arm | Requested endpoint | Published context used | Input / output price ceiling per million | Reservation per call |
| --- | --- | ---: | ---: | ---: |
| Mistral Small 24B Instruct 2501 | `deepinfra/fp8` | 32,768 | $0.06 / $0.10 | $0.00206608 |
| Qwen3 30B A3B Instruct 2507 | `nebius/fp8` | 262,144 | $0.12 / $0.36 | $0.03181728 |
| Pair | | | | **$0.03388336** |

Each reservation is `(context * input ceiling + 1,000 * output ceiling) / 1e6`,
plus the per-call non-token fee allowance, currently zero. Reserving both a full
input context and the output cap deliberately overestimates a normal request.
It is a bound under the recorded provider context/pricing/fee assumptions, not a
prediction or an independent guarantee of provider billing correctness.

Before the first call of every pair, both different reservations are written to
the run checkpoint. Calls run serially, without retry. A known charge replaces
that call's reservation, including charges for failed answers. Unknown billing
retains the attempted call's reservation and stops the run. If the first member
fails, the second stays unattempted and its reservation is released. Any reported
charge above its reservation is recorded as an overrun and stops the run.

The limits remain **$0.10 for A, $0.15 for B and $0.25 combined**. The next pair
starts only if its whole reservation fits alongside reconciled charges and any
holds. Twenty calls are not guaranteed to fit. Budget stops preserve all planned
slots and cannot pass the complete-pair quality screen. Purchase/funding fees and
account spending controls require separate verification; the local runner cannot
enforce a provider's bill or reverse an overcharge.

## Endpoint and context evidence

The shared client distinguishes routing identifiers from response identity:
`provider_routes` sends exact endpoint slugs; `providers` continues to validate
the returned provider display name. The receipt records the requested route.
An endpoint tag is a routing constraint, not a disclosed hosted weight revision.

V3 uses native non-reasoning endpoints and requires evidence for that behavior.
It requests no thinking field. It sends `transforms:[]` and explicitly disables
the current context-compression plugin with
`plugins:[{"id":"context-compression","enabled":false}]`. Oversized input must
fail rather than be silently shortened. See OpenRouter's
[message-transform documentation](https://openrouter.ai/docs/guides/features/message-transforms)
and [endpoint routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection).
The client still rejects reported reasoning tokens/content and unexpected model
or provider identities. It cannot independently observe an undisclosed backend
template or detect every form of provider-side silent alteration.

The approval worksheet contains exact wire hashes and per-request reservations;
it does not contain invented token counts. Each provider needs a hash-bound JSON
snapshot with this wrapper around its exact catalogue row:

```json
{
  "schema": "broadbridge.helper_endpoint_snapshot/1",
  "retrieved_at": "<timezone-aware retrieval timestamp>",
  "endpoint": {"...": "the complete selected row from the model endpoint API"}
}
```

Retain the raw HTTP response, URL and hash alongside the wrapper. The live validator
checks snapshots are at most 24 hours old and not future dated; exact model,
provider, endpoint tag and context; required schema/temperature/output-limit
parameters; prompt/completion prices within ceilings; and any disclosed request
fee within its allowance. V3 accepts only numeric status `0`. This is a deliberately
conservative acceptance policy, not a claim that the API documents all status
meanings or that a status alone proves a route works.

The operator must also record `context_and_billing_verified:true` with a pinned
`billing_evidence_sha256`: evidence that the context is enforced without silent
truncation and all applicable per-call charges fit the policy. A missing `request`
price is not independently proven to mean zero fees. This field complements the
existing `controls_verified` attestation for schema, privacy and reasoning behavior.
Undisclosed hosted revisions remain null. Nothing is signed automatically.

The 28 September recheck still returned **Nebius status -2**, so that real snapshot
does not pass v3. DeepInfra returned status 0. Prices and context matched the prior
preflight. The actual snapshots are retained under
`docs/verification/helper-v3-endpoints-20260928/`. They are observations, not live
capability tests. Refresh them before any later run; never edit a negative status
into an approval. Changing providers requires a new reviewed protocol and packet.

## Offline commands

Set `$Domain`, `$Foundry` and `$Python` to the existing checkouts/runtime described
in [the execution runbook](HELPER_COMPARISON_EXECUTION.md). The Foundry checkout
must include the optional route/compression controls. No keys are required below.
All output directories must be new.

```powershell
$Root = Join-Path $Domain ('tmp\helper-v3-' + (Get-Date -Format yyyyMMdd-HHmmss))
& $Python "$Domain\scripts\research\prepare_helper_comparison.py" --protocol-version v3 --stage stage_a --out "$Root\packet"
& $Python "$Domain\scripts\research\run_helper_comparison.py" plan --packet "$Root\packet" --foundry $Foundry --out "$Root\proposal"
& $Python "$Domain\scripts\research\run_helper_comparison.py" run --mode mock --packet "$Root\packet" --foundry $Foundry --out "$Root\run"
& $Python "$Domain\scripts\research\run_helper_comparison.py" score --run "$Root\run" --scores "$Root\run\scores.csv" --out "$Root\unreviewed"
```

Expected: twenty fabricated responses and twenty blank score rows, with zero real
calls and no engineering acceptance. Repeat with `--stage stage_b` and a separate
directory for the forty-response software rehearsal. Mock B is not evidence that
the live Stage-A review dependency has been met.

Before a live run, finish the existing source/reference/quality, spending and
exact-run approval fields as well as the v3 endpoint evidence. Regenerate the
worksheet after committing both repositories, because commit hashes are part of
its approval. The existing one-use interlock, 24-hour approval expiry and clean
repository requirements remain. Use the original execution runbook's live CLI
only after those requirements are fulfilled. No EC2 or training is involved.

## Verification

The [verification receipt](verification/helper-comparison-v3.json) records the
code, protocol and rehearsal hashes. The full Broadbridge Python run passed 449
tests with 106 skips; three skipped offline adapter tests then passed with their
Foundry path configured, leaving 103 database-dependent tests unrun. The full
Foundry suite passed 622 with two skips (Windows symlink support and opt-in
disposable PostgreSQL). Existing dependency/SWIG warnings remain.

All 26 v3 tests passed, including fresh endpoint checks, prices/context/status
drift, per-arm unknown/over-budget charges, complete A+B scoring and v2 regression
coverage in the wider suite. Saved rehearsals have 20 A and 40 B fabricated
answers, all unreviewed. The timeout rehearsal holds $0.03181728 for unknown Qwen
billing. None is model-performance evidence. Independent code review found no
confirmed P1/P2 defect; hosted context enforcement and live billing remain untested.
