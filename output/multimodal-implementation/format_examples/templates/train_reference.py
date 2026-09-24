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
