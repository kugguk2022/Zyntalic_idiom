# Zyntalic Dataset Pipeline

This document describes the optional corpus pipeline for building a larger
Zyntalic dictionary and embeddings. The pipeline is modular and opt-in.

Important:
- Use only texts you have rights to process.
- Scraping is optional and limited to URLs you provide.

## Quick Start (Local Files)

1) Place raw .txt or .pdf files under `data_generation/raw/`

2) Extract text (PDF supported if `PyPDF2` is installed):

```bash
python data_generation/extract_text.py \
  --in data_generation/raw \
  --out data_generation/raw_text
```

3) Clean text:

```bash
python data_generation/clean_text.py \
  --in data_generation/raw_text \
  --out data_generation/clean
```

4) Split into sentences:

```bash
python data_generation/sentence_split.py \
  --in data_generation/clean \
  --out data_generation/sentences/sentences.jsonl
```

5) Batch translate (in-process API):

```bash
python data_generation/batch_translate.py \
  --input data_generation/sentences/sentences.jsonl \
  --output data_generation/sentences/translations.jsonl \
  --mode api \
  --engine core \
  --mirror-rate 0.3
```

6) Build dictionary from corpus tokens:

```bash
python data_generation/build_dictionary.py \
  --input data_generation/sentences/sentences.jsonl \
  --output data_generation/dictionary/zyntalic_dictionary.json \
  --output-tsv data_generation/dictionary/zyntalic_dictionary.tsv
```

## One-Command Pipeline

Run the full pipeline with optional connectivity checks:

```bash
./run_data_pipeline.sh
```

Common environment overrides:

```bash
MODE=server SERVER_URL=http://127.0.0.1:8001/translate ./run_data_pipeline.sh
SCRAPE_GUTENBERG=1 SCRAPE_ANNAS=1 ./run_data_pipeline.sh
LIMIT=500 ./run_data_pipeline.sh
```

## Optional: Project Gutenberg

IDs (recommended): edit `data_generation/sources/gutenberg_ids.txt` and run:

```bash
python data_generation/collect_gutenberg.py \
  --ids data_generation/sources/gutenberg_ids.txt \
  --out data_generation/raw/gutenberg \
  --strip-boilerplate
```

URLs (optional scraping of book pages):

```bash
python data_generation/collect_gutenberg.py \
  --from-urls data_generation/sources/gutenberg_urls.txt \
  --out data_generation/raw/gutenberg \
  --strip-boilerplate
```

## Optional: Anna's Archive (user-provided URLs)

Add URLs to `data_generation/sources/annas_urls.txt` and run:

```bash
python data_generation/collect_annas.py \
  --urls data_generation/sources/annas_urls.txt \
  --out data_generation/raw/annas
```

If you provide page URLs and want the script to extract a download link:

```bash
python data_generation/collect_annas.py \
  --urls data_generation/sources/annas_urls.txt \
  --out data_generation/raw/annas \
  --scrape
```

## Connectivity Checks

Verify that your Gutenberg IDs/URLs and Anna's URLs are reachable (no downloads):

```bash
python data_generation/check_sources.py \
  --gutenberg-ids data_generation/sources/gutenberg_ids.txt \
  --gutenberg-urls data_generation/sources/gutenberg_urls.txt \
  --annas-urls data_generation/sources/annas_urls.txt \
  --scrape-gutenberg \
  --scrape-annas
```

## Server Mode (Optional)

If you prefer the HTTP server (e.g., for remote workers), run the app server and
then use `--mode server`:

```bash
python data_generation/batch_translate.py \
  --mode server \
  --server-url http://127.0.0.1:8001/translate
```

## Projection Training

The projection trainer now accepts JSONL pairs and optional anchor embeddings:

```bash
python scripts/train_projection.py \
  --pairs-jsonl data_generation/sentences/translations.jsonl \
  --embed-backend sentence-transformers \
  --anchor-embeddings data/embeddings/anchor_embeddings.json
```

Expected JSONL format for `--pairs-jsonl`:

```json
{"anchor": "Homer_Iliad", "text": "example sentence"}
```

## Dependencies

Optional data tools:

```bash
pip install -e .[data]
```

Optional PDF extraction:

```bash
pip install -e .[pdf]
```
