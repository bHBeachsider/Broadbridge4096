# Bill meeting: show useful behavior, then choose a real task

30 September 2026. A 20–30 minute Google Meet discussion; no AWS session needed. The local walkthrough is an authored, deterministic prototype, not Qwen inference. The future run is **20 optimizer steps**, not 20 independent cases.

## Open before the call

1. [Local walkthrough](demos/bill-pressure-walkthrough.html). Open in a browser and share the window. Runs offline; download notes before closing. It does not save to the database.
2. [Engineering training review](https://broadbridge-capture.vercel.app/questionnaires/pressure-training-v1) — live questionnaire, illustrated reference examples and database-backed feedback.
3. [Public-data review](https://broadbridge-capture.vercel.app/review/public-v1) — actual saved model answers against evidence. State the model/run displayed by the packet; these are not the yet-unrun Qwen fine-tuning comparison.
4. [Case Capture](https://broadbridge-capture.vercel.app) — priorities and actual cases. Bill uses his approved email address. Page links themselves do not expire.

Only the Vercel links are remotely accessible. A local-file or localhost link works on Brad's PC; screen-share the walkthrough. Nothing new was deployed by preparing this meeting.

## Meeting sequence

Suggested opening: “I want to show how we can turn source material into a reviewable engineering answer, and how your feedback can teach the system what to check. Then let's choose one task worth proving on a real job.”

| Time | Show / do | Purpose |
| --- | --- | --- |
| 0–3 min | **Known reference**: note and summary use different pressure bases; change a value. | Make the reasoning inspectable. A fixed rule illustrates the desired behavior, not model skill. |
| 3–6 min | **Missing basis**, then **Unsupported conclusion**. | What should the assistant ask, and when should it withhold a conclusion? |
| 6–9 min | Source and one actual saved public-data answer; include errors. | What does the evidence support? What did the model miss? |
| 9–12 min | **Teach & compare**: 36 candidates → proposed 20-step adapter → eight base/adapter pairs. | Explain the experiment without inventing before/after results. |
| 12–25 min | **Choose the first job** and live questionnaire. Bill may replace pressure checking. | Define inputs, output, missing evidence, critical errors and success criteria. |
| Last 3 min | Agree one small contribution. | One anonymized case or document package with identifiable ownership. |

Pressure arithmetic is easy to audit; it is not the commercial differentiator. The larger opportunity to test is preparing traceable review drafts, organizing evidence across a document package, and asking useful questions on unusual cases. Productivity and revenue gains remain hypotheses.

Ask for a specific task: “Given [inputs], help [person] prepare [output] for [decision].” Follow with: what is misleading; what observation changes the conclusion; what convincing answer is dangerous; what remains an engineer's decision; and what would prove time saved or improved quality. Ask which case Norm could clarify initially. Private archives are not required for this conversation.

## Voice capture: what works today

On 30 September, Docker reported `broadbridge-voice-interviewer-1` **running and healthy**, without a published host port. The installed pipeline uses Whisper small.en (transcription), Qwen3-1.7B (follow-up questions) and Kokoro (spoken prompts). Its recorded 27 September synthetic smoke test passed. Today's container status is not a new human-speech accuracy test.

A fresh 30 September local smoke also passed: a 15.22-second invented pump-datasheet note was spoken, transcribed, used for one follow-up question and answered with synthesized speech in **24.915 seconds** (in-process measurement, excluding Docker startup/checksum overhead). The transcript retained `12 bar`, `10 bar` and the revision uncertainty. The actual follow-up was: “What was known at the time regarding the revision history of the pump data sheets and drawings?” This is a real local model result on synthetic audio, not Bill's speech or proof of engineering correctness. [Saved result](evidence/bill-meeting-2026-09-30/voice-smoke.json).

The source audio and spoken follow-up are in the discovery worktree at `infra/discovery/runtime/meeting-smoke-20260930/synthetic-input.wav` and `follow-up.wav`. Play these two short clips during the call if useful. The normal runtime network was verified internal; existing pinned images/models were reused without downloads. The one-off speech container exited; the already-running interviewer was preserved. A preliminary command used an unsupported `--no-build` flag and was corrected before the successful run. ONNX emitted its previously documented read-only telemetry-ID warning; inference succeeded with telemetry disabled and no network egress.

**The website recorder, transcription queue and Google Meet interviewer integration are not implemented.** The production deployment remains the pressure questionnaire. There is no current button that records a call and inserts it into the knowledge base. Do not assume a microphone-only recorder captures Bill's remote audio.

1. Confirm Bill agrees to recording/transcription before starting.
2. Check Google Meet's recording/transcript controls before the call. Availability depends on the organizing account and administrator settings: [Google recording requirements](https://support.google.com/meet/answer/9308681?hl=en), [transcript controls](https://support.google.com/meet/answer/12849897?hl=en). Brad's subscription has not been checked, and no recording was started.
3. If unavailable, use notes and the live questionnaire for the first discussion, or an already available recording service after confirming its capture/storage arrangement. No new service purchase is needed.
4. Preserve the original privately outside Git. Local speech accepts audio clips of **15 minutes / 50 MiB maximum**. Longer Meet recordings need explicit audio extraction/segmentation; arbitrary meeting video is not accepted as-is. No speaker identification is installed. Never silently truncate.
5. Check names, equipment tags, numbers, units and speaker attribution. Summarize proposed tasks, assumptions, exceptions, follow-up questions and unresolved issues with timestamp references. Bill reviews the interpretation.
6. Enter confirmed priorities in A8 and the questionnaire. Actual cases use separate capture/sign-off. Recording consent, summary confirmation, source permission and training acceptance remain distinct.

Installed PowerShell commands:

```powershell
$voice = 'C:\Users\bradu\.codex\worktrees\codex-expert-discovery\Broadbridge4096\infra\discovery'
& "$voice\voice.ps1" -Action Status
# Saved supported audio clip, within the limits:
& "$voice\voice.ps1" -Action Transcribe -InputFile 'C:\path\meeting-segment.wav'
# One short reviewed excerpt; maximum 6,000 characters:
& "$voice\voice.ps1" -Action Ask -Text 'Reviewed, non-sensitive excerpt to clarify'
```

These commands do not join Meet, record the microphone or upload to the website. Do not use Windows Ollama or the EC2 tunnel for the local voice stack.

## Training preparation and remaining gates

The review bundle validates all six prepared artifacts and emits `execution-request.json`. Approval, release and host-packet hashes remain null. It describes the 20-step / 1,800-second training limit, up to 16 generations / 900 seconds, and the unchanged 90-minute host limit. It cannot launch training.

Rights and whole-family allocation remain pending. After those decisions, the exact examples must enter the immutable release workflow. The training-capable host payload still needs integration and rehearsal against that release; the load-only controller cannot execute this demo. Finally Brad approves the actual packet and fresh session. The meeting can happen now without closing these gates or inventing Bill's signature.

Rebuild without models, network, credentials or cloud access:

```powershell
$domain = 'C:\Users\bradu\Documents\Broadbridge4096\tmp\codex-broadbridge-ingestion-plan'
python "$domain\scripts\research\prepare_bill_meeting.py" `
  --package "$domain\packs\oil-gas\outputs\pressure-demo-v1" `
  --out "$domain\packs\oil-gas\outputs\bill-meeting-20260930"
```

Use a fresh output directory on repetition. Earlier notes/receipts are preserved. See [training package details](DOE_TRAINING_DEMO_PACKAGE.md) and [retained-cache preparation](AWS_CACHED_TRAINING_PREPARATION.md).
