from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Optional: PyPDF import
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import multipart  # type: ignore  # noqa: F401
    MULTIPART_INSTALLED = True
except ImportError:
    MULTIPART_INSTALLED = False

genai = None

from zyntalic.logging_utils import get_logger  # noqa: E402
from zyntalic.translator import (  # noqa: E402
    mirror_readback,
    translate_text,
    warm_translation_pipeline,
)
from zyntalic.utils.cache import (  # noqa: E402
    get_cached_translation,
    init_cache,
    put_cached_translation,
)

# Cache translations by default for repeatability and speed.
# Disable via env (ZYNTALIC_USE_CACHE=0) if fresh outputs are required.
USE_CACHE = os.getenv("ZYNTALIC_USE_CACHE", "1").lower() not in ("0", "false", "no", "off")

app = FastAPI(title="Zyntalic API", version="0.3.0")
logger = get_logger("zyntalic.web")
MAX_TEXT_CHARS = int(os.getenv("ZYNTALIC_MAX_TEXT_CHARS", "20000"))
ALLOWED_ENGINES = {"core", "transformer", "chiasmus", "test_suite", "reverse"}

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
    logger.warning("CORSMiddleware could not be imported. Ensure fastapi is installed.")


@app.on_event("startup")
async def startup_event():
    # Warm up cache on startup
    init_cache()
    try:
        warm_translation_pipeline()
    except Exception as exc:
        logger.warning("Translation warmup skipped: %s", exc)

# Mount static directory
# We now point to the built React app in zyntalic-flow/dist
# If running from project root:
repo_root = Path(__file__).resolve().parents[2]
static_dir = repo_root / "zyntalic-flow" / "dist"
public_dir = repo_root / "zyntalic-flow" / "public"

if not static_dir.exists():
    # Fallback to old static if build fails or during dev
    logger.warning("React build not found at %s. Falling back to legacy static.", static_dir)
    static_dir = Path(__file__).resolve().parent / "static"

assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    logger.warning("Assets directory not found at %s. Static assets will 404 until the frontend is built.", assets_dir)


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
    evidentiality: str = "direct"
    register: str = "formal"
    dialect: str = "standard"
    anchor_mode: str = "auto"
    selected_anchors: list[str] = Field(default_factory=list)
    frame_a: str = ""
    frame_b: str = ""
    zyntalic_only: bool = False


def _request_payload(req: TranslateRequest) -> dict:
    if hasattr(req, "model_dump"):
        return req.model_dump()
    return req.dict()


def _translation_options(req: TranslateRequest) -> dict:
    payload = _request_payload(req)
    return {
        "evidentiality": payload.get("evidentiality", "direct"),
        "register": payload.get("register", "formal"),
        "dialect": payload.get("dialect", "standard"),
        "anchor_mode": payload.get("anchor_mode", "auto"),
        "selected_anchors": payload.get("selected_anchors", []),
        "frame_a": payload.get("frame_a", ""),
        "frame_b": payload.get("frame_b", ""),
    }


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
        '\x00': '',  # Remove Unicode replacement character
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
                    logger.warning("Could not extract text from page %s: %s", page_num + 1, e)
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
        text = (req.text or "").strip()
        translation_options = _translation_options(req)
        if not text:
            raise HTTPException(status_code=400, detail="Text is required.")
        if len(text) > MAX_TEXT_CHARS:
            raise HTTPException(status_code=413, detail=f"Text too large (>{MAX_TEXT_CHARS} chars).")
        if not (0.0 <= req.mirror_rate <= 1.0):
            raise HTTPException(status_code=422, detail="mirror_rate must be between 0.0 and 1.0.")
        if req.engine not in ALLOWED_ENGINES:
            raise HTTPException(status_code=422, detail=f"Unsupported engine: {req.engine}")

        logger.info("Translate request: len=%s engine=%s mirror_rate=%.2f", len(text), req.engine, req.mirror_rate)

        cached = None
        if USE_CACHE:
            cached = get_cached_translation(
                text,
                req.engine,
                req.mirror_rate,
                options=translation_options,
            )
        if cached:
            sidecar = cached.get("sidecar") or {}
            requested_anchor_mode = str(translation_options.get("anchor_mode", "auto"))
            requested_selected = [
                str(item)
                for item in translation_options.get("selected_anchors", [])
                if str(item).strip()
            ]
            requested_frames = {
                key: value
                for key, value in (
                    ("A", translation_options.get("frame_a", "")),
                    ("B", translation_options.get("frame_b", "")),
                )
                if isinstance(value, str) and value.strip()
            }
            cached_frames = {
                str(frame.get("id")): str(frame.get("anchor"))
                for frame in sidecar.get("frames", [])
                if isinstance(frame, dict)
            }
            cached_anchor_names = {
                str(item.get("name"))
                for item in sidecar.get("anchor_weights", [])
                if isinstance(item, dict) and item.get("name")
            }
            if (
                not sidecar
                or "scope_signature" not in sidecar
                or "tokens" not in sidecar
                or "anchor_mode" not in sidecar
                or "selected_anchors" not in sidecar
                or str(sidecar.get("anchor_mode") or "auto") != requested_anchor_mode
                or list(sidecar.get("selected_anchors") or []) != requested_selected
                or any(cached_frames.get(frame_id) != anchor for frame_id, anchor in requested_frames.items())
                or any(anchor not in cached_anchor_names for anchor in requested_frames.values())
            ):
                cached = None
        if cached:
            logger.info("Translate cache hit")
            if req.mirror_rate > 0.75 and not cached.get("mirror_text"):
                cached["mirror_text"] = mirror_readback(
                    cached.get("source", text),
                    cached.get("anchors", []),
                    fallback_to_semantic=requested_anchor_mode != "neutral",
                )
            if req.zyntalic_only:
                return {
                    "rows": [
                        {
                            "target": cached.get("target", ""),
                            "mirror_text": cached.get("mirror_text", ""),
                            "sidecar": cached.get("sidecar", {}),
                        }
                    ],
                    "cached": True,
                }
            return {"rows": [cached], "cached": True}

        logger.info("Generating translation (cache %s)", "enabled" if USE_CACHE else "disabled")
        rows = translate_text(
            text,
            mirror_rate=req.mirror_rate,
            engine=req.engine,
            config=translation_options,
        )
        logger.info("Generated %s translation rows", len(rows))

        stored_rows = []
        for i, row in enumerate(rows):
            logger.debug("Row %s: source='%s' target='%s'", i, row.get("source", "N/A")[:30], row.get("target", "N/A")[:30])
            stored_rows.append(
                put_cached_translation(
                    source=row.get("source", req.text),
                    target=row.get("target", ""),
                    engine=row.get("engine", req.engine),
                    mirror_rate=req.mirror_rate,
                    anchors=row.get("anchors", []),
                    embedding=row.get("embedding") if isinstance(row, dict) else None,
                    mirror_text=row.get("mirror_text") if isinstance(row, dict) else None,
                    sidecar=row.get("sidecar") if isinstance(row, dict) else None,
                    options=translation_options,
                ) if USE_CACHE else row
            )

        logger.info("Translate success: returning %s rows", len(stored_rows))
        if req.zyntalic_only:
            return {
                "rows": [
                    {
                        "target": row.get("target", ""),
                        "mirror_text": row.get("mirror_text", ""),
                        "sidecar": row.get("sidecar", {}),
                    }
                    for row in stored_rows
                ],
                "cached": False,
            }
        return {"rows": stored_rows, "cached": False}

    except Exception as exc:
        logger.exception("Translation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Translation failed: {exc}") from exc
