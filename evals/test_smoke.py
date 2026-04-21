from zyntalic.translator import translate_text


def test_translate_returns_rows():
    rows = translate_text("Hello world.")
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert "source" in rows[0]
    assert "target" in rows[0]
    assert "lemma" in rows[0]
    assert "engine" in rows[0]

def test_determinism_same_input_same_output():
    a = translate_text("I see the river at night.")
    b = translate_text("I see the river at night.")
    assert a == b

def test_ctx_tail_present_in_core_engine():
    rows = translate_text("Hello world.", engine="core")
    assert "⟦ctx:" in rows[0]["target"] or "[ctx:" in rows[0]["target"]
