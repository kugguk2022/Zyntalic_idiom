#!/usr/bin/env python
"""Test the new output format showing source + translation"""

from zyntalic.translator import translate_text

# Test with a sample sentence
text = "The cat walks in the garden. I love poetry and art."

print("=" * 70)
print("TESTING NEW OUTPUT FORMAT")
print("=" * 70)
print(f"\nInput: {text}\n")

result = translate_text(text, mirror_rate=0.3, engine="core")

print("\nTranslation Results:")
print("-" * 70)

for i, row in enumerate(result, 1):
    print(f"\nSentence {i}:")
    print(f"  [Source]: {row['source']}")
    print(f"  [Target]: {row['target']}")
    print(f"  [Engine]: {row['engine']}")
    if row.get('anchors'):
        anchors_str = ", ".join([f"{a[0]}" for a in row['anchors'][:3]])
        print(f"  [Anchors]: {anchors_str}")

print("\n" + "=" * 70)
print("Frontend will show:")
print("=" * 70)
for row in result:
    print(f"\n[{row['source']}]")
    print(f"→ {row['target']}")

print("\n")
