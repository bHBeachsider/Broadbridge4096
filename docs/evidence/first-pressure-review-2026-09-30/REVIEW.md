# First dataset: pressure-basis review proposal

**Pending independent engineering and rights review. No training release or baseline run.**

Fifteen assistant-authored drafts, three per question type, using one DOE handbook family. These are educational review proposals, not signed case questions or an evaluation sample. Splits remain unassigned; do not split this family by page or paraphrase.

Extraction packet SHA-256: `0ae8da768e4fbc5427d5c4acbd4b2193dcf93308fffac6e8cb61fce26f0b8150`.
Source PDF SHA-256: `3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9`.

[DOE original PDF, starting at page 35](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35). The page numbers here are PDF pages, not printed handbook pages. Compare pages 35-37, printed HT-01 pages 9-11.

[Local extraction review and page renders](<C:/Users/bradu/Documents/Broadbridge4096/tmp/codex-broadbridge-ingestion-plan/packs/oil-gas/outputs/fq02-doe-review-20260930/REVIEW.md>). This local link is specific to Brad's workstation; another operator can recreate it with the commands in docs/FIRST_DATASET_REVIEW.md.

## Reviewer actions

1. Bill or an appointed engineer: choose whether pressure-basis checking is a useful first task; suggest a higher-priority task if needed.
2. Check each correction proposal and each draft answer, assumptions, tolerance and hard-fail criteria. Record accept/revise/exclude, correction, evidence, name and date in review.csv. Blank rows remain pending.
3. Brad: separately record rights/credits/permission evidence for the precise source and pages. This worksheet records no permission grant.
4. Before admission, check all related-family history and allocate the entire family to one split. Independent validation/test families are still needed; these 15 drafts are not 15 independent test cases.
5. Pass signed decisions and exact proposal hash through the existing acceptance/release workflow; editing this worksheet does not produce a release.

## Excluded from this first scope

- Hydrostatic numerical examples: resolve mass density, weight density and g/g_c conventions first.
- Universal use of 14.7 psia or rounded water/mercury column conversions without stated reference conditions.
- Figure 2 connectivity, native vision training, equipment design, set points or operating recommendations.
- General claims that negative absolute liquid pressure is physically impossible in every context.

## Nine proposed exception dispositions

- **figure** — Exclude graph/topology use; use definitions and equations for text questions only. Independent decision: ______
- **subscripts** — Page-image transcription: P_abs = P_atm + P_gauge and P_abs = P_atm - P_vac. Reviewer must confirm symbols/sign conventions. Independent decision: ______
- **symbol** — PDFium image retains rho; preserve raw parser disagreement. Do not substitute r or silently repair the hydrostatic recipe. Independent decision: ______
- **mass-force** — Exclude both hydrostatic numeric examples until mass/force/gravity conventions are explicitly accepted. Independent decision: ______
- **assumptions** — Use explicitly supplied atmospheric inputs. Exclude rounded fluid-column conversions from numerical candidates. Independent decision: ______
- **exponent** — Image shows 10^3, proposed transcription 1000. Retain as a review finding; do not admit the column-conversion recipe. Independent decision: ______
- **table** — Conversions are manually normalized typeset rows; detected-table count remains zero. Do not relabel them parser-extracted tables. Independent decision: ______
- **scope** — Propose pressure-basis education only. No process-design, equipment-limit or site-operation claims; reviewer decides applicability. Independent decision: ______
- **rights** — Brad records exact pages/credits/permission basis. Distribution Statement A and contractor credits are evidence to inspect, not an automatic training decision. Independent decision: ______

## Draft questions and references

### DOE-PRESSURE-DRAFT-01 — brief

An illustrative pressure log mixes psia, psig and a positive vacuum-depression reading. Give a short checking plan before comparing the entries.

**Draft reference:** Identify the reference basis and units for each reading. Absolute pressure is relative to vacuum; gauge is relative to local atmospheric pressure. Obtain the relevant atmospheric pressure, confirm the vacuum sign convention, convert onto one basis and retain the original readings. These definitions alone do not establish operating acceptability.

**Critical errors:** Treating psia and psig as interchangeable; silently assuming 14.7 psia; declaring the process safe from these data.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-02 — brief

An illustrative log contains a negative psig reading. Explain briefly what it means and which extra value is required to express it in psia.

**Draft reference:** It is below the gauge's atmospheric reference, not automatically a negative absolute pressure. With consistent psi units and the applicable local atmospheric pressure, P_abs = P_atm + P_gauge. Confirm the measurement basis before using it.

**Critical errors:** Equating negative gauge pressure with negative absolute pressure; inventing atmospheric pressure.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-03 — brief

Summarize what equations 1-9 and 1-10 on PDF page 36 can and cannot establish for an engineer reading a pressure report.

**Draft reference:** They relate absolute pressure to atmospheric pressure plus gauge pressure, or atmospheric pressure minus a positive vacuum-depression magnitude. They require compatible units and known reference conditions. They do not by themselves establish flow, equipment capacity or a permissible operating limit.

**Critical errors:** Reversing either sign; claiming these equations alone establish equipment limits.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-04 — missing_data

A note says only 'pressure = 35 psi'. What must be clarified before converting it to absolute pressure?

**Draft reference:** Ask whether the value is absolute, gauge or a vacuum depression; confirm units and sign convention. If gauge or vacuum, obtain the atmospheric reference applicable to the reading. Preserve uncertainty rather than assigning a basis.

**Critical errors:** Assuming gauge or absolute without evidence; adding a default atmosphere.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-05 — missing_data

An illustrative instrument log says '5 inches vacuum'. What is missing for a defensible conversion to absolute pressure in psi?

**Draft reference:** Clarify whether this is a fluid-column pressure unit, which fluid/reference conditions the calibration assumes, the vacuum magnitude/sign convention and the atmospheric reference. A validated unit conversion is required; the handbook's rounded column examples alone do not supply site conditions.

**Critical errors:** Treating inches as psi; choosing water or mercury without evidence; presenting an exact absolute result.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036, DOE-HDBK-1012-1-92:pdf-037.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-06 — missing_data

A report gives a psig reading from a remote site but no atmospheric pressure. Which specific reference input is missing, and why does it matter?

**Draft reference:** The atmospheric pressure applicable to the gauge reference at the site/time is missing. It is the additive term needed to compute absolute pressure from gauge pressure; 14.7 psia is a handbook example, not evidence of the site's pressure.

**Critical errors:** Inventing a site atmosphere or a precise absolute answer.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-07 — calculation

Illustrative arithmetic only: given local atmospheric pressure 14.2 psia and gauge pressure 36.8 psig, compute absolute pressure in psia to one decimal. Treat supplied inputs as exact for this exercise.

**Draft reference:** P_abs = P_atm + P_gauge. 14.2 + (36.8) = 51.0 psia. This is a pressure-basis conversion, not an operating-limit assessment.

**Critical errors:** Wrong reference basis or sign; reporting the result in psig; replacing the supplied atmospheric pressure; claiming instrument accuracy or process safety.

**Tolerance:** Proposed +/-0.05 psi for the rounded one-decimal answer; not instrument accuracy. Reviewer acceptance pending.

**Evidence:** DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-08 — calculation

Illustrative arithmetic only: given local atmospheric pressure 14.5 psia and gauge pressure -2.1 psig, compute absolute pressure in psia to one decimal. Treat supplied inputs as exact for this exercise.

**Draft reference:** P_abs = P_atm + P_gauge. 14.5 + (-2.1) = 12.4 psia. This is a pressure-basis conversion, not an operating-limit assessment.

**Critical errors:** Wrong reference basis or sign; reporting the result in psig; replacing the supplied atmospheric pressure; claiming instrument accuracy or process safety.

**Tolerance:** Proposed +/-0.05 psi for the rounded one-decimal answer; not instrument accuracy. Reviewer acceptance pending.

**Evidence:** DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-09 — calculation

Illustrative arithmetic only: given local atmospheric pressure 14.7 psia and positive vacuum depression 5.0 psi below atmosphere, compute absolute pressure in psia to one decimal. Treat supplied inputs as exact for this exercise.

**Draft reference:** P_abs = P_atm - P_vac. 14.7 - (5.0) = 9.7 psia. This is a pressure-basis conversion, not an operating-limit assessment.

**Critical errors:** Wrong reference basis or sign; reporting the result in psig; replacing the supplied atmospheric pressure; claiming instrument accuracy or process safety.

**Tolerance:** Proposed +/-0.05 psi for the rounded one-decimal answer; not instrument accuracy. Reviewer acceptance pending.

**Evidence:** DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-10 — grounded_explanation

Using PDF page 36, explain why gauge pressure is added in equation 1-9 while a positive vacuum depression is subtracted in equation 1-10.

**Draft reference:** Gauge pressure is a signed difference from atmosphere, so adding that difference gives absolute pressure. In the sub-atmospheric convention used here, vacuum depression is a positive amount below atmosphere, so it is subtracted. A negative gauge reading must not also be subtracted as though it were a positive depression. Cite equations 1-9 and 1-10.

**Critical errors:** Double-negating a negative gauge reading; reversing a sign; citing a formula absent from the evidence.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-11 — grounded_explanation

Explain, using the pressure definitions on PDF page 35, why two equal numerical psi readings need not represent the same pressure.

**Draft reference:** The reference bases can differ: psia is referenced to vacuum and psig to atmosphere. Equal numerical values with different bases describe different absolute pressures. The units and reference must accompany the number; cite the page's absolute/gauge definitions.

**Critical errors:** Saying equal numerical psi values are always interchangeable.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-12 — grounded_explanation

Why should an answer using this handbook distinguish a stated atmospheric input from its 14.7 psia example? Ground the answer in the pressure equations and worked-example assumptions.

**Draft reference:** P_atm is an explicit term in equations 1-9 and 1-10; the examples assume 14.7 psia. A calculation with a different supplied atmospheric pressure must use that input. A missing site value remains missing; the example does not measure the site.

**Critical errors:** Using the example's atmospheric value despite a different supplied value; treating it as universally exact.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-036, DOE-HDBK-1012-1-92:pdf-037.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-13 — abstention

For an illustrative vessel, all you have is '80 psia'. Can you determine its maximum safe operating pressure from PDF pages 35-37?

**Draft reference:** No. These pages define pressure and show elementary conversions; they do not provide this vessel's allowable pressure, design conditions, condition assessment or applicable design basis. Do not turn a measured value or worked-example watch limit into a vessel limit.

**Critical errors:** Giving a vessel safe operating limit or adopting the handbook's watch rating.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035, DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-14 — abstention

Can the first candidate set use the page-36 diver example's density 64 lbm/ft3 and P = rho H directly as a dimensionally explicit hydrostatic recipe?

**Draft reference:** Not without resolving the source's implicit mass/force and gravity convention. The equation as transcribed with mass density needs that convention made explicit by a qualified reviewer. Exclude numerical hydrostatic examples from this first set rather than silently rewriting the source.

**Critical errors:** Accepting a dimensionally incomplete mass-density formula as a verified general recipe; silently changing lbm to force units.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-036.

**Decision / correction / reviewer / date:** ______

### DOE-PRESSURE-DRAFT-15 — abstention

Can the handbook's pressure-scale Figure 2 establish pipe connections or flow direction in a plant P&ID?

**Draft reference:** No. It illustrates pressure reference levels, not plant piping topology. No plant connectivity or flow direction can be inferred from it. Request the relevant approved drawing/model and use the separate connectivity-verification process.

**Critical errors:** Inferring a plant connection or flow direction from the pressure-scale sketch.

**Tolerance:** not applicable

**Evidence:** DOE-HDBK-1012-1-92:pdf-035.

**Decision / correction / reviewer / date:** ______

## What this does not complete

Gate 0 still requires recorded rights/storage and at least 30 signed case-derived questions across all five types. This proposal contributes zero to that count. Production case status is not checked here. S0-cases, scored retrieval comparison, accepted family-separated release, exact-release token audit and a bounded GPU run decision remain prerequisites in the current plan. No model answer or score is fabricated.
