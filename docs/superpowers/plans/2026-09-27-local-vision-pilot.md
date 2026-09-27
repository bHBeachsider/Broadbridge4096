# Local vision ingestion pilot

Approved by Brad: proceed with the vision companions; test locally in Docker.
One execution lane. No EC2, paid inference, production changes or training.

## Tasks and acceptance

1. Pin Ollama, Granite-Docling-258M and Qwen3-VL-4B Instruct Q4_K_M. Install in
   a dedicated model volume. Download network is temporary; inference network
   is internal, with no published ports. Preserve the voice stack.
2. Foundry: add a local image client and bounded batch CLI, tests first. Verify
   image hashes and model digests; preserve errors, incomplete output, native
   DocTags, JSON proposals and provenance. No output grants training rights.
3. Broadbridge: freeze three existing DOE pages and four fabricated diagram
   fixtures before inference. References are development checks, not Bill's
   acceptance. Rights remain pending on DOE material. Synthetic families stay
   out of training. Record crossing/junction, unreadable tag, absent direction
   and conflicting pressure-basis expectations.
4. Run both models on all seven images, sequentially on CPU. Granite uses its
   documented conversion prompt, Qwen a structured observation prompt. Native
   DOE text is the baseline. They have different tasks; do not rank them from
   a single blended score. Bound each response by context, tokens and time.
5. Record outputs, model/runtime hashes, latency, cgroup peak memory and failure
   counts. Review readability, label fidelity, relationships, formulas and
   uncertainty. Keep expert correctness and correction-time fields pending.
6. Add reproduction commands, focused regression results and draft PRs in both
   repos. Stop only this pilot's containers when finished; retain model volume.

## Limits

Current text Qwen3-8B can consume reviewed text/JSON derived from images. Native
image fine-tuning requires a vision-language model and image/prompt/answer
examples. CAD topology, geospatial coordinates, video timing and audio need
their own parsers/evaluations. No claim of universal visual comprehension.

## Execution log

- 2026-09-27: separate `codex/vision-pilot` and
  `codex/foundry-local-vision` branches selected from clean worktrees.
- Confirmed Docker CPU runtime, ~15.45 GiB Docker RAM, ~153 GiB free host disk.
- Public model manifests pinned before download. Reuse installed Ollama image;
  existing Docling 2.130.0 pipeline is unchanged.
- Downloaded both models and verified full digests; inference network inspected
  as internal with no host port bindings. No voice stack modifications.
- Foundry client tests: 24 expected pre-implementation failures, then green;
  expanded to 31 offline tests including explicit remaining-run selection.
  Related ingestion/review/admission regression suite: 177 passed.
- Domain tests added for frozen references, no answer leakage, complete run
  denominators, duplicate-attempt refusal and source-receipt binding. All six
  frozen DOE text/image files independently matched the upstream receipt.
- First Qwen full-page call timed out at 240 seconds. Runner stopped the batch
  and runtime. Explicitly selected the six previously unrun IDs in a new results
  directory, retaining original job/image/prompt hashes and the failed attempt.
- Foundry draft PR #12 at 85dc97772f8471319fbc6709a9bcd70ba8cb5536:
  all three CPU acceptance checks passed. No merge or production release.
- Native Granite output is retained as a proposal; this pilot does not claim a
  successful DoclingDocument parse or normalize its output into training rows.
- Completed all 14 planned attempts exactly once: Granite 7 completed; Qwen 1
  completed, 3 token-limited, 3 timed out. Three explicit selections retained
  the same frozen job; no failure was overwritten. Peak cgroup RAM 5.379 GiB.
- Final domain regression: 371 passed, 106 live/database skips, one pre-existing
  dependency warning. Twelve new domain tests; source-chain checks passed.
- Pilot model service verified stopped with internal network and no published
  port. Weights retained. Report, raw receipts and blank technical review sheet
  saved; no training examples released. A more constrained v2 protocol is queued.
