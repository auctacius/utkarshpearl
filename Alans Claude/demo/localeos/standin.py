"""FAKE models, for testing the code paths on a machine with no GPU.

    LOCALEOS_STANDIN=1 python build_dataset.py ...

These do NOT translate anything. A "translation" is the English sentence with a
language tag in front, sometimes deliberately damaged (a number changed, the end
cut off, a phrase repeated) so the flagger has something to find. Everything
produced with these is written under data/standin/ and marked as stand-in, and
must never appear in the write-up or the video.
"""

from __future__ import annotations

import hashlib
import random
import re

TAG = {"Spanish": "[es]", "Hindi": "[hi]", "Mandarin": "[zh]", "Arabic": "[ar]", "Kurmanji": "[kmr]"}
DAMAGE_RATE = {"Spanish": 0.12, "Hindi": 0.2, "Mandarin": 0.18, "Arabic": 0.22, "Kurmanji": 0.4}


def _rng(text: str, salt: str) -> random.Random:
    return random.Random(int(hashlib.sha256((salt + text).encode()).hexdigest()[:12], 16))


def clean(text: str, target: str) -> str:
    """The stand-in for a perfect translation."""
    return f"{TAG[target]} {text}"


def damage(text: str, rng: random.Random) -> str:
    kind = rng.choice(["number", "cut", "repeat", "swap"])
    words = text.split()
    if kind == "number" and re.search(r"\d", text):
        return re.sub(r"\d+", lambda m: str(int(m.group()) + rng.randint(1, 9)), text, count=1)
    if kind == "cut" and len(words) > 4:
        return " ".join(words[: max(2, len(words) // 2)])
    if kind == "repeat" and len(words) > 3:
        return text + " " + " ".join(words[-3:] * 3)
    rng.shuffle(words)
    return " ".join(words)


class StandinTranslator:
    def translate(self, texts, source, target, batch_size=16):
        out, conf = [], []
        for t in texts:
            if target == "English":                      # "back-translation": strip the tag
                out.append(re.sub(r"^\[\w+\]\s*", "", t))
                conf.append(-0.3)
                continue
            rng = _rng(t, target)
            bad = rng.random() < DAMAGE_RATE[target]
            body = damage(t, rng) if bad else t
            out.append(f"{TAG[target]} {body}")
            conf.append(-(0.9 if bad else 0.35) - rng.random() * 0.5)   # noisy, so it is not a giveaway
        return out, conf


class StandinEmbedder:
    def similarity(self, a, b):
        sims = []
        for x, y in zip(a, b):
            wx, wy = set(x.lower().split()), set(re.sub(r"^\[\w+\]\s*", "", y).lower().split())
            sims.append(len(wx & wy) / max(1, len(wx | wy)))
        return sims


def standin_corpus(n: int, seed: int):
    """n made-up English sentences with numbers, like short business notices."""
    rng = random.Random(seed)
    things = ["order", "appointment", "delivery", "invoice", "class", "refund", "booking", "payment"]
    verbs = ["will arrive", "is confirmed", "was moved", "is ready", "has been cancelled", "is due"]
    places = ["at the front desk", "by email", "at our main office", "online", "at the pharmacy"]
    out = []
    for i in range(n):
        out.append(f"Your {rng.choice(things)} number {rng.randint(100, 999)} {rng.choice(verbs)} "
                   f"on day {rng.randint(1, 28)} {rng.choice(places)}, please bring {rng.randint(2, 9)} "
                   f"documents and arrive {rng.randint(5, 30)} minutes early.")
    return out
