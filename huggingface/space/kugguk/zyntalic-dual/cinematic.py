"""Safe, deterministic presentation helpers for cinematic Zyntalic surfaces."""

from __future__ import annotations

import hashlib
import html

MORPH_GLYPHS = tuple("⟡◊⌁∿∆∴·⟢⟣ʒŋłćńęą쥂챿숦듼렺힞쀞")


def _glyph(character: str, index: int, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{index}:{character}".encode("utf-8")).digest()
    return MORPH_GLYPHS[int.from_bytes(digest[:2], "big") % len(MORPH_GLYPHS)]


def cinematic_surface(text: str, *, lineage: str = "neutral") -> str:
    """Render text as an accessible, escaped, deterministic character reveal."""
    value = str(text or "")
    spans: list[str] = []
    visible_index = 0
    for character in value:
        if character == "\n":
            spans.append("<br>")
            continue
        if character.isspace():
            spans.append("<span class=\"zy-space\"> </span>")
            continue
        glyph = html.escape(_glyph(character, visible_index, lineage))
        escaped = html.escape(character)
        # Let viewers read the mutation as a sequence instead of a flash. The
        # cap keeps long passages from delaying their final characters forever.
        delay = min(visible_index, 120) * 28
        spans.append(
            f'<span class="zy-morph-char" data-morph="{glyph}" '
            f'style="--zy-delay:{delay}ms">{escaped}</span>'
        )
        visible_index += 1
    label = html.escape(value, quote=True)
    return (
        f'<div class="zy-cinematic-surface zy-{html.escape(lineage)}" '
        f'role="text" aria-label="{label}">{"".join(spans)}</div>'
    )


def cinematic_pair(a: str, b: str) -> tuple[str, str]:
    """Render the two deterministic lineages with distinct stable glyph paths."""
    return (
        cinematic_surface(a, lineage="a"),
        cinematic_surface(b, lineage="b"),
    )
