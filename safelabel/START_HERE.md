# START HERE (team)

**Goal:** by **10:59 PM CT tonight (11:59 PM ET)** submit SafeLabel — a study of whether a free translator keeps
medicine-label sentences safe in Hindi, Chinese and Arabic, plus a small warning tool.

## Everyone — your first 10 minutes
1. Read `PLAN.md` sections 1–2 (who does what, the four gates). It is for humans: do not paste it into AI tools.
2. Open your brief — **H** (Hindi, lead): `briefs/BRIEF_hindi_lead.md` · **C** (Chinese): `briefs/BRIEF_chinese_checks.md` · **A** (Arabic): `briefs/BRIEF_arabic_eval.md`
3. In your AI tool, paste ONLY: `AGENTS.md` + `CONTRACT.md` + your brief. (Codex and Claude Code read `AGENTS.md` / `CLAUDE.md`
   by themselves if you start them inside this folder.)
4. **First job — due 11:45 AM CT:** translate with the free NLLB model for YOUR language. In Google Colab choose
   Runtime → Change runtime type → GPU, then run these cells (replace `<lang>` with `hi`, `zh` or `ar`):
   ```
   !git clone https://github.com/auctacius/utkarshpearl repo        # (using safelabel.zip instead? upload and unzip it, then use %cd safelabel)
   %cd repo/safelabel
   !pip -q install transformers sentencepiece sacrebleu
   !python src/translate.py --lang <lang> --limit 5     # quick test first
   !python src/translate.py --lang <lang>               # the real run (a few minutes)
   !python tools/tie_out.py --lang <lang> --stage translations --quiet   # must end with: ALL CONTROL TOTALS TIE
   ```
   Then download `outputs/translations_<lang>.csv` from the Colab file panel and send it back (next section).

## Sending files back
- **GitHub:** on the repo page open the `safelabel/outputs` folder, choose *Add file → Upload files*, drag your CSV in, then *Commit changes*.
  (You must have accepted the invitation to the repo first.)
- **No GitHub:** send the file to H in the group chat; H puts it into `outputs/`.
- Only ever send files you own (`CONTRACT.md` section 3).

## The rules that matter most
- **Ratings are done by a human, never by an AI.** You are the "real speaker" check the judges ask for.
- Gates (Central Time): **11:45 AM · 2:30 PM · 4:30 PM · 6:00 PM**. Stuck for 20 minutes? Message H the last 30 lines of the error.
- The study design is frozen in `CONTRACT.md` sections 1 and 5. Do not change it after seeing results.
- This GitHub repo also holds other people's folders (`Adam's GPT`, `Alans Claude`). Only ever touch files inside `safelabel/`.
