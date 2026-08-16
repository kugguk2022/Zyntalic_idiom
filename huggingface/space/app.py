"""Gradio A/B demo for the Zyntalic deterministic synthetic-language engine.

Runs on a free CPU Space: the core engine is pure NumPy with no hosted model.

Because generation is deterministic, any difference between variant A and
variant B is caused by the settings alone. There is no sampling noise to
average out, so a single run of each side is a complete comparison.
"""

from __future__ import annotations

import difflib
import json
import time

import gradio as gr

from zyntalic import __version__
from zyntalic.core import ANCHORS
from zyntalic.translator import translate_text, warm_translation_pipeline

# Engines meaningful in a demo. "test_suite" is omitted: it returns the same
# surface as "core" and only adds internal validation metadata.
ENGINES = ["core", "transformer", "chiasmus", "reverse"]
REGISTERS = ["formal", "informal", "literary", "archaic", "technical"]
DIALECTS = ["standard", "northern", "southern", "coastal", "mountain"]
EVIDENTIALITIES = ["direct", "inferential", "hearsay", "assumptive"]
ANCHOR_MODES = ["auto", "manual", "neutral"]

warm_translation_pipeline()


def _run_variant(
    text: str,
    engine: str,
    mirror_rate: float,
    register: str,
    dialect: str,
    evidentiality: str,
    anchor_mode: str,
    selected_anchors: list[str],
) -> dict:
    """Translate once and report the surface, timing, and sidecar."""
    config = {
        "register": register,
        "dialect": dialect,
        "evidentiality": evidentiality,
        "anchor_mode": anchor_mode,
        "selected_anchors": list(selected_anchors or []),
        "frame_a": "",
        "frame_b": "",
    }
    started = time.perf_counter()
    rows = translate_text(text, mirror_rate=mirror_rate, engine=engine, config=config)
    elapsed_ms = (time.perf_counter() - started) * 1000

    return {
        "surface": "\n\n".join(row.get("target", "") for row in rows),
        "sidecar": rows[0].get("sidecar", {}) if rows else {},
        "elapsed_ms": elapsed_ms,
    }


def _anchor_summary(sidecar: dict) -> str:
    weights = sidecar.get("anchor_weights", []) or []
    if not weights:
        return "_No anchors applied._"
    return " · ".join(
        f"{entry.get('name', '?').replace('_', ' ')} {entry.get('weight', 0.0):.2f}"
        for entry in weights[:4]
    )


def _diff_markdown(a: str, b: str) -> str:
    """Word-level diff between the two surfaces, rendered as markdown."""
    a_tokens, b_tokens = a.split(), b.split()
    matcher = difflib.SequenceMatcher(None, a_tokens, b_tokens)

    only_a, only_b, shared = [], [], 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            shared += i2 - i1
        else:
            only_a.extend(a_tokens[i1:i2])
            only_b.extend(b_tokens[j1:j2])

    total = max(len(a_tokens), len(b_tokens)) or 1
    overlap = shared / total

    lines = [f"**Token overlap: {overlap:.0%}** ({shared} shared of {total})", ""]
    if only_a:
        lines.append("**Only in A:** " + " ".join(f"`{tok}`" for tok in only_a[:24]))
    if only_b:
        lines.append("**Only in B:** " + " ".join(f"`{tok}`" for tok in only_b[:24]))
    return "\n\n".join(lines)


def compare(
    text: str,
    a_engine: str, a_mirror: float, a_register: str, a_dialect: str,
    a_evidentiality: str, a_anchor_mode: str, a_anchors: list[str],
    b_engine: str, b_mirror: float, b_register: str, b_dialect: str,
    b_evidentiality: str, b_anchor_mode: str, b_anchors: list[str],
) -> tuple[str, str, str, str, str, str]:
    """Run both variants and report surfaces, verdict, diff, and sidecars."""
    if not (text or "").strip():
        return "", "", "_Enter source text to compare._", "", "{}", "{}"

    a = _run_variant(
        text, a_engine, a_mirror, a_register, a_dialect,
        a_evidentiality, a_anchor_mode, a_anchors,
    )
    b = _run_variant(
        text, b_engine, b_mirror, b_register, b_dialect,
        b_evidentiality, b_anchor_mode, b_anchors,
    )

    # Determinism check: re-run A and confirm it reproduces exactly.
    a_repeat = _run_variant(
        text, a_engine, a_mirror, a_register, a_dialect,
        a_evidentiality, a_anchor_mode, a_anchors,
    )
    stable = a_repeat["surface"] == a["surface"]

    identical = a["surface"] == b["surface"]
    if identical:
        verdict = (
            "### ⟦ Identical ⟧\n\n"
            "Both variants produced exactly the same surface. These settings do "
            "not affect the output for this input."
        )
    else:
        verdict = "### ⟦ Different ⟧\n\n" + _diff_markdown(a["surface"], b["surface"])

    verdict += (
        f"\n\n---\n\n**A** {a['elapsed_ms']:.1f} ms · {_anchor_summary(a['sidecar'])}"
        f"\n\n**B** {b['elapsed_ms']:.1f} ms · {_anchor_summary(b['sidecar'])}"
    )
    verdict += (
        "\n\n**Determinism check:** "
        + ("A reproduced exactly on re-run. ✓" if stable else "A did not reproduce — please report this. ✗")
    )

    return (
        a["surface"],
        b["surface"],
        verdict,
        "",
        json.dumps(a["sidecar"], ensure_ascii=False, indent=2),
        json.dumps(b["sidecar"], ensure_ascii=False, indent=2),
    )


def _variant_controls(label: str, engine: str, mirror: float, register: str):
    """Build one variant's control column and return its components."""
    gr.Markdown(f"#### Variant {label}")
    engine_in = gr.Dropdown(ENGINES, value=engine, label="Engine")
    mirror_in = gr.Slider(
        0.0, 1.0, value=mirror, step=0.05,
        label="Mirror rate",
        info="Lower values produce more Zyntalic vocabulary.",
    )
    register_in = gr.Dropdown(REGISTERS, value=register, label="Register")
    dialect_in = gr.Dropdown(DIALECTS, value="standard", label="Dialect")
    evidentiality_in = gr.Dropdown(EVIDENTIALITIES, value="direct", label="Evidentiality")
    anchor_mode_in = gr.Dropdown(
        ANCHOR_MODES, value="auto", label="Anchor mode",
        info="'manual' uses only the anchors selected below.",
    )
    anchors_in = gr.Dropdown(
        sorted(ANCHORS), value=[], multiselect=True, label="Anchors (manual mode)",
    )
    return [
        engine_in, mirror_in, register_in, dialect_in,
        evidentiality_in, anchor_mode_in, anchors_in,
    ]


with gr.Blocks(title="Zyntalic A/B", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        f"""
        # Zyntalic — A/B comparison

        A **deterministic** synthetic-language engine. The same input and settings
        always produce the same output — there is no sampling and no hosted model.

        Because of that, this page can compare two configurations honestly: run the
        same source text through both, and every difference you see is caused by the
        settings, not by chance. Each comparison also re-runs variant A to prove it
        reproduces exactly.

        Engine version `{__version__}` · [GitHub](https://github.com/kugguk2022/Zyntalic_idiom)
        """
    )

    text_in = gr.Textbox(
        label="Source text",
        placeholder="I see the river at night.",
        lines=3,
        value="I see the river at night.",
    )
    run = gr.Button("Compare A and B", variant="primary")

    with gr.Row():
        with gr.Column():
            a_controls = _variant_controls("A", "core", 0.3, "formal")
        with gr.Column():
            b_controls = _variant_controls("B", "chiasmus", 0.8, "literary")

    with gr.Row():
        with gr.Column():
            a_out = gr.Textbox(label="Variant A output", lines=5, show_copy_button=True)
        with gr.Column():
            b_out = gr.Textbox(label="Variant B output", lines=5, show_copy_button=True)

    verdict_out = gr.Markdown()
    _spacer = gr.Markdown(visible=False)

    with gr.Accordion("Sidecar metadata", open=False):
        with gr.Row():
            a_side = gr.Code(language="json", label="A sidecar")
            b_side = gr.Code(language="json", label="B sidecar")

    inputs = [text_in, *a_controls, *b_controls]
    outputs = [a_out, b_out, verdict_out, _spacer, a_side, b_side]

    run.click(compare, inputs=inputs, outputs=outputs)
    text_in.submit(compare, inputs=inputs, outputs=outputs)

    gr.Markdown(
        "**Try:** identical settings on both sides (verify they match exactly) · "
        "`core` vs `chiasmus` · mirror rate `0.0` vs `1.0` · "
        "manual anchors `Homer_Odyssey` vs `Laozi_TaoTeChing`."
    )

if __name__ == "__main__":
    demo.launch()
