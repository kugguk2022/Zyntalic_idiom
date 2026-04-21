#!/usr/bin/env python3
"""Manual demo of PDF text cleaning."""

import re


def clean_pdf_text(raw_text: str) -> str:
    """Clean extracted PDF text by removing metadata, garbled characters, and extra whitespace."""

    metadata_patterns = [
        r'%PDF-[\d\.]+',
        r'%����',
        r'/Author\([^)]*\)',
        r'/Creator\([^)]*\)',
        r'/Producer\([^)]*\)',
        r'/Title\([^)]*\)',
        r'/Subject\([^)]*\)',
        r'/Keywords\([^)]*\)',
        r'/CreationDate\([^)]*\)',
        r'/ModDate\([^)]*\)',
        r'\d+ \d+ obj',
        r'endobj',
        r'stream\s*.*?\s*endstream',
        r'<<[^>]*>>',
        r'\[http://[^\]]*\]',
        r'xref',
        r'trailer',
        r'startxref',
        r'%%EOF',
    ]

    cleaned = raw_text
    for pattern in metadata_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)

    replacements = {
        '�': '',
        '\x00': '',
        '\r\n': '\n',
        '\r': '\n',
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)

    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 3 and not line.isdigit():
            filtered_lines.append(line)

    cleaned = '\n'.join(filtered_lines).strip()
    return cleaned


def _demo():
    test_input = "%PDF-1.4\n%����\n/Author(John Doe)\n/Title(Sample Document)\n\nThis is the actual content of the document.\nIt should be preserved after cleaning.\n\nHere is another paragraph with meaningful text.\nThe quick brown fox jumps over the lazy dog.\n\n123\n\nMore content here that we want to keep.\n\nendobj\n%%EOF"
    print("=" * 80)
    print("🧹 PDF Text Cleaning Demo")
    print("=" * 80)
    cleaned = clean_pdf_text(test_input)
    print(cleaned or "(No readable content)")


if __name__ == "__main__":
    _demo()
