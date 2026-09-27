# Local vision development runbook

Use the domain branch `codex/vision-pilot` and Foundry branch
`codex/foundry-local-vision`. Models are installed locally in Docker; no EC2,
OpenRouter/OpenAI calls or training are involved. This run evaluates extraction
proposals, not a fine-tuned model. Keep voice inference idle during the run.

## Prepare once

In Foundry, install the pinned runtime/models using `infra/vision/vision.ps1
Install`. See that repository's `docs/LOCAL_VISION.md` for isolation and limits.
The first installation downloads approximately 3.8 GB of model artifacts. The
Ollama runtime is reused. A second operator needs Docker Desktop and enough free
RAM/disk; this host has 15.45 GiB Docker RAM and uses CPU rather than its 4 GB GPU.

In Broadbridge, install the pinned local PDF/Pillow dependencies into the chosen
Python environment. Use the existing FQ-02 DOE packet, or reproduce it using
`docs/SLM_PREPARATION_REHEARSAL.md`. Preserve originals and source permissions.

```powershell
python -m pip install -r scripts/research/requirements-evidence-review.txt -r scripts/research/vision/requirements.txt
python scripts/research/vision/prepare.py `
  --doe-packet packs/oil-gas/outputs/fq02-doe-pressure-2026-09-27 `
  --out packs/oil-gas/outputs/vision-pilot-2026-09-27 `
  --font C:/Windows/Fonts/arial.ttf
```

The output folder must be new. It holds seven PNGs, native DOE text, the frozen
references, a 14-request job and a provenance receipt. The font hash is recorded;
use the same font/rendering versions for byte-identical synthetic fixtures.
There are five families: all three DOE pages share one family, and each synthetic
challenge has its own. All are development-only, unapproved for training.

## Execute and report

In Foundry, substitute the absolute Broadbridge output directory:

```powershell
.\infra\vision\vision.ps1 Batch `
  -WorkDir 'C:\absolute\Broadbridge4096\packs\oil-gas\outputs\vision-pilot-2026-09-27' `
  -ResultName results-v1
```

Each call has a 240-second timeout; 14 calls have a maximum request budget of 56
minutes plus startup/verification overhead. A timeout stops the batch and runtime,
preserving completed requests and the failure. The initial observed Granite
requests took 29–51 seconds each; the first full-page Qwen request timed out.
These are measurements on this host, not guaranteed wall times.

If a request times out, inspect `summary.json` and explicitly run **only the
previously unrun IDs**, after the wrapper has stopped the model. Example from
this pilot:

```powershell
.\infra\vision\vision.ps1 Batch `
  -WorkDir 'C:\absolute\Broadbridge4096\packs\oil-gas\outputs\vision-pilot-2026-09-27' `
  -ResultName results-remaining `
  -Only qwen-syn-crossing,qwen-syn-unreadable,qwen-syn-direction,qwen-syn-basis,qwen-doe-036,qwen-doe-037
```

In the measured v1 run, DOE page 36 also timed out and stopped that selection.
The final previously unrun request was then attempted separately:

```powershell
.\infra\vision\vision.ps1 Batch `
  -WorkDir 'C:\absolute\Broadbridge4096\packs\oil-gas\outputs\vision-pilot-2026-09-27' `
  -ResultName results-final-page -Only qwen-doe-037
```

Do not change prompts, images or settings silently. Changed conditions require
a separate protocol and report. Keep failed attempts. The selection receipt
records order while retaining the original frozen job hash.

Back in Broadbridge:

```powershell
python scripts/research/vision/prepare.py `
  --out packs/oil-gas/outputs/vision-pilot-2026-09-27 `
  --report packs/oil-gas/outputs/vision-pilot-2026-09-27/results-v1 `
  --report packs/oil-gas/outputs/vision-pilot-2026-09-27/results-remaining `
  --report packs/oil-gas/outputs/vision-pilot-2026-09-27/results-final-page
```

The first results directory receives `coverage.json` and `REVIEW.md`. The report
keeps all 14 planned requests in the denominator and rejects duplicate attempts
across directories instead of choosing a preferred answer. Missing results are
`not_run`; failed/incomplete responses never become successful by aggregation.

## Review and next decision

Inspect original pixels alongside native text, raw Granite DocTags and Qwen JSON.
Record exact tag/unit fidelity, formula signs/subscripts/superscripts, direct
relations, arrow evidence, invented connections, uncertainty and omissions.
Keep software/debugging findings separate from independent engineering acceptance.
Literal text coverage can match prose outside a diagram; it does not prove that
the diagram was understood. Human correction time and technical scores remain
blank until a reviewer actually supplies them.

The initial protocol deliberately froze temperature 0 and tight output/time
limits. It is not the Qwen publisher's recommended VL decoding recipe. The
[official card](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct#generation-hyperparameters)
recommends non-greedy sampling (temperature 0.7, top-p 0.8, top-k 20 and presence
penalty 1.5). Repetition and truncation under the first protocol must not be
presented as a general ranking of the underlying models. A separate v2 protocol
should test that recipe, shorter evidence fields and focused regions/questions,
while preserving v1 failures and the same engineering reference checks.

Accepted corrections can eventually become evidence-linked text/JSON candidates
for Qwen3-8B. Native visual fine-tuning is a different training path, described in
`VISUAL_TRAINING_INPUTS.md`. No example from this pilot is automatically released.
