# Domain manifests

Gate 0 is open in pack.yaml. No training release is approved.

30 September update: [evaluation_sources.json](evaluation_sources.json) records six identified sources with rights **TBD** and permission pending. The DOE pressure handbook is linked to Brad's [scoring/test-set decision](../eval/pressure-diagnostic-v1/decision.json); Bill's agreement is explicitly assumed for that exercise, not evidenced by a signature. The other five entries are source leads only. The [pressure diagnostic set](../eval/pressure-diagnostic-v1/README.md) reserves DOE-HDBK-1012 to dev/testing-only, with no training or live-run authorization.

The register was validated locally with `scripts/register_sources.py` without `--db`; no Neon rows or production permissions were changed. Source registration records identity and status, not a rights grant. Original shortlist and historical proposal receipts remain unchanged.

Record source IDs, SHA256, approved private storage URI, rights by use,
confidentiality, case family, parser/review versions and reviewer in JSON.
Dataset manifests identify frozen train/val/test families and content hashes.
Release manifests identify both repository commits, pinned base, adapter,
tokenizer/template, runtime, conversion, evaluation and rollback artifacts.

Manifests live in this domain repository when their permissions permit it;
private originals, questions/answers and datasets remain in the approved bucket
or access-controlled local pack data directory. Never copy them to slm-foundry.
Deployment manifests must follow slm-foundry/deploy/README.md and be generated
from actual files; do not invent hashes or mark an empty register approved.
