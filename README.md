# Zyntalic

<p align="center">
  <img src="https://raw.githubusercontent.com/kugguk2022/Zyntalic_idiom/main/zyntalic-flow/public/favicon.svg" alt="Zyntalic logo" width="360">
</p>

<p align="center">
  <strong>A deterministic synthetic-language engine for reproducible creative text.</strong>
</p>

<p align="center">
  <a href="https://github.com/kugguk2022/Zyntalic_idiom/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/kugguk2022/Zyntalic_idiom/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/kugguk2022/Zyntalic_idiom/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB.svg">
  <img alt="Status: experimental" src="https://img.shields.io/badge/status-experimental-orange.svg">
</p>

Zyntalic maps source text to a stable constructed-language surface using seeded word generation, literary anchor priors, mixed Hangul/Latin forms, and Subject–Object–Verb–Context (S-O-V-C) ordering. Each non-reverse result ends with a machine-readable `⟦ctx: ...⟧` trace.

The baseline runs locally with NumPy. Embeddings, NLP, PDF extraction, the web API, and desktop integration are optional.

> [!IMPORTANT]
> Zyntalic is experimental. Output stability is a design goal within a fixed code and resource version, not a permanent compatibility guarantee. Record the package version and generation options with production assets.

## Why Zyntalic?

- **Repeatable:** stable seeded generation supports revision and regeneration.
- **Inspectible:** anchors, frames, sigils, scope, and warnings are available as structured metadata.
- **Rule-first:** the core works without a hosted model or heavyweight NLP stack.
- **Controllable:** anchor mode, frames, register, dialect, evidentiality, engine, and mirror rate are explicit options.
- **Integrable:** use the Python API, CLI, authenticated REST API, React interface, or desktop launcher.

Read [the idea](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/idea.md), [core concepts](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/core-concepts.md), and the honest [current-state inventory](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/current-state.md) for the full project context.

## Quick start

### Python and CLI

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install zyntalic

zyntalic translate "I see the river at night." --format plain
```

From Python:

```python
from zyntalic.translator import translate_sentence

result = translate_sentence("I see the river at night.", engine="core", mirror_rate=0.3)
print(result["target"])
print(result["sidecar"])
```

### Desktop experience

On Windows, run `run_desktop.bat`. On any supported platform with the optional dependencies installed:

```bash
python -m pip install -e ".[web,pdf,desktop]"
python -m scripts.run_desktop
```

The desktop launcher binds to localhost and explicitly enables local unauthenticated mode. Do not use that override on a network-facing deployment.

## REST API

Install and start the authenticated API:

```bash
python -m pip install -e ".[web,pdf]"
export ZYNTALIC_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn apps.web.app:app --host 127.0.0.1 --port 8000
```

```bash
curl --fail-with-body http://127.0.0.1:8000/v1/translate \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ZYNTALIC_API_KEY" \
  -d '{"text":"I see the river at night.","engine":"core","mirror_rate":0.3}'
```

| Endpoint | Purpose | Authentication |
| --- | --- | --- |
| `GET /v1/health` | Readiness, limits, version, and cache status | Public |
| `POST /v1/translate` | Translate one input with request metadata | API key |
| `POST /v1/translate/batch` | Translate up to 32 ordered inputs | API key |
| `POST /v1/extract` | Extract UTF-8 text from PDF, TXT, or Markdown | API key |
| `GET /docs` | Interactive OpenAPI reference | Public |

The in-process rate limiter is suitable for one server process. Multi-worker and distributed deployments should enforce shared limits at a gateway. Configure limits, CORS, cache location, and authentication through the variables documented in [.env.example](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/.env.example).

## Development

```bash
python -m pip install -e ".[dev,web,pdf]"
ruff check .
pytest
```

The project has three inherited regression failures tracked in [issue #9](https://github.com/kugguk2022/Zyntalic_idiom/issues/9). CI runs the remainder as a required suite and reports those cases separately; deselection is not their acceptance criterion.

Frontend development:

```bash
cd zyntalic-flow
npm ci
npm run build
```

See [CONTRIBUTING.md](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/CONTRIBUTING.md) for environment setup, test selection, deterministic-change review, and pull-request expectations.

## Project structure

```text
apps/                  Application adapters, including the FastAPI service
data/                  Small fixtures and anchor inputs
data_generation/       Corpus acquisition and transformation pipeline
docker/                Container build definition
evals/                 Evaluation and smoke checks
lexicon/               Checkout/runtime literary lexicons
scripts/               Operational, training, and maintenance commands
tests/                 Primary automated test suite
wiki/                  Product idea, history, architecture, and roadmap
zyntalic/              Installable Python engine
zyntalic_docs/         Generated language-design reference
zyntalic-flow/         React/Vite frontend
```

The [repository guide](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/repository-guide.md) defines ownership, safe cleanup practices, legacy directories, and generated artifacts.

## Wiki and documentation

- [Project wiki](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/README.md) — the complete guide and reading map.
- [Idea and vision](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/idea.md) — motivation and design intent.
- [Core concepts](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/core-concepts.md) — anchors, ordering, context tails, and deterministic generation.
- [Architecture](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/architecture.md) — engine and application structure.
- [Current state](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/current-state.md) — implemented capabilities and limitations.
- [Evolution](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/evolution.md) — how the language and toolkit developed.
- [Roadmap](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/wiki/roadmap.md) — planned work.
- [Language reference](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/zyntalic_docs/README.md) — grammar and language-design documentation.
- [Dataset pipeline](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/DATASET.md)
- [Embeddings](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/EMBEDDINGS.md)
- [Changelog](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/CHANGELOG.md)
- [Security policy](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/SECURITY.md)

## Authors

Zyntalic is created and maintained by **ZoltF**, in collaboration with
**OpenAI Codex ("Coda")**. See the permanent
[authors record](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/AUTHORS.md).

## Scope and limitations

Zyntalic is a creative toolkit, not a linguistically complete English parser or a translation system for a naturally spoken language. The default parser intentionally uses stable heuristics. The generated language reference contains design material that should be backed by executable tests before being treated as a compatibility guarantee.

Corpus and fixture contributions must be redistributable and must not contain personal or confidential information. See [CONTRIBUTING.md](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/CONTRIBUTING.md#data-and-lexicon-contributions).

## License

Released under the [MIT License](https://github.com/kugguk2022/Zyntalic_idiom/blob/main/LICENSE).
