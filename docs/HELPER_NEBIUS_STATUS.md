# FQ-07: Nebius endpoint status investigation

28 September 2026. **The meaning is resolved: `-2` means degraded performance.**
The later public API observation is `-5`, which OpenRouter labels Down. The live
comparison remains blocked on this route. No software defect was found in our
status check, and no inference request was needed to diagnose the catalogue flag.

## Evidence and interpretation

The generated [OpenRouter SDK enum](https://github.com/OpenRouterTeam/typescript-sdk/blob/main/src/models/endpointstatus.ts)
lists numeric values without semantic names. OpenRouter's own
[model page](https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507#providers)
loads a [public JavaScript asset](https://openrouter.ai/_next/static/immutable/chunks/3h226b2h-dywl.js)
that names the values:

| Value | First-party client enum name | Our v3 policy |
| --- | --- | --- |
| 0 | Default | May pass the status check; other checks still apply |
| -1 | Deprioritized | Reject |
| -2 | DegradedPerformance | Reject |
| -3 | Deranked | Reject |
| -5 | Down | Reject |
| -10 | Disabled | Reject |

This is a direct observation of first-party application code, not an inference
from a third-party uptime monitor. The enum excerpt, asset hash, capture time and
page build identifier are pinned in
[status-definitions.json](verification/helper-nebius-status-20260928/status-definitions.json).
The client implementation is evidence at capture time, not a promised stable API
contract. It does not disclose the internal condition or threshold that caused
Nebius's flag. In particular, `-2` alone does not mean retired, disabled, an invalid
key, or a universal failure of the model.

| Observation (UTC) | Route | Status | API rolling 30-minute uptime |
| --- | --- | --- | ---: |
| 18:29:23 | nebius/fp8 | -2 | 89.57% |
| 18:58:53 | nebius/fp8 | -5 | 78.04% |

Both came from HTTP 200 responses to the unauthenticated
[model endpoints API](https://openrouter.ai/api/v1/models/qwen/qwen3-30b-a3b-instruct-2507/endpoints).
These are observations at two times, not a continuous outage history. Browser
inspection additionally showed a Down badge on Nebius's provider row. Rolling
uptime can remain nonzero while the current status is Down; different capture
times/windows must not be treated as contradictory or as our own success rate.
Model-wide availability can also be higher because other providers serve it.

The unchanged context is 262,144 tokens; posted input/output prices remain
$0.10/$0.30 per million tokens. The new
[raw response](verification/helper-nebius-status-20260928/qwen-endpoints.json) and
[endpoint wrapper](verification/helper-nebius-status-20260928/nebius-endpoint.json)
are retained separately from the original snapshot. No credentials were read,
so this investigation neither tests nor diagnoses Brad's account authentication.

## Practical resolution before the comparison

1. Keep the current v3 protocol pinned to Nebius and blocked. Recheck immediately
   before any future run; a fresh status 0 only clears the status condition.
   Complete the existing source/reference/quality, provider behavior/billing,
   spend-control and exact-run requirements in the [v3 runbook](HELPER_COMPARISON_V3.md).
2. To avoid waiting on Nebius, the preferred candidate to investigate is
   **SiliconFlow `siliconflow/fp8` serving the same Qwen model**. In the same public
   endpoint response it had status 0, FP8, a 262,144-token context, the required
   schema/temperature/output-limit parameters and prices of $0.09/$0.30 per million.
   These fit the existing Qwen price ceilings and reservation. OpenRouter's public
   provider metadata declared no prompt retention or training; the exact route was
   also present in its [ZDR endpoint listing](https://openrouter.ai/api/v1/endpoints/zdr).
   The [candidate evidence](verification/helper-nebius-status-20260928/alternative-metadata.json)
   records the declarations and their limitations.
3. Selecting that candidate requires a new reviewed protocol and packet. Keep the
   same model, questions, prompts, score rules and budget; change and disclose the
   provider explicitly. Confirm its applicable terms/distillability and remaining
   behavior/billing requirements before a bounded live test. This investigation
   does not select the candidate, authorize a call, certify provider performance,
   or establish access for our account.

Do not relax the status rule, rotate a key in response to this catalogue flag,
enable automatic fallback, or mix providers within a paired comparison. There is
no local patch that repairs the upstream service. If Nebius remains necessary,
the pinned timestamps, model and route are sufficient context for an OpenRouter
support inquiry; none has been sent.

## Verification and scope

The existing v3 regression suite passed **26 tests**. Two additional offline
probes replayed the actual `-2` and `-5` snapshots through `validate_endpoint`;
both were rejected. The probes used synthetic prerequisite values in memory only
to isolate status checking, prohibited HTTP, and created no live approval. See
the [verification receipt](verification/helper-nebius-status-20260928/verification.json).

All three remote CI checks on Foundry #20 at `8290485` passed. This change adds
documentation and public evidence only: no runtime or protocol changes, no model
calls, no EC2, no training and no production changes. Qwen3-8B remains the SLM
training target; this investigation concerns the hosted 30B helper candidate.
