#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "Error: python not found. Set PYTHON_BIN or install Python."
    exit 127
  fi
fi

MODE="${MODE:-api}"
ENGINE="${ENGINE:-core}"
MIRROR_RATE="${MIRROR_RATE:-0.3}"
LIMIT="${LIMIT:-0}"
SERVER_URL="${SERVER_URL:-http://127.0.0.1:8001/translate}"
SLEEP="${SLEEP:-0}"
SCRAPE_GUTENBERG="${SCRAPE_GUTENBERG:-0}"
SCRAPE_ANNAS="${SCRAPE_ANNAS:-0}"
CHECK_SOURCES="${CHECK_SOURCES:-1}"

if [[ "$CHECK_SOURCES" == "1" ]]; then
  echo "==> Checking connectivity"
  "$PYTHON_BIN" data_generation/check_sources.py \
    --gutenberg-ids data_generation/sources/gutenberg_ids.txt \
    --gutenberg-urls data_generation/sources/gutenberg_urls.txt \
    --annas-urls data_generation/sources/annas_urls.txt \
    $( [[ "$SCRAPE_GUTENBERG" == "1" ]] && echo "--scrape-gutenberg" ) \
    $( [[ "$SCRAPE_ANNAS" == "1" ]] && echo "--scrape-annas" ) \
    || echo "[warn] Source connectivity check failed"
fi

if [[ -s data_generation/sources/gutenberg_ids.txt ]]; then
  echo "==> Collecting Project Gutenberg (IDs)"
  "$PYTHON_BIN" data_generation/collect_gutenberg.py \
    --ids data_generation/sources/gutenberg_ids.txt \
    --out data_generation/raw/gutenberg \
    --strip-boilerplate
fi

if [[ "$SCRAPE_GUTENBERG" == "1" && -s data_generation/sources/gutenberg_urls.txt ]]; then
  echo "==> Collecting Project Gutenberg (URLs)"
  "$PYTHON_BIN" data_generation/collect_gutenberg.py \
    --from-urls data_generation/sources/gutenberg_urls.txt \
    --out data_generation/raw/gutenberg \
    --strip-boilerplate
fi

if [[ -s data_generation/sources/annas_urls.txt ]]; then
  echo "==> Collecting Anna's Archive (URLs)"
  "$PYTHON_BIN" data_generation/collect_annas.py \
    --urls data_generation/sources/annas_urls.txt \
    --out data_generation/raw/annas \
    $( [[ "$SCRAPE_ANNAS" == "1" ]] && echo "--scrape" )
fi

echo "==> Extracting raw text"
"$PYTHON_BIN" data_generation/extract_text.py \
  --in data_generation/raw \
  --out data_generation/raw_text

echo "==> Cleaning text"
"$PYTHON_BIN" data_generation/clean_text.py \
  --in data_generation/raw_text \
  --out data_generation/clean \
  --gutenberg

echo "==> Sentence splitting"
"$PYTHON_BIN" data_generation/sentence_split.py \
  --in data_generation/clean \
  --out data_generation/sentences/sentences.jsonl

echo "==> Batch translate"
"$PYTHON_BIN" data_generation/batch_translate.py \
  --input data_generation/sentences/sentences.jsonl \
  --output data_generation/sentences/translations.jsonl \
  --mode "$MODE" \
  --server-url "$SERVER_URL" \
  --engine "$ENGINE" \
  --mirror-rate "$MIRROR_RATE" \
  --limit "$LIMIT" \
  --sleep "$SLEEP"

echo "==> Build dictionary"
"$PYTHON_BIN" data_generation/build_dictionary.py \
  --input data_generation/sentences/sentences.jsonl \
  --output data_generation/dictionary/zyntalic_dictionary.json \
  --output-tsv data_generation/dictionary/zyntalic_dictionary.tsv

echo "==> Done"
