#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test PDF text cleaning functionality."""

import re

def clean_pdf_text(raw_text: str) -> str:
    """Clean extracted PDF text by removing metadata, garbled characters, and extra whitespace."""
    
    # Remove common PDF metadata patterns
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
    
    # Remove multiple spaces and normalize whitespace
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    
    # Remove lines that are just numbers or single characters (often page numbers)
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        line = line.strip()
        # Keep line if it has substantial content
        if len(line) > 3 and not line.isdigit():
            filtered_lines.append(line)
    
    cleaned = '\n'.join(filtered_lines)
    
    # Final cleanup: remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


# Test with the problematic PDF text from the screenshot
test_input = """%PDF-1.4
%����
1 0 obj<</Author(�� E � a d e Q u e i r � s , R a m a l h o
O r t i g � o & E � a d e
Q u e i r � s)/CreationDate(D:2023
030814 0519+00'00')/Creator(�� c a
l i b r e \( 5 . 3 1 . 1 \)
[ h t t p : / / c a l i b r e - e b
o o k . c o m ])/ModDate(D:20230308140519+00'00')/Producer(�� c a l i b
r e \( 5 . 3 1 . 1 \)
[ h t t p : / / c a l i b r e - e b
o o k . c o m ])/Title(�� O
M i s t � r i o d a
E s t r a d a d e S i n t r a)>>
endobj"""

print("=" * 80)
print("🧹 PDF Text Cleaning Test")
print("=" * 80)

print("\n📄 Original text (first 200 chars):")
print(test_input[:200])

cleaned = clean_pdf_text(test_input)

print("\n✨ Cleaned text:")
print(cleaned if cleaned else "(No readable content)")

print("\n" + "=" * 80)

# Test with some actual content mixed with metadata
test_with_content = """%PDF-1.4
%����
/Author(John Doe)
/Title(Sample Document)

This is the actual content of the document.
It should be preserved after cleaning.

Here is another paragraph with meaningful text.
The quick brown fox jumps over the lazy dog.

123

More content here that we want to keep.

endobj
%%EOF"""

print("\n📄 Test with real content:")
cleaned2 = clean_pdf_text(test_with_content)
print(cleaned2)

print("\n" + "=" * 80)
print("✅ PDF cleaning test complete!")
