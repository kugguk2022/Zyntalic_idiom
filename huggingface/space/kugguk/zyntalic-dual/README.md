---
title: Zyntalic Dual
emoji: 🧬
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.49.1
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: AI-native adversarial intent language laboratory
tags:
  - artificial-language
  - multi-agent
  - adversarial-evaluation
  - openai
---

# Zyntalic Dual — machine-only A/B prototype

This Space tests whether two independent language policies can preserve the same
communicative intent under ambiguity, hostile interpretation and environmental
noise. It is not a translator, cipher, security boundary or deterministic
word-substitution engine.

## One run

1. An intent analyst converts the utterance and situation into a semantic and
   pragmatic contract.
2. ASCI and ASCI2 independently generate three strategic surfaces each.
3. ASCI blindly decodes and attacks ASCI2; ASCI2 independently does the same to
   ASCI. Neither opponent decoder sees the source or intent contract.
4. A neutral judge compares both cross-readings to the intent contract, perturbs
   every candidate and selects one candidate per lineage.
5. The immutable round manifest records model names, response IDs, token usage,
   equal lineage budgets and a content digest. Humans do not vote or evolve it.

There is deliberately no compiler fallback. If the model provider is unavailable,
the Space fails explicitly.

## Hugging Face setup

Add these private Space secrets:

- `OPENAI_API_KEY` — model provider credential. The existing Hugging Face
  secret name `OPENAI_TOKEN` is also accepted as an alias.

Optional variables:

- `ZYNTALIC_LINEAGE_MODEL` — defaults to `gpt-5.6-terra` for both lineages.
- `ZYNTALIC_JUDGE_MODEL` — defaults to the same model.
- `ZYNTALIC_DAILY_RUN_CAP` — defaults to `10` completed/attempted starts per UTC day.
- `ZYNTALIC_SESSION_RUN_CAP` — defaults to `2` starts per browser session.
- `ZYNTALIC_SAFETY_IDENTIFIER` — a privacy-preserving stable tester identifier.

The implementation uses the OpenAI Responses API with Pydantic Structured Outputs
and sends `store=False`. Each run makes six model judgments: intent, two parallel
encoders, two parallel opponent decoders and one neutral adjudicator. The Gradio
API endpoint is disabled and queue concurrency is one.

The SQLite run ledger enforces UTC-day and per-browser-session limits on one
replica. A Space restart may reset ephemeral counts, so keep the independent
OpenAI project budget as the hard outer boundary.

There is no automated billing or top-up workflow. If the OpenAI project reports
insufficient quota, the Space tells the user that funding is paused and requires
manual owner approval before service resumes.

## Versions

- `main` serves both editions in one Space: the v1.1 ASCI ↔ ASCI2 model duel and
  the v0.1 local deterministic A/B comparison.
- `v0-deterministic` preserves the earlier standalone, no-API edition.

Hugging Face runs the Space's default branch. The preserved branch is source
versioning, not a second live deployment; it can be duplicated into another Space
later if both editions need permanent public URLs.

## Language constraints

- Intent-level strategic substitution, never fixed English word mapping.
- S-O-V-C tendency with documented pragmatic exceptions.
- Polish-influenced extended Latin surface and agglutinative morphology.
- Hangul-derived marker only in the final context tail.
- Written-French time composition expressed through new Zyntalic morphemes.
- Synthetic/user-authored inputs and visible provenance.
- No optimization for concealment, moderation evasion or harmful intent.

## Local validation

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

The unit tests inject a fake model transport; they require no API key and verify
both decoder isolation boundaries, equal lineage budgets, evidence coverage and
spend-cap behavior.

## Repository-only v0.1 voice lab

The experimental local voice lab records or accepts a speaker-authorized reference
clip, transcribes it locally, creates the deterministic Zyntalic surface, and uses
that same clip to render a voice-matched alien-language film take. It is deliberately
excluded from the Hugging Face Space runtime.

Use a separate Python 3.11 environment (Chatterbox's documented/tested version):

```bash
python -m venv .venv-voice
.venv-voice/Scripts/pip install -r requirements-voice.txt
.venv-voice/Scripts/python voice_app.py
```

Model weights download on first local use. Only use your own voice or a voice for
which the production has explicit permission.
