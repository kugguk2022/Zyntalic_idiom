from hypothesis import given, settings
from hypothesis import strategies as st

from zyntalic import core


def setup_module():
    """Populate lazy caches outside Hypothesis's per-example timing window."""
    for seed in (
        "__hypothesis_cache_warmup__",
        chr(0xE9),
        chr(0x6F22),
        chr(0x1F642),
        chr(0x9F),
    ):
        core.generate_entry(seed, mirror_rate=0.2)


@settings(max_examples=50)
@given(st.text(min_size=1, max_size=30))
def test_generate_entry_deterministic(seed):
    a = core.generate_entry(seed, mirror_rate=0.2)
    b = core.generate_entry(seed, mirror_rate=0.2)
    assert a["sentence"] == b["sentence"]
    assert a["word"] == b["word"]
