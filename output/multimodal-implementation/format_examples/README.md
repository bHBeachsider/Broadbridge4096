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
