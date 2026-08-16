# syntax=docker/dockerfile:1

# ---- Stage 1: build the React frontend --------------------------------------
# The API serves zyntalic-flow/dist. That directory is gitignored, so it must be
# built here; without this stage the image falls back to apps/web/static and
# visitors get the legacy placeholder page instead of the real UI.
FROM node:22-slim AS frontend

WORKDIR /build
COPY zyntalic-flow/package.json zyntalic-flow/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY zyntalic-flow/ ./
RUN npm run build


# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app

# Install from the source tree in editable mode. apps/web/app.py resolves the
# frontend directory relative to its own __file__, so the package must stay at
# /app rather than being copied into site-packages.
COPY pyproject.toml README.md LICENSE ./
COPY zyntalic/ ./zyntalic/
COPY apps/ ./apps/
RUN pip install --no-cache-dir -e ".[web,pdf]"

# public/ supplies the favicon fallbacks the API looks for alongside dist/.
COPY --from=frontend /build/dist ./zyntalic-flow/dist
COPY zyntalic-flow/public ./zyntalic-flow/public

# Translation cache lives on a volume so redeploys do not start cold.
ENV ZYNTALIC_CACHE_PATH=/data/zyntalic/translations.sqlite3

RUN mkdir -p /data/zyntalic \
    && useradd --create-home --uid 10001 zyntalic \
    && chown -R zyntalic:zyntalic /app /data
USER zyntalic

EXPOSE 8000

# Startup warms lexicons and anchor vectors, which takes ~15s on a small host.
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/v1/health', timeout=4).status == 200 else 1)"

# One worker on purpose: the rate limiter keeps counters in process memory and
# the cache is local SQLite. Scaling out requires moving both first.
CMD ["uvicorn", "apps.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
