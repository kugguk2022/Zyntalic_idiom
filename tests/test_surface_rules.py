import importlib

import zyntalic.core as core
import zyntalic.translator as translator


def _script_counts(text: str) -> tuple[int, int]:
    hangul = sum("\uac00" <= ch <= "\ud7af" for ch in text)
    latin = sum(("a" <= ch.lower() <= "z") or ch in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ" for ch in text)
    return hangul, latin


def test_same_first_word_no_longer_collapses_sentence_seed(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    importlib.reload(translator)

    a = translator.translate_text("River remembers time.", mirror_rate=0.2, engine="core")[0]["target"]
    b = translator.translate_text("River forgets stone.", mirror_rate=0.2, engine="core")[0]["target"]

    assert a != b


def test_dirty_mappings_get_repaired_for_visible_surface_fields(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    importlib.reload(core)

    rng = core.get_rng("surface-rules")
    noun = core._map_term_to_zyntalic("journey", "nouns", rng=rng)
    adj = core._map_term_to_zyntalic("bright", "adjectives", rng=rng)
    verb = core._map_term_to_zyntalic("protected", "verbs", rng=rng)

    noun_hangul, noun_latin = _script_counts(noun)
    adj_hangul, adj_latin = _script_counts(adj)
    verb_hangul, verb_latin = _script_counts(verb)

    assert noun_latin >= 3
    assert adj_latin >= 3
    assert verb_latin >= 3
    assert noun_hangul == 0
    assert adj_hangul == 0
    assert verb_hangul == 0


def test_visible_surface_stays_latin_before_context_tail(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    importlib.reload(translator)

    target = translator.translate_text("Polish style should stay readable.", mirror_rate=0.2, engine="core")[0]["target"]
    visible_surface = target.split("⟦ctx:", 1)[0]
    hangul, latin = _script_counts(visible_surface)

    assert latin >= 6
    assert hangul == 0
