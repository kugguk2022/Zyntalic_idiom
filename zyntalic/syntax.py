# -*- coding: utf-8 -*-
"""
Zyntalic syntax + lightweight English parsing.

Goal: be deterministic and dependency-light.
- Word order: Subject – Object – Verb – Context  (S-O-V-C)
- Plurals: Hungarian-ish suffixes
- Tense: present (default), past, future

This is not a full NLP parser. It's a stable heuristic that makes "good enough"
S-O-V-C rearrangements, with an optional spaCy-backed tokenizer if available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from . import nlp

# A tiny vowel-harmony proxy to get a Hungarian-ish feeling.
BACK_VOWELS = "aáoóuú"
FRONT_VOWELS = "eéiíöőüű"

_CONTEXT_MARKERS = {
    "in","on","at","with","from","to","by","because","when","while","after","before","if","as",
    "during","over","under","into","onto","between","within","without","against","through",
}

_COMMON_VERBS = {
    "am","is","are","was","were","be","been","being",
    "have","has","had","do","does","did",
    "say","says","said","make","makes","made","go","goes","went",
    "see","sees","saw","know","knows","knew","think","thinks","thought",
    "take","takes","took","come","comes","came","want","wants","wanted",
    "use","uses","used","find","finds","found","give","gives","gave",
    "tell","tells","told","work","works","worked","call","calls","called",
    "try","tries","tried","ask","asks","asked","need","needs","needed",
    "feel","feels","felt","become","becomes","became","leave","leaves","left",
    "put","puts","keep","keeps","kept","let","lets",
    "begin","begins","began","seem","seems","help","helps","helped",
    "talk","talks","talked","turn","turns","turned","start","starts","started",
    "show","shows","showed","play","plays","played","move","moves","moved",
    "live","lives","lived","believe","believes","believed",
    "bring","brings","brought","write","writes","wrote",
    "sit","sits","sat","stand","stands","stood",
}

@dataclass(frozen=True)
class ParsedSentence:
    subject: str
    verb: str
    obj: str
    context: str = ""
    tense: str = "present"  # present|past|future
    subj_plural: bool = False
    obj_plural: bool = False


def _tokenize(text: str, use_nlp: Optional[bool] = None) -> list[str]:
    # Keep apostrophes inside words; optionally use NLP backend.
    if use_nlp is None:
        use_nlp = nlp.backend_name() == "spacy"
    if use_nlp:
        tokens = [t["text"] for t in nlp.analyze_tokens(text)]
        return [t for t in tokens if t]

    out = []
    buff = []
    for ch in text.strip():
        if ch.isalnum() or ch in ("'", "’", "-"):
            buff.append(ch)
        else:
            if buff:
                out.append("".join(buff))
                buff = []
    if buff:
        out.append("".join(buff))
    return out


def _guess_plural(phrase: str) -> bool:
    w = phrase.strip().split()
    if not w:
        return False
    last = w[-1].lower()
    return last.endswith("s") and not last.endswith(("ss", "us", "is"))


def _guess_tense(tokens: Sequence[str], verb_idx: int) -> str:
    low = [t.lower() for t in tokens]
    if "will" in low[:verb_idx+1]:
        return "future"
    v = low[verb_idx] if 0 <= verb_idx < len(low) else ""
    if v.endswith("ed") or v in ("was","were","had","did"):
        return "past"
    return "present"


def _find_verb(tokens: Sequence[str]) -> int:
    # 1) explicit "will <verb>"
    low = [t.lower() for t in tokens]
    if "will" in low and low.index("will") + 1 < len(tokens):
        return low.index("will") + 1

    # 2) first token that looks like a verb
    for i,t in enumerate(low):
        if t in _COMMON_VERBS:
            return i
        if t.endswith(("ed","ing")) and len(t) > 3:
            return i
        # naive 3rd person present
        if t.endswith("s") and len(t) > 3 and t[:-1] in _COMMON_VERBS:
            return i

    # 3) fallback: middle
    return max(0, min(len(tokens)-1, len(tokens)//2))


def parse_english(text: str, *, use_nlp: Optional[bool] = None) -> ParsedSentence:
    tokens = _tokenize(text, use_nlp=use_nlp)
    if not tokens:
        return ParsedSentence(subject="", verb="", obj="", context="")

    vidx = _find_verb(tokens)
    tense = _guess_tense(tokens, vidx)

    # subject = tokens before verb
    subj_tokens = tokens[:vidx]
    verb_token = tokens[vidx] if vidx < len(tokens) else ""

    rest = tokens[vidx+1:] if vidx+1 < len(tokens) else []

    # split rest into object vs context using context markers
    obj_tokens = []
    ctx_tokens = []
    seen_ctx = False
    for t in rest:
        if not seen_ctx and t.lower() in _CONTEXT_MARKERS:
            seen_ctx = True
        if seen_ctx:
            ctx_tokens.append(t)
        else:
            obj_tokens.append(t)

    subject = " ".join(subj_tokens).strip()
    obj = " ".join(obj_tokens).strip()
    context = " ".join(ctx_tokens).strip()

    return ParsedSentence(
        subject=subject,
        verb=verb_token,
        obj=obj,
        context=context,
        tense=tense,
        subj_plural=_guess_plural(subject),
        obj_plural=_guess_plural(obj),
    )


def _hungarian_plural_suffix(word: str) -> str:
    # toy vowel harmony: if last vowel is back -> "ok" else "ek"
    w = word.lower()
    last_vowel = ""
    for ch in reversed(w):
        if ch in BACK_VOWELS + FRONT_VOWELS:
            last_vowel = ch
            break
    if last_vowel and last_vowel in BACK_VOWELS:
        return "ok"
    return "ek"


def pluralize(noun: str) -> str:
    noun = noun.strip()
    if not noun:
        return noun
    if noun.endswith("ur"):  # already "beyond many"
        return noun
    return noun + "-" + _hungarian_plural_suffix(noun)


def mark_tense(verb: str, tense: Optional[str]) -> str:
    verb = verb.strip()
    if not verb:
        return verb
    t = (tense or "present").lower()
    if t == "past":
        return verb + "é"
    if t == "future":
        return "va-" + verb
    return verb


def to_zyntalic_order(text: str) -> ParsedSentence:
    """
    Convert English text to ParsedSentence in Zyntalic surface order.
    We keep context as a tail field (handled in core.make_context).
    """
    ps = parse_english(text)
    # Nothing to do here besides return parsed pieces; core decides how to render.
    return ps
