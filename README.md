# Zyntalic

<p align="center">
  <img src="zyntalic-flow/public/favicon (3).svg" alt="Zyntalic logo" width="600">
</p>

A deterministic **synthetic-language toolkit** (conlang engine) that maps input text to a stable “Zyntalic” surface form using:

- deterministic word generation (seeded by text)
- **anchor priors** (“Schelling points”) via bundled lexicons
- **S-O-V-C** ordering with an explicit **context tail** (`⟦ctx: ...⟧`)

This repo is intentionally lightweight: it runs with only NumPy, and upgrades automatically if you install optional extras.

## Install

Fastest way of running the repo: 

```
run_desktop.bat
```

Typical way:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Optional:
- Web API: `pip install -e ".[web]"`
- Better embeddings: `pip install -e ".[embeddings]"`
- Desktop/web app: `pip install -e ".[web,pdf,desktop]"`

# Running tests
```bash
pytest -q
```

Demo only (does not replace pytest):
```bash
python3 -c "from zyntalic.test_suite import demo_test_suite; demo_test_suite()"
```
## CLI

Translate a sentence:

```bash
zyntalic translate "Hello world" --format plain
```

JSONL output (good for pipelines):

```bash
zyntalic translate "I see the river at night." --format jsonl
```

## Web API (optional)

```bash
pip install -e ".[web]"
uvicorn apps.web.app:app --reload --port 8000
```

- `GET /health` and `POST /translate` remain compatible with the desktop UI.
- `GET /v1/health` reports readiness, limits, version, and cache status.
- `POST /v1/translate` adds a request ID and processing time.
- `POST /v1/translate/batch` translates up to 32 independent inputs per request.
- `POST /v1/extract` extracts UTF-8 text from PDF, TXT, or Markdown uploads.
- Interactive OpenAPI documentation is available at `/docs`.

Example:

```bash
curl -s http://127.0.0.1:8000/v1/translate \
  -H 'content-type: application/json' \
  -d '{"text":"I see the river at night.","engine":"core","mirror_rate":0.3}'
```

The server uses a concurrent SQLite WAL cache instead of rewriting one JSON
file for every sentence. Set `ZYNTALIC_CACHE_PATH` when deployments need a
persistent volume, or `ZYNTALIC_USE_CACHE=0` to disable it.

## Desktop/Web launcher

### Quick Start (Windows)

- Double-click or run: `run_desktop.bat`
  - This sets `ZYNTALIC_MAX_TEXT_CHARS=100000000` and launches the desktop app.

### Other launchers

- Windows (cmd/PowerShell): `scripts\start_server.bat`
- Bash/WSL: `chmod +x scripts/start_server.sh && scripts/start_server.sh`
- Direct Python (any shell): `python -m scripts.run_desktop`

The launchers check port 8001 before starting and then open the bundled UI.

## Projection training (optional)

There’s a simple projection trainer that produces `models/W.npy` + `models/meta.json`:

```bash
python scripts/train_projection.py --anchors data/anchors.tsv --method procrustes --out models
```

## Repo layout

```
Zyntalic/
  apps/        # CLI + web API wrappers
  zyntalic/    # core library (deterministic)
  evals/       # tests / regression checks
  tests/       # user-facing tests
  data/        # small fixtures only
  scripts/     # operational utilities and launchers
```

## Notes

- This is a **toolkit**, not a linguistics-perfect parser. The English parsing is a stable heuristic to enforce S-O-V-C and is designed to avoid heavy dependencies.
- All fixtures are either tiny examples or public-domain-ish excerpts; don’t commit any PII to `data/`.

## License

MIT.
