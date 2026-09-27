# Local voice installation — 27 September 2026

Installed and exercised on Brad's Windows PC, using Docker Desktop's Linux engine. Host RAM: 32 GB; Docker allocation: about 16 GB. Qwen reported **100% CPU**, 4,096-token context and 1.9 GB loaded model memory. No EC2 or hosted inference was used.

## Results

| Check | Result |
|---|---|
| Six new offline contract tests | Initially failed with the implementation absent; then all passed |
| Full Python regression suite, `python -m pytest -q` | **283 passed, 54 skipped, 13 subtests passed**, 58.38 seconds; database URLs disabled |
| PowerShell script syntax | Passed |
| Repeat `voice.ps1 -Action Install` | Passed; cached model files reused and hashes checked |
| `Stop` then `Start` | Passed, model volumes retained |
| Final `Smoke` on an internal Docker network | Passed with actual Whisper, Qwen and Kokoro |
| Actual Docker host port bindings | `{}` — no published model port |
| Runtime network | `internal=true`; no Internet route |
| Existing Windows Ollama | Still listening on its original localhost:11434 |

The synthetic input described conflicting pump datasheets: twelve bar in one document, ten bar in another, with uncertainty about the correct revision. Whisper retained both numbers and the unit as `12 bar` and `10 bar`.

Final smoke timing, after a container restart (OS file caches already warm):

| Stage | Time |
|---|---:|
| Generate 15.22 seconds of invented source speech | 5.491 s inference |
| Transcribe the recording | 2.099 s inference |
| Load/run Qwen and generate a question | 10.272 s |
| Generate 5.215 seconds of spoken follow-up | 2.093 s inference |
| Complete in-process smoke, including imports/loading | 23.829 s |

The first run took 43.454 seconds, including a 23.877-second interviewer call. A separate already-loaded Qwen call took 1.854 seconds. These are small pilot measurements, not service-level guarantees; Docker command startup and checksum verification add time outside the in-process smoke timer.

The sample follow-up was:

> What was known at the time regarding the revision history of the pump data sheets and drawings?

It included an exact evidence quote from the transcript and remained marked `needs_review`. This test verifies component integration on synthetic speech, not accuracy on Bill's voice, accents, noisy recordings or engineering terminology. It is not training admission or technical sign-off.

## Installed artifacts

- Qwen model digest: `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
- Speech image ID: `sha256:f96774802faaf1c1d4d7120629683fe3f1d2bc9909c1728838a3b2a23cda681d`.
- Model volumes: about 1.3 GiB for Qwen and 802 MiB for speech. Speech image: 843 MB; Ollama image: 9.28 GB including bundled runtimes. Docker also retains build cache; these numbers are not additive unique disk usage.
- Private local output: `runtime/smoke/synthetic-input.wav`, `follow-up.wav`, `smoke.json`. These files and installation logs are Git-ignored.

## Review and limits

Self-reviewed in the user-requested single implementation lane. Reviewed installer cleanup, explicit online/offline boundaries, model checksums, separate speaker/model roles, named-volume retention, build-context exclusions and draft-output handling. Full Python regression suite remained green.

One real smoke failure was corrected: phonemizer copies a shared eSpeak library into a temporary directory, so its bounded temporary mount must allow executable mappings. Speech still runs without root privileges or Linux capabilities, with a read-only root filesystem.

Minor retained diagnostic: ONNX Runtime emits a startup message that it could not persist its telemetry device ID on the read-only filesystem. Telemetry is explicitly disabled and the runtime network cannot reach the Internet; inference succeeds. No website recording, job-queue integration, human-audio acceptance or fine-tuning was performed.
