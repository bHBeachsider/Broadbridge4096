# AWS continuation: retained checkpoint to first training demonstration

30 September 2026. **Preparation only; no EC2 start, inference or training.**

Meeting follow-through: [Bill's screen-share runbook](BILL_MEETING_RUNBOOK.md) now ties the prepared candidates to a four-part interactive reference walkthrough, live feedback links and a truthful voice-capture status. The local review-bundle validator passed; its execution request leaves release/approval/host-packet fields empty. This does not complete the training-capable host integration in step 3 below.

## Current host status

At 14:43 UTC (10:43 a.m. Eastern), read-only AWS queries confirmed:

| Instance | Hardware | Zone | State |
| --- | --- | --- | --- |
| `i-079b24e2b51ef7630` | g5.2xlarge / A10G | us-east-1b | stopped |
| `i-0e5e1cbc7b1367566` | g6.2xlarge / L4 | us-east-1d | stopped |
| `i-0439f5841d631d9f8` | g6.2xlarge / L4 | us-east-1c | stopped |

No running/pending G or VT instances were returned in us-east-1. The 15-minute retry automation is paused. Stopped-state checks do not prove what capacity AWS will offer on a future start. Retained EBS storage still incurs charges.

The A10G's [successful checkpoint session](QWEN_MODEL_LOAD_RESULT_2026-09-30.md) already verified all 15 files and an NF4 CUDA load. Those files remain on its retained disk. Hardware/model loading is complete for that earlier session; no Broadbridge adapter has been trained.

## Engine change prepared now

The generic Foundry trainer can bind to the retained checkpoint with `model.offline_cache`. It verifies the pinned inventory and all model files before GPU imports, requires the dataset audit to use that snapshot's tokenizer, sets offline library controls, and supplies explicit local-only loader options. Its cache binding is included in the existing training-authorization configuration hash. A missing or changed cache fails instead of fetching another model.

Keep the base repository and revision unchanged:

```yaml
model:
  base: unsloth/Qwen3-8B
  revision: 946bc9ac74a6c1f8cf012497c503a119b2fcf2eb
  offline_cache:
    directory: /home/ec2-user/slm-training/hf-cache-qwen-946bc9ac74a6c1f8cf012497c503a119b2fcf2eb
    inventory: /home/ec2-user/slm-training/SESSION/domain/inventory.json
    inventory_sha256: ae69d76c4b5b18ac823687ee0df2bbc45ba12c030f9147970e51f799a0107ee5
```

This is an operator fragment, not an executable training config. `SESSION` must be replaced by the fresh, staged session directory before computing the resolved configuration hash. Use the inventory already in `docs/evidence/aws-runtime-bundle-2026-09-28/qwen-base-inventory.json`. Audit tokenizer path: the cache's `models--unsloth--Qwen3-8B/snapshots/946bc9ac74a6c1f8cf012497c503a119b2fcf2eb` directory. Keep AWS's validated Transformers 5.5.0 runtime; do not install the PC's 5.9.0 version.

This code has CPU/mock validation only until its first authorized GPU execution. It adds no AWS start, installation, model download, release approval or automatic training behavior. The load-only host controller remains load-only.

Validation: **971 Foundry tests passed, 12 skipped**, with three existing Requests/SWIG warnings. Tests cover the exact cache options at the trainer boundary, bad/missing files, a mismatched tokenizer, changed authorization bindings and retained legacy behavior. Domain documentation links and whitespace checks passed. The two AWS status queries above were read-only; no host or automation state was changed.

## Remaining path to the demonstration

1. Record the source-use basis for the exact three DOE pages and the whole-family move into demonstration training. Rights remain TBD. The former pressure diagnostic and related DOE-HDBK-1012 material then cannot count as independent evaluation.
2. Review/release the exact [36 prepared conversations](DOE_TRAINING_DEMO_PACKAGE.md) through the existing admission workflow. Questionnaire feedback can improve them but does not itself grant source rights or sign cases. Keep the eight comparison probes labeled non-independent.
3. Finish and rehearse the training-capable host packet: immutable source/release/config bindings, retained-cache verification, exact on-host rendering/masks, pre/post comparison commands, checkpoint capture and fixed shutdown controls. Do not substitute the old load-only packet or invoke an unbounded trainer directly.
4. Approve that exact packet for one A10G session: at most 90 minutes, 20 optimizer steps / 1,800 training seconds, at most 16 generations total / 900 comparison seconds. Retain the minute-78 work cutoff and minute-80/85/87/90 shutdown controls; stop early on completion or failure.
5. Report all eight before/after pairs, actual failures and checkpoint evidence. No quality-improvement claim until scored; real checkpoint resume and second-operator reproduction remain separate checks.

Nothing in this document fabricates Bill's signature or source permissions. The [live questionnaire](https://broadbridge-capture.vercel.app/questionnaires/pressure-training-v1) supplies the feedback route, and the commercial branch contains the updated unsent email.
