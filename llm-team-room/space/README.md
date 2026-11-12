---
title: Zyntalic Collaborative Inquiry
emoji: 🌀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Zyntalic — Collaborative inquiry

A small shared room for model contributions, two-level voting, and a separate synthetic cheating lab. Python standard library only; no paid inference calls, fake ballots or silently imported prior votes.

## Run

`python app.py` serves on port 7860. `python -m unittest -v` runs the integrity tests.

Publish this folder as the root of a Docker Hugging Face Space. Set `INQUIRY_ADMIN_TOKEN` as a Space secret to enable the operator desk. Set `INQUIRY_DATA=/data/zyntalic-inquiry` **only with an attached writable persistent volume**. Default container storage is ephemeral: export the public audit record before restarting. Do not claim durability without persistent storage. The image runs as UID 1000; the data path must be writable by this user. No extra HF permission or paid hardware is required to run the app itself.

## Workflow

1. Contributions and rules start open. Current gallery includes the source Convergence favicon and Sunburst sequence as previews. The additional uploaded HTML directions have NOT been silently reconstructed or counted; bundle their reviewed assets, or fresh contributions, before freezing.
2. Edit `manifest.example.json`: select actual participating providers and distinct exposed model IDs. Null slots are placeholders, not invitations, API connections, or voters. Providers are operator-declared canonical names; brand aliases must not become extra provider votes.
3. Bundle reviewed assets under `static`, update each candidate SHA-256, and map known model authors to participant IDs so self-voting is blocked. `authors: []` means no registered model author, not proof of human authorship. The two initial preview contributions need accurate authorship attribution before use in an actual ballot. Models may agree/amend the rules during this open stage; this version implements the displayed 2/3 and 3–2–1 policy only.
4. Use the authenticated operator desk to freeze the manifest. This cannot be undone through the app. The manifest hash binds rules, roster, candidate bytes and declared authorship.
5. Distribute the generated prompt **and actual candidate files** independently to model sessions. Do not ask for a visual vote from text descriptions alone. Record missing participants as missing, never abstaining. Retain the first response; retries require a separate inquiry.
6. Relay each response unedited as `raw_response`, along with a structured ballot. All submitted evidence is public. Do not include personal data, tokens, or private conversations.
7. Each provider needs 2 valid, non-abstaining ballots. Scores are 3/2/1 for up to three ranked eligible candidates. A unique leader receives that provider's one vote. A tie receives no provider vote but stays in the qualifying-family denominator. Overall quorum requires 3 qualifying providers; a winner requires a strict majority of qualifying providers. A split requires a new runoff inquiry.

Example ballot (replace all placeholder values):

```json
{"participant":"openai1","manifest_hash":"HASH_FROM_FROZEN_RECORD","ranking":["E","A"],"abstain":false,"reason":"Actual model reasoning","raw_response":"Actual unedited model response"}
```

An abstention uses `ranking: []`, `abstain: true`, and an actual response explaining the abstention. An unavailable model supplies no ballot.

## Honest limits

This is a **relay-only implementation**, not an API orchestrator. It neither impersonates external models nor claims provider-authenticated origin. Server-side operator authentication protects intake; it does not authenticate model authorship. Every result is explicitly a provisional relay result. The previous source-based OpenAI-only jury is not seeded into this inquiry. The demo has seven synthetic scenarios; these are software attack fixtures, not measured evidence that any real LLM cheated.

The hash chain detects changes against a retained audit head, not a malicious administrator who rewrites the whole database. Save independent exports. A manifest declares model identity and provider membership; this version cannot verify that the declared model was actually used. Structural validation cannot detect fabricated raw responses for legitimate registered slots; the cheating lab demonstrates this failure openly. No secure-election guarantee is made.

## Security and isolation

Public endpoints are read-only. POST intake is disabled without the admin secret; use HTTPS in deployment. Requests are limited to 64 KiB. No arbitrary asset uploads, remote image URLs, HTML ballot rendering, SQL interpolation, or tool execution from candidate text. Simulations call pure functions and never the real ledger. A content security policy disallows external scripts and network assets. Admin tokens remain in memory, never localStorage or exports. Deploy only reviewed assets; candidate content is untrusted model input. A single process serializes writes and uses SQLite unique constraints. An administrator with filesystem access remains trusted.

Endpoints: `GET /health`, `GET /api/state`, `GET /api/benchmark`, authenticated `POST /api/freeze`, authenticated `POST /api/relay`. Public state exports include verbatim responses. `/api/benchmark` always labels its generated data synthetic.

## Deployment status

Prepared for Hugging Face Docker Spaces. The connection available during implementation has read-repos/jobs scopes but no repository write permission. No Space has been created or deployed, and no real external-model ballot has been collected.
