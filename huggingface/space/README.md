---
title: Zyntalic
emoji: 🜂
colorFrom: indigo
colorTo: gray
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: Deterministic synthetic-language engine for reproducible creative text
tags:
  - conlang
  - synthetic-language
  - deterministic
  - text-generation
---

# Zyntalic

An interactive demo of [Zyntalic](https://github.com/kugguk2022/Zyntalic_idiom), a
deterministic synthetic-language engine.

Source text is mapped to a stable constructed-language surface using seeded word
generation, literary anchor priors, mixed Hangul/Latin forms, and
Subject–Object–Verb–Context (S-O-V-C) ordering. Every non-reverse result ends
with a machine-readable `⟦ctx: ...⟧` trace.

## Determinism

The same input and the same settings always produce the same output. There is no
sampling and no hosted model — the core runs on NumPy. Output stability is a
design goal within a fixed code and resource version, not a permanent
compatibility guarantee, so record the engine version alongside anything you
generate.

## Controls

| Control | Effect |
| --- | --- |
| Engine | `core` is the rule-based baseline; `transformer` uses semantic anchor matching; `chiasmus` is more stylized; `reverse` renders back toward English. |
| Mirror rate | Lower values produce more Zyntalic vocabulary. |
| Register / dialect / evidentiality | Explicit surface and scope options. |
| Anchor mode | `auto` infers anchors from the text, `manual` locks them to your selection, `neutral` suppresses anchor inference. |

## Scope

Zyntalic is a creative toolkit, not a linguistically complete English parser or a
translation system for a naturally spoken language. The default parser uses
stable heuristics by design.

Released under the MIT License.
