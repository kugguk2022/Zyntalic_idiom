# Zyntalic Implementation Backlog

## Objective
Build a rule-first, deterministic synthetic language engine robust enough for LLM-facing workflows, with Gemini as optional enhancement only.

## Status Legend
- [ ] Not started
- [~] In progress
- [x] Done

## P0 - Core Quality and Determinism

- [~] Rule 1: Strengthen rule engine fidelity
  - [x] Add canonical post-processing stage in translator pipeline
  - [x] Enforce context-tail presence/finality for non-reverse engines
  - [x] Add rule-validation warnings for malformed outputs
  - [x] Add explicit morphology-role checks (subject/object/verb markers)
  - [x] Add strict S-O-V-C conformance validator for generated surface forms

- [~] Rule 2: Deterministic quality gates
  - [x] Golden-set regression suite (initial 40-prompt seed; target 200-500)
  - [x] Failing checks for script-ratio drift and context-tail violations

- [ ] Rule 3: Generator upgrade (non-Gemini first)
  - [ ] Refactor generator into rule-guided assembly stages
  - [ ] Add deterministic fallback behavior for all stages

## P1 - Embeddings and Semantic Grounding

- [ ] Embedding backend hardening
  - [ ] Improve hash-only fallback with lexical/lemma priors
  - [ ] Add embedding schema/version tags to cache payloads

- [ ] Anchor relevance calibration
  - [ ] Blend token-level and sentence-level anchor scoring
  - [ ] Add paraphrase-stability metric

- [ ] Vocabulary quality
  - [ ] Expand core verbs/function words/domain lexicon
  - [ ] Add malformed mixed-script output checks

## P2 - Gemini as Optional Enhancer

- [ ] Keep Gemini fully optional and feature-flagged
- [ ] Ensure all primary tests pass with Gemini disabled
- [ ] Dual-path quality benchmark (deterministic vs Gemini-assisted)

## P3 - LLM Readiness Evaluation

- [ ] Build benchmark for consistency, long-context stability, and instruction adherence
- [ ] Add CI drift checks for morphology, syntax, and anchor semantics
