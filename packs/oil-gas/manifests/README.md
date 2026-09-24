# Domain manifests

No source or release manifest has been approved. Gate 0 is open in pack.yaml.

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
