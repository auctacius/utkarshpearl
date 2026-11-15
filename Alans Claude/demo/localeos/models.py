"""The two pretrained models LocaleOS builds on. Both are free and open.

Translator  NLLB-200 (Meta): translates between 200 languages, including all
            five of ours. It also reports how confident it was in each output.
Embedder    LaBSE (Google): turns a sentence in any language into a vector, so
            the meaning of a source and its translation can be compared.

Both need a GPU to run at a useful speed (Colab: Runtime > Change runtime type
> T4 GPU). The first use downloads about 4 GB.
"""

from __future__ import annotations

import os

# The language codes NLLB uses.
NLLB_CODES = {
    "English": "eng_Latn",
    "Spanish": "spa_Latn",
    "Hindi": "hin_Deva",
    "Mandarin": "zho_Hans",
    "Arabic": "arb_Arab",
    "Kurmanji": "kmr_Latn",
}
TARGETS = [lang for lang in NLLB_CODES if lang != "English"]
NATIVE = {"English": "English", "Spanish": "Español", "Hindi": "हिन्दी", "Mandarin": "中文",
          "Arabic": "العربية", "Kurmanji": "Kurmancî"}
RTL = {"Arabic"}

TRANSLATOR = "facebook/nllb-200-distilled-600M"
EMBEDDER = "sentence-transformers/LaBSE"


def use_standin() -> bool:
    """LOCALEOS_STANDIN=1 swaps in fake models, to test the code without a GPU."""
    return os.environ.get("LOCALEOS_STANDIN") == "1"


class Translator:
    def __init__(self, device: str | None = None):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.tok = AutoTokenizer.from_pretrained(TRANSLATOR)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(TRANSLATOR, torch_dtype=dtype).to(self.device)

    def translate(self, texts: list[str], source: str, target: str, batch_size: int = 16):
        """Translate a list of sentences. Returns (translations, confidences).

        The confidence is the model's own length-normalised log-probability for
        the output it chose: closer to 0 means more sure, more negative means
        less sure.
        """
        out_text, out_conf = [], []
        self.tok.src_lang = NLLB_CODES[source]
        target_id = self.tok.convert_tokens_to_ids(NLLB_CODES[target])
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            batch = self.tok(chunk, return_tensors="pt", padding=True, truncation=True,
                             max_length=256).to(self.device)
            with self.torch.no_grad():
                gen = self.model.generate(**batch, forced_bos_token_id=target_id, max_new_tokens=256,
                                          num_beams=4, output_scores=True, return_dict_in_generate=True)
            out_text += self.tok.batch_decode(gen.sequences, skip_special_tokens=True)
            out_conf += [float(s) for s in gen.sequences_scores]
        return out_text, out_conf


class Embedder:
    def __init__(self, device: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(EMBEDDER, device=device)

    def similarity(self, a: list[str], b: list[str]) -> list[float]:
        """Cosine similarity between a[i] and b[i], from about 0 to 1."""
        ea = self.model.encode(a, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        eb = self.model.encode(b, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return [float(x @ y) for x, y in zip(ea, eb)]


def load_models():
    """Returns (translator, embedder or None, is_standin)."""
    if use_standin():
        from standin import StandinEmbedder, StandinTranslator
        return StandinTranslator(), StandinEmbedder(), True
    translator = Translator()
    try:
        embedder = Embedder()
    except Exception as e:  # LaBSE is optional: the flagger works without it
        print(f"Sentence embedder not available ({type(e).__name__}); continuing without it.")
        embedder = None
    return translator, embedder, False
