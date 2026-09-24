from pathlib import Path
import json, hashlib, zipfile, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/multimodal-implementation'
KIT=OUT/'format_examples'
for folder in ['raw','images','evidence','curated','evaluation','schemas','templates']:(KIT/folder).mkdir(parents=True,exist_ok=True)
def write(path,text):(KIT/path).write_text(textwrap.dedent(text).lstrip(),encoding='utf-8')
def jsonfile(path,value):(KIT/path).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def lines(path,rows):(KIT/path).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
def sha(path):return hashlib.sha256((KIT/path).read_bytes()).hexdigest()

# A synthetic engineering-style plot, not an operational example or a model image edit.
write('raw/demo_measurements.csv','time_min,pressure_kpa_abs\n0,100\n1,105\n2,110\n3,115\n4,120\n')
im=Image.new('RGB',(1000,650),'white');dr=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
dr.text((85,25),'Synthetic format example   Not plant data',font=font,fill='black')
dr.text((85,72),'Pressure in kPa absolute',font=small,fill='black')
dr.line([(100,130),(100,530),(900,530)],fill='black',width=3)
for v in [100,105,110,115,120]:
    y=510-(v-100)*17;dr.text((40,y-12),str(v),font=small,fill='black');dr.line([(100,y),(900,y)],fill='#DADADA',width=1)
pts=[]
for t,v in enumerate([100,105,110,115,120]):
    x=140+t*180;y=510-(v-100)*17;pts.append((x,y));dr.text((x-6,540),str(t),font=small,fill='black')
dr.line(pts,fill='#18364D',width=4)
for x,y in pts:dr.ellipse((x-5,y-5,x+5,y+5),fill='#18364D')
dr.text((420,595),'Time in minutes',font=small,fill='black');im.save(KIT/'images/demo_pressure.png')

assets=[{'asset_id':'SYN-CSV-01','source_id':'SYN-01','family_id':'F-DEMO-TRAIN','path':'raw/demo_measurements.csv','sha256':sha('raw/demo_measurements.csv'),'mime':'text/csv','grant_id':'G-DEMO','purpose':'format_demo','state':'curated','uses':['retrieval','sft','evaluation']},
 {'asset_id':'SYN-IMG-01','source_id':'SYN-01','family_id':'F-DEMO-TRAIN','path':'images/demo_pressure.png','sha256':sha('images/demo_pressure.png'),'mime':'image/png','grant_id':'G-DEMO','purpose':'format_demo','state':'curated','uses':['retrieval','sft','evaluation'],'derived_from':'SYN-CSV-01','transform':'deterministic_plot_v1','width':1000,'height':650}]
lines('evidence/assets.jsonl',assets)
lines('evidence/chunks.jsonl',[{'chunk_id':'EV-SYN-01','source_id':'SYN-01','asset_id':'SYN-CSV-01','family_id':'F-DEMO-TRAIN','split':'train','text':'Synthetic measurement series: time0 min pressure100 kPa absolute; time4 min pressure120 kPa absolute. No equipment or cause supplied.','image_asset_ids':['SYN-IMG-01'],'locator':{'csv_rows':[2,6]},'acl_groups':['format-demo'],'grant_id':'G-DEMO','rights_state':'approved_for_demo','document_revision':'v1'}])
jsonfile('evidence/rights.json',{'G-DEMO':{'owner':'Broadbridge format demonstration','scope':'original synthetic fixture only','uses':['retrieval','sft','evaluation'],'production_approval':False,'note':'No Norm Lieberman, customer or publisher material is present.'}})
sys={'role':'system','content':[{'type':'text','text':'Answer only from supplied evidence. State missing information. Cite the provided evidence ID.'}]}
def record(id,question,answer,images):
    return {'schema_version':'bb-sft-1','example_id':id,'family_id':'F-DEMO-TRAIN','split':'train','purpose':'format_demo','source_ids':['SYN-01'],'evidence_ids':['EV-SYN-01'],'grant_ids':['G-DEMO'],'review':{'state':'format_checked','author':'synthetic_fixture_builder','reviewer':'fixture_validator','technical_approval':False},'image_paths':images,'prompt':[sys,{'role':'user','content':([{'type':'image'}] if images else [])+[{'type':'text','text':question}]}],'completion':[{'role':'assistant','content':[{'type':'text','text':answer}]}]}
records=[record('DEMO-TEXT-01','Evidence EV-SYN-01: pressure rose from100 to120 kPa absolute between0 and4 minutes. What was the change?','The increase was20 kPa over4 minutes. The supplied values do not establish a cause. [EV-SYN-01]',[]),record('DEMO-VIS-01','The attached plot is evidence EV-SYN-01. Describe the direction of change and state whether it establishes an equipment fault.','Pressure increases over the displayed interval. The plot alone does not establish an equipment fault because equipment identity, operating context and corroborating measurements are absent. [EV-SYN-01]',['images/demo_pressure.png'])]
lines('curated/train_demo.jsonl',records)
lines('curated/families.jsonl',[{'family_id':'F-DEMO-TRAIN','split':'train','source_ids':['SYN-01'],'example_ids':[r['example_id'] for r in records],'purpose':'format_demo'}])
jsonfile('evaluation/task_format_example.json',{'task_id':'EVAL-TEMPLATE-01','family_id':'TO_BE_ASSIGNED_FROM_SEPARATE_TEST_FAMILY','split':'test','prompt_asset_ids':[],'question':'Template only. Author a new question from an independent test family.','gold_stored_elsewhere':True,'rubric':{'critical_error':False,'accepted_without_material_correction':False},'production_approval':False})
schema={'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Broadbridge canonical SFT record','type':'object','additionalProperties':False,'required':list(records[0]),'properties':{
 'schema_version':{'const':'bb-sft-1'},'example_id':{'type':'string','minLength':1},'family_id':{'type':'string','minLength':1},'split':{'enum':['train','dev','test']},'purpose':{'enum':['format_demo','production_candidate']},'source_ids':{'type':'array','minItems':1,'items':{'type':'string'}},'evidence_ids':{'type':'array','minItems':1,'items':{'type':'string'}},'grant_ids':{'type':'array','minItems':1,'items':{'type':'string'}},'review':{'type':'object','required':['state','author','reviewer','technical_approval'],'properties':{'state':{'type':'string'},'author':{'type':'string'},'reviewer':{'type':'string'},'technical_approval':{'type':'boolean'}},'additionalProperties':False},'image_paths':{'type':'array','items':{'type':'string'}},'prompt':{'type':'array','minItems':1,'items':{'$ref':'#/$defs/message'}},'completion':{'type':'array','minItems':1,'maxItems':1,'items':{'$ref':'#/$defs/message'}}},'$defs':{'message':{'type':'object','required':['role','content'],'additionalProperties':False,'properties':{'role':{'enum':['system','user','assistant']},'content':{'type':'array','minItems':1,'items':{'oneOf':[{'type':'object','required':['type','text'],'properties':{'type':{'const':'text'},'text':{'type':'string'}},'additionalProperties':False},{'type':'object','required':['type'],'properties':{'type':{'const':'image'}},'additionalProperties':False}]}}}}}}
jsonfile('schemas/sft.schema.json',schema)
write('validate_and_preview.py',r'''
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
''')
write('templates/load_dataset.py',r'''
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
''')
write('templates/download_model.py',r'''
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
''')
write('templates/train_reference.py',r'''
    """REFERENCE RECIPE, NOT GPU-VALIDATED. No invocation is made by this kit.
    Required implementation gates: B02-B07, D09-D10, F03-F04.
    Project must create approved_training_config.json; do not bypass its checks.
    Exact targets, packages, masks and image budget must pass on the chosen model.
    """
    import json, torch
    from pathlib import Path
    from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
    from peft import LoraConfig, get_peft_model
    from trl import SFTConfig, SFTTrainer
    from load_dataset import load_sft
    cfg=json.loads(Path('approved_training_config.json').read_text())
    for key in ['rights_approved','dataset_audit_passed','token_preflight_passed','mask_test_passed','smoke_reload_passed']:
        if cfg.get(key) is not True:raise ValueError(f'Missing gate: {key}')
    if not cfg['target_modules']:raise ValueError('Explicit audited language-module names required')
    processor=AutoProcessor.from_pretrained(cfg['base_dir'],local_files_only=True,trust_remote_code=False)
    model=Qwen3_5ForConditionalGeneration.from_pretrained(cfg['base_dir'],torch_dtype=torch.bfloat16,local_files_only=True,trust_remote_code=False)
    targets=cfg['target_modules']
    names={n for n,_ in model.named_modules()}
    if not set(targets)<=names:raise ValueError('Adapter target does not exist in this revision')
    if any('visual' in n.lower() or 'vision' in n.lower() for n in targets):raise ValueError('Visual targets excluded from initial recipe')
    model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,bias='none',target_modules=targets,task_type='CAUSAL_LM'))
    model.print_trainable_parameters()
    train=load_sft(cfg['train_jsonl'],cfg['asset_root'])
    dev=load_sft(cfg['dev_jsonl'],cfg['asset_root'])
    args=SFTConfig(output_dir=cfg['output_dir'],num_train_epochs=1,learning_rate=5e-5,
        per_device_train_batch_size=1,gradient_accumulation_steps=16,bf16=True,
        max_length=None,packing=False,completion_only_loss=True,seed=17,
        report_to='none',save_strategy='epoch',logging_steps=10)
    trainer=SFTTrainer(model=model,args=args,train_dataset=train,eval_dataset=dev,processing_class=processor)
    # max_length=None is safe here ONLY after full token-length admission checks.
    # Run a mixed batch label audit and ten-step smoke test before a full run.
    trainer.train()
    trainer.save_model(cfg['output_dir'])
    processor.save_pretrained(cfg['output_dir'])
''')
jsonfile('templates/training_config_fields.json',{'status':'FIELD GUIDE ONLY; not an approved_training_config.json','required_fields':['base_dir','train_jsonl','dev_jsonl','asset_root','output_dir','target_modules','rights_approved','dataset_audit_passed','token_preflight_passed','mask_test_passed','smoke_reload_passed'],'provenance_to_record':['base_full_commit_sha','base_file_hashes','processor_revision','dependency_lock_sha256','dataset_manifest_sha256','review_approval_ids','GPU_driver_CUDA','image_pixel_budget','maximum_processed_tokens','effective_batch_size','seed','run_id','spend_limit'],'notes':'Boolean gates refer to saved review evidence, not user-toggled permissions. No real grants or hardware checks are supplied by this kit.'})
write('README.md',r'''
    # Broadbridge training format examples

    This is a format and handoff demonstration, accompanying the implementation workbook and runbook. It contains original synthetic data only. It is not an oil-and-gas training corpus, an operational diagnosis or a completed production pipeline.

    ## Run the CPU demonstration

    In a Python environment with Pillow and jsonschema installed:

    ```text
    python validate_and_preview.py
    ```

    Expected: two accepted format-demo records, one image record, runtime columns prompt/completion/images, and production_training_authorized=false. The validator does not install packages, download models, contact services or train. It checks schema, IDs, asset hashes, local paths, image validity, grant references, family consistency and image placeholder counts. It does not prove legal permissions, independent engineering correctness or token masks.

    ## Follow one record

    1. raw/demo_measurements.csv is a five-row synthetic pressure series.
    2. images/demo_pressure.png is a labeled plot of those values.
    3. evidence/assets.jsonl contains original/derived lineage and hashes.
    4. evidence/chunks.jsonl is an example searchable evidence record with a citation ID.
    5. curated/train_demo.jsonl contains a text example and an image/text example. These are two teaching views of ONE family, not two independent incidents.
    6. The JSONL stores image_paths. templates/load_dataset.py replaces these with in-memory PIL images in the images column and removes governance metadata from model input.
    7. The model's own processor converts prompt/completion/images into tokens and image tensors. That step requires the actual pinned model and is not executed here.

    The images key in runtime data is not a string URL and not a file name inserted in the question. Each image placeholder maps to an image in list order. Text-only examples use an empty list. Use the actual processor for image resizing, patch construction and chat formatting.

    ## Supplied reference templates

    - download_model.py: an explicit full revision is required. Does not fetch source documents.
    - load_dataset.py: canonical-to-runtime adapter. The caller must first validate rights, schema, lineage and data splits. A production mode refuses unreviewed fixture records and all test records.
    - train_reference.py: a Qwen3.5 LoRA recipe for implementation and smoke testing on a GPU. Requires a separately created approved_training_config.json. No model/runtime compatibility is claimed from the CPU test.
    - training_config_fields.json: configuration field guide, not executable approval.

    Current model classes and TRL APIs must be pinned and validated in B02-B07. A supported inference demo is not proof of adapter-training support. Inspect exact language modules and loss masks, and validate save/reload before accepting the environment. Keep the image encoder/projector frozen initially. Use a fresh environment for serving and verify that the adapter is actually loaded.

    ## Production additions still to build

    The task workbook specifies the quarantine handler, parsers, rights enforcement, case editor, family splitter, image annotation workflow, token preflight, retrieval service, checked tools, evaluation runner and serving application. They are not supplied as working services by these format examples. No source-register assets or model weights were acquired during plan creation.

    The evaluation file is a field-layout template only. It contains no independent held-out case. Production evaluator prompts and answers live outside the trainer's accessible storage. Do not count these fixtures toward the 2000-example or300-family targets.
''')
with zipfile.ZipFile(OUT/'Broadbridge_Training_Format_Examples.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(KIT.rglob('*')):
        if p.is_file():z.write(p,'Broadbridge_Training_Format_Examples/'+p.relative_to(KIT).as_posix())
print('Created format examples and reference templates')
