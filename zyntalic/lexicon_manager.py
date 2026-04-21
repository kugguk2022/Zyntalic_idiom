"""
Zyntalic Lexicon Management System

Advanced lexicon management for Zyntalic featuring:
- Semantic networks and word relationships
- Etymology and derivation tracking
- Frequency-based word selection
- Lexical categories and subcategories
- Cross-linguistic borrowing patterns
- Automatic lexicon expansion
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum

from .core import ANCHORS, generate_word, get_rng
from .morphology import MorphologicalProcessor
from .phonology import PhonologicalProcessor, phonological_distance

# -------------------- Lexical Categories --------------------

class LexicalCategory(Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adj"
    ADVERB = "adv"
    PREPOSITION = "prep"
    DETERMINER = "det"
    PRONOUN = "pron"
    CONJUNCTION = "conj"
    INTERJECTION = "interj"
    NUMERAL = "num"

class SemanticField(Enum):
    # Abstract concepts
    EMOTION = "emotion"
    COGNITION = "cognition"
    PHILOSOPHY = "philosophy"
    ETHICS = "ethics"
    TIME = "time"
    SPACE = "space"

    # Concrete domains
    NATURE = "nature"
    HUMAN = "human"
    SOCIETY = "society"
    ARTIFACT = "artifact"
    ANIMAL = "animal"
    PLANT = "plant"

    # Actions
    MOTION = "motion"
    COMMUNICATION = "communication"
    CREATION = "creation"
    DESTRUCTION = "destruction"

class RelationType(Enum):
    SYNONYM = "syn"        # Same meaning
    ANTONYM = "ant"        # Opposite meaning
    HYPERNYM = "hyper"     # More general
    HYPONYM = "hypo"       # More specific
    MERONYM = "mero"       # Part of
    HOLONYM = "holo"       # Has as part
    DERIVED = "deriv"      # Morphologically related
    BORROWED = "borrow"    # Borrowed from another language
    COMPOUND = "comp"      # Compound formation
    METAPHOR = "meta"      # Metaphorical relation

# -------------------- Lexical Entries --------------------

@dataclass
class EtymologyInfo:
    """Etymology and derivation information."""
    source_language: str | None = None
    source_form: str | None = None
    derivation_path: list[str] = field(default_factory=list)
    creation_date: str | None = None
    creation_method: str | None = None  # "generated", "borrowed", "derived"

@dataclass
class SemanticInfo:
    """Semantic information for lexical entries."""
    primary_sense: str
    additional_senses: list[str] = field(default_factory=list)
    semantic_field: SemanticField | None = None
    connotation: str | None = None  # "positive", "negative", "neutral"
    register: str | None = None      # "formal", "informal", "literary", "colloquial"
    frequency: float = 1.0              # Usage frequency (0.0-10.0)

@dataclass
class LexicalRelation:
    """Represents a relationship between lexical entries."""
    target_word: str
    relation_type: RelationType
    strength: float = 1.0  # Strength of relationship (0.0-1.0)
    notes: str | None = None

@dataclass
class LexicalEntry:
    """Complete lexical entry for Zyntalic words."""
    headword: str                    # The Zyntalic word
    category: LexicalCategory
    phonetic_form: str
    morphological_info: dict[str, any] = field(default_factory=dict)
    semantic_info: SemanticInfo = field(default_factory=SemanticInfo)
    etymology: EtymologyInfo = field(default_factory=EtymologyInfo)
    relations: list[LexicalRelation] = field(default_factory=list)
    anchor_weights: list[tuple[str, float]] = field(default_factory=list)
    usage_examples: list[str] = field(default_factory=list)

    def add_relation(self, target: str, relation_type: RelationType,
                    strength: float = 1.0, notes: str | None = None):
        """Add a lexical relation."""
        relation = LexicalRelation(
            target_word=target,
            relation_type=relation_type,
            strength=strength,
            notes=notes
        )
        self.relations.append(relation)

    def get_relations_by_type(self, relation_type: RelationType) -> list[LexicalRelation]:
        """Get all relations of specified type."""
        return [rel for rel in self.relations if rel.relation_type == relation_type]

# -------------------- Lexicon Manager --------------------

class ZyntalicLexicon:
    """Main lexicon management class."""

    def __init__(self, seed: str = "lexicon"):
        self.rng = get_rng(seed)
        self.morphology = MorphologicalProcessor(seed)
        self.phonology = PhonologicalProcessor(seed)

        # Core lexicon storage
        self.entries: dict[str, LexicalEntry] = {}
        self.by_category: dict[LexicalCategory, set[str]] = defaultdict(set)
        self.by_semantic_field: dict[SemanticField, set[str]] = defaultdict(set)

        # Semantic networks
        self.semantic_graph: dict[str, set[str]] = defaultdict(set)
        self.frequency_counts: Counter = Counter()

        # Load/initialize core vocabulary
        self._initialize_core_vocabulary()
        self._build_semantic_networks()

    def _initialize_core_vocabulary(self):
        """Initialize basic vocabulary from anchors."""
        from .core import load_lexicons

        lexicons = load_lexicons()

        # Process anchor-based vocabulary
        for anchor_name in ANCHORS:
            if anchor_name in lexicons:
                anchor_data = lexicons[anchor_name]

                # Add nouns
                if "nouns" in anchor_data:
                    for noun in anchor_data["nouns"][:50]:  # Limit to avoid bloat
                        self._create_entry_from_anchor(noun, LexicalCategory.NOUN, anchor_name)

                # Add verbs
                if "verbs" in anchor_data:
                    for verb in anchor_data["verbs"][:30]:
                        self._create_entry_from_anchor(verb, LexicalCategory.VERB, anchor_name)

                # Add adjectives
                if "adjectives" in anchor_data:
                    for adj in anchor_data["adjectives"][:30]:
                        self._create_entry_from_anchor(adj, LexicalCategory.ADJECTIVE, anchor_name)

    def _create_entry_from_anchor(self, english_word: str, category: LexicalCategory,
                                 anchor: str, frequency: float = 1.0):
        """Create a Zyntalic entry from English anchor word."""
        # Generate Zyntalic form
        zyntalic_word = generate_word(f"{anchor}:{english_word}")

        # Skip if already exists
        if zyntalic_word in self.entries:
            return

        # Create phonetic form
        phonetic = self.phonology.romanize(zyntalic_word)

        # Create semantic info
        semantic_field = self._infer_semantic_field(english_word, category)
        semantic_info = SemanticInfo(
            primary_sense=english_word,
            semantic_field=semantic_field,
            frequency=frequency
        )

        # Create etymology
        etymology = EtymologyInfo(
            source_language="English",
            source_form=english_word,
            creation_method="anchor_based",
            derivation_path=[anchor, english_word]
        )

        # Create entry
        entry = LexicalEntry(
            headword=zyntalic_word,
            category=category,
            phonetic_form=phonetic,
            semantic_info=semantic_info,
            etymology=etymology,
            anchor_weights=[(anchor, 1.0)]
        )

        self.add_entry(entry)

    def _infer_semantic_field(self, word: str, category: LexicalCategory) -> SemanticField | None:
        """Infer semantic field from English word and category."""
        # Emotion words
        emotion_words = {"love", "hate", "joy", "sad", "anger", "fear", "happy", "sorrow"}
        if word.lower() in emotion_words:
            return SemanticField.EMOTION

        # Nature words
        nature_words = {"water", "fire", "earth", "air", "sun", "moon", "star", "tree", "river", "mountain"}
        if word.lower() in nature_words:
            return SemanticField.NATURE

        # Time words
        time_words = {"day", "night", "hour", "minute", "year", "past", "future", "now", "when", "while"}
        if word.lower() in time_words:
            return SemanticField.TIME

        # Motion words (verbs)
        if category == LexicalCategory.VERB:
            motion_words = {"go", "come", "walk", "run", "fly", "move", "travel", "journey"}
            if word.lower() in motion_words:
                return SemanticField.MOTION

        # Default based on category
        if category == LexicalCategory.VERB:
            return SemanticField.COMMUNICATION  # Many verbs are communication
        elif category == LexicalCategory.NOUN:
            return SemanticField.ARTIFACT      # Default for nouns

        return None

    def add_entry(self, entry: LexicalEntry):
        """Add a new lexical entry."""
        self.entries[entry.headword] = entry
        self.by_category[entry.category].add(entry.headword)

        if entry.semantic_info.semantic_field:
            self.by_semantic_field[entry.semantic_info.semantic_field].add(entry.headword)

        # Update frequency
        self.frequency_counts[entry.headword] = entry.semantic_info.frequency

    def get_entry(self, word: str) -> LexicalEntry | None:
        """Get lexical entry for word."""
        return self.entries.get(word)

    def create_derived_word(self, base_word: str, derivation_type: str) -> LexicalEntry | None:
        """Create a derived word from existing base."""
        base_entry = self.get_entry(base_word)
        if not base_entry:
            return None

        # Generate derived form using morphology
        derived_form = self.morphology.derive_word(base_word, derivation_type)

        # Create new entry
        derived_entry = LexicalEntry(
            headword=derived_form.surface_form,
            category=LexicalCategory(derived_form.pos),
            phonetic_form=self.phonology.romanize(derived_form.surface_form),
            semantic_info=SemanticInfo(
                primary_sense=f"{base_entry.semantic_info.primary_sense} ({derivation_type})",
                semantic_field=base_entry.semantic_info.semantic_field,
                frequency=base_entry.semantic_info.frequency * 0.8  # Derived words are less frequent
            ),
            etymology=EtymologyInfo(
                source_form=base_word,
                creation_method="derivation",
                derivation_path=base_entry.etymology.derivation_path + [derivation_type]
            )
        )

        # Add derivation relation
        derived_entry.add_relation(base_word, RelationType.DERIVED)
        base_entry.add_relation(derived_entry.headword, RelationType.DERIVED)

        self.add_entry(derived_entry)
        return derived_entry

    def create_compound_word(self, word1: str, word2: str) -> LexicalEntry | None:
        """Create compound word from two existing words."""
        entry1 = self.get_entry(word1)
        entry2 = self.get_entry(word2)

        if not entry1 or not entry2:
            return None

        # Generate compound form (simple concatenation for now)
        compound_form = word1 + word2

        # Determine category (usually follows second element)
        compound_category = entry2.category

        # Combine semantic information
        compound_semantic = SemanticInfo(
            primary_sense=f"{entry1.semantic_info.primary_sense} {entry2.semantic_info.primary_sense}",
            semantic_field=entry2.semantic_info.semantic_field or entry1.semantic_info.semantic_field,
            frequency=min(entry1.semantic_info.frequency, entry2.semantic_info.frequency)
        )

        compound_entry = LexicalEntry(
            headword=compound_form,
            category=compound_category,
            phonetic_form=self.phonology.romanize(compound_form),
            semantic_info=compound_semantic,
            etymology=EtymologyInfo(
                creation_method="compounding",
                derivation_path=[word1, word2, "compound"]
            )
        )

        # Add compound relations
        compound_entry.add_relation(word1, RelationType.COMPOUND)
        compound_entry.add_relation(word2, RelationType.COMPOUND)

        self.add_entry(compound_entry)
        return compound_entry

    def _build_semantic_networks(self):
        """Build semantic networks between words."""
        # Create phonological similarity networks
        words = list(self.entries.keys())

        for i, word1 in enumerate(words):
            for word2 in words[i+1:]:
                # Calculate phonological distance
                phon_dist = phonological_distance(word1, word2)

                # If phonologically similar, might be semantically related
                if phon_dist < 0.3:
                    self.semantic_graph[word1].add(word2)
                    self.semantic_graph[word2].add(word1)

                    # Add potential synonym relation for very similar words
                    entry1 = self.entries[word1]
                    entry2 = self.entries[word2]

                    if (entry1.category == entry2.category and
                        entry1.semantic_info.semantic_field == entry2.semantic_info.semantic_field):
                        entry1.add_relation(word2, RelationType.SYNONYM, strength=1.0-phon_dist)
                        entry2.add_relation(word1, RelationType.SYNONYM, strength=1.0-phon_dist)

    def find_similar_words(self, word: str, similarity_type: str = "semantic",
                          limit: int = 5) -> list[tuple[str, float]]:
        """Find words similar to given word."""
        entry = self.get_entry(word)
        if not entry:
            return []

        similar = []

        if similarity_type == "semantic":
            # Find words in same semantic field
            if entry.semantic_info.semantic_field:
                candidates = self.by_semantic_field[entry.semantic_info.semantic_field]
                for candidate in candidates:
                    if candidate != word:
                        # Calculate semantic similarity (simplified)
                        cand_entry = self.entries[candidate]
                        similarity = self._semantic_similarity(entry, cand_entry)
                        similar.append((candidate, similarity))

        elif similarity_type == "phonological":
            # Find phonologically similar words
            for candidate in self.entries:
                if candidate != word:
                    phon_dist = phonological_distance(word, candidate)
                    similarity = 1.0 - phon_dist
                    if similarity > 0.5:  # Only include reasonably similar
                        similar.append((candidate, similarity))

        elif similarity_type == "morphological":
            # Find morphologically related words
            for relation in entry.relations:
                if relation.relation_type == RelationType.DERIVED:
                    similar.append((relation.target_word, relation.strength))

        # Sort by similarity and return top results
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]

    def _semantic_similarity(self, entry1: LexicalEntry, entry2: LexicalEntry) -> float:
        """Calculate semantic similarity between entries."""
        score = 0.0

        # Same category bonus
        if entry1.category == entry2.category:
            score += 0.3

        # Same semantic field bonus
        if (entry1.semantic_info.semantic_field and
            entry1.semantic_info.semantic_field == entry2.semantic_info.semantic_field):
            score += 0.5

        # Anchor overlap
        anchors1 = {anchor for anchor, _ in entry1.anchor_weights}
        anchors2 = {anchor for anchor, _ in entry2.anchor_weights}
        overlap = len(anchors1 & anchors2) / len(anchors1 | anchors2) if anchors1 or anchors2 else 0
        score += overlap * 0.2

        return min(score, 1.0)

    def expand_vocabulary(self, target_size: int = 1000):
        """Automatically expand vocabulary to target size."""
        current_size = len(self.entries)

        if current_size >= target_size:
            return

        needed = target_size - current_size
        created = 0

        # Create derived words
        base_words = list(self.entries.keys())
        self.rng.shuffle(base_words)

        derivation_types = ["agent", "instrument", "abstract", "diminutive"]

        for base_word in base_words:
            if created >= needed:
                break

            for deriv_type in derivation_types:
                if created >= needed:
                    break

                derived = self.create_derived_word(base_word, deriv_type)
                if derived:
                    created += 1

        # Create compound words
        if created < needed:
            for i, word1 in enumerate(base_words):
                if created >= needed:
                    break

                for word2 in base_words[i+1:]:
                    if created >= needed:
                        break

                    if self.rng.random() < 0.1:  # 10% chance to create compound
                        compound = self.create_compound_word(word1, word2)
                        if compound:
                            created += 1

    def export_lexicon(self, filename: str):
        """Export lexicon to JSON file."""
        export_data = {
            "metadata": {
                "total_entries": len(self.entries),
                "categories": {cat.value: len(words) for cat, words in self.by_category.items()},
                "semantic_fields": {field.value: len(words) for field, words in self.by_semantic_field.items()}
            },
            "entries": []
        }

        for word, entry in self.entries.items():
            entry_data = {
                "headword": entry.headword,
                "category": entry.category.value,
                "phonetic": entry.phonetic_form,
                "meaning": entry.semantic_info.primary_sense,
                "semantic_field": entry.semantic_info.semantic_field.value if entry.semantic_info.semantic_field else None,
                "frequency": entry.semantic_info.frequency,
                "relations": [
                    {"target": rel.target_word, "type": rel.relation_type.value, "strength": rel.strength}
                    for rel in entry.relations
                ],
                "anchors": entry.anchor_weights
            }
            export_data["entries"].append(entry_data)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def get_vocabulary_stats(self) -> dict[str, any]:
        """Get comprehensive vocabulary statistics."""
        return {
            "total_entries": len(self.entries),
            "by_category": {cat.value: len(words) for cat, words in self.by_category.items()},
            "by_semantic_field": {field.value: len(words) for field, words in self.by_semantic_field.items()},
            "most_frequent": self.frequency_counts.most_common(10),
            "average_frequency": sum(self.frequency_counts.values()) / len(self.frequency_counts) if self.frequency_counts else 0,
            "relation_types": self._count_relations(),
            "phonetic_diversity": self._measure_phonetic_diversity(),
        }

    def _count_relations(self) -> dict[str, int]:
        """Count relations by type."""
        relation_counts = Counter()
        for entry in self.entries.values():
            for relation in entry.relations:
                relation_counts[relation.relation_type.value] += 1
        return dict(relation_counts)

    def _measure_phonetic_diversity(self) -> float:
        """Measure phonetic diversity of the lexicon."""
        if len(self.entries) < 2:
            return 0.0

        # Calculate average pairwise phonetic distance (sample for efficiency)
        words = list(self.entries.keys())
        if len(words) > 100:
            words = self.rng.sample(words, 100)

        total_distance = 0.0
        comparisons = 0

        for i, word1 in enumerate(words):
            for word2 in words[i+1:]:
                total_distance += phonological_distance(word1, word2)
                comparisons += 1

        return total_distance / comparisons if comparisons > 0 else 0.0

    # -------------------- Test Compatibility Methods --------------------

    def find_related_words(self, headword: str, relation_type: RelationType) -> list[str]:
        """Find words related to the given word by relation type (alias for compatibility)."""
        entry = self.get_entry(headword)
        if not entry:
            return []

        related = []
        for relation in entry.relations:
            if relation.relation_type == relation_type:
                related.append(relation.target_word)

        return related

# -------------------- Demo Function --------------------

def demo_lexicon():
    """Demonstrate the lexicon management system."""
    lexicon = ZyntalicLexicon()

    print("=== Zyntalic Lexicon Management Demo ===\n")

    # Show initial stats
    stats = lexicon.get_vocabulary_stats()
    print(f"Initial vocabulary: {stats['total_entries']} entries")
    print(f"Categories: {stats['by_category']}")
    print(f"Semantic fields: {stats['by_semantic_field']}")
    print(f"Phonetic diversity: {stats['phonetic_diversity']:.3f}\n")

    # Show some entries
    print("Sample entries:")
    sample_words = list(lexicon.entries.keys())[:5]
    for word in sample_words:
        entry = lexicon.entries[word]
        print(f"  {word:15} [{entry.phonetic_form:15}] {entry.category.value:8} '{entry.semantic_info.primary_sense}'")

    # Create derived words
    print("\nCreating derived words...")
    if sample_words:
        base = sample_words[0]
        derived = lexicon.create_derived_word(base, "agent")
        if derived:
            print(f"  {base} → {derived.headword} (agent)")

    # Find similar words
    if sample_words:
        word = sample_words[0]
        similar = lexicon.find_similar_words(word, "semantic", limit=3)
        print(f"\nWords similar to '{word}':")
        for sim_word, score in similar:
            print(f"  {sim_word:15} (similarity: {score:.3f})")

    # Expand vocabulary
    print("\nExpanding vocabulary...")
    lexicon.expand_vocabulary(200)
    new_stats = lexicon.get_vocabulary_stats()
    print(f"New vocabulary size: {new_stats['total_entries']} entries")

if __name__ == "__main__":
    demo_lexicon()
