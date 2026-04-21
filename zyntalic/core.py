"""
Zyntalic Core (Schelling-anchored, Lexicon-aware)

- Deterministic via zyntalic.utils.rng.get_rng
- Respects S-O-V-C surface order with a Korean context tail
- Hangul-heavy nouns, Polish-heavy verbs
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

# --- Deterministic RNG --------------------------------------------------------
try:
    from .utils.rng import get_rng
except ImportError:  # pragma: no cover - fallback for legacy layouts
    def get_rng(seed: str):
        digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
        return random.Random(int(digest[:8], 16))


# Optional dependencies
try:  # pragma: no cover - optional
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional
    np = None
try:  # pragma: no cover - optional
    from .embeddings import embed_text  # type: ignore
except Exception:  # pragma: no cover - optional
    embed_text = None

# -------------------- Alphabet --------------------
# Standard Hangul Jamo for deterministic block composition.
CHOSEONG = [
    "ᄀ",
    "ᄁ",
    "ᄂ",
    "ᄃ",
    "ᄄ",
    "ᄅ",
    "ᄆ",
    "ᄇ",
    "ᄈ",
    "ᄉ",
    "ᄊ",
    "ᄋ",
    "ᄌ",
    "ᄍ",
    "ᄎ",
    "ᄏ",
    "ᄐ",
    "ᄑ",
    "ᄒ",
]
JUNGSEONG = [
    "ᅡ",
    "ᅢ",
    "ᅣ",
    "ᅤ",
    "ᅥ",
    "ᅦ",
    "ᅧ",
    "ᅨ",
    "ᅩ",
    "ᅪ",
    "ᅫ",
    "ᅬ",
    "ᅭ",
    "ᅮ",
    "ᅯ",
    "ᅰ",
    "ᅱ",
    "ᅲ",
    "ᅳ",
    "ᅴ",
    "ᅵ",
]
JONGSEONG = [
    "",
    "ᆨ",
    "ᆩ",
    "ᆪ",
    "ᆫ",
    "ᆬ",
    "ᆭ",
    "ᆮ",
    "ᆯ",
    "ᆰ",
    "ᆱ",
    "ᆲ",
    "ᆳ",
    "ᆴ",
    "ᆵ",
    "ᆶ",
    "ᆷ",
    "ᆸ",
    "ᆹ",
    "ᆺ",
    "ᆻ",
    "ᆼ",
    "ᆽ",
    "ᆾ",
    "ᆿ",
    "ᇀ",
    "ᇁ",
    "ᇂ",
]

# Polish-inspired Latin characters.
POLISH_CONSONANTS = "bcćdźfghjklłmnńprsśtwzźż"
POLISH_VOWELS = "aąeęioóuy"
POLISH_LATIN_CHARS = set((POLISH_CONSONANTS + POLISH_VOWELS + "qvx") + (POLISH_CONSONANTS + POLISH_VOWELS + "qvx").upper())

# Strict vocab mode avoids generated syllables and keeps outputs within known mappings.
_STRICT_VOCAB = os.getenv("ZYNTALIC_STRICT_VOCAB", "1").lower() not in ("0", "false", "no", "off")
_CTX_READBACK = os.getenv("ZYNTALIC_CTX_READBACK", "0").lower() in ("1", "true", "yes", "on")
try:
    _CTX_KEYWORD_COUNT = max(1, int(os.getenv("ZYNTALIC_CTX_KEYWORDS", "3") or "3"))
except Exception:
    _CTX_KEYWORD_COUNT = 3

# Bound affixes for rhythm.
_AFFIX_PREFIXES = ["na", "ve", "sy", "lu", "ta", "ri"]
_AFFIX_SUFFIXES = ["ek", "is", "or", "um", "ja", "ti", "en", "os", "ar", "ul"]
try:
    _AFFIX_PREFIX_RATE = float(os.getenv("ZYNTALIC_PREFIX_RATE", "0.28"))
except Exception:
    _AFFIX_PREFIX_RATE = 0.28
try:
    _AFFIX_SUFFIX_RATE = float(os.getenv("ZYNTALIC_SUFFIX_RATE", "0.72"))
except Exception:
    _AFFIX_SUFFIX_RATE = 0.72

# Short sentence particles (standalone tokens).
_SENTENCE_PARTICLES = ["ne", "ra", "lo", "ka", "se", "ti"]
try:
    _PARTICLE_RATE = float(os.getenv("ZYNTALIC_PARTICLE_RATE", "0.5"))
except Exception:
    _PARTICLE_RATE = 0.5

# Fixed pivot connectors for mirrors (proverb feel).
_MIRROR_PIVOTS = ["na", "ve", "sy", "lu"]

_MIRROR_LEXICON_PATH = os.path.join("data", "embeddings", "mirror_lexicon.json")
_MIRROR_LEXICON: dict[str, str] | None = None

# -------------------- Anchors --------------------
ANCHORS = [
    "Homer_Iliad",
    "Homer_Odyssey",
    "Plato_Republic",
    "Aristotle_Organon",
    "Virgil_Aeneid",
    "Dante_DivineComedy",
    "Shakespeare_Sonnets",
    "Goethe_Faust",
    "Cervantes_DonQuixote",
    "Milton_ParadiseLost",
    "Melville_MobyDick",
    "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice",
    "Tolstoy_WarPeace",
    "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing",
    "Sunzi_ArtOfWar",
    "Descartes_Meditations",
    "Bacon_NovumOrganum",
    "Spinoza_Ethics",
]

# -------------------- Lexicon Prior --------------------
_LEXICON_CACHE: dict[str, dict] | None = None
_VOCAB_MAPPINGS_CACHE: dict[str, dict[str, str]] | None = None
_PROJECTION_CACHE_SENTINEL = object()
_PROJECTION_CACHE = _PROJECTION_CACHE_SENTINEL
_VOCAB_EMB_CACHE: dict[str, list[list[float]]] = {}
_VOCAB_EMB_WORDS: dict[str, list[str]] = {}


def load_vocabulary_mappings(filepath: str = "data/embeddings/vocabulary_mappings.json") -> dict[str, dict[str, str]]:
    """Load pre-generated vocabulary mappings from English to Zyntalic.

    Tries the provided path, then falls back to a repo-relative default. Returns
    an empty mapping on any error so translation can proceed without hard failure.
    """
    global _VOCAB_MAPPINGS_CACHE
    if _VOCAB_MAPPINGS_CACHE is not None:
        return _VOCAB_MAPPINGS_CACHE

    # Try to load from file (direct path)
    if os.path.exists(filepath):
        try:
            with open(filepath, encoding='utf-8') as f:
                _VOCAB_MAPPINGS_CACHE = json.load(f)
                return _VOCAB_MAPPINGS_CACHE
        except Exception:
            pass

    # Fallback to repo-relative path
    try:
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[1]
        alt_path = repo_root / "data" / "embeddings" / "vocabulary_mappings.json"
        if alt_path.exists():
            with alt_path.open('r', encoding='utf-8') as f:
                _VOCAB_MAPPINGS_CACHE = json.load(f)
                return _VOCAB_MAPPINGS_CACHE
    except Exception:
        pass

    # Return empty dict if not found
    _VOCAB_MAPPINGS_CACHE = {}
    return _VOCAB_MAPPINGS_CACHE


def _load_mirror_lexicon() -> dict[str, str]:
    global _MIRROR_LEXICON
    if _MIRROR_LEXICON is not None:
        return _MIRROR_LEXICON
    base = {
        "light": "dark",
        "dark": "light",
        "order": "chaos",
        "chaos": "order",
        "spirit": "flesh",
        "flesh": "spirit",
        "time": "eternity",
        "eternity": "time",
        "truth": "doubt",
        "doubt": "truth",
        "silence": "noise",
        "noise": "silence",
        "love": "hate",
        "hate": "love",
        "war": "peace",
        "peace": "war",
        "life": "death",
        "death": "life",
        "open": "closed",
        "closed": "open",
        "rise": "fall",
        "fall": "rise",
        "memory": "forgetting",
        "forgetting": "memory",
        "presence": "absence",
        "absence": "presence",
        "gain": "loss",
        "loss": "gain",
        "hope": "despair",
        "despair": "hope",
        "true": "false",
        "false": "true",
        "near": "far",
        "far": "near",
        "inside": "outside",
        "outside": "inside",
        "beginning": "ending",
        "ending": "beginning",
    }
    data = dict(base)
    if os.path.exists(_MIRROR_LEXICON_PATH):
        try:
            with open(_MIRROR_LEXICON_PATH, encoding="utf-8") as f:
                extra = json.load(f)
            if isinstance(extra, dict):
                for k, v in extra.items():
                    if isinstance(k, str) and isinstance(v, str):
                        data[k.lower()] = v.lower()
        except Exception:
            pass
    _MIRROR_LEXICON = data
    return _MIRROR_LEXICON


def _mirror_term(term: str) -> str | None:
    key = (term or "").strip().lower()
    if not key:
        return None
    lex = _load_mirror_lexicon()
    if key in lex:
        return lex[key]
    # simple negation handling
    for prefix in ("un", "in", "im", "ir", "il", "dis", "non"):
        if key.startswith(prefix) and len(key) > len(prefix) + 2:
            return key[len(prefix) :]
    if key.endswith("less") and len(key) > 6:
        return key[:-4] + "ful"
    if key.endswith("ful") and len(key) > 5:
        return key[:-3] + "less"
    return None


def load_lexicons(dirpath: str = "lexicon") -> dict[str, dict]:
    """Load anchor lexicons.

    Resolution order:
    1) If ``dirpath`` exists on disk, load ``*.json`` files from there.
    2) Otherwise load bundled lexicons from ``zyntalic.resources.lexicon``.
    """
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE

    data: dict[str, dict] = {}

    # 1) Local filesystem (dev / overrides)
    if dirpath and os.path.isdir(dirpath):
        for fn in os.listdir(dirpath):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    obj = json.load(f)
                key = fn[:-5]
                data[key] = obj
            except Exception:
                continue
        _LEXICON_CACHE = data
        return _LEXICON_CACHE

    # 2) Bundled resources
    try:
        from importlib import resources
        base = resources.files("zyntalic.resources.lexicon")
        for entry in base.iterdir():
            if not entry.name.endswith(".json"):
                continue
            try:
                obj = json.loads(entry.read_text(encoding="utf-8"))
                data[entry.name[:-5]] = obj
            except Exception:
                continue
    except Exception:
        # If resources aren't available (e.g., frozen apps), just return empty.
        data = {}

    _LEXICON_CACHE = data
    return _LEXICON_CACHE


def _weighted_sample(rng, pool, weights):
    """Deterministic weighted sample using passed RNG."""
    if not pool:
        return None
    total = sum(weights)
    r = rng.random() * total
    acc = 0.0
    for item, w in zip(pool, weights):
        acc += w
        if r <= acc:
            return item
    return pool[-1]


def _mix_lists(anchors, weights, field, base_list, k_sharpen=1.0):
    """Mix lexicon lists based on anchor weights."""
    lex = load_lexicons()
    pool, wts = [], []
    for a, w in zip(anchors, weights):
        if a in lex and field in lex[a]:
            for tok in lex[a][field]:
                pool.append(tok)
                wts.append(max(1e-6, w**k_sharpen))
    # smooth with base list
    for tok in base_list:
        pool.append(tok)
        wts.append(0.2)
    return pool, wts


def _choose_motif(rng, anchors, weights, mirror_state: MirrorState | None = None):
    """Deterministic motif selection."""
    lex = load_lexicons()
    motif_pool, motif_w = [], []
    for a, w in zip(anchors, weights):
        if a in lex and "motifs" in lex[a]:
            for pair in lex[a]["motifs"]:
                if isinstance(pair, list) and len(pair) == 2:
                    motif_pool.append(tuple(pair))
                    motif_w.append(max(1e-6, w))
        # Augment with a couple of anchor-specific pairs to reduce repetition.
        data = lex.get(a, {})
        nouns = data.get("nouns", [])
        verbs = data.get("verbs", [])
        if len(nouns) >= 2:
            i = int(rng.random() * len(nouns))
            j = int(rng.random() * len(nouns))
            if j == i:
                j = (i + 1) % len(nouns)
            motif_pool.append((nouns[i], nouns[j]))
            motif_w.append(max(1e-6, w * 0.6))
        if len(verbs) >= 2:
            i = int(rng.random() * len(verbs))
            j = int(rng.random() * len(verbs))
            if j == i:
                j = (i + 1) % len(verbs)
            motif_pool.append((verbs[i], verbs[j]))
            motif_w.append(max(1e-6, w * 0.4))
    # Always add a broader default motif pool at low weight to reduce repetition.
    for pair in _DEFAULT_MOTIFS:
        motif_pool.append(pair)
        motif_w.append(0.2)
    if not motif_pool:
        return _DEFAULT_MOTIFS[int(rng.random() * len(_DEFAULT_MOTIFS))]

    if mirror_state is None:
        return _weighted_sample(rng, motif_pool, motif_w)

    recent = set(mirror_state.recent_motifs)
    filtered_pool = []
    filtered_w = []
    for pair, w in zip(motif_pool, motif_w):
        key = mirror_state.motif_key(pair[0], pair[1])
        if key in recent:
            continue
        filtered_pool.append(pair)
        filtered_w.append(w)

    if filtered_pool:
        choice = _weighted_sample(rng, filtered_pool, filtered_w)
    else:
        choice = _weighted_sample(rng, motif_pool, motif_w)

    mirror_state.recent_motifs.append(mirror_state.motif_key(choice[0], choice[1]))
    return choice


def _pick_pair_from_terms(
    rng,
    terms: list,
    mirror_state: MirrorState | None = None,
) -> tuple[tuple[str, str], tuple[str, str]]:
    if not terms:
        raise ValueError("Need terms for mirror pairing.")

    # Normalize to list of dicts: {"term": str, "pos": str, "mirror": Optional[str]}
    normalized = []
    for t in terms:
        if isinstance(t, str):
            normalized.append({"term": t, "pos": "nouns", "mirror": None})
        elif isinstance(t, dict):
            term = (t.get("term") or "").strip()
            if not term:
                continue
            normalized.append({
                "term": term,
                "pos": t.get("pos") or "nouns",
                "mirror": t.get("mirror"),
            })
    if len(normalized) < 2 and not any(t.get("mirror") for t in normalized):
        # Not enough terms, fallback later.
        raise ValueError("Need at least two usable terms for mirror pairing.")

    def pick_from_list(items):
        return items[int(rng.random() * len(items))]

    with_mirror = [t for t in normalized if t.get("mirror")]
    if with_mirror:
        if mirror_state is None:
            t = pick_from_list(with_mirror)
            a = t["term"]
            b = t["mirror"]
            pos = t.get("pos") or "nouns"
            return (a, pos), (b, pos)
        recent = set(mirror_state.recent_motifs)
        for _ in range(min(10, len(with_mirror))):
            t = pick_from_list(with_mirror)
            a = t["term"]
            b = t["mirror"]
            key = mirror_state.term_key(a, b)
            if key in recent:
                continue
            mirror_state.recent_motifs.append(key)
            pos = t.get("pos") or "nouns"
            return (a, pos), (b, pos)
        # fallback even if repeated
        t = pick_from_list(with_mirror)
        a = t["term"]
        b = t["mirror"]
        mirror_state.recent_motifs.append(mirror_state.term_key(a, b))
        pos = t.get("pos") or "nouns"
        return (a, pos), (b, pos)

    # Otherwise pick two distinct terms.
    if mirror_state is None:
        a = pick_from_list(normalized)
        b = pick_from_list(normalized)
        if b["term"] == a["term"]:
            b = normalized[(normalized.index(a) + 1) % len(normalized)]
        return (a["term"], a.get("pos") or "nouns"), (b["term"], b.get("pos") or "nouns")

    recent = set(mirror_state.recent_motifs)
    max_tries = min(12, len(normalized) * 2)
    for _ in range(max_tries):
        a = pick_from_list(normalized)
        b = pick_from_list(normalized)
        if b["term"] == a["term"]:
            b = normalized[(normalized.index(a) + 1) % len(normalized)]
        key = mirror_state.term_key(a["term"], b["term"])
        if key in recent:
            continue
        mirror_state.recent_motifs.append(key)
        return (a["term"], a.get("pos") or "nouns"), (b["term"], b.get("pos") or "nouns")

    a = pick_from_list(normalized)
    b = pick_from_list(normalized)
    if b["term"] == a["term"]:
        b = normalized[(normalized.index(a) + 1) % len(normalized)]
    mirror_state.recent_motifs.append(mirror_state.term_key(a["term"], b["term"]))
    return (a["term"], a.get("pos") or "nouns"), (b["term"], b.get("pos") or "nouns")


# -------------------- Helpers --------------------
def compose_hangul_block(ch: str, ju: str, jo: str) -> str:
    """Compose a Hangul syllable block from jamo lists."""
    _l_count, v_count, t_count = 19, 21, 28
    s_base = 0xAC00
    try:
        l_idx = CHOSEONG.index(ch)
        v_idx = JUNGSEONG.index(ju)
        t_idx = JONGSEONG.index(jo)
    except ValueError:
        return ch + ju + jo
    s_index = (l_idx * v_count + v_idx) * t_count + t_idx
    return chr(s_base + s_index)


def fuse_syllables(root: str, marker: str) -> str:
    return root + marker


def lemmatize(word: str) -> str:
    suffixes = ["ować", "anie", "enie", "ing", "ed", "s"]
    for s in suffixes:
        if word.endswith(s):
            return word[: -len(s)]
    return word


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _l2(a):
    return (sum(x * x for x in a)) ** 0.5


def _normalize(v):
    n = _l2(v) or 1.0
    return [x / n for x in v]


def _cosine(a: list[float], b: list[float]) -> float:
    return _dot(a, b) / ((_l2(a) or 1.0) * (_l2(b) or 1.0))


def _mix(vecs, weights):
    out = [0.0] * len(vecs[0])
    for w, v in zip(weights, vecs):
        for i, x in enumerate(v):
            out[i] += w * x
    return out


# -------------------- Deterministic Syllables --------------------
def create_hangul_syllable(rng) -> str:
    ch = rng.choice(CHOSEONG)
    ju = rng.choice(JUNGSEONG)
    jo = rng.choice(JONGSEONG)
    return compose_hangul_block(ch, ju, jo)


def create_latin_syllable(rng) -> str:
    c = rng.choice(POLISH_CONSONANTS)
    v = rng.choice(POLISH_VOWELS)
    tail = rng.choice(["", rng.choice(POLISH_CONSONANTS)])
    return c + v + tail


def create_syllable(rng, pos: str = "noun") -> str:
    """
    Surface syllables are strictly Polish/Latin based.
    Hangul is reserved for the context tail.
    """
    return create_latin_syllable(rng)


def generate_word(seed_key: str) -> str:
    """Generate Zyntalic word deterministically from a seed string."""
    rng = get_rng(seed_key)
    sylls = [
        create_syllable(rng, pos=rng.choice(["noun", "verb"])),
        create_syllable(rng, pos=rng.choice(["noun", "verb"])),
        create_syllable(rng, pos=rng.choice(["noun", "verb"])),
    ]
    if rng.random() < 0.3:
        sylls[1] = fuse_syllables(sylls[1], rng.choice(["ć", "ść", "rz", "ż"]))
    word = "".join(sylls)
    # Bound affixes for rhythm (deterministic via RNG).
    if _AFFIX_PREFIXES and rng.random() < _AFFIX_PREFIX_RATE:
        word = rng.choice(_AFFIX_PREFIXES) + word
    if _AFFIX_SUFFIXES and rng.random() < _AFFIX_SUFFIX_RATE:
        word = word + rng.choice(_AFFIX_SUFFIXES)
    return word


# -------------------- Sentence Templates --------------------
_EN_MIRROR_TEMPLATES = [
    "To {A} through {B}; to {B} through {A}.",
    "{A} begets {B}, and {B} reframes {A}.",
    "Seek {A} by {B}; keep {B} by {A}.",
    "Between {A} and {B}, the path mirrors back from {B} to {A}.",
]

_ZY_MIRROR_TEMPLATES = [
    "{adj1} {A} {B} {v1} {c} {adj2} {B} {A} {v2}.",
    "{adj1} {A} {B} {v1} · {adj2} {B} {A} {v2}.",
    "{adj1} {A} {B} {v1}; {adj2} {B} {A} {v2}.",
    "{adj1} {A} {B} {v1} / {adj2} {B} {A} {v2}.",
]

_DEFAULT_MOTIFS = [
    ("order", "chaos"),
    ("light", "dark"),
    ("spirit", "flesh"),
    ("time", "eternity"),
    ("silence", "noise"),
    ("truth", "doubt"),
    ("memory", "forgetting"),
    ("fire", "water"),
    ("stone", "wind"),
    ("path", "wall"),
    ("rise", "fall"),
    ("birth", "death"),
    ("dream", "wake"),
    ("north", "south"),
    ("east", "west"),
    ("body", "shadow"),
    ("voice", "echo"),
    ("root", "branch"),
    ("seed", "ash"),
    ("gold", "iron"),
    ("mirror", "veil"),
    ("open", "closed"),
    ("near", "far"),
    ("inside", "outside"),
    ("center", "edge"),
    ("shape", "void"),
    ("law", "breach"),
    ("hunger", "satiety"),
    ("blood", "snow"),
    ("eye", "mask"),
    ("sun", "moon"),
    ("storm", "calm"),
]

_MIRROR_TOKENS = None

@dataclass
class MirrorState:
    motif_window: int = 12
    template_window: int = 6
    connector_window: int = 6
    recent_motifs: deque = field(default_factory=lambda: deque(maxlen=12))
    recent_templates: deque = field(default_factory=lambda: deque(maxlen=6))
    recent_connectors: deque = field(default_factory=lambda: deque(maxlen=6))

    def motif_key(self, a: str, b: str) -> tuple[str, str]:
        return tuple(sorted((a, b)))

    def term_key(self, a: str, b: str) -> tuple[str, str]:
        return tuple(sorted((a, b)))

def _mirror_tokens() -> list[str]:
    global _MIRROR_TOKENS
    if _MIRROR_TOKENS is not None:
        return _MIRROR_TOKENS
    pivots = list(dict.fromkeys(_MIRROR_PIVOTS))
    if _STRICT_VOCAB:
        vocab = load_vocabulary_mappings()
        verbs = list(vocab.get("verbs", {}).values())
        if verbs:
            rng = get_rng("mirror::tokens")
            picks = []
            seen = set()
            for _ in range(min(12, len(verbs))):
                tok = verbs[int(rng.random() * len(verbs))]
                tok = _repair_surface_profile(tok, "verbs", f"mirror-token::{tok}")
                if tok in seen:
                    continue
                seen.add(tok)
                picks.append(tok)
            _MIRROR_TOKENS = picks or [
                _repair_surface_profile(tok, "verbs", f"mirror-token::{tok}")
                for tok in verbs[:8]
            ]
        else:
            _MIRROR_TOKENS = []
        for pivot in pivots:
            if pivot not in _MIRROR_TOKENS:
                _MIRROR_TOKENS.append(pivot)
    else:
        seeds = [
            "by", "through", "via", "path", "echo", "return", "fold", "turn", "bind", "mirror"
        ]
        _MIRROR_TOKENS = [generate_word(f"mirror::{s}") for s in seeds] + pivots
    return _MIRROR_TOKENS

def _map_motif_word(word: str, *, rng, field: str = "nouns") -> str:
    vocab = load_vocabulary_mappings()
    return _map_term_to_zyntalic(word, field, rng=rng, vocab_mappings=vocab)


def _pick_mapped_token(rng, vocab_mappings, field: str, pool, weights, base_list) -> str:
    en = _weighted_sample(rng, pool, weights) or rng.choice(base_list)
    return _map_term_to_zyntalic(en, field, rng=rng, vocab_mappings=vocab_mappings)


def _stable_pick(values: Iterable[str], seed: str) -> str | None:
    vals = list(values)
    if not vals:
        return None
    rng = get_rng(seed)
    return vals[int(rng.random() * len(vals))]


def _surface_script_counts(text: str) -> dict[str, int]:
    counts = {"hangul": 0, "latin": 0}
    for ch in text or "":
        if "\uac00" <= ch <= "\ud7af":
            counts["hangul"] += 1
        elif ("a" <= ch.lower() <= "z") or ch in POLISH_LATIN_CHARS:
            counts["latin"] += 1
    return counts


def _surface_profile_ok(text: str, field: str) -> bool:
    candidate = re.sub(r"\s+", "", text or "")
    if not candidate:
        return False

    counts = _surface_script_counts(candidate)
    total = counts["hangul"] + counts["latin"]
    if total == 0:
        return False

    counts["hangul"] / total
    field = (field or "").lower()

    # Visible surface tokens should read as Polish/Latin; Hangul is reserved
    # for the context tail emitted in the metadata block.
    if field == "verbs":
        return counts["latin"] >= 3 and counts["hangul"] == 0
    if field == "adjectives":
        return counts["latin"] >= 3 and counts["hangul"] == 0
    if field == "nouns":
        return counts["latin"] >= 3 and counts["hangul"] == 0
    return counts["latin"] > 0


def _repair_surface_profile(text: str, field: str, seed_key: str) -> str:
    candidate = re.sub(r"\s+", "", text or "")
    if _surface_profile_ok(candidate, field):
        return candidate
    return generate_word(seed_key)


def _get_vocab_embeddings(field: str, vocab_mappings) -> tuple[list[str], list[list[float]]] | None:
    if embed_text is None:
        return None
    if field in _VOCAB_EMB_CACHE and field in _VOCAB_EMB_WORDS:
        return _VOCAB_EMB_WORDS[field], _VOCAB_EMB_CACHE[field]
    keys = list(vocab_mappings.get(field, {}).keys())
    if not keys:
        return None
    vecs = []
    for k in keys:
        try:
            vecs.append(_normalize(base_embedding(k, dim=300)))
        except Exception:
            vecs.append(_normalize(base_embedding(k or "x", dim=300)))
    _VOCAB_EMB_WORDS[field] = keys
    _VOCAB_EMB_CACHE[field] = vecs
    return keys, vecs


def _map_term_to_zyntalic(
    term: str,
    field: str,
    *,
    rng,
    vocab_mappings: dict[str, dict[str, str]] | None = None,
) -> str:
    if vocab_mappings is None:
        vocab_mappings = load_vocabulary_mappings()
    key = (term or "").strip().lower()

    # Pre-compute the surface-compatible value pool once for strict mode.
    if _STRICT_VOCAB:
        values = list(vocab_mappings.get(field, {}).values())
        surface_ok = [v for v in values if _surface_profile_ok(re.sub(r"\s+", "", v), field)]
        pick_pool = surface_ok if surface_ok else values
    else:
        pick_pool = None

    mapped = vocab_mappings.get(field, {}).get(key)
    if mapped:
        repaired = _repair_surface_profile(mapped, field, f"{field}::{key}")
        # In strict mode, if repair fell back to generate_word, prefer a vocab value instead.
        if _STRICT_VOCAB and pick_pool and repaired not in set(vocab_mappings.get(field, {}).values()):
            pick = _stable_pick(pick_pool, f"{field}::{key}")
            if pick:
                return _repair_surface_profile(pick, field, f"{field}::{key}")
        return repaired

    # Try semantic nearest neighbor among vocabulary keys if embeddings are available.
    emb_pack = _get_vocab_embeddings(field, vocab_mappings)
    if emb_pack is not None and key:
        keys, vecs = emb_pack
        try:
            q = _normalize(base_embedding(key, dim=300))
            best_i = 0
            best = -1.0
            for i, v in enumerate(vecs):
                s = _cosine(q, v)
                if s > best:
                    best = s
                    best_i = i
            match = keys[best_i]
            mapped = vocab_mappings.get(field, {}).get(match)
            if mapped:
                repaired = _repair_surface_profile(mapped, field, f"{field}::{key}")
                if _STRICT_VOCAB and pick_pool and repaired not in set(vocab_mappings.get(field, {}).values()):
                    pick = _stable_pick(pick_pool, f"{field}::{key}")
                    if pick:
                        return _repair_surface_profile(pick, field, f"{field}::{key}")
                return repaired
        except Exception:
            pass

    if _STRICT_VOCAB and pick_pool:
        pick = _stable_pick(pick_pool, f"{field}::{key}")
        if pick:
            return _repair_surface_profile(pick, field, f"{field}::{key}")
    return generate_word(f"{field}::{key}")


def mirrored_sentence_anchored(
    rng,
    anchors,
    weights,
    mirror_state: MirrorState | None = None,
    mirror_terms: list[dict[str, str]] | None = None,
) -> str:
    """Chiasmus style (Zyntalic mirror templates)."""
    if mirror_terms and len(mirror_terms) >= 2:
        (A, A_field), (B, B_field) = _pick_pair_from_terms(rng, mirror_terms, mirror_state=mirror_state)
    else:
        A, B = _choose_motif(rng, anchors, weights, mirror_state=mirror_state)
        A_field = "nouns"
        B_field = "nouns"

    # Zyntalic mirror rendering (keeps the chiasmus structure without English text)
    A_z = _map_motif_word(A, rng=rng, field=A_field)
    B_z = _map_motif_word(B, rng=rng, field=B_field)

    vocab_mappings = load_vocabulary_mappings()
    base_adj = ["bright", "mysterious", "ancient", "vivid", "whimsical"]
    base_verb = ["weaves", "reveals", "hides", "balances"]
    pool_adj, w_adj = _mix_lists(anchors, weights, "adjectives", base_adj)
    pool_verb, w_verb = _mix_lists(anchors, weights, "verbs", base_verb)

    adj1 = _pick_mapped_token(rng, vocab_mappings, "adjectives", pool_adj, w_adj, base_adj)
    adj2 = _pick_mapped_token(rng, vocab_mappings, "adjectives", pool_adj, w_adj, base_adj)
    if adj2 == adj1:
        adj2 = _pick_mapped_token(rng, vocab_mappings, "adjectives", pool_adj, w_adj, base_adj)

    v1 = _pick_mapped_token(rng, vocab_mappings, "verbs", pool_verb, w_verb, base_verb)
    v2 = _pick_mapped_token(rng, vocab_mappings, "verbs", pool_verb, w_verb, base_verb)
    if v2 == v1:
        v2 = _pick_mapped_token(rng, vocab_mappings, "verbs", pool_verb, w_verb, base_verb)

    connectors = _mirror_tokens()
    if connectors:
        if mirror_state is None:
            connector = rng.choice(connectors)
        else:
            recent = set(mirror_state.recent_connectors)
            choices = [c for c in connectors if c not in recent] or connectors
            connector = rng.choice(choices)
            mirror_state.recent_connectors.append(connector)
    else:
        connector = _map_motif_word("mirror", rng=rng, field="verbs")

    templates = _ZY_MIRROR_TEMPLATES
    if mirror_state is None:
        t = rng.choice(templates)
    else:
        avail = [i for i in range(len(templates)) if i not in mirror_state.recent_templates]
        idx = rng.choice(avail) if avail else rng.randrange(len(templates))
        mirror_state.recent_templates.append(idx)
        t = templates[idx]
    return t.format(A=A_z, B=B_z, c=connector, adj1=adj1, adj2=adj2, v1=v1, v2=v2)


def plain_sentence_anchored(rng, anchors, weights) -> str:
    """Standard style using Lexicon Lists and Zyntalic vocabulary."""
    base_adj = ["bright", "mysterious", "ancient", "vivid", "whimsical"]
    base_noun = ["journey", "whisper", "echo", "saga", "pattern"]
    base_verb = ["weaves", "reveals", "hides", "balances"]

    pool_adj, w_adj = _mix_lists(anchors, weights, "adjectives", base_adj)
    pool_noun, w_noun = _mix_lists(anchors, weights, "nouns", base_noun)
    pool_verb, w_verb = _mix_lists(anchors, weights, "verbs", base_verb)

    adj_en = _weighted_sample(rng, pool_adj, w_adj) or rng.choice(base_adj)
    noun_en = _weighted_sample(rng, pool_noun, w_noun) or rng.choice(base_noun)
    verb_en = _weighted_sample(rng, pool_verb, w_verb) or rng.choice(base_verb)

    vocab_mappings = load_vocabulary_mappings()

    adj = _map_term_to_zyntalic(adj_en, "adjectives", rng=rng, vocab_mappings=vocab_mappings)
    noun = _map_term_to_zyntalic(noun_en, "nouns", rng=rng, vocab_mappings=vocab_mappings)
    verb = _map_term_to_zyntalic(verb_en, "verbs", rng=rng, vocab_mappings=vocab_mappings)

    particle = ""
    if _SENTENCE_PARTICLES and rng.random() < _PARTICLE_RATE:
        particle = rng.choice(_SENTENCE_PARTICLES)
    if particle:
        return f"{adj} {noun} {verb} {particle}"
    return f"{adj} {noun} {verb}"


# -------------------Korean tail ------------------------
def make_korean_tail(seed_key: str) -> str:
    """Deterministic Hangul-only tail used only in the final context block."""
    rng = get_rng(f"kctx::{seed_key}")
    sylls = [create_hangul_syllable(rng) for _ in range(2)]
    if rng.random() < 0.5:
        sylls.append(create_hangul_syllable(rng))
    return "".join(sylls)


# -------------------- Context Block --------------------
def make_context(
    seed_key: str,
    word: str,
    chosen_anchors: list[str],
    pos_hint: str,
    ctx_terms: list[str] | None = None,
) -> str:
    lemma = lemmatize(word)
    "|".join(chosen_anchors)
    han = make_korean_tail(seed_key or lemma)
    if _CTX_READBACK and ctx_terms:
        keys = "|".join(ctx_terms[:2])
        return f"⟦ctx:han={han}; key={keys}⟧"
    # Only show the Korean tail, hide metadata
    return f"⟦ctx:han={han}⟧"


# -------------------- Embeddings --------------------
def base_embedding(key: str, dim: int = 300):
    if embed_text is not None:
        return embed_text(key, dim=dim)
    rng = get_rng(f"embed::{key}")
    return [rng.random() for _ in range(dim)]



_ANCHOR_VECS_CACHE: dict[str, list[float]] | None = None

def _get_anchor_vecs(dim: int = 300) -> dict[str, list[float]]:
    global _ANCHOR_VECS_CACHE
    if _ANCHOR_VECS_CACHE is not None:
        return _ANCHOR_VECS_CACHE

    vecs = {}
    for name in ANCHORS:
        label = name.replace("_", " ")
        vecs[name] = _normalize(base_embedding(label, dim))
    _ANCHOR_VECS_CACHE = vecs
    return _ANCHOR_VECS_CACHE


def anchor_weights_for_vec(vec: list[float], top_k: int = 3):
    v = _normalize(vec)
    scores = []

    # Use lazy getter
    anchor_vecs = _get_anchor_vecs(len(v))

    for a, av in anchor_vecs.items():
        scores.append((a, _dot(v, _normalize(av))))
    scores.sort(key=lambda x: x[1], reverse=True)
    top = scores[:top_k]
    m = max(s for _, s in top) if top else 0.0
    exps = [math.exp(s - m) for _, s in top]
    Z = sum(exps) or 1.0
    weights = [e / Z for e in exps]
    return [(name, w) for (name, _), w in zip(top, weights)]


def _normalize_anchor_override(anchor_weights: list[tuple[str, float]] | None) -> list[tuple[str, float]]:
    merged: dict[str, float] = {}
    order: list[str] = []
    for item in anchor_weights or []:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        name = str(item[0]).strip()
        if not name:
            continue
        try:
            weight = float(item[1])
        except Exception:
            continue
        if weight <= 0:
            continue
        if name not in merged:
            order.append(name)
            merged[name] = 0.0
        merged[name] += weight

    total = sum(merged.values())
    if total <= 0:
        return []
    return [(name, merged[name] / total) for name in order]


def load_projection(path: str = "models/W.npy"):
    if np is None:
        return None
    if not os.path.exists(path):
        return None
    try:
        return np.load(path)
    except Exception:
        return None


def get_projection(path: str = "models/W.npy"):
    """Load and memoize projection matrix so repeated translations avoid disk I/O."""
    global _PROJECTION_CACHE
    if _PROJECTION_CACHE is not _PROJECTION_CACHE_SENTINEL:
        return _PROJECTION_CACHE
    _PROJECTION_CACHE = load_projection(path)
    return _PROJECTION_CACHE


def apply_projection(vec: list[float], W) -> list[float]:
    if np is None or W is None:
        return vec
    v = np.asarray(vec).reshape(1, -1) @ W
    v = v.flatten().tolist()
    return _normalize(v)


def generate_embedding(
    seed_key: str,
    dim: int = 300,
    W=None,
    anchor_weights_override: list[tuple[str, float]] | None = None,
):
    vb = base_embedding(seed_key, dim)
    canon = apply_projection(vb, W)
    forced = _normalize_anchor_override(anchor_weights_override)
    if forced:
        anchor_vecs = _get_anchor_vecs(len(canon))
        vecs = [canon]
        ws = [0.3]
        for name, weight in forced:
            av = anchor_vecs.get(name)
            if av is None:
                continue
            vecs.append(av)
            ws.append(0.7 * weight)
        canon = _normalize(_mix(vecs, ws)) if len(vecs) > 1 else canon
        aw = forced
    elif anchor_weights_override is not None:
        aw = []
    elif canon == vb and W is None:
        # no projection: softly mix with anchors
        aw0 = anchor_weights_for_vec(vb, top_k=3)

        anchor_vecs = _get_anchor_vecs()
        vecs = [vb] + [anchor_vecs[a] for a, _ in aw0]

        ws = [0.5] + [0.5 * w for _, w in aw0]
        canon = _normalize(_mix(vecs, ws))
        aw = anchor_weights_for_vec(canon, top_k=3)
    else:
        aw = anchor_weights_for_vec(canon, top_k=3)
    return canon, aw


def _build_context_terms(
    mirror_terms: list[dict[str, str]] | None,
    rng,
) -> list[str] | None:
    """Map optional readback terms into deterministic Zyntalic context keywords."""
    if not (_CTX_READBACK and mirror_terms):
        return None

    ctx_terms: list[str] = []
    for t in mirror_terms:
        if len(ctx_terms) >= max(1, _CTX_KEYWORD_COUNT):
            break
        if isinstance(t, dict):
            term = t.get("term") or ""
            field = t.get("pos") or "nouns"
        else:
            term = str(t)
            field = "nouns"
        if not term:
            continue
        ctx_terms.append(_map_term_to_zyntalic(term, field, rng=rng))
    return ctx_terms


def _generate_entry_legacy(
    seed_word: str,
    mirror_rate: float = 0.3,
    W=None,
    mirror_state: MirrorState | None = None,
    mirror_terms: list[dict[str, str]] | None = None,
    anchor_weights_override: list[tuple[str, float]] | None = None,
) -> dict:
    """Legacy single-pass generator retained as deterministic fallback."""
    rng = get_rng(seed_word)

    w = generate_word(seed_word)
    pos_hint = "noun" if any(c in w for c in CHOSEONG) else "verb"

    emb, aw = generate_embedding(seed_word, W=W, anchor_weights_override=anchor_weights_override)
    chosen = [name for name, _ in aw]
    weights = [wgt for _, wgt in aw]

    ctx_terms = _build_context_terms(mirror_terms, rng)

    if rng.random() < mirror_rate:
        sent_core = mirrored_sentence_anchored(
            rng,
            chosen,
            weights,
            mirror_state=mirror_state,
            mirror_terms=mirror_terms,
        )
    else:
        sent_core = plain_sentence_anchored(rng, chosen, weights)

    sentence = f"{sent_core} {make_context(seed_word, w, chosen, pos_hint, ctx_terms=ctx_terms)}"

    return {
        "word": w,
        "meaning": sent_core,
        "sentence": sentence,
        "anchors": aw,
        "embedding": emb,
    }


def _generate_entry_staged(
    seed_word: str,
    mirror_rate: float = 0.3,
    W=None,
    mirror_state: MirrorState | None = None,
    mirror_terms: list[dict[str, str]] | None = None,
    anchor_weights_override: list[tuple[str, float]] | None = None,
) -> dict:
    """Rule-guided staged generator.

    Stages:
    1) Lexical token selection
    2) Semantic grounding (embedding + anchors)
    3) Surface realization (plain vs mirrored)
    4) Context composition (final context tail)
    """
    # Test hook to verify deterministic fallback behavior.
    if os.getenv("ZYNTALIC_STAGE_FORCE_FAIL", "0").lower() in ("1", "true", "yes", "on"):
        raise RuntimeError("Forced staged-generation failure")

    rng = get_rng(seed_word)

    # Stage 1: lexical token
    token = generate_word(seed_word)
    pos_hint = "noun" if any(c in token for c in CHOSEONG) else "verb"

    # Stage 2: semantic grounding
    embedding, anchor_weights = generate_embedding(
        seed_word,
        W=W,
        anchor_weights_override=anchor_weights_override,
    )
    chosen = [name for name, _ in anchor_weights]
    weights = [wgt for _, wgt in anchor_weights]

    # Stage 3: surface realization
    if rng.random() < mirror_rate:
        surface = mirrored_sentence_anchored(
            rng,
            chosen,
            weights,
            mirror_state=mirror_state,
            mirror_terms=mirror_terms,
        )
    else:
        surface = plain_sentence_anchored(rng, chosen, weights)

    # Stage 4: context tail
    ctx_terms = _build_context_terms(mirror_terms, rng)
    sentence = f"{surface} {make_context(seed_word, token, chosen, pos_hint, ctx_terms=ctx_terms)}"

    return {
        "word": token,
        "meaning": surface,
        "sentence": sentence,
        "anchors": anchor_weights,
        "embedding": embedding,
    }


def _use_staged_generator() -> bool:
    return os.getenv("ZYNTALIC_USE_STAGED_GENERATOR", "1").lower() not in ("0", "false", "no", "off")


# -------------------- Public API --------------------
def generate_entry(
    seed_word: str,
    mirror_rate: float = 0.3,
    W=None,
    mirror_state: MirrorState | None = None,
    mirror_terms: list[dict[str, str]] | None = None,
    anchor_weights_override: list[tuple[str, float]] | None = None,
) -> dict:
    """
    Generate a full dictionary entry deterministically.
    seed_word: The English input (e.g., 'Love') which seeds ALL randomness.
    mirror_rate: Probability of using chiasmus templates (0.0-1.0).
                 Lower values produce more Zyntalic vocabulary output.
    """
    if _use_staged_generator():
        try:
            return _generate_entry_staged(
                seed_word,
                mirror_rate=mirror_rate,
                W=W,
                mirror_state=mirror_state,
                mirror_terms=mirror_terms,
                anchor_weights_override=anchor_weights_override,
            )
        except Exception:
            # Deterministic fallback path keeps generation available under stage failures.
            return _generate_entry_legacy(
                seed_word,
                mirror_rate=mirror_rate,
                W=W,
                mirror_state=mirror_state,
                mirror_terms=mirror_terms,
                anchor_weights_override=anchor_weights_override,
            )

    return _generate_entry_legacy(
        seed_word,
        mirror_rate=mirror_rate,
        W=W,
        mirror_state=mirror_state,
        mirror_terms=mirror_terms,
        anchor_weights_override=anchor_weights_override,
    )


def export_to_txt(entries, filename="zyntalic_words.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for e in entries:
            anchors_str = ";".join(f"{a}:{w:.3f}" for a, w in e["anchors"])
            emb_str = ",".join(f"{v:.6f}" for v in e["embedding"])
            f.write(
                f"{e['word']}\t{e['meaning']}\t{e['sentence']}\t{anchors_str}\t{emb_str}\n"
            )


def generate_words(
    n: int = 1000,
    use_projection: bool = True,
    root_seed: str = "zyntalic_default",
):
    """
    Deterministic bulk generator.
    - Same (n, use_projection, root_seed) -> same wordlist every run.
    - Different root_seed -> different stable lexicon.
    """
    W = load_projection("models/W.npy") if use_projection else None
    out = []
    seen = set()
    i = 0
    while len(out) < n:
        seed = f"{root_seed}:{i}"
        e = generate_entry(seed, W=W)
        if e["word"] not in seen:
            seen.add(e["word"])
            out.append(e)
        i += 1
        if i > n * 10:  # safety
            break
    return out


def generate_words_demo(n=10):
    """Generate n sample words using integer seeds for consistency."""
    results = []
    W = load_projection()
    for i in range(n):
        seed = f"concept_{i}"
        results.append(generate_entry(seed, W=W))
    return results


if __name__ == "__main__":
    print("--- Zyntalic Deterministic Core Test ---")

    e1 = generate_entry("Love")
    e2 = generate_entry("Love")
    e3 = generate_entry("War")

    print(f"Input 'Love' -> {e1['word']} | {e1['meaning']}")
    print(f"Input 'Love' -> {e2['word']} | {e2['meaning']}")
    print(f"Input 'War'  -> {e3['word']} | {e3['meaning']}")

    assert e1["word"] == e2["word"], "CRITICAL FAIL: Non-deterministic output!"
    print("\nSUCCESS: Output is deterministic.")

    print("\nGenerating demo lexicon...")
    entries = generate_words(n=20, use_projection=True, root_seed="demo_seed")
    export_to_txt(entries, "zyntalic_words_demo.txt")
    print("Wrote zyntalic_words_demo.txt")
