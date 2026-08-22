# Zyntalic_idiom: Next Steps Proposal

**Generated:** 2026-06-20  
**Repo:** kugguk2022/Zyntalic_idiom  
**Based on:** Current codebase (BACKLOG.md, README.md, zyntalic_docs/, zyntalic-flow/, core modules), chat history on conlang development, translation GUI/applications, and the goal of using Zyntalic for deterministic prose generation in AI movies, novels, lyrics, captions, and worldbuilding text.

---

## Vision & recovered context from prior discussions

Zyntalic is a **deterministic synthetic-language (conlang) engine** designed for stable, rule-governed surface forms. Key strengths: S-O-V-C ordering, explicit context tails `⟦ctx: ...⟧`, seeded deterministic word generation, anchor-based priors from lexicons (built from public-domain classics), mixed Hangul/Latin script aesthetics, and a lightweight NumPy core.

From development history:
- Strong emphasis on **rule-first determinism** (no heavy LLM dependency for the core path) so it remains reliable for pipelines, production assets, and LLM-facing tools.
- **Translation GUI** (`apps/web/` + `zyntalic-flow/`) as a practical application layer for writers, directors, editors, and worldbuilders.
- **Applications beyond general translation**: using Zyntalic morphology, phonology, and grammar as a disciplined framework for **prose generation and in-world language design** for AI films and novels. This includes dialogue, narration, chants, inscriptions, song fragments, subtitles, lore text, and recurring named phrases that must stay stable across scenes.

The goal is a toolkit that is:
- **Crash-proof** for production use (deterministic, testable, golden-set validated).
- **Creative yet rigorous** for prose, dialogue, and worldbuilding text.
- **Integratable** into writing, subtitle, storyboard, and rendering pipelines.
- **Beautiful & usable** via polished GUI and exports (Markdown, JSON, screenplay-friendly text).

---

## Prioritized Next Steps

Use `[ ]` for not started, `[~]` in progress / proposed start, `[x]` done. Builds directly on existing BACKLOG.md P0-P3 while expanding toward narrative generation and film/novel workflows.

### Immediate release plan: v0.5.0 visible compiler

`v0.4.0` made compiler data accessible through readable CLI output, per-sentence
JSON exports, and a bundled local dual display. The next release should make the
compilation process itself visible without presenting decorative animation as
real computation.

- [ ] Port the deterministic Hugging Face character-morph treatment into the bundled local UI.
- [ ] Present two independently configured deterministic channels concurrently.
- [ ] Define genuine compiler checkpoints: tokenization, semantic projection,
  anchor convergence, morphology, and final surface realization.
- [ ] Return an anchor-weight snapshot and intermediate surface for each checkpoint.
- [ ] Animate characters from the actual intermediate surfaces rather than interpolating
  only the final result.
- [ ] Drive the orbital visualization from convergence and channel disagreement.
- [ ] Export the full compilation trajectory per input file, including configuration,
  timings, intermediate weights, final surfaces, and receipt metadata.
- [ ] Keep the complete v0.5.0 deterministic experience local and usable without an API key.

**Effort estimate:** 1–2 hours for cinematic character morphing, 1–2 hours for
the two-channel interface, 4–8 hours for truthful intermediate trajectories,
and 45–90 minutes for tests, packaging, and PyPI deployment. Allow 15–45 minutes
for authenticated GitHub/Hugging Face deployment. Total: approximately 7–12
focused hours.

**Recommended sequencing:** when other launches are active, cap the same-day
Zyntalic work at two hours for the cinematic and dual-channel shell. Reserve a
dedicated 5–7 hour block the following day for real compiler trajectories, then
one hour for packaging and deployment.

**Release gate:** do not ship weight motion that merely implies changing semantic
state. Every visible weight transition in v0.5.0 must correspond to a recorded,
reproducible compiler checkpoint.

### P0: Core Quality, Determinism & Rule Fidelity (Highest priority - stabilize foundation)
Complete and harden what is already in progress per BACKLOG.md.

- [~] Finish Rule 1-3 items (canonical post-processing, context-tail enforcement, morphology-role checks, S-O-V-C validator, rule-validation warnings, generator refactor into rule-guided stages with deterministic fallbacks).
- [ ] Expand golden regression suite from ~40 to 200-500 prompts. **Include dedicated fiction subsets**: scene description, short dialogue, narration, lyric lines, subtitle-sized utterances, lore snippets, and character voice prompts.
- [ ] Add automated CI drift checks for morphology markers, script balance (Hangul nouns vs Latin verbs), context-tail presence, and `semantic_coherence` scores.
- [ ] Strengthen determinism: make all RNG paths fully seeded and reproducible across runs; add `verify_alphabet.py` and script-ratio checks to the test suite.
- [ ] Improve error surfacing and `logging_utils` for creative-pipeline debugging, especially when batch-generating prose assets.

**Success metric:** All golden tests pass with zero context-tail or morphology violations; repeated narrative prompts generate stable, production-safe output.

### P1: Embeddings, Semantic Grounding & Vocabulary (High - enables better prose generation)
Per BACKLOG plus narrative extensions.

- [ ] Embedding backend hardening: schema/version tags, improved hash-only fallback, and stronger lexical and lemma priors.
- [ ] Anchor relevance: blend token-level and sentence-level scoring; add a paraphrase-stability metric so similar prompts land near the same stylistic intent.
- [ ] **Narrative domain anchors & lexicon expansion**:
  - Curate and expand `data/anchors.tsv` or a new `lexicon/narrative/` with anchors for tone, setting, emotion, ritual language, cinematic atmosphere, and character voice.
  - Add stable phrase families for recurring fiction needs: oath forms, title forms, commands, laments, prophecy lines, greetings, farewell formulas, and scene transitions.
  - Add malformed mixed-script output checks and repeated-phrase collision checks.
- [ ] Vocabulary quality pass: expand core verbs, pronouns, connectors, and sensory vocabulary while preserving determinism.

**New tool idea (high leverage):** `zyntalic compose --mode scene|dialogue|lore|lyric` that outputs Zyntalic text, gloss, morphology breakdown, and a trace of the rule path used.

### P2: Narrative Generation & Story Pipeline (High value - main product direction)
This is the direct replacement for the older math-oriented path: Zyntalic becomes a prose engine for AI movies and novels.

- [ ] Create `zyntalic/narrative/` or `story_generation.py`:
  - Deterministic generators for scene prose, dialogue exchanges, monologues, chants, inscriptions, title cards, and lore paragraphs.
  - Character-voice templates so the same seed and profile yield stable speech patterns across chapters or scenes.
  - Story mode presets such as mythic, intimate, eerie, epic, romantic, and mechanical.
- [ ] Add prompt-to-structure tooling:
  - Input: English concept, scene brief, emotional beat, or screenplay note.
  - Output: Zyntalic prose, English gloss, literal back-translation, and optional alternate intensity levels.
- [ ] Add continuity helpers:
  - Stable naming for places, clans, artifacts, rituals, and recurring refrains.
  - Character memory packs for consistent diction and phrase reuse.
  - Seed-lock support so a scene can be regenerated without drift.
- [ ] Add screenplay and novel integration:
  - Export blocks formatted for subtitle files, screenplay dialogue, chapter snippets, narration cards, and production notes.
  - Optional sidecar JSON with trace metadata for pipeline automation.
- [ ] Validation: use `semantic_coherence.py`, `chiasmus.py`, and `bifurcation_scanner.py` to score internal consistency, rhetorical style, and variation range.

**Impact:** Turns Zyntalic into a practical narrative instrument - stable enough for repeated rendering passes, expressive enough for films and novels, and controlled enough for production reuse.

### P3: GUI, Frontend & Applications Polish (Medium-High - make the writing GUI useful daily)
Leverage existing `apps/web/`, `zyntalic-flow/` (React + TypeScript with sigils, anchors, settings), and desktop launchers.

- [ ] **zyntalic-flow enhancements**:
  - Live parse tree, morphology, and syntax breakdown visualization (expand `SigilColumn`, `AnchorBars`).
  - Batch generation UI with export for JSONL, Markdown, subtitle text, and writer-room notes.
  - "Narrative Composer" mode/tab: input scene brief or line prompt, generate prose/dialogue variants, show rule trace.
  - Character profile panel with tone, seed, relationship role, register, and recurring motifs.
  - Better error and edge-case display plus copy-to-clipboard for production use.
- [ ] Web API robustness: more endpoints (for example `/compose`, `/dialogue`, `/lore`, `/batch`), OpenAPI spec, health, and version.
- [ ] Desktop experience: refine `run_desktop.py` and scripts; support a one-command local writing workspace that starts the API and flow UI together.
- [ ] Mobile-friendly or PWA aspects for quick line generation on the go.

**Success:** A writer can generate stable lines, scene fragments, and lore text quickly enough for daily use during ideation, drafting, and revision.

### P4: Documentation, Tutorials & Discoverability (Medium)
- [ ] Expand `zyntalic_docs/`:
  - `narrative_generation.md` (core proposal + examples for scenes, dialogue, lore, and lyrics).
  - `advanced_usage.md` (custom lexicons, embedding training, pipeline integration).
  - `integration_examples.md` (film workflow, novel workflow, subtitle workflow, LLM-assisted workflow).
  - Update `grammar.md`, `morphology.md`, and `semantics.md` with more narrative and cinematic examples.
- [ ] README overhaul: prominent prose-generation use cases, quickstart for scene composition, links to `zyntalic-flow` demo, architecture diagram.
- [ ] Full end-to-end tutorial: "From English scene brief -> stable Zyntalic line set -> gloss -> subtitle or screenplay export".
- [ ] Add `CONTRIBUTING.md`, issue templates focused on rule fidelity, prose quality, and new domain lexicons.
- [ ] Prepare a clean PyPI release (v0.2+): proper `pyproject.toml` metadata, classifiers, and long description from README.

### P5: LLM Readiness, Optional Enhancers & Ecosystem (as BACKLOG P2/P3 + extensions)
- [ ] Keep Gemini fully optional and feature-flagged (never breaks the pure deterministic path).
- [ ] Dual-path quality benchmarks (deterministic baseline vs optional Gemini-assisted expansion for richer English glosses, prompt refinement, or alternate phrasings).
- [ ] LLM-facing robustness: structured output modes (JSON with trace, confidence, alternatives); long-context stability tests for chapter-sized workflows.
- [ ] CI and drift detection for morphology, anchor semantics, repeated phrase consistency, and character voice stability.
- [ ] Ecosystem hooks:
  - Optional integration points for writing tools, subtitle tooling, or personal media projects.
  - Prompt templates that use Zyntalic as an intermediate structured language for narrative agents.
  - Export formats friendly to Obsidian, screenplay tooling, and note-taking systems.

### P6: Data Pipeline, Advanced Features & Infrastructure (Ongoing)
- [ ] Data generation: extend for fiction and cinematic domains (synthetic scenes, dialogue turns, voice variants, chapter narration, lyric fragments); improve `run_data_pipeline.sh`.
- [ ] Leverage existing advanced modules more:
  - `semantic_coherence.py` for scene and line quality scoring.
  - `chiasmus.py` and `bifurcation_scanner.py` for stylistic and structural analysis of generated prose.
  - `enhanced_syntax.py` and `ir.py` for deeper intermediate representations useful in narrative control.
- [ ] Docker and deployment: polish `docker/`, add compose for full stack (API + flow UI); provide an easy demo deployment option.
- [ ] Performance and caching: optimize for larger lexicons and embeddings; improve `word_cache.json` handling for repeated production runs.
- [ ] Testing: property-based tests for determinism; more unit tests around narrative generation paths; expand `evals/`.

---

## Proposed Roadmap & Milestones

| Milestone | Target | Key Deliverables | Priority |
|-----------|--------|------------------|----------|
| **v0.2 Foundation** | 1-2 weeks | Complete P0 items, add fiction golden subsets, prototype `compose` mode, deliver GUI quick wins | Critical |
| **v0.3 Narrative Core** | 3-4 weeks | P1 narrative anchors and lexicon, `story_generation.py`, dialogue/lore exports, expanded docs | High |
| **v0.4 Writer Workflow** | 6-8 weeks | Production-ready `zyntalic-flow` narrative mode, subtitle/screenplay export, tutorials, PyPI publish | High |
| **v0.5+ Ecosystem** | Ongoing | Deeper film/novel workflow integrations, voice packs, lore systems, community contributions | Medium |

---

## How these ideas were recovered & synthesized

- **From BACKLOG.md & code**: strict adherence to the existing P0-P3 structure and rule engine philosophy.
- **From chat history (conlang + applications)**: the recurring theme is that Zyntalic should be more than a novelty language. It should be a **stable engine for evocative text**, where recurring phrases, names, dialogue patterns, and stylistic motifs survive across scenes, chapters, and production passes.
- **Our values**: determinism and crash-testing, reproducibility, beauty without losing control, honest iteration, and practical tooling for real creative work.
- **Practical constraints**: keep the core lightweight and NumPy-based, keep Gemini optional, and keep everything testable and pipeline-friendly.

This proposal is deliberately **actionable and prioritized**. Start with P0 completion plus a narrative composition prototype for quick wins that directly support AI film and novel workflows.

**Next action recommendation**: Review, edit priorities, or add/crash ideas, then we can:
1. Refine `next_steps.md` further if you want a sharper film-first or novel-first roadmap.
2. Implement the highest-ROI item (for example a `zyntalic compose` CLI or fiction golden tests).
3. Iterate rapidly on narrative presets, voice packs, and exports.

Feedback welcome - the right direction here is a deterministic prose engine that is actually useful when producing stories, scenes, and in-world language assets.
