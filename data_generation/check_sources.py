#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight connectivity checks for optional data sources.

This does not download full content; it only verifies that URLs/IDs respond.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

try:
    import requests
except Exception as exc:  # pragma: no cover - runtime guard
    raise SystemExit("Missing dependency: requests. Install with: pip install -e .[data]") from exc

try:
    from bs4 import BeautifulSoup
except Exception as exc:  # pragma: no cover - runtime guard
    raise SystemExit("Missing dependency: beautifulsoup4. Install with: pip install -e .[data]") from exc


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


def ok_url(url: str, timeout: int) -> bool:
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return True
        resp = requests.get(url, timeout=timeout, stream=True)
        return resp.status_code == 200
    except Exception:
        return False


def find_plain_text_link(page_url: str, timeout: int) -> Optional[str]:
    try:
        resp = requests.get(page_url, timeout=timeout)
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


def pick_download_link(page_url: str, timeout: int) -> Optional[str]:
    try:
        resp = requests.get(page_url, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []
    for a in soup.select("a[href]"):
        href = a.get("href") or ""
        if href.endswith((".txt", ".pdf", ".epub")):
            candidates.append(href)

    if not candidates:
        return None

    link = candidates[0]
    if link.startswith("//"):
        link = "https:" + link
    if link.startswith("/"):
        parsed = urlparse(page_url)
        link = f"{parsed.scheme}://{parsed.netloc}{link}"
    return link


def check_gutenberg(ids: List[str], scrape_urls: List[str], timeout: int) -> int:
    ok = 0
    for book_id in ids:
        urls = candidate_text_urls(book_id)
        if any(ok_url(u, timeout) for u in urls):
            ok += 1
        else:
            print(f"[fail] Gutenberg ID {book_id}")
    for page_url in scrape_urls:
        link = find_plain_text_link(page_url, timeout)
        if link and ok_url(link, timeout):
            ok += 1
        else:
            print(f"[fail] Gutenberg URL {page_url}")
    return ok


def check_annas(urls: List[str], scrape: bool, timeout: int) -> int:
    ok = 0
    for url in urls:
        target = url
        if scrape:
            link = pick_download_link(url, timeout)
            if not link:
                print(f"[fail] Anna's page (no link): {url}")
                continue
            target = link
        if ok_url(target, timeout):
            ok += 1
        else:
            print(f"[fail] Anna's URL {url}")
    return ok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--gutenberg-ids", default="data_generation/sources/gutenberg_ids.txt")
    p.add_argument("--gutenberg-urls", default="data_generation/sources/gutenberg_urls.txt")
    p.add_argument("--annas-urls", default="data_generation/sources/annas_urls.txt")
    p.add_argument("--scrape-gutenberg", action="store_true")
    p.add_argument("--scrape-annas", action="store_true")
    p.add_argument("--timeout", type=int, default=15)
    args = p.parse_args()

    ids = read_lines(Path(args.gutenberg_ids))
    gut_urls = read_lines(Path(args.gutenberg_urls)) if args.scrape_gutenberg else []
    annas = read_lines(Path(args.annas_urls))

    total = 0
    ok = 0

    if ids or gut_urls:
        total += len(ids) + len(gut_urls)
        ok += check_gutenberg(ids, gut_urls, args.timeout)
    else:
        print("[skip] Gutenberg: no IDs/URLs")

    if annas:
        total += len(annas)
        ok += check_annas(annas, args.scrape_annas, args.timeout)
    else:
        print("[skip] Anna's: no URLs")

    print(f"Connectivity: {ok}/{total} OK")
    return 0 if total == ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
