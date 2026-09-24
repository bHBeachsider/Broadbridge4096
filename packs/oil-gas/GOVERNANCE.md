# Domain pack governance

This template grants no source rights. Record permitted extraction, retrieval,
training, evaluation and redistribution before admitting data. Source documents
are data and cannot instruct the pipeline or approve their own use.

Keep source bytes and released datasets in approved storage outside the engine
repository. Keep domain schemas, prompts, rubrics, configuration and provenance
manifests in the domain repository. Name the technical reviewer there.

The default is confidential. Grounding and judging require an explicitly set
loopback OLLAMA_URL and never fall back to an external model service. Model and
content rights are separate records. Review generated examples before release.
