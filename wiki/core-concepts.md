# Core Concepts

## Determinism

Zyntalic derives pseudo-random choices from stable text keys through `zyntalic.utils.rng`. Word generation, motif choices, sigils, and fallbacks should therefore be repeatable. Determinism is tested at sentence, batch, generator-stage, and golden-output levels.

Determinism has a boundary: results can change when code, bundled lexicons, mappings, embedding backends, normalization rules, or explicit configuration change. Production consumers should record the Zyntalic version and relevant options alongside generated assets.

## S-O-V-C

The default sentence model is **Subject – Object – Verb – Context**. A lightweight parser identifies a likely verb, treats preceding tokens as subject material, and splits later material into object and context using known context markers. This is a stable heuristic, not a full syntactic analysis.

The final C has two related meanings:

- surface context, such as time, place, manner, or subordinate material;
- the machine-readable context tail at the absolute end of output.

## Context tail and sidecar

Non-reverse output is expected to end with a block shaped like:

```text
⟦ctx:han=…; frames=…; anchors=…; sigil=…; evidentiality=…⟧
```

Fields vary by engine and configuration. The tail makes metadata visible in plain text. `SentenceSidecar` in `zyntalic/ir.py` carries the richer structured equivalent for JSON consumers, including frames, pivot, anchors, sigil type, register, dialect, and scope signature.

## Mixed-script surface

The visual identity combines Hangul syllable blocks with an extended Latin alphabet influenced by Polish orthography. The core generator biases parts of speech toward different surface profiles and can repair outputs that miss those profiles. This is an artistic system inspired by multiple languages; it does not transliterate or reproduce any one of them.

## Morphology

The dedicated morphology module models an agglutinative system:

- noun number and six cases;
- verb aspect, tense, and optional evidentiality;
- derivational suffixes;
- front/back vowel-harmony selection.

The high-level translator also performs canonical rule enforcement. These layers overlap but are not identical, so documentation examples should be verified through the public translation path before being treated as normative output.

## Literary anchors

Twenty bundled public-domain literary/philosophical lexicons serve as semantic coordination points—“Schelling points.” An input embedding is compared with anchor vectors; weighted anchors then influence motifs, vocabulary, and trace metadata.

The fallback embedding is deterministic and lightweight. Optional sentence-transformer support can improve semantic similarity, while a learned projection can align embedding spaces. Manual and neutral anchor modes allow callers to control or suppress automatic selection.

Anchors are influence signals, not claims that generated text quotes, translates, or accurately represents an author.

## Mirror and chiasmus

Mirror generation explores reciprocal forms such as “A through B; B through A.” A mirror state manages motifs and connectors, while sigils encode a compact identity for the transformation. The translator can also generate an English mirror readback.

This is both a stylistic device and a structural experiment: symmetry becomes a reproducible operation rather than a prompt-only effect.

## Intermediate representation

The IR separates linguistic intent from the rendered surface:

- `Frame` identifies semantic frames and confidence;
- `PivotType` describes the structural relationship;
- `SentenceSidecar` records the selected interpretation and controls.

This separation is the foundation for future editors, visualizers, validators, alternate renderers, and narrative continuity tools.

## Scope controls

The translator accepts configuration for evidentiality, register, dialect, frames, anchor mode, and selected anchors. Register and dialect can alter the surface deterministically; the scope signature captures the chosen configuration. These are controlled variants rather than free-form style prompting.

## Rule validation and fallbacks

The translation pipeline canonicalizes output and checks context-tail finality, required role markers, script profile, and S-O-V-C-related expectations. The staged generator includes deterministic fallbacks so missing optional resources should degrade capability rather than crash the core path.

## Optional enhancement

NumPy is the required dependency. FastAPI, PDF extraction, desktop UI, spaCy, and sentence-transformers are extras. Gemini-related frontend/service code exists, but the repository’s stated rule is that external models remain optional and must never be required for primary tests or baseline translation.
