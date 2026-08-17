from __future__ import annotations

import hashlib
import ipaddress
import io
import os
import re
import secrets
import threading
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
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
RATE_LIMIT_PER_MINUTE = int(os.getenv("ZYNTALIC_RATE_LIMIT_PER_MINUTE", "60"))
API_KEY = os.getenv("ZYNTALIC_API_KEY", "")
ALLOW_UNAUTHENTICATED_LOCAL = os.getenv(
    "ZYNTALIC_ALLOW_UNAUTHENTICATED_LOCAL", "0"
).lower() in {"1", "true", "yes", "on"}

Engine = Literal["core", "transformer", "chiasmus", "test_suite", "reverse"]


class SlidingWindowRateLimiter:
    """Small process-local limiter for authenticated API traffic."""

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = max(0, limit)
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, identity: str) -> int | None:
        if self.limit == 0:
            return None
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events.setdefault(identity, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return max(1, int(self.window_seconds - (now - events[0])) + 1)
            events.append(now)
        return None


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ZyntalicApiKey",
    description="API key configured by the server's ZYNTALIC_API_KEY setting.",
    auto_error=False,
)
rate_limiter = SlidingWindowRateLimiter(RATE_LIMIT_PER_MINUTE)


def _is_loopback_request(request: Request) -> bool:
    """Return true only for clients whose resolved address is loopback."""
    host = request.client.host if request.client else ""
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # Do not trust hostnames or forwarding headers at this boundary.
        return False


def require_api_access(
    request: Request,
    supplied_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> None:
    """Allow real loopback clients; require a valid key everywhere else."""
    if _is_loopback_request(request):
        identity = f"local:{request.client.host if request.client else 'unknown'}"
    else:
        if not API_KEY:
            raise HTTPException(
                status_code=503,
                detail="API authentication is not configured.",
            )
        if supplied_key is None or not secrets.compare_digest(supplied_key, API_KEY):
            raise HTTPException(
                status_code=401,
                detail="A valid X-API-Key header is required.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        identity = f"key:{hashlib.sha256(supplied_key.encode()).hexdigest()}"

    retry_after = rate_limiter.check(identity)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded.",
            headers={"Retry-After": str(retry_after)},
        )


PROTECTED_ROUTE_DEPENDENCIES = [Depends(require_api_access)]


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
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
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


class ErrorResponse(BaseModel):
    detail: str


class RootStatusResponse(BaseModel):
    status: Literal["ok"]
    message: str


class LegacyHealthResponse(BaseModel):
    ok: bool


class CacheStatusResponse(BaseModel):
    backend: str
    entries: int
    version: int | None = None


class ApiLimitsResponse(BaseModel):
    text_characters: int
    batch_items: int
    batch_characters: int
    upload_bytes: int
    requests_per_minute: int


class HealthResponse(BaseModel):
    ok: bool
    ready: bool
    version: str
    cache: CacheStatusResponse
    limits: ApiLimitsResponse


class SidecarResponse(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    frames: list[dict[str, Any]] = Field(default_factory=list)
    pivot: str = "neutral"
    anchor_weights: list[dict[str, Any]] = Field(default_factory=list)
    anchor_mode: str | None = None
    selected_anchors: list[str] = Field(default_factory=list)
    sigil: str | None = None
    sigil_type: str | None = None
    evidentiality: str | None = None
    register_name: str | None = Field(
        default=None, alias="register", serialization_alias="register"
    )
    dialect: str | None = None
    scope_signature: str | None = None
    tokens: list[dict[str, Any]] | None = None


class TranslationRowResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str | None = None
    target: str
    engine: Engine | None = None
    lemma: str | None = None
    anchors: list[Any] = Field(default_factory=list)
    embedding: list[float] | None = None
    mirror_text: str | None = None
    sidecar: SidecarResponse = Field(default_factory=SidecarResponse)
    rule_warnings: list[str] | None = None


class LegacyTranslateResponse(BaseModel):
    rows: list[TranslationRowResponse]
    cached: bool


class TranslateResponse(BaseModel):
    api_version: Literal["v1"]
    request_id: str
    rows: list[TranslationRowResponse]
    cached: bool
    processing_ms: float


class BatchItemResponse(BaseModel):
    index: int
    cached: bool
    rows: list[TranslationRowResponse]


class TranslateBatchResponse(BaseModel):
    api_version: Literal["v1"]
    request_id: str
    results: list[BatchItemResponse]
    items: int
    cache_hits: int
    processing_ms: float


class LegacyExtractResponse(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    api_version: Literal["v1"]
    request_id: str
    filename: str
    characters: int
    text: str


AUTH_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Missing or invalid API key."},
    429: {"model": ErrorResponse, "description": "Per-key rate limit exceeded."},
    503: {"model": ErrorResponse, "description": "API authentication is not configured."},
}


class TranslationOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mirror_rate: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Lower values produce more Zyntalic vocabulary.",
    )
    engine: Engine = "core"
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
    texts: list[str] = Field(min_length=1, max_length=MAX_BATCH_ITEMS)


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


@app.get("/", response_model=RootStatusResponse)
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

    @app.post(
        "/upload",
        response_model=LegacyExtractResponse,
        dependencies=PROTECTED_ROUTE_DEPENDENCIES,
        responses=AUTH_RESPONSES,
    )
    @app.post(
        "/v1/extract",
        response_model=ExtractResponse,
        dependencies=PROTECTED_ROUTE_DEPENDENCIES,
        responses=AUTH_RESPONSES,
    )
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

    @app.post(
        "/upload",
        response_model=LegacyExtractResponse,
        dependencies=PROTECTED_ROUTE_DEPENDENCIES,
        responses=AUTH_RESPONSES,
    )
    @app.post(
        "/v1/extract",
        response_model=ExtractResponse,
        dependencies=PROTECTED_ROUTE_DEPENDENCIES,
        responses=AUTH_RESPONSES,
    )
    async def upload_document_unavailable():
        raise HTTPException(
            status_code=501,
            detail="File upload requires python-multipart. Install with: pip install -e '.[web,pdf]'.",
        )


@app.get("/health", response_model=LegacyHealthResponse)
def health():
    return {"ok": True}


@app.get("/v1/health", response_model=HealthResponse)
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
            "requests_per_minute": RATE_LIMIT_PER_MINUTE,
        },
    }


@app.post(
    "/translate",
    response_model=LegacyTranslateResponse,
    dependencies=PROTECTED_ROUTE_DEPENDENCIES,
    responses=AUTH_RESPONSES,
)
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


@app.post(
    "/v1/translate",
    response_model=TranslateResponse,
    dependencies=PROTECTED_ROUTE_DEPENDENCIES,
    responses=AUTH_RESPONSES,
)
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


@app.post(
    "/v1/translate/batch",
    response_model=TranslateBatchResponse,
    dependencies=PROTECTED_ROUTE_DEPENDENCIES,
    responses=AUTH_RESPONSES,
)
def translate_batch_v1(request: Request, req: TranslateBatchRequest):
    """Translate inputs in order and sequentially within the current worker."""
    started = time.perf_counter()
    total_characters = sum(len(text or "") for text in req.texts)
    if total_characters > MAX_BATCH_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch too large (>{MAX_BATCH_CHARS} characters).",
        )
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
