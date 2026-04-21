#!/usr/bin/env python3
"""Quick manual translation check."""

from zyntalic.translator import translate_text

TEST_DATA = [
    ("I love you", 0.2),
    ("The ancient philosopher wrote", 0.3),
    ("Beautiful morning", 0.1),
    ("Time flows", 0.2),
    ("Knowledge is power", 0.3),
]


def main():
    print("=" * 80)
    print("🌟 Zyntalic Translation Verification")
    print("=" * 80)

    for text, mirror_rate in TEST_DATA:
        result = translate_text(text, mirror_rate=mirror_rate, engine="core")[0]
        target = result["target"]

        if "⟦ctx:" in target:
            zyntalic_only = target.split("⟦ctx:")[0].strip()
            context = target.split("⟦ctx:")[1].split("⟧")[0] if "⟦ctx:" in target else ""
            han_part = [p for p in context.split(";") if "han=" in p]
            han_value = han_part[0].replace("han=", "").strip() if han_part else "N/A"
        else:
            zyntalic_only = target
            han_value = "N/A"

        has_hangul = any('\uac00' <= c <= '\ud7af' for c in zyntalic_only)
        has_polish = any(c in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ' for c in zyntalic_only)

        print(f"\n📝 English:  {text} (mirror_rate={mirror_rate})")
        print(f"🌀 Zyntalic: {zyntalic_only}")
        print(f"🔤 Context:  han={han_value}")
        print(f"   ✅ Hangul: {has_hangul}, Polish: {has_polish}")

    print("\n" + "=" * 80)
    print("✅ Quick check complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
