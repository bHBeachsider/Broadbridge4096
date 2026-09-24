# Proposed v0 rubric for Gate 0 acceptance

Brad/Broadbridge must name the technical reviewer and accept the approximately
30 questions, reference answers, source_ids, units and numeric tolerances before
the first document batch. This file is a draft contract, not an approved rubric.

Measure accuracy, citation membership and evidence support, missing-information
handling, critical errors and per-question latency. Score equivalent numeric
values after conversion into the reference unit. Absolute tolerances use that
reference unit; relative tolerances are dimensionless. Unsupported units fail.

The generic Foundry metrics only check declared structured fields and rules.
Citation membership does not prove semantic support. The appointed reviewer
adjudicates grounding and engineering correctness, including errors missed by
an LLM judge. Do not let a model certify its own answer.

Freeze S0 retrieval/model settings and question families before experiments.
Require the adapter to beat the predeclared S0 accuracy threshold with no new
critical errors; also compare the exact pinned base under identical ChatML,
thinking and decoding settings. Record each reviewer disposition. Retain a
separate acceptance set for later broader release claims.
