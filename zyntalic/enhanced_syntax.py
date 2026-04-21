"""
Enhanced Zyntalic Syntax System

Advanced syntactic processing for Zyntalic featuring:
- S-O-V-C (Subject-Object-Verb-Context) word order
- Dependency parsing for complex sentences
- Clause hierarchies and embedding
- Coordination and subordination
- Enhanced context marker system
- Integration with morphology
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from . import nlp
from .morphology import Case, MorphologicalProcessor
from .utils.rng import get_rng

# -------------------- Syntactic Categories --------------------

class PhraseType(Enum):
    NP = "NP"    # Noun Phrase
    VP = "VP"    # Verb Phrase
    PP = "PP"    # Prepositional Phrase
    AP = "AP"    # Adjectival Phrase
    CP = "CP"    # Context/Complementizer Phrase
    AdvP = "AdvP" # Adverbial Phrase

class SyntacticRole(Enum):
    SUBJECT = "subj"
    DIRECT_OBJECT = "dobj"
    INDIRECT_OBJECT = "iobj"
    OBLIQUE = "obl"
    ADJUNCT = "adjunct"
    PREDICATE = "pred"
    MODIFIER = "mod"
    COMPLEMENT = "comp"

class ClauseType(Enum):
    MAIN = "main"
    SUBORDINATE = "sub"
    RELATIVE = "rel"
    COMPLEMENT = "comp"
    ADVERBIAL = "adv"

class ContextType(Enum):
    TEMPORAL = "temp"    # when, while, after
    SPATIAL = "spat"     # where, in, on
    CAUSAL = "caus"      # because, since
    CONDITIONAL = "cond" # if, unless
    MODAL = "modal"      # might, could
    EVIDENTIAL = "evid"  # reportedly, apparently

# -------------------- Syntactic Structures --------------------

@dataclass
class SyntacticFeatures:
    """Bundle of syntactic features."""
    case: Case | None = None
    role: SyntacticRole | None = None
    phrase_type: PhraseType | None = None
    agreement: dict[str, any] | None = None

    def __post_init__(self):
        if self.agreement is None:
            self.agreement = {}

@dataclass
class SyntacticNode:
    """Represents a node in the syntactic tree."""
    label: str
    phrase_type: PhraseType
    head: SyntacticNode | None = None
    dependents: list[SyntacticNode] = field(default_factory=list)
    features: SyntacticFeatures = field(default_factory=SyntacticFeatures)
    surface_form: str = ""

    def add_dependent(self, dependent: SyntacticNode, role: SyntacticRole):
        """Add a dependent with specified grammatical role."""
        dependent.features.role = role
        self.dependents.append(dependent)

    def get_dependents_by_role(self, role: SyntacticRole) -> list[SyntacticNode]:
        """Get all dependents with specified role."""
        return [dep for dep in self.dependents if dep.features.role == role]

    def linearize_sovc(self) -> list[str]:
        """Linearize tree in S-O-V-C order."""
        result = []

        # Subject first
        subjects = self.get_dependents_by_role(SyntacticRole.SUBJECT)
        for subj in subjects:
            result.extend(subj.linearize_sovc())

        # Direct object
        dobjs = self.get_dependents_by_role(SyntacticRole.DIRECT_OBJECT)
        for dobj in dobjs:
            result.extend(dobj.linearize_sovc())

        # Indirect object
        iobjs = self.get_dependents_by_role(SyntacticRole.INDIRECT_OBJECT)
        for iobj in iobjs:
            result.extend(iobj.linearize_sovc())

        # Other arguments/adjuncts
        others = [dep for dep in self.dependents
                 if dep.features.role not in {SyntacticRole.SUBJECT,
                                             SyntacticRole.DIRECT_OBJECT,
                                             SyntacticRole.INDIRECT_OBJECT}]
        for other in others:
            if other.features.role != SyntacticRole.COMPLEMENT:  # Save complements for last
                result.extend(other.linearize_sovc())

        # Verb (head)
        if self.phrase_type == PhraseType.VP and self.surface_form:
            result.append(self.surface_form)
        elif self.surface_form:
            result.append(self.surface_form)

        # Context/Complements last (C position)
        complements = self.get_dependents_by_role(SyntacticRole.COMPLEMENT)
        for comp in complements:
            result.extend(comp.linearize_sovc())

        return result

@dataclass
class ContextClause:
    """Represents a context clause with specific semantic type."""
    content: str
    context_type: ContextType
    marker: str  # the word that introduces the clause
    embedded_clause: SyntacticNode | None = None

@dataclass
class ZyntalicSentence:
    """Complete analyzed Zyntalic sentence."""
    main_clause: SyntacticNode
    context_clauses: list[ContextClause] = field(default_factory=list)
    korean_context: str = ""  # Traditional Korean-style context tail
    surface_form: str = ""

# -------------------- Enhanced Parser --------------------

class ZyntalicSyntaxProcessor:
    """Advanced syntactic processor for Zyntalic."""

    def __init__(self, seed: str = "syntax"):
        self.rng = get_rng(seed)
        self.morphology = MorphologicalProcessor(seed)
        self._build_grammar_rules()
        self._build_context_markers()

    def _build_grammar_rules(self):
        """Define syntactic rules and patterns."""
        # Verb subcategorization frames
        self.verb_frames = {
            "intransitive": [SyntacticRole.SUBJECT],
            "transitive": [SyntacticRole.SUBJECT, SyntacticRole.DIRECT_OBJECT],
            "ditransitive": [SyntacticRole.SUBJECT, SyntacticRole.DIRECT_OBJECT, SyntacticRole.INDIRECT_OBJECT],
            "copula": [SyntacticRole.SUBJECT, SyntacticRole.PREDICATE],
        }

        # Case assignment rules (simplified)
        self.case_assignment = {
            SyntacticRole.SUBJECT: Case.NOMINATIVE,
            SyntacticRole.DIRECT_OBJECT: Case.ACCUSATIVE,
            SyntacticRole.INDIRECT_OBJECT: Case.DATIVE,
            SyntacticRole.OBLIQUE: Case.INSTRUMENTAL,
        }

    def _build_context_markers(self):
        """Enhanced context marker system."""
        self.context_markers = {
            # Temporal
            "when": ContextType.TEMPORAL,
            "while": ContextType.TEMPORAL,
            "after": ContextType.TEMPORAL,
            "before": ContextType.TEMPORAL,
            "during": ContextType.TEMPORAL,

            # Spatial
            "where": ContextType.SPATIAL,
            "in": ContextType.SPATIAL,
            "on": ContextType.SPATIAL,
            "at": ContextType.SPATIAL,
            "near": ContextType.SPATIAL,

            # Causal
            "because": ContextType.CAUSAL,
            "since": ContextType.CAUSAL,
            "as": ContextType.CAUSAL,
            "due to": ContextType.CAUSAL,

            # Conditional
            "if": ContextType.CONDITIONAL,
            "unless": ContextType.CONDITIONAL,
            "provided": ContextType.CONDITIONAL,

            # Modal/Evidential
            "apparently": ContextType.EVIDENTIAL,
            "reportedly": ContextType.EVIDENTIAL,
            "possibly": ContextType.MODAL,
            "definitely": ContextType.MODAL,
        }

        # Extended markers for philosophical/literary contexts
        self.philosophical_markers = {
            "through": ContextType.MODAL,
            "beyond": ContextType.MODAL,
            "within": ContextType.SPATIAL,
            "amongst": ContextType.SPATIAL,
            "concerning": ContextType.CAUSAL,
            "regarding": ContextType.CAUSAL,
        }

        self.context_markers.update(self.philosophical_markers)

    def parse_english_advanced(self, text: str) -> ZyntalicSentence:
        """Advanced parsing of English input."""
        # Tokenize and preprocess
        tokens = self._tokenize_advanced(text)

        # Identify main verb and clause boundaries
        main_verb_idx = self._find_main_verb(tokens)

        # Parse main clause
        main_clause = self._parse_main_clause(tokens, main_verb_idx)

        # Identify and parse context clauses
        context_clauses = self._parse_context_clauses(tokens)

        # Generate Korean context tail
        korean_context = self._generate_korean_context(text, main_clause)

        # Build complete sentence
        sentence = ZyntalicSentence(
            main_clause=main_clause,
            context_clauses=context_clauses,
            korean_context=korean_context
        )

        # Generate surface form in S-O-V-C order
        sentence.surface_form = self._generate_surface_form(sentence)

        return sentence

    def _tokenize_advanced(self, text: str) -> list[dict[str, str]]:
        """Advanced tokenization with POS tagging."""
        if nlp.backend_name() == "spacy":
            tokens = []
            for tok in nlp.analyze_tokens(text):
                tokens.append({
                    'word': tok.get('text', ''),
                    'pos': tok.get('pos', 'X'),
                    'lemma': (tok.get('lemma') or tok.get('text', '')).lower(),
                    'features': {}
                })
            return tokens

        # Simple tokenization - fallback when NLP isn't available
        raw_tokens = re.findall(r"\w+(?:'\w+)?|[^\w\s]", text.lower())

        tokens = []
        for token in raw_tokens:
            pos = self._guess_pos(token)
            tokens.append({
                'word': token,
                'pos': pos,
                'lemma': self._lemmatize(token),
                'features': {}
            })

        return tokens

    def _guess_pos(self, word: str) -> str:
        """Simple POS guesser."""
        # Common verbs
        if word in {'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                   'do', 'does', 'did', 'will', 'would', 'can', 'could', 'should', 'may', 'might'}:
            return 'VERB'

        # Common pronouns
        if word in {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'}:
            return 'PRON'

        # Common determiners
        if word in {'the', 'a', 'an', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}:
            return 'DET'

        # Common prepositions
        if word in {'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'of', 'about'}:
            return 'ADP'

        # Adjective endings
        if word.endswith(('able', 'ible', 'ful', 'less', 'ous', 'ive', 'al', 'ic')):
            return 'ADJ'

        # Verb endings
        if word.endswith(('ing', 'ed', 's')) and len(word) > 3:
            return 'VERB'

        # Noun endings
        if word.endswith(('tion', 'sion', 'ness', 'ment', 'ity', 'ty', 's')) and len(word) > 3:
            return 'NOUN'

        # Default to noun
        return 'NOUN'

    def _lemmatize(self, word: str) -> str:
        """Simple lemmatization."""
        if word.endswith('ing') and len(word) > 4:
            return word[:-3]
        if word.endswith('ed') and len(word) > 3:
            return word[:-2]
        if word.endswith('s') and len(word) > 2 and not word.endswith('ss'):
            return word[:-1]
        return word

    def _find_main_verb(self, tokens: list[dict]) -> int:
        """Find the main verb of the sentence."""
        # Look for auxiliary + main verb patterns first
        for i, token in enumerate(tokens):
            if token['pos'] == 'VERB' and token['word'] in {'will', 'would', 'can', 'could', 'should', 'may', 'might'}:
                # Look for main verb after auxiliary
                for j in range(i + 1, min(i + 3, len(tokens))):
                    if tokens[j]['pos'] == 'VERB':
                        return j

        # Otherwise, find first main verb
        for i, token in enumerate(tokens):
            if token['pos'] == 'VERB' and token['word'] not in {'will', 'would', 'can', 'could', 'should', 'may', 'might'}:
                return i

        # Fallback to middle of sentence
        return len(tokens) // 2

    def _parse_main_clause(self, tokens: list[dict], verb_idx: int) -> SyntacticNode:
        """Parse the main clause structure."""
        verb_token = tokens[verb_idx]

        # Create verb phrase node
        vp = SyntacticNode(
            label="VP_main",
            phrase_type=PhraseType.VP,
            surface_form=verb_token['word']
        )

        # Find subject (before verb, excluding context markers)
        subject_tokens = []
        for i in range(verb_idx):
            if tokens[i]['word'] not in self.context_markers and tokens[i]['pos'] in {'NOUN', 'PRON'}:
                subject_tokens.append(tokens[i])

        if subject_tokens:
            subj_node = SyntacticNode(
                label="NP_subj",
                phrase_type=PhraseType.NP,
                surface_form=" ".join(t['word'] for t in subject_tokens),
                features=SyntacticFeatures(case=Case.NOMINATIVE)
            )
            vp.add_dependent(subj_node, SyntacticRole.SUBJECT)

        # Find object (after verb, before context markers)
        object_tokens = []
        context_start = len(tokens)

        # Find where context markers start
        for i in range(verb_idx + 1, len(tokens)):
            if tokens[i]['word'] in self.context_markers:
                context_start = i
                break

        # Collect object tokens
        for i in range(verb_idx + 1, context_start):
            if tokens[i]['pos'] in {'NOUN', 'PRON', 'ADJ'}:
                object_tokens.append(tokens[i])

        if object_tokens:
            obj_node = SyntacticNode(
                label="NP_obj",
                phrase_type=PhraseType.NP,
                surface_form=" ".join(t['word'] for t in object_tokens),
                features=SyntacticFeatures(case=Case.ACCUSATIVE)
            )
            vp.add_dependent(obj_node, SyntacticRole.DIRECT_OBJECT)

        return vp

    def _parse_context_clauses(self, tokens: list[dict]) -> list[ContextClause]:
        """Parse context clauses from token stream."""
        context_clauses = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token['word'] in self.context_markers:
                # Found context marker, collect following clause
                marker = token['word']
                context_type = self.context_markers[marker]

                # Collect tokens until next context marker or end
                clause_tokens = []
                j = i + 1
                while j < len(tokens):
                    if tokens[j]['word'] in self.context_markers:
                        break
                    clause_tokens.append(tokens[j])
                    j += 1

                if clause_tokens:
                    content = " ".join(t['word'] for t in clause_tokens)
                    context_clause = ContextClause(
                        content=content,
                        context_type=context_type,
                        marker=marker
                    )
                    context_clauses.append(context_clause)

                i = j
            else:
                i += 1

        return context_clauses

    def _generate_korean_context(self, original_text: str, main_clause: SyntacticNode) -> str:
        """Generate Korean-style context tail."""
        from .core import lemmatize, make_korean_tail

        # Use original method but enhanced
        lemma = lemmatize(original_text.split()[0] if original_text else "default")
        han_tail = make_korean_tail(lemma)

        # Add syntactic information
        verb_surface = main_clause.surface_form
        num_args = len(main_clause.dependents)

        # Determine clause type
        clause_type = "main"
        if any(dep.features.role == SyntacticRole.COMPLEMENT for dep in main_clause.dependents):
            clause_type = "complex"

        return f"⟦ctx:han={han_tail}; verb={verb_surface}; args={num_args}; type={clause_type}⟧"

    def _generate_surface_form(self, sentence: ZyntalicSentence) -> str:
        """Generate surface form following S-O-V-C order."""
        # Get linearized main clause
        main_parts = sentence.main_clause.linearize_sovc()

        # Add context clauses
        context_parts = []
        for ctx_clause in sentence.context_clauses:
            # Translate context marker to Zyntalic equivalent
            zyntalic_marker = self._translate_context_marker(ctx_clause.marker)
            context_parts.append(f"{zyntalic_marker} {ctx_clause.content}")

        # Combine all parts
        all_parts = main_parts + context_parts

        # Add Korean context tail
        if sentence.korean_context:
            all_parts.append(sentence.korean_context)

        return " ".join(all_parts)

    def _translate_context_marker(self, marker: str) -> str:
        """Translate English context markers to Zyntalic equivalents."""
        # Generate deterministic Zyntalic context markers
        from .core import generate_word

        marker_translations = {
            "when": "뛀쨮",     # temporal
            "where": "깟뼍",    # spatial
            "because": "룏딲",  # causal
            "if": "솻뷨",       # conditional
            "while": "뚧홧",    # temporal
            "after": "켓뚜",    # temporal
            "before": "쾏뫼",   # temporal
            "in": "홍뛸",       # spatial
            "on": "뷠콮",       # spatial
            "at": "멷뚺",       # spatial
        }

        return marker_translations.get(marker, generate_word(f"ctx:{marker}"))

    def analyze_sentence_complexity(self, sentence: ZyntalicSentence) -> dict[str, any]:
        """Analyze the syntactic complexity of a sentence."""
        return {
            'main_clause_depth': self._calculate_depth(sentence.main_clause),
            'context_clause_count': len(sentence.context_clauses),
            'context_types': [ctx.context_type.value for ctx in sentence.context_clauses],
            'argument_count': len(sentence.main_clause.dependents),
            'has_coordination': self._has_coordination(sentence.main_clause),
            'has_subordination': len(sentence.context_clauses) > 0,
        }

    def _calculate_depth(self, node: SyntacticNode) -> int:
        """Calculate maximum depth of syntactic tree."""
        if not node.dependents:
            return 1
        return 1 + max(self._calculate_depth(dep) for dep in node.dependents)

    def _has_coordination(self, node: SyntacticNode) -> bool:
        """Check if node contains coordination."""
        # Simplified - look for multiple dependents of same role
        roles = [dep.features.role for dep in node.dependents]
        return len(roles) != len(set(roles))

# -------------------- Convenience Functions --------------------

def parse_to_zyntalic(text: str) -> str:
    """Parse English text and return Zyntalic S-O-V-C form."""
    processor = ZyntalicSyntaxProcessor()
    sentence = processor.parse_english_advanced(text)
    return sentence.surface_form

def analyze_syntax(text: str) -> dict[str, any]:
    """Analyze syntactic structure of English text."""
    processor = ZyntalicSyntaxProcessor()
    sentence = processor.parse_english_advanced(text)
    analysis = processor.analyze_sentence_complexity(sentence)

    analysis['original'] = text
    analysis['zyntalic'] = sentence.surface_form
    analysis['korean_context'] = sentence.korean_context

    return analysis

# -------------------- Demo Function --------------------

def demo_syntax():
    """Demonstrate the enhanced syntax system."""
    processor = ZyntalicSyntaxProcessor()

    print("=== Enhanced Zyntalic Syntax System Demo ===\n")

    test_sentences = [
        "I love you.",
        "The cat walks in the garden.",
        "She gave him a book because he asked nicely.",
        "When the sun rises, birds sing while flowers bloom.",
        "If you study hard, you will succeed in life.",
        "The teacher explained the lesson to students after class ended.",
    ]

    for i, sent in enumerate(test_sentences, 1):
        print(f"{i}. Original: {sent}")

        parsed = processor.parse_english_advanced(sent)
        print(f"   Zyntalic: {parsed.surface_form}")

        analysis = processor.analyze_sentence_complexity(parsed)
        print(f"   Analysis: depth={analysis['main_clause_depth']}, " +
              f"contexts={analysis['context_clause_count']}, " +
              f"args={analysis['argument_count']}")

        if parsed.context_clauses:
            for ctx in parsed.context_clauses:
                print(f"   Context:  [{ctx.context_type.value}] {ctx.marker} → {ctx.content}")

        print()

if __name__ == "__main__":
    demo_syntax()
