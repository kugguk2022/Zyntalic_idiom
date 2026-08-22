# Roadmap

The roadmap combines the engineering backlog with the narrative-product proposal. Ordering is based on dependency and risk, not calendar promises.

## Now: establish a trustworthy baseline

1. Run and record the complete test suite on supported Python versions.
2. Resolve or explicitly quarantine inherited failures; do not normalize known failures as acceptance criteria.
3. Add a single capability matrix showing which public options work in Python, CLI, API, and frontend.
4. Version the deterministic contract: normalization, lexicon snapshot, embedding backend, seed derivation, and output schema.
5. Revalidate generated language documentation against executable examples.

**Exit condition:** a clean checkout has one documented setup path, primary tests pass, and repeated calls are stable for a versioned golden corpus.

## Next: consolidate the language engine

1. Decide which advanced morphology, phonology, and syntax systems are normative.
2. Route normative behavior through the high-level translator rather than parallel demo-only paths.
3. Define one canonical lexicon source and verify packaged resources against it.
4. Add embedding-cache schema/version tags and lexical fallback priors.
5. Expand the golden set to 200–500 examples, including dialogue, narration, lore, lyrics, and subtitle-sized lines.
6. Add property tests for determinism, context finality, script profiles, and serialization round trips.

**Exit condition:** the language reference describes tested behavior, and optional backends cannot silently alter the deterministic baseline.

## Near-term release: v0.5.0 visible compiler

The objective is to bring the impact of the Hugging Face deterministic A/B
experience into the installable local product while improving the honesty of
the visualization.

### Phase 1 — cinematic shell (2–4 hours)

- deterministic per-character glyph mutation;
- simultaneous A/B channels with independent engine and style controls;
- source, final surfaces, timing, and sidecars visible together;
- orbital motion driven by channel agreement and final anchor weights.

### Phase 2 — truthful trajectories (4–8 hours)

- explicit tokenization, projection, anchor-convergence, morphology, and surface checkpoints;
- intermediate surfaces and anchor-weight snapshots produced by the compiler;
- UI animation driven by those recorded checkpoints;
- downloadable per-file trajectory and immutable final receipt;
- performance work so optional embeddings do not freeze first paint.

### Phase 3 — release and deployment (1–2 hours)

- targeted trajectory, determinism, UI, packaging, and clean-wheel tests;
- PyPI build and install verification;
- authenticated GitHub and Hugging Face deployment.

**Total estimate:** approximately 7–12 focused hours. If other products are
shipping concurrently, complete only Phase 1 on the first day and reserve a
dedicated block on the following day for Phases 2 and 3.

**Exit condition:** every animated semantic-weight change maps to a reproducible
compiler checkpoint. The interface must not represent interpolated decoration as
live embedding computation.

## Then: narrative composition MVP

Build composition as orchestration over existing primitives rather than a second language engine.

Suggested contract:

```text
zyntalic compose INPUT
  --mode dialogue|scene|lore|lyric|inscription
  --project PROJECT_ID
  --speaker CHARACTER_ID
  --seed SEED
  --register ... --dialect ... --anchors ...
  --format text|jsonl|markdown
```

Each result should include surface text, source/gloss, literal readback where possible, configuration, engine version, anchor trace, warnings, and stable asset ID.

Start with three modes—dialogue, lore, and inscription—because they exercise voice, continuity, and concise production assets without requiring full paragraph generation.

**Exit condition:** a writer can regenerate a named asset exactly and can intentionally create a controlled variant.

## After that: continuity and workflow

- project dictionaries for people, places, artifacts, and rituals;
- character profiles with stable register, dialect, motifs, and phrase memory;
- phrase-family and collision detection;
- batch review and approval states;
- subtitle, screenplay, Markdown, and JSON sidecars;
- frontend views for morphology, syntax, anchors, and rule traces;
- import/export suitable for a story bible.

**Exit condition:** a small production can use Zyntalic across multiple scenes without maintaining consistency by hand.

## Later: optional intelligence and ecosystem

- benchmark deterministic versus model-assisted semantic selection;
- keep model assistance behind explicit feature flags;
- long-context and paraphrase-stability evaluation;
- integrations with writing and media tools;
- packaged releases and a reproducible demo deployment;
- community lexicon and language-rule contribution workflow.

## Recommended next three issues

1. **Baseline audit:** make `pytest -q` green or document each remaining failure with an owner and removal criterion.
2. **Documentation contract tests:** turn ten representative wiki/language-reference examples into executable golden tests.
3. **Composition schema:** specify and test the JSON result for a deterministic `dialogue`, `lore`, or `inscription` asset before building UI.

## Decision principles

- Prefer one end-to-end supported path over several disconnected demonstrations.
- Treat output compatibility like an API contract.
- Store provenance with every creative asset.
- Make variation explicit and seedable.
- Add optional intelligence only when the deterministic fallback remains useful.
