"""
predict.py -- the one function the demo app calls:  check_translation(src_en, lang)

WHAT IT DOES (plain language)
-----------------------------
Given an English medicine-label sentence and a language (hi / zh / ar) it

  1. translates the sentence with the free NLLB-200 model, and translates the result BACK to English,
  2. runs our two simple safety checks from checks.py (do the numbers survive? did a "do not" survive?),
  3. scores how closely the back-translation matches the original (round-trip chrF), and
  4. returns a verdict in plain language:

       "dont_rely"         a check fired, or the back-translation drifted below our warning level
       "unsure"            no check fired, but the score is only a little above the warning level
       "looks_consistent"  we found no problem   <-- we NEVER call a translation "safe"

The warning level (a chrF number) is chosen on the DEV sentences by src/evaluate.py and saved in
outputs/thresholds.json. If that file does not exist yet, only the number and negation checks are used.

Importing this file is instant: the big translation model is loaded the first time it is needed.
Owner: Person H.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import checks

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_THRESHOLDS = REPO_ROOT / "outputs" / "thresholds.json"
DEFAULT_CACHE = REPO_ROOT / "outputs" / "demo_cache.json"

DISCLAIMER = "This project is a prototype and is not medical advice."
NEXT_STEP_WARN = "Ask your pharmacist or doctor to confirm this instruction in your language."
NEXT_STEP_OK = ("Our checks found no problems. That does not prove the translation is right - "
                "confirm with your pharmacist.")
UNSURE_MARGIN = 5.0  # chrF points above the warning level that we still call "unsure"

LANG_NAMES = {"hi": "Hindi", "zh": "Chinese", "ar": "Arabic"}
MODEL_NAME = "facebook/nllb-200-distilled-600M"
NLLB_CODES = {"en": "eng_Latn", "hi": "hin_Deva", "zh": "zho_Hans", "ar": "arb_Arab"}


# ----------------------------------------------------------------------------------------------
# The translator (loaded only when first used)
# ----------------------------------------------------------------------------------------------
class NllbTranslator:
    """Translate English -> language, then back to English, with NLLB-200 (same settings as src/translate.py)."""

    def __init__(self, model_name: str = MODEL_NAME, device: str | None = None):
        self.model_name = model_name
        self._device = device
        self._model = None
        self._tokenizer = None
        self._torch = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:  # Windows laptops with a company/antivirus certificate: use the system certificate store
            import truststore

            truststore.inject_into_ssl()
        except ImportError:
            pass
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._torch = torch
        self._device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self._device).eval()

    def _translate(self, text: str, src_code: str, tgt_code: str) -> str:
        self._tokenizer.src_lang = src_code  # which language the input is in
        batch = self._tokenizer([text], return_tensors="pt", truncation=True, max_length=256).to(self._device)
        with self._torch.inference_mode():
            out = self._model.generate(
                **batch,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(tgt_code),  # write in this language
                num_beams=4,
                max_new_tokens=200,
            )
        return self._tokenizer.batch_decode(out, skip_special_tokens=True)[0]

    def __call__(self, src_en: str, lang: str) -> tuple[str, str]:
        """Return (translation, back_translation)."""
        self._load()
        target = NLLB_CODES[lang]
        forward = self._translate(src_en, NLLB_CODES["en"], target)
        back = self._translate(forward, target, NLLB_CODES["en"])
        return forward, back


_default_translator: NllbTranslator | None = None


def default_translator() -> NllbTranslator:
    """One shared translator, so the model is loaded only once per session."""
    global _default_translator
    if _default_translator is None:
        _default_translator = NllbTranslator()
    return _default_translator


# ----------------------------------------------------------------------------------------------
# Scores and thresholds
# ----------------------------------------------------------------------------------------------
_chrf = None


def round_trip_chrf(src_en: str, back_translation: str) -> float | None:
    """chrF similarity (0-100) between the original English and the back-translation, or None without sacrebleu."""
    global _chrf
    try:
        from sacrebleu.metrics import CHRF
    except ImportError:
        return None
    if _chrf is None:
        _chrf = CHRF()
    return float(_chrf.sentence_score(back_translation, [src_en]).score)


def load_thresholds(path: str | Path | None = None) -> dict:
    """Read outputs/thresholds.json. Returns {"rt_chrf": None} when the file is not there yet."""
    p = Path(path) if path else DEFAULT_THRESHOLDS
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return {"rt_chrf": data.get("rt_chrf")}
    return {"rt_chrf": None}


def load_cached_examples(path: str | Path | None = None) -> list[dict]:
    """Saved results of check_translation() for the demo examples (works with no GPU and no internet)."""
    p = Path(path) if path else DEFAULT_CACHE
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------------------------
# The verdict
# ----------------------------------------------------------------------------------------------
def _numbers(values: list[float]) -> str:
    return ", ".join(f"{v:g}" for v in values)


def build_reasons(c: dict, rt_chrf: float | None, threshold: float | None) -> list[str]:
    """Turn the check results into plain sentences a family member can read."""
    reasons = []
    if c["missing"]:
        reasons.append(f"These numbers in the English are not in the translation: {_numbers(c['missing'])}.")
    if c["extra"]:
        reasons.append(f"These numbers are in the translation but not in the English: {_numbers(c['extra'])}.")
    if c["negation_flag"]:
        if c["src_neg"] and not c["tgt_neg"]:
            reasons.append("The English says 'do not', 'avoid' or 'without', but the translation does not seem to.")
        else:
            reasons.append("The translation seems to say 'do not' or 'avoid', but the English does not.")
    if rt_chrf is not None and threshold is not None and rt_chrf < threshold:
        reasons.append("Translated back to English, the sentence no longer closely matches the original "
                       f"(similarity {rt_chrf:.0f}; we warn below {threshold:.0f}).")
    return reasons


def check_translation(src_en: str, lang: str, translator=None, thresholds: dict | None = None, scorer=None) -> dict:
    """Translate, check, and decide. `translator(src_en, lang) -> (translation, back_translation)` and
    `scorer(src_en, back_translation) -> float | None` can be replaced (the tests do this)."""
    src_en = (src_en or "").strip()
    if not src_en:
        raise ValueError("Please type an English sentence.")
    if lang not in LANG_NAMES:
        raise ValueError(f"Language must be one of {sorted(LANG_NAMES)}.")

    translator = translator or default_translator()
    thresholds = thresholds if thresholds is not None else load_thresholds()
    threshold = thresholds.get("rt_chrf")

    translation, back = translator(src_en, lang)
    c = checks.run_all_checks(src_en, translation, lang)
    rt = (scorer or round_trip_chrf)(src_en, back)

    below = rt is not None and threshold is not None and rt < threshold
    reasons = build_reasons(c, rt, threshold)
    if c["any_rule_flag"] or below:
        verdict, next_step = "dont_rely", NEXT_STEP_WARN
    elif rt is not None and threshold is not None and rt < threshold + UNSURE_MARGIN:
        verdict, next_step = "unsure", NEXT_STEP_WARN
        reasons.append(f"The back-translation is close to our warning level (similarity {rt:.0f} vs {threshold:.0f}).")
    else:
        verdict, next_step = "looks_consistent", NEXT_STEP_OK
        reasons.append("No changed or missing numbers and no lost 'do not' words were found.")

    return {
        "lang": lang, "src_en": src_en, "translation": translation, "back_translation": back,
        "verdict": verdict, "reasons": reasons, "rt_chrf": rt, "checks": c,
        "next_step": next_step, "disclaimer": DISCLAIMER,
    }


# ----------------------------------------------------------------------------------------------
# A small HTML box for the app and the notebook
# ----------------------------------------------------------------------------------------------
BANNER = {
    "dont_rely": ("#C8453B", "Don't rely on this translation"),
    "unsure": ("#B7791F", "Unsure - check with your pharmacist"),
    "looks_consistent": ("#2F7D5B", "No problems found by our checks - still confirm with your pharmacist"),
}


def render_result_html(r: dict) -> str:
    """One coloured box for a result of check_translation(). Everything from outside is escaped."""
    color, title = BANNER.get(r["verdict"], ("#555555", r["verdict"]))
    reasons = "".join(f"<li>{html.escape(x)}</li>" for x in r.get("reasons", []))
    name = LANG_NAMES.get(r["lang"], r["lang"])
    return (
        f"<div style='border-left:8px solid {color};padding:8px 14px;margin:8px 0'>"
        f"<b style='color:{color};font-size:1.1em'>{html.escape(title)}</b>"
        f"<div style='margin-top:6px'><i>English:</i> {html.escape(r['src_en'])}</div>"
        f"<div dir='auto'><i>{html.escape(name)}:</i> {html.escape(r['translation'])}</div>"
        f"<ul>{reasons}</ul><div>{html.escape(r.get('next_step', ''))}</div>"
        f"<small>{html.escape(r.get('disclaimer', DISCLAIMER))}</small></div>"
    )
