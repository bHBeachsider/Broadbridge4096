"""Local-only inference check on AWS GPU. Not a domain acceptance test."""
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
