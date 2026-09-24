"""Apply the user's gate review to the existing handoff, preserving a prior copy."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
path = ROOT/'output/foundry-infrastructure/SLM_Foundry_Broadbridge_Infrastructure_Brief.md'
backup = ROOT/'tmp/foundry-infrastructure/before-gate-review'
backup.mkdir(parents=True, exist_ok=True)
for item in [path, path.with_suffix('.docx'), ROOT/'Broadbridge-Foundry-Implementation-Update.md']:
    if item.exists() and not (backup/item.name).exists():
        shutil.copy2(item, backup/item.name)
if path.exists():
    source = path.read_text(encoding='utf-8')
else:
    # The editable Word original remains present; recover the missing Markdown
    # source from its ordered paragraphs/tables without discarding hyperlinks.
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    from docx.oxml.ns import qn
    document = Document(path.with_suffix('.docx'))
    blocks = []
    for node in document.element.body:
        if node.tag == qn('w:tbl'):
            rows = [[cell.text.replace('\n', ' ') for cell in row.cells] for row in Table(node, document).rows]
            blocks.append('\n'.join(['| ' + ' | '.join(rows[0]) + ' |', '| ' + ' | '.join(['---']*len(rows[0])) + ' |'] + ['| ' + ' | '.join(row) + ' |' for row in rows[1:]]))
        elif node.tag == qn('w:p'):
            paragraph = Paragraph(node, document)
            if node.xpath('.//w:br[@w:type="page"]'):
                blocks.append('<!-- page -->')
                continue
            if not paragraph.text.strip():
                continue
            if any(run.font.name == 'Consolas' for run in paragraph.runs):
                kind = 'json' if paragraph.text.startswith('{') else 'python'
                blocks.append('```'+kind+'\n'+paragraph.text+'\n```')
                continue
            parts=[]
            for child in node:
                if child.tag == qn('w:hyperlink'):
                    label=''.join(child.xpath('.//w:t/text()'))
                    url=document.part.rels[child.get(qn('r:id'))].target_ref
                    parts.append(f'[{label}]({url})')
                elif child.tag == qn('w:r'):
                    parts.append(''.join(child.xpath('.//w:t/text()')))
            text=''.join(parts)
            prefix={'Title':'# ', 'Heading 1':'## ', 'List Bullet':'- '}.get(paragraph.style.name,'')
            blocks.append(prefix+text)
    source='\n\n'.join(blocks)+'\n'
    (backup/'recovered-source.md').write_text(source,encoding='utf-8')
old = source.split('<!-- page -->')
assert len(old) == 13, len(old)

def section(n, title, text):
    return f'## {n} {title}\n\n{text.strip()}\n'

pages = []
pages.append('''# SLM Foundry infrastructure implementation brief

Broadbridge Oil and Gas | Broadbridge4096 | 24 September 2026 revised after Foundry review

## 1 Verified starting point and delivery status

Use the existing Foundry Qwen3-8B platform for Broadbridge Oil & Gas, a subsidiary of Broadbridge4096. This revision corrects the earlier Broadbridge update and replaces the six-week infrastructure-first sequence with Gates 0 through 3. Scope decisions and a retrieval baseline precede domain training. This task performs offline Foundry fixes and document revision only; EC2 remains unstarted by this work.

The initial scope is refining and process operations: evidence review, missing-information questions, checked calculations and engineer-reviewed diagnostic briefs. Norm Lieberman remains an illustrative expert candidate, with no appointment or source permissions assumed.

| Item and task mapping | Verified status and evidence |
| --- | --- |
| Current EC2 instance | i-0e5e1cbc7b1367566 in us-east-1, as recorded in infra/status.ps1 and docs/SLM_SERVING_BRIEF.md at commit f8f5827. The old June-plan ID i-02d15a1d9645210ad is stale. |
| B01 and B02 B04 | COMPLETE for the serving host/model setup: qwen3:8b, Q4_K_M, GPU-served on the L4. Completion is documented in docs/SLM_SERVING_BRIEF.md; no repeat setup is planned. |
| B05 | COMPLETE for end-to-end inference through localhost:11435 and closed external port 11434, per the same serving brief. Do not reopen this as a new work package. |
| Shared inference client | src/llm_client.py, mocked tests and .env.example are committed in 3fe688f after tests passed. It has think:false by default and JSON mode; it does not enforce the engineering answer schema. |
| Gate 1a and 1b | Implemented and CPU-tested on codex/broadbridge-gate1-data-training. Family splits, explicit fixture counts, assistant-only labels and local-tokenizer dry-run are covered in tests/. GPU integration remains Gate 3. |
| Gate 0 and Gate 1c to 1e | OPEN. Brad/Broadbridge must close scope and rights decisions; engineering evaluation, generic deployment and confidential-call guards remain implementation work. |
| Training host blockers | No ~/slm training venv and no slm-foundry-ec2 instance profile are reported in the serving brief. Both must be resolved before B03/B07. Serving completion does not resolve them. |

Evidence was verified from local files and commit history, not by starting or connecting to AWS. The old instance ARN also remains in infra/iam-ec2-selfmanage-policy.json; replace that obsolete policy during the later infrastructure work. The slm SSH alias used by status diagnostics can become stale after a restart. Preserve unrelated Nast, Broderick and stripe work.
''')
pages.append(section(2, 'Gate 0 scope and Gate 1 offline Foundry fixes', '''
Critical path: Gate 0 Broadbridge scope → Gate 1 Foundry readiness → Gate 2 retrieval and baseline → Gate 3 training prerequisites and experiments. No prior calendar estimate overrides a failed gate.

Gate 0 is OPEN and owned by Brad/Broadbridge. It requires no GPU and no code. Record the approved rights and exact storage location, a named technical reviewer, approximately 30 target engineering questions with reference answers, and the output schema. Each question needs source_ids, applicable numeric tolerances/units, missing-evidence expectations and critical-error criteria. The reviewer name and these assets are decisions to be supplied, not invented here.

C01 may register source leads and unresolved permissions. Nothing after C01, including proprietary extraction, dataset production or baseline processing, proceeds until Gate 0 is accepted. The generic offline Gate 1a–1b work explicitly requested in this review proceeds independently using synthetic fixtures; it does not close Gate 0 or authorize any source use.

Gate 1 runs without a GPU. Scaffold the future oil-gas pack by copying packs/_template, then adapting its name, brain-only shape, governance, schema, data references and artifact location. Remove template personas and unrelated hand/image-generation fields. Do not build a parallel pack format from scratch. Domain values are populated only after Gate 0.

| Work package | Required behavior and tests |
| --- | --- |
| 1a Complete on branch | prepare.py --group-key keeps whole families together; --fixture-splits TRAIN VAL TEST bypasses the old 50/50 minimum. tests/test_prepare.py covers disjoint groups, deterministic splits, duplicates, invalid groups/counts and small fixtures. |
| 1b Complete on branch | train.py --dry-run uses local fast-tokenizer files, prints a rendered batch, input IDs, labels, assistant mask and length statistics. Prompt/padding labels are -100. Overlength data is reported and rejected, with no silent truncation. tests/test_train.py covers these behaviors and CPU loss gradients. |
| 1c Open | evaluate.py gains --split, a pluggable judge and engineering metrics: numeric tolerance, unit equivalence, missing evidence and grounding against source_ids. Add tests/test_evaluate.py for valid/invalid units, absent evidence, unresolved citations and split selection. |
| 1d Open | Generic deploy script accepts pack/model names and builds into an adapter-hash release directory using a unique build ID. Never reuse a merge/GGUF simply because a file exists. Add tests/test_deploy_pack.py for hash/path isolation, wrong manifests and parameter propagation. |
| 1e Open | ground.py and judge.py refuse confidential packs unless an explicitly configured local OLLAMA_URL judge is approved. Both route locally with no external fallback. Add tests/test_confidential_llm.py for unset/nonlocal URLs, rejected external calls and permitted loopback tunnel use. |

Gate 1 exit requires all five work packages and the regression suite. A confidentiality flag or default localhost URL alone is not permission to send data. Keep independent technical review even when a local model assists evaluation.
'''))
pages.append(section(3, 'Gate 2 retrieval baseline and fair comparisons', '''
After Gates 0 and 1, process the first approximately 20 approved documents and the approximately 30 reviewer-approved questions. Build permission-filtered retrieval and run the existing stock qwen3:8b before training. A later authorized inference session may start the box; this document revision does not. The existing serving setup is reused, not reprovisioned.

Freeze document versions, source_ids, question IDs, reference answers, schema, retrieval/index versions and inference settings. Treat this small set as development evidence; exclude its case families from training and retain a separate acceptance set for eventual release claims. Thirty questions do not establish broad engineering reliability.

Stock qwen3:8b uses Ollama's Qwen3 template and normally enables thinking. The Foundry's fine-tuned route uses pinned ChatML. Comparing those defaults would confound template, thinking, quantization and training effects. Use the following explicitly labeled tracks.

| Track | Required method |
| --- | --- |
| S0 Product baseline before training | Stock qwen3:8b with its native Ollama template, think:false, stream:false, frozen schema/system prompt and retrieval. Record its digest/template and settings. This is the practical benchmark the proposed tuned system must improve. |
| S1 Template control before training | Create a separately named base serving artifact from the same stock GGUF with the proposed pinned ChatML template and stop tokens. Use think:false and identical evidence, context/output limits and sampling settings. Compare S1 against S0 to expose template effects. |
| B versus A Training effect at Gate 3 | Use the exact pinned Hugging Face base without an adapter (B) and with the candidate adapter (A). Render identical prompts with the same tokenizer/template and thinking policy. For serving comparisons, export both through the same pinned merge/conversion/quantization process. Do not assume the stock GGUF is identical to this base. |

Set think:false on every Ollama comparison; use temperature 0 and identical context/output limits for the controlled benchmark. On Hugging Face use the same saved ChatML template and generation settings for B and A. A custom template may ignore thinking controls: inspect rendered prompts and score unexpected reasoning/schema leakage consistently. If an explicit nonthinking prefix is needed, apply and validate it identically in training and both matched evaluation paths. Never silently change only the baseline template.

For each track record engineering accuracy, grounding/citation validity, critical errors and per-question latency; distinguish cold-start from warm latency. Preserve predictions, source IDs, retrieval results, settings and reviewer dispositions. Predeclare scoring tolerances and required improvement at Gate 0.

Gate 2 exit is a reviewed baseline report and a specific failure analysis. Authorize only bounded training experiments aimed at those gaps. Retain a tuned release only if it improves the agreed S0 benchmark and the matched B comparison without new critical errors or worse grounding. If retrieval already meets the objective or tuning fails to improve it, do not scale training.
'''))
pages.append(section(4, 'Gate 3 training prerequisites and pinned base', '''
Gate 3 begins only after the baseline and experiment decision at Gate 2. First fix both known box blockers: run infra/bootstrap.sh to establish ~/slm, and attach the slm-foundry-ec2 instance profile after confirming its S3/KMS policy is appropriate for the Gate 0 storage decision. Verify the assumed role and an allowed S3 read/write plus denied out-of-scope access. Both blockers must be closed before B03 and B07.

B03 establishes the pinned trainable checkpoint and runtime. The current bootstrap is an unpinned discovery recipe; lock the working Python 3.11, driver/CUDA, PyTorch, Unsloth, Transformers, TRL, PEFT, Datasets, Accelerate, bitsandbytes and Hub client combination after validation. Record the code commit and model/template hashes. The existing Ollama artifact is a serving baseline, not the training input.

After the environment and encrypted /data/models mount exist, resolve a revision once and download that exact snapshot. Run this only in the later authorized Gate 3 session. [R2]

```python
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

root = Path('/data/models/qwen3-8b')
root.mkdir(parents=True, exist_ok=True)
lock = root / 'base-lock.json'
if not lock.exists():
    repo = 'unsloth/Qwen3-8B'
    sha = HfApi().model_info(repo).sha
    assert sha, 'No model revision returned'
    lock.write_text(json.dumps({'repo': repo, 'revision': sha}))
spec = json.loads(lock.read_text())
target = root / spec['revision']
snapshot_download(repo_id=spec['repo'],
                  revision=spec['revision'], local_dir=target)
print(target)
```

Hash weights, config, tokenizer and template; retain the model card/license. Set model.base to the verified local path. Prove offline reload. Keep the Ollama stock digest separate. Create the matched untuned B baseline from this pinned base before interpreting any adapter gain.

B07 is the QLoRA smoke test: load → tokenize/mask audit → short train → save adapter/checkpoint → reload → generate → resume. Use explicit disjoint synthetic fixtures first. Measure VRAM, host RAM, disk and time; unload inference weights while training. Add and test bounded-step/checkpoint-resume controls before running the proposed 50-step smoke recipe. These controls and GPU integration are not claimed complete by Gate 1b.

Only after the smoke test passes run bounded experiments on approved training families. Expand toward 400 and later 2,000 reviewed examples only when learning-curve evidence supports it. Model promotion requires the comparisons in Gate 2 and independent technical acceptance.
'''))
pages.append(old[4].strip()+'\n')
pages.append(old[5].replace('Do not use src/prepare.py unchanged: its minimum 50-row validation and test allocations can empty a small training set.', 'Use --group-key case_family_id and --fixture-splits 16 8 8 on a joined working JSONL containing top-level case_family_id. Counts refer to families in grouped mode. The trainer ignores this metadata; retain the sidecar and source lineage. Legacy ungrouped row splitting still has the 50/50 minimum and now rejects an empty training set.').strip()+'\n')
train = old[6]
train = train.replace('Add the following capabilities to the domain training path while retaining existing pack behavior:', 'Gate 1b now implements answer masking and CPU inspection. The remaining GPU, checkpoint and release work stays in Gate 3:')
train = train.replace('Compute loss only on assistant answers. The current trainer flattens whole conversations and does not establish answer-only masks. Use a verified Unsloth mask or a conversational TRL implementation compatible with the selected template. Inspect token IDs and labels: prompt and padding labels must be -100; answer labels must be present. TRL assistant-only loss requires a compatible generation-aware template. [R5]', 'The implemented trainer tokenizes complete text-only ChatML conversations and assigns assistant-body/end-of-turn labels by character offsets. Prompt and padding labels are -100; a custom collator preserves them. TRL receives pretokenized records with preparation skipped. The CPU path supports the existing qwen-2.5 text contract and plain chatml; unsupported templates, images and tool-call records are rejected. Native TRL assistant-mask support is a separate option, not silently assumed. [R5]')
train = train.replace('Enforce a token budget, including answer and special tokens, before training. Keep packing disabled until sample-boundary behavior has been tested.', 'The dry-run reports min/p50/p95/max, overlength_count and truncation_count for train and development data, plus a rendered batch and masks. It returns exit 2 on overlength input and never truncates. Actual training also rejects overlength input. Packing remains disabled.')
pages.append(train.strip()+'\n')
deploy = old[7].replace('Create packs/oil-gas/brain/deploy_box.sh from the tested Nast pattern, replacing every Nast path, persona and schema. Use a unique run/release directory so existing files cannot cause stale merge or GGUF reuse.', 'Gate 1d must create deploy/deploy_pack.sh parameterized by pack and model name, adapting the proven Nast conversion pattern. Write each build under releases/<adapter_sha256>/<build_id>/ with base/template/converter hashes in its manifest. Never skip merge/conversion because an old file exists; reject conflicting artifacts and publish only a validated complete build. A pack wrapper may supply domain parameters.')
pages.append(deploy.strip()+'\n')
architecture = old[1].replace('## 2 Architecture to implement', '## 9 Infrastructure architecture after the gates')
architecture = architecture.replace('Reuse existing Foundry code and the L4 for the initial compatibility test.', 'Reuse the completed serving setup at Gate 2 and the existing L4 for Gate 3 training compatibility.')
architecture = architecture.replace('Existing single L4 for synthetic compatibility work;', 'Existing single L4 for Gate 3 synthetic compatibility work;')
pages.append(architecture.strip()+'\n')
security = old[2].replace('## 3 AWS identity access and storage requirements', '## 10 AWS identity access and storage requirements')
pages.append(security.strip()+'\n')
repo = old[10].replace('The paths below are proposed implementation deliverables', 'Except for completed Gate 1a–1b and the client, the paths below are proposed implementation deliverables')
repo = repo.replace('Shape A brain-only pack, foundation, artifact location, output contract and content rules.', 'Copy packs/_template first; adapt to a shape A brain-only pack, approved schema, content rules and storage.')
repo = repo.replace('| packs/oil-gas/brain/deploy_box.sh | Unique release paths, pinned conversion/template, validation and rollback support. |', '| deploy/deploy_pack.sh and tests/test_deploy_pack.py | Gate 1d generic pack/model parameters, adapter-hash build directories, pinned conversion/template and rollback. |')
repo = repo.replace('Existing files needing bounded changes: src/train.py for optional masking/resume/step controls; infra/status.ps1 for dynamic host resolution; environment-specific self-stop policy generation instead of the obsolete instance ARN. Add domain splitting and evaluation without silently changing other packs\' behavior. Reuse src/llm_client.py for approved text calls during the later integration task; keep vision extraction separate.', 'Completed: src/prepare.py and tests/test_prepare.py; src/train.py and tests/test_train.py; the committed shared client. Still open: src/evaluate.py --split/judge/engineering metrics; confidential-call guards in src/ground.py and src/judge.py; generic deployment; bounded-step/resume controls. Fix stale self-stop policies and SSH-alias handling during the later infrastructure work. Keep vision extraction separate.')
pages.append(repo.strip()+'\n')
accept = old[11].replace('Use current regional quotes at F02;', 'Use current regional quotes when Brad approves Gate 3;')
accept = accept.replace('At kickoff the Managing Director confirms account/storage ownership and spend authority; Head of Product & AI confirms staff and scope; shared IT/security confirms identity/network controls; Technical Director confirms evidence and evaluation criteria; Knowledge Engineer confirms the first admitted assets. Infrastructure can start with synthetic fixtures while content rights are resolved.', 'Gate 0 remains an explicit open Brad/Broadbridge decision: rights, storage location, named technical reviewer, approximately 30 questions with reference answers, and output schema. Generic offline Foundry tests use synthetic fixtures; no Broadbridge processing after C01 proceeds until this is resolved. Gate 3 cloud activity needs a later authorized session and the closed baseline gate.')
pages.append(accept.strip()+'\n')
refs = old[12].replace('six-week schedule', 'gate sequence').replace('during F05', 'during Gate 3')
refs = refs.replace('The six-week estimate covers infrastructure and a bounded training demonstration, not the previous 24- or 31-week whole-program commitments.', 'Gates 0–3 replace the prior six-week infrastructure-first estimate. Rebaseline dates after Gate 0 and the retrieval benchmark; previous 24- or 31-week whole-program estimates are not renewed commitments.')
refs = refs.replace('The immediate Foundry handoff is F01 through F06: inventory, establish the Broadbridge boundary, provision controlled storage/access, prepare the GPU host, download a pinned trainable Qwen3-8B checkpoint, and prove a synthetic train/save/reload cycle. Follow with source processing, domain evaluation and controlled release.', 'Immediate handoff: Brad resolves Gate 0; review the completed Gate 1a–1b branch and client commit; then implement and test Gate 1c–1e. Next comes the approved-document retrieval/stock-model baseline, then both host prerequisites, B03 and B07. B01/B02/B04/B05 remain complete per docs/SLM_SERVING_BRIEF.md at f8f5827. This revision makes no new AWS connection, training or engineering-performance claim.')
pages.append(refs.strip()+'\n')
path.write_text('\n\n<!-- page -->\n\n'.join(pages), encoding='utf-8')
print(path)
