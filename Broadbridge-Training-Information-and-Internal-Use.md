# Broadbridge Oil & Gas: ideal training information and internal-use assessment
23 September 2026

## Scope and answer

This checklist supports the domain-specific SLM program of Broadbridge Oil & Gas, a subsidiary of Broadbridge4096. The user clarified that source data will not be productized and the immediate intended use is internal model training. This assessment does not assume public distribution of data, weights, or a customer-facing system.

Internal training can be acceptable when supported by ownership, an applicable license or a legal exception. Keeping source data private does not automatically make a use noncommercial. This distinction refines the earlier references to commercial restrictions: a ban on resale is narrower than a ban on commercial use, and neither can be substituted for the actual source terms.

The checklist is a proposed curriculum, not an inventory of approved training data. Begin with refining/process operations; gas processing and upstream remain later practices with separate specialists and evaluation.

## Ideal training information

Each row specifies a capability to teach. Many documents can supply one capability, and one approved case can support several tasks. Avoid counting those derivatives as independent incidents.

| ID | Information set | Information to capture | Example training task |
|---|---|---|---|
| T01 | Engineering vocabulary, units and fundamentals | Definitions; aliases; gauge versus absolute pressure; mass versus volume basis; physical balances; phase behavior | Normalize a problem statement and identify incompatible units or missing bases |
| T02 | Process and equipment relationships | Flowsheet topology; stream roles; trays versus packing; condensers; reboilers; ejectors; utility connections | Explain which equipment interactions matter for a stated symptom |
| T03 | Distillation troubleshooting | Feed and operating regime; temperature/pressure profiles; separation symptoms; entrainment; flooding; weeping; internal damage | Compare plausible causes using only supplied evidence |
| T04 | Vacuum-system troubleshooting | Absolute pressure; load; steam/utility conditions; ejector and condenser behavior; leakage; discharge constraints | Request evidence that distinguishes process-load and vacuum-equipment explanations |
| T05 | Heat transfer and steam systems | Duty and temperature profiles; fouling; bypassing; noncondensables; condensate behavior; reboiler circulation | Reconcile performance observations with a checked heat balance |
| T06 | Pumps and hydraulic context | Pump/system curves; fluid properties; head and flow; suction evidence; piping losses; interaction with process conditions | Distinguish competing hydraulic explanations without inventing an operating instruction |
| T07 | Measurements, controls and data quality | Sensor locations; time stamps; lag; calibration; control mode; sample timing; conflicting readings | Identify unreliable evidence and ask the next useful clarification |
| T08 | Calculations and validated tool use | Input definitions; equations; units; property methods; assumptions; valid ranges; reproducible outputs | Call a validated tool; interpret results; reject dimensionally inconsistent inputs |
| T09 | Complete incident histories | Initial decision; chronology; alternatives; evidence; authorized intervention; outcome; uncertainty | Produce a concise diagnostic brief supported by observations |
| T10 | Diagnostic questions and evidence selection | Missing facts; hypothesis-specific observations; contradictory evidence; what would change the conclusion | Choose the highest-value next question and explain why it matters |
| T11 | Rules of thumb and applicability | Rule; rationale; valid range; assumptions; exceptions; counterexample; uncertainty | State when a shortcut applies and when additional analysis is necessary |
| T12 | Failures, counterexamples and unresolved cases | Wrong first diagnosis; ineffective remedy; same symptom with another cause; combined faults; incomplete outcomes | Revise an earlier answer or retain uncertainty when evidence is insufficient |
| T13 | Operating boundaries and escalation | Scope of competence; specialist triggers; procedure authority; management-of-change context; historical incident lessons | Recognize when evidence cannot support a recommendation and route for review |
| T14 | Source-grounded technical answers | Source identity; page/figure/time stamp; edition; relevance; conflicting or absent evidence | Answer from supplied references, cite the supporting passage and disclose gaps |
| T15 | Outcome verification and business impact | Before/after basis; confounders; recurrence; energy/yield/downtime effects; historical prices; uncertainty | Distinguish measured improvement from attributed or estimated benefit |
| T16 | Professional response and tool discipline | Concise explanations; assumptions; correction of mistakes; confidentiality boundaries; document instructions treated as data | Separate facts from hypotheses; decline unsupported claims; respect authorized tool scope |

The accompanying CSV adds priority, candidate source types, recommended routing and accountable owners.

## Material to collect from Norm and other experts

Collect original interviews; complete technical email threads and attachments; site reports and work papers; calculations and spreadsheets; annotated sketches and inspection records; published articles and book chapters; conference papers and presentations; seminar recordings, teaching notes and quizzes; and corrections to earlier publications.

Norm is a proposed expert candidate. Request his strongest distillation, vacuum and equipment-troubleshooting cases; obtain complementary reviews from qualified equipment, controls, operations, reliability and process-safety specialists. Published coauthored works and client material require their own rights analysis.

Capture correspondence through to its resolution. A reply sent early in an investigation may have been superseded by later evidence. Preserve dates, evidence available at the time, uncertain recollections and unresolved outcomes. Anonymize unnecessary personal or client identifiers, but do not treat anonymization as a substitute for contractual permissions.

For a text SLM, convert cleared diagrams and trends into verified structured descriptions linked to the original figure. Raw image files and time series are not automatically usable as text fine-tuning examples. A multimodal model or dedicated analytical tool would require separate design and validation.

## What goes into training, retrieval, tools and evaluation

| Destination | Include | Reason |
|---|---|---|
| Fine-tuning | Reviewed question/answer exchanges, diagnosis briefs, missing-data questions, applicability distinctions, tool calls, grounded responses and escalation examples | Teach stable task behavior and domain judgment |
| Retrieval | Licensed full references, exact editions, current site procedures, equipment manuals and customer-specific context | Preserve source attribution, versioning and access controls |
| Engineering tools | Validated equations, property calculations, balances and reproducible simulations | Make numerical results independently checkable |
| Held-out evaluation | Fresh expert cases, reserved quizzes, failure tests and answer rubrics | Measure generalization without teaching the answers |
| Governance records | Source hashes, rightsholders, grants, privacy controls, versions, reviewers and split assignments | Control admission and audit lineage; do not train on confidential administration |

Retrieval also needs an appropriate use basis; it is not a workaround for a source restriction. Existing model weights from Hugging Face are separately licensed foundation assets, not an automatic grant to their training data. Check model, dataset and teacher-model terms independently. LLM-generated examples require review and source lineage; paraphrasing restricted material does not establish permission.

### Minimum record for each training example

Record: case-family ID; topic and task; source/version/page or time stamp; decision-time facts; plant/equipment regime; units and measurement basis; missing information; approved target answer; evidence supporting the answer; alternatives and limitations; actual versus inferred outcome; reproducible tool inputs/results where needed; author and independent reviewer; permission reference; and train/development/test assignment.

Retain source administration outside the prompt unless it is needed for the task. Teach concise, evidence-linked explanations. Do not train identifiable personal correspondence, obsolete setpoints, confidential live plant values or raw publisher pages merely because they can be collected.

### Existing first-release planning target

Retain the proposed 2,000 approved examples: 900 diagnostic examples, 400 missing-data/clarification examples, 300 calculation/tool examples, 200 grounding/citation examples and 200 uncertainty/escalation examples. These are planning allocations, not achieved quantities or experimentally established optimal ratios.

The existing topic allocation remains 700 distillation, 500 vacuum, 400 heat/steam, 200 pumps/hydraulics and 200 instrumentation/evidence-quality examples. These task and topic totals are different views of the same 2,000 records, not additive datasets.

Continue grouping 300 incident/scenario families into 180 training, 60 development and 60 locked test families before deriving examples. Keep answer keys out of training, retrieval and teacher prompts. Public cases may have appeared in foundation-model pretraining; fresh withheld cases provide stronger evidence.

## Does internal training satisfy noncommercial restrictions?

Not automatically. Creative Commons explains that the purpose of the use determines whether the NC restriction applies; the user's for-profit or nonprofit status is not itself decisive. It expressly discusses both internal company use and onward distribution. Developing a model to improve Broadbridge's engineering productivity or paid-service capability plausibly serves commercial advantage even if no source files are sold. Treat that as requiring a specific grant or a source-specific legal basis, rather than assuming the NC license covers it. [Creative Commons FAQ](https://creativecommons.org/faq/#does-my-use-violate-the-noncommercial-clause-of-the-licenses)

| Source terms | Effect of internal-only use | Proposed Broadbridge disposition |
|---|---|---|
| Material Broadbridge owns or licenses for internal AI training | Can support the intended use within the grant; third-party obligations still matter | Admit after rights and technical review |
| Genuine public-domain material or CC0 | Copyright reuse is generally available; verify provenance and other applicable rights | Prefer suitable material with documented status |
| CC BY 4.0 | Permits commercial use within its scope; internal use need not involve resale | Candidate after source-level review; preserve provenance and meet applicable conditions |
| CC BY-NC or CC BY-NC-SA | No automatic exemption for internal business benefit | Hold pending additional permission or documented legal assessment |
| Restriction only on redistribution or resale | May allow internal training if the positive grant covers necessary acts and no other clause forbids them | Read the complete agreement; do not infer from one phrase |
| Purchased books, subscriptions, manuals or unlicensed websites | Reading access does not establish a training grant | Review exact agreement and rights holder |
| Confidential expert or customer emails / work papers | Internal processing may still exceed the original engagement or data permission | Obtain an appropriate expert/customer grant and confidentiality controls |
| Bespoke internal-use license | Can authorize training and operation without permitting public datasets or model distribution | Preferred route for high-value proprietary material |

The CC BY license permits commercial reuse; the detailed conditions and other rights still need review. CC's FAQ explains that ordinary attribution requirements are tied to public sharing rather than purely internal distribution. Keeping an internal source ledger is still recommended for auditability. [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), [CC attribution FAQ](https://creativecommons.org/faq/#do-i-always-have-to-attribute-the-creator-of-the-licensed-material)

### Effect on sources previously discussed

- **PetroGPT/petro-dataset-v2:** the current dataset card labels it CC BY-NC 4.0. Do not clear internal business training merely because the dataset will not be sold. A separate permission could change its disposition; it would not eliminate source-provenance review. [Dataset card](https://huggingface.co/datasets/PetroGPT/petro-dataset-v2)
- **MIT OpenCourseWare:** its published AI terms restrict the use of trained models to noncommercial purposes. Internal business deployment should not be assumed permitted under those terms. [MIT OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/)
- **Wiley:** its standard TDM agreement is noncommercial and requires written consent for direct or indirect commercial purposes. The policy recognizes more permissive article-level licenses and statutory rights, and directs corporate subscribers to discuss appropriate arrangements. The standard agreement is not a blanket internal-business training grant. [Wiley TDM policy](https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining)
- **Norm's original material:** a tailored internal-business-use grant may be practical for material he controls. Do not assume his agreement also covers publisher-owned chapters, coauthored material, client records or third-party email contributions.
- **Norm's published books and articles:** identify the actual holder and exact edition. The author-hosted Working Guide preview carries McGraw Hill restrictions; the author hosting it is not an open-training license. [Working Guide preview](https://lieberman-eng.com/pdfs/A%20Working%20Guide%20To%20Process%20Equipment.pdf)

Under US law, fair use considers purpose, the nature and amount of the material, and market effects. Commercial purpose does not by itself defeat fair use, and internal use does not by itself establish it. The answer also depends on applicable jurisdiction and contract terms. Counsel should assess any source for which Broadbridge proposes to rely on an exception rather than a grant. This document is planning guidance, not a legal opinion. [17 USC 107](https://www.copyright.gov/title17/92chap1.html#107)

## Internal-use permission brief to negotiate

Request permission for Broadbridge Oil & Gas and any expressly named Broadbridge4096 personnel or approved processors to copy, extract, transcribe, prepare reviewed examples, train/fine-tune and evaluate models, and operate the resulting models for the agreed internal business purposes. Specify that source data will not be sold or publicly distributed. Resolve hosting, access, confidentiality, permitted excerpts, attribution and continued model use after license expiry.

Any later customer-facing service, third-party access or distribution of weights needs its own scope decision. An internal-only data restriction does not necessarily authorize serving customer questions through a trained model. Define that boundary explicitly.

This proposed scope is narrower than acquiring rights to resell a dataset, but it still needs to cover internal business benefit. No license has been accepted, no expert has been contacted and no data has been ingested through this work.
