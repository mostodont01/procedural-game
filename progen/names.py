"""Deterministic random names and seeded sub-generators."""

from __future__ import annotations

import hashlib
import random

ONSETS = ["b", "br", "c", "cr", "d", "dr", "f", "g", "gr", "h", "k", "kr", "l", "m", "n",
          "p", "pr", "r", "s", "st", "t", "tr", "v", "vr", "z", "th", "sh", "x", "y", "qu"]
VOWELS = ["a", "e", "i", "o", "u", "ae", "y", "io", "ei", "ou"]
CODAS = ["", "", "n", "r", "l", "s", "th", "x", "m", "k", "nd"]


def rng_for(seed: int, tag: str) -> random.Random:
    """An independent RNG per subsystem, so changing one part of the generator
    doesn't reshuffle everything else for the same seed."""
    digest = hashlib.sha256(f"{seed}:{tag}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class NameGen:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.used: set[str] = set()

    def root(self, min_len: int = 4, max_len: int = 8) -> str:
        while True:
            n = self.rng.choice((2, 2, 3))
            s = "".join(self.rng.choice(ONSETS) + self.rng.choice(VOWELS) for _ in range(n))
            s = (s + self.rng.choice(CODAS)).capitalize()
            if min_len <= len(s) <= max_len and s not in self.used:
                self.used.add(s)
                return s
