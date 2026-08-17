from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import _loading_state, _ring_loader
from cinematic import cinematic_pair, cinematic_surface
from engine import ConfigurationError, OpenAITransport, build_receipt, run_generation
from models import (
    Adjudication,
    AdversarialProbe,
    CandidateScore,
    CrossDecodeReport,
    IntentState,
    LineageProposal,
    ReceiverReading,
    SemanticRole,
    StrategicCandidate,
    TokenMove,
)
from prompts import ASCI2_DECODER_PROMPT, ASCI2_PROMPT, ASCI_DECODER_PROMPT, ASCI_PROMPT
from rate_limit import AccessDeniedError, SpendGate, SpendLimitReachedError


def candidate(lineage: str, index: int) -> StrategicCandidate:
    return StrategicCandidate(
        candidate_id=f"{lineage.lower()}-{index}",
        surface=f"žar{index} ven{index} drumi{index}",
        context_tail=f"맥락-{index}",
        strategy="intent-conditioned role rotation",
        token_moves=[
            TokenMove(
                token=f"žar{index}",
                intent_unit="cooperative warning",
                pragmatic_function="bounded offer",
                strategic_reason="survives role ambiguity",
                substitution_trigger="audience distrust",
            )
        ],
        expected_reading="a bounded cooperative warning",
        robustness_claim="role survives one dropped boundary",
        known_failure="tail loss weakens urgency",
    )


def reading(candidate_id: str) -> ReceiverReading:
    return ReceiverReading(
        candidate_id=candidate_id,
        inferred_goal="bounded warning",
        inferred_speech_act="warning",
        inferred_roles=["speaker", "recipient"],
        inferred_implications=["time limit"],
        ambiguity=["exact deadline"],
        noise_reading="warning remains",
        confidence=0.8,
    )


def attack(candidate_id: str) -> AdversarialProbe:
    return AdversarialProbe(
        candidate_id=candidate_id,
        perturbation="drop final marker",
        intended_attack="erase urgency",
        likely_misreading="soft invitation",
        survives=True,
        explanation="role morphology remains",
    )


class FakeTransport:
    lineage_model = "fake-equal-model"
    judge_model = "fake-judge-model"
    traces = []

    def __init__(self) -> None:
        self.calls = []

    def parse(
        self,
        schema,
        system,
        payload,
        *,
        stage,
        effort="medium",
        model=None,
        max_output_tokens=4000,
    ):
        self.calls.append(
            {
                "schema": schema,
                "system": system,
                "payload": payload,
                "stage": stage,
                "effort": effort,
                "model": model,
                "max_output_tokens": max_output_tokens,
            }
        )
        if schema is IntentState:
            return IntentState(
                literal_meaning="the route is briefly available",
                communicative_goal="warn while preserving cooperation",
                speech_act="bounded offer and warning",
                audience_model="distrustful rival",
                relationship_pressure="softness may be misread",
                semantic_roles=[SemanticRole(role="speaker", value="negotiator", certainty=1.0)],
                required_implications=["deadline is real"],
                forbidden_misreadings=["unconditional access"],
                productive_ambiguities=["degree of urgency"],
                environmental_pressures=["signal loss"],
                risk_if_misread="missed deadline",
                intent_signature="bounded-cooperative-warning",
            )
        if schema is LineageProposal:
            lineage = "ASCI2" if "You are ASCI2" in system else "ASCI"
            return LineageProposal(
                lineage=lineage,
                lineage_thesis=f"{lineage} thesis",
                competitive_adaptation="independent opponent-aware strategy",
                candidates=[candidate(lineage, index) for index in range(1, 4)],
            )
        if schema is CrossDecodeReport:
            decoder = "ASCI2" if "ASCI2's decoder-adversary" in system else "ASCI"
            target = payload["target_lineage"]
            ids = [item["candidate_id"] for item in payload["candidates"]]
            return CrossDecodeReport(
                decoder_lineage=decoder,
                target_lineage=target,
                method="opponent-only pragmatic reconstruction",
                readings=[reading(value) for value in ids],
                attacks=[attack(value) for value in ids],
            )
        if schema is Adjudication:
            ids = [item["candidate_id"] for item in payload["candidate_surfaces"]]
            return Adjudication(
                scores=[
                    CandidateScore(
                        candidate_id=value,
                        intent_match=0.8,
                        pragmatic_match=0.8,
                        noise_robustness=0.7,
                        ambiguity_control=0.7,
                        human_legibility=0.6,
                        strategic_novelty=0.7,
                        composite=0.75,
                        decisive_reason="opponent decoder preserves warning",
                    )
                    for value in ids
                ],
                probes=[attack(value) for value in ids],
                selected_asci_id="asci-1",
                selected_asci2_id="asci2-1",
                winner="DRAW",
                verdict="both preserve the bounded warning",
                intent_preserved=True,
                next_mutation="differentiate urgency encoding",
            )
        raise AssertionError(f"Unexpected schema: {schema}")


class EngineTests(unittest.TestCase):
    def test_cinematic_surface_is_escaped_stable_and_accessible(self):
        source = '<script>alert("x")</script> żółć 한'
        first = cinematic_surface(source, lineage="a")
        self.assertEqual(first, cinematic_surface(source, lineage="a"))
        self.assertNotIn("<script>", first)
        self.assertIn("&lt;", first)
        self.assertIn('aria-label="&lt;script&gt;alert(&quot;x&quot;)', first)
        self.assertIn('class="zy-morph-char"', first)

    def test_cinematic_pair_keeps_distinct_lineage_paths(self):
        a, b = cinematic_pair("same", "same")
        self.assertNotEqual(a, b)
        self.assertIn("zy-a", a)
        self.assertIn("zy-b", b)

    def test_v11_loading_state_exposes_the_ring_before_models_finish(self):
        ring = _ring_loader()
        self.assertIn("zy-ring-stage", ring)
        self.assertIn("ASCI2", ring)
        state = _loading_state()
        self.assertEqual(len(state), 6)
        self.assertEqual(state[1], ring)
        self.assertEqual(state[4], ring)

    def test_no_api_key_has_no_compiler_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "no compiler fallback"):
                OpenAITransport()

    def test_machine_duel_isolation_and_equal_budgets(self):
        secret_source = "UNIQUE_SOURCE_PHRASE_7f31"
        tx = FakeTransport()
        result = run_generation(
            secret_source,
            "Synthetic negotiation across a noisy channel",
            "Distrustful rival",
            "Mixed pressure",
            25,
            transport=tx,
        )
        self.assertEqual(result.adjudication.winner, "DRAW")
        decoder_calls = [call for call in tx.calls if call["schema"] is CrossDecodeReport]
        self.assertEqual(len(decoder_calls), 2)
        for call in decoder_calls:
            material = str(call["payload"])
            self.assertNotIn(secret_source, material)
            self.assertNotIn("intent_contract", call["payload"])
            self.assertEqual(len(call["payload"]["candidates"]), 3)
        encode_calls = [call for call in tx.calls if call["schema"] is LineageProposal]
        self.assertEqual(len(encode_calls), 2)
        self.assertEqual(
            {(call["model"], call["effort"], call["max_output_tokens"]) for call in encode_calls},
            {("fake-equal-model", "medium", 4500)},
        )
        judge_call = next(call for call in tx.calls if call["schema"] is Adjudication)
        self.assertIn("asci_decoder_report", judge_call["payload"])
        self.assertIn("asci2_decoder_report", judge_call["payload"])

    def test_receipt_is_content_bound_and_not_replay_claim(self):
        first = build_receipt({"a": 1, "b": 2}, "model-a")
        same = build_receipt({"b": 2, "a": 1}, "model-a")
        changed = build_receipt({"a": 2, "b": 1}, "model-a")
        self.assertEqual(first["run_digest"], same["run_digest"])
        self.assertNotEqual(first["run_digest"], changed["run_digest"])
        self.assertIn("not deterministic", first["claim"])

    def test_prompts_require_cross_adversarial_strategy(self):
        self.assertIn("Do not use a fixed lexicon", ASCI_PROMPT)
        self.assertIn("context may rotate a token", ASCI2_PROMPT)
        self.assertIn("do NOT receive the source utterance", ASCI_DECODER_PROMPT)
        self.assertIn("do NOT receive the source utterance", ASCI2_DECODER_PROMPT)


class SpendGateTests(unittest.TestCase):
    def test_public_access_and_both_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "limits.sqlite3")
            env = {
                "ZYNTALIC_DAILY_RUN_CAP": "2",
                "ZYNTALIC_SESSION_RUN_CAP": "1",
            }
            with patch.dict(os.environ, env, clear=True):
                gate = SpendGate(db_path)
                self.assertEqual(gate.consume("session-a")["session_remaining"], 0)
                with self.assertRaises(SpendLimitReachedError):
                    gate.consume("session-a")
                self.assertEqual(gate.consume("session-b")["daily_remaining"], 0)
                with self.assertRaises(SpendLimitReachedError):
                    gate.consume("session-c")

    def test_missing_browser_session_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as tmp:
            gate = SpendGate(str(Path(tmp) / "limits.sqlite3"))
            with self.assertRaisesRegex(AccessDeniedError, "browser session"):
                gate.consume("")


if __name__ == "__main__":
    unittest.main()
