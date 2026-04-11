# Zyntalic Status & Quick Fix Guide

## ✅ What's Working

1. **Frontend rebuilt successfully** (11:03 AM today)
   - File: `zyntalic-flow/dist/assets/index-BFk5Z0w3.js`
   - New output format implemented: Shows `[English] → Zyntalic`

2. **Backend code updated**:
   - ✅ PDF cleaning: Removes metadata, garbled characters  
   - ✅ Output simplified: Only shows `⟦ctx:han=뽻륉맣⟧` (no anchor/lemma/pos)
   - ✅ Translation includes source sentence

3. **API endpoints working**:
   - `/translate` - Translates text
   - `/upload` - Uploads PDFs/text files
   - `/health` - Health check

## ⚠️ Current Issues

### Windows (Your current system)
- Server runs but exits when other commands execute
- This is expected PowerShell behavior - running commands interrupts background process

### Linux/WSL (Your screenshot error)
- **Port 8001 already in use** - Another process is using the port
- pywebview dependencies missing (non-critical, uses browser instead)

## 🔧 Quick Fixes

### For Linux/WSL:

```bash
# 1. Kill process on port 8001
lsof -ti :8001 | xargs kill -9

# 2. Start server
python3 -m scripts.run_desktop
```

### For Windows:

```powershell
# Use the batch file
scripts\start_server.bat

# OR manually:
python -m scripts.run_desktop
```

## 🎯 What You'll See Now

**Input**: "The cat walks in the garden."

**Output**:
```
[The cat walks in the garden.]
→ 먯tol쏎 꽭옒 툥늎źą ⟦ctx:han=뿡댩⟧
```

**Benefits**:
- ✅ See what's being translated (English source)
- ✅ See the Zyntalic translation
- ✅ Only Korean context tail (no metadata clutter)
- ✅ PDF uploads cleaned (no %PDF-1.7, endobj, etc.)

## 📊 System Status

Run this to check everything:
```bash
python scripts/check_status.py
```

Run this to test output format:
```bash
pytest -q tests/test_output_format.py
```

## 🐛 Troubleshooting

**"Failed to connect to Zyntalic Local Engine"**
- Server not running → Run `python -m scripts.run_desktop`
- Port conflict → Kill process on 8001 first

**"Address already in use"**
```bash
# Linux
lsof -ti :8001 | xargs kill -9

# Windows
netstat -ano | findstr :8001
taskkill /F /PID <PID>
```

**PDF shows garbled characters**
- Server has latest code (applied today)
- Just restart: `python -m run_desktop`

## 📝 Testing

The test scripts verify everything works:

1. `test_output_format.py` - Shows new output format
2. `test_api_connection.py` - Tests API connectivity  
3. `check_status.py` - Full system diagnostic

All tests passed when server is running!

## 🚧 To Implement (LLM-Ready Language Quality)

Priority objective: make Zyntalic generation robust and high quality without depending on Gemini.

### P0 - Core quality and determinism

1. **Strengthen rule engine fidelity**
   - Formalize and enforce grammar rules (S-O-V-C ordering, role markers, morphology constraints) in one canonical pipeline.
   - Add rule validation pass before final surface rendering.

2. **Deterministic quality gates**
   - Add regression tests that fail when output violates script ratios, grammar constraints, or context-tail format.
   - Add golden-set snapshots for 200-500 benchmark prompts.

3. **Generator upgrade (non-Gemini fallback first)**
   - Refactor generator to use rule-guided token/word assembly with explicit morphology/syntax checks.
   - Keep current deterministic path as baseline; avoid introducing stochastic drift.

### P1 - Embeddings and semantic grounding

4. **Embedding backend hardening**
   - Improve hash-only fallback quality with better lexical similarity heuristics (lemma/stem/token features + anchor priors), not just random-like hash vectors.
   - Add consistent dimensionality/version tagging to embedding caches.

5. **Anchor relevance calibration**
   - Re-score anchor weights with sentence-level plus token-level blending.
   - Add eval metrics for anchor stability across paraphrases.

6. **Vocabulary/lexicon expansion quality**
   - Expand coverage for common verbs, function words, and domain vocabulary.
   - Add quality checks to prevent malformed mixed-script outputs.

### P2 - Optional Gemini integration (assistive, not required)

7. **Gemini as optional enhancer only**
   - Keep Gemini path feature-flagged and non-blocking.
   - Ensure all primary translation tests pass with Gemini disabled.

8. **Dual-path evaluation**
   - Compare deterministic-only vs Gemini-assisted outputs on the same benchmark set.
   - Track gains in semantic coherence without sacrificing deterministic reproducibility.

### P3 - LLM-focused evaluation suite

9. **LLM readiness benchmark**
   - Create an evaluation set for instruction-following, consistency, reversibility hints, and long-context stability.
   - Add CI checks for drift in morphology, syntax, and anchor semantics.

10. **Implementation target**
   - Deliver a stable synthetic language engine that is rule-first, deterministic, and usable as an LLM-facing representation layer with minimal external model dependence.
