# Synthetic data expert worksheet

Blank planning/review template. It is not a signed case, an executable schema,
a completed scorecard or training approval. Store completed copies privately.
Bill Hurt is the designated technical reviewer; Norm is a potential contributor.

## A. Recipe approval, before generation

| Field | Expert entry |
| --- | --- |
| Recipe ID and version | |
| Author and relevant technical scope | |
| Independent accepting reviewer and scope | |
| Task type: brief / missing_data / calculation / grounded_explanation / abstention | |
| Competency and practical use | |
| Approved source IDs, revisions, hashes and family IDs | |
| Rights decision reference and permitted processing location | |
| Family split and holdout-register revision | |
| What the student may see | |
| Target answer and evidence supporting its material claims | |
| Competing explanations and discriminating observations | |
| Inputs that are mandatory, including units and basis | |
| Conditions under which a conclusion must be withheld | |
| Assumptions and method applicability limits | |
| Allowed variations and ranges | |
| Changes that require a different answer or fresh expert review | |
| Equation/tool version and independently checked reference result | |
| Absolute/relative tolerance and why it is appropriate | |
| Hard-fail criteria, including consequential omissions | |
| Draft/revise/accepted/escalated, decision date and reason | |

For non-calculation tasks record why calculation checks are not applicable.
Do not enter an invented reference value to fill a blank. A recipe acceptance
does not automatically accept any generated candidate or authorize training.

## B. Candidate review, one copy per exact candidate

| Identity | Entry |
| --- | --- |
| Run ID, candidate ID and exact candidate hash | |
| Recipe/prompt/rubric versions and hashes | |
| Source revisions, evidence locations and family | |
| Generation model/provider/settings and receipt reference | |
| Author of this answer or substantive correction | |
| Independent accepting reviewer | |
| Challenger objections and evidence | |

Use `pass`, `fail`, `not_applicable` or `needs_review`. Give evidence for each
entry; a source quote matching verbatim does not establish correct interpretation.

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| Material claims supported by permitted evidence | | |
| Numerical result and independently checked method | | |
| Units, absolute/gauge pressure and other bases | | |
| Physical assumptions and applicability | | |
| Missing information and discriminators | | |
| Appropriate uncertainty / abstention / action limits | | |
| Hindsight and reference answers absent from student input | | |
| Family holdout and current source permission | | |

| Decision | Entry |
| --- | --- |
| 0/1/2 score using the task rubric | |
| Critical error: yes/no; exact matched criterion | |
| Accept / revise / reject / escalate | |
| Reason and required correction | |
| Reviewer, date and review duration in minutes | |
| Existing technical-review record reference | |

A matched hard fail requires 0/yes and prevents acceptance. Unresolved applicable
checks prevent acceptance. For this pilot, a training target must score 2 with no
critical error; useful but incomplete answers are revised, not accepted as-is.
An edited answer gets a new hash and a fresh review. An author's substantive
correction requires another qualified accepting reviewer. Register the decision
through the existing technical-review procedure; this worksheet alone cannot
release a dataset or grant source rights.

## C. Batch decision

| Measure / decision | Entry |
| --- | --- |
| Attempted / returned / rejected / revised / accepted candidates | |
| Accepted candidates and distinct families per task type | |
| Calculation path unavailable or other coverage gaps | |
| Critical-error count and recurring failure categories | |
| Total known generation cost; missing receipts or charges | |
| Review minutes and minutes per accepted example | |
| Cost per accepted example, or N/A if none accepted | |
| Confirmed checks still needing improvement | |
| Continue / revise recipe / stop | |
| Bill's technical decision and date | |
| Brad's separate rights, external-processing and release decision references | |

No financial estimate, trial size or blank field constitutes authorization.
Report abandoned and failed attempts as well as accepted examples.
