# Local voice installation ledger

Scope: install and validate the local speech/interviewer models authorized by Brad on 27 September. Parent design: `../specs/2026-09-27-expert-discovery-design.md`. This is the installation prerequisite to discovery tasks 5–6, not implementation of the questionnaire, job queue or website recorder.

Ruling: use CPU Whisper small.en + Kokoro ONNX + Qwen3-1.7B for this one-person English pilot. The PC has 32 GB RAM, 16 GB allocated to Docker and a 4 GB laptop GPU. CPU execution avoids competing with other GPU apps; measured latency may justify GPU or larger-model evaluation later. The interviewer is not the Qwen3-8B engineering model.

Ruling: execute one lane and self-review, preserving the user's single-lane instruction. Install only isolated containers and named model volumes. No EC2, Railway, production writes or hosted inference.

Ruling: publish no host model port. Verification showed Docker's internal network does not expose the proposed host mapping; all authorized file/turn operations work through the Compose CLI. Keeping the model API inside Docker also fits the future outbound-worker design. Direct host API access would require a separately designed connection.

Ruling: permit executable library mappings in the bounded temporary filesystem, retaining non-root speech execution, no capabilities and the read-only root. The real smoke test failed because phonemizer copies eSpeak's shared library into `/tmp` before loading it; `/proc/mounts` confirmed `noexec`. The corrected offline smoke test passed.

Pre-flight: download and inference use the same pinned model manifest. Normal runtime uses an internal Docker network and read-only speech models; only an explicit install override enables downloads. No repository `.env` is loaded or included in an image.

- [x] Contract tests: six tests observed RED, then GREEN. Final full Python suite: 283 passed, 54 skipped, 13 subtests passed, with database URLs disabled.
- [x] Build pinned CPU speech image; download Whisper, Kokoro and Qwen; retain model and package provenance. Repeated installer succeeded.
- [x] Actual synthetic speech → transcript → follow-up → spoken prompt with network disabled; final in-process smoke 23.829 seconds. Separate warm interviewer call: 1.854 seconds.
- [x] Document start/stop/use and self-review scoped changes in this single lane. See `infra/discovery/VERIFICATION.md`. Changes prepared for the existing draft branch; no production release.

Final review: self-review per the user-requested single lane; no outstanding functional blocker to this installation. Minor retained diagnostic: ONNX cannot persist its telemetry device ID on the read-only filesystem. Telemetry is disabled and runtime egress is blocked; inference succeeds. Website/worker integration and human-voice quality evaluation remain separate tasks.
