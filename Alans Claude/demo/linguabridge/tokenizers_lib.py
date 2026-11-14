"""Load the tokenizers of several real AI models.

Four tokenizers ship inside official Python packages and need no internet
or account: Llama 3, Llama 4 (Meta's `llama-models`) and two Mistral ones
(`mistral-common`). In Colab we also try GPT-4o (via `tiktoken`) and Qwen 2.5
(via `transformers`); they are skipped quietly if they can't be downloaded.
"""

from __future__ import annotations

import os
from typing import Callable, Dict

# The regular expressions Meta's own code uses to pre-split text before BPE.
LLAMA3_PATTERN = (
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*"
    r"|\s*[\r\n]+|\s+(?!\S)|\s+"
)
LLAMA4_PATTERN = (
    r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?"
    r"|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?"
    r"|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n/]*|\s*[\r\n]+|\s+(?!\S)|\s+"
)


class Tok:
    """A tokenizer with two methods: count(text) and pieces(text)."""

    def __init__(self, name: str, year: int, encode: Callable, piece: Callable):
        self.name, self.year = name, year
        self._encode, self._piece = encode, piece

    def ids(self, text: str):
        return list(self._encode(text))

    def count(self, text: str) -> int:
        return len(self.ids(text))

    def pieces(self, text: str):
        """The text cut into the pieces the model actually sees."""
        return [self._piece(i) for i in self.ids(text)]


def _pkg_file(pkg: str, rel: str) -> str:
    mod = __import__(pkg)
    return os.path.join(os.path.dirname(mod.__file__), rel)


def _tiktoken_from_file(path: str, pattern: str, name: str):
    import tiktoken
    from tiktoken.load import load_tiktoken_bpe

    enc = tiktoken.Encoding(name=name, pat_str=pattern,
                            mergeable_ranks=load_tiktoken_bpe(path), special_tokens={})
    return enc


def _piece_from_tiktoken(enc):
    return lambda i: enc.decode_single_token_bytes(i).decode("utf-8", "replace")


def load_tokenizers(verbose: bool = True) -> Dict[str, Tok]:
    toks: Dict[str, Tok] = {}

    def add(name, year, builder):
        try:
            toks[name] = builder()
            toks[name].name, toks[name].year = name, year
        except Exception as e:  # missing package or no internet: skip that model
            if verbose:
                print(f"  skipped {name}: {type(e).__name__}: {str(e)[:80]}")

    def gpt4o():
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        return Tok("", 0, lambda t: enc.encode(t), _piece_from_tiktoken(enc))

    def llama(version, pattern):
        def build():
            enc = _tiktoken_from_file(_pkg_file("llama_models", f"{version}/tokenizer.model"), pattern, version)
            return Tok("", 0, lambda t: enc.encode(t), _piece_from_tiktoken(enc))
        return build

    def tekken():
        from mistral_common.tokens.tokenizers.tekken import Tekkenizer
        k = Tekkenizer.from_file(_pkg_file("mistral_common", "data/tekken_240911.json"))
        def piece(i):
            try:
                return k.id_to_byte_piece(i).decode("utf-8", "replace")
            except Exception:
                return k.decode([i])
        return Tok("", 0, lambda t: k.encode(t, bos=False, eos=False), piece)

    def mistral_v1():
        import sentencepiece as spm
        sp = spm.SentencePieceProcessor(model_file=_pkg_file("mistral_common", "data/tokenizer.model.v1"))
        return Tok("", 0, sp.encode, lambda i: sp.id_to_piece(i).replace("▁", " "))

    def qwen():
        from transformers import AutoTokenizer
        t = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")
        return Tok("", 0, lambda s: t.encode(s, add_special_tokens=False),
                   lambda i: t.decode([i]))

    add("Mistral 7B v1", 2023, mistral_v1)
    add("Llama 3", 2024, llama("llama3", LLAMA3_PATTERN))
    add("Mistral Tekken", 2024, tekken)
    add("GPT-4o", 2024, gpt4o)
    add("Qwen 2.5", 2024, qwen)
    add("Llama 4", 2025, llama("llama4", LLAMA4_PATTERN))
    if verbose:
        print("Loaded tokenizers:", ", ".join(toks))
    return toks
