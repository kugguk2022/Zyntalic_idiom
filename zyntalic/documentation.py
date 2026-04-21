"""
Zyntalic Language Documentation Generator

Comprehensive documentation tools for Zyntalic including:
- Grammar reference generation
- Lexicon documentation
- Tutorial generation
- Linguistic analysis reports
- Interactive examples
- Cross-reference systems
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .advanced_features import AdvancedZyntalicProcessor
from .core import ANCHORS
from .enhanced_syntax import ZyntalicSyntaxProcessor
from .lexicon_manager import ZyntalicLexicon
from .morphology import Case, MorphologicalProcessor, Tense
from .phonology import HANGUL_CONSONANTS, LATIN_CONSONANTS, PhonologicalProcessor
from .semantic_coherence import SemanticCoherenceProcessor

# -------------------- Documentation Types --------------------

class DocumentationType(Enum):
    GRAMMAR_REFERENCE = "grammar"
    LEXICON = "lexicon"
    TUTORIAL = "tutorial"
    PHONOLOGY_GUIDE = "phonology"
    MORPHOLOGY_GUIDE = "morphology"
    SYNTAX_GUIDE = "syntax"
    CULTURAL_GUIDE = "culture"
    QUICK_REFERENCE = "quick_ref"

@dataclass
class DocumentationSection:
    """Represents a section of documentation."""
    title: str
    content: str
    subsections: list[DocumentationSection] = field(default_factory=list)
    examples: list[dict[str, str]] = field(default_factory=list)
    cross_references: list[str] = field(default_factory=list)

    def add_example(self, zyntalic: str, english: str, explanation: str = ""):
        """Add an example to this section."""
        self.examples.append({
            'zyntalic': zyntalic,
            'english': english,
            'explanation': explanation
        })

    def to_markdown(self, level: int = 1) -> str:
        """Convert section to Markdown format."""
        md = []

        # Title
        md.append(f"{'#' * level} {self.title}\n")

        # Content
        md.append(f"{self.content}\n")

        # Examples
        if self.examples:
            md.append("### Examples\n")
            for i, example in enumerate(self.examples, 1):
                md.append(f"{i}. **Zyntalic:** {example['zyntalic']}")
                md.append(f"   **English:** {example['english']}")
                if example['explanation']:
                    md.append(f"   **Note:** {example['explanation']}")
                md.append("")

        # Subsections
        for subsection in self.subsections:
            md.append(subsection.to_markdown(level + 1))

        # Cross-references
        if self.cross_references:
            md.append("### See Also\n")
            for ref in self.cross_references:
                md.append(f"- {ref}")
            md.append("")

        return "\n".join(md)

# -------------------- Documentation Generator --------------------

class ZyntalicDocumentationGenerator:
    """Main class for generating Zyntalic documentation."""

    def __init__(self):
        # Initialize all language systems
        self.morphology = MorphologicalProcessor()
        self.phonology = PhonologicalProcessor()
        self.syntax = ZyntalicSyntaxProcessor()
        self.lexicon = ZyntalicLexicon()
        self.semantics = SemanticCoherenceProcessor(self.lexicon)
        self.advanced = AdvancedZyntalicProcessor()

        # Documentation tracking
        self.generated_docs: dict[str, DocumentationSection] = {}
        self.cross_references: dict[str, set[str]] = {}

    def generate_complete_documentation(self, output_dir: str = "zyntalic_docs"):
        """Generate complete documentation suite."""
        os.makedirs(output_dir, exist_ok=True)

        # Generate all documentation types
        docs = {
            'grammar': self.generate_grammar_reference(),
            'phonology': self.generate_phonology_guide(),
            'morphology': self.generate_morphology_guide(),
            'syntax': self.generate_syntax_guide(),
            'lexicon': self.generate_lexicon_documentation(),
            'semantics': self.generate_semantics_guide(),
            'culture': self.generate_cultural_guide(),
            'tutorial': self.generate_beginner_tutorial(),
            'quick_ref': self.generate_quick_reference()
        }

        # Write individual files
        for doc_type, doc in docs.items():
            filename = os.path.join(output_dir, f"{doc_type}.md")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(doc.to_markdown())

        # Generate master index
        self._generate_index(docs, output_dir)

        print(f"Documentation generated in {output_dir}/")
        return output_dir

    def generate_grammar_reference(self) -> DocumentationSection:
        """Generate comprehensive grammar reference."""
        grammar = DocumentationSection(
            "Zyntalic Grammar Reference",
            "Complete reference for Zyntalic grammar, covering all aspects of the language structure."
        )

        # Word Order Section
        word_order = DocumentationSection(
            "Word Order (S-O-V-C)",
            """Zyntalic follows a **Subject-Object-Verb-Context** (S-O-V-C) word order, which differs from English's Subject-Verb-Object pattern.

**Structure:**
- **Subject** (S): The doer of the action
- **Object** (O): The receiver of the action
- **Verb** (V): The action itself
- **Context** (C): Additional information (time, place, manner, etc.)

The Context position is unique to Zyntalic and includes both embedded clauses and the distinctive Korean-style context tail marked with ⟦ctx:...⟧."""
        )

        # Add examples for word order
        word_order.add_example(
            "나 너 사랑해 ⟦ctx:han=뽇뎻; lemma=사랑; pos=verb; anchors=Shakespeare_Sonnets⟧",
            "I love you",
            "Subject (나) + Object (너) + Verb (사랑해) + Context block"
        )

        word_order.add_example(
            "고양이 정원에서 걸어 ⟦ctx:han=걷기; lemma=걸; pos=verb; anchors=Nature⟧",
            "The cat walks in the garden",
            "Subject (고양이) + Location (정원에서) + Verb (걸어) + Context"
        )

        grammar.subsections.append(word_order)

        # Case System Section
        case_system = DocumentationSection(
            "Case System",
            """Zyntalic uses a six-case system with vowel harmony determining the exact form of case suffixes.

**Cases:**
1. **Nominative** (Subject marker) - unmarked
2. **Accusative** (Direct object) - -eł/-oł
3. **Genitive** (Possession) - -nek/-nok
4. **Dative** (Indirect object) - -re/-ra
5. **Locative** (Location) - -ben/-ban
6. **Instrumental** (Means/method) - -vel/-val

**Vowel Harmony:**
- Front vowels (e, é, i, í, ö, ő, ü, ű) take front variants (-eł, -nek, -re, -ben, -vel)
- Back vowels (a, á, o, ó, u, ú) take back variants (-oł, -nok, -ra, -ban, -val)"""
        )

        # Add case examples
        for case in Case:
            if case == Case.NOMINATIVE:
                continue
            example_word = "뚧홧깍"  # Example root
            inflected = self.morphology.inflect_noun(example_word, case=case)
            case_system.add_example(
                inflected.surface_form,
                f"Root word in {case.value} case",
                inflected.gloss
            )

        grammar.subsections.append(case_system)

        # Add cross-references
        grammar.cross_references = ["Morphology Guide", "Syntax Guide", "Phonology Guide"]

        return grammar

    def generate_phonology_guide(self) -> DocumentationSection:
        """Generate phonology and sound system guide."""
        phonology = DocumentationSection(
            "Zyntalic Phonology Guide",
            "Guide to the sound system of Zyntalic, including the mixed Hangul-Latin script system."
        )

        # Script System
        script_section = DocumentationSection(
            "Mixed Script System",
            """Zyntalic uses a unique mixed script system combining Korean Hangul and Latin characters.

**Script Distribution:**
- **Nouns**: 85% Hangul, 15% Latin
- **Verbs**: 85% Latin, 15% Hangul
- **Other parts of speech**: 50/50 distribution

This creates a distinctive visual pattern where nouns tend to appear in Korean script while verbs appear in Latin script, though mixing occurs in both directions."""
        )

        # Add script examples
        script_section.add_example("뚧홧깍", "house (noun)", "Hangul-heavy noun")
        script_section.add_example("mówić", "to speak (verb)", "Latin-heavy verb")
        script_section.add_example("깍speak뚧", "speaking house", "Mixed script compound")

        phonology.subsections.append(script_section)

        # Consonant System
        consonants = DocumentationSection(
            "Consonant Inventory",
            f"""Zyntalic has a rich consonant system drawing from both Korean and Polish phonologies.

**Hangul Consonants ({len(HANGUL_CONSONANTS)}):**
{self._format_phoneme_table(HANGUL_CONSONANTS)}

**Latin Consonants ({len(LATIN_CONSONANTS)}):**
{self._format_phoneme_table(LATIN_CONSONANTS)}

**Consonant Clusters:**
Zyntalic allows complex consonant clusters, especially in Latin-script portions. Common patterns include:
- Initial: sp-, st-, sk-, szp-, szk-
- Final: -nt, -mp, -ŋk, -st"""
        )

        phonology.subsections.append(consonants)

        # Sound Changes
        sound_changes = DocumentationSection(
            "Phonological Processes",
            """Zyntalic applies several sound changes at morpheme boundaries:

**Assimilation:**
- Voicing assimilation: /p/ + /b/ → [bb]
- Nasal place assimilation: /n/ + /k/ → [ŋk]

**Vowel Changes:**
- Vowel harmony in suffixes
- Hiatus resolution: /a/ + /a/ → [a]

**Consonant Changes:**
- Cluster simplification: /spt/ → [st]
- Palatalization: /t/ + /i/ → [ć]"""
        )

        phonology.subsections.append(sound_changes)

        return phonology

    def generate_morphology_guide(self) -> DocumentationSection:
        """Generate morphology guide."""
        morphology = DocumentationSection(
            "Zyntalic Morphology Guide",
            "Comprehensive guide to Zyntalic word formation and inflection."
        )

        # Agglutinative Nature
        agglutination = DocumentationSection(
            "Agglutinative Structure",
            """Zyntalic is an agglutinative language, meaning it builds complex words by adding suffixes to roots in a predictable order.

**Morpheme Order (for nouns):**
Root + Derivation + Number + Case

**Example Build-up:**
- 뚧홧깍 (root: house)
- 뚧홧깍-ász (+ agent suffix: house-builder)
- 뚧홧깍-ász-ok (+ plural: house-builders)
- 뚧홧깍-ász-ok-oł (+ accusative: house-builders.ACC)"""
        )

        # Add morphological examples
        root = "뚧홧깍"
        for deriv_type in ["agent", "instrument", "abstract"]:
            derived = self.morphology.derive_word(root, deriv_type)
            agglutination.add_example(
                derived.surface_form,
                f"Derived word: {deriv_type}",
                derived.gloss
            )

        morphology.subsections.append(agglutination)

        # Verbal Morphology
        verbal_morph = DocumentationSection(
            "Verbal Morphology",
            """Verbs in Zyntalic inflect for tense, aspect, and evidentiality.

**Morpheme Order (for verbs):**
Root + Aspect + Tense + Evidentiality

**Tenses:**
- Past: -eć/-ać
- Present: -esz/-asz
- Future: -ész/-ász
- Gnomic (timeless): -ím/-ám

**Aspects:**
- Perfective: -meł/-moł (completed action)
- Imperfective: -ísz/-ász (ongoing action)
- Iterative: -géł/-gáł (repeated action)

**Evidentiality:**
- Direct: -déł/-dáł (witnessed)
- Hearsay: -kéł/-káł (heard from others)
- Inferential: -téł/-táł (inferred)
- Assumptive: -véł/-váł (assumed)"""
        )

        # Add verbal examples
        vroot = "mówić"
        for tense in [Tense.PAST, Tense.PRESENT, Tense.FUTURE]:
            inflected = self.morphology.inflect_verb(vroot, tense=tense)
            verbal_morph.add_example(
                inflected.surface_form,
                f"Verb in {tense.value} tense",
                inflected.gloss
            )

        morphology.subsections.append(verbal_morph)

        return morphology

    def generate_syntax_guide(self) -> DocumentationSection:
        """Generate syntax guide."""
        syntax = DocumentationSection(
            "Zyntalic Syntax Guide",
            "Guide to sentence structure and syntactic patterns in Zyntalic."
        )

        # Clause Structure
        clause_structure = DocumentationSection(
            "Clause Structure",
            """Zyntalic clauses follow the S-O-V-C template with specific positions for different elements.

**Basic Clause Template:**
[Subject] [Indirect Object] [Direct Object] [Obliques] [Verb] [Context Clauses] [Context Tail]

**Context Clauses:**
Context clauses are introduced by specific markers and appear after the main verb:
- Temporal: 뛀쨮 (when), 뚧홧 (while), 켓뚜 (after)
- Spatial: 홍뛸 (in/at), 뷠콮 (on), 멷뚺 (at)
- Causal: 룏딲 (because), 솻뷨 (if)

**Context Tail:**
The distinctive Korean-style context tail ⟦ctx:...⟧ contains grammatical metadata."""
        )

        syntax.subsections.append(clause_structure)

        # Complex Sentences
        complex_sent = DocumentationSection(
            "Complex Sentences",
            """Zyntalic handles complex sentences through subordination and context marking.

**Subordination:**
Subordinate clauses are marked and positioned in the context area:
- Relative clauses follow their head nouns
- Complement clauses follow the main verb
- Adverbial clauses are marked with context markers

**Coordination:**
Multiple clauses of equal status are linked with conjunctions or juxtaposition."""
        )

        # Generate syntax examples
        test_sentences = [
            "The teacher explained the lesson to students after class ended.",
            "When the sun rises, birds sing while flowers bloom.",
            "If you study hard, you will succeed in life."
        ]

        for sent in test_sentences:
            parsed = self.syntax.parse_english_advanced(sent)
            complex_sent.add_example(
                parsed.surface_form,
                sent,
                f"Complex sentence with {len(parsed.context_clauses)} context clause(s)"
            )

        syntax.subsections.append(complex_sent)

        return syntax

    def generate_lexicon_documentation(self) -> DocumentationSection:
        """Generate lexicon documentation."""
        lexicon_doc = DocumentationSection(
            "Zyntalic Lexicon",
            "Documentation of the Zyntalic vocabulary system and word relationships."
        )

        # Statistics
        stats = self.lexicon.get_vocabulary_stats()

        overview = DocumentationSection(
            "Lexicon Overview",
            f"""The Zyntalic lexicon contains **{stats['total_entries']} entries** organized by semantic fields and grammatical categories.

**Distribution by Category:**
{self._format_stats_table(stats['by_category'])}

**Distribution by Semantic Field:**
{self._format_stats_table(stats['by_semantic_field'])}

**Key Features:**
- Deterministic word generation from semantic seeds
- Anchor-based semantic grounding using literary texts
- Rich network of lexical relations (synonymy, derivation, etc.)
- Phonetic diversity score: {stats['phonetic_diversity']:.3f}"""
        )

        lexicon_doc.subsections.append(overview)

        # Word Formation
        word_formation = DocumentationSection(
            "Word Formation Processes",
            """Zyntalic creates new words through several productive processes:

**Derivation:**
- Agent suffixes: -ász/-ész (doer)
- Instrument suffixes: -ány/-ény (tool)
- Abstract suffixes: -ság/-ség (quality)
- Diminutive suffixes: -ka/-ko (small)

**Compounding:**
Words can be combined to create compounds following head-final pattern.

**Borrowing:**
Lexical items are borrowed from anchor texts and adapted to Zyntalic phonology."""
        )

        # Add word formation examples
        base_words = list(self.lexicon.entries.keys())[:3]
        for base in base_words:
            derived = self.lexicon.create_derived_word(base, "agent")
            if derived:
                word_formation.add_example(
                    f"{base} → {derived.headword}",
                    f"Derivation: {derived.semantic_info.primary_sense}",
                    "Agent derivation"
                )

        lexicon_doc.subsections.append(word_formation)

        return lexicon_doc

    def generate_semantics_guide(self) -> DocumentationSection:
        """Generate semantics and coherence guide."""
        semantics = DocumentationSection(
            "Zyntalic Semantics & Coherence",
            "Guide to meaning and discourse coherence in Zyntalic."
        )

        # Anchor System
        anchor_system = DocumentationSection(
            "Literary Anchor System",
            f"""Zyntalic uses a unique anchor system based on {len(ANCHORS)} classical literary works for semantic grounding.

**Anchor Texts:**
{self._format_anchor_list(ANCHORS)}

**How Anchors Work:**
1. Each input text gets mapped to semantic vectors
2. Similarity to anchor texts is computed
3. Top anchors influence word choice and style
4. Creates deterministic but culturally grounded translations"""
        )

        semantics.subsections.append(anchor_system)

        # Semantic Fields
        semantic_fields = DocumentationSection(
            "Semantic Field System",
            """Zyntalic organizes vocabulary into semantic fields for coherence:

**Abstract Fields:**
- Emotion, Cognition, Philosophy, Ethics, Time, Space

**Concrete Fields:**
- Nature, Human, Society, Artifact, Animal, Plant

**Action Fields:**
- Motion, Communication, Creation, Destruction

Words within the same semantic field tend to co-occur and support discourse coherence."""
        )

        semantics.subsections.append(semantic_fields)

        return semantics

    def generate_cultural_guide(self) -> DocumentationSection:
        """Generate cultural context guide."""
        culture = DocumentationSection(
            "Zyntalic Cultural Context",
            "Understanding the cultural and philosophical foundations of Zyntalic."
        )

        # Philosophy
        philosophy = DocumentationSection(
            "Philosophical Foundations",
            """Zyntalic is designed around several philosophical principles:

**Chiasmic Structure:**
The language favors chiasmic (mirrored) expressions that reflect philosophical balance:
"A begets B, and B reframes A"

**Schelling Points:**
Cultural anchors serve as coordination points for meaning, ensuring shared understanding across speakers.

**S-O-V-C Order:**
The distinctive word order places context in a privileged position, reflecting the importance of situational awareness in meaning."""
        )

        culture.subsections.append(philosophy)

        # Literary Heritage
        literary = DocumentationSection(
            "Literary Heritage",
            """Zyntalic draws from diverse world literature:

**Western Classics:**
- Homer, Plato, Aristotle (Greek tradition)
- Dante, Shakespeare (Medieval/Renaissance)
- Goethe, Austen, Dostoevsky (Modern literature)

**Eastern Wisdom:**
- Laozi, Sunzi (Chinese philosophy)
- Buddhist and Confucian influences

**Scientific Tradition:**
- Darwin, Descartes, Bacon (Empirical thought)

This creates a language that bridges cultures while maintaining coherent philosophical grounding."""
        )

        culture.subsections.append(literary)

        return culture

    def generate_beginner_tutorial(self) -> DocumentationSection:
        """Generate beginner's tutorial."""
        tutorial = DocumentationSection(
            "Zyntalic Tutorial for Beginners",
            "Step-by-step guide to learning Zyntalic."
        )

        # Lesson 1: Basics
        lesson1 = DocumentationSection(
            "Lesson 1: Basic Sentences",
            """Welcome to Zyntalic! Let's start with simple sentences.

**Key Concept: S-O-V-C Order**
Unlike English (Subject-Verb-Object), Zyntalic uses Subject-Object-Verb-Context.

**Your First Sentence:**
English: "I love you"
Zyntalic: "나 너 사랑해 ⟦ctx:han=뽇뎻; lemma=사랑; pos=verb; anchors=Shakespeare_Sonnets⟧"

**Breaking it down:**
- 나 (na) = I (subject)
- 너 (neo) = you (object)
- 사랑해 (sarang-hae) = love (verb)
- ⟦ctx:...⟧ = context information (ignore for now)"""
        )

        tutorial.subsections.append(lesson1)

        # Lesson 2: Cases
        lesson2 = DocumentationSection(
            "Lesson 2: Case Markers",
            """Zyntalic uses case markers to show relationships between words.

**Basic Cases:**
- No marker = subject (nominative)
- -eł/-oł = direct object (accusative)
- -re/-ra = to/for someone (dative)

**Practice:**
Try building: "I give you a book"
- 나 = I (subject, no marker)
- 너-re = to you (dative marker)
- 책-eł = book (accusative marker)
- 줘 = give (verb)

Result: "나 너-re 책-eł 줘 ⟦ctx:...⟧" """
        )

        tutorial.subsections.append(lesson2)

        return tutorial

    def generate_quick_reference(self) -> DocumentationSection:
        """Generate quick reference card."""
        quick_ref = DocumentationSection(
            "Zyntalic Quick Reference",
            "Essential information for quick lookup."
        )

        # Grammar Summary
        grammar_summary = DocumentationSection(
            "Grammar at a Glance",
            """**Word Order:** Subject - Object - Verb - Context (S-O-V-C)

**Case System:**
- ∅ (nominative), -eł/-oł (accusative), -nek/-nok (genitive)
- -re/-ra (dative), -ben/-ban (locative), -vel/-val (instrumental)

**Verb Inflection:**
- Aspect + Tense + Evidentiality
- Aspect: -ísz/-ász (imperfective), -meł/-moł (perfective)
- Tense: -esz/-asz (present), -eć/-ać (past), -ész/-ász (future)

**Scripts:**
- Nouns: mostly Hangul (85%)
- Verbs: mostly Latin (85%)"""
        )

        quick_ref.subsections.append(grammar_summary)

        # Common Phrases
        phrases = DocumentationSection(
            "Common Phrases",
            "Essential expressions for daily use."
        )

        common_expressions = [
            ("Hello", "안녕하세요"),
            ("Thank you", "감사합니다"),
            ("I don't understand", "이해 못해요"),
            ("How are you?", "어떻게 지내세요?"),
            ("Good morning", "좋은 아침")
        ]

        for english, zyntalic in common_expressions:
            phrases.add_example(zyntalic, english, "Common expression")

        quick_ref.subsections.append(phrases)

        return quick_ref

    def _format_phoneme_table(self, phoneme_dict: dict[str, str]) -> str:
        """Format phoneme inventory as table."""
        lines = []
        items = list(phoneme_dict.items())

        for i in range(0, len(items), 4):  # 4 columns
            row = items[i:i+4]
            formatted_row = " | ".join(f"{symbol} /{ipa}/" for symbol, ipa in row)
            lines.append(formatted_row)

        return "\n".join(f"| {line} |" for line in lines)

    def _format_stats_table(self, stats_dict: dict) -> str:
        """Format statistics as table."""
        lines = []
        for key, value in stats_dict.items():
            lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        return "\n".join(lines)

    def _format_anchor_list(self, anchors: list[str]) -> str:
        """Format anchor list."""
        formatted = []
        for anchor in anchors:
            name = anchor.replace('_', ' ')
            formatted.append(f"- {name}")
        return "\n".join(formatted)

    def _generate_index(self, docs: dict[str, DocumentationSection], output_dir: str):
        """Generate master index file."""
        index_content = """# Zyntalic Language Documentation

Welcome to the complete documentation for the Zyntalic constructed language.

## Quick Start

New to Zyntalic? Start with these documents:

1. [Tutorial](tutorial.md) - Step-by-step learning guide
2. [Quick Reference](quick_ref.md) - Essential information
3. [Grammar Reference](grammar.md) - Complete grammar guide

## Complete Documentation

### Language Structure
- [Grammar Reference](grammar.md) - Complete grammatical description
- [Phonology Guide](phonology.md) - Sound system and script
- [Morphology Guide](morphology.md) - Word formation and inflection
- [Syntax Guide](syntax.md) - Sentence structure

### Vocabulary & Meaning
- [Lexicon](lexicon.md) - Vocabulary system and word relationships
- [Semantics Guide](semantics.md) - Meaning and coherence systems

### Cultural Context
- [Cultural Guide](culture.md) - Philosophical and literary foundations

### Learning Materials
- [Beginner Tutorial](tutorial.md) - Structured learning path
- [Quick Reference](quick_ref.md) - Handy reference card

## About Zyntalic

Zyntalic is a deterministic constructed language featuring:

- **S-O-V-C word order** with distinctive context positioning
- **Mixed Hangul-Latin script** system
- **Literary anchor system** based on world literature
- **Rich morphological system** with agglutination
- **Semantic coherence** through philosophical grounding

---

*Documentation generated on {date}*
""".format(date=datetime.now().strftime("%Y-%m-%d"))

        with open(os.path.join(output_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(index_content)

# -------------------- Demo Function --------------------

def demo_documentation():
    """Demonstrate documentation generation."""
    generator = ZyntalicDocumentationGenerator()

    print("=== Zyntalic Documentation Generator Demo ===\n")

    # Generate sample documentation sections
    print("Generating sample documentation sections...\n")

    # Grammar sample
    grammar = generator.generate_grammar_reference()
    print("Grammar Reference (excerpt):")
    print(grammar.subsections[0].to_markdown()[:500] + "...\n")

    # Phonology sample
    phonology = generator.generate_phonology_guide()
    print("Phonology Guide (excerpt):")
    print(phonology.subsections[0].to_markdown()[:300] + "...\n")

    # Generate complete documentation
    print("Generating complete documentation suite...")
    output_dir = generator.generate_complete_documentation()
    print(f"Complete documentation generated in: {output_dir}")

if __name__ == "__main__":
    demo_documentation()
