# The Idea

## One-sentence thesis

Zyntalic turns source text into a stable, inspectable constructed-language form that can be regenerated across drafts, scenes, builds, and software pipelines without silent stylistic drift.

## The problem

Invented language in creative work often has one of two weaknesses. Hand-authored fragments can be evocative but difficult to keep consistent at scale. Free-form generative output can scale, but names, morphology, phrasing, and tone may change between runs. Conventional machine translation solves a different problem: it targets an existing language and optimizes for natural equivalence, not the controlled invention of a new one.

Zyntalic explores a middle ground. Its output is synthetic, but its production is governed by explicit rules and stable seeds. A line can therefore function as a reusable production asset rather than a disposable suggestion.

## Product promise

Given the same normalized input, engine, and configuration, Zyntalic aims to return the same result. The result should also expose enough structure to explain how it was made:

- a surface form with a recognizable visual identity;
- a consistent S-O-V-C organization;
- semantic influence from named literary anchors;
- grammatical and semantic metadata in a context tail/sidecar;
- warnings when output violates project rules;
- structured output suitable for applications and automated workflows.

Determinism is the foundation, not the entire creative proposition. The larger idea is **controlled variation**: change the seed, register, dialect, anchor selection, frame, or mirror behavior deliberately, and keep everything else stable.

## Who it is for

### Writers and worldbuilders

Recurring names, vows, inscriptions, ritual phrases, dialogue registers, and lore fragments need to survive revision. Zyntalic can become a language continuity layer between the story bible and the manuscript.

### Film, game, and media pipelines

Subtitles, prop text, title cards, chants, lyrics, and repeated spoken lines often pass through many tools. Stable generation plus JSON sidecars makes those assets traceable and regenerable.

### Language-design experimentation

The repository offers concrete implementations of word order, vowel harmony, agglutinative morphology, phonotactics, evidentiality, and mixed-script generation. It is a toolkit for experimenting with those systems, not a claim to model Korean, Hungarian, or Polish themselves.

### Developers

The Python API, CLI, REST API, and React frontend expose the same core engine through different boundaries. The dependency-light fallback makes local and automated use possible without a hosted model.

## What makes the idea distinctive

1. **Reproducibility over improvisation.** Random-looking forms derive from stable seeds.
2. **Rules before optional models.** External or heavyweight semantic models enhance rather than define the core.
3. **Meaning has provenance.** Literary anchors and sidecar fields make influences visible.
4. **Context is first-class.** Context is represented at the end of the clause and recorded in an explicit `⟦ctx: ...⟧` tail.
5. **The artifact is dual.** A human sees the surface language; software can consume the structured trace.

## Non-goals

- Faithful translation into a naturally spoken language.
- A linguistically complete English parser; the default parser is intentionally heuristic.
- Unbounded creative generation in the deterministic core.
- Requiring Gemini, sentence-transformers, spaCy, or another remote/heavy dependency.
- Claiming that every generated reference example is current engine behavior without a regression test.

## Long-term shape

The natural product evolution is from **translator** to **narrative language system**. Translation remains the primitive. On top of it, composition modes could manage character voices, naming, repeated motifs, lore, scene-level seeds, and export formats. That direction is documented in [the roadmap](roadmap.md); it is not yet fully implemented.
