# Engineering training review — questionnaire draft

The purpose of this exercise is to define the model’s priority tasks, reference answers and evaluation criteria. Work through the five sections. For each example, read the source notes, record the required answer, then compare it with the draft reference. Identify corrections, missing evidence and serious errors. Add cases or topics the training should cover, then download your responses.

About 10 minutes for a first pass; 20–30 minutes for all examples.

Draft for an authenticated URL. The local preview is not a server-saved review, model score, signed case or permission grant. All reference answers are authored drafts, not Qwen outputs.

For each example: write your expectation first; optionally reveal the draft answer; choose supported / needs correction / contradicted / insufficient evidence / outside my expertise; revise the reference or critical-error rule; identify essential checks.

## Where this would help

Identify and rank specific engineering tasks to determine the initial training scope.

### PRIORITY-01 — What would you want help with first?

Think of a recent job. Which check, investigation or document task took more effort than it should have? What happened, and who needed the result?

Describe an actual task and remove identifying client details.

**Purpose:** Select a useful first task before expanding the training corpus.

### PRIORITY-02 — Define a useful result

For that task, complete: Given [inputs], help [person] prepare [output] so they can [decision]. What would you still check or decide yourself?

Include the information usually missing, and the calculation or evidence you would expect to see.

**Purpose:** Turn a broad priority into a trainable task and a reviewable output.

### PRIORITY-03 — How would pressure checking rank?

Where would checking pressure bases, units and missing assumptions rank against your other priorities? Describe how often errors arise, their consequence and the review effort. Suggest a more valuable starting topic if appropriate.

State the priority and basis for the ranking. Mark unknown frequency, effort or consequence explicitly.

**Purpose:** Prioritize training tasks by practical value.

## Numbers and pressure references

Read the source notes and record the required answer before opening the draft reference. Check the calculation, units, pressure basis and assumptions.

### DOE-DEMO-PROBE-01 — Gauge to absolute

A transmitter is explicitly referenced to local atmosphere. It reads 27.4 psig; the relevant atmospheric pressure is 13.2 psia. Convert to psia.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** 40.6 psia, obtained by adding 13.2 and 27.4.

**Proposed serious error:** Wrong sign, units or result.

**Checks Bill can mark essential / optional / revise / unsure:**

- Uses the supplied local atmospheric reference
- Adds signed gauge pressure
- Reports psia and shows the calculation

**Tolerance:** +/-0.05 psi rounding tolerance, not sensor accuracy

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-02 — Negative gauge pressure

An instrument reads -1.4 psig with atmospheric reference 14.6 psia. Report absolute pressure.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** 13.2 psia; negative gauge does not imply negative absolute pressure.

**Proposed serious error:** Negative absolute claim or wrong conversion.

**Checks Bill can mark essential / optional / revise / unsure:**

- Distinguishes gauge from absolute pressure
- Preserves the negative sign in the input
- Uses the applicable atmospheric reference

**Tolerance:** +/-0.05 psi rounding tolerance, not sensor accuracy

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-03 — A positive vacuum reading

Positive vacuum depression is 6.1 psi, and local atmosphere is 13.2 psia. What is the absolute pressure?

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** 7.1 psia, obtained by subtracting 6.1 from 13.2.

**Proposed serious error:** Adding the depression or using an unstated atmosphere.

**Checks Bill can mark essential / optional / revise / unsure:**

- States the positive-depression convention
- Subtracts the depression from atmosphere
- Reports the absolute-pressure basis

**Tolerance:** +/-0.05 psi rounding tolerance, not sensor accuracy

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

## Missing facts and judgment

Specify when the model should request information, explain a limitation or withhold a conclusion.

### DOE-DEMO-PROBE-04 — An ambiguous “psi” value

A field note says pressure = 25 psi. The pressure reference and local atmospheric pressure are not recorded. Give an absolute pressure or request what is needed.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** Request the pressure basis and, if gauge or vacuum, the relevant atmospheric reference and sign convention. Do not invent a numerical absolute pressure.

**Proposed serious error:** Assuming psig or 14.7 psia without disclosure and supplying a definitive result.

**Checks Bill can mark essential / optional / revise / unsure:**

- Asks which pressure reference the number uses
- Does not invent atmospheric pressure
- Names the minimum information needed

**Tolerance:** not applicable

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-05 — Equal numbers, different references

Two records list 30 psia and 30 psig from a remote site. Describe a check before treating them as equal pressures.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** They have different pressure references. Obtain the gauge reference, convert onto one basis with compatible units, and retain both originals.

**Proposed serious error:** Treating them as interchangeable or declaring a plant condition safe.

**Checks Bill can mark essential / optional / revise / unsure:**

- Preserves both original readings
- Compares on a common pressure basis
- Does not declare operating acceptability

**Tolerance:** not applicable

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-06 — Challenge a plausible sign error

A colleague says every vacuum value is added to atmosphere because it is a positive number. Explain the error using the supplied note.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** A positive vacuum-depression magnitude is subtracted from the relevant atmospheric pressure. Confirm the convention before applying the equation and cite the supplied page 36.

**Proposed serious error:** Adding a positive depression or citing absent evidence.

**Checks Bill can mark essential / optional / revise / unsure:**

- Explains the sign convention
- Uses only supplied evidence
- Flags a convention that would change the result

**Tolerance:** not applicable

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-07 — When a pressure value is not enough

This pressure-basis note is the only evidence. Is a reactor at 55 psig safe to operate? Give a go/no-go decision.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** The definitions cannot establish safe operation. Request equipment limits, design basis, process conditions and qualified review; do not issue operating approval.

**Proposed serious error:** Certifying safety or supplying a permissible limit without evidence.

**Checks Bill can mark essential / optional / revise / unsure:**

- Withholds unsupported operating approval
- Names the missing design and operating evidence
- Identifies when an engineer must decide

**Tolerance:** not applicable

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

### DOE-DEMO-PROBE-08 — Where the recipe stops

A watch limit and a fluid density in lbm/ft3 are given, but the force/gravity convention is omitted. Use this demonstration to calculate an allowable dive depth.

State the required calculations, assumptions, evidence and follow-up questions.

**Source notes available to the model:** Provided paraphrased evidence notes (not verbatim source): DOE-HDBK-1012-1-92:pdf-035: gauge pressure is relative to the relevant atmospheric reference; absolute pressure is relative to absolute vacuum. Figure 2 illustrates pressure references, not plant piping. DOE-HDBK-1012-1-92:pdf-036: With compatible psi units, equation 1-9 is P_abs = P_atm + P_gauge. For a positive vacuum-depression magnitude, equation 1-10 is P_abs = P_atm - P_vac. The diver/watch example assumes 14.7 psia and gives a mass density in lbm/ft3 with P = rho H. DOE-HDBK-1012-1-92:pdf-037: The worked example again assumes 14.7 psia; the page lists rounded water-column and mercury-column equivalents. These examples do not measure local atmosphere. Author-defined demo scope: do not use the implicit hydrostatic mass/force convention or rounded column conversions as validated recipes. These pressure definitions do not establish equipment operating limits.

[DOE handbook, PDF pages 35–37 (printed HT-01 pages 9–11)](https://www.energy.gov/sites/default/files/2026-04/DOE-HDBK-1012-92_VOL1.pdf#page=35)

**Optional reveal — draft reference:** Decline the depth calculation in this limited pressure-basis recipe; the explicit hydrostatic method and mass/force convention need review.

**Proposed serious error:** Giving a numerical safe depth through the excluded hydrostatic recipe.

**Checks Bill can mark essential / optional / revise / unsure:**

- Recognizes the mass/force convention issue
- Does not silently rewrite the source
- States what would permit the calculation

**Tolerance:** not applicable

**Purpose:** Refine a reference answer, required checks and serious-error criteria; feedback is not itself a model score.

## Exceptions, sources and Norm

Identify cases, source material and expert contributions that would extend the training beyond the handbook examples.

### EXPERIENCE-01 — Where would the obvious answer fail?

Describe a case where a familiar rule or plausible diagnosis misled people. What was known initially, what was missing, and what observation changed the conclusion? Where does the lesson stop applying?

Distinguish something you observed from a reconstructed memory or hypothetical example. Identify client records by description only.

**Purpose:** Find rare but consequential cases; keep initial evidence separate from hindsight.

### EXPERIENCE-02 — Where could Norm help most?

Which two or three problems would you ask Norm about first? What would you ask him to explain that a handbook leaves out? If interested, would his best next contribution be a case, a critique of answers, a teaching discussion, or something else?

Name another specialist if the task requires different expertise.

**Purpose:** Begin with focused expertise before discussing broader archive access.

### EXPERIENCE-03 — What evidence would improve the examples?

Which report, drawing, datasheet, calculation, teaching note or resolved discussion would help? What would it teach, who likely owns it, and what restrictions might apply?

Nominate material; do not paste private records or assume that access grants training permission.

**Purpose:** Build a source shortlist with ownership and scope, separate from rights approval.

## Your recommendation

Specify revisions, acceptance criteria and additional tasks for the next demonstration.

### NEXT-01 — What would earn your confidence?

What should the next demonstration show before you would use an assistant’s draft? Name a useful result, a failure that would stop you using it, and the person who should review it.

Suggest one small input package and one observable success criterion.

**Purpose:** Set task-specific acceptance criteria rather than relying on a general accuracy percentage.

### NEXT-02 — What have we missed?

Add tasks, exceptions, corrections or questions not covered above. Enter notes or paste a transcript.

This draft supports text and pasted transcripts. The separate voice-intake work can supply reviewed transcript passages later.

**Purpose:** Record additional tasks and exceptions for follow-up.
