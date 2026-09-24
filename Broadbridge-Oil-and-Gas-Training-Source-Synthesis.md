# Broadbridge Oil and Gas training sources
Public data models and expert knowledge for SLM training
Research reviewed 23 September 2026

## 1 Recommended source strategy

Build Broadbridge Process SLM around a general open-weight model, a small body of licensed expert cases, and a versioned technical reference library. Public material supplies fundamentals and evidence; experts supply the diagnostic distinctions that make those fundamentals useful at a plant. This sourcing program supports Broadbridge Oil & Gas, a subsidiary of Broadbridge4096, and the existing refining-first development plan.

Start with distillation and vacuum troubleshooting. Steam, heat transfer, pumps and instrumentation provide supporting context. Broad petroleum, chemistry and geoscience collections should enter only when they address a measured gap in that scope. Model size, download counts and dataset row counts do not demonstrate refinery competence.

| Input layer | What to acquire | How it contributes |
|---|---|---|
| Foundation model | Qwen3-8B and a 4B challenger; an alternative from Mistral [M01](https://huggingface.co/Qwen/Qwen3-8B) [M02](https://huggingface.co/Qwen/Qwen3.5-4B) [M03](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512) | Starting weights for supervised fine-tuning; general language and tool-use behavior. |
| Public engineering references | Selected DOE sourcebooks, EPA process descriptions and CSB investigations [P01](https://www.energy.gov/cmei/ito/steam-systems) [P02](https://betterbuildingssolutioncenter.energy.gov/better-plants/process-heating) [P04](https://www.csb.gov/bp-america-texas-city-refinery-explosion/) [P05](https://www.epa.gov/air-emissions-factors-and-quantification/ap-42-fifth-edition-volume-i-chapter-5-petroleum-1) | Citable retrieval and reviewed fundamentals, evidence and escalation examples. |
| Licensed expert knowledge | Original case capture with experts such as Norman Lieberman; published works require separate rights [K01](https://www.lieberman-eng.com/personnel.htm) [K02](https://www.sciencedirect.com/book/monograph/9780128161616/understanding-process-equipment-for-operators-and-engineers) | Diagnostic questions, competing explanations, counterexamples and boundaries. |
| Engineering tools | CoolProp properties and selected IDAES models [P07](https://github.com/CoolProp/CoolProp) [P08](https://github.com/IDAES/idaes-pse) | Checkable calculations and simulated examples with declared assumptions. |
| Customer evidence | Explicitly permitted site records [K05] | Tenant-specific retrieval; optional shared examples only when the grant permits it. |

### Initial acquisition priorities

Prioritize one lead process expert, one independent reviewer, three DOE sourcebook collections, one carefully reconstructed CSB case, a small licensed reference library and two model candidates. Preserve the 2,000-example training target. Do not begin with a bulk collection of millions of petroleum-tagged rows.

This brief and the accompanying 32-entry source register are a sourcing assessment. The listed materials have not been ingested, licensed on Broadbridge’s behalf, or approved for production training. Candidate experts have not been contacted or appointed. Source IDs in brackets link to the reviewed public pages; the register records rights evidence and the next acquisition action.

## 2 Public sources for the refining launch

| Source | Useful knowledge and proposed artifact | Admission condition |
|---|---|---|
| DOE Steam Systems [P01](https://www.energy.gov/cmei/ito/steam-systems) | Steam generation, distribution, condensate and heat-transfer context. Produce short cited explanations and missing-data questions. | Check each document and third-party contribution; retain edition. |
| DOE Process Heating [P02](https://betterbuildingssolutioncenter.energy.gov/better-plants/process-heating) | Heat balances, heating efficiency and system-performance vocabulary. Produce reviewed fundamental examples. | Use cleared passages; an efficiency guide is not a site operating procedure. |
| DOE Pumping Systems [P03](https://betterbuildingssolutioncenter.energy.gov/better-plants/pumps) | Pump/system relationships and performance evidence. Add supporting diagnostic questions. | Review contributed material, including industry-association content. |
| CSB refinery investigations [P04](https://www.csb.gov/bp-america-texas-city-refinery-explosion/) | Event sequences, evidence gaps and escalation failures. Create historical cases with an explicit decision time. | Review report attachments and rights; keep final findings out of pre-event prompts. |
| EPA AP 42 Chapter 5 [P05](https://www.epa.gov/air-emissions-factors-and-quantification/ap-42-fifth-edition-volume-i-chapter-5-petroleum-1) | Refinery process taxonomy and emissions context. Build a versioned glossary and reference collection. | Record the applicable section and date; validate intended use of factors. |
| CoolProp [P07](https://github.com/CoolProp/CoolProp) | Property calculations for approved fluids and ranges. Produce tool calls with units, outputs and validation records. | MIT software license; check backends, ranges and property-model suitability. |
| IDAES [P08](https://github.com/IDAES/idaes-pse) | Balances and constrained process simulations. Generate controlled perturbations and tool exercises. | BSD-style terms; audit dependencies and validate the model. Simulations are not plant observations. |
| EIA Open Data [P06](https://www.eia.gov/opendata/) | Refinery throughput, capacity and energy context. Use a dated API/tool feed. | Preserve series definitions and revisions; aggregate statistics are not troubleshooting labels. |

DOE distinguishes government information from protected contributed content. Its policy supports selecting and attributing cleared material, not declaring every hosted PDF reusable. EPA likewise notes document-specific copyright conditions. The source register links these policies. This review identifies collections and intended uses; acquisition must inspect the actual files and passages.

### Additional data with narrower uses

NIST Chemistry WebBook is valuable for property validation, but Standard Reference Data has a distinct copyright regime; bulk reuse needs its own review [P09](https://webbook.nist.gov/chemistry/). Volve is a later upstream resource under custom terms, including restrictions on selling the licensed material [P10](https://www.equinor.com/energy/volve-data-sharing). NETL EDX is a discovery portal whose individual datasets require separate selection and rights checks [P11](https://edx.netl.doe.gov/). Neither is a substitute for refining cases.

## 3 Existing models and their roles

Use existing models in four distinct ways: starting weights, a drafting teacher, passage embeddings and passage ranking. A language model is not a verified source of engineering facts. Preserve the selected model’s license, revision, tokenizer, chat template and training configuration separately from the rights ledger for data.

| Exact Hugging Face repository | Role and recommendation | Check before selection |
|---|---|---|
| Qwen/Qwen3-8B [M01](https://huggingface.co/Qwen/Qwen3-8B) | Primary 8B-class baseline for the planned adapter. Official card lists Apache 2.0. | Measure refining performance before and after tuning with identical retrieval and tools. |
| Qwen/Qwen3.5-4B [M02](https://huggingface.co/Qwen/Qwen3.5-4B) | Smaller challenger; official card lists Apache 2.0. Use text-only scope initially. | Validate hybrid architecture, adapter targets and serving compatibility; vision capability is outside v1. |
| mistralai/Ministral-3-8B-Instruct-2512 [M03](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512) | Alternative, with an 8.4B language model and vision encoder. Apache 2.0. | Card describes FP8 instruction weights; establish a supported training format and reload test. |
| Qwen/Qwen3-32B [M04](https://huggingface.co/Qwen/Qwen3-32B) | Optional locally hosted teacher and larger-model comparison. Apache 2.0. | Draft only from cleared evidence. An independent expert accepts the answer; teacher output is not ground truth. |
| Qwen/Qwen3-Embedding-0.6B [M05](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) | Embedding baseline for semantic retrieval. Apache 2.0. | Compare with lexical search and a hybrid combination using engineer-labeled relevant passages. |
| Qwen/Qwen3-Reranker-0.6B [M06](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | Rank retrieved passages by relevance. Apache 2.0. | Measure retrieval quality and latency separately from answer quality. |

### How to use a teacher model

Give the teacher an authorized evidence packet and an approved task template. Ask for a concise diagnostic brief, missing-data questions or a tool-use example. Preserve supporting passage IDs and calculation outputs. Reject unsupported claims, copied protected passages and implausible variations; then obtain expert review. Synthetic examples inherit the permission constraints of their inputs.

Maintain the existing QLoRA/SFT approach and compare it with the untuned model plus the same retrieval and tools. Treat model merging, broad continued pretraining and training from scratch as separate experiments requiring evidence of need. Do not send private expert or customer material to a hosted teacher unless the agreement and approved hosting controls permit that processing.

## 4 Domain models and datasets that need qualification

| Asset | Finding from the reviewed source | Broadbridge decision |
|---|---|---|
| PetroGPT model [M07](https://huggingface.co/PetroGPT/Llama-3-Petro-Instruct-v1) | Llama-3-Petro-Instruct-v1 labels itself Apache 2.0 but identifies a Llama 3 base. | Hold pending license-chain and data-provenance review; no demonstrated advantage for this refinery task. |
| PetroGPT dataset [D01](https://huggingface.co/datasets/PetroGPT/petro-dataset-v2) | petro-dataset-v2 lists CC BY-NC 4.0; the displayed examples include broad chemistry topics. | Exclude from commercial training and teacher generation unless separate rights are secured. |
| GeoGPT model [M08](https://huggingface.co/GeoGPT-Research-Project/GeoGPT-R1-Preview) | GeoGPT-R1-Preview is a 72B geoscience model under custom terms; its card specifies noncommercial research/education. | Hold commercial deployment and distillation use pending permission. It is outside the launch SLM size and domain. |
| GeoGPT CoT QA [D02](https://huggingface.co/datasets/GeoGPT-Research-Project/GeoGPT-CoT-QA) | 39,393 generated geoscience QA records; card lists CC BY 4.0 and source-publication license metadata. | Potential later subset after DOI, answer and relevance review. Dataset rights differ from model rights. |
| PETRA [D03](https://huggingface.co/datasets/petra-2026/PETRA) | Retrieval/reranking collection; license field says other. Displayed source chunks include unrelated subject matter. | Hold bulk ingestion; inspect source permissions and relevant labels before any retrieval experiment. |
| PetroBench [D04](https://huggingface.co/datasets/my2000cup/PetroBench) | Hugging Face card lists MIT and a test split; the viewer shows schema/encoding issues in some material. | Secondary evaluation candidate after cleanup and technical review. Keep it out of training. |
| FormationEval [D05](https://github.com/AlmazErmilov/FormationEval-an-Open-Benchmark-for-Oil-Gas-Geoscience-MCQ-Evaluation) | Original 505-question petroleum-geoscience track; repository CC BY 4.0 with separate notices for imported tracks. | Use for later regression only after source review. MCQ performance does not validate refining diagnosis. |

ChemLLM addresses chemistry and molecular science. Its card distinguishes code licensing from model-weight terms and requests commercial-license contact; defer it for this launch [M09](https://huggingface.co/AI4Chem/ChemLLM-7B-Chat). MIT OpenCourseWare’s published AI policy restricts commercial training, so exclude it without separate permission [D06](https://ocw.mit.edu/pages/privacy-and-terms-of-use/).

These dispositions are acquisition recommendations, not a model bake-off or a legal clearance. The reviewed PetroBench repository and a 2026 paper share a name; this brief does not assume they are the same release. No public benchmark should be presented as an unseen test of a foundation model whose pretraining data is unknown.

## 5 Proprietary domains worth capturing

The most valuable expert contribution is a record of what changed the diagnosis: the observation that ruled out a tempting explanation, the measurement that mattered, the limit of a rule of thumb, and the circumstances requiring escalation. Capture those distinctions in original, rights-cleared cases with observable outcomes and independent review.

| Knowledge domain | Expert or content route | Training artifact |
|---|---|---|
| Distillation and vacuum systems | Norman Lieberman as an illustrative candidate; separately licensed published references [K01](https://www.lieberman-eng.com/personnel.htm) [K02](https://www.sciencedirect.com/book/monograph/9780128161616/understanding-process-equipment-for-operators-and-engineers) | Competing diagnoses, evidence selection, misleading readings, operating-regime boundaries and counterexamples. |
| Equipment and operator reasoning | Norman and Elizabeth Lieberman expertise; their coauthored and individually published work requires title-level review [K01](https://www.lieberman-eng.com/personnel.htm) [K02](https://www.sciencedirect.com/book/monograph/9780128161616/understanding-process-equipment-for-operators-and-engineers) | Translation of field observations into testable engineering questions, with units and instrument context. |
| Distillation diagnostics review | Henry Kister’s published diagnostic work and a qualified independent fractionation reviewer [K03](https://onlinelibrary.wiley.com/doi/book/10.1002/9781119640165) | Independent challenge cases, falsification questions and reviewer rubrics. |
| Rotating equipment and controls | Contract qualified pump, compressor and instrumentation specialists; obtain exact OEM references [K06] | Equipment-specific evidence requirements; distinguish sensor faults from process behavior. |
| Gas conditioning and processing | Potential institutional licensing and specialist instruction through PetroSkills/Campbell materials [K04](https://www.petroskills.com/en/training/courses/gas-conditioning-and-processing-g-4~p2995) | Later dehydration, treatment and processing curricula after practice approval. |
| Actual site incidents | Customer operators, process engineers and reliability teams under a data agreement [K05] | Timestamped observations, approved interventions, outcomes and unresolved uncertainties. |

### Expert acquisition package

Propose a lead-expert engagement for original interviews and case development, plus a separately assigned reviewer. Plan an initial 8–12 recorded sessions of 60–90 minutes, supported by preparation and follow-up. This is a proposed workload, not an appointment or a guarantee of case yield. Secure recording and transcription rights before capture.

License original interviews and published material separately. Specify retrieval, fine-tuning, synthetic derivatives, customer display, academy reuse, sublicensing and post-termination model use. Confirm publisher, coauthor, employer and former-client interests. Use retainers and scoped licensing; any equity remains a Broadbridge4096 decision. Name and likeness permissions do not imply expert endorsement of generated answers.

## 6 Training curriculum and source mixture

Use the existing target of 2,000 approved SFT examples as a planning constraint. The proposed mixture below allocates each record to its principal source; all contributing sources remain in its lineage. It is a curation target, not a claim that these examples already exist or an empirically optimal training ratio.

| Principal source | Diagnosis | Missing data | Tool use | Grounding | Escalation | Total |
|---|---|---|---|---|---|---|
| Original expert cases | 600 | 250 | 0 | 50 | 100 | 1000 |
| Cleared public sources | 180 | 80 | 0 | 150 | 90 | 500 |
| Validated simulations and tools | 0 | 0 | 300 | 0 | 0 | 300 |
| Explicitly licensed customer cases | 120 | 70 | 0 | 0 | 10 | 200 |
| Total | 900 | 400 | 300 | 200 | 200 | 2000 |

This is 50% original expert material, 25% cleared public material, 15% validated calculations/simulations and 10% customer cases. If shared customer rights are unavailable, replace that 200-record allocation with cleared original expert cases while preserving the task totals. Teacher-generated variants remain in their source category and are separately tagged as synthetic; they do not count as new independent incidents.

| Proposed topic emphasis | Examples | Scope |
|---|---|---|
| Distillation | 700 | Launch diagnostic workflow |
| Vacuum systems | 500 | Launch diagnostic workflow |
| Heat transfer and steam | 400 | Supporting equipment and calculations |
| Pumps and hydraulic context | 200 | Supporting evidence within launch cases |
| Instrumentation and evidence quality | 200 | Sensor context, uncertainty and escalation |
| Total | 2000 | No upstream or drilling capability implied |

### Separate source families before generating examples

Retain the program target of 300 incident/scenario families: 180 training, 60 development and 60 locked test. Derive the 2,000 training examples only from approved training families. Group incident retellings, book chapters, translations, paraphrases and simulation variants before splitting. Split simulation families by meaningful regime or topology, not adjacent random parameter rows.

The existing acceptance suite remains 120 tasks from 60 locked cases plus 180 challenge prompts. Public historical cases are useful regression material but may already be known to base models. Use fresh, confidential, expert-reviewed cases to assess generalization; label synthetic cases and public cases separately in results.

## 7 Turn sources into auditable training records

Use a controlled transformation pipeline: select a business task, clear its sources, preserve the originals, extract evidence, group related material, assign a split, author examples, verify engineering content and publish a versioned release. Retrieval indexing follows the same rights and split controls as training.

| Stage | Required result | Accountable owner |
|---|---|---|
| Source selection and capture | Document/version ID, original file hash, rights evidence, exact page or timestamp and capture date. | Knowledge Engineer |
| Technical interpretation | Units, stream/equipment identity, measurement reliability, boundary conditions and observed versus inferred facts. | Technical Director |
| Case authoring | Decision-time prompt, approved evidence, answer rubric and permitted tool calls; source lineage retained. | Knowledge Engineer |
| Calculation validation | Reproducible tool inputs, software/model version, range checks and independently checked result. | Process Applications Engineer |
| Independent review | Reviewer findings, technical corrections and acceptance record; reviewer did not author the item. | Technical Director |
| Dataset release | Frozen manifest, source permissions, family split, deduplication report and tested export. | Head of Product & AI |

### Illustrative case structure

Example topic: a vacuum column’s reported absolute pressure has risen while separation performance has deteriorated. This is an original outline for authoring, not a validated plant diagnosis or an account attributed to Lieberman.

The prompt includes only available observations and their timestamps. The target response identifies what can and cannot be concluded, asks for gauge basis and instrument verification, and organizes the evidence needed to distinguish process-load, condensation and vacuum-system explanations. It requests approved calculations where needed and states the boundary for specialist review. It does not invent a setpoint or issue a control action.

Attach an expert-authored rubric listing plausible hypotheses, discriminating observations, unsupported leaps and escalation conditions. Keep the actual resolution and post-event findings in a separately protected answer record. Derive a diagnostic task, a missing-data task and a counterexample within the same family and split. Only accepted records enter the training release.

Train concise explanations tied to observable evidence and tool results. Preserve disagreement and unresolved cases as uncertainty examples; do not force every incident into a confident single-cause answer. Remove duplicated passages, OCR mistakes, contradictory units and embedded document instructions before approval.

## 8 Rights provenance and evaluation controls

Use the register as an acquisition queue. Candidate means worth evaluating; Item review means the exact file or row needs review; Permission required means no grant is recorded; Hold excludes the material from the commercial pipeline; Evaluation only excludes it from training. Every entry currently says Not ingested. None of these labels records a production approval.

| Permission or asset | Record and control |
|---|---|
| Expert background material | Actual owner, title/edition, author and publisher interests; signed grant and permitted uses. |
| New interviews and cases | Recording, transcription, editing, model training, derivative examples, attribution and post-termination terms. |
| Customer and OEM content | Tenant, site and authorized purpose; separate grants for shared training, external hosting, display and redistribution. |
| Model weights and code | Base and derivative licenses, exact revisions, notices and deployment/distribution obligations. |
| Dataset lineage | Source IDs and hashes, page/timestamp, family/split, transformations, synthetic flag and teacher/tool versions. |
| Review and lifecycle | Author, independent reviewer, acceptance status, expiry, revocation, deletion obligations and affected releases. |

The Managing Director owns licensing commitments within delegation, supported by parent legal. Broadbridge4096 decides material IP transactions. The Knowledge Engineer maintains evidence; the Technical Director accepts engineering content; the Head of Product & AI enforces approved use in dataset and product releases. A free download, a book purchase or a customer’s access does not by itself record all of these permissions.

### Controls that preserve a meaningful test

Exclude held-out answer keys and resolutions from training, teacher prompts, retrieval indexes, tool responses and caches. An evaluation may retrieve authorized evidence that would have been available at the question’s decision time. This requires explicit corpus filtering; keeping test rows out of an SFT file alone is insufficient.

Audit source overlap with public benchmarks and evaluate base-model contamination where possible. Use blinded expert review, independent calculations and source-grounding checks. Report performance by topic, source class and real versus synthetic case. Keep private test answers outside general staff and customer retrieval.

Maintain separate grants for retrieval and weight training. Prefer retrieval for frequently changing or revocable content. Removing a source from storage does not prove its influence has been removed from trained weights; any training contract must address retention, post-termination rights and the handling of affected model releases.

## 9 Eight week sourcing and qualification program

| Timing | Concrete deliverable | Accountable owner |
|---|---|---|
| Weeks 1–2 | Confirm distillation/vacuum task coverage; rank the 32 sources; choose expert and reviewer candidates; define rights and family-split rules. | Technical Director |
| Weeks 1–3 | Negotiate only the required expert, publisher and pilot-data grants; record each permitted use before acquisition. | Managing Director |
| Weeks 2–4 | Prepare a proposed starter set of 20–30 selected documents or authorized excerpts; audit provenance, extraction and relevance. | Knowledge Engineer |
| Weeks 3–6 | Capture and review original expert cases; reconstruct permitted public cases; validate one property tool and one small simulation. | Technical Director |
| Weeks 5–7 | Run untuned model and retrieval comparisons using separate development material; measure supporting-passage retrieval and diagnostic quality. | Head of Product & AI |
| Week 8 | Target 50–60 cleared training families, a separate development sample and up to 500 approved training examples; provide rights, review and cost evidence for the next funding decision. | Head of Product & AI |

These are the sourcing work packages within the existing eight-week first tranche, not additional budget or new employees. The seven launch roles, contracted experts and parent shared services remain as planned. The 2,000-example/300-family target remains a later program milestone, not an eight-week promise.

### Source admission scorecard

First require valid rights for the proposed use, traceable provenance and exclusion of confidential material without permission. Then rank eligible sources on proposed weights: task relevance 35%, technical reliability 25%, case/evidence richness 20%, extraction quality 10% and acquisition effort 10%. These weights are management hypotheses. No high relevance score overrides missing rights.

Proceed with adapter training when cleared case diversity, engineering acceptance and the untuned baseline are sufficient to test a measurable improvement. Continue source capture when gaps remain; do not fill the quota with unverified synthetic answers. Require a paid customer mandate and new specialists before adding gas-processing or upstream corpora to a commercial practice.

### Deliverables to carry into the training build

Maintain the source register, signed grants, case schema, topic/task matrix, approved source library, separated case families, engineer-labeled retrieval queries, tool validation records and a dataset release manifest. The first model experiment should be reproducible from those records. Public-source findings and model-license observations in this brief are dated 23 September 2026 and must be rechecked for the chosen revisions.

The companion CSV and JSON register contain the direct source links, rights-evidence links, priority, disposition, owner and next action for all 32 entries. The existing SLM Development Plan remains the schedule, staffing, budget and release-gate reference.
