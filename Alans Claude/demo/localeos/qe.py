"""The review flagger: decide which machine translations a human should check.

For each (English source, translation) pair we compute a handful of signals
that need NO human reference translation. A logistic regression then combines
them into one "needs review" score between 0 and 1.

Nothing in this file needs a GPU. The translator and the sentence embedder
live in models.py; this file only does arithmetic on their outputs.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from statistics import median

import numpy as np
from sacrebleu.metrics import CHRF

_chrf = CHRF()  # character n-gram F-score: works for any script, no word splitting needed

LATIN_TARGETS = {"Spanish", "Kurmanji"}  # languages written with the same alphabet as English

# Each signal, in the order the model sees them, with the sentence the app shows
# when that signal is what pushed a translation into the review pile.
FEATURES = [
    ("roundtrip_loss", "Translating it back into English changed the wording a lot."),
    ("meaning_gap", "Its meaning is measurably far from the original sentence."),
    ("low_confidence", "The translator itself was unsure about this sentence."),
    ("numbers_lost", "A number in the original is missing or different."),
    ("odd_length", "It is unusually short or long for this language."),
    ("repetition", "It repeats itself."),
    ("left_in_english", "Part of it seems to have been left in English."),
]
FEATURE_NAMES = [name for name, _ in FEATURES]
REASON = dict(FEATURES)


def chrf(hypothesis: str, reference: str) -> float:
    """Similarity of two strings from 0 to 100 (higher = more alike)."""
    return _chrf.sentence_score(hypothesis, [reference]).score


# ── the signals ────────────────────────────────────────────────────────────

def numbers_in(text: str) -> list[str]:
    """All numbers in a text, with Hindi/Arabic digits converted to 0-9."""
    ascii_digits = "".join(
        str(unicodedata.digit(ch)) if ch.isdigit() and not ch.isascii() else ch for ch in text
    )
    return re.findall(r"\d+(?:[.,:]\d+)*", ascii_digits)


def numbers_lost(source: str, translation: str) -> float:
    """Share of the source's numbers that do not appear in the translation."""
    wanted = Counter(numbers_in(source))
    if not wanted:
        return 0.0
    found = Counter(numbers_in(translation))
    missing = sum(max(0, n - found[num]) for num, n in wanted.items())
    return missing / sum(wanted.values())


def repetition(text: str) -> float:
    """0 when no 4-character chunk repeats; near 1 when the text loops."""
    compact = re.sub(r"\s+", " ", text.strip())
    grams = [compact[i:i + 4] for i in range(max(0, len(compact) - 3))]
    return 0.0 if len(grams) < 8 else 1 - len(set(grams)) / len(grams)


def left_in_english(source: str, translation: str, language: str) -> float:
    """How much of the output looks untranslated."""
    if language in LATIN_TARGETS:
        # same alphabet: count longer source words copied word for word
        words = {w for w in re.findall(r"[a-z]{5,}", source.lower())}
        if not words:
            return 0.0
        out = set(re.findall(r"[a-zçêîşû]{5,}", translation.lower()))
        return len(words & out) / len(words)
    letters = [ch for ch in translation if ch.isalpha()]
    if not letters:
        return 1.0
    return sum(ch.isascii() for ch in letters) / len(letters)   # Latin letters in a non-Latin script


def length_log_ratio(source: str, translation: str) -> float:
    return math.log((len(translation) + 1) / (len(source) + 1))


def signals(source: str, translation: str, back_translation: str, language: str, *,
            confidence: float | None = None, meaning_similarity: float | None = None,
            typical_log_ratio: float = 0.0) -> dict[str, float]:
    """All signals for one translation. Higher always means riskier.

    confidence          the translator's own score for its output (None if unknown)
    meaning_similarity  cosine similarity of sentence embeddings (None if no embedder)
    typical_log_ratio   the usual length ratio for this language, learned on training data
    """
    return {
        "roundtrip_loss": 1 - chrf(back_translation, source) / 100,
        "meaning_gap": float("nan") if meaning_similarity is None else 1 - meaning_similarity,
        "low_confidence": float("nan") if confidence is None else -confidence,
        "numbers_lost": numbers_lost(source, translation),
        "odd_length": abs(length_log_ratio(source, translation) - typical_log_ratio),
        "repetition": repetition(translation),
        "left_in_english": left_in_english(source, translation, language),
    }


# ── the model ──────────────────────────────────────────────────────────────

class Flagger:
    """Logistic regression over the signals, saved as plain JSON (no pickle).

    A missing signal (for example no sentence embedder installed) is replaced by
    its training average, so it neither raises nor lowers the score.
    """

    def __init__(self):
        self.mean = self.scale = self.coef = None
        self.intercept = 0.0
        self.typical_log_ratio: dict[str, float] = {}
        self.check_at = 0.35      # score at or above this: "check"
        self.review_at = 0.6      # score at or above this: "needs review"
        self.trained = False

    # -- training ----------------------------------------------------------
    @staticmethod
    def learn_length_ratios(rows) -> dict[str, float]:
        """Median log length ratio per language, from training rows only."""
        by_lang: dict[str, list[float]] = {}
        for r in rows:
            by_lang.setdefault(r["language"], []).append(length_log_ratio(r["source"], r["translation"]))
        out = {lang: median(v) for lang, v in by_lang.items()}
        out["*"] = median([x for v in by_lang.values() for x in v])   # used for a language never seen
        return out

    def matrix(self, feature_rows) -> np.ndarray:
        X = np.array([[row[name] for name in FEATURE_NAMES] for row in feature_rows], dtype=float)
        if self.mean is not None:
            idx = np.where(np.isnan(X))
            X[idx] = np.take(self.mean, idx[1])
        return X

    def fit(self, feature_rows, labels, review_share=0.2, check_share=0.4):
        from sklearn.linear_model import LogisticRegression

        X = np.array([[row[name] for name in FEATURE_NAMES] for row in feature_rows], dtype=float)
        self.mean = np.nan_to_num(np.nanmean(X, axis=0), nan=0.0)
        idx = np.where(np.isnan(X))
        X[idx] = np.take(self.mean, idx[1])
        self.scale = X.std(axis=0)
        self.scale[self.scale == 0] = 1.0
        model = LogisticRegression(max_iter=1000, class_weight="balanced")
        model.fit((X - self.mean) / self.scale, labels)
        self.coef, self.intercept = model.coef_[0], float(model.intercept_[0])
        self.trained = True
        # bands: the riskiest 20% of training translations "need review", the next 20% get "check"
        scores = self.score(feature_rows)
        self.review_at = float(np.quantile(scores, 1 - review_share))
        self.check_at = float(np.quantile(scores, 1 - check_share))
        return self

    # -- using it ----------------------------------------------------------
    def _z(self, feature_rows) -> np.ndarray:
        return (self.matrix(feature_rows) - self.mean) / self.scale

    def score(self, feature_rows) -> np.ndarray:
        return 1 / (1 + np.exp(-(self._z(feature_rows) @ self.coef + self.intercept)))

    def band(self, score: float) -> str:
        return "review" if score >= self.review_at else "check" if score >= self.check_at else "clear"

    def reasons(self, feature_row, top=2) -> list[str]:
        """The signals that pushed this translation's score up the most."""
        contrib = self._z([feature_row])[0] * self.coef
        order = np.argsort(contrib)[::-1]
        return [REASON[FEATURE_NAMES[i]] for i in order[:top] if contrib[i] > 0.15]

    # -- saving ------------------------------------------------------------
    def to_json(self) -> dict:
        return {"features": FEATURE_NAMES, "mean": list(map(float, self.mean)),
                "scale": list(map(float, self.scale)), "coef": list(map(float, self.coef)),
                "intercept": self.intercept, "typical_log_ratio": self.typical_log_ratio,
                "check_at": self.check_at, "review_at": self.review_at, "trained": self.trained}

    @classmethod
    def from_json(cls, d: dict) -> "Flagger":
        f = cls()
        assert d["features"] == FEATURE_NAMES, "model.json was trained with a different signal list"
        f.mean, f.scale, f.coef = (np.array(d[k], dtype=float) for k in ("mean", "scale", "coef"))
        f.intercept, f.typical_log_ratio = d["intercept"], d["typical_log_ratio"]
        f.check_at, f.review_at, f.trained = d["check_at"], d["review_at"], d.get("trained", True)
        return f

    @classmethod
    def load(cls, path: str) -> "Flagger":
        with open(path, encoding="utf-8") as fh:
            return cls.from_json(json.load(fh))

    @classmethod
    def untrained_default(cls) -> "Flagger":
        """A hand-set rule of thumb, used ONLY until evaluate_qe.py has trained a real model.

        The app labels its output "not trained yet" whenever this is in use.
        """
        f = cls()
        f.mean = np.array([0.45, 0.2, 0.6, 0.0, 0.25, 0.05, 0.05])
        f.scale = np.array([0.15, 0.1, 0.3, 0.3, 0.2, 0.1, 0.15])
        f.coef = np.array([1.2, 1.0, 0.8, 1.5, 0.5, 0.8, 0.8])
        f.intercept = -0.8
        f.typical_log_ratio = {"*": 0.0}
        return f
