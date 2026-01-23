from hypothesis import given, settings
from hypothesis import strategies as st

from zyntalic import syntax


@settings(max_examples=30)
@given(st.text(min_size=1, max_size=50))
def test_parse_english_returns_structure(text):
    ps = syntax.parse_english(text, use_nlp=False)
    assert ps is not None
    assert hasattr(ps, "subject")
    assert hasattr(ps, "verb")
