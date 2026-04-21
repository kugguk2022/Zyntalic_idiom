"""
bifurcation_scanner.py
----------------------
Given a seed text and two anchor frame names, ranks lemmas by their
usefulness as neutral bifurcators — words that sit in the interference
zone between two semantic frames.

Three scores per lemma:
  interference  — how evenly the lemma's embedding is split between
                  Frame A and Frame B anchors (1.0 = perfect split)
  duality       — for verbs: does WordNet list both agentive AND
                  experiential uses? (boolean → 0.0 or 1.0)
  combined      — interference * 0.6 + duality * 0.4

Usage:
  python scripts/bifurcation_scanner.py \
      --text "path/to/seed.txt" \
      --frame-a "Sunzi_ArtOfWar" \
      --frame-b "Dostoevsky_BrothersKaramazov" \
      --top 20

Or import directly:
  from scripts.bifurcation_scanner import scan_bifurcators
  results = scan_bifurcators(text, frame_a, frame_b, top_k=20)
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Resolve repo root so we can import zyntalic regardless of cwd
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Optional deps — fail gracefully with clear messages
# ---------------------------------------------------------------------------
try:
    import spacy  # type: ignore
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False

try:
    import nltk
    from nltk.corpus import wordnet as wn  # type: ignore
    _WN_AVAILABLE = True
except ImportError:
    _WN_AVAILABLE = False

try:
    from zyntalic.core import ANCHORS, anchor_weights_for_vec, base_embedding
    _ZYNTALIC_AVAILABLE = True
except ImportError:
    _ZYNTALIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------
@dataclass
class LemmaScore:
    lemma: str
    pos: str                   # "VERB", "NOUN", "ADJ", etc.
    frame_a_weight: float      # softmax weight toward Frame A anchor
    frame_b_weight: float      # softmax weight toward Frame B anchor
    interference: float        # 1 - |a - b|  — 1.0 = perfect split
    has_duality: bool          # verb with both agentive + experiential uses
    combined: float            # final ranking score
    example_sentences: list[str]  # up to 3 sentences from seed text

    def __str__(self) -> str:
        dual_mark = " [dual]" if self.has_duality else ""
        return (
            f"{self.lemma:<22} {self.pos:<6}  "
            f"A={self.frame_a_weight:.2f}  B={self.frame_b_weight:.2f}  "
            f"interference={self.interference:.2f}  "
            f"combined={self.combined:.2f}{dual_mark}"
        )


# ---------------------------------------------------------------------------
# WordNet duality check
# ---------------------------------------------------------------------------

# Verb frames in WordNet that signal agentive use (subject is intentional agent)
_AGENTIVE_FRAMES = {
    1,   # "Something ----s"
    2,   # "Somebody ----s"
    8,   # "Somebody ----s somebody"
    9,   # "Somebody ----s something"
    10,  # "Something ----s something"
    11,  # "Somebody ----s to INFINITIVE"
    12,  # "Somebody ----s VERB-ing"
    13,  # "Somebody ----s that CLAUSE"
    15,  # "Somebody ----s PP"
    16,  # "Somebody ----s INFINITIVE"
}

# Verb frames that signal experiential use (subject is undergoer/experiencer)
_EXPERIENTIAL_FRAMES = {
    3,   # "It is ----ing"
    4,   # "Something is ----ing PP"
    5,   # "Something ----s Adjective"
    6,   # "Something ----s PP"
    7,   # "Something ----s to somebody"
    14,  # "Somebody ----s INFINITIVE"  (can be either, but often experiencer)
    17,  # "Somebody is ----ing"
    18,  # "Something is ----ing"
    19,  # "Something ----s somebody"
    20,  # "Something ----s Adjective/Noun INFINITIVE"
    21,  # "Somebody ----s Adjective/Noun"
    22,  # "Somebody ----s to somebody"
    23,  # "Somebody ----s on something"
    24,  # "Somebody ----s somebody INFINITIVE"
    25,  # "Somebody ----s somebody of something"
    26,  # "Somebody ----s somebody PP"
    27,  # "Somebody ----s somebody that CLAUSE"
    28,  # "Somebody ----s somebody to INFINITIVE"
    29,  # "Somebody ----s somebody into V-ing"
    30,  # "Somebody ----s something to somebody"
    31,  # "Somebody ----s something from somebody"
    32,  # "Somebody ----s somebody with something"
    33,  # "Somebody ----s somebody of something"
    34,  # "Somebody ----s something on somebody"
    35,  # "Somebody ----s somebody Adjective/Noun"
    36,  # "Somebody ----s something Adjective/Noun"
}

# High-signal experiential verbs by definition (feel, seem, appear, etc.)
_EXPERIENTIAL_LEMMAS = {
    "feel", "seem", "appear", "become", "remain", "stay", "look",
    "sound", "smell", "taste", "hear", "see", "notice", "realize",
    "understand", "know", "believe", "think", "suppose", "expect",
    "fear", "hope", "wish", "want", "need", "suffer", "endure",
    "experience", "perceive", "witness", "sense", "recall", "remember",
}

# High-signal agentive verbs
_AGENTIVE_LEMMAS = {
    "attack", "build", "create", "destroy", "command", "order",
    "plan", "execute", "deploy", "advance", "retreat", "position",
    "control", "dominate", "seize", "capture", "defend", "strike",
    "move", "direct", "organize", "manage", "lead", "coordinate",
}


def _check_wn_duality(lemma: str) -> bool:
    """
    Returns True if WordNet lists this verb with both agentive
    and experiential frame IDs, OR if it appears in both
    high-signal sets above.
    """
    if not _WN_AVAILABLE:
        # Fallback: check against the curated sets
        return lemma.lower() in _AGENTIVE_LEMMAS or lemma.lower() in _EXPERIENTIAL_LEMMAS

    synsets = wn.synsets(lemma, pos=wn.VERB)
    if not synsets:
        return False

    seen_agentive = lemma.lower() in _AGENTIVE_LEMMAS
    seen_experiential = lemma.lower() in _EXPERIENTIAL_LEMMAS

    for ss in synsets:
        for lemma_obj in ss.lemmas():
            frames = set(lemma_obj.frame_ids())
            if frames & _AGENTIVE_FRAMES:
                seen_agentive = True
            if frames & _EXPERIENTIAL_FRAMES:
                seen_experiential = True
        if seen_agentive and seen_experiential:
            return True

    return seen_agentive and seen_experiential


# ---------------------------------------------------------------------------
# Embedding interference score
# ---------------------------------------------------------------------------

def _interference_score(
    lemma: str,
    frame_a: str,
    frame_b: str,
    dim: int = 300,
) -> tuple[float, float, float]:
    """
    Returns (weight_a, weight_b, interference).
    interference = 1 - |weight_a - weight_b|
    Maximum = 1.0 when the lemma splits exactly 50/50 between the two frames.
    """
    if not _ZYNTALIC_AVAILABLE:
        raise RuntimeError("zyntalic package not found — run from repo root")

    vec = base_embedding(lemma, dim=dim)
    weights = anchor_weights_for_vec(vec, top_k=len(ANCHORS))
    weight_map = dict(weights)

    wa = weight_map.get(frame_a, 0.0)
    wb = weight_map.get(frame_b, 0.0)

    # Renormalize to just these two frames so scores are interpretable
    total = wa + wb
    if total > 0:
        wa /= total
        wb /= total
    else:
        wa = wb = 0.5

    interference = 1.0 - abs(wa - wb)
    return wa, wb, interference


# ---------------------------------------------------------------------------
# spaCy lemmatizer
# ---------------------------------------------------------------------------

def _extract_lemmas(text: str) -> dict:
    """
    Returns {lemma: {"pos": str, "sentences": [str]}} using spaCy.
    Falls back to simple whitespace tokenization if spaCy unavailable.
    """
    if not _SPACY_AVAILABLE:
        # Simple fallback
        result = {}
        for word in text.split():
            clean = word.strip(".,;:!?\"'()[]{}").lower()
            if clean and len(clean) > 2:
                if clean not in result:
                    result[clean] = {"pos": "UNKNOWN", "sentences": []}
        return result

    # Load the smallest model — install with: python -m spacy download en_core_web_sm
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("spaCy model not found. Run: python -m spacy download en_core_web_sm")
        sys.exit(1)

    doc = nlp(text)
    result = {}

    for sent in doc.sents:
        sent_text = sent.text.strip()
        for token in sent:
            if token.is_stop or token.is_punct or token.is_space:
                continue
            if len(token.lemma_) < 3:
                continue
            lemma = token.lemma_.lower()
            pos = token.pos_
            if pos not in ("VERB", "NOUN", "ADJ"):
                continue
            if lemma not in result:
                result[lemma] = {"pos": pos, "sentences": []}
            if sent_text not in result[lemma]["sentences"]:
                result[lemma]["sentences"].append(sent_text)

    return result


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan_bifurcators(
    text: str,
    frame_a: str,
    frame_b: str,
    top_k: int = 20,
    pos_filter: list[str] | None = None,
    min_interference: float = 0.6,
    dim: int = 300,
    verbose: bool = False,
) -> list[LemmaScore]:
    """
    Scan a seed text for lemmas that work as neutral bifurcators
    between frame_a and frame_b.

    Parameters
    ----------
    text            : seed text to scan
    frame_a         : anchor name, e.g. "Sunzi_ArtOfWar"
    frame_b         : anchor name, e.g. "Dostoevsky_BrothersKaramazov"
    top_k           : how many top results to return
    pos_filter      : if set, only consider these POS tags (e.g. ["VERB"])
    min_interference: discard lemmas below this threshold (0.0–1.0)
    dim             : embedding dimension
    verbose         : print progress to stderr

    Returns
    -------
    List of LemmaScore, sorted by combined score descending
    """
    if not _ZYNTALIC_AVAILABLE:
        raise RuntimeError(
            "Cannot import zyntalic. Run from the repo root or install with pip install -e ."
        )

    # Validate anchor names
    if frame_a not in ANCHORS:
        raise ValueError(f"Unknown anchor '{frame_a}'. Valid anchors: {sorted(ANCHORS)}")
    if frame_b not in ANCHORS:
        raise ValueError(f"Unknown anchor '{frame_b}'. Valid anchors: {sorted(ANCHORS)}")

    if verbose:
        print(f"Scanning text ({len(text)} chars) for bifurcators...", file=sys.stderr)
        print(f"  Frame A: {frame_a}", file=sys.stderr)
        print(f"  Frame B: {frame_b}", file=sys.stderr)

    # Step 1: extract lemmas
    lemma_map = _extract_lemmas(text)
    if verbose:
        print(f"  {len(lemma_map)} unique lemmas found", file=sys.stderr)

    # Step 2: optionally download NLTK WordNet data
    if _WN_AVAILABLE:
        try:
            nltk.data.find("corpora/wordnet")
        except LookupError:
            if verbose:
                print("  Downloading WordNet data...", file=sys.stderr)
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)

    # Step 3: score each lemma
    results: list[LemmaScore] = []
    total = len(lemma_map)

    for i, (lemma, meta) in enumerate(lemma_map.items()):
        pos = meta["pos"]
        sentences = meta["sentences"][:3]

        if pos_filter and pos not in pos_filter:
            continue

        if verbose and i % 50 == 0:
            print(f"  [{i}/{total}] scoring '{lemma}'...", file=sys.stderr)

        try:
            wa, wb, interference = _interference_score(lemma, frame_a, frame_b, dim=dim)
        except Exception:
            continue

        if interference < min_interference:
            continue

        # Duality check (verbs only — nouns and adjectives get 0.5 bonus if
        # they appear in both anchor lexicons, but we don't penalize them)
        if pos == "VERB":
            has_duality = _check_wn_duality(lemma)
            duality_score = 1.0 if has_duality else 0.0
        else:
            has_duality = False
            duality_score = 0.5  # neutral contribution for non-verbs

        combined = interference * 0.6 + duality_score * 0.4

        results.append(LemmaScore(
            lemma=lemma,
            pos=pos,
            frame_a_weight=round(wa, 3),
            frame_b_weight=round(wb, 3),
            interference=round(interference, 3),
            has_duality=has_duality,
            combined=round(combined, 3),
            example_sentences=sentences,
        ))

    # Step 4: sort and return top_k
    results.sort(key=lambda x: x.combined, reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def print_results(results: list[LemmaScore], show_sentences: bool = False) -> None:
    if not results:
        print("No bifurcators found above threshold.")
        return

    print(f"\n{'LEMMA':<22} {'POS':<6}  {'A':>5}  {'B':>5}  {'INTF':>6}  {'COMB':>6}  {'DUAL'}")
    print("─" * 72)
    for r in results:
        dual = "[+]" if r.has_duality else "   "
        print(
            f"{r.lemma:<22} {r.pos:<6}  "
            f"{r.frame_a_weight:>5.2f}  {r.frame_b_weight:>5.2f}  "
            f"{r.interference:>6.2f}  {r.combined:>6.2f}  {dual}"
        )
        if show_sentences and r.example_sentences:
            for s in r.example_sentences:
                snippet = s[:90] + "..." if len(s) > 90 else s
                print(f"    › {snippet}")

    print()
    pivot_verbs = [r for r in results if r.has_duality]
    neutral_nouns = [r for r in results if r.pos in ("NOUN", "ADJ") and r.interference > 0.8]

    print(f"Top pivot verbs (dual agentive+experiential): {len(pivot_verbs)}")
    if pivot_verbs:
        print("  " + ", ".join(r.lemma for r in pivot_verbs[:10]))

    print(f"Neutral nouns/adj in interference zone (>0.8): {len(neutral_nouns)}")
    if neutral_nouns:
        print("  " + ", ".join(r.lemma for r in neutral_nouns[:10]))


def export_json(results: list[LemmaScore], path: str) -> None:
    import json
    data = [
        {
            "lemma": r.lemma,
            "pos": r.pos,
            "frame_a_weight": r.frame_a_weight,
            "frame_b_weight": r.frame_b_weight,
            "interference": r.interference,
            "has_duality": r.has_duality,
            "combined": r.combined,
            "example_sentences": r.example_sentences,
        }
        for r in results
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Results written to {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Scan a seed text for neutral bifurcator lemmas between two semantic frames.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/bifurcation_scanner.py \\
      --text data/generation/clean/pg1342.txt \\
      --frame-a Sunzi_ArtOfWar \\
      --frame-b Dostoevsky_BrothersKaramazov \\
      --top 30 --sentences

  python scripts/bifurcation_scanner.py \\
      --text seed.txt \\
      --frame-a Plato_Republic \\
      --frame-b Darwin_OriginOfSpecies \\
      --pos VERB \\
      --out pivots.json

Valid anchor names:
  Homer_Iliad, Homer_Odyssey, Plato_Republic, Aristotle_Organon,
  Virgil_Aeneid, Dante_DivineComedy, Shakespeare_Sonnets, Goethe_Faust,
  Cervantes_DonQuixote, Milton_ParadiseLost, Melville_MobyDick,
  Darwin_OriginOfSpecies, Austen_PridePrejudice, Tolstoy_WarPeace,
  Dostoevsky_BrothersKaramazov, Laozi_TaoTeChing, Sunzi_ArtOfWar,
  Descartes_Meditations, Bacon_NovumOrganum, Spinoza_Ethics
        """,
    )
    p.add_argument("--text", required=True, help="Path to seed text file (UTF-8)")
    p.add_argument("--frame-a", required=True, dest="frame_a", help="Anchor name for Frame A")
    p.add_argument("--frame-b", required=True, dest="frame_b", help="Anchor name for Frame B")
    p.add_argument("--top", type=int, default=20, help="Number of results to return (default 20)")
    p.add_argument("--pos", choices=["VERB", "NOUN", "ADJ"], default=None,
                   help="Filter to a single POS tag")
    p.add_argument("--min-interference", type=float, default=0.6, dest="min_interference",
                   help="Minimum interference score (0.0–1.0, default 0.6)")
    p.add_argument("--dim", type=int, default=300, help="Embedding dimension (default 300)")
    p.add_argument("--sentences", action="store_true",
                   help="Show example sentences for each lemma")
    p.add_argument("--out", default=None, help="Export results as JSON to this path")
    p.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Read seed text
    try:
        with open(args.text, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.text}", file=sys.stderr)
        sys.exit(1)

    pos_filter = [args.pos] if args.pos else None

    results = scan_bifurcators(
        text=text,
        frame_a=args.frame_a,
        frame_b=args.frame_b,
        top_k=args.top,
        pos_filter=pos_filter,
        min_interference=args.min_interference,
        dim=args.dim,
        verbose=args.verbose,
    )

    print_results(results, show_sentences=args.sentences)

    if args.out:
        export_json(results, args.out)


if __name__ == "__main__":
    main()
