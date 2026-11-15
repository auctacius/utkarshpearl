"""
checks.py -- simple, explainable safety checks for machine-translated medicine instructions.

WHAT THIS FILE DOES (plain language)
------------------------------------
We put the ENGLISH sentence next to its TRANSLATION and ask two yes/no questions:

  1. NUMBER CHECK    Are the same numbers (doses, hours, days, mL ...) on both sides?
  2. NEGATION CHECK  If the English says "do not / avoid / without", does the translation also
                     contain a "not"-style word?  (And the reverse: no surprise "not" appearing.)

If either answer is "no" we raise a flag. The app shows a flag as "don't rely on this translation".

These rules are deliberately SIMPLE: easy to explain to a judge, easy to test. They will miss
translations that are fluent but wrong in some other way. Evaluation measures that honestly.

Only the Python standard library is used on purpose, so this runs anywhere (Colab, laptop, tests).

Owner: the Chinese-speaking teammate (see CONTRACT.md). First version drafted with Claude;
the owner must read every function, be able to explain it, and extend it.

Quick try:  PYTHONPATH=src python -m safelabel.checks "Take 2 tablets." "每次服用3片。" zh
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

# Where the per-language word lists live: data/lexicons/negation_<lang>.json
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEXICON_DIR = REPO_ROOT / "data" / "lexicons"

# ----------------------------------------------------------------------------------------
# Step 0 - tidy text so that different scripts can be compared fairly
# ----------------------------------------------------------------------------------------

# Invisible direction / joiner characters that Arabic and Hindi text often contains.
_INVISIBLE = dict.fromkeys(
    map(ord, "​‌‍‎‏‪‫‬‭‮⁦⁧⁨⁩﻿"),
    None,  # None means "delete this character"
)

# Arabic vowel marks and the stretching character; we ignore them when matching words.
_ARABIC_MARKS = re.compile("[ً-ٰٟـ]")

# Fraction symbols turned into text fractions (with a leading space so "1½" becomes "1 1/2").
_VULGAR_FRACTIONS = {"½": " 1/2", "¼": " 1/4", "¾": " 3/4"}


def to_ascii_digits(text: str) -> str:
    """Turn digits from any script (Arabic-Indic, Devanagari, full-width ...) into 0-9.

    Also maps the Arabic decimal/thousands marks to '.' and ',' and expands fraction symbols.
    """
    out = []
    for ch in text:
        if ch in _VULGAR_FRACTIONS:
            out.append(_VULGAR_FRACTIONS[ch])
        elif ch.isdecimal():  # any "decimal digit" character in any script
            out.append(str(unicodedata.decimal(ch)))
        elif ch == "٫":  # Arabic decimal separator
            out.append(".")
        elif ch == "٬":  # Arabic thousands separator
            out.append(",")
        elif ch == "．":  # full-width full stop
            out.append(".")
        else:
            out.append(ch)
    return "".join(out)


# ----------------------------------------------------------------------------------------
# Step 1 - find the numbers in a sentence
# ----------------------------------------------------------------------------------------

# One regular expression that understands: 1 1/2, 1/2, 1,000, 2.5 and 25.
# The first line says: the number must NOT be glued to a letter, digit or dot on its left,
# which is how "vitamin B12" and "H2O" are ignored.
_NUMBER_RE = re.compile(
    r"""
    (?<![A-Za-z0-9.])
    (?:
        (?P<mixed>\d+)\s+(?P<mn>\d+)\s*/\s*(?P<md>\d+)
      | (?P<fn>\d+)\s*/\s*(?P<fd>\d+)
      | (?P<thou>\d{1,3}(?:,\d{3})+(?:\.\d+)?)
      | (?P<dec>\d+\.\d+)
      | (?P<int>\d+)
    )
    """,
    re.VERBOSE,
)

# English number words that appear in dosing instructions.
EN_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "half": 0.5, "quarter": 0.25, "once": 1, "twice": 2,
}
_EN_WORD_RE = re.compile(r"\b(" + "|".join(EN_NUMBER_WORDS) + r")\b", re.IGNORECASE)

# Match Chinese number words before common label units. This avoids reading the
# 一 in 一旦 (once something happens) as a dose or frequency.
_ZH_VALUES = {char: value for value, char in enumerate("零一二三四五六七八九")}
_ZH_VALUES.update({"两": 2, "兩": 2, "半": 0.5, "一半": 0.5})
_ZH_NUMBER = r"(?:一半|[一二三四五六七八九]?十[一二三四五六七八九]?|[零一二两兩三四五六七八九半])"
_ZH_QUANTITY_RE = re.compile(
    rf"(?<![A-Za-z0-9.零一二两兩三四五六七八九十百千万萬亿億半])"
    rf"({_ZH_NUMBER})\s*(?=(?:次(?!性)|片|药丸|藥丸|粒|顆|颗|錠|锭|劑|剂|小時|小时|分鐘|分钟|"
    rf"天|日|週|周|歲|岁|毫升|毫克|克|滴|茶匙|湯匙|汤匙|杯|度|%|％|°|mL|mg))",
    re.IGNORECASE,
)


def _zh_word_values(text: str) -> list[float]:
    """Read Chinese label quantities written as half, single digits, or tens."""
    values = []
    for word in _ZH_QUANTITY_RE.findall(text):
        if "十" in word:
            tens, ones = word.split("十")
            values.append(10 * _ZH_VALUES.get(tens, 1) + _ZH_VALUES.get(ones, 0))
        else:
            values.append(_ZH_VALUES[word])
    return values


def _digit_values(ascii_text: str) -> list[float]:
    """Read every number written with digits and return its value."""
    values: list[float] = []
    for m in _NUMBER_RE.finditer(ascii_text):
        if m.group("mixed"):  # e.g. 1 1/2
            den = int(m.group("md"))
            if den:
                values.append(int(m.group("mixed")) + int(m.group("mn")) / den)
        elif m.group("fn"):  # e.g. 1/2
            den = int(m.group("fd"))
            if den:
                values.append(int(m.group("fn")) / den)
        elif m.group("thou"):  # e.g. 1,000
            values.append(float(m.group("thou").replace(",", "")))
        elif m.group("dec"):  # e.g. 2.5
            values.append(float(m.group("dec")))
        else:  # e.g. 25
            values.append(float(m.group("int")))
    return values


def extract_numbers(text: str, lang: str = "en", use_words: bool = False) -> list[float]:
    """Return the sorted, de-duplicated numbers found in `text`.

    - Digits from any script are understood (2, ٢, २, ２ all mean 2).
    - For English (lang == "en") number words such as "twice" or "half" also count.
    - Chinese label quantities also count when use_words=True. Hindi and Arabic use digits only.
    We keep a SET of numbers (not a count) so "1 tablet at 8 a.m. and 1 tablet at 8 p.m." and a
    translation that says "1 tablet at 8 a.m. and 8 p.m." are treated as the same.
    """
    if use_words and lang not in ("en", "zh"):
        raise NotImplementedError("STRETCH: target-side number words (see briefs/BRIEF_chinese_checks.md)")
    text = text.translate(_INVISIBLE)
    values = _digit_values(to_ascii_digits(text))
    if lang == "en":
        values += [EN_NUMBER_WORDS[w.lower()] for w in _EN_WORD_RE.findall(text)]
    elif lang == "zh" and use_words:
        values += _zh_word_values(to_ascii_digits(text))
    return sorted({round(float(v), 4) for v in values})


def number_check(src_en: str, tgt: str, lang: str) -> dict:
    """Compare the numbers in the English with the numbers in the translation.

    Returns: src_numbers, tgt_numbers, missing (in English but not in translation),
    extra (in translation but not in English), flag (True if anything differs).
    """
    src = extract_numbers(src_en, "en")
    tgt_nums = extract_numbers(tgt, lang, use_words=(lang == "zh"))
    missing = sorted(set(src) - set(tgt_nums))
    extra = sorted(set(tgt_nums) - set(src))
    return {
        "src_numbers": src,
        "tgt_numbers": tgt_nums,
        "missing": missing,
        "extra": extra,
        "flag": bool(missing or extra),
    }


# ----------------------------------------------------------------------------------------
# Step 2 - find "do not / avoid / without" in a sentence
# ----------------------------------------------------------------------------------------

# English cues. "do not", "should not", "must not" are all caught by the word "not".
# The word "no" is left out on purpose (it also means "zero", as in "no more than").
_EN_NEG = re.compile(
    r"\b(?:not|never|avoid|without|cannot|can't|don't|doesn't|didn't|won't)\b", re.IGNORECASE
)


def _normalize_for_match(text: str) -> str:
    """Lower-case, remove invisible marks and Arabic vowel marks, unify look-alike characters."""
    text = unicodedata.normalize("NFKC", text).translate(_INVISIBLE)
    return _ARABIC_MARKS.sub("", text).lower()


def _padded_tokens(text: str) -> str:
    """Turn punctuation into spaces and wrap the sentence in spaces so ' word ' matches whole words.

    (Python's \\w does not treat Hindi vowel signs as letters, so we split on punctuation instead.)
    """
    chars = [" " if unicodedata.category(c)[0] in "PZ" else c for c in text]
    return " " + " ".join("".join(chars).split()) + " "


@lru_cache(maxsize=None)
def load_negation_lexicon(lang: str, lexicon_dir: str | None = None) -> dict:
    """Load data/lexicons/negation_<lang>.json and prepare the cues for matching."""
    folder = Path(lexicon_dir) if lexicon_dir else DEFAULT_LEXICON_DIR
    path = folder / f"negation_{lang}.json"
    if not path.exists():
        raise FileNotFoundError(f"No negation word list for '{lang}': expected {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    mode = data.get("mode", "token")
    if mode not in ("token", "substring"):
        raise ValueError(f"{path.name}: mode must be 'token' or 'substring'")
    cues = []
    for cue in data["cues"]:
        norm = _normalize_for_match(cue)
        cues.append(norm if mode == "substring" else _padded_tokens(norm).strip())
    return {"mode": mode, "cues": cues}


def has_negation(text: str, lang: str, lexicon_dir: str | None = None) -> bool:
    """True if the sentence contains a 'not'-style word for its language."""
    if lang == "en":
        return bool(_EN_NEG.search(text.replace("’", "'")))  # also catch curly apostrophes
    lex = load_negation_lexicon(lang, lexicon_dir)
    norm = _normalize_for_match(text)
    if lex["mode"] == "substring":  # Chinese: no spaces between words
        return any(cue in norm for cue in lex["cues"])
    padded = _padded_tokens(norm)  # Hindi / Arabic: match whole words
    return any(f" {cue} " in padded for cue in lex["cues"])


def negation_check(src_en: str, tgt: str, lang: str, lexicon_dir: str | None = None) -> dict:
    """Flag when the English and the translation disagree about having a 'not'-style word."""
    src_neg = has_negation(src_en, "en")
    tgt_neg = has_negation(tgt, lang, lexicon_dir)
    return {"src_neg": src_neg, "tgt_neg": tgt_neg, "flag": src_neg != tgt_neg}


# ----------------------------------------------------------------------------------------
# Step 3 - run everything
# ----------------------------------------------------------------------------------------

def run_all_checks(src_en: str, tgt: str, lang: str, lexicon_dir: str | None = None) -> dict:
    """Run both checks and combine them. `any_rule_flag` is what the demo app uses."""
    nums = number_check(src_en, tgt, lang)
    neg = negation_check(src_en, tgt, lang, lexicon_dir)
    return {
        "src_numbers": nums["src_numbers"],
        "tgt_numbers": nums["tgt_numbers"],
        "missing": nums["missing"],
        "extra": nums["extra"],
        "number_flag": nums["flag"],
        "src_neg": neg["src_neg"],
        "tgt_neg": neg["tgt_neg"],
        "negation_flag": neg["flag"],
        "any_rule_flag": nums["flag"] or neg["flag"],
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print('usage: PYTHONPATH=src python -m safelabel.checks "English" "translation" <hi|zh|ar>')
    else:
        print(json.dumps(run_all_checks(sys.argv[1], sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2))
