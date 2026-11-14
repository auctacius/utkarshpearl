"""LinguaBridge: use AI in your own language, at a fair price.

Tab 1, Language Tax: paste a message and see what it costs on real AI models,
       word by word, against the same meaning in English.
Tab 2, Ask: ask a question in Spanish, Hindi, Mandarin, Arabic or Kurmanji.
       See the direct answer and the bridged answer (via English) side by side.
Tab 3, Findings: the tax for every language on every model.

Run:  python app.py            (local)
      python app.py --share    (Colab: gives a public link for 72 hours)
"""

from __future__ import annotations

import argparse

import gradio as gr
import pandas as pd

from bridge import load_routes
from tax import LANGUAGES, load_pilot, tax_table
from tokenizers_lib import load_tokenizers

TOKS = load_tokenizers()
PILOT = load_pilot()
TABLE = tax_table(TOKS, PILOT)
MODELS = list(TOKS)
DEFAULT_MODEL = "Llama 4" if "Llama 4" in TOKS else MODELS[-1]
NON_ENGLISH = [l for l in LANGUAGES if l != "English"]

QUESTIONS = {
    "Spanish": "¿Cuántas veces al día debo tomar un medicamento si la receta dice «cada 8 horas»?",
    "Hindi": "अगर दवा की पर्ची पर 'हर 8 घंटे' लिखा है तो मुझे दिन में कितनी बार दवा लेनी चाहिए?",
    "Mandarin": "如果药方上写着“每8小时一次”，我一天应该吃几次药？",
    "Arabic": "إذا كانت الوصفة تقول «كل 8 ساعات»، فكم مرة في اليوم يجب أن أتناول الدواء؟",
    "Kurmanji": "Ger li ser reçeteyê \"her 8 saetan\" hatibe nivîsîn, divê ez rojê çend caran dermanê bixwim?",
}

BRIDGE = None  # loaded on first question (needs a GPU and ~4 GB download)


# ----------------------------------------------------------------- Tab 1
def measure(text: str, lang: str, model: str):
    text = (text or "").strip()
    if not text:
        return "Type or paste a message first.", [], None, None
    tok = TOKS[model]
    n = tok.count(text)
    mult = TABLE[model][lang]
    english_equiv = max(1, round(n / mult))
    if lang == "English":
        headline = f"### {n} tokens on {model}\nThis is the baseline every other language is compared with."
    else:
        extra = (mult - 1) * 100
        word = "more" if extra >= 0 else "less"
        headline = (
            f"### {n} tokens on {model}\n"
            f"The same meaning in English takes about **{english_equiv} tokens**. "
            f"On {model}, {lang} speakers pay **{mult:.1f}x** the English price: "
            f"{abs(extra):.0f}% {word} for every message, and their conversations "
            f"fill the model's memory {mult:.1f} times faster."
        )
    pieces = tok.pieces(text)
    highlighted = [(p, "A" if i % 2 == 0 else "B") for i, p in enumerate(pieces)]
    per_model = pd.DataFrame(
        [{"Model": m, "Year": t.year, "Tokens for this message": t.count(text),
          f"{lang} tax (x English)": round(TABLE[m][lang], 2)} for m, t in TOKS.items()]
    )
    chart = pd.DataFrame([{"Language": l, "Times English": round(TABLE[model][l], 2)} for l in LANGUAGES])
    return headline, highlighted, per_model, chart


def fill_example(lang: str):
    return PILOT[lang][0]


# ----------------------------------------------------------------- Tab 2
def ask(question: str, lang: str):
    global BRIDGE
    question = (question or "").strip()
    if not question:
        return "Type a question first.", "", "", "", ""
    if BRIDGE is None:
        try:
            from bridge import Bridge

            BRIDGE = Bridge()
        except Exception as e:  # no GPU, no internet, or transformers missing
            msg = (f"The answer models could not load here ({type(e).__name__}). "
                   "Run this tab in Colab with a T4 GPU: see LinguaBridge_Colab.ipynb.")
            return msg, "", "", "", ""
    d = BRIDGE.direct(question, lang)
    b = BRIDGE.bridged(question, lang)
    routes = load_routes()
    r = routes.get(lang, {})
    measured = not routes.get("_status", "").startswith("PROVISIONAL")
    basis = ("measured on the Belebele reading test" if measured
             else "provisional, from the token-tax pilot; run evaluate.py to measure it")
    rec = (f"**LinguaBridge would use the {r.get('route', 'direct')} route for {lang}** ({basis}). "
           f"The bridged route asked the model in English: \"{b['english_question']}\"")
    return d["answer"], f"{d['tokens']} tokens", b["answer"], f"{b['tokens']} tokens", rec


# ----------------------------------------------------------------- Tab 3
def findings_table():
    rows = []
    for m in MODELS:
        row = {"Model": m, "Year": TOKS[m].year}
        row.update({l: f"{TABLE[m][l]:.2f}x" for l in LANGUAGES})
        rows.append(row)
    return pd.DataFrame(rows).sort_values("Year")


GRADIO_6 = int(gr.__version__.split(".")[0]) >= 6
THEME = gr.themes.Soft()
with gr.Blocks(title="LinguaBridge", **({} if GRADIO_6 else {"theme": THEME})) as demo:
    gr.Markdown(
        "# LinguaBridge\n"
        "**AI charges you more, and understands you less, when you don't speak English.** "
        "LinguaBridge shows the price of your language and gets you a better answer anyway. "
        "Built for Spanish, Hindi, Mandarin, Arabic and Kurmanji speakers."
    )
    with gr.Tab("1. The Language Tax"):
        with gr.Row():
            lang_in = gr.Dropdown(LANGUAGES, value="Kurmanji", label="Language of your message")
            model_in = gr.Dropdown(MODELS, value=DEFAULT_MODEL, label="AI model")
        text_in = gr.Textbox(lines=3, label="Your message", value=PILOT["Kurmanji"][0])
        go = gr.Button("Measure the tax", variant="primary")
        headline = gr.Markdown()
        pieces = gr.HighlightedText(label="What the model actually sees: each colour is one token",
                                    color_map={"A": "#c7dcf5", "B": "#f5dcc7"}, show_legend=False,
                                    combine_adjacent=False)
        with gr.Row():
            per_model = gr.Dataframe(label="This message on every model")
            chart = gr.BarPlot(x="Language", y="Times English", title="Tax per language on this model",
                               y_lim=[0, 2.5], height=260)
        lang_in.change(fill_example, lang_in, text_in)
        for trigger in (go.click, model_in.change):
            trigger(measure, [text_in, lang_in, model_in], [headline, pieces, per_model, chart])
        demo.load(measure, [text_in, lang_in, model_in], [headline, pieces, per_model, chart])

    with gr.Tab("2. Ask in your language"):
        gr.Markdown("Two routes to the same free AI model: ask it **directly** in your language, or "
                    "**bridge** through English with a translation model. Needs a GPU (Colab T4).")
        with gr.Row():
            q_lang = gr.Dropdown(NON_ENGLISH, value="Kurmanji", label="Language")
        q_in = gr.Textbox(lines=2, label="Your question", value=QUESTIONS["Kurmanji"])
        ask_btn = gr.Button("Ask both ways", variant="primary")
        with gr.Row():
            with gr.Column():
                gr.Markdown("#### Direct")
                d_out, d_tok = gr.Textbox(label="Answer", lines=5), gr.Textbox(label="Model tokens used")
            with gr.Column():
                gr.Markdown("#### Bridged through English")
                b_out, b_tok = gr.Textbox(label="Answer", lines=5), gr.Textbox(label="Model tokens used")
        rec = gr.Markdown()
        q_lang.change(lambda l: QUESTIONS[l], q_lang, q_in)
        ask_btn.click(ask, [q_in, q_lang], [d_out, d_tok, b_out, b_tok, rec])

    with gr.Tab("3. Findings"):
        gr.Markdown(
            "Tokens needed for the same 12 sentences, as a multiple of English. "
            "Newer models cut the tax sharply for Hindi and Arabic; Kurmanji stays the most expensive.\n\n"
            "*Pilot: 12 sentences translated with AI help; each of us must check our own language before we report it. "
            "The full study uses the 1,012 professional FLORES+ sentences.*"
        )
        gr.Dataframe(findings_table())
    gr.Markdown("*Prototype built for the Veritas AI Hackathon 2026, Languages track.*")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", action="store_true")
    ap.add_argument("--port", type=int, default=7860)
    a = ap.parse_args()
    demo.launch(share=a.share, server_port=a.port, **({"theme": THEME} if GRADIO_6 else {}))
