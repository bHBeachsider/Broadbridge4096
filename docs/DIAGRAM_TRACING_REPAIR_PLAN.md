# Diagram tracing repair experiment

27 September 2026. Brad requested a fix to the recorded connectivity failures. One implementation lane, draft successor PRs; no EC2, training, production, client drawings or downloads. Use only the installed pinned Qwen3-VL model in the dedicated CPU Docker stack.

Hypothesis: the combined v2 task encourages enumerating nearby tag pairs and assigning a default relative direction. Separate undirected route tracing from explicit arrow reading, using literal `from_tag`/`to_tag` instead of relative direction enums. This may improve reading but is an experiment, not a guaranteed model repair.

1. Add two small bounded profiles in Foundry: connections_v3 (direct endpoint pairs only), arrows_v3 (only visible flow-arrow endpoints). Preserve v2 prompts/sampling/schemas and all old results. Each new call has the existing 180-second timeout; keep installed model pins and sampling, 384 output-token cap.
2. Add a deterministic composer. Direction defaults to unknown; explicit arrows must match a traced direct connection. Reject inconsistent/duplicate/mismatched-image results, retain uncertainty, and keep training_approved false. The composer never reads a reference graph or deletes a wrong edge to improve a score.
3. Use the same six qualified image bytes (corrected crossing plus five original controls/failures), two calls per image, **12 requests total**, once each, sequentially. Do not expose reference graph, model specification, expected answers or old model answers in either prompt. These are development fixtures, not a held-out benchmark or engineering sign-off.
4. Freeze jobs/prompts/images and independent references before execution. Compare exact edge/direction counts and unsupported claims to saved v2. Failed/incomplete calls score as empty predictions. Preserve all attempts; no best-of-many selection. If the experiment still fails, report the remaining gaps rather than claim that validation equals model correction.
5. Run profile/composer/replay regression tests and the impacted CPU suites, review the changes, publish draft successors, and stop the dedicated vision stack in finally. Keep voice service unchanged.

Reference-source gaps are outside this repair: C01's four missing endpoints and absent direction evidence must remain null/unknown. Native-model or independently signed tracing remains necessary for real drawing acceptance. No image-derived graph can certify itself.

## Recorded follow-up decision, before further inference

The first five v3 calls missed obvious connections/arrows on the forward/reverse/junction drawings. Preserve the full twelve-call run and do not promote v3. Add **four** v2 calls on disclosed two-times enlarged crops: the three original failures (reverse-chain, corrected crossing, mixed-junction) and forward-chain as control. Keep the original v2 prompt, schema, sampling and model; change only image framing/scale. Crop boxes are chosen from the visible drawings, retain all labeled nodes and routes, and remove captions/footer. Bind each crop to its parent bytes, rectangle, transform and separately carried reference. Maximum total this task: **16 calls**, no retries. Report this as a development follow-up selected after v3 regression, not a held-out improvement claim. A remaining failure ends this bounded experiment; do not search indefinitely for a passing prompt.

## Completion and review ledger

Both batches completed within the sixteen-call bound; neither repaired the errors. [Results and all limitations](DIAGRAM_TRACING_REPAIR_RESULTS.md). The dedicated vision stack is stopped. No promotion or training approval.

Fresh read-only review: two important provenance findings, fixed after reproducing failures in tests. New jobs bind the full evaluation payload; crop reports require the pinned model digest. The original run is retained with an explicit retrospective evaluation pin and canonical historical comparison rather than rewritten as though its initial binding had been stronger. Cost of that decision: this initial run remains weaker provenance evidence; it is a negative development experiment only.

Deferred minor: crop-lineage sidecar integrity. It remains supplementary to the image/reference data pinned by the job; future experiment formats should pin the entire sidecar. No source permission or engineering acceptance is delegated to it.
