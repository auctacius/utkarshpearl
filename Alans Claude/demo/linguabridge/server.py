"""LinguaBridge web app: a small FastAPI server behind the designed front end.

    python server.py              -> http://127.0.0.1:8000
    python server.py --port 8010

The page in web/ calls four endpoints:
    GET  /api/status   which tokenizers loaded, and whether the Ask models can run here
    GET  /api/pilot    the 12 parallel sentences and the measured tax per model
    POST /api/measure  cut a message into tokens and price it against English
    POST /api/ask      answer a question two ways: direct, and bridged through English
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from bridge import load_routes
from tax import LANGUAGES, load_pilot, tax_table
from tokenizers_lib import load_tokenizers

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")

TOKS = load_tokenizers()
PILOT = load_pilot()
TABLE = tax_table(TOKS, PILOT)
NATIVE = {"English": "English", "Spanish": "Español", "Hindi": "हिन्दी", "Mandarin": "中文",
          "Arabic": "العربية", "Kurmanji": "Kurmancî"}
RTL = {"Arabic"}

app = FastAPI(title="LinguaBridge")
_bridge = None
_bridge_lock = threading.Lock()


def ask_capability():
    """Can the answer models run on this machine? They need torch + transformers."""
    if _bridge is not None:
        return {"state": "ready", "reason": ""}
    missing = [m for m in ("torch", "transformers") if importlib.util.find_spec(m) is None]
    if missing:
        return {"state": "unavailable",
                "reason": f"The answer models need {' and '.join(missing)}, which are not installed here."}
    return {"state": "loadable", "reason": "The models download on the first question (about 4 GB)."}


@app.get("/api/status")
def status():
    return {"models": [{"name": n, "year": t.year} for n, t in TOKS.items()],
            "ask": ask_capability()}


@app.get("/api/pilot")
def pilot():
    routes = load_routes()
    return {
        "languages": [{"name": l, "native": NATIVE[l], "rtl": l in RTL} for l in LANGUAGES],
        "models": [{"name": n, "year": t.year} for n, t in TOKS.items()],
        "sentences": PILOT,
        "tax": {m: {l: round(v, 3) for l, v in row.items()} for m, row in TABLE.items()},
        "routes": {k: v for k, v in routes.items() if not k.startswith("_")},
        "routes_measured": not routes.get("_status", "").startswith("PROVISIONAL"),
    }


class MeasureIn(BaseModel):
    text: str
    language: str
    model: str
    example: int | None = None  # index into the pilot sentences, if the text is one of them


@app.post("/api/measure")
def measure(q: MeasureIn):
    if q.model not in TOKS or q.language not in PILOT:
        return JSONResponse({"error": "Unknown model or language."}, status_code=400)
    text = q.text.strip()
    if not text:
        return JSONResponse({"error": "Type or paste a message first."}, status_code=400)
    tok = TOKS[q.model]
    tokens = tok.detail(text)
    is_example = (q.example is not None and 0 <= q.example < len(PILOT[q.language])
                  and PILOT[q.language][q.example].strip() == text)
    english = PILOT["English"][q.example] if is_example else None

    def english_count(name, n_tokens):
        """Tokens the same meaning takes in English on this model."""
        if english is not None:                       # measured on this sentence's own translation
            return TOKS[name].count(english)
        return max(1, round(n_tokens / TABLE[name][q.language]))  # scaled by the 12-sentence average

    per_model = []
    for name, t in TOKS.items():
        n = t.count(text)
        en = english_count(name, n)
        per_model.append({"model": name, "year": t.year, "count": n, "english_count": en,
                          "ratio": round(n / en, 2)})
    out = {"tokens": tokens, "count": len(tokens), "per_model": per_model,
           "english_count": english_count(q.model, len(tokens)),
           "basis": "translation" if english is not None else "estimate"}
    if english is not None and q.language != "English":
        out["english"] = {"text": english, "tokens": tok.detail(english)}
    return out


class AskIn(BaseModel):
    question: str
    language: str


@app.post("/api/ask")
def ask(q: AskIn):
    global _bridge
    if q.language not in PILOT or q.language == "English":
        return JSONResponse({"error": "Choose one of the five non-English languages."}, status_code=400)
    if not q.question.strip():
        return JSONResponse({"error": "Type a question first."}, status_code=400)
    cap = ask_capability()
    if cap["state"] == "unavailable":
        return JSONResponse({"error": cap["reason"],
                             "recovery": "Open LinguaBridge_Colab.ipynb in Google Colab with a T4 GPU."},
                            status_code=503)
    with _bridge_lock:
        if _bridge is None:
            try:
                from bridge import Bridge
                _bridge = Bridge()
            except Exception as e:
                return JSONResponse({"error": f"The answer models could not load: {type(e).__name__}.",
                                     "recovery": "Check the GPU runtime and the internet connection, then try again."},
                                    status_code=503)
        direct = _bridge.direct(q.question, q.language)
        bridged = _bridge.bridged(q.question, q.language)
    routes = load_routes()
    return {"direct": direct, "bridged": bridged, "route": routes.get(q.language, {}),
            "routes_measured": not routes.get("_status", "").startswith("PROVISIONAL")}


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))


if __name__ == "__main__":
    import uvicorn

    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
