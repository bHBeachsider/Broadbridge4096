# Which diagram errors remain

**Update, 27 September:** the [bounded repair experiment](DIAGRAM_TRACING_REPAIR_RESULTS.md) tested separate route/arrow prompts and enlarged crops. Neither repaired the recorded errors; v3 is not promoted. The checker still blocks these outputs from training.

The [frozen reference-graph pilot](REFERENCE_GRAPH_RESULTS.md) identifies three separate model failures. These are Qwen3-VL extraction failures on small local test drawings, not results from fine-tuning the text Qwen3-8B model.

| Failure | Observed evidence | Required correction / acceptance condition |
|---|---|---|
| **Joining pipes that merely cross** | Corrected crossing drawing: two real edges recovered, two nonexistent cross-connections added; 50% edge precision | Distinguish junctions from bridge/no-join crossings using the drawing legend and native graph. Require exact port/line matches; no extra edges on the reviewed crop set. A crossing without enough evidence stays unresolved. |
| **Reversing flow arrows** | Reverse-chain drawing: correct two connections, both flow directions reversed | Inspect arrowheads independently from endpoint identification. Compare with native flow attributes or signed tracing. All explicit arrows must match; left-to-right visual order is not evidence. |
| **Inventing flow direction** | Mixed-junction drawing: two direction claims on connections whose source supplies no arrow | Return `unknown` where the reference has no supported direction. Do not infer it from component position or a plausible engineering story. Count unsupported claims separately from known-direction accuracy. |

The no-arrow chain correctly retained unknown directions and requested review. That is a useful outcome, not a reason to force a direction into the graph. Valid JSON alone cannot establish correct connectivity.

There are also **source/mapping gaps**, distinct from the model failures:

- DEXPI C01 has 31 segment connections, four with missing endpoints and no explicit known flow directions in our mapped source. Preserve null endpoints and unknown flow; resolving them needs additional source information or an independent signed tracing. Do not score guessed directions as gold.
- The sampled PID2Graph member has undirected annotation edges. Its graph has not been approved as physical piping connectivity. Symbol adjacency, signal lines and fluid connections cannot be treated interchangeably without a reviewed mapping.
- Unmapped DEXPI classes fail explicitly. Additional mappings need tests and reviewer acceptance; they must not silently drop equipment or invent ports.

Next diagram experiment: test a dedicated line/arrow tracing stage on a small **new development set** from licensed native models with explicit ports, arrows and crossing conventions. Preserve image/graph/seed and drawing revision. Have a qualified reviewer accept render quality and the graph mapping; compare deterministic pixel tracing and explicit arrow detection against that independent reference before introducing any richer model. This is a hypothesis to test, not an implemented repair. Use separate locked evaluation families for any later effectiveness claim; tuning against these pilot drawings makes them development data.

For eventual training admission, all required connections/directions in each accepted example must agree with its trusted reference, unsupported claims must be absent, and unresolved endpoint/mapping issues must be resolved or the example excluded. Confidence scores cannot waive this condition. Human-traced references need independent sign-off; model output can propose a tracing but cannot certify itself.

Text, calculation and document-source preparation can continue while these visual issues are unresolved. The linked repair experiment used 16 bounded local CPU calls; no training, EC2 or production changes occurred.
