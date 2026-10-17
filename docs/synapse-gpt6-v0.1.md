# Zyntalic ∇ — GPT-6 adapter v0.1

Status: **experimental design branch**. This name identifies an adapter protocol, not a fine-tuned GPT-6 model or a claim about the model's internals.

## Goal
Make the existing Zyntalic engine usable from ChatGPT and other model clients without retraining a bespoke LLM. Preserve the human-readable text, generated language, deterministic inputs and honest uncertainty in one auditable response.

## Proposed operations
- `write_dual`: write original scene and request Zyntalic rendering.
- `translate`: source text -> Zyntalic with seed and lexicon version.
- `reverse`: Zyntalic -> best-effort human interpretation, never promise exact reversibility.
- `compare`: compare source and reconstructed meaning, flag ambiguity or semantic drift.
- `export`: bundle source, target, provenance and optional parallel manuscript.

## Proposed response envelope
```json
{
  "source_text": "Example source text",
  "source_language": "en",
  "zyntalic_text": null,
  "reverse_interpretation": null,
  "seed": 42,
  "engine_version": null,
  "lexicon_version": null,
  "warnings": ["Pending real engine output"]
}
```

`null` means unverified or unavailable: do not hallucinate valid Zyntalic words.

## Next implementation checks
1. Inspect deployed Hugging Face Gradio API names and request/response schemas.
2. Test one authentic deterministic translation against the existing engine.
3. Implement a thin versioned JSON/MCP bridge, not a duplicate grammar.
4. Keep an explicit human approval checkpoint for creative publication.
5. Add regression fixtures for two-way translation, ambiguity, seed reproducibility, encoding and failure cases.

Non-goals: retraining a foundation model, changing the default branch, deploying publicly, or introducing paid inference silently.
