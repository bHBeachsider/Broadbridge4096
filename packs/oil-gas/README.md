# Broadbridge Oil and Gas domain pack

Scaffolded by copying slm-foundry/packs/_template, then replacing its example
identity and adding proposed configs/train.yaml, schemas/answer.schema.json,
prompts/system.txt and rubrics/engineering-v0.md. Gate 0 remains open in pack.yaml.
These drafts grant no source permissions or technical acceptance. Do not put
Broadbridge domain assets in slm-foundry.

From the Foundry root, use python -m src.train --pack /absolute/domain/pack
--dry-run --tokenizer-dir /local/tokenizer. Preparation and evaluation accept
the same --pack directory or pack.yaml path. Relative asset/config paths resolve
from the pack root; output_dir defaults to outputs/<name> under that pack.

This pack has no data, approved source manifests, question set or reviewer
appointment. Brad/Broadbridge must supply those and accept the draft schema
before any domain processing. Use the canonical brief under
output/foundry-infrastructure for the v0 sequence and Post-v0 roadmap.
