from __future__ import annotations

import hashlib
import random


def stable_seed(seed: str) -> int:
    """
    Turn an arbitrary string seed into a stable 64-bit integer.
    """
    data = str(seed).encode("utf-8")
    digest = hashlib.blake2b(data, digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=False)

def get_rng(seed: str) -> random.Random:
    """
    Deterministic RNG instance derived from `seed`.
    """
    return random.Random(stable_seed(seed))
