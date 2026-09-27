# Which visual inputs can help the SLM?

The two installed vision companions prepare evidence. They do not make the
current text-only Qwen3-8B see images, and neither is an engineering verifier.

| Material | First preparation route | Review needed before training use |
| --- | --- | --- |
| Scanned reports, manuals, specifications | Page renders + native text where available; Granite document conversion | Reading order, missing text, units, equations, source/revision and rights |
| Tables, plots and calculation sheets | Preserve cells/axes and original page; compare parsed values against pixels | Headers, superscripts, scales, signs, pressure basis and arithmetic |
| PFDs, P&IDs and electrical/control diagrams | Qwen-VL observation proposals alongside native CAD metadata if available | Equipment tags, legends, junctions, arrows and cross-sheet links; never infer connectivity from proximity |
| Equipment photographs | Vision captions/observations tied to the original image | What is visibly supported versus inferred; task-specific evidence and reviewer |
| CAD/BIM and 3D models | Authorized structured export plus selected views | Native geometry/topology/units must survive; a screenshot is not the design model |
| Maps, satellite and aerial imagery | Geospatial pipeline with coordinates, capture date and resolution | Registration, scale, cloud/occlusion effects, identification uncertainty; these models are not validated remote-sensing tools |
| Video or recorded walkthroughs | Timestamped frames, speech transcript and temporal links | Sequence, movement, speaker corrections and evidence available at the decision time |

Granite is specifically a document-conversion model, not a general image
interpreter. Qwen-VL is broader, but the small local pilot cannot establish its
accuracy across these categories. Evaluate each task separately.

The installed pilot accepts rendered PNG pages/regions, not every native file
format. Large engineering sheets need legible tiles plus original sheet and
coordinate links; reducing a whole sheet until tiny tags disappear is not an
adequate ingestion method. Preserve CAD geometry, geospatial coordinates and
video timestamps alongside any image views.

## Two distinct training destinations

1. **Existing text SLM:** reviewed text/JSON, including explicit uncertainty and
   source IDs, becomes a question-answer candidate. Preserve the source image
   as evidence. Never teach a fabricated interpretation as an established fact.
2. **Future vision-language model:** store the actual image (or bounded crop), a
   question/prompt and a verified target answer or structured annotation. Use
   that model's processor/chat template and image-token handling. Text LoRA
   training code alone is not a multimodal training implementation.

A conceptual vision training record is:

```json
{
  "source_id": "source-revision-id",
  "family_id": "whole-project-family",
  "image": "relative/path/page-035.png",
  "image_sha256": "verified-full-image-hash",
  "page": 35,
  "crop_bbox": null,
  "question": "Which labels are legible and what remains uncertain?",
  "verified_answer": "Added only after independent review",
  "annotation_origin": "model proposal corrected by reviewer",
  "review_status": "pending",
  "permitted_use": "reference_only"
}
```

This illustrates the information to retain; it is not a new intake contract or
an admitted training row. Source permissions, confidentiality, actual reviewer
sign-off, held-out family history and release approval remain mandatory. Keep
multiple pages/crops/revisions from the same source family in the same split.

The next work is to score the local pilot and decide whether targeted crops,
specialist symbol detection or native CAD extraction are needed. Do not train
the vision model simply because it produced syntactically valid output.

Sources: [IBM model scope](https://ollama.com/ibm/granite-docling:258m),
[Qwen vision model card](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct).
