# Local speech and interviewer pilot

This installs local models for an explicit, one-question-at-a-time interview. It does not install a fine-tuned engineering model, connect the website recorder, claim database jobs, or approve material for training. No cloud inference credentials are required.

| Purpose | Installed model/runtime | License |
|---|---|---|
| English transcription | Whisper small.en, faster-whisper, CPU int8 | MIT |
| Follow-up questions | Qwen3-1.7B Q4_K_M through isolated Ollama | Apache-2.0 model; MIT runtime |
| Spoken questions | Kokoro v1.0, ONNX CPU, stock `af_sarah` voice | Apache-2.0 weights; MIT wrapper |

Model revisions and upstream artifact checksums live in `models.json`. The speech volume records every downloaded file's hash and the Ollama model digest. Runtime verifies these before use. Official sources: [Whisper runtime](https://github.com/SYSTRAN/faster-whisper), [Qwen](https://ollama.com/library/qwen3:1.7b), [Kokoro weights](https://huggingface.co/hexgrad/Kokoro-82M), [Kokoro ONNX](https://github.com/thewh1teagle/kokoro-onnx). eSpeak NG supplies phonemization under GPL-3.0-or-later; review all bundled dependencies before redistributing container images.

## PowerShell commands

Run from this directory with Docker Desktop's Linux engine running. Python/model dependencies are contained inside Docker.

```powershell
.\voice.ps1 -Action Install    # first install; explicit public model downloads
.\voice.ps1 -Action Smoke      # synthetic voice -> transcript -> question -> spoken question
.\voice.ps1 -Action Ask -Text "We lose time reconciling pump data sheets and drawings."
.\voice.ps1 -Action Speak -Text "Which part of that review takes the most time?"
.\voice.ps1 -Action Transcribe -InputFile "C:\path\recording.wav"
.\voice.ps1 -Action Stop       # release runtime memory; preserve installed models
.\voice.ps1 -Action Start
.\voice.ps1 -Action Status
```

`runtime/smoke/follow-up.wav` contains the spoken synthetic follow-up; `smoke.json` records timings, source text, draft transcript and separate interviewer output. This directory is Git-ignored. `Speak` writes `runtime/prompt.wav`; `Transcribe` retains a uniquely named local input copy and prints the draft transcript. File commands do not record the microphone or upload anything. Stop the stack when not needed; it does not auto-start after reboot.

## Boundaries

- The model API is available only inside this project's private Docker network (`http://interviewer:11434`). No host port is published. Use `voice.ps1` to invoke it. The existing Windows Ollama `11434` and EC2 tunnel `11435` are untouched. Bill's remote browser will use the authenticated website and future job worker, never Ollama directly.
- Normal Compose uses an **internal Docker network** with no Internet route, cloud inference disabled and offline Hugging Face. `compose.install.yaml` enables public downloads only during installation; the installer removes that network afterward. There is no hosted fallback.
- The two named volumes are `broadbridge-voice_interviewer-models` and `broadbridge-voice_speech-models`. `stop`/`down` preserve them. Do not use `down -v` unless deliberately uninstalling these models.
- CPU execution is capped at six CPUs and 4 GiB per container. Only Ollama remains running; speech commands are temporary containers. Initial model loading adds latency, and concurrent desktop workloads affect it.
- The speech container has a read-only root filesystem and no Linux capabilities. Its bounded `/tmp` mount permits library loading because phonemizer copies eSpeak there before loading it; this is required for speech generation. ONNX and Hugging Face telemetry are disabled, and the runtime network has no Internet route.
- This English pilot accepts at most 15 minutes/50 MiB of audio. One interviewer turn accepts at most 6,000 characters; larger transcripts must be segmented explicitly. No speaker identification or live interruption handling is installed.
- The interviewer prompt requests a neutral question and validates a verbatim quote from the participant. These checks cannot prove neutrality, domain correctness or immunity to prompt injection. All output is a draft requiring human review. Numbers, units and equipment tags in transcripts require checking against the recording.
- The smoke test uses Kokoro-generated invented testimony. It proves local component integration, not accuracy on Bill's speech or a petrochemical benchmark.
- Next integration: authenticated questionnaire recording, outbound job queue, transcript correction and participant-controlled follow-ups. Bill will use the website; it will not require exposing this PC publicly.

## Offline tests

```powershell
python -m unittest discover -s tests -v
```

No production environment file is mounted or copied. The Docker build context includes only the explicit runtime files, excluding recordings and credentials.
