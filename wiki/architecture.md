# Architecture

## Runtime flow

```text
CLI / Python / React UI / REST client
                 │
                 ▼
       zyntalic.translator
  normalize → parse → embed → anchor
       → generate → enforce rules
       → attach IR/sidecar → batch
                 │
       ┌─────────┼──────────┐
       ▼         ▼          ▼
 zyntalic.core  syntax   embeddings
 generation     + NLP    + projection
       │
       ▼
surface text + ⟦ctx: ...⟧ + structured metadata
```

The public translation layer in `zyntalic/translator.py` is the best starting point for understanding actual application behavior. Specialist modules are useful, but not every advanced class participates in every normal translation.

## Major components

| Area | Location | Responsibility |
| --- | --- | --- |
| Translation orchestration | `zyntalic/translator.py` | Normalization, batching, anchors, scope, canonical enforcement, sidecars |
| Core generation | `zyntalic/core.py` | Word/syllable generation, lexicons, embeddings, anchors, mirror/plain entries, context |
| Lightweight parsing | `zyntalic/syntax.py`, `zyntalic/nlp.py` | Sentence splitting, token analysis, heuristic S-O-V-C fields, optional spaCy |
| Language systems | `morphology.py`, `phonology.py`, `enhanced_syntax.py` | Richer grammatical and sound-system experiments |
| Meaning and rhetoric | `semantic_coherence.py`, `chiasmus.py`, `bifurcation_scanner.py` | Coherence analysis, sigils, mirror/rhetorical analysis |
| Intermediate representation | `zyntalic/ir.py` | Frames, pivots, and sentence sidecars |
| Optional semantics | `embeddings.py`, `transformers.py`, `models/` | Hash/model embeddings and learned projection |
| API | `apps/web/app.py` | Authenticated REST endpoints, validation, rate limits, extraction, static UI |
| Frontend | `zyntalic-flow/` | React/Vite translation interface and controls |
| Operations | `scripts/`, root launch shims | Launching, status checks, administration, training |
| Data pipeline | `data_generation/` | Collection, cleanup, sentence splitting, batch translation, dictionaries |
| Verification | `tests/`, `evals/` | Behavioral, API, determinism, rule, and golden tests |

## Public interfaces

### Python and CLI

`translate_sentence`, `translate_text`, and `translate_batch` are the main programmatic operations. The installed `zyntalic` command exposes translation and version information.

### REST API

The current server maintains legacy compatibility and versioned `/v1` endpoints. The versioned surface includes health, single translation, ordered batch translation, and text/PDF extraction. Translation routes require an API key unless the explicit localhost desktop override is enabled.

### Frontend and desktop

`zyntalic-flow` is the richer React/Vite frontend. The Python desktop launcher starts a localhost server and opens the bundled experience. Root-level launchers are compatibility conveniences; reusable launcher logic belongs under `scripts/`.

## Data and caches

- `lexicon/` contains source/runtime lexicons used by the repository checkout.
- `zyntalic/resources/lexicon/` contains packaged copies for installed distributions.
- `data/anchors.tsv` is a compact anchor fixture/training source.
- `data_generation/` contains raw, cleaned, segmented, and translated corpus stages.
- `models/` is the ignored output location for a trained projection.
- runtime caches belong under ignored cache paths; the REST layer uses SQLite WAL for concurrent access.

The duplicate lexicon trees are intentional packaging concerns, but they create drift risk. A future release process should generate or verify the packaged copy from one canonical source.

## Architectural constraints

- Baseline translation must work with NumPy only.
- Optional backends are lazily loaded and should fail soft.
- Random choices must use stable seeded RNG utilities.
- Context metadata must remain final and machine-readable.
- API security defaults must fail closed for network-facing translation.
- Batch output order must match input order.
