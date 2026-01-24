# -*- coding: utf-8 -*-
"""
Zyntalic Core (Schelling-anchored, Lexicon-aware)

- Deterministic via zyntalic.utils.rng.get_rng
- Respects S-O-V-C surface order with a Korean context tail
- Hangul-heavy nouns, Polish-heavy verbs
"""

import hashlib
import json
import math
import os
import random
from typing import Dict, List, Optional, Tuple

from .syntax import ParsedSentence, to_zyntalic_order

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
_LEXICON_CACHE: Optional[Dict[str, dict]] = None
_VOCAB_MAPPINGS_CACHE: Optional[Dict[str, Dict[str, str]]] = None
_PROJECTION_CACHE_SENTINEL = object()
_PROJECTION_CACHE = _PROJECTION_CACHE_SENTINEL


def load_vocabulary_mappings(filepath: str = "data/embeddings/vocabulary_mappings.json") -> Dict[str, Dict[str, str]]:
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
            with open(filepath, 'r', encoding='utf-8') as f:
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


def load_lexicons(dirpath: str = "lexicon") -> Dict[str, dict]:
    """Load anchor lexicons.

    Resolution order:
    1) If ``dirpath`` exists on disk, load ``*.json`` files from there.
    2) Otherwise load bundled lexicons from ``zyntalic.resources.lexicon``.
    """
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE

    data: Dict[str, dict] = {}

    # 1) Local filesystem (dev / overrides)
    if dirpath and os.path.isdir(dirpath):
        for fn in os.listdir(dirpath):
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(dirpath, fn), "r", encoding="utf-8") as f:
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


def _choose_motif(rng, anchors, weights):
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
    if motif_pool:
        return _weighted_sample(rng, motif_pool, motif_w)
    return _DEFAULT_MOTIFS[int(rng.random() * len(_DEFAULT_MOTIFS))]


# -------------------- Helpers --------------------
def compose_hangul_block(ch: str, ju: str, jo: str) -> str:
    """Compose a Hangul syllable block from jamo lists."""
    l_count, v_count, t_count = 19, 21, 28
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
    return "".join(sylls)


# -------------------- Sentence Templates --------------------
_MIRROR_STYLE = os.getenv("ZYNTALIC_MIRROR_STYLE", "zyntalic").strip().lower()

_EN_MIRROR_TEMPLATES = [
    "To {A} through {B}; to {B} through {A}.",
    "{A} begets {B}, and {B} reframes {A}.",
    "Seek {A} by {B}; keep {B} by {A}.",
    "Between {A} and {B}, the path mirrors back from {B} to {A}.",
]

_ZY_MIRROR_TEMPLATES = [
    "{A} {c} {B}; {B} {c} {A}.",
    "{A} {c} {B} · {B} {c} {A}.",
    "{A} {c} {B} ↔ {B} {c} {A}.",
    "{A} {c} {B} ⇄ {B} {c} {A}.",
    "{A} {c} {B} / {B} {c} {A}.",
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

def _mirror_tokens() -> List[str]:
    global _MIRROR_TOKENS
    if _MIRROR_TOKENS is not None:
        return _MIRROR_TOKENS
    seeds = [
        "by", "through", "via", "path", "echo", "return", "fold", "turn", "bind", "mirror"
    ]
    _MIRROR_TOKENS = [generate_word(f"mirror::{s}") for s in seeds]
    return _MIRROR_TOKENS

def _map_motif_word(word: str) -> str:
    vocab = load_vocabulary_mappings()
    key = (word or "").strip().lower()
    mapped = vocab.get("nouns", {}).get(key)
    return mapped or generate_word(f"motif::{key}")


def mirrored_sentence_anchored(rng, anchors, weights) -> str:
    """Chiasmus style."""
    A, B = _choose_motif(rng, anchors, weights)
    if _MIRROR_STYLE == "english":
        t = rng.choice(_EN_MIRROR_TEMPLATES)
        return t.format(A=A, B=B)
    # Zyntalic mirror rendering (keeps the chiasmus structure without English text)
    A_z = _map_motif_word(A)
    B_z = _map_motif_word(B)
    connector = rng.choice(_mirror_tokens())
    t = rng.choice(_ZY_MIRROR_TEMPLATES)
    return t.format(A=A_z, B=B_z, c=connector)


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

    # Try to translate to Zyntalic
    vocab_mappings = load_vocabulary_mappings()
    
    adj = vocab_mappings.get("adjectives", {}).get(adj_en, generate_word(f"adj::{adj_en}"))
    noun = vocab_mappings.get("nouns", {}).get(noun_en, generate_word(f"noun::{noun_en}"))
    verb = vocab_mappings.get("verbs", {}).get(verb_en, generate_word(f"verb::{verb_en}"))

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
def make_context(seed_key: str, word: str, chosen_anchors: List[str], pos_hint: str) -> str:
    lemma = lemmatize(word)
    ctx_anchors = "|".join(chosen_anchors)
    han = make_korean_tail(seed_key or lemma)
    # Only show the Korean tail, hide metadata
    return f"⟦ctx:han={han}⟧"


# -------------------- Embeddings --------------------
def base_embedding(key: str, dim: int = 300):
    if embed_text is not None:
        return embed_text(key, dim=dim)
    rng = get_rng(f"embed::{key}")
    return [rng.random() for _ in range(dim)]



_ANCHOR_VECS_CACHE: Optional[Dict[str, List[float]]] = None

def _get_anchor_vecs(dim: int = 300) -> Dict[str, List[float]]:
    global _ANCHOR_VECS_CACHE
    if _ANCHOR_VECS_CACHE is not None:
        return _ANCHOR_VECS_CACHE
    
    vecs = {}
    for name in ANCHORS:
        label = name.replace("_", " ")
        vecs[name] = _normalize(base_embedding(label, dim))
    _ANCHOR_VECS_CACHE = vecs
    return _ANCHOR_VECS_CACHE


def anchor_weights_for_vec(vec: List[float], top_k: int = 3):
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


def apply_projection(vec: List[float], W) -> List[float]:
    if np is None or W is None:
        return vec
    v = np.asarray(vec).reshape(1, -1) @ W
    v = v.flatten().tolist()
    return _normalize(v)


def generate_embedding(seed_key: str, dim: int = 300, W=None):
    vb = base_embedding(seed_key, dim)
    canon = apply_projection(vb, W)
    if canon == vb and W is None:
        # no projection: softly mix with anchors
        aw0 = anchor_weights_for_vec(vb, top_k=3)
        
        anchor_vecs = _get_anchor_vecs()
        vecs = [vb] + [anchor_vecs[a] for a, _ in aw0]
        
        ws = [0.5] + [0.5 * w for _, w in aw0]
        canon = _normalize(_mix(vecs, ws))
    aw = anchor_weights_for_vec(canon, top_k=3)
    return canon, aw


# -------------------- Public API --------------------
def generate_entry(seed_word: str, mirror_rate: float = 0.3, W=None) -> Dict:
    """
    Generate a full dictionary entry deterministically.
    seed_word: The English input (e.g., 'Love') which seeds ALL randomness.
    mirror_rate: Probability of using chiasmus templates (0.0-1.0).
                 Lower values produce more Zyntalic vocabulary output.
    """
    rng = get_rng(seed_word)

    # 1. Zyntalic Token (deterministic)
    w = generate_word(seed_word)
    pos_hint = "noun" if any(c in w for c in CHOSEONG) else "verb"

    # 2. Embedding & Anchors (seeded by the same key)
    emb, aw = generate_embedding(seed_word, W=W)
    chosen = [name for name, _ in aw]
    weights = [wgt for _, wgt in aw]

    # 3. Sentence
    if rng.random() < mirror_rate:
        sent_core = mirrored_sentence_anchored(rng, chosen, weights)
    else:
        sent_core = plain_sentence_anchored(rng, chosen, weights)

    # 4. Context (kept at the end per S-O-V-C rule)
    sentence = f"{sent_core} {make_context(seed_word, w, chosen, pos_hint)}"

    return {
        "word": w,
        "meaning": sent_core,
        "sentence": sentence,
        "anchors": aw,
        "embedding": emb,
    }


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
