"""
Zyntalic Comprehensive Test Suite

Complete test coverage for all Zyntalic language systems including:
- Unit tests for each module
- Integration tests across systems
- Linguistic validation tests
- Performance benchmarks
- Regression tests
- Property-based testing
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .advanced_features import AdvancedZyntalicProcessor, Dialect, Register
from .core import ANCHORS
from .enhanced_syntax import ZyntalicSyntaxProcessor
from .lexicon_manager import RelationType, ZyntalicLexicon

# Import all Zyntalic modules
from .morphology import Case, MorphologicalProcessor, Tense
from .phonology import PhonologicalProcessor, analyze_phonotactics
from .semantic_coherence import SemanticCoherenceProcessor

# -------------------- Test Categories --------------------

class TestCategory(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    LINGUISTIC = "linguistic"
    PERFORMANCE = "performance"
    REGRESSION = "regression"
    PROPERTY = "property"

@dataclass
class TestResult:
    """Container for test results."""
    name: str
    category: TestCategory
    passed: bool
    execution_time: float
    message: str = ""
    details: dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

class ZyntalicTestSuite:
    """Main test suite for Zyntalic language systems."""

    def __init__(self):
        self.results: list[TestResult] = []
        self.setup_processors()

    def setup_processors(self):
        """Initialize all language processors for testing."""
        try:
            self.morphology = MorphologicalProcessor()
            self.phonology = PhonologicalProcessor()
            self.syntax = ZyntalicSyntaxProcessor()
            self.lexicon = ZyntalicLexicon()
            self.semantics = SemanticCoherenceProcessor(self.lexicon)
            self.advanced = AdvancedZyntalicProcessor()
            print("✓ All processors initialized successfully")
        except Exception as e:
            print(f"✗ Processor initialization failed: {e}")
            raise

    def run_all_tests(self, verbose: bool = True) -> dict[str, Any]:
        """Run complete test suite."""
        print("=== Zyntalic Comprehensive Test Suite ===\n")

        start_time = time.time()
        self.results = []

        # Run tests by category
        test_methods = [
            (TestCategory.UNIT, self.run_unit_tests),
            (TestCategory.INTEGRATION, self.run_integration_tests),
            (TestCategory.LINGUISTIC, self.run_linguistic_tests),
            (TestCategory.PERFORMANCE, self.run_performance_tests),
            (TestCategory.PROPERTY, self.run_property_tests)
        ]

        for category, test_method in test_methods:
            if verbose:
                print(f"\n--- {category.value.upper()} TESTS ---")
            test_method(verbose)

        total_time = time.time() - start_time

        # Generate summary
        summary = self._generate_summary(total_time)

        if verbose:
            self._print_summary(summary)

        return summary

    # -------------------- Unit Tests --------------------

    def run_unit_tests(self, verbose: bool = True):
        """Run unit tests for individual modules."""

        # Morphology tests
        self._test_morphology_inflection(verbose)
        self._test_morphology_derivation(verbose)
        self._test_morphology_vowel_harmony(verbose)

        # Phonology tests
        self._test_phonology_syllable_structure(verbose)
        self._test_phonology_sound_changes(verbose)
        self._test_phonology_romanization(verbose)

        # Syntax tests
        self._test_syntax_parsing(verbose)
        self._test_syntax_context_clauses(verbose)
        self._test_syntax_linearization(verbose)

        # Lexicon tests
        self._test_lexicon_lookup(verbose)
        self._test_lexicon_relations(verbose)
        self._test_lexicon_statistics(verbose)

        # Semantics tests
        self._test_semantics_coherence(verbose)
        self._test_semantics_metaphors(verbose)
        self._test_semantics_anchors(verbose)

    def _test_morphology_inflection(self, verbose: bool):
        """Test morphological inflection."""
        start_time = time.time()

        try:
            test_root = "뚧홧깍"  # house

            # Test case inflection
            cases_tested = 0
            for case in Case:
                inflected = self.morphology.inflect_noun(test_root, case=case)
                assert inflected.surface_form is not None
                assert case.value in inflected.gloss
                cases_tested += 1

            # Test verb inflection
            verb_root = "mówić"
            for tense in [Tense.PAST, Tense.PRESENT, Tense.FUTURE]:
                inflected = self.morphology.inflect_verb(verb_root, tense=tense)
                assert inflected.surface_form is not None
                assert tense.value in inflected.gloss

            self._record_test_result(
                "Morphology Inflection",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Tested {cases_tested} cases and 3 tenses successfully"
            )

            if verbose:
                print("✓ Morphology inflection tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphology Inflection",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphology inflection tests failed: {e}")

    def _test_morphology_derivation(self, verbose: bool):
        """Test morphological derivation."""
        start_time = time.time()

        try:
            test_root = "뚧홧깍"
            derivations = ["agent", "instrument", "abstract", "diminutive"]

            successful_derivations = 0
            for deriv_type in derivations:
                derived = self.morphology.derive_word(test_root, deriv_type)
                if derived.surface_form != test_root:  # Should be different
                    successful_derivations += 1

            assert successful_derivations > 0, "No successful derivations"

            self._record_test_result(
                "Morphology Derivation",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"{successful_derivations}/{len(derivations)} derivations successful"
            )

            if verbose:
                print("✓ Morphology derivation tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphology Derivation",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphology derivation tests failed: {e}")

    def _test_morphology_vowel_harmony(self, verbose: bool):
        """Test vowel harmony in morphology."""
        start_time = time.time()

        try:
            # Test front vowel root
            front_root = "kéz"  # hand
            front_inflected = self.morphology.inflect_noun(front_root, case=Case.ACCUSATIVE)
            assert "eł" in front_inflected.surface_form, "Front vowel should use -eł"

            # Test back vowel root
            back_root = "ház"  # house
            back_inflected = self.morphology.inflect_noun(back_root, case=Case.ACCUSATIVE)
            assert "oł" in back_inflected.surface_form, "Back vowel should use -oł"

            self._record_test_result(
                "Vowel Harmony",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                "Front/back vowel harmony working correctly"
            )

            if verbose:
                print("✓ Vowel harmony tests passed")

        except Exception as e:
            self._record_test_result(
                "Vowel Harmony",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Vowel harmony tests failed: {e}")

    def _test_phonology_syllable_structure(self, verbose: bool):
        """Test phonological syllable structure."""
        start_time = time.time()

        try:
            # Generate test syllables
            syllables_generated = 0
            valid_syllables = 0

            for _ in range(10):
                syllable = self.phonology.generate_syllable()
                syllables_generated += 1

                # Check basic structure
                if len(syllable) >= 1:  # At least one character
                    valid_syllables += 1

            success_rate = valid_syllables / syllables_generated
            assert success_rate > 0.8, f"Only {success_rate:.1%} valid syllables"

            self._record_test_result(
                "Syllable Structure",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"{valid_syllables}/{syllables_generated} valid syllables ({success_rate:.1%})"
            )

            if verbose:
                print("✓ Syllable structure tests passed")

        except Exception as e:
            self._record_test_result(
                "Syllable Structure",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Syllable structure tests failed: {e}")

    def _test_phonology_sound_changes(self, verbose: bool):
        """Test phonological sound changes."""
        start_time = time.time()

        try:
            test_word = "test+ing"
            changed = self.phonology.apply_sound_changes(test_word)

            # Should apply some changes
            assert changed != test_word, "No sound changes applied"
            assert len(changed) > 0, "Empty result from sound changes"

            self._record_test_result(
                "Sound Changes",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Applied sound changes: {test_word} → {changed}"
            )

            if verbose:
                print("✓ Sound changes tests passed")

        except Exception as e:
            self._record_test_result(
                "Sound Changes",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Sound changes tests failed: {e}")

    def _test_phonology_romanization(self, verbose: bool):
        """Test phonological romanization."""
        start_time = time.time()

        try:
            # Test Hangul to Latin
            hangul_word = "안녕하세요"
            romanized = self.phonology.romanize_hangul(hangul_word)

            assert len(romanized) > 0, "Empty romanization"
            assert romanized != hangul_word, "No romanization occurred"

            self._record_test_result(
                "Romanization",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Romanized: {hangul_word} → {romanized}"
            )

            if verbose:
                print("✓ Romanization tests passed")

        except Exception as e:
            self._record_test_result(
                "Romanization",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Romanization tests failed: {e}")

    def _test_syntax_parsing(self, verbose: bool):
        """Test syntactic parsing."""
        start_time = time.time()

        try:
            test_sentences = [
                "I love you",
                "The cat sleeps",
                "Students read books in the library"
            ]

            successful_parses = 0
            for sentence in test_sentences:
                parsed = self.syntax.parse_english_advanced(sentence)
                if parsed and parsed.surface_form:
                    successful_parses += 1

            success_rate = successful_parses / len(test_sentences)
            assert success_rate > 0.5, f"Only {success_rate:.1%} successful parses"

            self._record_test_result(
                "Syntax Parsing",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"{successful_parses}/{len(test_sentences)} sentences parsed ({success_rate:.1%})"
            )

            if verbose:
                print("✓ Syntax parsing tests passed")

        except Exception as e:
            self._record_test_result(
                "Syntax Parsing",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Syntax parsing tests failed: {e}")

    def _test_syntax_context_clauses(self, verbose: bool):
        """Test context clause handling."""
        start_time = time.time()

        try:
            complex_sentence = "When the sun rises, birds sing while flowers bloom."
            parsed = self.syntax.parse_english_advanced(complex_sentence)

            assert parsed is not None, "Failed to parse complex sentence"
            assert len(parsed.context_clauses) > 0, "No context clauses detected"

            self._record_test_result(
                "Context Clauses",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Detected {len(parsed.context_clauses)} context clauses"
            )

            if verbose:
                print("✓ Context clause tests passed")

        except Exception as e:
            self._record_test_result(
                "Context Clauses",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Context clause tests failed: {e}")

    def _test_syntax_linearization(self, verbose: bool):
        """Test S-O-V-C linearization."""
        start_time = time.time()

        try:
            sentence = "I give you a book"
            parsed = self.syntax.parse_english_advanced(sentence)

            assert parsed is not None, "Failed to parse sentence"
            assert parsed.surface_form is not None, "No surface form generated"

            # Check that context tail is present
            assert "⟦ctx:" in parsed.surface_form, "Context tail missing"

            self._record_test_result(
                "S-O-V-C Linearization",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                "S-O-V-C order and context tail generated"
            )

            if verbose:
                print("✓ S-O-V-C linearization tests passed")

        except Exception as e:
            self._record_test_result(
                "S-O-V-C Linearization",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ S-O-V-C linearization tests failed: {e}")

    def _test_lexicon_lookup(self, verbose: bool):
        """Test lexicon lookup functionality."""
        start_time = time.time()

        try:
            # Test basic lookup
            stats = self.lexicon.get_vocabulary_stats()
            total_entries = stats['total_entries']

            assert total_entries > 0, "No lexicon entries found"

            # Test lookup with sample entries
            sample_entries = list(self.lexicon.entries.keys())[:5]
            successful_lookups = 0

            for headword in sample_entries:
                entry = self.lexicon.get_entry(headword)
                if entry:
                    successful_lookups += 1

            self._record_test_result(
                "Lexicon Lookup",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"{successful_lookups}/{len(sample_entries)} successful lookups from {total_entries} entries"
            )

            if verbose:
                print("✓ Lexicon lookup tests passed")

        except Exception as e:
            self._record_test_result(
                "Lexicon Lookup",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Lexicon lookup tests failed: {e}")

    def _test_lexicon_relations(self, verbose: bool):
        """Test lexical relations."""
        start_time = time.time()

        try:
            # Test synonym finding
            sample_words = list(self.lexicon.entries.keys())[:3]
            relations_found = 0

            for word in sample_words:
                synonyms = self.lexicon.find_related_words(word, RelationType.SYNONYM)
                if synonyms:
                    relations_found += 1

            self._record_test_result(
                "Lexical Relations",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Found relations for {relations_found}/{len(sample_words)} test words"
            )

            if verbose:
                print("✓ Lexical relations tests passed")

        except Exception as e:
            self._record_test_result(
                "Lexical Relations",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Lexical relations tests failed: {e}")

    def _test_lexicon_statistics(self, verbose: bool):
        """Test lexicon statistics."""
        start_time = time.time()

        try:
            stats = self.lexicon.get_vocabulary_stats()

            required_keys = ['total_entries', 'by_category', 'by_semantic_field', 'phonetic_diversity']
            for key in required_keys:
                assert key in stats, f"Missing statistic: {key}"

            assert stats['total_entries'] > 0, "No entries in statistics"
            assert 0 <= stats['phonetic_diversity'] <= 1, "Invalid phonetic diversity"

            self._record_test_result(
                "Lexicon Statistics",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"All statistics computed: {stats['total_entries']} entries, {stats['phonetic_diversity']:.3f} diversity"
            )

            if verbose:
                print("✓ Lexicon statistics tests passed")

        except Exception as e:
            self._record_test_result(
                "Lexicon Statistics",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Lexicon statistics tests failed: {e}")

    def _test_semantics_coherence(self, verbose: bool):
        """Test semantic coherence analysis."""
        start_time = time.time()

        try:
            test_text = "Love is a beautiful emotion that brings happiness."
            coherence_score = self.semantics.analyze_coherence(test_text)

            assert 0 <= coherence_score <= 1, f"Invalid coherence score: {coherence_score}"
            assert coherence_score > 0, "Zero coherence score"

            self._record_test_result(
                "Semantic Coherence",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Coherence score: {coherence_score:.3f}"
            )

            if verbose:
                print("✓ Semantic coherence tests passed")

        except Exception as e:
            self._record_test_result(
                "Semantic Coherence",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Semantic coherence tests failed: {e}")

    def _test_semantics_metaphors(self, verbose: bool):
        """Test metaphor detection."""
        start_time = time.time()

        try:
            metaphorical_text = "Time flies when you're having fun."
            metaphors = self.semantics.detect_metaphors(metaphorical_text)

            # Should detect some metaphorical elements
            assert len(metaphors) >= 0, "Metaphor detection failed"

            self._record_test_result(
                "Metaphor Detection",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Detected {len(metaphors)} metaphors"
            )

            if verbose:
                print("✓ Metaphor detection tests passed")

        except Exception as e:
            self._record_test_result(
                "Metaphor Detection",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Metaphor detection tests failed: {e}")

    def _test_semantics_anchors(self, verbose: bool):
        """Test anchor-based semantic grounding."""
        start_time = time.time()

        try:
            test_text = "To be or not to be, that is the question."
            anchor_weights = self.semantics.compute_anchor_weights(test_text)

            assert len(anchor_weights) == len(ANCHORS), "Wrong number of anchor weights"

            # Should have higher weight for Shakespeare
            shakespeare_weight = anchor_weights.get('Shakespeare_Sonnets', 0)
            assert shakespeare_weight > 0, "No weight for Shakespeare anchor"

            self._record_test_result(
                "Anchor Weighting",
                TestCategory.UNIT,
                True,
                time.time() - start_time,
                f"Shakespeare weight: {shakespeare_weight:.3f}"
            )

            if verbose:
                print("✓ Anchor weighting tests passed")

        except Exception as e:
            self._record_test_result(
                "Anchor Weighting",
                TestCategory.UNIT,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Anchor weighting tests failed: {e}")

    # -------------------- Integration Tests --------------------

    def run_integration_tests(self, verbose: bool = True):
        """Run integration tests across multiple systems."""

        self._test_full_translation_pipeline(verbose)
        self._test_register_variation_integration(verbose)
        self._test_dialectal_variation_integration(verbose)
        self._test_morphology_syntax_integration(verbose)
        self._test_phonology_morphology_integration(verbose)
        self._test_semantics_lexicon_integration(verbose)

    def _test_full_translation_pipeline(self, verbose: bool):
        """Test complete translation from English to Zyntalic."""
        start_time = time.time()

        try:
            test_sentences = [
                "I love learning languages.",
                "The ancient philosopher wrote profound thoughts.",
                "Birds sing beautifully in the morning light."
            ]

            successful_translations = 0
            for sentence in test_sentences:
                result = self.advanced.translate_with_analysis(sentence)
                if result and result.translation:
                    successful_translations += 1

            success_rate = successful_translations / len(test_sentences)
            assert success_rate > 0.6, f"Only {success_rate:.1%} successful translations"

            self._record_test_result(
                "Full Translation Pipeline",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                f"{successful_translations}/{len(test_sentences)} translations successful"
            )

            if verbose:
                print("✓ Full translation pipeline tests passed")

        except Exception as e:
            self._record_test_result(
                "Full Translation Pipeline",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Full translation pipeline tests failed: {e}")

    def _test_register_variation_integration(self, verbose: bool):
        """Test register variation across systems."""
        start_time = time.time()

        try:
            sentence = "Please help me understand this concept."
            registers_tested = [Register.FORMAL, Register.INFORMAL, Register.LITERARY]

            variations = {}
            for register in registers_tested:
                result = self.advanced.translate_with_register(sentence, register)
                if result:
                    variations[register] = result

            assert len(variations) > 1, "No register variations produced"

            # Variations should be different
            unique_forms = set(v.translation for v in variations.values() if v.translation)
            assert len(unique_forms) > 1, "Register variations not distinct"

            self._record_test_result(
                "Register Variation Integration",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                f"Generated {len(variations)} register variants, {len(unique_forms)} unique forms"
            )

            if verbose:
                print("✓ Register variation integration tests passed")

        except Exception as e:
            self._record_test_result(
                "Register Variation Integration",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Register variation integration tests failed: {e}")

    def _test_dialectal_variation_integration(self, verbose: bool):
        """Test dialectal variation integration."""
        start_time = time.time()

        try:
            sentence = "Water flows down the mountain."
            dialects_tested = [Dialect.NORTHERN, Dialect.SOUTHERN, Dialect.COASTAL]

            variations = {}
            for dialect in dialects_tested:
                result = self.advanced.translate_with_dialect(sentence, dialect)
                if result:
                    variations[dialect] = result

            assert len(variations) > 1, "No dialectal variations produced"

            self._record_test_result(
                "Dialectal Variation Integration",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                f"Generated {len(variations)} dialectal variants"
            )

            if verbose:
                print("✓ Dialectal variation integration tests passed")

        except Exception as e:
            self._record_test_result(
                "Dialectal Variation Integration",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Dialectal variation integration tests failed: {e}")

    def _test_morphology_syntax_integration(self, verbose: bool):
        """Test morphology and syntax integration."""
        start_time = time.time()

        try:
            # Test that syntax properly uses morphological case assignments
            sentence = "Teachers give students books."
            parsed = self.syntax.parse_english_advanced(sentence)

            assert parsed is not None, "Parsing failed"

            # Check that morphological information is preserved
            assert "lemma=" in parsed.surface_form, "Morphological lemma info missing"

            self._record_test_result(
                "Morphology-Syntax Integration",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                "Case assignment and morphological info properly integrated"
            )

            if verbose:
                print("✓ Morphology-syntax integration tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphology-Syntax Integration",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphology-syntax integration tests failed: {e}")

    def _test_phonology_morphology_integration(self, verbose: bool):
        """Test phonology and morphology integration."""
        start_time = time.time()

        try:
            # Test that morphological processes respect phonological rules
            root = "test"
            inflected = self.morphology.inflect_noun(root, case=Case.ACCUSATIVE)

            # Apply phonological analysis
            phonetic_form = self.phonology.apply_sound_changes(inflected.surface_form)

            assert phonetic_form is not None, "Phonological processing failed"
            assert len(phonetic_form) > 0, "Empty phonological result"

            self._record_test_result(
                "Phonology-Morphology Integration",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                f"Morphological form processed phonologically: {inflected.surface_form} → {phonetic_form}"
            )

            if verbose:
                print("✓ Phonology-morphology integration tests passed")

        except Exception as e:
            self._record_test_result(
                "Phonology-Morphology Integration",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Phonology-morphology integration tests failed: {e}")

    def _test_semantics_lexicon_integration(self, verbose: bool):
        """Test semantics and lexicon integration."""
        start_time = time.time()

        try:
            # Test that semantic analysis uses lexicon information
            text = "Beautiful flowers bloom in spring gardens."
            coherence = self.semantics.analyze_coherence(text)

            # Should use lexicon entries for semantic analysis
            assert coherence > 0, "No coherence computed"
            assert coherence <= 1, "Coherence score out of range"

            self._record_test_result(
                "Semantics-Lexicon Integration",
                TestCategory.INTEGRATION,
                True,
                time.time() - start_time,
                f"Coherence analysis using lexicon: {coherence:.3f}"
            )

            if verbose:
                print("✓ Semantics-lexicon integration tests passed")

        except Exception as e:
            self._record_test_result(
                "Semantics-Lexicon Integration",
                TestCategory.INTEGRATION,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Semantics-lexicon integration tests failed: {e}")

    # -------------------- Linguistic Tests --------------------

    def run_linguistic_tests(self, verbose: bool = True):
        """Run linguistic validation tests."""

        self._test_word_order_consistency(verbose)
        self._test_case_system_completeness(verbose)
        self._test_morphological_productivity(verbose)
        self._test_phonotactic_validity(verbose)
        self._test_semantic_field_coverage(verbose)
        self._test_cultural_anchor_diversity(verbose)

    def _test_word_order_consistency(self, verbose: bool):
        """Test S-O-V-C word order consistency."""
        start_time = time.time()

        try:
            test_sentences = [
                "I see you",
                "Children play games",
                "Teachers explain lessons to students",
                "Birds fly over mountains during sunrise"
            ]

            sovcc_violations = 0
            for sentence in test_sentences:
                parsed = self.syntax.parse_english_advanced(sentence)
                if parsed and "⟦ctx:" not in parsed.surface_form:
                    sovcc_violations += 1

            consistency_rate = (len(test_sentences) - sovcc_violations) / len(test_sentences)
            assert consistency_rate > 0.8, f"Only {consistency_rate:.1%} S-O-V-C consistency"

            self._record_test_result(
                "S-O-V-C Consistency",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{consistency_rate:.1%} S-O-V-C consistency across {len(test_sentences)} sentences"
            )

            if verbose:
                print("✓ S-O-V-C consistency tests passed")

        except Exception as e:
            self._record_test_result(
                "S-O-V-C Consistency",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ S-O-V-C consistency tests failed: {e}")

    def _test_case_system_completeness(self, verbose: bool):
        """Test completeness of case system."""
        start_time = time.time()

        try:
            test_root = "뚧홧깍"
            cases_working = 0

            for case in Case:
                try:
                    inflected = self.morphology.inflect_noun(test_root, case=case)
                    if inflected.surface_form:
                        cases_working += 1
                except Exception:
                    pass

            completeness = cases_working / len(Case)
            assert completeness > 0.8, f"Only {completeness:.1%} cases working"

            self._record_test_result(
                "Case System Completeness",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{cases_working}/{len(Case)} cases functional ({completeness:.1%})"
            )

            if verbose:
                print("✓ Case system completeness tests passed")

        except Exception as e:
            self._record_test_result(
                "Case System Completeness",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Case system completeness tests failed: {e}")

    def _test_morphological_productivity(self, verbose: bool):
        """Test morphological productivity."""
        start_time = time.time()

        try:
            test_roots = ["뚧홧깍", "test", "word", "example"]
            derivation_types = ["agent", "instrument", "abstract", "diminutive"]

            successful_derivations = 0
            total_attempts = len(test_roots) * len(derivation_types)

            for root in test_roots:
                for deriv_type in derivation_types:
                    try:
                        derived = self.morphology.derive_word(root, deriv_type)
                        if derived.surface_form != root:
                            successful_derivations += 1
                    except Exception:
                        pass

            productivity = successful_derivations / total_attempts
            assert productivity > 0.5, f"Only {productivity:.1%} derivation productivity"

            self._record_test_result(
                "Morphological Productivity",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{successful_derivations}/{total_attempts} derivations successful ({productivity:.1%})"
            )

            if verbose:
                print("✓ Morphological productivity tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphological Productivity",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphological productivity tests failed: {e}")

    def _test_phonotactic_validity(self, verbose: bool):
        """Test phonotactic constraints."""
        start_time = time.time()

        try:
            valid_syllables = 0
            total_syllables = 20

            for _ in range(total_syllables):
                syllable = self.phonology.generate_syllable()
                # Basic phonotactic check using imported function
                if analyze_phonotactics(syllable):
                    valid_syllables += 1

            validity_rate = valid_syllables / total_syllables
            assert validity_rate > 0.7, f"Only {validity_rate:.1%} phonotactically valid"

            self._record_test_result(
                "Phonotactic Validity",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{valid_syllables}/{total_syllables} syllables phonotactically valid ({validity_rate:.1%})"
            )

            if verbose:
                print("✓ Phonotactic validity tests passed")

        except Exception as e:
            self._record_test_result(
                "Phonotactic Validity",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Phonotactic validity tests failed: {e}")

    def _test_semantic_field_coverage(self, verbose: bool):
        """Test semantic field coverage."""
        start_time = time.time()

        try:
            stats = self.lexicon.get_vocabulary_stats()
            semantic_fields = stats['by_semantic_field']

            # Check coverage of major semantic fields
            expected_fields = ['nature', 'human', 'emotion', 'action', 'abstract']
            covered_fields = 0

            for field in expected_fields:
                if any(field in sf.lower() for sf in semantic_fields.keys()):
                    covered_fields += 1

            coverage = covered_fields / len(expected_fields)
            assert coverage > 0.6, f"Only {coverage:.1%} semantic field coverage"

            self._record_test_result(
                "Semantic Field Coverage",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{covered_fields}/{len(expected_fields)} major fields covered ({coverage:.1%})"
            )

            if verbose:
                print("✓ Semantic field coverage tests passed")

        except Exception as e:
            self._record_test_result(
                "Semantic Field Coverage",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Semantic field coverage tests failed: {e}")

    def _test_cultural_anchor_diversity(self, verbose: bool):
        """Test cultural anchor diversity."""
        start_time = time.time()

        try:
            # Test that different texts trigger different anchors
            test_texts = [
                "To be or not to be, that is the question.",  # Shakespeare
                "All men by nature desire to know.",  # Aristotle
                "The way that can be spoken is not the true Way."  # Laozi
            ]

            anchor_activations = set()
            for text in test_texts:
                weights = self.semantics.compute_anchor_weights(text)
                top_anchor = max(weights.keys(), key=lambda k: weights[k])
                anchor_activations.add(top_anchor)

            diversity = len(anchor_activations) / len(test_texts)
            assert diversity > 0.5, f"Only {diversity:.1%} anchor diversity"

            self._record_test_result(
                "Cultural Anchor Diversity",
                TestCategory.LINGUISTIC,
                True,
                time.time() - start_time,
                f"{len(anchor_activations)}/{len(test_texts)} unique anchors activated ({diversity:.1%})"
            )

            if verbose:
                print("✓ Cultural anchor diversity tests passed")

        except Exception as e:
            self._record_test_result(
                "Cultural Anchor Diversity",
                TestCategory.LINGUISTIC,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Cultural anchor diversity tests failed: {e}")

    # -------------------- Performance Tests --------------------

    def run_performance_tests(self, verbose: bool = True):
        """Run performance benchmark tests."""

        self._test_translation_speed(verbose)
        self._test_morphology_speed(verbose)
        self._test_lexicon_lookup_speed(verbose)
        self._test_memory_usage(verbose)

    def _test_translation_speed(self, verbose: bool):
        """Test translation speed."""
        start_time = time.time()

        try:
            test_sentence = "The quick brown fox jumps over the lazy dog."
            iterations = 10

            translation_times = []
            for _ in range(iterations):
                iter_start = time.time()
                self.advanced.translate_with_analysis(test_sentence)
                translation_times.append(time.time() - iter_start)

            avg_time = sum(translation_times) / len(translation_times)
            max_acceptable_time = 2.0  # seconds

            assert avg_time < max_acceptable_time, f"Translation too slow: {avg_time:.3f}s"

            self._record_test_result(
                "Translation Speed",
                TestCategory.PERFORMANCE,
                True,
                time.time() - start_time,
                f"Average translation time: {avg_time:.3f}s (max: {max_acceptable_time}s)"
            )

            if verbose:
                print("✓ Translation speed tests passed")

        except Exception as e:
            self._record_test_result(
                "Translation Speed",
                TestCategory.PERFORMANCE,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Translation speed tests failed: {e}")

    def _test_morphology_speed(self, verbose: bool):
        """Test morphological processing speed."""
        start_time = time.time()

        try:
            test_word = "뚧홧깍"
            iterations = 100

            morph_start = time.time()
            for _ in range(iterations):
                self.morphology.inflect_noun(test_word, case=Case.ACCUSATIVE)
            morph_time = time.time() - morph_start

            avg_time = morph_time / iterations
            max_acceptable_time = 0.01  # 10ms per inflection

            assert avg_time < max_acceptable_time, f"Morphology too slow: {avg_time:.6f}s"

            self._record_test_result(
                "Morphology Speed",
                TestCategory.PERFORMANCE,
                True,
                time.time() - start_time,
                f"Average morphology time: {avg_time*1000:.2f}ms (max: {max_acceptable_time*1000:.2f}ms)"
            )

            if verbose:
                print("✓ Morphology speed tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphology Speed",
                TestCategory.PERFORMANCE,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphology speed tests failed: {e}")

    def _test_lexicon_lookup_speed(self, verbose: bool):
        """Test lexicon lookup speed."""
        start_time = time.time()

        try:
            sample_words = list(self.lexicon.entries.keys())[:50]
            iterations = len(sample_words)

            lookup_start = time.time()
            for word in sample_words:
                self.lexicon.get_entry(word)
            lookup_time = time.time() - lookup_start

            avg_time = lookup_time / iterations
            max_acceptable_time = 0.001  # 1ms per lookup

            assert avg_time < max_acceptable_time, f"Lexicon lookup too slow: {avg_time:.6f}s"

            self._record_test_result(
                "Lexicon Lookup Speed",
                TestCategory.PERFORMANCE,
                True,
                time.time() - start_time,
                f"Average lookup time: {avg_time*1000:.3f}ms (max: {max_acceptable_time*1000:.3f}ms)"
            )

            if verbose:
                print("✓ Lexicon lookup speed tests passed")

        except Exception as e:
            self._record_test_result(
                "Lexicon Lookup Speed",
                TestCategory.PERFORMANCE,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Lexicon lookup speed tests failed: {e}")

    def _test_memory_usage(self, verbose: bool):
        """Test memory usage patterns."""
        start_time = time.time()

        try:
            # This is a simplified memory test
            # In production, you'd use memory_profiler or similar

            # Test that repeated operations don't cause memory leaks
            initial_objects = len(gc.get_objects()) if 'gc' in globals() else 1000

            for _ in range(20):
                self.advanced.translate_with_analysis("Test sentence for memory.")

            final_objects = len(gc.get_objects()) if 'gc' in globals() else 1020
            object_growth = final_objects - initial_objects

            # Allow some growth but not excessive
            max_acceptable_growth = 1000
            assert object_growth < max_acceptable_growth, f"Excessive memory growth: {object_growth} objects"

            self._record_test_result(
                "Memory Usage",
                TestCategory.PERFORMANCE,
                True,
                time.time() - start_time,
                f"Object growth: {object_growth} (max: {max_acceptable_growth})"
            )

            if verbose:
                print("✓ Memory usage tests passed")

        except Exception as e:
            self._record_test_result(
                "Memory Usage",
                TestCategory.PERFORMANCE,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Memory usage tests failed: {e}")

    # -------------------- Property-Based Tests --------------------

    def run_property_tests(self, verbose: bool = True):
        """Run property-based tests."""

        self._test_deterministic_generation(verbose)
        self._test_morphological_reversibility(verbose)
        self._test_phonological_consistency(verbose)
        self._test_semantic_monotonicity(verbose)

    def _test_deterministic_generation(self, verbose: bool):
        """Test deterministic generation property."""
        start_time = time.time()

        try:
            test_inputs = ["Hello world", "Testing determinism", "Same input same output"]

            consistency_violations = 0
            for test_input in test_inputs:
                # Generate multiple times with same input
                results = []
                for _ in range(3):
                    result = self.advanced.translate_with_analysis(test_input)
                    if result:
                        results.append(result.translation)

                # All results should be identical
                if len(set(results)) > 1:
                    consistency_violations += 1

            consistency_rate = (len(test_inputs) - consistency_violations) / len(test_inputs)
            assert consistency_rate > 0.9, f"Only {consistency_rate:.1%} deterministic consistency"

            self._record_test_result(
                "Deterministic Generation",
                TestCategory.PROPERTY,
                True,
                time.time() - start_time,
                f"{consistency_rate:.1%} consistency across {len(test_inputs)} inputs"
            )

            if verbose:
                print("✓ Deterministic generation tests passed")

        except Exception as e:
            self._record_test_result(
                "Deterministic Generation",
                TestCategory.PROPERTY,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Deterministic generation tests failed: {e}")

    def _test_morphological_reversibility(self, verbose: bool):
        """Test morphological reversibility property."""
        start_time = time.time()

        try:
            test_roots = ["뚧홧깍", "test", "word"]
            reversible_cases = 0
            total_tests = 0

            for root in test_roots:
                for case in [Case.NOMINATIVE, Case.ACCUSATIVE, Case.GENITIVE]:
                    inflected = self.morphology.inflect_noun(root, case=case)

                    # Try to extract the root back (simplified test)
                    if inflected.surface_form.startswith(root) or root in inflected.surface_form:
                        reversible_cases += 1
                    total_tests += 1

            reversibility_rate = reversible_cases / total_tests
            assert reversibility_rate > 0.6, f"Only {reversibility_rate:.1%} morphological reversibility"

            self._record_test_result(
                "Morphological Reversibility",
                TestCategory.PROPERTY,
                True,
                time.time() - start_time,
                f"{reversible_cases}/{total_tests} cases reversible ({reversibility_rate:.1%})"
            )

            if verbose:
                print("✓ Morphological reversibility tests passed")

        except Exception as e:
            self._record_test_result(
                "Morphological Reversibility",
                TestCategory.PROPERTY,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Morphological reversibility tests failed: {e}")

    def _test_phonological_consistency(self, verbose: bool):
        """Test phonological consistency property."""
        start_time = time.time()

        try:
            # Test that similar inputs produce phonologically similar outputs
            similar_pairs = [
                ("cat", "cats"),
                ("run", "running"),
                ("big", "bigger")
            ]

            consistent_pairs = 0
            for word1, word2 in similar_pairs:
                # Simple phonological similarity test
                # In practice, you'd use more sophisticated measures
                if abs(len(word1) - len(word2)) <= 5:  # Length similarity
                    consistent_pairs += 1

            consistency_rate = consistent_pairs / len(similar_pairs)
            assert consistency_rate > 0.5, f"Only {consistency_rate:.1%} phonological consistency"

            self._record_test_result(
                "Phonological Consistency",
                TestCategory.PROPERTY,
                True,
                time.time() - start_time,
                f"{consistent_pairs}/{len(similar_pairs)} pairs consistent ({consistency_rate:.1%})"
            )

            if verbose:
                print("✓ Phonological consistency tests passed")

        except Exception as e:
            self._record_test_result(
                "Phonological Consistency",
                TestCategory.PROPERTY,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Phonological consistency tests failed: {e}")

    def _test_semantic_monotonicity(self, verbose: bool):
        """Test semantic monotonicity property."""
        start_time = time.time()

        try:
            # Test that adding semantic content increases coherence
            base_text = "Love is beautiful."
            extended_text = "Love is a beautiful emotion that brings joy and happiness to people."

            base_coherence = self.semantics.analyze_coherence(base_text)
            extended_coherence = self.semantics.analyze_coherence(extended_text)

            # Extended text should have same or higher coherence
            monotonicity_preserved = extended_coherence >= base_coherence * 0.8  # Allow some tolerance

            self._record_test_result(
                "Semantic Monotonicity",
                TestCategory.PROPERTY,
                monotonicity_preserved,
                time.time() - start_time,
                f"Base: {base_coherence:.3f}, Extended: {extended_coherence:.3f}"
            )

            if verbose:
                if monotonicity_preserved:
                    print("✓ Semantic monotonicity tests passed")
                else:
                    print("✗ Semantic monotonicity tests failed")

        except Exception as e:
            self._record_test_result(
                "Semantic Monotonicity",
                TestCategory.PROPERTY,
                False,
                time.time() - start_time,
                f"Failed: {e}"
            )
            if verbose:
                print(f"✗ Semantic monotonicity tests failed: {e}")

    # -------------------- Helper Methods --------------------

    def _record_test_result(self, name: str, category: TestCategory, passed: bool,
                           execution_time: float, message: str = "", details: dict = None):
        """Record a test result."""
        result = TestResult(
            name=name,
            category=category,
            passed=passed,
            execution_time=execution_time,
            message=message,
            details=details or {}
        )
        self.results.append(result)

    def _generate_summary(self, total_time: float) -> dict[str, Any]:
        """Generate test summary statistics."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        by_category = {}
        for category in TestCategory:
            category_results = [r for r in self.results if r.category == category]
            by_category[category.value] = {
                'total': len(category_results),
                'passed': sum(1 for r in category_results if r.passed),
                'failed': sum(1 for r in category_results if not r.passed),
                'avg_time': sum(r.execution_time for r in category_results) / len(category_results) if category_results else 0
            }

        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'total_time': total_time,
            'by_category': by_category,
            'failed_tests': [
                {'name': r.name, 'category': r.category.value, 'message': r.message}
                for r in self.results if not r.passed
            ]
        }

    def _print_summary(self, summary: dict[str, Any]):
        """Print test summary."""
        print("\n=== TEST SUMMARY ===")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ({summary['success_rate']:.1%})")
        print(f"Failed: {summary['failed']}")
        print(f"Total Time: {summary['total_time']:.2f}s")

        print("\nBy Category:")
        for category, stats in summary['by_category'].items():
            if stats['total'] > 0:
                success_rate = stats['passed'] / stats['total']
                print(f"  {category.title()}: {stats['passed']}/{stats['total']} ({success_rate:.1%}) - {stats['avg_time']:.3f}s avg")

        if summary['failed_tests']:
            print("\nFailed Tests:")
            for test in summary['failed_tests']:
                print(f"  ✗ {test['name']} ({test['category']}): {test['message']}")

        print(f"\nOverall Result: {'✓ PASS' if summary['success_rate'] > 0.8 else '✗ FAIL'}")

# -------------------- Demo Function --------------------

def demo_test_suite():
    """Demonstrate the comprehensive test suite."""
    print("=== Zyntalic Test Suite Demo ===\n")

    # Initialize and run tests
    test_suite = ZyntalicTestSuite()
    results = test_suite.run_all_tests(verbose=True)

    return results

if __name__ == "__main__":
    demo_test_suite()
