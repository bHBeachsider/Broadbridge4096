# Pressure diagnostic v1 — recorded approval and sources

Brad approved this 15-question test set and its scoring criteria in the conversation on 30 September 2026 UTC, directing that Bill's agreement be assumed for this purpose and rights remain TBD. [decision.json](decision.json) records the exact instruction, scope and source proposal hash. It records Brad's instruction; it is not a signature or completed review by Bill.

| Artifact | Purpose |
| --- | --- |
| [questions.jsonl](questions.jsonl) | Fifteen question prompts; source/family/evidence identifiers; no reference answers or hard-fail answer key |
| [answer_key.jsonl](answer_key.jsonl) | Reference answers, proposed numerical tolerances and critical-error criteria; scorer/reviewer side only |
| [manifest.json](manifest.json) | Frozen hashes, question coverage, scoring rules, family allocation and remaining execution conditions |
| [Source register](../../manifests/evaluation_sources.json) | One active pressure source plus five identified leads; item-level rights TBD |

Scoring is 0 = incorrect or required answer missing; 1 = needs correction; 2 = correct and supported. A matched hard-fail criterion gives score 0 and a critical-error flag. There are no model responses, completed scores or claimed accuracy in this set.

All fifteen questions belong to **DOE-HDBK-1012**, reserved to **dev / testing-only** for this exercise. Keep related handbook volumes, versions and derivatives out of training. Because the questions and references have already been exposed during development, this is a diagnostic set, not a blind locked acceptance test. Other held-out families and the existing public-v1 allocations remain unchanged.

**Rights remain TBD / permission pending.** The set is prepared locally; no inference, external processing or training was authorized by this record. Resolve rights for the intended processing and bind the model/template/settings and bounded run before execution. Assumed expert agreement does not supply signed `case_record/1` records: this adds zero to Gate 0's 30 case-derived questions and does not replace S0-cases or the retrieval comparison.

Only the pressure set receives the recorded scoring/test approval. The five additional documents are source leads, with no acquired-file hashes invented and no automatic approval of their future questions or formulas. Neither OpenMath's known quality problems nor diagram-training gates are changed.

The original review proposal and its pending fields remain preserved under `docs/evidence/first-pressure-review-2026-09-30/`. This separate, hash-bound decision is the current disposition. It avoids rewriting historical evidence or fabricating an expert signature.
