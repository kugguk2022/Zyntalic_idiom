"""Gradio demo for the Zyntalic deterministic synthetic-language engine.

Runs on a free CPU Space: the core engine is pure NumPy with no hosted model.
"""

from __future__ import annotations

import json

import gradio as gr

from zyntalic import __version__
from zyntalic.core import ANCHORS
from zyntalic.translator import translate_text, warm_translation_pipeline

# Engines that are meaningful in a demo. "test_suite" is omitted: it returns the
# same surface as "core" and only adds internal validation metadata.
ENGINES = ["core", "transformer", "chiasmus", "reverse"]
REGISTERS = ["formal", "informal", "literary", "archaic", "technical"]
DIALECTS = ["standard", "northern", "southern", "coastal", "mountain"]
EVIDENTIALITIES = ["direct", "inferential", "hearsay", "assumptive"]
ANCHOR_MODES = ["auto", "manual", "neutral"]

warm_translation_pipeline()


def translate(
    text: str,
    engine: str,
    mirror_rate: float,
    register: str,
    dialect: str,
    evidentiality: str,
    anchor_mode: str,
    selected_anchors: list[str],
) -> tuple[str, str, str]:
    """Return the Zyntalic surface, the anchor table, and the full sidecar JSON."""
    if not (text or "").strip():
        return "", "", "{}"

    config = {
        "register": register,
        "dialect": dialect,
        "evidentiality": evidentiality,
        "anchor_mode": anchor_mode,
        "selected_anchors": list(selected_anchors or []),
        "frame_a": "",
        "frame_b": "",
    }
    rows = translate_text(text, mirror_rate=mirror_rate, engine=engine, config=config)

    surface = "\n\n".join(row.get("target", "") for row in rows)

    sidecar = rows[0].get("sidecar", {}) if rows else {}
    weights = sidecar.get("anchor_weights", []) or []
    if weights:
        anchor_lines = "\n".join(
            f"- **{entry.get('name', '?').replace('_', ' ')}** — {entry.get('weight', 0.0):.3f}"
            for entry in weights
        )
    else:
        anchor_lines = "_No anchors applied (neutral mode)._"

    return surface, anchor_lines, json.dumps(sidecar, ensure_ascii=False, indent=2)


with gr.Blocks(title="Zyntalic", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        f"""
        # Zyntalic

        A **deterministic** synthetic-language engine. The same input and settings
        always produce the same output — there is no sampling and no hosted model.

        Source text is mapped to a constructed surface using seeded word
        generation, literary anchor priors, mixed Hangul/Latin forms, and
        Subject–Object–Verb–Context ordering. Each result ends with a
        machine-readable `⟦ctx: ...⟧` trace.

        Engine version `{__version__}` · [GitHub](https://github.com/kugguk2022/Zyntalic_idiom)
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            text_in = gr.Textbox(
                label="Source text",
                placeholder="I see the river at night.",
                lines=5,
                value="I see the river at night.",
            )
            run = gr.Button("Translate", variant="primary")
            surface_out = gr.Textbox(label="Zyntalic surface", lines=5, show_copy_button=True)

        with gr.Column(scale=2):
            engine_in = gr.Dropdown(ENGINES, value="core", label="Engine")
            mirror_in = gr.Slider(
                0.0,
                1.0,
                value=0.3,
                step=0.05,
                label="Mirror rate",
                info="Lower values produce more Zyntalic vocabulary.",
            )
            register_in = gr.Dropdown(REGISTERS, value="formal", label="Register")
            dialect_in = gr.Dropdown(DIALECTS, value="standard", label="Dialect")
            evidentiality_in = gr.Dropdown(
                EVIDENTIALITIES, value="direct", label="Evidentiality"
            )
            anchor_mode_in = gr.Dropdown(
                ANCHOR_MODES,
                value="auto",
                label="Anchor mode",
                info="'manual' uses only the anchors you select below.",
            )
            anchors_in = gr.Dropdown(
                sorted(ANCHORS),
                value=[],
                multiselect=True,
                label="Anchors (manual mode)",
            )

    with gr.Row():
        anchors_out = gr.Markdown(label="Anchor weights")
    with gr.Accordion("Full sidecar metadata", open=False):
        sidecar_out = gr.Code(language="json", label="sidecar")

    inputs = [
        text_in,
        engine_in,
        mirror_in,
        register_in,
        dialect_in,
        evidentiality_in,
        anchor_mode_in,
        anchors_in,
    ]
    outputs = [surface_out, anchors_out, sidecar_out]

    run.click(translate, inputs=inputs, outputs=outputs)
    text_in.submit(translate, inputs=inputs, outputs=outputs)

    gr.Examples(
        examples=[
            ["I see the river at night.", "core", 0.3],
            ["The wind carries the old song.", "core", 0.0],
            ["War and peace walk together.", "chiasmus", 0.5],
            ["Knowledge grows in silence.", "core", 0.8],
        ],
        inputs=[text_in, engine_in, mirror_in],
    )

if __name__ == "__main__":
    demo.launch()
