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
