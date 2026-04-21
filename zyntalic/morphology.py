"""
Zyntalic Morphological System

Advanced morphology for Zyntalic featuring:
- Agglutinative inflection (Korean-inspired)
- Vowel harmony (Hungarian-inspired)
- Polish consonant clusters
- Case system (6 cases)
- Aspect/evidentiality markers
- Derivational morphology
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .utils.rng import get_rng

# -------------------- Morphological Categories --------------------

class Case(Enum):
    NOMINATIVE = "nom"    # Subject marker
    ACCUSATIVE = "acc"    # Direct object
    GENITIVE = "gen"      # Possession, "of"
    DATIVE = "dat"        # Indirect object, "to/for"
    LOCATIVE = "loc"      # Location, "at/in/on"
    INSTRUMENTAL = "ins"  # "with/by means of"

class Aspect(Enum):
    PERFECTIVE = "pfv"    # Completed action
    IMPERFECTIVE = "ipfv" # Ongoing/habitual action
    ITERATIVE = "iter"    # Repeated action

class Evidentiality(Enum):
    DIRECT = "dir"        # Witnessed directly
    HEARSAY = "hear"      # Heard from others
    INFERENTIAL = "inf"   # Inferred from evidence
    ASSUMPTIVE = "assm"   # Assumed/believed

class Number(Enum):
    SINGULAR = "sg"
    PLURAL = "pl"
    COLLECTIVE = "col"    # Group as unit

class Tense(Enum):
    PAST = "pst"
    PRESENT = "prs"
    FUTURE = "fut"
    GNOMIC = "gnom"       # Timeless truths

# -------------------- Vowel Harmony System --------------------

FRONT_VOWELS = {"ᅡ", "ᅢ", "ᅣ", "ᅤ", "ᅦ", "ᅧ", "ᅨ", "e", "é", "i", "í", "ö", "ő", "ü", "ű"}
BACK_VOWELS = {"ᅥ", "ᅩ", "ᅪ", "ᅫ", "ᅬ", "ᅭ", "ᅮ", "ᅯ", "ᅰ", "ᅱ", "ᅲ", "ᅳ", "ᅴ", "ᅵ",
               "a", "á", "o", "ó", "u", "ú"}
NEUTRAL_VOWELS = {"ᅵ", "y"}  # Can appear with either

def get_vowel_harmony(word: str) -> str:
    """Determine vowel harmony class of a word."""
    vowels_found = []
    for char in word.lower():
        if char in FRONT_VOWELS:
            vowels_found.append("front")
        elif char in BACK_VOWELS:
            vowels_found.append("back")

    # If mixed or no clear pattern, default to back
    if not vowels_found:
        return "back"

    front_count = vowels_found.count("front")
    back_count = vowels_found.count("back")

    return "front" if front_count > back_count else "back"

# -------------------- Morpheme Inventory --------------------

# Case suffixes with vowel harmony
CASE_SUFFIXES = {
    Case.NOMINATIVE: {"front": "", "back": ""},  # Zero marking
    Case.ACCUSATIVE: {"front": "-eł", "back": "-oł"},
    Case.GENITIVE: {"front": "-nek", "back": "-nok"},
    Case.DATIVE: {"front": "-re", "back": "-ra"},
    Case.LOCATIVE: {"front": "-ben", "back": "-ban"},
    Case.INSTRUMENTAL: {"front": "-vel", "back": "-val"},
}

# Number suffixes
NUMBER_SUFFIXES = {
    Number.SINGULAR: "",
    Number.PLURAL: {"front": "-ek", "back": "-ok"},
    Number.COLLECTIVE: {"front": "-ség", "back": "-ság"},
}

# Aspect suffixes for verbs
ASPECT_SUFFIXES = {
    Aspect.PERFECTIVE: {"front": "-meł", "back": "-moł"},
    Aspect.IMPERFECTIVE: {"front": "-ísz", "back": "-ász"},
    Aspect.ITERATIVE: {"front": "-géł", "back": "-gáł"},
}

# Evidentiality suffixes
EVIDENTIALITY_SUFFIXES = {
    Evidentiality.DIRECT: {"front": "-déł", "back": "-dáł"},
    Evidentiality.HEARSAY: {"front": "-kéł", "back": "-káł"},
    Evidentiality.INFERENTIAL: {"front": "-téł", "back": "-táł"},
    Evidentiality.ASSUMPTIVE: {"front": "-véł", "back": "-váł"},
}

# Tense suffixes for verbs
TENSE_SUFFIXES = {
    Tense.PAST: {"front": "-eć", "back": "-ać"},
    Tense.PRESENT: {"front": "-esz", "back": "-asz"},
    Tense.FUTURE: {"front": "-ész", "back": "-ász"},
    Tense.GNOMIC: {"front": "-ím", "back": "-ám"},
}

# Derivational suffixes
DERIVATIONAL_SUFFIXES = {
    "agent": {"front": "-ész", "back": "-ász"},      # doer suffix
    "instrument": {"front": "-ény", "back": "-ány"}, # tool suffix
    "abstract": {"front": "-ség", "back": "-ság"},   # quality suffix
    "diminutive": {"front": "-ka", "back": "-ko"},   # small suffix
    "augmentative": {"front": "-úł", "back": "-úł"}, # big suffix
    "verbal_noun": {"front": "-ésí", "back": "-ásí"}, # gerund
}

# -------------------- Morphological Classes --------------------

@dataclass
class MorphemeBundle:
    """Represents a bundle of morphological features."""
    case: Case | None = None
    number: Number | None = None
    aspect: Aspect | None = None
    evidentiality: Evidentiality | None = None
    tense: Tense | None = None
    derivations: list[str] = None

    def __post_init__(self):
        if self.derivations is None:
            self.derivations = []

@dataclass
class InflectedWord:
    """Represents a fully inflected Zyntalic word."""
    root: str
    morphemes: MorphemeBundle
    surface_form: str
    gloss: str
    pos: str  # part of speech

class MorphologicalProcessor:
    """Main class for handling Zyntalic morphology."""

    def __init__(self, seed: str = "morphology"):
        self.rng = get_rng(seed)
        self._cache = {}

    def inflect_noun(self, root: str, case: Case = Case.NOMINATIVE,
                     number: Number = Number.SINGULAR) -> InflectedWord:
        """Inflect a noun with case and number."""
        harmony = get_vowel_harmony(root)

        # Build surface form
        surface = root

        # Add number suffix first
        if number != Number.SINGULAR:
            if isinstance(NUMBER_SUFFIXES[number], dict):
                surface += NUMBER_SUFFIXES[number][harmony]
            else:
                surface += NUMBER_SUFFIXES[number]

        # Add case suffix
        if case != Case.NOMINATIVE:
            surface += CASE_SUFFIXES[case][harmony]

        # Build gloss
        gloss_parts = [root]
        if number != Number.SINGULAR:
            gloss_parts.append(number.value)
        if case != Case.NOMINATIVE:
            gloss_parts.append(case.value)

        morphemes = MorphemeBundle(case=case, number=number)

        return InflectedWord(
            root=root,
            morphemes=morphemes,
            surface_form=surface,
            gloss="-".join(gloss_parts),
            pos="noun"
        )

    def inflect_verb(self, root: str, tense: Tense = Tense.PRESENT,
                     aspect: Aspect = Aspect.IMPERFECTIVE,
                     evidentiality: Evidentiality | None = None) -> InflectedWord:
        """Inflect a verb with tense, aspect, and evidentiality."""
        harmony = get_vowel_harmony(root)

        surface = root
        gloss_parts = [root]

        # Add aspect suffix
        surface += ASPECT_SUFFIXES[aspect][harmony]
        gloss_parts.append(aspect.value)

        # Add tense suffix
        surface += TENSE_SUFFIXES[tense][harmony]
        gloss_parts.append(tense.value)

        # Add evidentiality if specified
        if evidentiality:
            surface += EVIDENTIALITY_SUFFIXES[evidentiality][harmony]
            gloss_parts.append(evidentiality.value)

        morphemes = MorphemeBundle(tense=tense, aspect=aspect, evidentiality=evidentiality)

        return InflectedWord(
            root=root,
            morphemes=morphemes,
            surface_form=surface,
            gloss="-".join(gloss_parts),
            pos="verb"
        )

    def derive_word(self, root: str, derivation_type: str, pos: str = "noun") -> InflectedWord:
        """Apply derivational morphology to create new words."""
        if derivation_type not in DERIVATIONAL_SUFFIXES:
            raise ValueError(f"Unknown derivation type: {derivation_type}")

        harmony = get_vowel_harmony(root)
        suffix = DERIVATIONAL_SUFFIXES[derivation_type][harmony]

        surface = root + suffix
        gloss = f"{root}-{derivation_type}"

        # Determine new POS
        new_pos = pos
        if derivation_type in ["agent", "instrument"]:
            new_pos = "noun"
        elif derivation_type == "verbal_noun":
            new_pos = "noun"
        elif derivation_type == "abstract":
            new_pos = "noun"

        morphemes = MorphemeBundle(derivations=[derivation_type])

        return InflectedWord(
            root=root,
            morphemes=morphemes,
            surface_form=surface,
            gloss=gloss,
            pos=new_pos
        )

    def phonological_assimilation(self, word: str) -> str:
        """Apply phonological rules for morpheme boundaries."""
        # Consonant cluster simplification
        word = re.sub(r'([szść])ć', r'\1', word)  # sz+ć -> sz
        word = re.sub(r'([ln])ł', r'\1', word)    # n+ł -> n

        # Vowel hiatus resolution
        word = re.sub(r'([aeiou])\1', r'\1', word)  # aa -> a

        # Polish palatalization
        word = re.sub(r't([ei])', r'ć\1', word)   # t+e/i -> ć+e/i
        word = re.sub(r'd([ei])', r'dź\1', word)  # d+e/i -> dź+e/i

        return word

    def analyze_word(self, word: str) -> InflectedWord | None:
        """Attempt to morphologically analyze a Zyntalic word."""
        # This is a simplified analyzer - in a full implementation,
        # this would use finite-state morphology or similar

        # Try to identify suffixes working backwards
        for case in Case:
            if case == Case.NOMINATIVE:
                continue
            for harmony in ["front", "back"]:
                suffix = CASE_SUFFIXES[case][harmony]
                if suffix and word.endswith(suffix):
                    root = word[:-len(suffix)]
                    # Check if this could be a valid root
                    if len(root) >= 2:  # Minimum root length
                        morphemes = MorphemeBundle(case=case)
                        return InflectedWord(
                            root=root,
                            morphemes=morphemes,
                            surface_form=word,
                            gloss=f"{root}-{case.value}",
                            pos="noun"
                        )

        # If no analysis found, treat as uninflected root
        return InflectedWord(
            root=word,
            morphemes=MorphemeBundle(),
            surface_form=word,
            gloss=word,
            pos="unknown"
        )

# -------------------- Convenience Functions --------------------

def inflect(word: str, **kwargs) -> str:
    """Quick inflection function."""
    processor = MorphologicalProcessor()

    # Determine POS and inflect accordingly
    if "case" in kwargs or "number" in kwargs:
        result = processor.inflect_noun(
            word,
            case=kwargs.get("case", Case.NOMINATIVE),
            number=kwargs.get("number", Number.SINGULAR)
        )
    elif "tense" in kwargs or "aspect" in kwargs:
        result = processor.inflect_verb(
            word,
            tense=kwargs.get("tense", Tense.PRESENT),
            aspect=kwargs.get("aspect", Aspect.IMPERFECTIVE),
            evidentiality=kwargs.get("evidentiality")
        )
    else:
        # No inflection specified, return as-is
        return word

    return result.surface_form

def derive(root: str, derivation_type: str) -> str:
    """Quick derivation function."""
    processor = MorphologicalProcessor()
    result = processor.derive_word(root, derivation_type)
    return result.surface_form

# -------------------- Testing Functions --------------------

def demo_morphology():
    """Demonstrate the morphological system."""
    processor = MorphologicalProcessor()

    print("=== Zyntalic Morphological System Demo ===\n")

    # Noun inflection
    root = "뚧홧깍"  # Some Hangul root
    print("Noun inflection:")
    for case in Case:
        inflected = processor.inflect_noun(root, case=case)
        print(f"  {case.name:12}: {inflected.surface_form:15} [{inflected.gloss}]")

    print("\nPlural forms:")
    for case in [Case.NOMINATIVE, Case.ACCUSATIVE, Case.GENITIVE]:
        inflected = processor.inflect_noun(root, case=case, number=Number.PLURAL)
        print(f"  {case.name:12}: {inflected.surface_form:15} [{inflected.gloss}]")

    # Verb inflection
    vroot = "mówić"  # Polish-style root
    print(f"\nVerb inflection for '{vroot}':")
    for tense in Tense:
        inflected = processor.inflect_verb(vroot, tense=tense)
        print(f"  {tense.name:12}: {inflected.surface_form:15} [{inflected.gloss}]")

    # Evidentiality
    print("\nEvidentiality markers:")
    for evid in Evidentiality:
        inflected = processor.inflect_verb(vroot, evidentiality=evid)
        print(f"  {evid.name:12}: {inflected.surface_form:20} [{inflected.gloss}]")

    # Derivational morphology
    print(f"\nDerivational morphology from '{root}':")
    for deriv_type in ["agent", "instrument", "abstract", "diminutive"]:
        derived = processor.derive_word(root, deriv_type)
        print(f"  {deriv_type:12}: {derived.surface_form:15} [{derived.gloss}]")

if __name__ == "__main__":
    demo_morphology()
