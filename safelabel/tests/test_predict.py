"""
Tests for src/safelabel/predict.py (stdlib unittest; no model, no internet, no sacrebleu needed).
Run from the repo root:   python -m unittest discover -s tests -v
The translator and the chrF scorer are replaced by tiny fakes, so only OUR decision logic is tested.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safelabel import predict  # noqa: E402

SRC = "Take 2 tablets every 6 hours. Do not crush the tablets."


def fake_translator(translation, back="back"):
    """A translator that always answers with the given text."""
    return lambda src, lang: (translation, back)


def fake_scorer(value):
    return lambda src, back: value


class TestVerdicts(unittest.TestCase):
    def test_changed_number_means_dont_rely(self):
        r = predict.check_translation(SRC, "zh", fake_translator("每8小时服用2片。请勿压碎药片。"),
                                      {"rt_chrf": None}, fake_scorer(None))
        self.assertEqual(r["verdict"], "dont_rely")
        self.assertTrue(any("not in the translation: 6" in x for x in r["reasons"]))
        self.assertTrue(any("not in the English: 8" in x for x in r["reasons"]))
        self.assertIn("pharmacist", r["next_step"])

    def test_lost_negation_means_dont_rely(self):
        r = predict.check_translation(SRC, "zh", fake_translator("每6小时服用2片。压碎药片。"),
                                      {"rt_chrf": None}, fake_scorer(None))
        self.assertEqual(r["verdict"], "dont_rely")
        self.assertTrue(any("'do not'" in x for x in r["reasons"]))

    def test_added_negation_is_also_flagged(self):
        r = predict.check_translation("Take with food.", "zh", fake_translator("请勿与食物同服。"),
                                      {"rt_chrf": None}, fake_scorer(None))
        self.assertEqual(r["verdict"], "dont_rely")
        self.assertTrue(any("but the English does not" in x for x in r["reasons"]))

    def test_low_chrf_alone_means_dont_rely(self):
        r = predict.check_translation("Take with food.", "zh", fake_translator("与食物同服。"),
                                      {"rt_chrf": 60.0}, fake_scorer(40.0))
        self.assertEqual(r["verdict"], "dont_rely")
        self.assertTrue(any("similarity 40" in x for x in r["reasons"]))

    def test_close_to_threshold_means_unsure(self):
        r = predict.check_translation("Take with food.", "zh", fake_translator("与食物同服。"),
                                      {"rt_chrf": 60.0}, fake_scorer(62.0))
        self.assertEqual(r["verdict"], "unsure")

    def test_clean_translation_looks_consistent(self):
        r = predict.check_translation("Take with food.", "zh", fake_translator("与食物同服。"),
                                      {"rt_chrf": 60.0}, fake_scorer(90.0))
        self.assertEqual(r["verdict"], "looks_consistent")
        self.assertIn("confirm with your pharmacist", r["next_step"])

    def test_without_threshold_only_the_rules_decide(self):
        r = predict.check_translation("Take with food.", "zh", fake_translator("与食物同服。"),
                                      {"rt_chrf": None}, fake_scorer(1.0))
        self.assertEqual(r["verdict"], "looks_consistent")

    def test_we_never_say_safe(self):
        for translation, score in (("每6小时服用2片。请勿压碎药片。", 95.0), ("每8小时服用2片。压碎药片。", 20.0),
                                   ("每6小时服用2片。请勿压碎药片。", 61.0)):
            r = predict.check_translation(SRC, "zh", fake_translator(translation), {"rt_chrf": 60.0}, fake_scorer(score))
            texts = [r["verdict"], r["next_step"], *r["reasons"], predict.render_result_html(r)]
            for text in texts:
                self.assertNotIn("safe", text.lower().replace("unsafe", ""), text)

    def test_result_has_every_contract_key(self):
        r = predict.check_translation(SRC, "ar", fake_translator("خذ 2 قرص كل 6 ساعات. لا تسحق الأقراص."),
                                      {"rt_chrf": None}, fake_scorer(None))
        for key in ("lang", "src_en", "translation", "back_translation", "verdict", "reasons", "rt_chrf",
                    "checks", "next_step", "disclaimer"):
            self.assertIn(key, r)
        self.assertEqual(r["disclaimer"], "This project is a prototype and is not medical advice.")
        json.dumps(r)  # must be JSON-serializable: the notebook saves results to demo_cache.json


class TestInputsAndHelpers(unittest.TestCase):
    def test_bad_language_and_empty_text(self):
        with self.assertRaises(ValueError):
            predict.check_translation("Take 2 tablets.", "fr", fake_translator("x"), {"rt_chrf": None})
        with self.assertRaises(ValueError):
            predict.check_translation("   ", "hi", fake_translator("x"), {"rt_chrf": None})

    def test_html_is_escaped(self):
        r = predict.check_translation("Take 2 tablets.", "zh", fake_translator("<script>alert(1)</script> 2片"),
                                      {"rt_chrf": None}, fake_scorer(None))
        page = predict.render_result_html(r)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_thresholds_file_missing_or_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(predict.load_thresholds(Path(tmp) / "nope.json"), {"rt_chrf": None})
            path = Path(tmp) / "thresholds.json"
            path.write_text(json.dumps({"rt_chrf": 71.5, "labse_cos": None, "chosen_on": "dev"}), encoding="utf-8")
            self.assertEqual(predict.load_thresholds(path), {"rt_chrf": 71.5})

    def test_cached_examples_missing_or_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(predict.load_cached_examples(Path(tmp) / "nope.json"), [])
            path = Path(tmp) / "demo_cache.json"
            path.write_text(json.dumps([{"lang": "hi"}], ensure_ascii=False), encoding="utf-8")
            self.assertEqual(predict.load_cached_examples(path), [{"lang": "hi"}])


if __name__ == "__main__":
    unittest.main()
