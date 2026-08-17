"""Machine-only ASCI ↔ ASCI2 adversarial orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

from pydantic import BaseModel

from models import Adjudication, CrossDecodeReport, IntentState, LineageProposal, RunResult
from prompts import (
    ASCI2_DECODER_PROMPT,
    ASCI2_PROMPT,
    ASCI_DECODER_PROMPT,
    ASCI_PROMPT,
    INTENT_PROMPT,
    JUDGE_PROMPT,
    PROMPT_VERSION,
)

T = TypeVar("T", bound=BaseModel)
ENGINE_VERSION = "2.0.0-machine-duel"
MAX_SOURCE_CHARS = 2000
MAX_CONTEXT_CHARS = 2500


class ConfigurationError(RuntimeError):
    pass


class ModelRefusal(RuntimeError):
    pass


class ModelProviderError(RuntimeError):
    """A sanitized provider failure that is safe to show in the Space UI."""

    pass


def _compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bounded(value: str, limit: int, label: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    if len(text) > limit:
        raise ValueError(f"{label} exceeds {limit:,} characters")
    return text


def _usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    result = {}
    for public, field in (
        ("input_tokens", "input_tokens"),
        ("output_tokens", "output_tokens"),
        ("total_tokens", "total_tokens"),
    ):
        value = getattr(usage, field, None)
        if isinstance(value, int):
            result[public] = value
    return result


class OpenAITransport:
    def __init__(
        self,
        client: Any | None = None,
        lineage_model: str | None = None,
        judge_model: str | None = None,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_TOKEN")
        if client is None and not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY or OPENAI_TOKEN is not configured. "
                "Zyntalic Dual has no compiler fallback."
            )
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self.client = client
        self.lineage_model = lineage_model or os.getenv(
            "ZYNTALIC_LINEAGE_MODEL", "gpt-5.6-terra"
        )
        self.judge_model = judge_model or os.getenv(
            "ZYNTALIC_JUDGE_MODEL", self.lineage_model
        )
        self.safety_identifier = os.getenv("ZYNTALIC_SAFETY_IDENTIFIER", "").strip()
        self.traces: list[dict[str, object]] = []
        self._trace_lock = threading.Lock()

    def parse(
        self,
        schema: type[T],
        system: str,
        payload: dict[str, Any],
        *,
        stage: str,
        effort: str = "medium",
        model: str | None = None,
        max_output_tokens: int = 4000,
    ) -> T:
        selected_model = model or self.lineage_model
        kwargs: dict[str, Any] = {
            "model": selected_model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": _compact(payload)},
            ],
            "text_format": schema,
            "reasoning": {"effort": effort},
            "store": False,
            "max_output_tokens": max_output_tokens,
        }
        if self.safety_identifier:
            kwargs["safety_identifier"] = self.safety_identifier
        try:
            response = self.client.responses.parse(**kwargs)
        except Exception as exc:
            # Avoid leaking request details or credentials into the public UI,
            # while still giving the operator a useful stage/provider signal.
            if exc.__class__.__module__.startswith("openai"):
                error_code = str(getattr(exc, "code", "") or "").lower()
                error_text = str(exc).lower()
                if "insufficient_quota" in error_code or "insufficient_quota" in error_text:
                    raise ModelProviderError(
                        "The experiment funding limit has been reached. The Space owner "
                        "must review usage and manually approve a top-up before more duels run."
                    ) from exc
                raise ModelProviderError(
                    f"OpenAI request failed during {stage} ({type(exc).__name__}). "
                    "Check the Space logs, project balance, model access, and rate limits."
                ) from exc
            raise
        parsed = response.output_parsed
        if parsed is None:
            refusal = getattr(response, "refusal", None)
            raise ModelRefusal(str(refusal or f"{stage} returned no structured result."))
        trace = {
            "stage": stage,
            "model": getattr(response, "model", selected_model),
            "response_id": getattr(response, "id", "unavailable"),
            "effort": effort,
            "max_output_tokens": max_output_tokens,
            "usage": _usage(response),
        }
        with self._trace_lock:
            self.traces.append(trace)
        return parsed


def _lineage_payload(
    intent: IntentState,
    context: str,
    audience: str,
    pressure: str,
    noise: int,
) -> dict[str, Any]:
    return {
        "intent_contract": intent.model_dump(),
        "public_context": context,
        "audience": audience,
        "adversarial_pressure": pressure,
        "environmental_noise_percent": noise,
        "round_policy": "independent proposals; equal model, effort, and output budget",
    }


def _candidate_surfaces(asci: LineageProposal, asci2: LineageProposal) -> list[dict[str, str]]:
    return [
        {
            "candidate_id": candidate.candidate_id,
            "lineage": proposal.lineage,
            "surface": candidate.surface,
            "context_tail": candidate.context_tail,
        }
        for proposal in (asci, asci2)
        for candidate in proposal.candidates
    ]


def _assert_proposal(proposal: LineageProposal, lineage: str) -> None:
    if proposal.lineage != lineage:
        raise ValueError(f"Expected {lineage}, received {proposal.lineage}")
    if len(proposal.candidates) != 3:
        raise ValueError(f"{lineage} must return exactly three candidates")
    ids = [candidate.candidate_id for candidate in proposal.candidates]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{lineage} returned duplicate candidate IDs")
    if any(not c.surface.strip() or not c.context_tail.strip() for c in proposal.candidates):
        raise ValueError(f"{lineage} returned an empty surface or context tail")


def _assert_decoder(
    report: CrossDecodeReport,
    decoder: str,
    target: str,
    target_ids: set[str],
) -> None:
    if report.decoder_lineage != decoder or report.target_lineage != target:
        raise ValueError(f"Expected {decoder} to decode {target}")
    reading_ids = [item.candidate_id for item in report.readings]
    attack_ids = [item.candidate_id for item in report.attacks]
    if len(reading_ids) != len(set(reading_ids)) or set(reading_ids) != target_ids:
        raise ValueError(f"{decoder} did not decode every {target} candidate exactly once")
    if len(attack_ids) != len(set(attack_ids)) or set(attack_ids) != target_ids:
        raise ValueError(f"{decoder} did not attack every {target} candidate exactly once")


def _assert_evidence(
    surfaces: list[dict[str, str]],
    asci_decoder: CrossDecodeReport,
    asci2_decoder: CrossDecodeReport,
    adjudication: Adjudication,
) -> None:
    expected = {item["candidate_id"] for item in surfaces}
    if len(expected) != len(surfaces):
        raise ValueError("Candidate IDs must be unique across both lineages")
    asci_ids = {item["candidate_id"] for item in surfaces if item["lineage"] == "ASCI"}
    asci2_ids = {item["candidate_id"] for item in surfaces if item["lineage"] == "ASCI2"}
    _assert_decoder(asci_decoder, "ASCI", "ASCI2", asci2_ids)
    _assert_decoder(asci2_decoder, "ASCI2", "ASCI", asci_ids)
    scored = [item.candidate_id for item in adjudication.scores]
    probed = [item.candidate_id for item in adjudication.probes]
    if len(scored) != len(set(scored)) or set(scored) != expected:
        raise ValueError("Adjudicator scores do not cover every candidate exactly once")
    if len(probed) != len(set(probed)) or set(probed) != expected:
        raise ValueError("Adjudicator probes do not cover every candidate exactly once")
    if adjudication.selected_asci_id not in asci_ids:
        raise ValueError("Adjudicator selected an invalid ASCI candidate")
    if adjudication.selected_asci2_id not in asci2_ids:
        raise ValueError("Adjudicator selected an invalid ASCI2 candidate")


def build_receipt(
    result_without_receipt: dict[str, Any],
    manifest: dict[str, object] | str,
) -> dict[str, object]:
    if isinstance(manifest, str):
        manifest = {"lineage_model": manifest, "judge_model": manifest}
    material = _compact(result_without_receipt)
    return {
        "engine_version": ENGINE_VERSION,
        "prompt_version": PROMPT_VERSION,
        **manifest,
        "store": False,
        "run_digest": hashlib.sha256(material.encode("utf-8")).hexdigest(),
        "claim": "immutable round receipt, not deterministic model replay",
    }


def run_generation(
    source: str,
    context: str,
    audience: str,
    pressure: str,
    noise: int,
    *,
    transport: OpenAITransport | None = None,
) -> RunResult:
    source = _bounded(source, MAX_SOURCE_CHARS, "Utterance")
    context = _bounded(context, MAX_CONTEXT_CHARS, "Situation context")
    audience = _bounded(audience, 500, "Audience / relationship")
    pressure = _bounded(pressure, 500, "Adversarial pressure")
    noise = max(0, min(100, int(noise)))
    tx = transport or OpenAITransport()
    lineage_model = getattr(tx, "lineage_model", "injected-transport")
    judge_model = getattr(tx, "judge_model", lineage_model)

    intent = tx.parse(
        IntentState,
        INTENT_PROMPT,
        {
            "utterance": source,
            "situation_context": context,
            "audience": audience,
            "adversarial_pressure": pressure,
            "environmental_noise_percent": noise,
        },
        stage="intent",
        effort="medium",
        model=lineage_model,
        max_output_tokens=3000,
    )

    payload = _lineage_payload(intent, context, audience, pressure, noise)
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="zyntalic-encode") as pool:
        asci_future = pool.submit(
            tx.parse,
            LineageProposal,
            ASCI_PROMPT,
            payload,
            stage="asci_encode",
            effort="medium",
            model=lineage_model,
            max_output_tokens=4500,
        )
        asci2_future = pool.submit(
            tx.parse,
            LineageProposal,
            ASCI2_PROMPT,
            payload,
            stage="asci2_encode",
            effort="medium",
            model=lineage_model,
            max_output_tokens=4500,
        )
        asci, asci2 = asci_future.result(), asci2_future.result()

    _assert_proposal(asci, "ASCI")
    _assert_proposal(asci2, "ASCI2")
    surfaces = _candidate_surfaces(asci, asci2)
    public = {
        "public_context": context,
        "audience": audience,
        "adversarial_pressure": pressure,
        "environmental_noise_percent": noise,
    }
    asci_targets = [item for item in surfaces if item["lineage"] == "ASCI2"]
    asci2_targets = [item for item in surfaces if item["lineage"] == "ASCI"]

    # Isolation boundary: neither opponent decoder sees source or intent.
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="zyntalic-decode") as pool:
        asci_decode_future = pool.submit(
            tx.parse,
            CrossDecodeReport,
            ASCI_DECODER_PROMPT,
            {**public, "target_lineage": "ASCI2", "candidates": asci_targets},
            stage="asci_decodes_asci2",
            effort="medium",
            model=lineage_model,
            max_output_tokens=3500,
        )
        asci2_decode_future = pool.submit(
            tx.parse,
            CrossDecodeReport,
            ASCI2_DECODER_PROMPT,
            {**public, "target_lineage": "ASCI", "candidates": asci2_targets},
            stage="asci2_decodes_asci",
            effort="medium",
            model=lineage_model,
            max_output_tokens=3500,
        )
        asci_decoder = asci_decode_future.result()
        asci2_decoder = asci2_decode_future.result()

    adjudication = tx.parse(
        Adjudication,
        JUDGE_PROMPT,
        {
            "intent_contract": intent.model_dump(),
            "candidate_surfaces": surfaces,
            "asci_decoder_report": asci_decoder.model_dump(),
            "asci2_decoder_report": asci2_decoder.model_dump(),
            "adversarial_pressure": pressure,
            "environmental_noise_percent": noise,
        },
        stage="neutral_judge",
        effort="high",
        model=judge_model,
        max_output_tokens=4500,
    )
    _assert_evidence(surfaces, asci_decoder, asci2_decoder, adjudication)

    partial = {
        "intent": intent.model_dump(),
        "asci": asci.model_dump(),
        "asci2": asci2.model_dump(),
        "asci_decoder": asci_decoder.model_dump(),
        "asci2_decoder": asci2_decoder.model_dump(),
        "adjudication": adjudication.model_dump(),
    }
    manifest: dict[str, object] = {
        "lineage_model": lineage_model,
        "judge_model": judge_model,
        "lineage_effort": "medium",
        "judge_effort": "high",
        "equal_lineage_budget": True,
        "calls": sorted(getattr(tx, "traces", []), key=lambda item: str(item.get("stage"))),
    }
    return RunResult(**partial, receipt=build_receipt(partial, manifest))
