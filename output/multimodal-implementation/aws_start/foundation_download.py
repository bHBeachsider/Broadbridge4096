"""Run on AWS EC2. Public model download only; no proprietary data upload."""
import argparse,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
from huggingface_hub import HfApi,snapshot_download

p=argparse.ArgumentParser()
g=p.add_mutually_exclusive_group(required=True)
g.add_argument('--resolve-only',action='store_true')
g.add_argument('--revision')
p.add_argument('--root',type=Path,default=Path('/srv/broadbridge'))
a=p.parse_args(); repo='Qwen/Qwen3.5-4B'
a.root.mkdir(parents=True,exist_ok=True)
if a.resolve_only:
    info=HfApi().model_info(repo)
    result={'repo_id':repo,'revision':info.sha,'license_review':'Review upstream license before downloading','resolved_utc':datetime.now(timezone.utc).isoformat()}
    (a.root/'foundation_revision.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    raise SystemExit(0)
if not re.fullmatch(r'[0-9a-f]{40}',a.revision):
    raise SystemExit('Use the reviewed full 40-character commit SHA.')
dest=a.root/'models'/'Qwen3.5-4B'/a.revision
snapshot_download(repo_id=repo,revision=a.revision,local_dir=dest,
    allow_patterns=['*.safetensors','*.json','*.txt','*.model','*.tiktoken','*.jinja','*.md','LICENSE*','NOTICE*'])
assert (dest/'config.json').exists(),'Missing config.json'
assert list(dest.glob('*.safetensors')),'Missing safetensors weights'
for idx in dest.glob('*.safetensors.index.json'):
    for shard in set(json.loads(idx.read_text())['weight_map'].values()):
        assert (dest/shard).is_file(),f'Missing shard {shard}'
files=[]
for f in sorted(dest.rglob('*')):
    if not f.is_file() or '.cache' in f.relative_to(dest).parts or f.name=='bb_manifest.json':continue
    h=hashlib.sha256()
    with f.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    files.append({'path':str(f.relative_to(dest)),'bytes':f.stat().st_size,'sha256':h.hexdigest()})
manifest={'repo_id':repo,'revision':a.revision,'downloaded_utc':datetime.now(timezone.utc).isoformat(),'files':files}
(dest/'bb_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'model_dir':str(dest),'files':len(files),'total_bytes':sum(f['bytes'] for f in files)},indent=2))
