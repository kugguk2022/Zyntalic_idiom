from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import io
import os
from pathlib import Path
import time

# Optional: PyPDF import
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import multipart  # type: ignore
    MULTIPART_INSTALLED = True
except ImportError:
    MULTIPART_INSTALLED = False

genai = None

from zyntalic.translator import translate_text, warm_translation_pipeline
from zyntalic.utils.cache import (
    get_cached_translation,
    put_cached_translation,
    init_cache,
)

# Disable cache via env if needed for batch/PDF flows where users expect fresh outputs
# Disable cache via env if needed for batch/PDF flows where users expect fresh outputs
USE_CACHE = False

app = FastAPI(title="Zyntalic API", version="0.3.0")

try:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except ImportError:
    print("WARNING: CORSMiddleware could not be imported. Ensure fastapi is installed.")


@app.on_event("startup")
async def startup_event():
    # Warm up cache on startup
    init_cache()
    try:
        warm_translation_pipeline()
    except Exception as exc:
        print(f"[startup] Translation warmup skipped: {exc}")

# Mount static directory
# We now point to the built React app in zyntalic-flow/dist
# If running from project root:
repo_root = Path(__file__).resolve().parents[2]
static_dir = repo_root / "zyntalic-flow" / "dist"
public_dir = repo_root / "zyntalic-flow" / "public"

if not static_dir.exists():
    # Fallback to old static if build fails or during dev
    print(f"WARNING: React build not found at {static_dir}. Falling back to legacy static.")
    static_dir = Path(__file__).resolve().parent / "static"

assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    print(f"WARNING: Assets directory not found at {assets_dir}. Static assets will 404 until the frontend is built.")


def _find_frontend_file(filename: str) -> Path | None:
    """Return the first matching file from the built or public frontend folders."""
    for base in (static_dir, public_dir):
        candidate = base / filename
        if candidate.exists():
            return candidate
    return None


class TranslateRequest(BaseModel):
    text: str
    mirror_rate: float = 0.3  # Lower value = more Zyntalic vocabulary, higher = more English templates
    engine: str = "core"  # "core"|"chiasmus"|"transformer"|"test_suite"


@app.get("/")
def read_root():
    index_path = _find_frontend_file("index.html")
    if index_path:
        return FileResponse(index_path)
    return {
        "status": "ok",
        "message": "Frontend build not found. Run: cd zyntalic-flow && npm install && npm run build",
    }


@app.get("/favicon.ico")
def favicon():
    icon_path = _find_frontend_file("favicon.ico") or _find_frontend_file("favicon.svg")
    if icon_path:
        media = "image/x-icon" if icon_path.suffix == ".ico" else "image/svg+xml"
        return FileResponse(icon_path, media_type=media)
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/favicon.svg")
def favicon_svg():
    icon_path = _find_frontend_file("favicon.svg") or _find_frontend_file("favicon.ico")
    if icon_path:
        media = "image/svg+xml" if icon_path.suffix == ".svg" else "image/x-icon"
        return FileResponse(icon_path, media_type=media)
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/index.css")
def index_css():
    css_path = _find_frontend_file("index.css")
    if css_path:
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="index.css not found")

def clean_pdf_text(raw_text: str) -> str:
    """Clean extracted PDF text by removing metadata, garbled characters, and extra whitespace."""
    import re
    
    # Remove common PDF metadata patterns
    metadata_patterns = [
        r'%PDF-[\d\.]+',
        r'%����',
        r'%[^\n]*',  # Remove PDF comment lines
        r'/Author\([^)]*\)',
        r'/Creator\([^)]*\)',
        r'/Producer\([^)]*\)',
        r'/Title\([^)]*\)',
        r'/Subject\([^)]*\)',
        r'/Keywords\([^)]*\)',
        r'/CreationDate\([^)]*\)',
        r'/ModDate\([^)]*\)',
        r'/[A-Z][a-z]+\([^)]*\)',  # Any /Property(value) pattern
        r'\d+ \d+ obj',
        r'endobj',
        r'stream\s*.*?\s*endstream',
        r'<<[^>]*>>',
        r'\[http://[^\]]*\]',
        r'xref',
        r'trailer',
        r'startxref',
        r'%%EOF',
        r'/Filter\s+/[A-Za-z]+',
        r'/Length1?\s+\d+',
        r'/Type\s+/[A-Za-z]+',
    ]
    
    cleaned = raw_text
    for pattern in metadata_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove non-printable characters and binary data
    # Keep only ASCII printable, common punctuation, spaces, and basic Latin
    cleaned = ''.join(char for char in cleaned if (
        char.isprintable() or char in '\n\r\t'
    ) and ord(char) < 127 or char.isspace())
    
    # Replace common PDF encoding issues
    replacements = {
        '�': '',  # Remove replacement character
        '\x00': '',  # Remove null bytes
        '\ufffd': '',  # Remove Unicode replacement character
        '\r\n': '\n',  # Normalize line endings
        '\r': '\n',
    }
    
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # Remove patterns that look like encoding artifacts
    cleaned = re.sub(r'[^\w\s.,!?;:\'"\-()\[\]]+', '', cleaned)
    
    # Remove multiple spaces and normalize whitespace
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    
    # Remove lines that are just numbers, single characters, or look like metadata
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        # Skip empty, numeric-only, single char, or metadata-looking lines
        if (len(line) > 3 and 
            not line.isdigit() and 
            not re.match(r'^[A-Z][a-z]+$', line) and  # Single words capitalized (often artifacts)
            not re.match(r'^\W+$', line)):  # Only punctuation
            filtered_lines.append(line)
    
    cleaned = '\n'.join(filtered_lines)
    
    # Final cleanup: remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


if MULTIPART_INSTALLED:

    @app.post("/upload")
    async def upload_pdf(file: UploadFile = File(...)):
        """Upload and extract text from PDF or text files."""
        
        # Handle plain text files
        if file.filename.endswith((".txt", ".md")):
            try:
                content = await file.read()
                text = content.decode("utf-8", errors="ignore")
                return {"text": text.strip()}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reading text file: {str(e)}")
        
        # Handle PDF files
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="File must be PDF, TXT, or MD format",
            )
        
        if not PyPDF2:
            raise HTTPException(
                status_code=500,
                detail="PyPDF2 not installed. Install with: pip install -e '.[pdf]'",
            )

        try:
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="PDF is encrypted. Please provide an unencrypted PDF.",
                )

            # Extract text from all pages
            raw_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        raw_text += page_text + "\n"
                except Exception as e:
                    # Skip problematic pages but continue
                    print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
                    continue

            # Clean the extracted text
            cleaned_text = clean_pdf_text(raw_text)

            if not cleaned_text or len(cleaned_text) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="No readable text found in PDF. The file may be scanned images or corrupted.",
                )

            return {"text": cleaned_text}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

else:

    @app.post("/upload")
    async def upload_pdf_unavailable():
        """Fallback when python-multipart is missing."""
        raise HTTPException(
            status_code=501,
            detail=(
                "File upload requires python-multipart. "
                "Install with: pip install python-multipart or pip install -e '.[web,pdf]'."
            ),
        )


@app.get("/health")
def health():
    return {"ok": True}

@app.post("/translate")
def translate(req: TranslateRequest):
    try:
        print(f"[TRANSLATE] Request received: text='{req.text[:50]}...', engine={req.engine}, mirror_rate={req.mirror_rate}")
        
        cached = None
        if USE_CACHE:
            cached = get_cached_translation(req.text, req.engine, req.mirror_rate)
        if cached:
            print(f"[TRANSLATE] Cache hit, returning cached result")
            return {"rows": [cached], "cached": True}

        print(f"[TRANSLATE] Generating new translation... (cache {'enabled' if USE_CACHE else 'disabled'})")
        rows = translate_text(req.text, mirror_rate=req.mirror_rate, engine=req.engine)
        print(f"[TRANSLATE] Generated {len(rows)} translation rows")

        stored_rows = []
        for i, row in enumerate(rows):
            print(f"[TRANSLATE] Row {i}: source='{row.get('source', 'N/A')[:30]}...', target='{row.get('target', 'N/A')[:30]}...'")
            stored_rows.append(
                put_cached_translation(
                    source=row.get("source", req.text),
                    target=row.get("target", ""),
                    engine=row.get("engine", req.engine),
                    mirror_rate=req.mirror_rate,
                    anchors=row.get("anchors", []),
                    embedding=row.get("embedding") if isinstance(row, dict) else None,
                ) if USE_CACHE else row
            )

        print(f"[TRANSLATE] Success: returning {len(stored_rows)} rows")
        return {"rows": stored_rows, "cached": False}
        
    except Exception as exc:
        print(f"[TRANSLATE] ERROR: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Translation failed: {exc}") from exc

