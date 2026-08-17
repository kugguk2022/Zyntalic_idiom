"""Local-only voice pipeline for the deterministic Zyntalic edition.

The pipeline never uploads audio. It transcribes a reference performance,
translates the transcript through v0.1, then renders the synthetic line with a
zero-shot clone conditioned on the speaker's own reference clip.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from zyntalic.translator import translate_text

_CONTEXT_TAIL = re.compile(r"\s*⟦ctx:.*?⟧\s*$")


@lru_cache(maxsize=1)
def _transcriber():
    from faster_whisper import WhisperModel

    return WhisperModel("small", device="cpu", compute_type="int8")


@lru_cache(maxsize=1)
def _voice_model():
    import torch
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return ChatterboxTurboTTS.from_pretrained(device=device, nano=device == "cpu")


def transcribe_reference(audio_path: str) -> str:
    if not audio_path or not Path(audio_path).is_file():
        raise ValueError("Record or upload a reference voice clip first.")
    segments, _info = _transcriber().transcribe(audio_path, beam_size=5, vad_filter=True)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    if not transcript:
        raise ValueError("No speech was detected in the reference clip.")
    return transcript


def deterministic_surface(text: str) -> str:
    rows = translate_text(
        text,
        mirror_rate=0.25,
        engine="core",
        config={
            "register": "literary",
            "dialect": "standard",
            "evidentiality": "direct",
            "anchor_mode": "auto",
            "selected_anchors": [],
            "frame_a": "",
            "frame_b": "",
        },
    )
    # The written engine appends a machine-readable context sidecar. Preserve it
    # in normal text workflows, but never ask the voice renderer to pronounce it.
    surface = " ".join(
        _CONTEXT_TAIL.sub("", row.get("target", "")).strip() for row in rows
    ).strip()
    if not surface:
        raise RuntimeError("The deterministic engine returned no surface text.")
    return surface


def render_self_voice(audio_path: str, consent: bool):
    if not consent:
        raise ValueError("Confirm that the reference is your voice or licensed for this production.")
    transcript = transcribe_reference(audio_path)
    surface = deterministic_surface(transcript)
    model = _voice_model()
    waveform = model.generate(surface, audio_prompt_path=audio_path)
    samples = waveform.detach().cpu().float().squeeze().numpy()
    return transcript, surface, (model.sr, samples)
