# Diagram target recovery: scope and acceptance

28 September 2026. Brad authorized a plan and execution on separate branches.
The diagram branch must not block the main text/calculation SLM work.

## Outcome

Deliver a reproducible, reviewer-ready deterministic extraction system, then
measure whether it meets the [metric contract](../../DIAGRAM_METRIC_CONTRACT.md)
on independently reviewed unseen drawing families. Engineering performance is
an experimental outcome, not guaranteed by completing the implementation.

Three milestones have different meanings:

1. **Software/regression:** fixes, contracts, tests and frozen regression reports.
2. **Reviewer-ready:** source-only tracing, convention checklist, evidence overlay,
   immutable correction proposals and review-time study packet.
3. **Qualified for the declared route/scope:** held-out targets and uncertainty
   requirements met, independent references and technical acceptance recorded.
   This still does not itself authorize training or production release.

## Targets

| Measure | Vector PDF/DXF | Raster |
|---|---:|---:|
| Edge precision | >=99.5% | >=99% |
| Edge recall | >=95% | >=90% |
| Direction precision when claimed | >=99.5% | >=99.5% |
| Correct direction recovery | >=95% | >=90% |
| Evidence completeness | 100% | 100% |
| Named critical errors | 0 observed | 0 observed |

Point targets describe pilots. Qualification additionally requires appropriate
95% lower bounds and preregistered cluster-aware analysis across independent
families. Zero denominators are unknown; assisted ports are not end-to-end tag
detection. PDF/DXF/raster siblings, crops and revisions stay in one family.
The existing twelve drawings remain regression data forever.

Reviewer study target: at least 50% lower median review time without increased
post-review errors, using matched different drawings and counterbalanced order.
Two raster validations mean two unseen family cohorts, not two replays.

## Constraints and ownership

- Generic extraction, validation and tests: slm-foundry.
- Domain policy, manifests, fixtures, reports and review packets: Broadbridge4096.
- Brad: rights, budget, staffing and release decisions. Bill or an appointed
  qualified reviewer: conventions, source-only reference/eligibility acceptance,
  engineering evaluation. An assistant cannot sign on their behalf.
- Existing draft PRs stay draft. New work uses `codex/diagram-target-recovery` in
  each repository, with draft successors only; no main checkout changes/merges.
- CPU/local only. No model calls, training, EC2/GPU, production writes, client
  drawings or new dataset downloads. Stop before any >1 GB download or scope
  requiring those resources. No additional prompting experiments.
- At most 38 new synthetic drawings alongside the twelve existing stress
  drawings (50 total in this stress program). Synthetic reserves are development
  discipline, not proof of real-world family independence.
- Preserve all old assets, outputs and metrics. New outputs use exclusive paths
  and hashes. Never amend gold after seeing detector results.

## Required design

Qualification preflight must fail closed on missing provenance, split leakage,
unreviewed conventions, unsigned reference/visibility decisions, missing crop
lineage, insufficient independent evidence or rights/release holds. A local
JSON name/signature flag cannot authenticate a reviewer. Offline tooling emits
pending proposals; authenticated acceptance remains a separate boundary.

Raster arrows are detected on original pixels independently of the unchanged
skeletonization input. Base-to-tip direction requires unique line attachment
and compatible orientation. Conflicts/weak evidence remain unknown. Vector
geometry retains native source entity/path identity; unexplained breaks and
unmatched off-page connectors remain unresolved.

The overlay exposes proposed paths, arrow geometry/evidence, unknowns and
rejected contacts. Reference tracing starts with a source-only view; corrections
are new pending versions, not in-place changes to scored references.

## Known starting point

Frozen regression: PDF and DXF each 23 TP / 0 FP / 1 FN, seven correct direction
claims. Raster: 16 TP / 0 FP / 8 FN and no direction claims. The remaining vector
miss is an interrupted line whose visible gap does not establish continuity.
These small, supplied-port results do not qualify any production route.

Implementation: [task plan](../plans/2026-09-28-diagram-target-recovery.md).
