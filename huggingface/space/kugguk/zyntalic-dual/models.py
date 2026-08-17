"""Typed contracts for the Zyntalic Dual model loop."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SemanticRole(StrictModel):
    role: str
    value: str
    certainty: float


class IntentState(StrictModel):
    literal_meaning: str
    communicative_goal: str
    speech_act: str
    audience_model: str
    relationship_pressure: str
    semantic_roles: list[SemanticRole]
    required_implications: list[str]
    forbidden_misreadings: list[str]
    productive_ambiguities: list[str]
    environmental_pressures: list[str]
    risk_if_misread: str
    intent_signature: str


class TokenMove(StrictModel):
    token: str
    intent_unit: str
    pragmatic_function: str
    strategic_reason: str
    substitution_trigger: str


class StrategicCandidate(StrictModel):
    candidate_id: str
    surface: str
    context_tail: str
    strategy: str
    token_moves: list[TokenMove]
    expected_reading: str
    robustness_claim: str
    known_failure: str


class LineageProposal(StrictModel):
    lineage: Literal["ASCI", "ASCI2"]
    lineage_thesis: str
    competitive_adaptation: str
    candidates: list[StrategicCandidate]


class ReceiverReading(StrictModel):
    candidate_id: str
    inferred_goal: str
    inferred_speech_act: str
    inferred_roles: list[str]
    inferred_implications: list[str]
    ambiguity: list[str]
    noise_reading: str
    confidence: float


class AdversarialProbe(StrictModel):
    candidate_id: str
    perturbation: str
    intended_attack: str
    likely_misreading: str
    survives: bool
    explanation: str


class CrossDecodeReport(StrictModel):
    decoder_lineage: Literal["ASCI", "ASCI2"]
    target_lineage: Literal["ASCI", "ASCI2"]
    method: str
    readings: list[ReceiverReading]
    attacks: list[AdversarialProbe]


class CandidateScore(StrictModel):
    candidate_id: str
    intent_match: float
    pragmatic_match: float
    noise_robustness: float
    ambiguity_control: float
    human_legibility: float
    strategic_novelty: float
    composite: float
    decisive_reason: str


class Adjudication(StrictModel):
    scores: list[CandidateScore]
    probes: list[AdversarialProbe]
    selected_asci_id: str
    selected_asci2_id: str
    winner: Literal["ASCI", "ASCI2", "DRAW", "NEITHER"]
    verdict: str
    intent_preserved: bool
    next_mutation: str


class RunResult(StrictModel):
    intent: IntentState
    asci: LineageProposal
    asci2: LineageProposal
    asci_decoder: CrossDecodeReport
    asci2_decoder: CrossDecodeReport
    adjudication: Adjudication
    receipt: dict[str, object]
