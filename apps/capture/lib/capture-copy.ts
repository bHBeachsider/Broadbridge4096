// Verbatim field copy and trusted introductory markup from case-capture.html.
export const PART_A = [
  ['A1','When a distillation or vacuum problem lands on your desk, what are the first three things you do, in order?','We want the real sequence, not the textbook one.'],
  ['A2','Roughly how long does a typical case take from first call to a brief you would put your name on? Where does most of that time go?','Gathering data, waiting on people, calculating, writing, reviewing. Rough percentages are fine.'],
  ['A3','What data do you always ask for first, and where does it usually come from?','Historian, lab, operators, drawings, previous reports.'],
  ['A4','Which calculations or checks do you run on nearly every case?','Pressure-drop vs flow, flood/weep checks, ejector curves, heat and material balances, dew/bubble points. Name the ones that settle arguments.'],
  ['A5','What does a good written brief contain? What do reviewers or clients push back on when it is missing?',''],
  ['A6','What is the most common wrong diagnosis you see from less experienced engineers in this area, and what evidence usually exposes it?',''],
  ['A7','What must a tool never do or say? What would make you stop trusting it immediately?','Inventing a measurement, recommending a change to an operating limit, citing a source that does not exist.'],
  ['A8','Which parts of your workflow would you hand to an assistant, and which would you insist on doing yourself?',''],
  ['A9','Which references do you reach for (books, standards, vendor curves, internal notes)? Which could be licensed or are public?','Rights are recorded separately; this is to know what exists.'],
  ['A10','If the tool cut the time to an accepted brief by a quarter, what would that be worth to a client, and how would they measure it?',''],
] as const;
export const DECISION = [
  ['b1_trigger','B1','What first made this case worth looking at? What decision had to be made?','The reported symptom, who reported it, what was normal before.'],
  ['b2_operating_context','B2','What did the unit look like operationally at the time?','Configuration, feed and products, steady or transient, recent changes, constraints.'],
  ['b3_initial_info_and_requests','B3','What information did you have at the start, and what did you ask for first?','List the actual data requests. This becomes the missing information the model must learn to ask for.'],
  ['b5_initial_hypotheses','B5','What were the plausible explanations at that point, including the tempting wrong one?','Two to four. What made each plausible?'],
  ['b6_distrusted_or_missing','B6','What did you distrust or lack? Which instruments or records did you not believe, and why?',''],
] as const;
export const HINDSIGHT = [
  ['b8_turning_point','B8','Which single observation or calculation changed the ranking of explanations? Why did it outweigh the rest?','The diagnostic turning point. This is what we most want the model to learn to look for.'],
  ['b9_calculations','B9','What did you calculate? Inputs, units, assumptions, method, result, and how you checked it.','A photo or sheet is better than a description. Mark estimated numbers.'],
  ['b10_actions_taken','B10','What was actually tried, by whom, with what authorisation, and what happened? Include what did not work.','Historical fact, not a recommendation.'],
  ['b11_confidence','B11','How confident are you in the final explanation? Confirmed, inferred, disputed or unresolved, on what evidence?',''],
  ['b12_dangerous_wrong_answer','B12','What would a dangerous wrong answer have looked like? What should a junior engineer or a tool never have said?','This becomes a hard-fail criterion in testing.'],
  ['b13_lesson_and_limits','B13','What is the transferable lesson, and where does it stop applying?','The rule of thumb, its limits, a counterexample if you have one.'],
] as const;
export const IDENTITY = [
  ['title','Short title','text'],
  ['unit_service','Unit / service (generic label is fine)','text'],
  ['period','Approximate date or period','text'],
  ['record_type','Record type','select',['real_event','reconstructed','hypothetical']],
  ['confidentiality','Confidentiality and who may see it','text'],
  ['permitted_use','Permitted use','select',['training','testing_only','reference_only']],
] as const;
export const OBS_COLS = [['time','Time'],['variable_location','Variable and location'],['value_units_basis','Value, units, basis'],['source','Source'],['quality','Quality / doubts']] as const;
export const HYP_COLS = [['hypothesis','Hypothesis'],['evidence_for','Evidence for'],['evidence_against','Evidence against'],['discriminator','What would settle it']] as const;
export const EVI_COLS = [['item','Item'],['format','Format'],['available_at_decision_time','Available at decision time?'],['restriction','Sharing restriction']] as const;
export const Q_TYPES = [['brief','Brief','Assemble a diagnostic brief from decision-time evidence only.'],['missing_data','Missing data','Ask for the right next measurements.'],['calculation','Calculation','Run the check with correct units and assumptions.'],['grounded_explanation','Grounded explanation','Explain a mechanism citing only supplied sources.'],['abstention','Abstention','Refuse or escalate when evidence is insufficient.']] as const;

export const ABOUT_HTML = `
<div class="head"><div><h2>Read this first</h2><p class="sub">About five minutes. Then fill Part A once, and one case per session.</p></div></div>
<div class="section">
<div class="callout"><p>We are building a small language model that helps a process engineer produce a diagnostic brief faster. It does not replace the engineer. Its job is to pull together the evidence, list what is missing, run the standard checks, lay out the competing explanations, and hand the engineer a draft to correct and sign.</p>
<p>To build and test it we need real troubleshooting cases told the way you actually worked them: what you saw first, what you asked for, what you calculated, what you ruled out, and what would have been a dangerous wrong answer. Five to ten cases in distillation and vacuum systems is enough to start.</p></div>
<h3>What happens to your answers</h3>
<ul><li>Each case becomes one record that you approve before it is used.</li><li>From each case we derive 3–6 test questions with your reference answer, to score the model against (section C).</li><li>Approved cases become training examples. Cases you mark <b>testing only</b> are kept out of training entirely.</li></ul>
<h3>Ground rules</h3>
<ul><li>Sanitise as you see fit: site, client and unit names can be generic. Physics and numbers should stay real.</li><li>"Unknown" or "not recorded" is a valid answer. Please do not fill gaps with plausible guesses; the model must learn to say what it does not know.</li><li>Keep the sequence honest: what you knew at the time (B1–B6) versus what you learned afterwards (B7–B13).</li><li>Everything saves automatically as you type. Nothing is used until you tick the sign-off at the bottom of a case.</li></ul>
<h3>What happens after you fill this in</h3>
<ol>
<li><b>Your record becomes the test.</b> Each case's decision-time section (B1–B6) is what the model is shown. Your hindsight section (B7–B13) and section C are the answer key it is scored against. The model never sees the answer key.</li>
<li><b>We measure the model as it is today.</b> Before any training, the stock model plus a document search runs your cases and produces a draft brief. You score it: what it got right, what it missed, anything it said that it must never say.</li>
<li><b>Your scores decide what to train.</b> Where the draft is already good, we keep the search and skip training. Where it fails, approved cases marked <i>training</i> teach it; cases marked <i>testing only</i> stay hidden so the retest is fair.</li>
<li><b>You see the retest.</b> Same cases, same scoring, before and after. The model is accepted only if it improves without new critical errors.</li>
<li><b>Then it goes in front of an engineer's real work.</b> A pilot where the tool drafts the brief and the engineer corrects it. Their corrections come back here as new cases.</li>
</ol>
<h3>Suggested pace</h3>
<p class="muted">Part A: about 20 minutes, once. First case: 30–40 minutes, less thereafter. You can type directly, or talk it through on a call while Brad types, then correct the record yourself.</p>
</div>`;
