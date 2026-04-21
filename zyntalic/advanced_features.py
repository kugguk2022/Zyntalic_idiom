"""
Advanced Zyntalic Language System

Integration of all linguistic components with advanced features:
- Unified translation pipeline
- Register variation (formal/informal/literary)
- Dialectal variation
- Historical language change simulation
- Code-switching between scripts
- Advanced discourse phenomena
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .core import generate_entry, get_rng
from .enhanced_syntax import ZyntalicSyntaxProcessor
from .lexicon_manager import ZyntalicLexicon
from .morphology import MorphologicalProcessor
from .phonology import PhonologicalProcessor
from .semantic_coherence import SemanticCoherenceProcessor

# -------------------- Advanced Linguistic Features --------------------

class Register(Enum):
    FORMAL = "formal"        # Official, academic, ceremonial
    INFORMAL = "informal"    # Casual, everyday conversation
    LITERARY = "literary"    # Poetic, artistic, elevated
    ARCHAIC = "archaic"      # Ancient, traditional forms
    TECHNICAL = "technical"  # Specialized, scientific

class Dialect(Enum):
    STANDARD = "standard"    # Standard Zyntalic
    NORTHERN = "northern"    # Northern dialect variation
    SOUTHERN = "southern"    # Southern dialect variation
    COASTAL = "coastal"      # Maritime/coastal variant
    MOUNTAIN = "mountain"    # Highland/mountain variant

class ScriptPreference(Enum):
    HANGUL_HEAVY = "hangul"     # 85% Hangul, 15% Latin
    LATIN_HEAVY = "latin"       # 85% Latin, 15% Hangul
    MIXED = "mixed"             # 50/50 mix
    DYNAMIC = "dynamic"         # Context-dependent switching

@dataclass
class LanguageVariation:
    """Configuration for language variation."""
    register: Register = Register.FORMAL
    dialect: Dialect = Dialect.STANDARD
    script_preference: ScriptPreference = ScriptPreference.HANGUL_HEAVY
    formality_level: float = 0.5    # 0.0 = very informal, 1.0 = very formal
    archaism_rate: float = 0.1      # How often to use archaic forms
    innovation_rate: float = 0.05   # How often to create new forms

@dataclass
class TranslationOptions:
    """Options for advanced translation."""
    preserve_metaphors: bool = True
    maintain_register: bool = True
    enhance_coherence: bool = True
    add_cultural_context: bool = True
    apply_sound_changes: bool = True
    use_dialectal_forms: bool = False

@dataclass
class AdvancedTranslationResult:
    """Result of advanced translation with analysis."""
    def __init__(self, zyntalic_text, original_text, morphological_analysis=None,
                 phonological_analysis=None, syntactic_analysis=None, semantic_analysis=None,
                 coherence_score=0.0, register_analysis=None, cultural_elements=None):
        self.zyntalic_text = zyntalic_text
        self.original_text = original_text
        self.morphological_analysis = morphological_analysis or {}
        self.phonological_analysis = phonological_analysis or {}
        self.syntactic_analysis = syntactic_analysis or {}
        self.semantic_analysis = semantic_analysis or {}
        self.coherence_score = coherence_score
        self.register_analysis = register_analysis or {}
        self.cultural_elements = cultural_elements or []

    @property
    def translation(self) -> str:
        """Alias for zyntalic_text for compatibility."""
        return self.zyntalic_text

# -------------------- Advanced Language Processor --------------------

class AdvancedZyntalicProcessor:
    """Unified processor for advanced Zyntalic language features."""

    def __init__(self, seed: str = "advanced_zyntalic"):
        self.rng = get_rng(seed)

        # Initialize all subsystems
        self.morphology = MorphologicalProcessor(seed)
        self.phonology = PhonologicalProcessor(seed)
        self.syntax = ZyntalicSyntaxProcessor(seed)
        self.lexicon = ZyntalicLexicon(seed)
        self.semantics = SemanticCoherenceProcessor(self.lexicon, seed)

        # Initialize variation systems
        self._build_register_variations()
        self._build_dialect_variations()
        self._build_historical_forms()

    def _build_register_variations(self):
        """Build register-specific variations."""
        self.register_variations = {
            Register.FORMAL: {
                'honorifics': ['존경하는', '귀하', '각하'],
                'particles': ['-습니다', '-입니다'],
                'vocabulary_bias': 'high_frequency',
                'sentence_complexity': 'high',
            },

            Register.INFORMAL: {
                'contractions': ['해', '가', '야'],
                'particles': ['-어', '-아', '-지'],
                'vocabulary_bias': 'common',
                'sentence_complexity': 'simple',
            },

            Register.LITERARY: {
                'archaic_forms': ['하옵니다', '어이다'],
                'metaphor_rate': 0.8,
                'complex_syntax': True,
                'poetic_devices': ['alliteration', 'parallelism'],
            },

            Register.TECHNICAL: {
                'terminology': True,
                'precision': 'high',
                'passive_voice': 'preferred',
                'definitions': True,
            }
        }

    def _build_dialect_variations(self):
        """Build dialectal variations."""
        self.dialect_variations = {
            Dialect.NORTHERN: {
                'phonology': {
                    'vowel_shift': {'a': 'ə', 'o': 'ʊ'},
                    'consonant_change': {'k': 'x', 'p': 'f'},
                },
                'vocabulary': {
                    'house': '집북', 'water': '물동', 'fire': '불서'
                },
                'morphology': {
                    'plural_suffix': '-들녹',
                    'past_suffix': '-었녹'
                }
            },

            Dialect.SOUTHERN: {
                'phonology': {
                    'vowel_shift': {'i': 'e', 'u': 'o'},
                    'consonant_lenition': {'t': 'd', 'k': 'g'},
                },
                'vocabulary': {
                    'house': '집남', 'water': '물남', 'fire': '불남'
                },
                'morphology': {
                    'plural_suffix': '-들남',
                    'past_suffix': '-었남'
                }
            },

            Dialect.COASTAL: {
                'phonology': {
                    'nasal_harmony': True,
                    'liquid_merger': {'l': 'r'},
                },
                'vocabulary': {
                    'boat': '배바다', 'fish': '물고기바다', 'wave': '파도바다'
                },
                'cultural_terms': ['조류', '해류', '갯벌']
            }
        }

    def _build_historical_forms(self):
        """Build historical language forms for diachronic variation."""
        self.historical_forms = {
            'proto_zyntalic': {
                'consonant_inventory': 'fuller',
                'case_system': 'richer',
                'vowel_length': 'distinctive',
            },

            'old_zyntalic': {
                'verbal_system': 'complex_evidentials',
                'noun_classes': 'animate_inanimate',
                'script': 'pure_hangul',
            },

            'middle_zyntalic': {
                'latin_borrowings': 'extensive',
                'case_syncretism': 'beginning',
                'script_mixing': 'innovation',
            },

            'modern_zyntalic': {
                'simplified_morphology': True,
                'fixed_stress': True,
                'standardized_orthography': True,
            }
        }

    def translate_advanced(self, text: str, variation: LanguageVariation = None,
                          options: TranslationOptions = None) -> AdvancedTranslationResult:
        """Perform advanced translation with full linguistic analysis."""

        # Set defaults
        if variation is None:
            variation = LanguageVariation()
        if options is None:
            options = TranslationOptions()

        # Initialize result
        result = AdvancedTranslationResult(
            original_text=text,
            zyntalic_text=""
        )

        # Step 1: Semantic Analysis
        if options.enhance_coherence:
            result.semantic_analysis = self.semantics.analyze_semantic_coherence(text).__dict__

        # Step 2: Syntactic Parsing
        parsed_sentence = self.syntax.parse_english_advanced(text)
        result.syntactic_analysis = self.syntax.analyze_sentence_complexity(parsed_sentence)

        # Step 3: Basic Translation
        base_translation = self._generate_base_translation(text, variation)

        # Step 4: Apply Register Variations
        if options.maintain_register:
            register_translation = self._apply_register_variation(base_translation, variation)
        else:
            register_translation = base_translation

        # Step 5: Apply Dialectal Variations
        if options.use_dialectal_forms:
            dialect_translation = self._apply_dialect_variation(register_translation, variation)
        else:
            dialect_translation = register_translation

        # Step 6: Apply Phonological Processes
        if options.apply_sound_changes:
            phonological_translation = self.phonology.apply_sound_changes(dialect_translation)
            # Import the analysis function from phonology module
            from .phonology import analyze_phonotactics
            result.phonological_analysis = analyze_phonotactics(phonological_translation)
        else:
            phonological_translation = dialect_translation

        # Step 7: Morphological Analysis
        result.morphological_analysis = self._analyze_morphology(phonological_translation)

        # Step 8: Add Cultural Context
        if options.add_cultural_context:
            final_translation = self._add_cultural_context(phonological_translation, text, variation)
            result.cultural_elements = self._identify_cultural_elements(text)
        else:
            final_translation = phonological_translation

        # Step 9: Coherence Check
        if options.enhance_coherence:
            final_translation, coherence = self.semantics.ensure_translation_coherence(
                text, final_translation
            )
            result.coherence_score = coherence

        # Step 10: Register Analysis
        result.register_analysis = self._analyze_register_features(final_translation, variation)

        result.zyntalic_text = final_translation
        return result

    def _generate_base_translation(self, text: str, variation: LanguageVariation) -> str:
        """Generate base translation using core system."""
        # Use existing core translation but with variation parameters
        sentences = re.split(r'[.!?]+', text)
        translated_parts = []

        for sentence in sentences:
            if sentence.strip():
                # Adjust mirror rate based on register
                mirror_rate = 0.8
                if variation.register == Register.LITERARY:
                    mirror_rate = 0.95  # More philosophical/mirrored
                elif variation.register == Register.INFORMAL:
                    mirror_rate = 0.3   # Less philosophical

                entry = generate_entry(sentence.strip(), mirror_rate=mirror_rate)
                translated_parts.append(entry["sentence"])

        return " ".join(translated_parts)

    def _apply_register_variation(self, text: str, variation: LanguageVariation) -> str:
        """Apply register-specific variations to text."""
        register_config = self.register_variations.get(variation.register, {})

        modified_text = text

        # Apply formality markers
        if variation.register == Register.FORMAL:
            # Add formal particles and honorifics
            if 'particles' in register_config:
                # Replace informal endings with formal ones (simplified)
                modified_text = re.sub(r'(\w+)어', r'\1습니다', modified_text)

        elif variation.register == Register.LITERARY:
            # Increase metaphorical content
            if self.rng.random() < register_config.get('metaphor_rate', 0.5):
                # Add literary flourishes (simplified)
                if '⟦ctx:' in modified_text:
                    parts = modified_text.split('⟦ctx:')
                    literary_addition = " — 시공을 넘어서 — "  # "beyond time and space"
                    modified_text = parts[0] + literary_addition + '⟦ctx:' + parts[1]

        elif variation.register == Register.ARCHAIC:
            # Apply archaic forms based on rate
            if self.rng.random() < variation.archaism_rate:
                # Add archaic particles (simplified)
                archaic_marker = " 하옵니다 "  # archaic honorific
                modified_text = modified_text.replace(" ⟦ctx:", archaic_marker + " ⟦ctx:")

        return modified_text

    def _apply_dialect_variation(self, text: str, variation: LanguageVariation) -> str:
        """Apply dialectal variations to text."""
        if variation.dialect == Dialect.STANDARD:
            return text

        dialect_config = self.dialect_variations.get(variation.dialect, {})
        modified_text = text

        # Apply phonological changes
        if 'phonology' in dialect_config:
            phon_changes = dialect_config['phonology']

            # Vowel shifts
            if 'vowel_shift' in phon_changes:
                for old_v, new_v in phon_changes['vowel_shift'].items():
                    modified_text = modified_text.replace(old_v, new_v)

            # Consonant changes
            if 'consonant_change' in phon_changes:
                for old_c, new_c in phon_changes['consonant_change'].items():
                    modified_text = modified_text.replace(old_c, new_c)

        # Apply morphological changes
        if 'morphology' in dialect_config:
            morph_changes = dialect_config['morphology']

            # Change suffixes
            if 'plural_suffix' in morph_changes:
                new_suffix = morph_changes['plural_suffix']
                modified_text = re.sub(r'-ek\b', new_suffix, modified_text)
                modified_text = re.sub(r'-ok\b', new_suffix, modified_text)

        # Add dialectal vocabulary
        if 'vocabulary' in dialect_config:
            vocab_changes = dialect_config['vocabulary']
            for standard, dialectal in vocab_changes.items():
                # This is simplified - real implementation would need proper word boundaries
                modified_text = modified_text.replace(standard, dialectal)

        return modified_text

    def _add_cultural_context(self, text: str, original: str, variation: LanguageVariation) -> str:
        """Add cultural context markers to translation."""
        cultural_markers = []

        # Detect cultural concepts in original
        cultural_concepts = {
            'family': '가족문화',
            'honor': '명예문화',
            'nature': '자연철학',
            'time': '시간관념',
            'space': '공간철학',
        }

        original_lower = original.lower()
        for concept, marker in cultural_concepts.items():
            if concept in original_lower:
                cultural_markers.append(marker)

        # Add cultural context to the Korean context block
        if cultural_markers and '⟦ctx:' in text:
            cultural_str = "|".join(cultural_markers)
            text = text.replace('⟦ctx:', f'⟦ctx:culture={cultural_str}; ')

        return text

    def _identify_cultural_elements(self, text: str) -> list[str]:
        """Identify cultural elements in the source text."""
        elements = []

        # Cultural keywords
        cultural_keywords = {
            'family', 'honor', 'respect', 'tradition', 'wisdom', 'nature',
            'harmony', 'balance', 'journey', 'path', 'heart', 'soul'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if word in cultural_keywords:
                elements.append(word)

        return list(set(elements))  # Remove duplicates

    def _analyze_morphology(self, text: str) -> dict[str, any]:
        """Analyze morphological structure of translated text."""
        analysis = {
            'word_count': len(text.split()),
            'morphological_complexity': 0.0,
            'derivational_forms': 0,
            'inflectional_forms': 0,
            'compound_forms': 0,
        }

        words = text.split()
        complex_morphology = 0

        for word in words:
            # Count morphological complexity (simplified)
            if '-' in word:  # Has morpheme boundaries
                complex_morphology += word.count('-')

                # Check for derivational morphology
                derivational_suffixes = ['ász', 'ány', 'ság', 'ka', 'ko']
                for suffix in derivational_suffixes:
                    if suffix in word:
                        analysis['derivational_forms'] += 1
                        break

                # Check for inflectional morphology
                inflectional_suffixes = ['eł', 'oł', 'nek', 'nok', 're', 'ra']
                for suffix in inflectional_suffixes:
                    if suffix in word:
                        analysis['inflectional_forms'] += 1
                        break

            # Check for compounds (multiple roots)
            if len(word) > 6 and any(c in word for c in 'ᄀᄁᄂᄃ'):  # Has Hangul + length
                analysis['compound_forms'] += 1

        analysis['morphological_complexity'] = complex_morphology / len(words) if words else 0
        return analysis

    def _analyze_register_features(self, text: str, variation: LanguageVariation) -> dict[str, any]:
        """Analyze register features in the translated text."""
        analysis = {
            'target_register': variation.register.value,
            'formality_markers': 0,
            'honorifics': 0,
            'archaic_forms': 0,
            'technical_terms': 0,
            'literary_devices': 0,
        }

        # Count formality markers
        formal_markers = ['습니다', '입니다', '각하', '존경']
        for marker in formal_markers:
            analysis['formality_markers'] += text.count(marker)

        # Count honorifics
        honorifics = ['님', '씨', '선생', '귀하']
        for hon in honorifics:
            analysis['honorifics'] += text.count(hon)

        # Count archaic forms
        archaic_forms = ['하옵니다', '어이다', '누구니']
        for arch in archaic_forms:
            analysis['archaic_forms'] += text.count(arch)

        # Count literary devices (simplified)
        if '—' in text:  # Literary punctuation
            analysis['literary_devices'] += 1

        # Metaphorical patterns
        metaphor_patterns = ['through', 'beyond', 'within', '넘어서', '통하여']
        for pattern in metaphor_patterns:
            analysis['literary_devices'] += text.count(pattern)

        return analysis

    def generate_variation_samples(self, base_text: str, num_samples: int = 5) -> dict[str, str]:
        """Generate multiple variations of the same text."""
        samples = {}

        # Different registers
        for register in Register:
            variation = LanguageVariation(register=register)
            result = self.translate_advanced(base_text, variation)
            samples[f"{register.value}_register"] = result.zyntalic_text

        # Different dialects
        for dialect in Dialect:
            if dialect != Dialect.STANDARD:  # Skip standard as it's default
                variation = LanguageVariation(dialect=dialect)
                result = self.translate_advanced(base_text, variation)
                samples[f"{dialect.value}_dialect"] = result.zyntalic_text

        return samples

    def analyze_diachronic_variation(self, text: str) -> dict[str, str]:
        """Show how text might appear in different historical periods."""
        variations = {}

        # Simulate historical changes (very simplified)
        base_result = self.translate_advanced(text)
        modern = base_result.zyntalic_text

        # Old Zyntalic (more conservative)
        old_form = modern
        old_form = old_form.replace('ł', 'l')  # No ł in old form
        old_form = old_form.replace('-', '')   # No morpheme boundaries marked
        old_form = re.sub(r'[a-zA-Z]', '', old_form)  # Pure Hangul
        variations['old_zyntalic'] = old_form

        # Middle Zyntalic (beginning of mixing)
        middle_form = modern
        middle_form = re.sub(r'[a-zA-Z]{3,}', lambda m: m.group()[:2], middle_form)  # Shorter Latin
        variations['middle_zyntalic'] = middle_form

        # Modern Zyntalic (current form)
        variations['modern_zyntalic'] = modern

        # Future Zyntalic (predicted evolution)
        future_form = modern
        future_form = re.sub(r'⟦ctx:[^⟧]+⟧', '⟦++⟧', future_form)  # Simplified context
        variations['future_zyntalic'] = future_form

        return variations

    # -------------------- Test Compatibility Methods --------------------

    def translate_with_analysis(self, text: str) -> TranslationResult:
        """Translate text with full analysis (alias for compatibility)."""
        variation = LanguageVariation(register=Register.FORMAL)
        return self.translate_advanced(text, variation)

    def translate_with_register(self, text: str, register: Register) -> TranslationResult:
        """Translate text with specific register (alias for compatibility)."""
        variation = LanguageVariation(register=register)
        return self.translate_advanced(text, variation)

    def translate_with_dialect(self, text: str, dialect: Dialect) -> TranslationResult:
        """Translate text with specific dialect (alias for compatibility)."""
        variation = LanguageVariation(dialect=dialect)
        options = TranslationOptions(use_dialectal_forms=True)
        return self.translate_advanced(text, variation, options)

# -------------------- Demo Function --------------------

def demo_advanced_features():
    """Demonstrate advanced Zyntalic features."""
    processor = AdvancedZyntalicProcessor()

    print("=== Advanced Zyntalic Language System Demo ===\n")

    test_text = "I love you with all my heart when the sun shines brightly."

    print(f"Original: {test_text}\n")

    # 1. Different registers
    print("=== Register Variations ===")
    for register in [Register.FORMAL, Register.INFORMAL, Register.LITERARY]:
        variation = LanguageVariation(register=register)
        result = processor.translate_advanced(test_text, variation)
        print(f"{register.value:10}: {result.zyntalic_text}")
    print()

    # 2. Different dialects
    print("=== Dialectal Variations ===")
    for dialect in [Dialect.NORTHERN, Dialect.SOUTHERN, Dialect.COASTAL]:
        variation = LanguageVariation(dialect=dialect)
        options = TranslationOptions(use_dialectal_forms=True)
        result = processor.translate_advanced(test_text, variation, options)
        print(f"{dialect.value:10}: {result.zyntalic_text}")
    print()

    # 3. Detailed analysis
    print("=== Detailed Analysis ===")
    variation = LanguageVariation(register=Register.LITERARY)
    result = processor.translate_advanced(test_text, variation)

    print(f"Coherence Score: {result.coherence_score:.3f}")
    print(f"Morphological Complexity: {result.morphological_analysis.get('morphological_complexity', 0):.3f}")
    print(f"Cultural Elements: {', '.join(result.cultural_elements) if result.cultural_elements else 'None'}")
    print()

    # 4. Historical variations
    print("=== Diachronic Variations ===")
    historical = processor.analyze_diachronic_variation(test_text)
    for period, form in historical.items():
        print(f"{period:15}: {form}")

if __name__ == "__main__":
    demo_advanced_features()
