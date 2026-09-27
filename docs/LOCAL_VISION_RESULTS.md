# Local vision pilot: installation and development findings

27 September 2026. The models are installed in a dedicated local Docker volume.
They are research tools for preparing evidence, not approved engineering readers
or training-data generators. No EC2, paid inference, training, database writes
or production release is part of this work.

## Reproducible setup

- Generic runner: Foundry draft [PR #12](https://github.com/bHBeachsider/slm-foundry/pull/12),
  commit `85dc97772f8471319fbc6709a9bcd70ba8cb5536`.
- Ollama 0.34.4 in a digest-pinned Docker image, internal network, no host port;
  CPU only, eight CPU limit, 10 GiB model-service memory cap, serial inference.
- IBM Granite-Docling-258M digest
  `c4bb6f55fc69f97a51fab35408776a098c6836231b022149e66ed05084d33125`.
- Qwen3-VL-4B Instruct Q4_K_M digest
  `ee4b975b58c17ce268cd19d40db35d5edc64603035d2ffc1fee1968eb0947f7b`.
- Original native templates, licenses and runtime metadata are retained locally
  in each run's `runtime.json`. The existing Foundry Docling converter is unchanged.
- Frozen job SHA-256:
  `ed3d2c0f2a689bee722f34062166965884ed3b0ca72a8500db357a3c692947f7`.
- Three DOE pages (35–37), plus four explicitly fabricated diagrams/records.
  All seven are development-only. References were frozen before model calls.

See the [runbook](LOCAL_VISION_RUNBOOK.md) for commands, the
[input guide](VISUAL_TRAINING_INPUTS.md) for possible training uses, and
`docs/verification/local-vision-pilot.json` for the completed execution receipt.

All 14 requests were attempted exactly once. Failed attempts were not replaced.

| Model | Completed response | Token-limited | Timed out | Mean request time |
| --- | ---: | ---: | ---: | ---: |
| Granite-Docling-258M | 7/7 | 0 | 0 | 37.8 seconds |
| Qwen3-VL-4B Instruct Q4_K_M | 1/7 | 3/7 | 3/7 | 192.9 seconds |

All three Qwen full-page DOE requests timed out. Total recorded request time was
about 27 minutes, excluding installation and between-run work. Peak model-service
cgroup memory, including cache, was **5.379 GiB**. The model service exited cleanly
and remains stopped; model weights remain in its dedicated volume. The network
was verified internal and no host port was published. The voice stack was untouched.

These are response-completion measures, not accuracy scores. Valid JSON and
nonempty document conversion do not establish complete or correct engineering data.

## What the first protocol demonstrates

Granite produced a nonempty completed conversion for all seven images, in about
29–51 seconds per image. That does not mean it recovered every element:

- The DOE pressure page's prose was recovered, but internal diagram labels and
  relationships were omitted.
- It retained the two main absolute/gauge/vacuum equation operators, while
  rendering rho as `p` in the worked calculation and flattening the conversion
  superscript into `10 3`. Those cannot be silently treated as exact notation.
- Several synthetic diagrams were represented as an empty picture region:
  their visible labels were omitted. Both `80 psig` and `80 psia` were copied
  from the conflicting-record fixture.
- Raw conversion output was retained; successful conversion into a full
  DoclingDocument or normalized evidence schema was not established here.

Qwen-VL showed both useful observations and material failures:

- The first full-page DOE request exceeded its 240-second limit. The runtime
  stopped; the six previously unrun IDs were then selected explicitly under
  the unchanged job/prompt/image settings. The timeout was retained.
- Its crossing-diagram response read the equipment labels, but proposed
  connections through a crossing which the drawing legend says is not joined.
  It also reached the token cap, leaving incomplete JSON.
- On the unreadable-tag fixture it used an unlabeled node rather than inventing
  a legible tag, but repeated its connection description until truncation.
- The simple two-equipment fixture returned valid JSON in 89 seconds, retained
  the visible connection and correctly reported direction as unknown. This is
  one software observation, not general engineering acceptance.
- On the conflicting-pressure records it transcribed the two bases but invented
  a relation based on their proximity despite the absence of a drawn connection;
  that response was also truncated.

These are operator/development observations. Bill has not scored this pilot;
formal critical-error counts, engineering accuracy, relation precision/recall
and human correction time remain pending. Literal string coverage can match
prose outside a diagram and must not be labelled engineering accuracy.

## Decision and next work

Keep both models available for experiments; **do not automatically admit these
outputs into training**. Granite is useful for initial document transcription,
but it does not close the diagram gap. Qwen-VL needs a more constrained protocol
and separate connectivity validation before it can be considered for that role.

The v1 settings (greedy decoding, full pages and tight output caps) differ from
the [Qwen publisher's VL recommendations](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct#generation-hyperparameters).
Repetition/truncation therefore describe this model/runtime/prompt/configuration
combination, not the model's best attainable quality. No blended model ranking is
justified: Granite was asked for conversion, Qwen for structured observations.

The next bounded protocol should use short, task-specific questions/regions,
bounded evidence strings, the publisher's sampling recipe and separate checks
for labels versus physical connectivity. Retain v1 failures; use native CAD
connectivity when available, and compare both against independently labelled
reference geometry. Source rights, expert review and release gates remain open.

For Granite, test the documented formula-to-LaTeX and region-conversion tasks on
the known rho/superscript failures, rather than assuming whole-page conversion
preserves them. For Qwen, constrain each request to one task and short evidence;
compare sampling configurations without deleting the original failed outputs.
Those changes are queued as a separate v2 protocol, not silently folded into v1.

## Software verification

- Foundry: **31 new tests; 177 passed** including ingestion/review/admission
  regressions. All three draft-PR CPU acceptance jobs passed at `85dc977`.
- Broadbridge: **12 new tests; 371 passed, 106 skipped** in the offline Python
  suite. Skips are live/database gates. Both repos retain a pre-existing requests
  dependency warning; no dependency upgrade was made to hide it.
- All six DOE image/text inputs matched the upstream source receipt. Hash,
  reference leakage, duplicate-attempt and changed-input checks passed.
- Raw images, model outputs, weights and local runtime files remain outside
  commits. Model outputs have no authority to approve source rights or training.
