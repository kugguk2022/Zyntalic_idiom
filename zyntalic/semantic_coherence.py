"""
Zyntalic Semantic Coherence System

Advanced semantic processing for maintaining coherence in Zyntalic featuring:
- Thematic consistency across translations
- Discourse-level semantic tracking
- Conceptual metaphor preservation
- Cross-sentence coherence
- Semantic field activation
- Context-sensitive meaning selection
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum

from .core import ANCHORS, generate_embedding
from .lexicon_manager import LexicalCategory, SemanticField, ZyntalicLexicon
from .utils.rng import get_rng

# -------------------- Semantic Structures --------------------

class CoherenceLevel(Enum):
    LEXICAL = "lexical"      # Individual word meanings
    PROPOSITIONAL = "prop"   # Sentence-level meaning
    DISCOURSE = "discourse"  # Cross-sentence coherence
    THEMATIC = "thematic"    # Overall theme/topic

class MetaphorType(Enum):
    CONCEPTUAL = "conceptual"    # A is B (love is war)
    STRUCTURAL = "structural"    # A is like B in structure
    ORIENTATIONAL = "orient"     # Up/down, in/out metaphors
    ONTOLOGICAL = "ontological"  # Events as objects, etc.

@dataclass
class SemanticFrame:
    """Represents semantic frame/schema."""
    frame_name: str
    core_elements: list[str]       # Required semantic roles
    peripheral_elements: list[str]  # Optional semantic roles
    typical_fillers: dict[str, list[str]] = field(default_factory=dict)

@dataclass
class ConceptualMapping:
    """Represents conceptual metaphor mapping."""
    source_domain: str
    target_domain: str
    mappings: dict[str, str]  # source concept -> target concept
    metaphor_type: MetaphorType
    strength: float = 1.0

@dataclass
class SemanticContext:
    """Tracks semantic context across discourse."""
    active_frames: set[str] = field(default_factory=set)
    active_fields: dict[SemanticField, float] = field(default_factory=dict)
    metaphor_chains: list[ConceptualMapping] = field(default_factory=list)
    entity_mentions: dict[str, int] = field(default_factory=dict)
    coherence_links: list[tuple[str, str, str]] = field(default_factory=list)  # (sent1, sent2, link_type)

@dataclass
class SemanticAnalysis:
    """Result of semantic analysis."""
    def __init__(self, coherence_score=0.0, primary_theme=None, semantic_fields=None,
                 conceptual_metaphors=None, anchor_activation=None, discourse_entities=None):
        self.coherence_score = coherence_score
        self.primary_theme = primary_theme
        self.semantic_fields = semantic_fields or {}
        self.conceptual_metaphors = conceptual_metaphors or []
        self.anchor_activation = anchor_activation or {}
        self.discourse_entities = discourse_entities or []

    @property
    def metaphor_chains(self) -> list[ConceptualMapping]:
        """Alias for conceptual_metaphors for compatibility."""
        return self.conceptual_metaphors

# -------------------- Semantic Coherence Processor --------------------

class SemanticCoherenceProcessor:
    """Main class for semantic coherence processing."""

    def __init__(self, lexicon: ZyntalicLexicon | None = None, seed: str = "semantics"):
        self.rng = get_rng(seed)
        self.lexicon = lexicon or ZyntalicLexicon(seed)

        # Initialize semantic resources
        self._build_semantic_frames()
        self._build_conceptual_metaphors()
        self._build_coherence_patterns()

        # Discourse state
        self.discourse_context = SemanticContext()
        self.sentence_history: list[str] = []
        self.theme_tracking: dict[str, float] = {}

    def _build_semantic_frames(self):
        """Build library of semantic frames."""
        self.frames = {
            # Motion frame
            "motion": SemanticFrame(
                frame_name="motion",
                core_elements=["mover", "path", "goal"],
                peripheral_elements=["manner", "speed", "instrument"],
                typical_fillers={
                    "mover": ["person", "animal", "object"],
                    "path": ["road", "river", "sky"],
                    "goal": ["place", "destination"]
                }
            ),

            # Communication frame
            "communication": SemanticFrame(
                frame_name="communication",
                core_elements=["speaker", "addressee", "message"],
                peripheral_elements=["medium", "topic", "manner"],
                typical_fillers={
                    "speaker": ["person", "authority", "voice"],
                    "addressee": ["audience", "listener", "reader"],
                    "message": ["words", "information", "story"]
                }
            ),

            # Creation frame
            "creation": SemanticFrame(
                frame_name="creation",
                core_elements=["creator", "created_entity"],
                peripheral_elements=["material", "purpose", "method"],
                typical_fillers={
                    "creator": ["artist", "god", "person"],
                    "created_entity": ["work", "object", "idea"]
                }
            ),

            # Conflict frame
            "conflict": SemanticFrame(
                frame_name="conflict",
                core_elements=["protagonist", "antagonist", "issue"],
                peripheral_elements=["battlefield", "weapon", "stakes"],
                typical_fillers={
                    "protagonist": ["hero", "side", "force"],
                    "antagonist": ["enemy", "opposition", "evil"],
                    "issue": ["territory", "principle", "resource"]
                }
            ),

            # Love/Relationship frame
            "relationship": SemanticFrame(
                frame_name="relationship",
                core_elements=["experiencer", "target", "emotion"],
                peripheral_elements=["intensity", "duration", "cause"],
                typical_fillers={
                    "experiencer": ["lover", "person", "heart"],
                    "target": ["beloved", "object", "ideal"],
                    "emotion": ["love", "affection", "devotion"]
                }
            )
        }

    def _build_conceptual_metaphors(self):
        """Build library of conceptual metaphors."""
        self.metaphors = {
            "love_is_journey": ConceptualMapping(
                source_domain="journey",
                target_domain="love",
                mappings={
                    "travelers": "lovers",
                    "destination": "life_goals",
                    "obstacles": "difficulties",
                    "path": "relationship"
                },
                metaphor_type=MetaphorType.CONCEPTUAL
            ),

            "argument_is_war": ConceptualMapping(
                source_domain="war",
                target_domain="argument",
                mappings={
                    "opponents": "arguers",
                    "weapons": "evidence",
                    "battle": "debate",
                    "victory": "winning"
                },
                metaphor_type=MetaphorType.CONCEPTUAL
            ),

            "life_is_theatre": ConceptualMapping(
                source_domain="theatre",
                target_domain="life",
                mappings={
                    "actors": "people",
                    "stage": "world",
                    "script": "destiny",
                    "performance": "behavior"
                },
                metaphor_type=MetaphorType.CONCEPTUAL
            ),

            "time_is_space": ConceptualMapping(
                source_domain="space",
                target_domain="time",
                mappings={
                    "forward": "future",
                    "backward": "past",
                    "distance": "duration",
                    "movement": "passage"
                },
                metaphor_type=MetaphorType.ORIENTATIONAL
            )
        }

    def _build_coherence_patterns(self):
        """Build patterns for maintaining coherence."""
        self.coherence_patterns = {
            # Lexical cohesion patterns
            "repetition": r'\b(\w+)\b.*\b\1\b',           # Word repetition
            "synonymy": "semantic_similarity",             # Synonym chains
            "antonymy": "semantic_opposition",             # Contrast patterns

            # Reference patterns
            "pronoun": r'\b(he|she|it|they|this|that)\b',  # Pronominal reference
            "definite": r'\bthe\s+\w+',                   # Definite reference

            # Discourse markers
            "temporal": r'\b(when|then|after|before|while|during)\b',
            "causal": r'\b(because|since|therefore|thus|so)\b',
            "adversative": r'\b(but|however|although|yet|nevertheless)\b',
            "additive": r'\b(and|also|furthermore|moreover|additionally)\b'
        }

    def analyze_semantic_coherence(self, text: str) -> SemanticAnalysis:
        """Analyze semantic coherence of input text."""
        sentences = self._split_sentences(text)
        analysis = SemanticAnalysis()

        # Analyze each sentence
        sentence_analyses = []
        for sent in sentences:
            sent_analysis = self._analyze_sentence_semantics(sent)
            sentence_analyses.append(sent_analysis)

            # Update discourse context
            self._update_discourse_context(sent, sent_analysis)

        # Compute overall analysis
        analysis.primary_theme = self._identify_primary_theme(sentence_analyses)
        analysis.semantic_fields = self._aggregate_semantic_fields(sentence_analyses)
        analysis.conceptual_metaphors = self._detect_metaphor_chains(sentence_analyses)
        analysis.coherence_score = self._compute_coherence_score(sentence_analyses)
        analysis.anchor_activation = self._compute_anchor_activation(text)

        return analysis

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _analyze_sentence_semantics(self, sentence: str) -> dict[str, any]:
        """Analyze semantics of individual sentence."""
        words = sentence.lower().split()

        analysis = {
            'sentence': sentence,
            'semantic_fields': defaultdict(float),
            'active_frames': set(),
            'entities': [],
            'metaphor_indicators': [],
            'anchor_weights': {}
        }

        # Analyze words
        for word in words:
            # Check if word exists in lexicon
            entry = self.lexicon.get_entry(word)
            if entry:
                if entry.semantic_info.semantic_field:
                    analysis['semantic_fields'][entry.semantic_info.semantic_field] += 1.0

                # Check for frame activation
                for frame_name, frame in self.frames.items():
                    if word in frame.typical_fillers.get('mover', []) + frame.typical_fillers.get('speaker', []) + frame.typical_fillers.get('creator', []):
                        analysis['active_frames'].add(frame_name)

                # Add to entities if noun
                if entry.category == LexicalCategory.NOUN:
                    analysis['entities'].append(word)

        # Detect metaphor indicators
        analysis['metaphor_indicators'] = self._detect_metaphor_indicators(sentence)

        # Get anchor weights for sentence
        analysis['anchor_weights'] = self._get_sentence_anchor_weights(sentence)

        return analysis

    def _detect_metaphor_indicators(self, sentence: str) -> list[str]:
        """Detect linguistic indicators of metaphor."""
        indicators = []

        # Look for metaphor signal words
        metaphor_signals = ['like', 'as', 'seems', 'appears', 'through', 'beyond', 'within']
        words = sentence.lower().split()

        for signal in metaphor_signals:
            if signal in words:
                indicators.append(signal)

        # Look for domain mixing (simplified)
        # If we have words from very different semantic fields, might indicate metaphor
        fields_present = set()
        for word in words:
            entry = self.lexicon.get_entry(word)
            if entry and entry.semantic_info.semantic_field:
                fields_present.add(entry.semantic_info.semantic_field)

        # If we have both abstract and concrete domains, possible metaphor
        abstract_fields = {SemanticField.EMOTION, SemanticField.COGNITION, SemanticField.PHILOSOPHY}
        concrete_fields = {SemanticField.NATURE, SemanticField.ARTIFACT, SemanticField.ANIMAL}

        if (fields_present & abstract_fields) and (fields_present & concrete_fields):
            indicators.append("domain_mixing")

        return indicators

    def _get_sentence_anchor_weights(self, sentence: str) -> dict[str, float]:
        """Get anchor weights for sentence."""
        # Use existing anchor weighting system
        try:
            embedding, anchor_weights = generate_embedding(sentence)
            return {anchor: weight for anchor, weight in anchor_weights}
        except Exception:
            return {}

    def _update_discourse_context(self, sentence: str, analysis: dict[str, any]):
        """Update discourse context with new sentence."""
        # Add to sentence history
        self.sentence_history.append(sentence)

        # Update active semantic fields
        for sem_field, weight in analysis['semantic_fields'].items():
            if sem_field in self.discourse_context.active_fields:
                # Decay previous weight and add new
                self.discourse_context.active_fields[sem_field] = \
                    self.discourse_context.active_fields[sem_field] * 0.8 + weight
            else:
                self.discourse_context.active_fields[sem_field] = weight

        # Update active frames
        self.discourse_context.active_frames.update(analysis['active_frames'])

        # Track entity mentions
        for entity in analysis['entities']:
            self.discourse_context.entity_mentions[entity] = \
                self.discourse_context.entity_mentions.get(entity, 0) + 1

    def _identify_primary_theme(self, sentence_analyses: list[dict]) -> str | None:
        """Identify primary theme from sentence analyses."""
        # Aggregate semantic field activations
        field_totals = defaultdict(float)
        for analysis in sentence_analyses:
            for sem_field, weight in analysis['semantic_fields'].items():
                field_totals[sem_field] += weight

        if not field_totals:
            return None

        # Find most activated field
        primary_field = max(field_totals.items(), key=lambda x: x[1])[0]

        # Map semantic field to theme
        field_to_theme = {
            SemanticField.EMOTION: "emotional_experience",
            SemanticField.PHILOSOPHY: "philosophical_inquiry",
            SemanticField.NATURE: "natural_world",
            SemanticField.TIME: "temporal_experience",
            SemanticField.MOTION: "journey_movement",
            SemanticField.COMMUNICATION: "dialogue_expression"
        }

        return field_to_theme.get(primary_field, primary_field.value)

    def _aggregate_semantic_fields(self, sentence_analyses: list[dict]) -> dict[SemanticField, float]:
        """Aggregate semantic field activations."""
        aggregated = defaultdict(float)

        for analysis in sentence_analyses:
            for sem_field, weight in analysis['semantic_fields'].items():
                aggregated[sem_field] += weight

        # Normalize by number of sentences
        if sentence_analyses:
            for sem_field in aggregated:
                aggregated[sem_field] /= len(sentence_analyses)

        return dict(aggregated)

    def _detect_metaphor_chains(self, sentence_analyses: list[dict]) -> list[ConceptualMapping]:
        """Detect conceptual metaphor chains across sentences."""
        detected_metaphors = []

        # Look for metaphor indicators across sentences
        all_indicators = []
        for analysis in sentence_analyses:
            all_indicators.extend(analysis['metaphor_indicators'])

        # If we have domain mixing indicators, check known metaphors
        if "domain_mixing" in all_indicators:
            # Check which conceptual metaphors might be active
            for metaphor in self.metaphors.values():
                # Simplified detection - check if both domains are present
                source_present = False
                target_present = False

                for analysis in sentence_analyses:
                    fields = set(analysis['semantic_fields'].keys())

                    # Map domains to semantic fields (simplified)
                    if metaphor.source_domain in ['journey', 'war', 'space']:
                        if SemanticField.MOTION in fields:
                            source_present = True
                    elif metaphor.source_domain == 'theatre':
                        if SemanticField.SOCIETY in fields:
                            source_present = True

                    if metaphor.target_domain in ['love', 'argument', 'life', 'time']:
                        if SemanticField.EMOTION in fields or SemanticField.PHILOSOPHY in fields:
                            target_present = True

                if source_present and target_present:
                    detected_metaphors.append(metaphor)

        return detected_metaphors

    def _compute_coherence_score(self, sentence_analyses: list[dict]) -> float:
        """Compute overall coherence score."""
        if len(sentence_analyses) < 2:
            return 1.0  # Single sentence is trivially coherent

        coherence_factors = []

        # Factor 1: Semantic field consistency
        field_consistency = self._measure_field_consistency(sentence_analyses)
        coherence_factors.append(field_consistency)

        # Factor 2: Entity coherence (repeated mentions)
        entity_coherence = self._measure_entity_coherence()
        coherence_factors.append(entity_coherence)

        # Factor 3: Anchor consistency
        anchor_coherence = self._measure_anchor_consistency(sentence_analyses)
        coherence_factors.append(anchor_coherence)

        # Factor 4: Frame consistency
        frame_coherence = self._measure_frame_consistency(sentence_analyses)
        coherence_factors.append(frame_coherence)

        # Average the factors
        return sum(coherence_factors) / len(coherence_factors)

    def _measure_field_consistency(self, sentence_analyses: list[dict]) -> float:
        """Measure semantic field consistency across sentences."""
        if not sentence_analyses:
            return 1.0

        # Get all fields mentioned
        all_fields = set()
        for analysis in sentence_analyses:
            all_fields.update(analysis['semantic_fields'].keys())

        if not all_fields:
            return 0.5  # No clear semantic content

        # Calculate overlap between consecutive sentences
        overlaps = []
        for i in range(len(sentence_analyses) - 1):
            fields1 = set(sentence_analyses[i]['semantic_fields'].keys())
            fields2 = set(sentence_analyses[i+1]['semantic_fields'].keys())

            if fields1 and fields2:
                overlap = len(fields1 & fields2) / len(fields1 | fields2)
                overlaps.append(overlap)

        return sum(overlaps) / len(overlaps) if overlaps else 0.5

    def _measure_entity_coherence(self) -> float:
        """Measure entity mention coherence."""
        mentions = self.discourse_context.entity_mentions

        if not mentions:
            return 0.5  # No entities to track

        # Entities mentioned multiple times contribute to coherence
        repeated_entities = sum(1 for count in mentions.values() if count > 1)
        total_entities = len(mentions)

        return repeated_entities / total_entities if total_entities > 0 else 0.5

    def _measure_anchor_consistency(self, sentence_analyses: list[dict]) -> float:
        """Measure anchor consistency across sentences."""
        if not sentence_analyses:
            return 1.0

        # Get anchor weights for each sentence
        all_anchors = set()
        sentence_anchors = []

        for analysis in sentence_analyses:
            anchors = set(analysis['anchor_weights'].keys())
            all_anchors.update(anchors)
            sentence_anchors.append(anchors)

        if len(all_anchors) < 2:
            return 1.0  # Trivially consistent

        # Calculate pairwise anchor overlap
        overlaps = []
        for i in range(len(sentence_anchors) - 1):
            anchors1 = sentence_anchors[i]
            anchors2 = sentence_anchors[i+1]

            if anchors1 and anchors2:
                overlap = len(anchors1 & anchors2) / len(anchors1 | anchors2)
                overlaps.append(overlap)

        return sum(overlaps) / len(overlaps) if overlaps else 0.5

    def _measure_frame_consistency(self, sentence_analyses: list[dict]) -> float:
        """Measure semantic frame consistency."""
        all_frames = []
        for analysis in sentence_analyses:
            all_frames.extend(list(analysis['active_frames']))

        if not all_frames:
            return 0.5  # No frames detected

        # Calculate frame repetition rate
        frame_counts = Counter(all_frames)
        repeated_frames = sum(1 for count in frame_counts.values() if count > 1)
        unique_frames = len(frame_counts)

        return repeated_frames / unique_frames if unique_frames > 0 else 0.5

    def _compute_anchor_activation(self, text: str) -> dict[str, float]:
        """Compute anchor activation for entire text."""
        try:
            embedding, anchor_weights = generate_embedding(text)
            return {anchor: weight for anchor, weight in anchor_weights}
        except Exception:
            return {}

    def ensure_translation_coherence(self, english_text: str, zyntalic_translation: str) -> tuple[str, float]:
        """Ensure semantic coherence between English and Zyntalic."""
        # Analyze both texts
        english_analysis = self.analyze_semantic_coherence(english_text)
        zyntalic_analysis = self.analyze_semantic_coherence(zyntalic_translation)

        # Compute coherence between source and target
        coherence_score = self._cross_lingual_coherence(english_analysis, zyntalic_analysis)

        # If coherence is low, suggest improvements
        if coherence_score < 0.6:
            improved_translation = self._improve_translation_coherence(
                english_text, zyntalic_translation, english_analysis
            )
            return improved_translation, coherence_score

        return zyntalic_translation, coherence_score

    def _cross_lingual_coherence(self, english_analysis: SemanticAnalysis,
                                zyntalic_analysis: SemanticAnalysis) -> float:
        """Compute coherence between English and Zyntalic analyses."""
        factors = []

        # Theme consistency
        theme_match = 1.0 if english_analysis.primary_theme == zyntalic_analysis.primary_theme else 0.3
        factors.append(theme_match)

        # Semantic field overlap
        english_fields = set(english_analysis.semantic_fields.keys())
        zyntalic_fields = set(zyntalic_analysis.semantic_fields.keys())

        if english_fields and zyntalic_fields:
            field_overlap = len(english_fields & zyntalic_fields) / len(english_fields | zyntalic_fields)
            factors.append(field_overlap)
        else:
            factors.append(0.5)

        # Anchor activation similarity
        english_anchors = english_analysis.anchor_activation
        zyntalic_anchors = zyntalic_analysis.anchor_activation

        if english_anchors and zyntalic_anchors:
            # Calculate cosine similarity of anchor vectors
            common_anchors = set(english_anchors.keys()) & set(zyntalic_anchors.keys())
            if common_anchors:
                dot_product = sum(english_anchors[a] * zyntalic_anchors[a] for a in common_anchors)
                norm_en = sum(w**2 for w in english_anchors.values())**0.5
                norm_zy = sum(w**2 for w in zyntalic_anchors.values())**0.5

                if norm_en > 0 and norm_zy > 0:
                    anchor_similarity = dot_product / (norm_en * norm_zy)
                    factors.append(anchor_similarity)

        return sum(factors) / len(factors) if factors else 0.5

    def _improve_translation_coherence(self, english_text: str, zyntalic_translation: str,
                                     english_analysis: SemanticAnalysis) -> str:
        """Improve translation coherence by adjusting Zyntalic output."""
        # This is a simplified version - real implementation would be more sophisticated

        # If primary theme is missing, try to incorporate theme-relevant anchors
        if english_analysis.primary_theme:
            self._get_theme_relevant_anchors(english_analysis.primary_theme)

            # Add a context marker that emphasizes the theme
            theme_marker = f"⟦theme:{english_analysis.primary_theme}⟧"

            # Insert theme marker before existing context
            if "⟦ctx:" in zyntalic_translation:
                parts = zyntalic_translation.split("⟦ctx:")
                improved = parts[0].strip() + " " + theme_marker + " ⟦ctx:" + parts[1]
            else:
                improved = zyntalic_translation + " " + theme_marker

            return improved

        return zyntalic_translation

    def _get_theme_relevant_anchors(self, theme: str) -> list[str]:
        """Get anchors most relevant to given theme."""
        theme_to_anchors = {
            "emotional_experience": ["Shakespeare_Sonnets", "Austen_PridePrejudice"],
            "philosophical_inquiry": ["Plato_Republic", "Descartes_Meditations", "Spinoza_Ethics"],
            "natural_world": ["Darwin_OriginOfSpecies", "Homer_Odyssey"],
            "journey_movement": ["Homer_Odyssey", "Dante_DivineComedy"],
            "dialogue_expression": ["Plato_Republic", "Goethe_Faust"]
        }

        return theme_to_anchors.get(theme, ANCHORS[:3])

    # -------------------- Test Compatibility Methods --------------------

    def analyze_coherence(self, text: str) -> float:
        """Analyze semantic coherence of text (alias for compatibility)."""
        analysis = self.analyze_semantic_coherence(text)
        return analysis.coherence_score

    def detect_metaphors(self, text: str) -> list[ConceptualMapping]:
        """Detect metaphors in text (alias for compatibility)."""
        analysis = self.analyze_semantic_coherence(text)
        return analysis.metaphor_chains

    def compute_anchor_weights(self, text: str) -> dict[str, float]:
        """Compute anchor weights for text (alias for compatibility)."""
        return self._compute_anchor_activation(text)

# -------------------- Demo Function --------------------

def demo_semantic_coherence():
    """Demonstrate semantic coherence system."""
    processor = SemanticCoherenceProcessor()

    print("=== Zyntalic Semantic Coherence System Demo ===\n")

    test_texts = [
        "I love you with all my heart.",
        "The sun rises in the east every morning. Birds sing as flowers bloom in the garden.",
        "War is hell. Soldiers fight battles with courage and honor. Victory comes to those who persist.",
        "Time flows like a river. Past moments drift away while future possibilities approach.",
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"{i}. Text: {text}")

        analysis = processor.analyze_semantic_coherence(text)

        print(f"   Theme: {analysis.primary_theme}")
        print(f"   Coherence Score: {analysis.coherence_score:.3f}")

        if analysis.semantic_fields:
            fields_str = ", ".join(f"{field.value}({weight:.2f})"
                                 for field, weight in analysis.semantic_fields.items())
            print(f"   Semantic Fields: {fields_str}")

        if analysis.conceptual_metaphors:
            metaphors_str = ", ".join(f"{m.source_domain}→{m.target_domain}"
                                    for m in analysis.conceptual_metaphors)
            print(f"   Metaphors: {metaphors_str}")

        if analysis.anchor_activation:
            top_anchors = sorted(analysis.anchor_activation.items(),
                               key=lambda x: x[1], reverse=True)[:3]
            anchors_str = ", ".join(f"{anchor}({weight:.3f})"
                                  for anchor, weight in top_anchors)
            print(f"   Top Anchors: {anchors_str}")

        print()


# -------------------- Demo Function --------------------
    demo_semantic_coherence()
