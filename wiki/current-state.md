# Current State

This page is a capability inventory, not a release promise. It reflects the repository as of 16 August 2026 and should be updated when behavior changes.

## Implemented and exercised

- Deterministic core word and sentence generation.
- Plain and mirrored translation paths.
- Heuristic English parsing into S-O-V-C fields.
- Canonical context-tail enforcement and rule warnings.
- Automatic, manual, and neutral anchor selection.
- Structured sentence sidecars with frames, pivots, anchors, sigils, and scope.
- Register, dialect, evidentiality, and frame configuration.
- Sentence, text, and ordered batch translation.
- CLI and Python interfaces.
- Versioned FastAPI health, translation, batch, and extraction routes.
- API-key enforcement, payload limits, rate limiting, request IDs, and timing metadata.
- SQLite WAL translation cache.
- React/Vite frontend and local desktop launcher.
- Tests for determinism, generator stages, surface/mirror rules, IR, batch behavior, cache, PDF cleaning, API behavior, and golden outputs.

## Implemented but optional

- sentence-transformer embeddings;
- spaCy token analysis;
- trained projection matrices;
- PDF extraction;
- pywebview desktop integration;
- data-collection dependencies;
- Gemini-facing frontend/service integration.

The baseline should continue to work without these extras.

## Experimental or partially integrated

The repository contains substantial phonology, morphology, enhanced-syntax, semantic-coherence, lexicon-management, advanced-variation, and bifurcation-analysis modules. Their existence does not mean every feature is routed through the normal `translate` command or REST endpoint. Before productizing one, document its integration point and add an end-to-end test.

The generated `zyntalic_docs/` reference is useful design material, but some counts, common phrases, and examples may describe a generated design snapshot rather than guaranteed current output.

## Proposed, not yet delivered as a unified feature

- `compose` modes for scenes, dialogue, lore, lyrics, chants, and inscriptions;
- persistent character voice profiles;
- project-level naming and phrase continuity packs;
- seed locks surfaced as a first-class writer workflow;
- literal gloss and back-translation packages for every composition;
- subtitle, screenplay, and story-bible exports;
- a dedicated narrative composer UI;
- long-context narrative consistency benchmarks.

## Known organizational debt

- Root launchers duplicate or wrap scripts under `scripts/`.
- Tests are split between active `tests/`/`evals/` and a legacy `unittests/` tree.
- Lexicons exist both at repository root and inside package resources.
- Generated artifacts and caches are present in some working directories, though ignored by Git.
- Planning documents overlap: `BACKLOG.md` is engineering-focused while `next_steps.md` is product/narrative-focused.
- Language documentation is generated separately from project documentation and needs behavioral verification.

These should be resolved incrementally because moving runtime files or data without compatibility shims can break packaging and launch workflows.
