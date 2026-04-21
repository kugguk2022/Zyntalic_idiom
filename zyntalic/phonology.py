"""
Zyntalic Phonological System

Comprehensive phonology for Zyntalic featuring:
- Mixed Hangul-Latin phoneme inventory
- Syllable structure constraints
- Phonotactic rules
- Sound change processes
- Romanization system
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .utils.rng import get_rng

# -------------------- Phoneme Inventory --------------------

# Hangul consonants (onset/coda positions)
HANGUL_CONSONANTS = {
    # Stops
    'ᄀ': 'k',   'ᄁ': 'kʰ',   'ᄃ': 't',   'ᄄ': 'tʰ',
    'ᄇ': 'p',   'ᄈ': 'pʰ',
    # Fricatives
    'ᄉ': 's',   'ᄊ': 'sʰ',   'ᄒ': 'h',
    # Nasals
    'ᄂ': 'n',   'ᄆ': 'm',    'ᄋ': 'ŋ',
    # Liquids
    'ᄅ': 'l',
    # Affricates
    'ᄌ': 'ʧ',   'ᄍ': 'ʧʰ',   'ᄎ': 'ʧʰ',
    # Other
    'ᄏ': 'kʰ',  'ᄐ': 'tʰ',   'ᄑ': 'pʰ',
}

# Polish-inspired Latin consonants
LATIN_CONSONANTS = {
    # Stops
    'p': 'p',   'b': 'b',   't': 't',   'd': 'd',   'k': 'k',   'g': 'g',
    # Fricatives
    'f': 'f',   'v': 'v',   's': 's',   'z': 'z',   'ś': 'ɕ',   'ź': 'ʑ',
    'sz': 'ʃ',  'ż': 'ʒ',   'h': 'x',   'ch': 'x',
    # Nasals
    'm': 'm',   'n': 'n',   'ń': 'ɲ',
    # Liquids
    'l': 'l',   'ł': 'w',   'r': 'r',
    # Affricates
    'c': 'ʦ',   'dz': 'ʣ',  'ć': 'ʧ',   'dź': 'ʤ',
    'cz': 'ʧ',  'dż': 'ʤ',
}

# Hangul vowels
HANGUL_VOWELS = {
    'ᅡ': 'a',   'ᅢ': 'ɛ',   'ᅣ': 'ja',  'ᅤ': 'jɛ',
    'ᅥ': 'ʌ',   'ᅦ': 'e',   'ᅧ': 'jʌ',  'ᅨ': 'je',
    'ᅩ': 'o',   'ᅪ': 'wa',  'ᅫ': 'wɛ',  'ᅬ': 'we',
    'ᅭ': 'jo',  'ᅮ': 'u',   'ᅯ': 'wʌ',  'ᅰ': 'we',
    'ᅱ': 'wi',  'ᅲ': 'ju',  'ᅳ': 'ɯ',   'ᅴ': 'ɯi',
    'ᅵ': 'i',
}

# Latin vowels (Polish-inspired)
LATIN_VOWELS = {
    'a': 'a',   'ą': 'ã',   'e': 'e',   'ę': 'ẽ',
    'i': 'i',   'o': 'o',   'ó': 'u',   'u': 'u',
    'y': 'ɨ',
}

# Final consonants (codas)
HANGUL_CODAS = {
    'ᆨ': 'k',   'ᆩ': 'k',   'ᆪ': 'k',   'ᆫ': 'n',
    'ᆬ': 'n',   'ᆭ': 'n',   'ᆮ': 't',   'ᆯ': 'l',
    'ᆰ': 'l',   'ᆱ': 'l',   'ᆲ': 'l',   'ᆳ': 'l',
    'ᆴ': 'l',   'ᆵ': 'l',   'ᆶ': 'l',   'ᆷ': 'm',
    'ᆸ': 'p',   'ᆹ': 'p',   'ᆺ': 't',   'ᆻ': 't',
    'ᆼ': 'ŋ',   'ᆽ': 't',   'ᆾ': 't',   'ᆿ': 'k',
    'ᇀ': 'k',   'ᇁ': 'ŋ',   'ᇂ': 't',   '': '',
}

# -------------------- Phonotactic Constraints --------------------

class SyllableType(Enum):
    CV = "CV"           # Consonant-Vowel
    CVC = "CVC"         # Consonant-Vowel-Consonant
    CCV = "CCV"         # Consonant-Consonant-Vowel
    CCVC = "CCVC"       # Consonant-Consonant-Vowel-Consonant
    V = "V"             # Vowel only
    VC = "VC"           # Vowel-Consonant

@dataclass
class Phoneme:
    """Represents a phoneme with features."""
    symbol: str
    ipa: str
    script: str  # 'hangul' or 'latin'
    manner: str  # 'stop', 'fricative', 'nasal', etc.
    place: str   # 'bilabial', 'alveolar', etc.
    voice: bool  # voiced or voiceless

@dataclass
class Syllable:
    """Represents a phonological syllable."""
    onset: list[str]     # Initial consonant(s)
    nucleus: str         # Vowel
    coda: list[str]      # Final consonant(s)
    stress: bool = False
    tone: str | None = None

    @property
    def structure(self) -> SyllableType:
        """Get syllable type."""
        has_onset = bool(self.onset)
        has_coda = bool(self.coda)
        complex_onset = len(self.onset) > 1

        if not has_onset and not has_coda:
            return SyllableType.V
        elif not has_onset and has_coda:
            return SyllableType.VC
        elif has_onset and not has_coda:
            return SyllableType.CCV if complex_onset else SyllableType.CV
        else:  # has both
            return SyllableType.CCVC if complex_onset else SyllableType.CVC

class PhonologicalProcessor:
    """Main class for Zyntalic phonological operations."""

    def __init__(self, seed: str = "phonology"):
        self.rng = get_rng(seed)
        self._build_phoneme_inventory()
        self._build_phonotactic_rules()

    def _build_phoneme_inventory(self):
        """Build the complete phoneme inventory."""
        self.consonants = {}
        self.vowels = {}

        # Add Hangul consonants
        for hangul, ipa in HANGUL_CONSONANTS.items():
            self.consonants[hangul] = Phoneme(
                symbol=hangul, ipa=ipa, script='hangul',
                manner=self._get_manner(ipa), place=self._get_place(ipa),
                voice=self._is_voiced(ipa)
            )

        # Add Latin consonants
        for latin, ipa in LATIN_CONSONANTS.items():
            self.consonants[latin] = Phoneme(
                symbol=latin, ipa=ipa, script='latin',
                manner=self._get_manner(ipa), place=self._get_place(ipa),
                voice=self._is_voiced(ipa)
            )

        # Add vowels
        for hangul, ipa in HANGUL_VOWELS.items():
            self.vowels[hangul] = Phoneme(
                symbol=hangul, ipa=ipa, script='hangul',
                manner='vowel', place='', voice=True
            )

        for latin, ipa in LATIN_VOWELS.items():
            self.vowels[latin] = Phoneme(
                symbol=latin, ipa=ipa, script='latin',
                manner='vowel', place='', voice=True
            )

    def _build_phonotactic_rules(self):
        """Define phonotactic constraints."""
        # Valid consonant clusters
        self.valid_onsets = {
            # Polish-style clusters
            ('s', 'p'), ('s', 't'), ('s', 'k'), ('ś', 'p'), ('ś', 't'),
            ('sz', 'p'), ('sz', 't'), ('sz', 'k'), ('sz', 'ć'),
            ('p', 'r'), ('b', 'r'), ('t', 'r'), ('d', 'r'), ('k', 'r'), ('g', 'r'),
            ('p', 'ł'), ('b', 'ł'), ('k', 'ł'), ('g', 'ł'),
            ('f', 'r'), ('ch', 'r'),
            # Hangul-style (simplified)
            ('ᄀ', 'ᄅ'), ('ᄇ', 'ᄅ'), ('ᄃ', 'ᄅ'),
        }

        self.valid_codas = {
            # Single consonants (most common)
            ('n',), ('m',), ('ŋ',), ('l',), ('r',), ('t',), ('k',), ('p',),
            # Consonant clusters (limited)
            ('n', 't'), ('m', 'p'), ('ŋ', 'k'), ('l', 't'),
            # Hangul codas
            ('ᆫ',), ('ᆷ',), ('ᆯ',), ('ᆨ',), ('ᆮ',), ('ᆸ',),
        }

    def _get_manner(self, ipa: str) -> str:
        """Classify consonant by manner of articulation."""
        if ipa in 'ptk':
            return 'stop'
        elif ipa in 'fvszʃʒxh':
            return 'fricative'
        elif ipa in 'mn ɲŋ':
            return 'nasal'
        elif ipa in 'lr':
            return 'liquid'
        elif ipa in 'ʧʤʦʣ':
            return 'affricate'
        else:
            return 'other'

    def _get_place(self, ipa: str) -> str:
        """Classify consonant by place of articulation."""
        if ipa in 'pm':
            return 'bilabial'
        elif ipa in 'fv':
            return 'labiodental'
        elif ipa in 'tdsznlr':
            return 'alveolar'
        elif ipa in 'ʃʒʧʤ':
            return 'postalveolar'
        elif ipa in 'kg ɲŋ':
            return 'velar'
        else:
            return 'other'

    def _is_voiced(self, ipa: str) -> bool:
        """Determine if consonant is voiced."""
        return ipa in 'bdgvzʒmnɲŋlrʤʣ'

    def parse_syllable(self, syll_str: str) -> Syllable:
        """Parse a syllable string into phonological structure."""
        # This is a simplified parser - real implementation would be more complex
        onset = []
        nucleus = ""
        coda = []

        i = 0
        # Extract onset consonants
        while i < len(syll_str):
            char = syll_str[i]
            if char in self.vowels:
                break
            onset.append(char)
            i += 1

        # Extract nucleus (vowel)
        if i < len(syll_str) and syll_str[i] in self.vowels:
            nucleus = syll_str[i]
            i += 1

        # Extract coda consonants
        while i < len(syll_str):
            coda.append(syll_str[i])
            i += 1

        return Syllable(onset=onset, nucleus=nucleus, coda=coda)

    def is_valid_syllable(self, syllable: Syllable) -> bool:
        """Check if syllable follows phonotactic constraints."""
        # Check onset cluster validity
        if len(syllable.onset) > 1:
            onset_tuple = tuple(syllable.onset)
            if onset_tuple not in self.valid_onsets:
                return False

        # Check coda cluster validity
        if len(syllable.coda) > 0:
            coda_tuple = tuple(syllable.coda)
            if len(syllable.coda) == 1:
                # Single codas are generally OK
                pass
            elif coda_tuple not in self.valid_codas:
                return False

        # Must have a nucleus
        if not syllable.nucleus:
            return False

        return True

    def apply_sound_changes(self, word: str) -> str:
        """Apply phonological sound changes."""
        # Assimilation rules
        word = self._voice_assimilation(word)
        word = self._nasal_assimilation(word)
        word = self._sibilant_harmony(word)

        # Deletion rules
        word = self._vowel_deletion(word)
        word = self._consonant_cluster_simplification(word)

        # Insertion rules
        word = self._epenthesis(word)

        return word

    def _voice_assimilation(self, word: str) -> str:
        """Voicing assimilation across morpheme boundaries."""
        # Simplified: devoice before voiceless, voice before voiced
        rules = [
            (r'([bdg])([ptk])', r'p\2'),   # bdg -> ptk before ptk
            (r'([ptk])([bdg])', r'b\2'),   # ptk -> bdg before bdg
        ]

        for pattern, replacement in rules:
            word = re.sub(pattern, replacement, word)

        return word

    def _nasal_assimilation(self, word: str) -> str:
        """Nasal place assimilation."""
        rules = [
            (r'n([pk])', r'm\1'),    # n -> m before labials
            (r'n([kg])', r'ŋ\1'),    # n -> ŋ before velars
        ]

        for pattern, replacement in rules:
            word = re.sub(pattern, replacement, word)

        return word

    def _sibilant_harmony(self, word: str) -> str:
        """Sibilant harmony (Polish-style)."""
        # s/z harmonize with sz/ż in same word
        if 'sz' in word or 'ż' in word:
            word = word.replace('s', 'sz').replace('z', 'ż')

        return word

    def _vowel_deletion(self, word: str) -> str:
        """Delete unstressed vowels in certain contexts."""
        # Very simplified - delete vowels between identical consonants
        word = re.sub(r'([bcdfghjklmnpqrstvwxyz])[aeiou]\1', r'\1\1', word)
        return word

    def _consonant_cluster_simplification(self, word: str) -> str:
        """Simplify complex consonant clusters."""
        # Remove middle consonant from 3+ clusters
        word = re.sub(r'([ptk])([sz])([ptk])', r'\1\3', word)
        return word

    def _epenthesis(self, word: str) -> str:
        """Insert vowels to break up illegal clusters."""
        # Insert 'e' between certain consonant clusters
        word = re.sub(r'([sz])([ptk])([^aeiouąę])', r'\1e\2\3', word)
        return word

    def romanize(self, text: str) -> str:
        """Convert Zyntalic text to romanized form."""
        result = []

        for char in text:
            if char in HANGUL_CONSONANTS:
                result.append(HANGUL_CONSONANTS[char])
            elif char in HANGUL_VOWELS:
                result.append(HANGUL_VOWELS[char])
            elif char in HANGUL_CODAS:
                result.append(HANGUL_CODAS[char])
            else:
                result.append(char)  # Keep Latin chars as-is

        return ''.join(result)

    def generate_phonological_word(self, semantic_seed: str, syllable_count: int = 2) -> str:
        """Generate a phonologically valid Zyntalic word."""
        rng = get_rng(f"phon:{semantic_seed}")
        syllables = []

        for i in range(syllable_count):
            # Choose script preference based on position and randomness
            use_hangul = rng.random() < 0.7  # 70% Hangul preference

            # Generate onset
            onset = []
            if rng.random() < 0.8:  # 80% chance of onset
                if use_hangul:
                    consonants = [c for c, p in self.consonants.items() if p.script == 'hangul']
                else:
                    consonants = [c for c, p in self.consonants.items() if p.script == 'latin']

                if consonants:
                    onset.append(rng.choice(consonants))

                # Sometimes add second consonant for complex onset
                if rng.random() < 0.2 and len(onset) == 1:
                    second_c = rng.choice(consonants)
                    test_onset = tuple(onset + [second_c])
                    if test_onset in self.valid_onsets:
                        onset.append(second_c)

            # Generate nucleus (vowel)
            if use_hangul:
                vowels = [v for v, p in self.vowels.items() if p.script == 'hangul']
            else:
                vowels = [v for v, p in self.vowels.items() if p.script == 'latin']

            nucleus = rng.choice(vowels) if vowels else 'a'

            # Generate coda
            coda = []
            if rng.random() < 0.4:  # 40% chance of coda
                if use_hangul:
                    codas = list(HANGUL_CODAS.keys())
                    codas = [c for c in codas if c]  # Remove empty string
                else:
                    codas = ['n', 'm', 'l', 'r', 't', 'k', 'p']

                if codas:
                    coda.append(rng.choice(codas))

            syllable = Syllable(onset=onset, nucleus=nucleus, coda=coda)

            if self.is_valid_syllable(syllable):
                syllables.append(syllable)

        # Convert syllables to string
        word = ""
        for syll in syllables:
            word += "".join(syll.onset) + syll.nucleus + "".join(syll.coda)

        # Apply phonological processes
        word = self.apply_sound_changes(word)

        return word

    # -------------------- Test Compatibility Methods --------------------

    def generate_syllable(self) -> str:
        """Generate a random syllable (alias for compatibility)."""
        # Use the core syllable generation functions
        from .core import create_syllable, get_rng
        rng = get_rng("syllable_gen")
        return create_syllable(rng)

    def romanize_hangul(self, hangul_text: str) -> str:
        """Romanize Hangul text (alias for compatibility)."""
        # Simple romanization mapping
        romanization_map = {
            '안': 'an', '녕': 'nyeong', '하': 'ha', '세': 'se', '요': 'yo',
            '감': 'gam', '사': 'sa', '합': 'hab', '니': 'ni', '다': 'da',
            '이': 'i', '해': 'hae', '못': 'mot', '어': 'eo', '떻': 'tteok',
            '지': 'ji', '내': 'nae', '좋': 'joh', '은': 'eun', '아': 'a',
            '침': 'chim'
        }

        result = ""
        for char in hangul_text:
            if char in romanization_map:
                result += romanization_map[char]
            elif char.isspace():
                result += " "
            else:
                result += char  # Keep non-Hangul characters as-is

        return result

# -------------------- Utility Functions --------------------

def analyze_phonotactics(word: str) -> dict[str, any]:
    """Analyze the phonotactic structure of a word."""
    PhonologicalProcessor()

    analysis = {
        'word': word,
        'syllables': [],
        'phoneme_count': len(word),
        'consonant_clusters': [],
        'vowel_sequences': [],
        'script_mixing': False,
    }

    # Detect script mixing
    has_hangul = any(c in HANGUL_CONSONANTS or c in HANGUL_VOWELS for c in word)
    has_latin = any(c.isalpha() and c not in HANGUL_CONSONANTS and c not in HANGUL_VOWELS for c in word)
    analysis['script_mixing'] = has_hangul and has_latin

    # Find consonant clusters (simplified)
    consonants = set(HANGUL_CONSONANTS.keys()) | set(LATIN_CONSONANTS.keys())
    cluster = ""
    for char in word:
        if char in consonants:
            cluster += char
        else:
            if len(cluster) > 1:
                analysis['consonant_clusters'].append(cluster)
            cluster = ""

    # Find vowel sequences
    vowels = set(HANGUL_VOWELS.keys()) | set(LATIN_VOWELS.keys())
    vowel_seq = ""
    for char in word:
        if char in vowels:
            vowel_seq += char
        else:
            if len(vowel_seq) > 1:
                analysis['vowel_sequences'].append(vowel_seq)
            vowel_seq = ""

    return analysis

def phonological_distance(word1: str, word2: str) -> float:
    """Calculate phonological distance between two words."""
    # Simplified distance metric based on edit distance
    # Real implementation would use feature-based distance

    def char_distance(c1: str, c2: str) -> float:
        if c1 == c2:
            return 0.0
        # Same script = closer
        if (c1 in HANGUL_CONSONANTS and c2 in HANGUL_CONSONANTS) or \
           (c1 in LATIN_CONSONANTS and c2 in LATIN_CONSONANTS):
            return 0.5
        # Different scripts = farther
        return 1.0

    # Dynamic programming for edit distance with weighted substitutions
    m, n = len(word1), len(word2)
    dp = [[0.0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                substitution_cost = char_distance(word1[i-1], word2[j-1])
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + substitution_cost  # substitution
                )

    return dp[m][n] / max(m, n)  # Normalize by length

    # -------------------- Test Compatibility Methods --------------------

    def generate_syllable(self) -> str:
        """Generate a random syllable (alias for compatibility)."""
        # Use the core syllable generation functions
        from .core import create_syllable, get_rng
        rng = get_rng("syllable_gen")
        return create_syllable(rng)

    def romanize_hangul(self, hangul_text: str) -> str:
        """Romanize Hangul text (alias for compatibility)."""
        # Simple romanization mapping
        romanization_map = {
            '안': 'an', '녕': 'nyeong', '하': 'ha', '세': 'se', '요': 'yo',
            '감': 'gam', '사': 'sa', '합': 'hab', '니': 'ni', '다': 'da',
            '이': 'i', '해': 'hae', '못': 'mot', '어': 'eo', '떻': 'tteok',
            '지': 'ji', '내': 'nae', '좋': 'joh', '은': 'eun', '아': 'a',
            '침': 'chim'
        }

        result = ""
        for char in hangul_text:
            if char in romanization_map:
                result += romanization_map[char]
            elif char.isspace():
                result += " "
            else:
                result += char  # Keep non-Hangul characters as-is

        return result

# -------------------- Demo Function --------------------

def demo_phonology():
    """Demonstrate the phonological system."""
    processor = PhonologicalProcessor()

    print("=== Zyntalic Phonological System Demo ===\n")

    # Generate some words
    print("Generated phonological words:")
    test_seeds = ["water", "fire", "earth", "air", "love", "war", "peace", "time"]

    for seed in test_seeds:
        word = processor.generate_phonological_word(seed, syllable_count=2)
        romanized = processor.romanize(word)
        analysis = analyze_phonotactics(word)

        print(f"  {seed:8} → {word:12} [{romanized:15}] " +
              f"({'mixed' if analysis['script_mixing'] else 'uniform'} script)")

    # Show sound changes
    print("\nPhonological processes:")
    test_words = ["maskret", "antok", "sptkal", "뚧홧깍녹"]

    for word in test_words:
        changed = processor.apply_sound_changes(word)
        if changed != word:
            print(f"  {word:12} → {changed:12} (sound changes applied)")
        else:
            print(f"  {word:12}   {word:12} (no changes)")

    # Phonological distance
    print("\nPhonological distances:")
    word_pairs = [("뚧홧깍", "뚧홧거"), ("mask", "mast"), ("뚧홧깍", "polska"), ("fire", "water")]

    for w1, w2 in word_pairs:
        distance = phonological_distance(w1, w2)
        print(f"  {w1:10} ~ {w2:10} : {distance:.3f}")

if __name__ == "__main__":
    demo_phonology()
