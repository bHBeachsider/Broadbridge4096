# Vision extraction v2 — execution record

Approved scope: tighten extraction prompts and independently check diagram connectivity before any training admission. Development experiment only; no EC2, training, cloud inference or production changes.

1. Add bounded label, direct-connection, transcription and formula profiles to the generic local Foundry client. Keep v1 behavior and receipts unchanged. Test malformed, truncated and authority-claiming outputs.
2. Add a deterministic comparison with a separately frozen, image-bound reference graph. Test crossings, junctions, arrows, omitted edges, extra edges, source mismatch and absent references. This compares graphs; it does not independently trace pixels. Synthetic geometry can test software, not approve engineering advice.
3. Freeze nine requests in Broadbridge: seven Qwen requests over the four existing synthetic images; two Granite formula crops from the existing DOE pages. No reference answers in model prompts. Preserve crop coordinates and parent hashes.
4. Run each once on the installed CPU Docker models, with a 180-second request limit. Preserve all outcomes, including failures, in a new directory. Stop the vision stack afterward.
5. Record comparison, tests and limitations; open stacked draft PRs. No dataset exporter accepts raw visual proposals. Graph matches remain unapproved until source rights, independent technical review and existing training release gates are satisfied.

Qwen v2 uses the publisher's visual sampling settings, translated to Ollama: temperature 0.7, top_p 0.8, top_k 20, repeat_penalty 1.0, presence_penalty 1.5. Seed 42; 256-token labels/transcription and 384-token connections. Formula conversion uses Granite's documented prompt and 256 tokens. Context 8192, eight CPU threads, thinking disabled. This changes prompts, schemas and decoding together; it is not a prompt-only causal comparison or held-out benchmark.

Sources: [Qwen generation settings](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct#generation-hyperparameters), [Ollama 0.34.4 option definitions](https://github.com/ollama/ollama/blob/v0.34.4/api/types.go), [Granite conversion prompts](https://ollama.com/ibm/granite-docling:258m).

Execution ledger: branches prepared from Broadbridge `16955ba` and Foundry `85dc977`. Generic work completed in Foundry draft #13 at `41c1780`; 215 relevant offline tests and all three CI jobs pass. Domain protocol tests passed and the complete domain suite returned 375 passed / 113 skipped. Tests were written first; malformed-record handling was tightened after a failing negative test. One implementation lane was retained.

Nine requests completed once each in 508.699 request-seconds. Independent fixture checks: four pass, two fail, three need review. Both incorrect connectivity proposals were rejected; zero training rows admitted. Vision Docker stopped normally; voice Docker remains healthy. See [the complete results and limitations](VISION_V2_RESULTS.md). No later-stage training or production gate was opened.
