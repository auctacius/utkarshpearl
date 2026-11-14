"""The bridge: answer a question asked in any of our languages, two ways.

  direct  - ask the AI model in the user's own language
  bridged - translate to English (NLLB-200), ask in English, translate back

Both run on free open models, so this needs a GPU (Colab: Runtime > Change
runtime type > T4 GPU). The first call downloads about 4 GB of models.
"""

from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Language codes used by the NLLB-200 translation model and the FLORES+ dataset.
NLLB_CODES = {
    "English": "eng_Latn",
    "Spanish": "spa_Latn",
    "Hindi": "hin_Deva",
    "Mandarin": "zho_Hans",
    "Arabic": "arb_Arab",
    "Kurmanji": "kmr_Latn",
}

TRANSLATOR = "facebook/nllb-200-distilled-600M"
CHAT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"  # small, free, no account needed


def load_routes():
    """Which path to use per language. evaluate.py overwrites this file with
    measured results; until then it holds a provisional guess from the pilot."""
    with open(os.path.join(HERE, "data", "route_table.json"), encoding="utf-8") as f:
        return json.load(f)


class Bridge:
    def __init__(self, device: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.mt_tok = AutoTokenizer.from_pretrained(TRANSLATOR)
        self.mt = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATOR, torch_dtype=dtype).to(self.device)
        self.lm_tok = AutoTokenizer.from_pretrained(CHAT_MODEL)
        self.lm = AutoModelForCausalLM.from_pretrained(CHAT_MODEL, torch_dtype=dtype).to(self.device)

    # --- translation -------------------------------------------------------
    def translate(self, text: str, src: str, tgt: str) -> str:
        if src == tgt:
            return text
        self.mt_tok.src_lang = NLLB_CODES[src]
        batch = self.mt_tok(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with self.torch.no_grad():
            out = self.mt.generate(
                **batch,
                forced_bos_token_id=self.mt_tok.convert_tokens_to_ids(NLLB_CODES[tgt]),
                max_new_tokens=400,
            )
        return self.mt_tok.batch_decode(out, skip_special_tokens=True)[0]

    # --- the chat model ----------------------------------------------------
    def chat(self, prompt: str, language: str, max_new_tokens: int = 200):
        """Returns (answer, tokens the model read, tokens it wrote)."""
        system = f"You are a helpful assistant. Answer briefly and clearly in {language}."
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        text = self.lm_tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        ids = self.lm_tok(text, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.lm.generate(**ids, max_new_tokens=max_new_tokens, do_sample=False)
        new = out[0][ids["input_ids"].shape[1]:]
        return self.lm_tok.decode(new, skip_special_tokens=True).strip(), ids["input_ids"].shape[1], len(new)

    # --- the two paths -----------------------------------------------------
    def direct(self, question: str, language: str) -> dict:
        answer, read, wrote = self.chat(question, language)
        return {"route": "direct", "answer": answer, "tokens": read + wrote}

    def bridged(self, question: str, language: str) -> dict:
        english_q = self.translate(question, language, "English")
        english_a, read, wrote = self.chat(english_q, "English")
        answer = self.translate(english_a, "English", language)
        return {"route": "bridged", "answer": answer, "tokens": read + wrote,
                "english_question": english_q, "english_answer": english_a}
