# Diagram success targets and qualification contract

28 September 2026. These are proposed project acceptance gates, not ISA
certification or a claim of production accuracy. Bill/the appointed technical
reviewer must ratify the task scope and drawing conventions. The executable
thresholds live in `packs/oil-gas/manifests/diagram_metric_contract.json`.

| Metric | Numerator / denominator | Vector PDF/DXF pilot target | Raster pilot target |
|---|---|---:|---:|
| Edge precision | correct predicted edges / all predicted edges (TP+FP) | 99.5% | 99% |
| Edge recall | correct predicted edges / all reference edges (TP+FN) | 95% | 90% |
| Direction precision | correct direction claims / ALL direction claims, including claims on false/unknown edges | 99.5% | 99.5% |
| Direction recovery | correct directions / pre-frozen eligible reference directions | 95% | 90% |
| Evidence completeness | edges satisfying all path/arrow rules / emitted edges | 100% | 100% |
| Critical errors | false edges at non-connections, reversals, unsupported directions, failed evidence | zero observed | zero observed |

Report counts and two-sided 95% Wilson intervals for the four rates. Zero
denominators are null/unknown, never zero error or a pass. Show unknown directions,
missed directed edges and checker-rejected drawings separately. Error categories
can overlap; their sum counts flags, not unique incidents. Crossing FP counts in
the current harness are category-level flags, not localized intersection diagnoses.

Always report raw proposals and evidence-accepted graphs side by side. A checker
rejection protects downstream use but does not erase extraction errors; a rejected
whole graph still loses recall in accepted results. Direction coverage (known claims
over reference directions) is not accuracy, and neither is correct/known claims
the same as direction precision. The legacy report is retained unchanged for audit.

## Point performance is not qualification

A pilot may reach the point targets on a regression set and still be unqualified.
23/23 correct predicted edges has a Wilson lower bound of 85.69%; 23/24 recall,
79.76%; 7/7 correct directions, 64.57%. Even 750/750 gives 99.4904%, below 99.5%.
765/765 gives 99.5004%: this is the minimum all-correct **independent Bernoulli**
denominator for that bound, not a promised required drawing count. One error
requires a larger denominator. Direction claims have their own denominator.

For qualification, each lower bound must meet its target AND the non-statistical
gates must close. Thousands of edges from one layout do not create thousands of
independent trials. Formats, crops, revisions and generated variants remain in
the same family. Report per drawing/family and route; preregister a cluster-aware
uncertainty analysis with adequate independent families. The edge-level Wilson
interval is descriptive until that review. Never pool PDF/DXF/PNG siblings to
inflate confidence. Reserve unseen families before development; do not relabel
the existing twelve stress drawings as held out. A repeat replay demonstrates
reproducibility, not a second independent validation.

Eligibility of clearly visible arrows and visually ambiguous breaks must be
reviewed and pinned BEFORE a new freeze. Keep all-edge recall alongside eligible
subsets. The existing break fixture remains a miss in every report: its source
model contains continuity that the visible gap does not establish.

## Bill's convention and task checklist

For each supported plant/drawing family, record the legend/revision and examples:

- Which crossings connect? Which tees connect without a dot? What does a hop or
  break mean? Can a break establish through-continuity, and by what symbol/legend?
- Which arrows indicate process flow, instrument signals, or something else?
  What should happen with conflicting arrows, reversals, or an unreadable mark?
- How do off-page connectors match tag, sheet and drawing revision? Which
  equipment/nozzle ports, reducers and instrument bubbles are real graph nodes?
- Which errors could materially mislead an engineer? When must the tool abstain
  and ask for a better drawing or review instead of emitting a connection?
- What is the first useful task: tracing a selected line, checking a package, or
  answering a bounded operating question? Define its accepted formats and scope.

Reference tracers work from the source/model before seeing detector output;
Bill/another independent reviewer signs it. A later overlay correction creates a
new version marked development/review data; never overwrite evaluated gold.

## Sequencing

1. Repair native curve continuity and report the frozen regression replay.
2. Build a reviewer overlay with unresolved contacts and arrow/path provenance;
   run the convention review above. Evaluate review-time savings using matched,
   counterbalanced different drawings; target 50% lower median time without
   more errors, not a familiar drawing shown twice.
3. Freeze genuinely independent, rights-cleared vector families, ports/OCR and
   arrow eligibility; test end-to-end separately from assisted port localization.
   The small synthetic cap remains 50 total drawings pending a new decision.
4. Fix raster segmentation/arrow localization in its own development lane. No
   prompting, no transfer of vector acceptance to scans, no training admission.

Diagram training remains blocked on crop lineage, rights/software terms, signed
reference and technical acceptance, held-out/cluster-aware qualification and an
explicit training/release decision. Text and calculation work can continue.

Method reference: [NIST Wilson confidence limits](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
