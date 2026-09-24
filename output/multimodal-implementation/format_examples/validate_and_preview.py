"""CPU demonstration. Does not download a model, call a service or train."""
from pathlib import Path
import json, hashlib
from PIL import Image
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parent
def jsonl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s.strip()]
schema=json.loads((ROOT/'schemas/sft.schema.json').read_text())
validator=Draft202012Validator(schema)
assets=jsonl(ROOT/'evidence/assets.jsonl')
evidence={r['chunk_id'] for r in jsonl(ROOT/'evidence/chunks.jsonl')}
grants=json.loads((ROOT/'evidence/rights.json').read_text())
for a in assets:
    p=(ROOT/a['path']).resolve();assert p.is_relative_to(ROOT)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
records=jsonl(ROOT/'curated/train_demo.jsonl')
seen=set();families={};runtime=[]
for r in records:
    validator.validate(r)
    assert r['example_id'] not in seen;seen.add(r['example_id'])
    assert set(r['evidence_ids']) <= evidence
    assert all('sft' in grants[g]['uses'] for g in r['grant_ids'])
    assert families.setdefault(r['family_id'],r['split'])==r['split']
    assert r['completion'][0]['role']=='assistant'
    assert all(m['role']!='assistant' for m in r['prompt'])
    count=sum(c['type']=='image' for m in r['prompt'] for c in m['content'])
    assert count==len(r['image_paths'])
    imgs=[]
    for rel in r['image_paths']:
        p=(ROOT/rel).resolve();assert p.is_relative_to(ROOT)
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:imgs.append(im.convert('RGB').copy())
    runtime.append({'prompt':r['prompt'],'completion':r['completion'],'images':imgs})
print(json.dumps({'records':len(records),'image_records':sum(bool(r['images']) for r in runtime),'runtime_columns':['prompt','completion','images'],'production_training_authorized':False}))
print('Validated fixture structure and image integrity only. No GPU/model compatibility claim.')
