"""
Acceptance tests for src/safelabel/checks.py  (stdlib unittest, nothing to install).

Run from the repo root:
    macOS/Linux/Colab:   PYTHONUTF8=1 python -m unittest discover -s tests -v
    Windows PowerShell:  $env:PYTHONUTF8=1; python -m unittest discover -s tests -v

Every test must pass before Gate 2. When you fix a bug, add a test for it.
"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safelabel import checks  # noqa: E402


class TestExtractNumbers(unittest.TestCase):
    def test_plain_digits(self):
        self.assertEqual(checks.extract_numbers("Take 2 tablets every 6 hours."), [2, 6])

    def test_ranges(self):
        self.assertEqual(checks.extract_numbers("Take 1 to 2 tablets every 4 to 6 hours as needed."), [1, 2, 4, 6])

    def test_english_number_words(self):
        self.assertEqual(checks.extract_numbers("Take one tablet twice a day."), [1, 2])
        self.assertEqual(checks.extract_numbers("Take once daily at bedtime."), [1])
        self.assertEqual(checks.extract_numbers("Take half a tablet."), [0.5])

    def test_fractions(self):
        self.assertEqual(checks.extract_numbers("Take 1/2 tablet."), [0.5])
        self.assertEqual(checks.extract_numbers("Take ½ tablet."), [0.5])
        self.assertEqual(checks.extract_numbers("Take 1 1/2 tablets."), [1.5])

    def test_decimals_and_thousands(self):
        self.assertEqual(checks.extract_numbers("Apply the 0.5% cream."), [0.5])
        self.assertEqual(checks.extract_numbers("Each dose is 1,000 mg."), [1000])
        self.assertEqual(checks.extract_numbers("Give 7.5 mL."), [7.5])

    def test_numbers_glued_to_letters_are_ignored(self):
        self.assertEqual(checks.extract_numbers("Contains vitamin B12 and H2O."), [])

    def test_degrees(self):
        self.assertEqual(checks.extract_numbers("Store below 25 °C."), [25])

    def test_duplicates_collapse(self):
        self.assertEqual(checks.extract_numbers("Take 1 tablet at 8 a.m. and 1 tablet at 8 p.m."), [1, 8])

    def test_arabic_indic_digits(self):
        self.assertEqual(checks.extract_numbers("خذ ٢ قرص كل ٦ ساعات.", "ar"), [2, 6])

    def test_arabic_decimal_separator(self):
        self.assertEqual(checks.extract_numbers("٠٫٥ ملغ", "ar"), [0.5])

    def test_arabic_range_with_dash(self):
        self.assertEqual(checks.extract_numbers("٦–٨ ساعات", "ar"), [6, 8])

    def test_devanagari_digits(self):
        self.assertEqual(checks.extract_numbers("दिन में २ बार, हर ६ घंटे।", "hi"), [2, 6])

    def test_fullwidth_digits(self):
        self.assertEqual(checks.extract_numbers("每天３次", "zh"), [3])

    def test_invisible_direction_marks_are_removed(self):
        self.assertEqual(checks.extract_numbers("‏٢‏ قرص", "ar"), [2])

    def test_english_words_only_count_for_english(self):
        self.assertEqual(checks.extract_numbers("one tablet", "zh"), [])


class TestNumberCheck(unittest.TestCase):
    SRC = "Take 2 tablets every 6 hours."

    def test_same_numbers_no_flag(self):
        r = checks.number_check(self.SRC, "每6小时服用2片。", "zh")
        self.assertFalse(r["flag"])
        self.assertEqual((r["missing"], r["extra"]), ([], []))

    def test_changed_number_is_flagged(self):
        r = checks.number_check(self.SRC, "每8小时服用2片。", "zh")
        self.assertTrue(r["flag"])
        self.assertEqual(r["missing"], [6])
        self.assertEqual(r["extra"], [8])

    def test_dropped_number_is_flagged(self):
        r = checks.number_check(self.SRC, "每6小时服用片。", "zh")
        self.assertTrue(r["flag"])
        self.assertEqual(r["missing"], [2])
        self.assertEqual(r["extra"], [])

    def test_repeated_numbers_merged_by_translation_are_ok(self):
        src = "Take 1 tablet at 8 a.m. and 1 tablet at 8 p.m."
        self.assertFalse(checks.number_check(src, "早上8点和晚上8点各服1片。", "zh")["flag"])

    def test_arabic_digits_equal(self):
        self.assertFalse(checks.number_check(self.SRC, "خذ ٢ قرص كل ٦ ساعات.", "ar")["flag"])

    def test_devanagari_digits_changed(self):
        r = checks.number_check(self.SRC, "हर ८ घंटे में २ गोली लें।", "hi")
        self.assertTrue(r["flag"])
        self.assertEqual((r["missing"], r["extra"]), ([6], [8]))


class TestNegation(unittest.TestCase):
    def test_english(self):
        self.assertTrue(checks.has_negation("Do not crush or chew the tablets.", "en"))
        self.assertTrue(checks.has_negation("Avoid alcohol.", "en"))
        self.assertTrue(checks.has_negation("If symptoms do not improve in 5 days, see a doctor.", "en"))
        self.assertTrue(checks.has_negation("Don’t drive.", "en"))
        self.assertFalse(checks.has_negation("Take 2 tablets with water.", "en"))
        self.assertFalse(checks.has_negation("Keep out of the reach of children.", "en"))
        self.assertFalse(checks.has_negation("Tell your doctor about all other medicines you take.", "en"))

    def test_chinese(self):
        self.assertTrue(checks.has_negation("请勿压碎或咀嚼药片。", "zh"))
        self.assertTrue(checks.has_negation("避免饮酒。", "zh"))
        self.assertFalse(checks.has_negation("每次服用2片，用水送服。", "zh"))

    def test_chinese_not_recommended(self):
        self.assertFalse(checks.negation_check(
            "Not recommended for babies under 6 months.",
            "对于6个月以下的婴儿来说不建议.", "zh",
        )["flag"])

    def test_chinese_symptoms_do_not_improve(self):
        self.assertTrue(checks.has_negation("如果您的症状在5天内恶化或不改善,请咨询医生.", "zh"))

    def test_chinese_affirmative_recommendation_has_no_negation(self):
        self.assertFalse(checks.has_negation("建议咨询医生。", "zh"))

    def test_hindi(self):
        self.assertTrue(checks.has_negation("गोली को कुचलें या चबाएं नहीं।", "hi"))
        self.assertTrue(checks.has_negation("शराब से बचें।", "hi"))
        self.assertFalse(checks.has_negation("दिन में दो बार एक गोली लें।", "hi"))

    def test_arabic(self):
        self.assertTrue(checks.has_negation("لا تسحق القرص أو تمضغه.", "ar"))
        self.assertTrue(checks.has_negation("لَا تَسْحَقِ الْقُرْصَ.", "ar"))  # with vowel marks
        self.assertTrue(checks.has_negation("تجنّب الكحول.", "ar"))
        self.assertTrue(checks.has_negation("يُستخدم من دون وصفة.", "ar"))  # two-word cue
        self.assertFalse(checks.has_negation("خذ قرصين مرتين يوميا مع الماء.", "ar"))

    def test_negation_check_flags_lost_negation(self):
        r = checks.negation_check("Do not crush or chew the tablets.", "压碎或咀嚼药片。", "zh")
        self.assertEqual((r["src_neg"], r["tgt_neg"], r["flag"]), (True, False, True))

    def test_negation_check_ok_when_kept(self):
        r = checks.negation_check("Do not crush or chew the tablets.", "请勿压碎或咀嚼药片。", "zh")
        self.assertFalse(r["flag"])

    def test_negation_check_flags_added_negation(self):
        r = checks.negation_check("Take with food.", "请勿与食物同服。", "zh")
        self.assertTrue(r["flag"])

    def test_missing_lexicon_gives_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            checks.has_negation("x", "xx")


class TestRunAll(unittest.TestCase):
    def test_keys_and_combination(self):
        r = checks.run_all_checks("Take 2 tablets every 6 hours. Do not crush.", "每8小时服用2片。请勿压碎。", "zh")
        for key in ("src_numbers", "tgt_numbers", "missing", "extra", "number_flag",
                    "src_neg", "tgt_neg", "negation_flag", "any_rule_flag"):
            self.assertIn(key, r)
        self.assertTrue(r["number_flag"])
        self.assertFalse(r["negation_flag"])
        self.assertTrue(r["any_rule_flag"])

    def test_clean_translation_has_no_flags(self):
        r = checks.run_all_checks("Take 2 tablets with water.", "用水送服2片。", "zh")
        self.assertFalse(r["any_rule_flag"])


class TestSeedSentences(unittest.TestCase):
    """Control totals for data/sentences_en.csv (our shared input)."""

    def setUp(self):
        with open(ROOT / "data" / "sentences_en.csv", encoding="utf-8-sig", newline="") as f:
            self.rows = list(csv.DictReader(f))

    def test_ids(self):
        self.assertEqual([r["sentence_id"] for r in self.rows], [f"S{i:03d}" for i in range(1, 61)])

    def test_splits_are_balanced(self):
        splits = [r["split"] for r in self.rows]
        self.assertEqual((splits.count("dev"), splits.count("test")), (30, 30))

    def test_hand_labelled_numbers_match_extractor(self):
        for r in self.rows:
            expected = [float(x) for x in r["expected_numbers_en"].split("|") if x]
            self.assertEqual(checks.extract_numbers(r["src_en"]), expected, r["sentence_id"])

    def test_hand_labelled_negation_matches_extractor(self):
        for r in self.rows:
            self.assertEqual(int(checks.has_negation(r["src_en"], "en")), int(r["has_negation_en"]), r["sentence_id"])


class TestChineseNumberWords(unittest.TestCase):
    def test_chinese_number_words(self):
        self.assertEqual(checks.extract_numbers("每天两次，每次一片。", "zh", use_words=True), [1, 2])

    def test_half_tablet_matches_fraction(self):
        r = checks.number_check("Take 1/2 tablet.", "服用半片。", "zh")
        self.assertFalse(r["flag"])

    def test_half_written_as_yiban(self):
        r = checks.number_check("Take half a tablet in the morning.", "早上服用一半药丸.", "zh")
        self.assertEqual(r["tgt_numbers"], [0.5])
        self.assertFalse(r["flag"])

    def test_written_tens_are_compared_as_one_value(self):
        r = checks.number_check("Use within 24 hours.", "二十四小时内使用。", "zh")
        self.assertFalse(r["flag"])

    def test_changed_written_frequency_is_flagged(self):
        r = checks.number_check("Take twice daily.", "每天服用一次。", "zh")
        self.assertEqual((r["missing"], r["extra"]), ([2], [1]))

    def test_non_quantity_phrases_do_not_add_numbers(self):
        self.assertEqual(checks.extract_numbers("一旦打开，请一次性使用。", "zh", use_words=True), [])

    def test_default_extractor_still_counts_digits_only(self):
        self.assertEqual(checks.extract_numbers("每天两次，每次１片。", "zh"), [1])



if __name__ == "__main__":
    unittest.main()
