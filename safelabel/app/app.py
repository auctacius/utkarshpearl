"""
app.py -- the SafeLabel demo (Gradio). Owner: Person H.

    python app/app.py                       # opens http://127.0.0.1:7860
    from app.app import build_demo          # what the Colab notebook does

You type (or pick) an English medicine-label sentence and a language. The app translates it with the free
NLLB-200 model, runs our checks, and shows ONE of three boxes: "Don't rely on this", "Unsure", or
"No problems found by our checks - still confirm with your pharmacist". It never says "safe".

If the translator cannot start (no model, no internet, no GPU) the live button shows a friendly message, and the
"saved examples" below it still work, because they were computed earlier and stored in outputs/demo_cache.json.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from safelabel import predict  # noqa: E402

INTRO = (
    "# SafeLabel\n"
    "**Can you trust a machine translation of a medicine label?** Type an English instruction, choose a language, "
    "and we translate it with a free model and check it for changed numbers and lost \"do not\" words.\n\n"
    "*" + predict.DISCLAIMER + "*"
)
PLACEHOLDER = "Take 2 tablets every 6 hours. Do not take more than 8 tablets in 24 hours."


def _message_box(text: str) -> str:
    return f"<div style='border-left:8px solid #888;padding:8px 14px;margin:8px 0'>{html.escape(text)}</div>"


def build_demo(translator=None, thresholds=None, cache_path=None):
    """Make the Gradio app. `translator`, `thresholds` and `cache_path` can be replaced for testing."""
    import gradio as gr

    cached = predict.load_cached_examples(cache_path)
    thresholds = thresholds if thresholds is not None else predict.load_thresholds()

    def run_live(sentence, lang):
        try:
            result = predict.check_translation(sentence, lang, translator=translator, thresholds=thresholds)
        except ValueError as err:                      # empty text, wrong language
            return _message_box(str(err))
        except Exception as err:                       # model could not start (no internet, no memory ...)
            return _message_box("The live translator could not run here (" + type(err).__name__ + "). "
                                "Pick a saved example below instead.")
        return predict.render_result_html(result)

    def show_saved(index):
        if index in (None, ""):
            return _message_box("Pick a saved example first.")
        return predict.render_result_html(cached[int(index)])

    with gr.Blocks(title="SafeLabel") as demo:
        gr.Markdown(INTRO)
        with gr.Row():
            sentence = gr.Textbox(label="English medicine instruction", lines=3, placeholder=PLACEHOLDER)
            lang = gr.Dropdown(choices=[("Hindi", "hi"), ("Chinese", "zh"), ("Arabic", "ar")], value="hi",
                               label="Translate into")
        go = gr.Button("Check the translation", variant="primary")
        out = gr.HTML()
        go.click(run_live, [sentence, lang], out)

        if cached:
            gr.Markdown("### Saved examples (these work without the translator)")
            labels = [(f"{predict.LANG_NAMES.get(r['lang'], r['lang'])}: {r['src_en'][:60]}", str(i))
                      for i, r in enumerate(cached)]
            pick = gr.Dropdown(choices=labels, label="Pick an example")
            show = gr.Button("Show saved example")
            show.click(show_saved, pick, out)
    return demo


if __name__ == "__main__":
    build_demo().launch()
