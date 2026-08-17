"""Hugging Face Space UI for the machine-only Zyntalic duel."""

from __future__ import annotations

import html
import difflib
import json
import threading
import time
from typing import Any

import gradio as gr
from zyntalic import __version__ as deterministic_engine_version
from zyntalic.core import ANCHORS
from zyntalic.translator import translate_text, warm_translation_pipeline

from cinematic import cinematic_pair, cinematic_surface
from engine import ConfigurationError, ModelProviderError, ModelRefusal, run_generation
from models import CrossDecodeReport, RunResult
from rate_limit import AccessDenied, SpendGate, SpendLimitReached
from theme import CSS, HERO

PRESSURES = [
    "Hostile paraphrase",
    "False contextual cue",
    "Role / authority spoofing",
    "Ambiguous social intent",
    "Dropped or corrupted signal",
    "Mixed pressure",
]
DETERMINISTIC_ENGINES = ["core", "transformer", "chiasmus", "reverse"]
REGISTERS = ["formal", "informal", "literary", "archaic", "technical"]
DIALECTS = ["standard", "northern", "southern", "coastal", "mountain"]
EVIDENTIALITIES = ["direct", "inferential", "hearsay", "assumptive"]
ANCHOR_MODES = ["auto", "manual", "neutral"]

warm_translation_pipeline()

_GATE: SpendGate | None = None
_GATE_LOCK = threading.Lock()


def _spend_gate() -> SpendGate:
    global _GATE
    with _GATE_LOCK:
        if _GATE is None:
            _GATE = SpendGate()
        return _GATE


def _e(value: Any) -> str:
    return html.escape(str(value or ""))


def _run_deterministic_variant(
    text: str,
    engine: str,
    mirror_rate: float,
    register: str,
    dialect: str,
    evidentiality: str,
    anchor_mode: str,
    selected_anchors: list[str],
) -> dict[str, Any]:
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
    return {
        "surface": "\n\n".join(row.get("target", "") for row in rows),
        "sidecar": rows[0].get("sidecar", {}) if rows else {},
        "elapsed_ms": (time.perf_counter() - started) * 1000,
    }


def _deterministic_diff(a: str, b: str) -> str:
    a_tokens, b_tokens = a.split(), b.split()
    matcher = difflib.SequenceMatcher(None, a_tokens, b_tokens)
    shared = sum(i2 - i1 for tag, i1, i2, _j1, _j2 in matcher.get_opcodes() if tag == "equal")
    total = max(len(a_tokens), len(b_tokens)) or 1
    return f"### {'Identical' if a == b else 'Different'}\n\nToken overlap: **{shared / total:.0%}** ({shared}/{total})"


def compare_deterministic(
    text: str,
    a_engine: str, a_mirror: float, a_register: str, a_dialect: str,
    a_evidentiality: str, a_anchor_mode: str, a_anchors: list[str],
    b_engine: str, b_mirror: float, b_register: str, b_dialect: str,
    b_evidentiality: str, b_anchor_mode: str, b_anchors: list[str],
) -> tuple[str, str, str, str, str, str, str]:
    if not (text or "").strip():
        return "", "", "", "", "Enter source text to compare.", "{}", "{}"
    a = _run_deterministic_variant(
        text, a_engine, a_mirror, a_register, a_dialect,
        a_evidentiality, a_anchor_mode, a_anchors,
    )
    b = _run_deterministic_variant(
        text, b_engine, b_mirror, b_register, b_dialect,
        b_evidentiality, b_anchor_mode, b_anchors,
    )
    a_repeat = _run_deterministic_variant(
        text, a_engine, a_mirror, a_register, a_dialect,
        a_evidentiality, a_anchor_mode, a_anchors,
    )
    verdict = _deterministic_diff(a["surface"], b["surface"])
    verdict += (
        f"\n\nA: {a['elapsed_ms']:.1f} ms · B: {b['elapsed_ms']:.1f} ms"
        f"\n\nDeterminism check: **{'passed' if a_repeat['surface'] == a['surface'] else 'failed'}**"
    )
    a_surface, b_surface = cinematic_pair(a["surface"], b["surface"])
    return (
        a_surface, b_surface, a["surface"], b["surface"], verdict,
        json.dumps(a["sidecar"], ensure_ascii=False, indent=2),
        json.dumps(b["sidecar"], ensure_ascii=False, indent=2),
    )


def _deterministic_controls(label: str, engine: str, mirror: float, register: str):
    gr.Markdown(f"#### Variant {label}")
    engine_in = gr.Dropdown(DETERMINISTIC_ENGINES, value=engine, label="Engine")
    mirror_in = gr.Slider(0, 1, value=mirror, step=.05, label="Mirror rate")
    register_in = gr.Dropdown(REGISTERS, value=register, label="Register")
    dialect_in = gr.Dropdown(DIALECTS, value="standard", label="Dialect")
    evidentiality_in = gr.Dropdown(EVIDENTIALITIES, value="direct", label="Evidentiality")
    anchor_mode_in = gr.Dropdown(ANCHOR_MODES, value="auto", label="Anchor mode")
    anchors_in = gr.Dropdown(sorted(ANCHORS), value=[], multiselect=True, label="Anchors")
    return [engine_in, mirror_in, register_in, dialect_in, evidentiality_in, anchor_mode_in, anchors_in]


def _candidate_card(result: RunResult, lineage: str) -> str:
    proposal = result.asci if lineage == "ASCI" else result.asci2
    card_class = "a" if lineage == "ASCI" else "b"
    channel = "CHANNEL A" if lineage == "ASCI" else "CHANNEL B"
    blocks = []
    for candidate in proposal.candidates:
        moves = " · ".join(
            f"{_e(move.token)} ← {_e(move.intent_unit)}" for move in candidate.token_moves[:4]
        )
        blocks.append(
            f"""<div class="zy-candidate">
              <div class="zy-id">{_e(candidate.candidate_id)}</div>
              <div class="zy-surface">{cinematic_surface(candidate.surface, lineage=card_class)}</div>
              <div class="zy-tail">context · {_e(candidate.context_tail)}</div>
              <div class="zy-strategy"><b>move:</b> {_e(candidate.strategy)}</div>
              <div class="zy-detail"><b>expected reading</b><span>{_e(candidate.expected_reading)}</span></div>
              <div class="zy-detail"><b>robustness</b><span>{_e(candidate.robustness_claim)}</span></div>
              <div class="zy-detail"><b>known failure</b><span>{_e(candidate.known_failure)}</span></div>
              <div class="zy-note">{moves}</div>
            </div>"""
        )
    return (
        f'<section class="zy-card {card_class}"><div class="zy-kicker">{channel}</div>'
        f'<h3>{lineage}</h3><div class="zy-thesis">{_e(proposal.lineage_thesis)}</div>'
        f'<div class="zy-adaptation"><b>competitive adaptation</b><br>{_e(proposal.competitive_adaptation)}</div>'
        + "".join(blocks)
        + "</section>"
    )


def _decoder_lane(report: CrossDecodeReport) -> str:
    attacks = {attack.candidate_id: attack for attack in report.attacks}
    blocks = []
    for reading in report.readings:
        attack = attacks.get(reading.candidate_id)
        attack_text = (
            f"attack: {_e(attack.perturbation)} → {_e(attack.likely_misreading)}"
            if attack
            else "attack unavailable"
        )
        blocks.append(
            f"""<div class="zy-reading"><div class="zy-id">{_e(reading.candidate_id)}</div>
            <b>{_e(reading.inferred_speech_act)}</b> · {_e(reading.inferred_goal)}
            <div class="zy-note">roles: {_e(' · '.join(reading.inferred_roles))}</div>
            <div class="zy-note">ambiguity: {_e(' · '.join(reading.ambiguity))}</div>
            <div class="zy-attack">{attack_text} · {'survives' if attack and attack.survives else 'fails'} · confidence {reading.confidence:.0%}</div></div>"""
        )
    return (
        f'<section class="zy-card"><h3>{_e(report.decoder_lineage)} decodes '
        f'{_e(report.target_lineage)}</h3><div class="zy-receiver">'
        + "".join(blocks)
        + "</div></section>"
    )


def _verdict_card(result: RunResult) -> str:
    scores = []
    for score in sorted(result.adjudication.scores, key=lambda item: item.composite, reverse=True):
        width = max(0, min(100, round(score.composite * 100)))
        scores.append(
            f'<div class="zy-score"><span>{_e(score.candidate_id)}</span>'
            f'<span class="zy-meter"><i style="width:{width}%"></i></span><b>{width}</b></div>'
        )
    preserved = "intent preserved" if result.adjudication.intent_preserved else "intent rejected"
    return f"""<section class="zy-verdict">
      <div class="zy-kicker">neutral judge · {_e(preserved)}</div>
      <h2>{_e(result.adjudication.winner)}</h2>
      <p>{_e(result.adjudication.verdict)}</p>
      {''.join(scores)}
      <div class="zy-note"><b>next machine mutation:</b> {_e(result.adjudication.next_mutation)}</div>
    </section>"""


def _error(exc: Exception):
    panel = f'<div class="zy-error"><b>Duel not started.</b><br>{_e(str(exc))}</div>'
    return {}, panel, panel, "", panel, {}


def _ring_loader() -> str:
    return """<section class="zy-ring-stage" aria-live="polite" aria-label="Machine duel compiling">
      <div class="zy-ring-grid"></div>
      <div class="zy-orbit outer"><span>ASCI</span></div>
      <div class="zy-orbit inner"><span>ASCI2</span></div>
      <div class="zy-ring-core"><b>COMPILING</b><small>intent → duel → cross-read → judge</small></div>
      <div class="zy-ring-status"><i></i> Two independent lineages are entering the ring</div>
    </section>"""


def _loading_state():
    ring = _ring_loader()
    waiting = '<div class="zy-empty zy-pulse">Waiting for the ring verdict…</div>'
    return {}, ring, ring, waiting, ring, {}


def execute(
    source: str,
    context: str,
    audience: str,
    pressure: str,
    noise: int,
    request: gr.Request,
):
    # A generator lets Gradio paint the arena before the slower hosted-model
    # stages begin. Without this first yield, the v1.1 tab appears frozen.
    yield _loading_state()
    try:
        session_id = getattr(request, "session_hash", "") or ""
        remaining = _spend_gate().consume(session_id)
        result = run_generation(source, context, audience, pressure, noise)
        result.receipt["spend_gate"] = remaining
        decode_html = (
            '<div class="zy-duel">'
            + _decoder_lane(result.asci_decoder)
            + _decoder_lane(result.asci2_decoder)
            + "</div>"
        )
        yield (
            result.intent.model_dump(mode="json"),
            _candidate_card(result, "ASCI"),
            _candidate_card(result, "ASCI2"),
            decode_html,
            _verdict_card(result),
            result.receipt,
        )
    except (
        AccessDenied,
        SpendLimitReached,
        ConfigurationError,
        ModelProviderError,
        ModelRefusal,
        ValueError,
        RuntimeError,
    ) as exc:
        yield _error(exc)


with gr.Blocks(title="Zyntalic Dual — Machine A/B", css=CSS) as demo:
    gr.HTML(HERO)
    with gr.Tabs():
        with gr.Tab("v1.1 · ASCI ↔ ASCI2"):
            gr.Markdown("**Experimental deep machine duel.** Public and rate-limited; the arena stays live while the round compiles.")
            source_in = gr.Textbox(
                label="Utterance",
                lines=2,
                value="Tell them the gate remains open, but only until the storm reaches us.",
            )
            with gr.Accordion("Round conditions", open=False):
                with gr.Row():
                    context_in = gr.Textbox(
                        label="Situation context",
                        lines=2,
                        value="A negotiator sends a final cooperative warning across an unreliable channel.",
                    )
                    audience_in = gr.Textbox(
                        label="Audience / relationship",
                        value="A cautious rival who may interpret softness as weakness",
                    )
                with gr.Row():
                    pressure_in = gr.Dropdown(PRESSURES, value="Mixed pressure", label="Adversarial pressure")
                    noise_in = gr.Slider(0, 80, value=25, step=5, label="Environmental noise %")
            run_btn = gr.Button("Start ASCI ↔ ASCI2 duel", variant="primary")
            gr.Markdown("Independent machine lineages · one neutral verdict · no human vote")

            gr.Markdown("## Round verdict")
            verdict_out = gr.HTML('<div class="zy-empty">Run a duel to reveal the machine verdict.</div>')
            gr.Markdown("## Machine proposals")
            with gr.Row():
                asci_out = gr.HTML()
                asci2_out = gr.HTML()
            gr.Markdown("## Blind cross-decoding and attacks")
            duel_out = gr.HTML()
            # Internal contract and provider manifest support orchestration and
            # auditing but are intentionally not exposed in the product UI.
            intent_out = gr.State()
            receipt_out = gr.State()

            inputs = [source_in, context_in, audience_in, pressure_in, noise_in]
            outputs = [intent_out, asci_out, asci2_out, duel_out, verdict_out, receipt_out]
            # Gradio 5 uses api_name=False to keep the spend-bearing action off the API.
            run_btn.click(execute, inputs=inputs, outputs=outputs, api_name=False)

        with gr.Tab("v0.1 · Deterministic A/B"):
            gr.Markdown(
                f"**Local deterministic engine `{deterministic_engine_version}`.** "
                "No hosted model, token spend, or sampling. Compare two configurations side by side."
            )
            deterministic_text = gr.Textbox(
                label="Source text", lines=2, value="I see the river at night."
            )
            deterministic_run = gr.Button("Compare deterministic variants", variant="primary")
            with gr.Row():
                with gr.Column():
                    deterministic_a_inputs = _deterministic_controls("A", "core", .3, "formal")
                with gr.Column():
                    deterministic_b_inputs = _deterministic_controls("B", "chiasmus", .8, "literary")
            deterministic_verdict = gr.Markdown("Run a comparison to see the reproducibility result.")
            with gr.Row():
                deterministic_a_out = gr.HTML(
                    '<div class="zy-output-shell a"><div class="zy-id">VARIANT A · CINEMATIC SURFACE</div>'
                    '<div class="zy-empty">Run the deterministic duel to reveal channel A.</div></div>'
                )
                deterministic_b_out = gr.HTML(
                    '<div class="zy-output-shell b"><div class="zy-id">VARIANT B · CINEMATIC SURFACE</div>'
                    '<div class="zy-empty">Run the deterministic duel to reveal channel B.</div></div>'
                )
            with gr.Accordion("Copy exact deterministic surfaces", open=False):
                with gr.Row():
                    deterministic_a_raw = gr.Textbox(
                        label="Variant A exact output", lines=4, show_copy_button=True,
                    )
                    deterministic_b_raw = gr.Textbox(
                        label="Variant B exact output", lines=4, show_copy_button=True,
                    )
            with gr.Accordion("Deterministic sidecars", open=False):
                with gr.Row():
                    deterministic_a_side = gr.Code(language="json", label="A sidecar")
                    deterministic_b_side = gr.Code(language="json", label="B sidecar")

            deterministic_inputs = [
                deterministic_text, *deterministic_a_inputs, *deterministic_b_inputs,
            ]
            deterministic_outputs = [
                deterministic_a_out, deterministic_b_out,
                deterministic_a_raw, deterministic_b_raw, deterministic_verdict,
                deterministic_a_side, deterministic_b_side,
            ]
            deterministic_run.click(
                compare_deterministic,
                inputs=deterministic_inputs,
                outputs=deterministic_outputs,
                api_name=False,
            )
            deterministic_text.submit(
                compare_deterministic,
                inputs=deterministic_inputs,
                outputs=deterministic_outputs,
                api_name=False,
            )
    gr.Markdown("Built by the Zyntalic team with Codex as a development teammate.")

demo.queue(default_concurrency_limit=1, max_size=4)

if __name__ == "__main__":
    demo.launch(ssr_mode=False)
