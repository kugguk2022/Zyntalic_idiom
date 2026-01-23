#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect Project Gutenberg texts.

Supports:
- IDs (preferred) using Gutenberg's public text endpoints.
- Optional scraping of book pages to find a plain-text link.

This is opt-in and intended for public-domain texts only.
"""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

try:
    import requests
except Exception as exc:  # pragma: no cover - runtime guard
    raise SystemExit("Missing dependency: requests. Install with: pip install -e .[data]") from exc

try:
    from bs4 import BeautifulSoup
except Exception as exc:  # pragma: no cover - runtime guard
    raise SystemExit("Missing dependency: beautifulsoup4. Install with: pip install -e .[data]") from exc

try:
    from tqdm import tqdm
except Exception as exc:  # pragma: no cover - runtime guard
    raise SystemExit("Missing dependency: tqdm. Install with: pip install -e .[data]") from exc


_START_RE = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)
_END_RE = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)


def read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    lines: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def candidate_text_urls(book_id: str) -> List[str]:
    return [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    ]


def find_plain_text_link(page_url: str) -> Optional[str]:
    try:
        resp = requests.get(page_url, timeout=30)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        label = (a.get_text() or "").lower()
        if "plain text" in label and "utf-8" in label:
            links.append(href)
        elif href.endswith(".txt"):
            links.append(href)

    if not links:
        return None

    link = links[0]
    if link.startswith("//"):
        link = "https:" + link
    if link.startswith("/"):
        parsed = urlparse(page_url)
        link = f"{parsed.scheme}://{parsed.netloc}{link}"
    return link


def strip_gutenberg_boilerplate(text: str) -> str:
    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and _START_RE.search(line):
            start_idx = i + 1
        if end_idx is None and _END_RE.search(line):
            end_idx = i
            break
    if start_idx is not None and end_idx is not None and start_idx < end_idx:
        return "\n".join(lines[start_idx:end_idx]).strip()
    return text


def download_text(urls: Iterable[str]) -> Optional[str]:
    for url in urls:
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and resp.text:
                return resp.text
        except Exception:
            continue
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ids", default="data_generation/sources/gutenberg_ids.txt")
    p.add_argument("--from-urls", default=None, help="File with Gutenberg book page URLs")
    p.add_argument("--out", default="data_generation/raw/gutenberg")
    p.add_argument("--strip-boilerplate", action="store_true")
    p.add_argument("--delay", type=float, default=1.0)
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ids = read_lines(Path(args.ids))
    urls = read_lines(Path(args.from_urls)) if args.from_urls else []

    if not ids and not urls:
        print("No IDs or URLs provided.")
        return 1

    if ids:
        for book_id in tqdm(ids, desc="Gutenberg IDs"):
            text = download_text(candidate_text_urls(book_id))
            if not text:
                print(f"Failed to fetch ID {book_id}")
                continue
            if args.strip_boilerplate:
                text = strip_gutenberg_boilerplate(text)
            out_path = out_dir / f"pg{book_id}.txt"
            out_path.write_text(text, encoding="utf-8")
            time.sleep(args.delay)

    if urls:
        for page_url in tqdm(urls, desc="Gutenberg URLs"):
            text_url = find_plain_text_link(page_url)
            if not text_url:
                print(f"No plain text link found: {page_url}")
                continue
            text = download_text([text_url])
            if not text:
                print(f"Failed to fetch: {text_url}")
                continue
            if args.strip_boilerplate:
                text = strip_gutenberg_boilerplate(text)
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(urlparse(page_url).path).stem)
            if not safe_name:
                safe_name = "gutenberg_book"
            out_path = out_dir / f"{safe_name}.txt"
            out_path.write_text(text, encoding="utf-8")
            time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
