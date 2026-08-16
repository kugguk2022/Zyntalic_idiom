# Evolution of the Idea

This timeline is reconstructed from Git history, the codebase, `BACKLOG.md`, and `next_steps.md`. Dates describe repository milestones, not necessarily the first moment an idea was conceived.

## 1. Foundation: deterministic conlang toolkit — December 2025

The first commit established most of the enduring thesis at once:

- a Python package and CLI;
- deterministic random-number generation;
- S-O-V-C parsing and rendering;
- mixed-script word generation;
- twenty literary lexicons and anchor vectors;
- chiasmic/mirrored sentence generation;
- projection training, tests, API scaffolding, and packaging.

The project was already more than a vocabulary list. It treated the language as an engine whose output could be reproduced and integrated.

Late-December additions broadened the language model with phonology, morphology, semantic coherence, enhanced syntax, advanced variation, documentation generation, and a richer test suite. A web/desktop layer and optional Gemini proxy appeared, but the core philosophy remained dependency-light.

## 2. Data and general translation — January 2026

The repository added a corpus pipeline for collecting, cleaning, splitting, and translating public-domain text. This changed the scale of the problem: vocabulary and behavior could now be developed from datasets rather than isolated examples.

Translation became more general-purpose, with speed controls and optional embedding aliases. Reverse translation and mirror context were introduced. Mirror generation evolved from a decorative template toward stateful motif selection and explicit contextual behavior.

## 3. Structure, traceability, and rule fidelity — April 2026

The project introduced an intermediate representation in `zyntalic/ir.py`. Translation results gained frames, pivot types, anchor weights, sigils, scope information, and a serializable sidecar. The frontend exposed more of these controls.

At the same time, `BACKLOG.md` crystallized an engineering priority: make the rule-first path trustworthy before expanding model-assisted behavior. Work followed on:

- canonical post-processing;
- guaranteed context-tail placement;
- morphology-role and S-O-V-C validation;
- deterministic fallbacks;
- staged generation;
- golden regression tests and script-ratio checks;
- CI and lint repair.

This phase transformed “deterministic” from an aspiration into something increasingly enforced by tests.

## 4. From conlang engine to narrative instrument — June 2026

`next_steps.md` reframed the likely product direction. Instead of treating translation as the endpoint, it proposed stable prose assets for AI films, novels, lyrics, captions, and worldbuilding.

The key conceptual shift was from individual output to **continuity**:

- stable names and recurring phrases;
- character voice profiles;
- scene and project seed locks;
- dialogue, lore, lyric, inscription, and narration modes;
- glosses and back-translations;
- subtitle, screenplay, Markdown, and JSON exports.

Most of that layer remains proposed. It is valuable because it explains why determinism, anchors, metadata, and application interfaces belong together.

## 5. Product surface and API hardening — August 2026

Branding and the React application received attention, followed by a substantial REST API modernization. The API gained versioned health and translation routes, batching, extraction, request metadata, payload limits, authentication, rate limiting, OpenAPI documentation, and a concurrent SQLite WAL cache.

This made the engine more deployable and clarified its security boundary: authenticated network use versus an explicit unauthenticated localhost desktop mode.

## The through-line

The implementation has expanded, but the central idea has stayed remarkably consistent:

```text
stable seed + explicit rules + semantic anchors
                    ↓
      reproducible synthetic-language asset
                    ↓
 CLI / API / desktop / creative production workflow
```

The next important evolution is not adding more isolated features. It is joining the mature primitives into one documented, validated narrative workflow.
