# Zyntalic Wiki

Zyntalic is a deterministic synthetic-language toolkit: the same input and configuration should produce the same stylized language output. It combines a rule-first translation pipeline, a mixed Hangul/Latin surface aesthetic, literary semantic anchors, an explicit sentence sidecar, and interfaces for command-line, API, desktop, and browser use.

This wiki separates three things that are easy to conflate:

- **The idea** — a reproducible language instrument for writers, worldbuilders, and software pipelines.
- **The implementation** — the capabilities that exist in this repository today.
- **The direction** — the proposed evolution toward narrative composition and continuity tooling.

## Start here

1. [The idea](idea.md) explains the problem, product thesis, and intended users.
2. [Evolution](evolution.md) reconstructs how the project changed from Git history and repository artifacts.
3. [Core concepts](core-concepts.md) defines determinism, S-O-V-C, anchors, mixed script, morphology, mirror forms, and the context sidecar.
4. [Architecture](architecture.md) maps the runtime and the codebase.
5. [Current state](current-state.md) distinguishes working, optional, experimental, and proposed features.
6. [Roadmap](roadmap.md) turns the existing backlog into an ordered delivery plan.
7. [Repository guide](repository-guide.md) explains where things belong and how to contribute without adding more root-level clutter.
8. [Glossary](glossary.md) provides a shared vocabulary.

## Install and explore

Zyntalic is published on [PyPI](https://pypi.org/project/zyntalic/) as `zyntalic` for Python 3.10 and newer:

```bash
python -m pip install zyntalic
```

Install `zyntalic[web]` to include the local web application. The PyPI project page contains the current release, release history, dependency metadata, and downloadable package files.

[Zyntalic Dual on Hugging Face Spaces](https://huggingface.co/spaces/kugguk/zyntalic-dual) is a related machine-only A/B language experiment. It is maintained as a separate prototype and should not be treated as the deterministic package runtime or its hosted replacement.

## Language references

The generated language reference remains in [`zyntalic_docs/`](../zyntalic_docs/README.md). It covers grammar, phonology, morphology, syntax, semantics, the lexicon, and a tutorial. Treat it as a design reference: some examples and statistics were generated in December 2025 and should be revalidated against the current engine before being presented as guarantees.

## Project documents

- [README](../README.md): installation and common entry points
- [PyPI package](https://pypi.org/project/zyntalic/): published releases and package metadata
- [Hugging Face Space](https://huggingface.co/spaces/kugguk/zyntalic-dual): related Zyntalic Dual prototype
- [Backlog](../BACKLOG.md): original engineering backlog
- [Next-steps proposal](../next_steps.md): narrative-product proposal from June 2026
- [Dataset guide](../DATASET.md): corpus-generation pipeline
- [Embeddings guide](../EMBEDDINGS.md): optional semantic backend
- [Changelog](../CHANGELOG.md): release notes

## Guiding principle

Zyntalic should be **creative in appearance and meaning, but predictable in operation**. Optional statistical or model-based components can improve semantic selection, but the core path should remain local, reproducible, testable, and usable without an external AI service.
