# Public document evaluation pre review

Prepared 26 September 2026 by Codex. **Assistant analysis only. No human scores,
technical sign-off, model selection or training approval are recorded here.**
This report reveals the model identity and could influence a reviewer. To score
independently, read the original masked packets and record initial judgments
before consulting these notes.

## What was checked

Read all 30 returned Qwen answers against the fixed questions, draft references,
hard-fail criteria and saved source excerpts. Recomputed the six illustrative
arithmetic results. Re-ran the existing source verifier against the local HTML
cache, with no network. This checks the frozen sample, not whether a historical
publication is current engineering guidance.

- All 10 source snapshots match their raw and normalized hashes; every selected
  excerpt and recorded location matches. See [source check](pre_review_source_check.json).
- The run sample equals the pack sample. The 30 answer texts are within the
  requested 150-word limit under a simple whitespace count.
- Six arithmetic results match the stated numerical references/tolerances.
  This does not validate equipment sizing, property models or a real plant balance.
- The existing [citation audit](citation_audit.json) has **11 non-exact evidence
  quotations across 8 questions and 5 source documents**. Seven match after its
  limited punctuation-spacing normalization; four do not. Original flags remain.
- Human review remains **0/60 planned slots**. There are 30 actual Qwen answers;
  Mistral has three slots affected by its first-call output-limit failure and
  27 subsequent not-run slots. No engineering-quality comparison is possible.

## Review these five questions first

These are review priorities, not preassigned 0/1/2 scores or confirmed critical
errors. Apply the original criteria and record Bill's or Brad's own judgment.

| Question | Evidence to inspect | Concern and reviewer decision |
| --- | --- | --- |
| PUB-022 | [Tesoro packet](scorecard_CSB-TESORO.md), CSB-TESORO-B02 | Correctly names hydrogen partial pressure, but omits the explicit absolute/psia basis. Adds atomic-hydrogen/diffusion and relative-risk explanations not established by the provided excerpts. The hard-fail criteria explicitly include loss of absolute-pressure basis. Decide whether this triggers that criterion and whether the added explanation is acceptably bounded. |
| PUB-024 | [Tesoro packet](scorecard_CSB-TESORO.md), CSB-TESORO-B02 | Requests hydrogen mole fraction and supplies a partial-pressure formula, but does not state that the total pressure in that formula must have the required absolute basis. It quotes the alert's psia threshold but leaves actual equipment temperature, material/service history and damage evidence unaddressed. Assess completeness and basis, keeping the dated alert distinct from current requirements. |
| PUB-026 | [Williams packet](scorecard_CSB-WILLIAMS.md), CSB-WILLIAMS-B02 | Infers that rupture indicates the design pressure was exceeded. The supplied source reports rising pressure and rupture but gives neither design pressure nor a measured pressure. Reject that inference as source-established evidence; determine its technical significance. The answer appropriately withholds a numerical pressure prediction. |
| PUB-011 | [Pipeline packet](scorecard_EIA-PIPELINE.md), question and draft reference | The requested compressor input list omits suction/discharge pressures, their absolute/gauge basis and flow-volume basis. It also omits the operating envelope. It does not invent a compressor size, but these omissions matter for a missing-data answer. |
| PUB-014 | [HGL packet](scorecard_EIA-HGL.md), question and EIA-HGL-B03 | Requests the pipeline specification but not representative analysis of the actual gas to compare with it. Its evidence quote also adds an ellipsis and fails exact matching. Judge substantive incompleteness separately from citation formatting. |

## Additional review concerns

- **PUB-003:** correctly declines a numerical gasoline-blend prediction, but does
  not explicitly request component proportions and property measurement/test
  conditions. Decide whether its general request for composition is sufficient.
- **PUB-007:** obtains the requested volume and retains the stated gas basis,
  but does not clearly qualify the result as approximate in its own prose. The
  evidence quote drops a parenthetical from the source. Do not expand this
  illustration into a universal gas-to-liquid conversion.
- **PUB-009:** summarizes the chain but presents the 7–15% onsite-use range
  without the facility-design qualification visible in EIA-LNG-B04, which also
  describes an electrically driven exception. Assess whether it overgeneralizes.
- **PUB-020:** requests actual thickness, material, operating and inspection
  history but leaves the remaining-life method/minimum allowable thickness and
  explicit rate/uncertainty requirements incomplete against the draft reference.
- **PUB-023:** correctly refuses a current safety/code conclusion; named ASME/API
  references are not supplied in the excerpt. Do not treat their mention as a
  determination of which current requirements apply.
- **PUB-025:** explains isolation and loss of relief, but compresses installation,
  isolation and administrative-control failure into a causal sequence that needs
  checking against the source's wording. Its narrative includes an abbreviated
  quotation; the automated check only validates structured `evidence[]` quotes.
- **PUB-027:** refuses to provide a valve sequence. For a complete abstention,
  consider whether it should explicitly request reviewed P&IDs, verified relief
  configuration, vessel condition and an approved procedure/authorization.
- **PUB-028:** retains thermal fatigue and probable cause, but the phrase about
  current industry practices should be tied to the dated investigation rather
  than presented as an independently verified assessment of today's practice.
- **PUB-029:** useful temperature-cycle and repair requests; review the missing
  construction details and applicable vendor limits in the draft reference.

The original references are themselves drafts. If Bill disputes one, record the
issue; do not silently change the benchmark after seeing the model answer.

## Arithmetic check

The returned values below were read from the original answers. Independent decimal
arithmetic reproduced them and matched the frozen reference tolerances.

| Question | Calculation from the givens | Returned value | Remaining review |
| --- | --- | --- | --- |
| PUB-004 | 42 × 1.063 | 44.646 US gallons | Illustrative volume gain, not a closed real mass balance |
| PUB-007 | 120000 / 600 | 200 cubic metres | Approximate same-gas-basis comparison; quotation issue remains |
| PUB-008 | 100 × (1 − 0.10) | 90 million standard cubic feet/day gas-equivalent | Synthetic onsite consumption; not physical liquid volume |
| PUB-010 | 60 bara / 30 bara | 2, dimensionless | Insufficient to determine power; preserve the absolute basis |
| PUB-016 | (96 + 86) / 2 | 91 octane rating | Synthetic test values; quotation issue remains |
| PUB-017 | 2 × 91 − 96 | 86 MON rating | Synthetic test values; quotation issue remains |

## Complete coverage and original response labels

The labels below identify Qwen's existing response in each original packet. They
do not rename or reorder either model's output. An unflagged item still requires
human review; no row below is a pass or sign-off.

| Packet | Qwen label | Questions read | Focus |
| --- | --- | --- | --- |
| [Refining](scorecard_EIA-REFINING.md) | B | PUB-001, PUB-002, PUB-003 | Physical separation/conversion distinction; non-exact citations in 001/002; completeness in 003 |
| [Processing gain](scorecard_EIA-YIELD.md) | A | PUB-004, PUB-005, PUB-006 | Correct illustrative arithmetic and rejection of a guaranteed yield; actual mass-balance scope remains a reviewer check |
| [LNG](scorecard_EIA-LNG.md) | B | PUB-007, PUB-008, PUB-009 | Approximate volume basis, synthetic gas-equivalent balance and facility variation |
| [Pipelines](scorecard_EIA-PIPELINE.md) | A | PUB-010, PUB-011, PUB-012 | Pressure ratio correct; missing compressor pressures in 011; non-exact quotation in 012 |
| [HGL](scorecard_EIA-HGL.md) | B | PUB-013, PUB-014, PUB-015 | Dry gas versus purity; sample analysis absent in 014; buyer-specific limits cannot be inferred; quotation flags in 013/014 |
| [Octane](scorecard_EIA-OCTANE.md) | A | PUB-016, PUB-017, PUB-018 | Arithmetic matches; distinct tests retained; quotation spacing in 016/017 |
| [Chevron](scorecard_CSB-CHEVRON.md) | B | PUB-019, PUB-020, PUB-021 | Sulfidation and historical scope retained; fuller remaining-life inputs in 020; no diameter-only safety conclusion |
| [Tesoro](scorecard_CSB-TESORO.md) | A | PUB-022, PUB-023, PUB-024 | Absolute/partial-pressure basis, evidence limits and historical alert context |
| [Williams](scorecard_CSB-WILLIAMS.md) | B | PUB-025, PUB-026, PUB-027 | Causal precision, unsupported design-pressure inference and completeness of abstention |
| [Enterprise](scorecard_CSB-ENTERPRISE.md) | A | PUB-028, PUB-029, PUB-030 | Probable thermal-fatigue cause and dated conclusions; requested evidence; rejects leak-before-failure assurance |

## What to do next

1. Bill or Brad independently scores the original answers in [scores.csv](scores.csv),
   starting with Tesoro, Williams, compressor inputs and gas acceptance. Read
   [REVIEW_INSTRUCTIONS.md](REVIEW_INSTRUCTIONS.md) first. Do not copy these notes
   into reviewer fields as though they were a human's judgments.
2. Record critical flags and evidence. Classify Mistral's missing outputs as
   operational availability findings; do not invent substantive errors for
   unattempted questions. Resolve defective reference questions before selection.
3. Run the existing offline summary. Brad/Bill still need to confirm a quality
   threshold before a model selection decision. The current report remains HOLD.
4. Use confirmed failures to specify a new, versioned comparison protocol if
   needed. Run both models under identical revised constraints; do not overwrite
   v1, weaken its quote check retroactively or call this calibration sample unseen.
5. Keep training admission separate. This entire sample remains testing_only/dev;
   its source families do not become training candidates through review.

No EC2, model/API request, training, database/bucket write, production change or
message to Bill occurred during this pre-review.

## Reproduction and preservation

Source verification used the existing `scripts/research/verify_public_sources.py`
with `C:\Python313\python.exe` and the existing local cache. The Broadbridge and
Foundry virtual environments and the bundled artifact runtime did not have
BeautifulSoup; no dependency was installed or environment modified. The successful
runtime produced the existing requests dependency warning; the check made no
network requests.

Only this report and its source-check JSON were added to the frozen run directory.
The question set, prompts, original model results, reviewer packets and score file
are preserved. SHA256 at pre-review:

| File | SHA256 |
| --- | --- |
| sample.json | 3407f8d2ea56e0cc8c379f9a84b5c1808b72d5dedd7c504d1badbcb423a0e736 |
| protocol.json | 47f38b1b9d0cf7b9930200c38e68f4b126776a341a49239489d310509912f241 |
| results.json | 9cb326693fe100acc1b01b625547997a50749b538a07009a93f85f83b2cdc330 |
| run.json | 9d55add47c397c9e9d1658f25ac39f26e44e7020934154f40e3a13313c8c455c |
| scores.csv | 630d90fbf96a113e279fe38975d7652a735511f4724e77f184d77e51ce1893d5 |
