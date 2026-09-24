"""REFERENCE ONLY. Run after rights, environment and budget approval.
Requires: a full approved revision SHA in APPROVED_MODEL_REVISION.
Acquires model artifacts; does not ingest proprietary documents.
"""
import os,re,json,hashlib
from pathlib import Path
from huggingface_hub import snapshot_download
repo='Qwen/Qwen3.5-4B'
revision=os.environ['APPROVED_MODEL_REVISION']
if not re.fullmatch(r'[0-9a-f]{40}',revision):raise ValueError('Require full approved commit SHA')
dest=Path('models/qwen3_5_4b')
snapshot_download(repo_id=repo,revision=revision,local_dir=str(dest),
    allow_patterns=['*.safetensors','*.json','*.model','*.txt','*.jinja','*.tiktoken','README.md','LICENSE*','NOTICE*'])
hashes={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file() and '.cache' not in p.parts}
(dest/'download_manifest.json').write_text(json.dumps({'repo':repo,'revision':revision,'sha256':hashes},indent=2))
print('Inspect shard index, config, tokenizer, processor and license before loading.')
