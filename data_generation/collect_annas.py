#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect texts from user-provided URLs (e.g., Anna's Archive pages or direct links).

This script does NOT perform bulk crawling. It only fetches URLs you provide.
If --scrape is enabled, it will parse an HTML page and try to find a direct
text/pdf/epub link to download.
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


def pick_download_link(page_url: str) -> Optional[str]:
    try:
        resp = requests.get(page_url, timeout=30)
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


def download_url(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200 and resp.content:
            return resp.content
    except Exception:
        return None
    return None


def file_name_from_url(url: str, fallback: str) -> str:
    path = Path(urlparse(url).path)
    name = path.name
    if not name:
        return fallback
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--urls", default="data_generation/sources/annas_urls.txt")
    p.add_argument("--out", default="data_generation/raw/annas")
    p.add_argument("--scrape", action="store_true")
    p.add_argument("--delay", type=float, default=1.0)
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = read_lines(Path(args.urls))
    if not urls:
        print("No URLs provided.")
        return 1

    for idx, url in enumerate(tqdm(urls, desc="Downloads"), 1):
        target_url = url
        if args.scrape:
            link = pick_download_link(url)
            if link:
                target_url = link
            else:
                print(f"No download link found on page: {url}")
                continue

        data = download_url(target_url)
        if data is None:
            print(f"Failed to fetch: {target_url}")
            continue

        fname = file_name_from_url(target_url, f"annas_{idx}")
        out_path = out_dir / fname
        out_path.write_bytes(data)
        time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
