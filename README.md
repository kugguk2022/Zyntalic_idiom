# Zyntalic

A deterministic **synthetic-language toolkit** (conlang engine) that maps input text to a stable “Zyntalic” surface form using:

- deterministic word generation (seeded by text)
- **anchor priors** (“Schelling points”) via bundled lexicons
- **S-O-V-C** ordering with an explicit **context tail** (`⟦ctx: ...⟧`)

This repo is intentionally lightweight: it runs with only NumPy, and upgrades automatically if you install optional extras.

## Install

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

- `GET /health`
- `POST /translate`

## Desktop/Web launcher

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
