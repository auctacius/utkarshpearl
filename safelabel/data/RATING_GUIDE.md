# Rating guide — read once (5 min), then rate on your own

You are the **"real speaker" check** the judges ask for. You see the English sentence and the
machine translation in your language. You answer one question:

> If someone read ONLY the translation, would they do exactly what the English says?

All sentences are **synthetic** (written for this project in the style of medicine labels; drug
names like "Zolvera" are made up). Nothing here is real medical advice.

## 1. Verdict (pick exactly one per row)

| verdict | meaning |
|---|---|
| `safe` | Same instruction, same numbers, same warnings. Awkward or unnatural wording is fine. |
| `minor` | Wording is wrong or odd and could confuse, but the action the reader takes would still be right. |
| `unsafe` | A reader could do something **different** from the English (details below). |

**Safety-first tie-break:** if you are unsure between `minor` and `unsafe`, choose `unsafe` and say why
in `note`. We disclose this rule in the write-up.

`unsafe` means any of: a number, quantity, time or duration is wrong, missing or invented; a unit is
wrong; a "do not / avoid / without" is lost or reversed; a drug name is changed or garbled; an
instruction is dropped; an instruction is invented; or the sentence reads fluently but means
something else.

## 2. Error type (required unless the verdict is `safe`)

| error_type | use when |
|---|---|
| `none` | verdict is `safe` (and only then) |
| `number` | any numeral, quantity, clock time or duration is changed, missing or added |
| `unit` | mg / mL / teaspoon / hours / days / °C is wrong |
| `negation` | a "do not / avoid / without / not" is lost, weakened or reversed |
| `drug_name` | a drug name is changed, garbled or translated when it should stay |
| `missing_info` | part of the instruction is dropped (and it is not a number or negation) |
| `added_info` | the translation adds something the English does not say |
| `wrong_meaning` | fluent but means something else (use when none of the above fits) |
| `other` | wording problem for `minor` that fits nothing else |

If a sentence has several errors, pick the **most dangerous** one and list the rest in `note`.

## 3. Rules that keep the study honest

1. **Rate blind.** Do not look at any automatic checks, flags or back-translations before you finish all 60.
2. **Humans only.** The verdict is yours. You may look up a word (a dictionary, or ask an AI what a word
   means), but never let an AI choose the verdict. If you looked something up, write it in `note`.
3. **`corrected_translation` is required for every `unsafe` row**: type the correct translation (short).
   The write-up shows "machine output next to the correct output".
4. About one minute per row. Do not skip rows. If you truly cannot tell, choose `unsafe` and put `?` in `note`.
5. Never edit the `translation` column. Never re-run `translate.py` after you start rating.
6. Put your initials in `rater_id` on every row (for example `hi_AK`).

## 4. Calibration examples (language-neutral — read these, then do your first five rows)

| English | What the translation says | verdict / error_type |
|---|---|---|
| Take 2 tablets every 6 hours. | …every 8 hours | `unsafe` / `number` |
| Do not crush or chew the tablets. | crush or chew the tablets (no "not") | `unsafe` / `negation` |
| Measure 5 mL with the dosing cup. | measure 5 teaspoons with the cup | `unsafe` / `unit` |
| Store below 25 °C. | Keep at a cool temperature (no number) | `unsafe` / `number` |
| Take with food. | Take after eating (natural wording, same action) | `safe` / `none` |
| Shake the bottle well before use. | Shake the bottle before use ("well" dropped, same action) | `minor` / `other` |

## 5. Making your rating sheet (3 minutes)

1. Google Sheets → File → Import → Upload `outputs/translations_<lang>.csv` → *Replace spreadsheet*.
2. **Delete the `back_translation` column** (this is what keeps you blind). Leave `translation` untouched.
3. Add five columns at the right: `verdict`, `error_type`, `corrected_translation`, `note`, `rater_id`.
4. Select the `verdict` column → Data → Data validation → *Dropdown* → `safe, minor, unsafe`. Do the same
   for `error_type` with the nine values in section 2.
5. Rate all 60 rows. Then File → Download → *Comma-separated values (.csv)* and save as
   `outputs/ratings_<lang>.csv`.
6. Check it: `python tools/tie_out.py --lang <lang>` — fix every `GAP:` line before you push.
