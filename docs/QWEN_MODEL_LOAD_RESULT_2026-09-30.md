# Qwen checkpoint and GPU-load result

30 September 2026 UTC / 29 September evening Eastern. **Passed: the pinned Qwen3-8B checkpoint is now retained on the existing A10G host and loaded successfully in NF4.** This establishes model-loading readiness, not a trained Broadbridge adapter or a serving endpoint.

| Check | Actual result |
| --- | --- |
| Source | `unsloth/Qwen3-8B`, revision `946bc9ac74a6c1f8cf012497c503a119b2fcf2eb` |
| Verified checkpoint | 15 files, 16,397,438,697 bytes; all recorded hashes and sizes matched |
| GPU | Existing `i-079b24e2b51ef7630`, g5.2xlarge, NVIDIA A10G, us-east-1b |
| Runtime | Existing pinned venv; installed versions rechecked; no package or driver changes |
| Load | NF4, 2,048 configured context, 252 NF4 linear modules, all parameters on CUDA |
| Load time | 4.178 seconds after acquisition and verification; excludes those earlier phases |
| Peak GPU memory | 6,188,362,752 bytes allocated; 6,259,998,720 bytes reserved (5.83 GiB) |
| Model operations | Zero inference calls, optimizer steps or adapters |
| Offline checks | 7 diagnostic + 7 admission-guard + 19 controller tests passed; two fail-closed shell checks and Bash syntax passed |
| Session | One accepted start at 00:52:39 UTC; load completed 00:56:13; stopped confirmed 01:00:30 (7 minutes 51 seconds total) |
| Shutdown | Guest minute-80 and independent minute-85 guards armed; early graceful stop followed by the bounded forced-stop fallback; all three retained hosts independently confirmed stopped |
| Automation | Paused; no further paid session scheduled |

[Machine-readable result and artifact hashes](evidence/aws-runtime-bundle-2026-09-28/qwen-model-load-2026-09-30.json).

The preflight now records GPU PID/process/service details before enforcing the busy check. Busy, unknown, missing or contradictory telemetry blocks model work. The existing hardware and second busy assertion remain intact. The original 259 MiB busy condition did not recur on the diagnostic boot or this load boot; its process identity remains unknown. No GPU process was killed and no service was stopped or disabled.

The weights remain under `~/slm-training/hf-cache-qwen-946bc9ac74a6c1f8cf012497c503a119b2fcf2eb` on the A10G EBS volume. The model was unloaded after inspection and the host is stopped. In a later authorized bounded session, run the existing `verify` and `load-check` operations against that cache. Do not rerun `fetch`: its fresh-cache refusal prevents accidental replacement/redownload. Reverify the host, runtime, cache hashes and ownership before reuse.

The published source archives were Foundry `e3b7e31dfe5ae0e54b58f2fdcca2ff4ee1c34d67` and Broadbridge `f65fe0060cde809cc9d3dd4509b01e7d8f0fb744`. Private session-controller/preflight sources, test outputs and logs are retained in Foundry `outputs/qwen-load-session-20260930-guarded/`; their hashes are bound in the receipt. This session reran the 33 private tests, not the previously recorded 850-test Foundry suite. The checkpoint CLI and runtime packages were unchanged.

Next gates remain accepted task/data and source rights, scored S0 baselines, a bounded QLoRA/checkpoint-resume smoke test, and second-operator reproduction. Peak load memory does not prove training memory requirements or engineering quality. No datasets, database/R2 operations, model evaluation, training, production changes or merges occurred. Diagram-training admission remains blocked separately.
