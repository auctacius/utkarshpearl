# Demo video script (target 1:55, hard limit 2:00)

Screen recording with our own voices. Record the app running in Colab with the **real** models,
never the stand-in mode (the yellow banner must not be on screen). Fill each `[bracket]` from
`data/results.json`. About 230 words.

| Time | On screen | Who |
| --- | --- | --- |
| 0:00 to 0:15 | The app, example text already pasted | Storyteller |
| 0:15 to 1:15 | Click "Translate and check"; open flagged lines | Integrator, then each speaker |
| 1:15 to 1:45 | The Evidence page: chart, then the language table | Builder |
| 1:45 to 1:55 | The "Where it fails" gallery, one case open | Storyteller |

**0:00 The problem.**
"A small shop that serves families in five languages can't pay a translator to check every line.
It uses a free translator and hopes. LocaleOS tells the owner which lines to worry about."

**0:15 The demo.**
"Here is a shop's text: a welcome line, a shipping offer, an order update, a medicine
instruction. One click translates it into Spanish, Hindi, Mandarin, Arabic and Kurmanji.
Out of 30 translations, LocaleOS marks [N] for review."

*(Open one flagged line.)* "This one is flagged because [the reason shown]. Translated back
into English it says '[back-translation]'."

*(The speaker of that language, in one sentence:)* "I speak [language], and this is wrong:
it actually says [what it says]."

*(Open a second flagged line in another language; that speaker confirms or disagrees.)*

"The owner exports only the flagged lines and sends those to a human."

**1:15 How it works.**
"We trained on [N] translations of FLORES+ sentences and tested on [N] it had never seen. If a
human reviews just the 20% we flag, they catch [X] percent of the bad translations. Picking at
random catches 20. The translator's own confidence catches [Z]. It [also works / works less
well] on a language it never trained on: [Kurmanji number]."

**1:45 Limits and next.**
"It misses fluent sentences that are simply wrong, like this one. Our 'bad' label is automatic,
so we each checked a sample in our own language. Next we'd test with a real business.
LocaleOS is a prototype."

## Before recording
- Run the demo once so the models are already loaded; cut all loading time from the video.
- Browser zoom 125%, notifications off, bookmarks bar hidden.
- Pick the two flagged lines in advance, and have each speaker read the real translation first.
  If the speaker thinks a flag is wrong, say so on camera: that honesty scores.
- Record a rough backup by Sunday 3 PM ET. Upload as Unlisted on YouTube, then open the link in a
  private window.
- No names, faces or school on screen: Round 1 is reviewed blind.
