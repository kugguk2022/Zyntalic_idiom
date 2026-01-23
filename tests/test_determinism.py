from hypothesis import given, settings
from hypothesis import strategies as st

from zyntalic import core


@settings(max_examples=50)
@given(st.text(min_size=1, max_size=30))
def test_generate_entry_deterministic(seed):
    a = core.generate_entry(seed, mirror_rate=0.2)
    b = core.generate_entry(seed, mirror_rate=0.2)
    assert a["sentence"] == b["sentence"]
    assert a["word"] == b["word"]
