"""AWS-first instructions and reference scripts. No cloud operations at build time."""
from pathlib import Path
import json,zipfile,shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/multimodal-implementation'

AWS_ROWS=[
 ['1','B01','Launch AWS compute','Cloud implementer','EC2 console: launch g6e.2xlarge from an AWS PyTorch GPU Deep Learning AMI; select the approved VPC/subnet, instance role and no-inbound security group; add 300 GiB encrypted gp3 EBS.','SSM session opens; nvidia-smi shows GPU; save instance and AMI IDs.','AWS 2'],
 ['2','B01','Create storage and permissions','Cloud implementer','Create private S3 model, data, run and evaluator buckets with versioning and default KMS encryption. Trainer can read only released train/dev prefixes; evaluator answers use a separate role/bucket.','Record bucket names, key ARNs and roles; positive and denial access tests pass.','AWS 2'],
 ['3','B02','Install the model runtime','Applied AI Engineer','Activate the AMI PyTorch environment; run bootstrap.sh from the supplied AWS ZIP on EC2. Preserve the AMI Torch version with a constraint.','CUDA/BF16 and model-class imports pass; candidate-requirements.txt saved.','AWS 3'],
 ['4','B03','Choose an exact foundation revision','Head of Product and AI','Pin the full commit using Hugging Face repository history before AWS setup, or the helper in a developer environment. On EC2, use foundation_download.py --resolve-only to check the candidate. Download the reviewed SHA even if main has advanced.','Approved full commit SHA and license evidence recorded.','AWS 3'],
 ['5','B04','Download the foundation into AWS','Applied AI Engineer','Run foundation_download.py --revision FULL_SHA on EC2. Weights, config, tokenizer and image processor land in /srv/broadbridge/models/Qwen3.5-4B/FULL_SHA.','Shard references resolve; artifact hashes and manifest written.','AWS 3'],
 ['6','B04','Back up the model in S3','Applied AI Engineer','Copy the local revision directory to s3://MODEL_BUCKET/foundation/Qwen3.5-4B/FULL_SHA/ using aws s3 sync and KMS encryption.','List object count, verify representative downloads against local SHA256; save S3 URI.','AWS 4'],
 ['7','B05','Run text and image questions','Applied AI Engineer','Run foundation_smoke.py with --model local revision directory and --image fixtures/demo_pressure.png. Review generated text and chart answer.','baseline_smoke.json contains actual responses, timing and peak memory.','AWS 4'],
 ['8','B06 B07','Prove a training step and reload','Applied AI Engineer','Use the earlier synthetic training kit to audit language-only adapter targets and completion loss masks; execute ten optimizer steps; save/reload adapter against this exact AWS base.','Finite loss, actual parameter changes, correct masks and successful reload.','14 and 15'],
 ['9','C01 C02','Upload the first cleared source batch','Knowledge Engineer','Upload about 20 representative cleared originals with manifests to the S3 quarantine prefix. Include digital PDFs, scans and diagrams; include emails only with appropriate grants.','Every file has source ID, checksum and permitted routes.','AWS 5 and 3'],
 ['10','C03 C04 C10','Extract and normalize evidence','Applied AI Engineer','Run isolated CPU extraction/OCR workers; save ordered text/table JSONL and PNG images to the extracted prefix; verify units and critical values.','Page/region citations and reviewable derivatives reconcile to originals.','5 through 8'],
 ['11','D01 D02 D03','Create the first 400 teaching examples','Knowledge Engineer','Build case families and split first; write 300 text and 100 visual prompt/completion examples with image paths and independent expert review.','train_v0.jsonl plus image assets pass schema, rights, leakage and technical checks.','9 and 10'],
 ['12','E01 E02 F01','Establish retrieval and a measured baseline','Applied AI Engineer','Build permissioned chunks and indexes; run the unchanged foundation on dev questions both with and without retrieval; retain scores and answers.','A measured comparison exists before domain fine-tuning.','11 and 16'],
 ['13','F03 F04 F05 D06 D07','Train the first adapter then expand data','Applied AI Engineer','Fine-tune a LoRA adapter on the initial released set; compare on dev; expand to 1500 text and 500 visual examples from the planned training families.','Versioned dataset and adapter; expansion is justified by observed errors.','13 and 14'],
 ['14','F08 H03 I01 I02 I06','Evaluate and package the chosen model','Technical Director','Use untouched test families; review failures; package exact base revision, adapter, processor, runtime and retrieval-index revision.','Independent acceptance evidence and reproducible release manifest.','15 and 16'],
 ['15','H01 H02 H04 G4 J01 J02','Deploy internally and pilot','Head of Product and AI','Deploy private authenticated service on separate AWS serving capacity; add source citations, logs, feedback, monitoring and rollback; run supervised internal briefs.','Approved users can submit text/images; quality, latency, cost and corrections are measured.','17 and 18']
]

AWS_REFS=[
 ['AWS01','EC2 G6e instance specifications','https://aws.amazon.com/ec2/instance-types/g6e/','Initial 48 GB GPU candidate; validate training memory on actual batches'],
 ['AWS02','AWS Deep Learning AMI releases','https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html','Choose regional PyTorch GPU AMI and record exact image ID'],
 ['AWS03','Session Manager prerequisites','https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-prerequisites.html','Agent, instance role and outbound connectivity'],
 ['AWS04','S3 sync command','https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html','Copy snapshots, datasets and run artifacts']
]

BOOTSTRAP='''#!/usr/bin/env bash
set -euo pipefail
# Run on the EC2 Linux host after activating its documented PyTorch environment.
# This file does not launch infrastructure or change AWS permissions.
python -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__)'
python -m venv --system-site-packages /srv/broadbridge/venv
source /srv/broadbridge/venv/bin/activate
python -c 'import torch; print("torch=="+torch.__version__)' > /srv/broadbridge/torch-constraint.txt
python -m pip install --upgrade -c /srv/broadbridge/torch-constraint.txt \\
  transformers accelerate huggingface_hub pillow safetensors
python -m pip check
python -c 'import torch; from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); print(torch.cuda.get_device_name(0))'
python -m pip freeze > /srv/broadbridge/candidate-requirements.txt
nvidia-smi > /srv/broadbridge/gpu-inventory.txt
# This is a candidate runtime. Freeze it for reuse only after B05 and B07 pass.
'''

DOWNLOAD='''"""Run on AWS EC2. Public model download only; no proprietary data upload."""
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
'''

SMOKE='''"""Local-only inference check on AWS GPU. Not a domain acceptance test."""
import argparse,json,time
from pathlib import Path
import torch
from transformers import AutoProcessor,Qwen3_5ForConditionalGeneration

p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True)
p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('baseline_smoke.json'))
a=p.parse_args();assert a.image.is_file();assert torch.cuda.is_available()
assert torch.cuda.is_bf16_supported()
torch.cuda.reset_peak_memory_stats()
processor=AutoProcessor.from_pretrained(a.model,local_files_only=True,trust_remote_code=False)
model=Qwen3_5ForConditionalGeneration.from_pretrained(a.model,local_files_only=True,
    trust_remote_code=False,dtype=torch.bfloat16,device_map={'':'cuda:0'},attn_implementation='eager')
model.eval()
queries=[('text',[{'type':'text','text':'In two sentences explain the purpose of a heat exchanger.'}]),
         ('image',[{'type':'image','url':str(a.image.resolve())},
                   {'type':'text','text':'Describe the visible pressure trend and quote the units. Do not diagnose its cause.'}])]
results=[]
for label,content in queries:
    inputs=processor.apply_chat_template([{'role':'user','content':content}],
        add_generation_prompt=True,tokenize=True,return_dict=True,return_tensors='pt',enable_thinking=False).to('cuda:0')
    torch.cuda.synchronize();start=time.perf_counter()
    with torch.inference_mode():
        output=model.generate(**inputs,max_new_tokens=256,do_sample=False)
    torch.cuda.synchronize()
    text=processor.decode(output[0,inputs['input_ids'].shape[1]:],skip_special_tokens=True)
    results.append({'kind':label,'response':text,'seconds':time.perf_counter()-start,'input_tokens':inputs['input_ids'].shape[1]})
report={'model_dir':str(a.model),'gpu':torch.cuda.get_device_name(0),
        'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
        'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'results':results,
        'domain_acceptance':'not evaluated'}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
'''

def pages(p,h,steps,tab,code,tasks):
    by={t['id']:t for t in tasks}
    milestone=by['B05']['finish_day']
    return [
    ('AWS 1 Download and run the foundation first',[
      p(f'The first deliverable is Qwen3.5-4B downloaded into Broadbridge AWS and running text and image inference. Begin with AWS resources and model acquisition. The revised task schedule targets this milestone by working day {milestone}, assuming the AWS account, GPU quota, network and sandbox spend envelope already exist. Account or quota delays move the date.'),
      p('Use the selected post-trained image/text checkpoint as the foundation for domain adaptation. There is no need to pretrain a model from scratch. Start with public weights and synthetic examples; expert-content acquisition and licensing proceed alongside the initial AWS work.'),
      tab(['Step','What the engineer does','Evidence of completion'],[
       ['1','Launch AWS GPU host and download the model','Pinned weights stored on EC2 and private S3'],
       ['2','Ask the unchanged model text and image questions','Saved baseline answers and memory measurements'],
       ['3','Run a tiny training and save/reload check','Working adapter-training path'],
       ['4','Upload and process a small cleared document batch','Reviewed JSONL evidence and PNG figures'],
       ['5','Create 400 reviewed training examples and retrieval index','Validated dataset plus measured baseline'],
       ['6','Fine-tune an adapter and compare with the baseline','Development-set results justify the change'],
       ['7','Expand to 2000 examples and run independent evaluation','Accepted release with documented limits'],
       ['8','Deploy privately in AWS and run supervised pilot','Measured quality, cost, feedback and rollback']],[.6,3.2,3.4]),
      p('The workbook opens with AWS start. Its numbered steps map to the detailed Tasks and Gantt tabs. This opening sequence supersedes the earlier governance-first reading order; the later format recipes and acceptance controls remain in force.')]),
    ('AWS 2 Create the AWS resources',[
      p('Implementation choice: use one EC2 GPU instance for the first experiment. This gives the engineer direct access to model files, Python, logs and adapters. Use a separate CPU worker for document parsing and separate serving capacity for the eventual pilot. SageMaker migration is optional after the workload is proven.'),
      tab(['Resource','Initial setting','Action and check'],[
       ['AWS account and region','Broadbridge sandbox; us-east-1 is an example only','Confirm residency, permissions, G6e availability, On-Demand GPU quota and a named spend owner before launching.'],
       ['EC2 GPU','g6e.2xlarge candidate','One L40S GPU with 48 GB VRAM, 8 vCPUs and 64 GiB host RAM. Measure actual training memory before committing to this size.'],
       ['AMI and disk','AWS PyTorch GPU DLAMI; 300 GiB encrypted gp3 EBS','Choose a current compatible regional AMI and record its ID. Keep durable files on EBS and S3, not local instance-store NVMe.'],
       ['Network','Private subnet with controlled outbound access','No public IP or inbound SSH. Use Session Manager. Provide NAT or approved egress for Hugging Face and package downloads; an S3 endpoint alone cannot reach them.'],
       ['S3','Four private versioned buckets','MODEL_BUCKET for weights; DATA_BUCKET for raw/extracted/released data; RUN_BUCKET for adapters/logs; EVAL_BUCKET for independent answers. Enable block-public-access and KMS encryption.'],
       ['Identity','Instance role and separate worker roles','Use temporary role credentials. Trainer reads released train/dev only and model artifacts, writes runs, and cannot read EVAL_BUCKET or raw mailboxes.'],
       ['Cost controls','Tags, budget alerts and stop schedule','Tag project and owner. Stop GPU outside booked work, preserve EBS, and archive checkpoints first. Budgets are alerts, not an automatic hard spending cap.']],[1.05,2.2,3.95]),
      steps('EC2 console → Launch instance → select the documented AWS GPU AMI and instance size. Choose the approved subnet, no-inbound security group, encrypted EBS and instance profile; require IMDSv2. Use the AWS AMI release page to verify publisher and image.','Ensure SSM Agent, AmazonSSMManagedInstanceCore-equivalent permissions and outbound SSM connectivity. Open Connect → Session Manager. Run nvidia-smi and aws sts get-caller-identity; save non-secret environment identifiers.','Create the four S3 buckets in the approved region. Add per-role S3 prefix permissions and KMS key permissions. Verify permitted reads/writes and explicit inability of the trainer to read test answers. Save aws_environment.json.')]),
    ('AWS 3 Download the foundation model',[
      p('Commands below run in Bash on the AWS Linux GPU host, not local Windows PowerShell. Download the AWS starter ZIP from this project, transfer it through approved private storage, and extract it on the host. Set real bucket names, key ARNs and the reviewed revision; no account IDs or credentials have been invented.'),
      h('Prepare the working directory and runtime'),
      code('sudo mkdir -p /srv/broadbridge\nsudo chown "$(id -u):$(id -g)" /srv/broadbridge\ncd /srv/broadbridge\n# Activate the PyTorch environment documented by the chosen AMI.\n# Extract Broadbridge_AWS_Start.zip here before the following commands.\nbash bootstrap.sh\nsource /srv/broadbridge/venv/bin/activate'),
      p('bootstrap.sh preserves the AMI Torch version, installs the model libraries, checks CUDA/BF16 and model imports, and records the candidate package set. If the model class is absent, select an explicitly reviewed Transformers release or full Git commit that implements Qwen3.5, then repeat the checks. Do not treat a successful installation as a training-compatibility result.'),
      h('Resolve and download a fixed model revision'),
      code('python foundation_download.py --resolve-only\n# Review foundation_revision.json and the model license.\nexport BB_MODEL_SHA="REPLACE_WITH_REVIEWED_40_CHARACTER_SHA"\npython foundation_download.py --revision "$BB_MODEL_SHA"\nexport BB_MODEL_DIR="/srv/broadbridge/models/Qwen3.5-4B/$BB_MODEL_SHA"\nls "$BB_MODEL_DIR"'),
      p('The download script calls Hugging Face snapshot_download with the exact revision. It obtains safetensors weight shards, configuration, tokenizer and image-processor files; verifies shard references; and writes bb_manifest.json with per-file hashes. The model directory is now the starting foundation inside AWS. Installing a Python library alone would not download these weights.'),
      p('The model uses the publisher Apache-2.0 license, subject to its terms. Preserve license and attribution records in the snapshot. This license covers the model; permissions for Norm Lieberman articles, emails and client data are separate. Other Hugging Face models are downloaded into separate directories only when required for comparison or retrieval.')]),
    ('AWS 4 Run the model and retain the baseline',[
      h('Archive the exact model in private S3'),
      code('export BB_MODEL_BUCKET="REPLACE_WITH_MODEL_BUCKET"\nexport BB_KMS_KEY="REPLACE_WITH_MODEL_BUCKET_KMS_KEY_ARN"\naws s3 sync "$BB_MODEL_DIR/" \\\n  "s3://$BB_MODEL_BUCKET/foundation/Qwen3.5-4B/$BB_MODEL_SHA/" \\\n  --exclude ".cache/*" --sse aws:kms --sse-kms-key-id "$BB_KMS_KEY"'),
      p('Compare uploaded object count with the snapshot manifest and verify sampled files after downloading them back. Record the S3 URI. Retain the local EBS copy for loading; from_pretrained loads a local model directory rather than an s3:// URI.'),
      h('Run a text question and a synthetic chart question'),
      code('mkdir -p /srv/broadbridge/runs/baseline\npython foundation_smoke.py --model "$BB_MODEL_DIR" \\\n  --image fixtures/demo_pressure.png \\\n  --output /srv/broadbridge/runs/baseline/baseline_smoke.json'),
      p('foundation_smoke.py loads the local model and processor, runs a text question and an image question on CUDA, then saves responses, latency and peak GPU memory. It does not fetch proprietary data. Review the chart response against the visible units and trend. Extend B05 with two-image ordering and empty-image checks.'),
      steps('Archive the baseline report, package inventory, AMI ID, GPU inventory and model manifest in RUN_BUCKET. First milestone is complete only after actual responses are saved.','Next perform B06 and B07 with the synthetic training kit: inspect adapter targets and loss masks, run ten optimizer steps, save and reload. This is the first proof that domain training can work on the chosen AWS environment.','Keep base weights unchanged. Save future adapters under runs/RUN_ID/adapter and release manifests under releases/RELEASE_ID. Version base, adapter, processor and runtime together.','Stop the GPU when idle through the EC2 console after checkpoints are uploaded. EBS, S3, NAT and other provisioned resources can continue to incur charges. Use measured GPU memory to choose larger hardware only if required.')]),
    ('AWS 5 Add the oil and gas data next',[
      p('Once the foundation runs, process a small representative batch end to end. A proposed first extraction batch is about 20 cleared originals. Include a digital article, scanned working paper and engineering diagram; add emails and recordings only when their uses are authorized. This batch is for proving parsing quality, not a claim that 20 files are sufficient for domain competence.'),
      tab(['Location in DATA_BUCKET','What goes there','Next operation'],[
       ['quarantine/BATCH_ID/','Original PDF DOCX EML CSV images and manifest','Isolated MIME/malware check and admission by source use'],
       ['raw/SOURCE_ID/ASSET_HASH/','Accepted immutable original and grant reference','Run the format-specific extractor on CPU'],
       ['extracted/BATCH_ID/','JSONL text and tables; page/figure PNGs','Review reading order, tags, equations, numbers and units'],
       ['curated/DATASET_REV/','Case families, annotations and review records','Split case families before producing example variants'],
       ['released/DATASET_REV/train/','train.jsonl and images/ for approved training families','Trainer copies this exact revision to local EBS'],
       ['released/DATASET_REV/dev/','Development prompts and permitted evidence','Run baseline and model comparisons; no gradient training'],
       ['retrieval/INDEX_REV/','Cited chunks, embedding metadata and index export','Load permissioned evidence retrieval; isolate test answers']],[2.15,2.5,2.55]),
      p('Independent test answers live in EVAL_BUCKET, outside trainer and production retrieval permissions. Capture S3 VersionIds and file hashes in each dataset release manifest; a prefix name alone does not prove that a dataset is immutable.'),
      steps('Apply the detailed recipes in sections 5–8: PDF/HTML to ordered text and figures; scans to OCR plus images; email to redacted thread records; recordings to reviewed transcripts and frames; numeric exports to typed tables with units.','Norm and other experts turn reviewed evidence into cases and teaching examples. Section 10 defines prompt/completion JSONL and image paths. Begin with 400 accepted examples, then expand to 2000 after reviewing initial model errors.','Build retrieval alongside the dataset, measure the unchanged AWS foundation, and then run LoRA training on the same pinned base. Section 13 covers model-native token/image processing; section 14 covers the training run.','Save the adapter to S3, reload it with the base, compare on development questions, and submit the selected release to independent testing. Only then deploy an authenticated internal service and start the supervised pilot.')])]

def build_kit():
    kit=OUT/'aws_start';kit.mkdir(exist_ok=True)
    for name,content in [('bootstrap.sh',BOOTSTRAP),('foundation_download.py',DOWNLOAD),('foundation_smoke.py',SMOKE)]:
        (kit/name).write_text(content,encoding='utf-8',newline='\n')
    (kit/'fixtures').mkdir(exist_ok=True)
    shutil.copy2(OUT/'format_examples/images/demo_pressure.png',kit/'fixtures/demo_pressure.png')
    (kit/'README.md').write_text('''# Broadbridge AWS starter

Run these reference scripts on the AWS GPU host after provisioning the resources in AWS 2 of the implementation runbook. Do not run them in local Windows PowerShell.

1. Extract this ZIP under /srv/broadbridge and activate the selected DLAMI PyTorch environment.
2. Run bash bootstrap.sh and source /srv/broadbridge/venv/bin/activate.
3. Run python foundation_download.py --resolve-only. Review and retain the exact revision and upstream license.
4. Run python foundation_download.py --revision FULL_40_CHARACTER_SHA.
5. Use the runbook S3 sync command to archive the snapshot with the real bucket and KMS key.
6. Run python foundation_smoke.py --model LOCAL_SNAPSHOT_PATH --image fixtures/demo_pressure.png --output /srv/broadbridge/runs/baseline/baseline_smoke.json.

These files were syntax checked locally. They have not been executed against AWS, a GPU, or downloaded model weights. The bootstrap selects candidate library versions; freeze the exact working environment only after the inference and train/save/reload checks pass. S3 IAM/KMS permissions and model licenses must already be configured. No credentials belong in this ZIP.

The synthetic chart is a format fixture. Passing the smoke check does not establish engineering competence. Use the companion training-format kit for the later adapter smoke test, then process cleared source files and reviewed examples according to the implementation workbook.
''',encoding='utf-8')
    with zipfile.ZipFile(OUT/'Broadbridge_AWS_Start.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in kit.rglob('*'):
            if f.is_file():z.write(f,f.relative_to(kit))

if __name__=='__main__':build_kit()
