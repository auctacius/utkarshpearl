"""LocaleOS web app server.

    python server.py                       -> http://127.0.0.1:8000
    LOCALEOS_STANDIN=1 python server.py    -> same, with fake models (no GPU needed; for testing only)

Endpoints used by the page in web/:
    GET  /api/status     what can run here, and whether the flagger has been trained
    POST /api/review     translate English text and flag the translations a human should check
    GET  /api/evidence   the test results written by evaluate_qe.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from build_dataset import out_dir
from models import NATIVE, RTL, TARGETS, load_models, use_standin
from qe import Flagger, signals

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
MAX_LINES, MAX_CHARS = 40, 600

app = FastAPI(title="LocaleOS")
_models = None                # (translator, embedder, standin), loaded on the first request
_lock = threading.Lock()


def load_flagger() -> Flagger:
    path = os.path.join(out_dir(), "model.json")
    return Flagger.load(path) if os.path.exists(path) else Flagger.untrained_default()


def capability() -> dict:
    if _models is not None or use_standin():
        return {"state": "ready", "reason": ""}
    missing = [m for m in ("torch", "transformers") if importlib.util.find_spec(m) is None]
    if missing:
        return {"state": "unavailable",
                "reason": f"The translation model needs {' and '.join(missing)}, which are not installed on this machine."}
    return {"state": "loadable", "reason": "The models download on first use (about 4 GB)."}


@app.get("/api/status")
def status():
    return {"languages": [{"name": l, "native": NATIVE[l], "rtl": l in RTL} for l in TARGETS],
            "models": capability(), "standin": use_standin(),
            "flagger_trained": load_flagger().trained,
            "has_results": os.path.exists(os.path.join(out_dir(), "results.json"))}


class ReviewIn(BaseModel):
    text: str
    languages: list[str] = TARGETS
    glossary: list[str] = []


@app.post("/api/review")
def review(q: ReviewIn):
    global _models
    lines = [ln.strip()[:MAX_CHARS] for ln in q.text.splitlines() if ln.strip()][:MAX_LINES]
    languages = [l for l in q.languages if l in TARGETS]
    if not lines:
        return JSONResponse({"error": "Paste some English text first."}, status_code=400)
    if not languages:
        return JSONResponse({"error": "Pick at least one language."}, status_code=400)
    cap = capability()
    if cap["state"] == "unavailable":
        return JSONResponse({"error": cap["reason"],
                             "recovery": "Open LocaleOS_Colab.ipynb in Google Colab with a T4 GPU."}, status_code=503)
    with _lock:
        if _models is None:
            try:
                _models = load_models()
            except Exception as e:
                return JSONResponse({"error": f"The models could not load ({type(e).__name__}).",
                                     "recovery": "Check the GPU runtime and the internet connection, then try again."},
                                    status_code=503)
        translator, embedder, standin = _models
        flagger = load_flagger()
        glossary = [g.strip() for g in q.glossary if g.strip()]
        segments = [{"source": ln, "items": []} for ln in lines]
        for lang in languages:
            translations, confidences = translator.translate(lines, "English", lang)
            backs, _ = translator.translate(translations, lang, "English")
            sims = embedder.similarity(lines, translations) if embedder else [None] * len(lines)
            typical = flagger.typical_log_ratio.get(lang, flagger.typical_log_ratio.get("*", 0.0))
            for i, source in enumerate(lines):
                sig = signals(source, translations[i], backs[i], lang, confidence=confidences[i],
                              meaning_similarity=sims[i], typical_log_ratio=typical)
                score = float(flagger.score([sig])[0])
                band, reasons = flagger.band(score), flagger.reasons(sig)
                # two plain rules sit on top of the model, because these mistakes are never acceptable
                if sig["numbers_lost"] > 0:
                    rule = "A number in the original is missing or different."
                    reasons = [rule] + [r for r in reasons if r != rule]
                    band = "check" if band == "clear" else band
                lost = [g for g in glossary if g.lower() in source.lower() and g.lower() not in translations[i].lower()]
                if lost:
                    reasons = [f"The protected term “{g}” is missing." for g in lost] + reasons
                    band = "review"
                if band != "clear" and not reasons:
                    reasons = ["Several small warning signs added up."]
                segments[i]["items"].append({"language": lang, "translation": translations[i], "back": backs[i],
                                             "score": round(score, 3), "band": band, "reasons": reasons[:3]})
    counts = {b: sum(it["band"] == b for s in segments for it in s["items"]) for b in ("clear", "check", "review")}
    return {"segments": segments, "counts": counts, "trained": flagger.trained, "standin": standin}


@app.get("/api/evidence")
def evidence():
    path = os.path.join(out_dir(), "results.json")
    if not os.path.exists(path):
        return {"available": False}
    with open(path, encoding="utf-8") as f:
        return {"available": True, **json.load(f)}


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
