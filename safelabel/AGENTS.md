# SafeLabel — context for coding assistants (Codex, Claude, ChatGPT)

Hackathon prototype (Veritas AI International High School Hackathon 2026, track: AI + Languages).
We test whether a free translator (NLLB-200) keeps medicine-label sentences safe in Hindi, Chinese and
Arabic, and whether simple checks can warn a reader. Read `CONTRACT.md` first, then your brief in `briefs/`.
Do NOT read `PLAN.md` unless asked (it is for humans and is long).

## Rules
- Only edit files you own (CONTRACT.md section 3). Edit in place; do not reprint whole files.
- This project lives in the `safelabel/` folder of a shared repo that also holds other people's folders (`Adam's GPT`, `Alans Claude`): never edit or delete anything outside `safelabel/`.
- `src/safelabel/checks.py` uses the standard library only (sacrebleu is allowed in `src/run_checks.py`).
- Comment code in plain language; a high-school teammate must be able to explain every line to judges.
- Human ratings are never produced or guessed by AI. Never put API keys in files.
- Never report numbers computed from `outputs_dummy/` (fake data).
- Read CSVs with `encoding="utf-8-sig"`, write UTF-8. On Windows set `PYTHONUTF8=1`.

## Commands
- Tests: `python -m unittest discover -s tests -v`
- Self-check your files: `python tools/tie_out.py --lang <hi|zh|ar> [--stage translations] --quiet`
- Fake data for building before real data exists: `python tools/make_dummy.py` (writes `outputs_dummy/`),
  then add `--outputs outputs_dummy` to tools that accept it.

## Token savers
- Show a CSV as header + 3 rows, never the whole file. Paste only the last 30 lines of an error.
- Run small smoke tests first (`--limit 5`). Prefer diffs/edits over rewrites.
- Record decisions in `NOTES.md` so a new chat does not need to re-derive them.
