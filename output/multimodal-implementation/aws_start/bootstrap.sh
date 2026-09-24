#!/usr/bin/env bash
set -euo pipefail
# Run on the EC2 Linux host after activating its documented PyTorch environment.
# This file does not launch infrastructure or change AWS permissions.
python -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__)'
python -m venv --system-site-packages /srv/broadbridge/venv
source /srv/broadbridge/venv/bin/activate
python -c 'import torch; print("torch=="+torch.__version__)' > /srv/broadbridge/torch-constraint.txt
python -m pip install --upgrade -c /srv/broadbridge/torch-constraint.txt \
  transformers accelerate huggingface_hub pillow safetensors
python -m pip check
python -c 'import torch; from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(); print(torch.cuda.get_device_name(0))'
python -m pip freeze > /srv/broadbridge/candidate-requirements.txt
nvidia-smi > /srv/broadbridge/gpu-inventory.txt
# This is a candidate runtime. Freeze it for reuse only after B05 and B07 pass.
