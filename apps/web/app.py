from __future__ import annotations

import io
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

try:
    import pypdf
except ImportError:  # pragma: no cover - optional dependency
    pypdf = None

try:
    import python_multipart  # type: ignore  # noqa: F401

    MULTIPART_INSTALLED = True
except ImportError:  # pragma: no cover - optional dependency
    MULTIPART_INSTALLED = False

from zyntalic import __version__
from zyntalic.logging_utils import get_logger
from zyntalic.translator import translate_text, warm_translation_pipeline
from zyntalic.utils.cache import (
    cache_info,
    get_cached_response,
    init_cache,
    put_cached_response,
)

logger = get_logger("zyntalic.web")

USE_CACHE = os.getenv("ZYNTALIC_USE_CACHE", "1").lower() not in {
    "0",
    "false",
    "no",
    "off",
}
MAX_TEXT_CHARS = int(os.getenv("ZYNTALIC_MAX_TEXT_CHARS", "20000"))
MAX_BATCH_ITEMS = int(os.getenv("ZYNTALIC_MAX_BATCH_ITEMS", "32"))
MAX_BATCH_CHARS = int(os.getenv("ZYNTALIC_MAX_BATCH_CHARS", "100000"))
MAX_UPLOAD_BYTES = int(os.getenv("ZYNTALIC_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
ALLOWED_ENGINES = {"core", "transformer", "chiasmus", "test_suite", "reverse"}


def _cors_origins() -> list[str]:
    raw = os.getenv("ZYNTALIC_CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ready = False
    await run_in_threadpool(init_cache)
    try:
        await run_in_threadpool(warm_translation_pipeline)
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Translation warmup skipped: %s", exc)
    app.state.ready = True
    yield
    app.state.ready = False


app = FastAPI(
    title="Zyntalic API",
    version=__version__,
    description="Deterministic synthetic-language translation and document extraction.",
    lifespan=lifespan,
)

origins = _cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def request_metadata(request: Request, call_next):
    started = time.perf_counter()
    supplied = request.headers.get("X-Request-ID", "")
    request_id = supplied if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied) else uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - started) * 1000:.2f}"
    return response


repo_root = Path(__file__).resolve().parents[2]
static_dir = repo_root / "zyntalic-flow" / "dist"
public_dir = repo_root / "zyntalic-flow" / "public"

if not static_dir.exists():
    logger.warning("React build not found at %s. Falling back to legacy static.", static_dir)
    static_dir = Path(__file__).resolve().parent / "static"

assets_dir = static_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    logger.warning("Assets directory not found at %s. Static assets will 404.", assets_dir)


def _find_frontend_file(filename: str) -> Path | None:
    for base in (static_dir, public_dir):
        candidate = base / filename
        if candidate.exists():
            return candidate
    return None


class TranslationOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mirror_rate: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Lower values produce more Zyntalic vocabulary.",
    )
    engine: str = "core"
    evidentiality: str = "direct"
    register_name: str = Field(default="formal", alias="register", serialization_alias="register")
    dialect: str = "standard"
    anchor_mode: str = "auto"
    selected_anchors: list[str] = Field(default_factory=list, max_length=32)
    frame_a: str = ""
    frame_b: str = ""
    zyntalic_only: bool = False


class TranslateRequest(TranslationOptions):
    text: str


class TranslateBatchRequest(TranslationOptions):
    texts: list[str] = Field(min_length=1)


def _request_payload(req: BaseModel) -> dict[str, Any]:
    return req.model_dump(by_alias=True)


def _translation_options(req: TranslationOptions) -> dict[str, Any]:
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


def _validate_engine(engine: str) -> None:
    if engine not in ALLOWED_ENGINES:
        allowed = ", ".join(sorted(ALLOWED_ENGINES))
        raise HTTPException(
            status_code=422, detail=f"Unsupported engine: {engine}. Use: {allowed}."
        )


def _normalize_text(text: str) -> str:
    normalized = (text or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Text is required.")
    if len(normalized) > MAX_TEXT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Text too large (>{MAX_TEXT_CHARS} characters).",
        )
    return normalized


def _project_rows(rows: list[dict[str, Any]], zyntalic_only: bool) -> list[dict[str, Any]]:
    if not zyntalic_only:
        return rows
    return [
        {
            "target": row.get("target", ""),
            "mirror_text": row.get("mirror_text", ""),
            "sidecar": row.get("sidecar", {}),
        }
        for row in rows
    ]


def _translate_one(text: str, req: TranslationOptions) -> tuple[list[dict[str, Any]], bool]:
    normalized = _normalize_text(text)
    _validate_engine(req.engine)
    options = _translation_options(req)

    if USE_CACHE:
        cached_rows = get_cached_response(
            normalized,
            req.engine,
            req.mirror_rate,
            options=options,
        )
        if cached_rows is not None:
            return _project_rows(cached_rows, req.zyntalic_only), True

    logger.info(
        "Translate request: len=%s engine=%s mirror_rate=%.2f",
        len(normalized),
        req.engine,
        req.mirror_rate,
    )
    rows = translate_text(
        normalized,
        mirror_rate=req.mirror_rate,
        engine=req.engine,
        config=options,
    )
    if USE_CACHE:
        rows = put_cached_response(
            normalized,
            rows,
            req.engine,
            req.mirror_rate,
            options=options,
        )
    return _project_rows(rows, req.zyntalic_only), False


def _v1_response(
    request: Request,
    rows: list[dict[str, Any]],
    cached: bool,
    started: float,
) -> dict[str, Any]:
    return {
        "api_version": "v1",
        "request_id": request.state.request_id,
        "rows": rows,
        "cached": cached,
        "processing_ms": round((time.perf_counter() - started) * 1000, 2),
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
    """Remove common PDF artifacts while preserving Unicode source text."""
    metadata_patterns = [
        r"%PDF-[\d.]+",
        r"%[^\n]*",
        r"/(?:Author|Creator|Producer|Title|Subject|Keywords|CreationDate|ModDate)\([^)]*\)",
        r"\d+ \d+ obj",
        r"endobj",
        r"stream\s*.*?\s*endstream",
        r"<<[^>]*>>",
        r"xref",
        r"trailer",
        r"startxref",
        r"%%EOF",
    ]
    cleaned = raw_text
    for pattern in metadata_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    cleaned = cleaned.replace("\ufffd", "").replace("\x00", "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "".join(
        char for char in cleaned if char in "\n\t" or (char.isprintable() and char != "\x0b")
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    lines = [
        line.strip()
        for line in cleaned.split("\n")
        if len(line.strip()) > 3 and not line.strip().isdigit()
    ]
    return "\n".join(lines).strip()


def _extract_pdf(content: bytes) -> str:
    if pypdf is None:
        raise HTTPException(
            status_code=501,
            detail="PDF extraction is unavailable. Install with: pip install -e '.[pdf]'.",
        )
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise HTTPException(status_code=400, detail="PDF must be unencrypted.")
        pages: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
            except Exception as exc:  # pragma: no cover - depends on source PDF
                logger.warning("Could not extract PDF page %s: %s", page_number, exc)
                continue
            if page_text:
                pages.append(page_text)
        text = clean_pdf_text("\n".join(pages))
        if len(text) < 10:
            raise HTTPException(
                status_code=400,
                detail="No readable text found; the PDF may contain scanned images.",
            )
        return text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid PDF: {exc}") from exc


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (>{MAX_UPLOAD_BYTES} bytes).",
        )
    return content


if MULTIPART_INSTALLED:

    @app.post("/upload")
    @app.post("/v1/extract")
    async def upload_document(request: Request, file: UploadFile = File(...)):
        filename = (file.filename or "upload").strip()
        suffix = Path(filename).suffix.lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise HTTPException(status_code=400, detail="File must be PDF, TXT, or MD format.")
        content = await _read_upload(file)
        if suffix == ".pdf":
            text = await run_in_threadpool(_extract_pdf, content)
        else:
            text = content.decode("utf-8", errors="replace").strip()

        if request.url.path.startswith("/v1/"):
            return {
                "api_version": "v1",
                "request_id": request.state.request_id,
                "filename": filename,
                "characters": len(text),
                "text": text,
            }
        return {"text": text}

else:

    @app.post("/upload")
    @app.post("/v1/extract")
    async def upload_document_unavailable():
        raise HTTPException(
            status_code=501,
            detail="File upload requires python-multipart. Install with: pip install -e '.[web,pdf]'.",
        )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/health")
def health_v1(request: Request):
    return {
        "ok": True,
        "ready": bool(getattr(request.app.state, "ready", False)),
        "version": __version__,
        "cache": cache_info() if USE_CACHE else {"backend": "disabled", "entries": 0},
        "limits": {
            "text_characters": MAX_TEXT_CHARS,
            "batch_items": MAX_BATCH_ITEMS,
            "batch_characters": MAX_BATCH_CHARS,
            "upload_bytes": MAX_UPLOAD_BYTES,
        },
    }


@app.post("/translate")
def translate(req: TranslateRequest):
    """Backward-compatible translation endpoint used by the current UI."""
    try:
        rows, cached = _translate_one(req.text, req)
        return {"rows": rows, "cached": cached}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Translation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Translation failed.") from exc


@app.post("/v1/translate")
def translate_v1(request: Request, req: TranslateRequest):
    started = time.perf_counter()
    try:
        rows, cached = _translate_one(req.text, req)
        return _v1_response(request, rows, cached, started)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Translation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Translation failed.") from exc


@app.post("/v1/translate/batch")
def translate_batch_v1(request: Request, req: TranslateBatchRequest):
    started = time.perf_counter()
    if len(req.texts) > MAX_BATCH_ITEMS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large (>{MAX_BATCH_ITEMS} items).",
        )
    total_characters = sum(len(text or "") for text in req.texts)
    if total_characters > MAX_BATCH_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large (>{MAX_BATCH_CHARS} characters).",
        )
    _validate_engine(req.engine)

    results = []
    cache_hits = 0
    try:
        for index, text in enumerate(req.texts):
            rows, cached = _translate_one(text, req)
            cache_hits += int(cached)
            results.append({"index": index, "cached": cached, "rows": rows})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Batch translation failed: %s", exc)
        raise HTTPException(status_code=500, detail="Batch translation failed.") from exc

    return {
        "api_version": "v1",
        "request_id": request.state.request_id,
        "results": results,
        "items": len(results),
        "cache_hits": cache_hits,
        "processing_ms": round((time.perf_counter() - started) * 1000, 2),
    }
