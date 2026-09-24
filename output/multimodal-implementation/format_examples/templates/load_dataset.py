"""Reference loader. Install the project-locked datasets and Pillow packages.
This maps canonical local paths to TRL runtime images; it does not tokenize.
Run production rights/lineage/schema checks BEFORE this adapter.
"""
from pathlib import Path
import json
from PIL import Image
from datasets import Dataset
def load_sft(jsonl_path,asset_root,allow_demo=False):
    root=Path(asset_root).resolve();rows=[]
    for line in Path(jsonl_path).read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        r=json.loads(line)
        if not allow_demo and (r['purpose']!='production_candidate' or not r['review']['technical_approval']):
            raise ValueError('Record lacks production candidate review')
        if r['split']=='test':raise ValueError('Test records cannot enter trainer')
        images=[]
        for rel in r['image_paths']:
            p=(root/rel).resolve()
            if not p.is_relative_to(root):raise ValueError('Image path outside dataset root')
            with Image.open(p) as im:images.append(im.convert('RGB').copy())
        rows.append({'prompt':r['prompt'],'completion':r['completion'],'images':images})
    return Dataset.from_list(rows)
