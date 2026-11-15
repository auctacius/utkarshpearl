"""Pinned, local GLiNER inference. Never call a hosted inference service."""
import os
from pathlib import Path
from functools import lru_cache
from threading import Lock
from .core import Span, validate
MODEL_ID='urchade/gliner_multi-v2.1'
MODEL_REVISION='443d26d654e0324125a96bebd8e796c14ff2efe6'
LABEL_MAP={'person':'PERSON','location':'LOCATION','email address':'EMAIL','phone number':'PHONE'}
THRESHOLD=0.5
PROJECT=Path(__file__).resolve().parents[2]
LOCK=Lock()

def check_input(text):
    if not isinstance(text,str):raise ValueError('Input must be text.')
    if len(text)>1500:raise ValueError('Use a short paragraph: maximum 1,500 characters. Nothing was processed.')
    if any(0xD800<=ord(c)<=0xDFFF for c in text):raise ValueError('Input contains invalid Unicode surrogate characters.')
    if any(ord(c)<32 and c not in '\n\r\t' for c in text):raise ValueError('Remove control characters from the input.')

@lru_cache(maxsize=1)
def load_model():
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['HF_HUB_DISABLE_TELEMETRY']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from gliner import GLiNER
    path=PROJECT/'data/models/gliner'
    if not (path/'model.safetensors').is_file():
        raise RuntimeError('Model assets are missing. Run python experiments/download_model.py first.')
    torch.set_num_threads(4)
    model=GLiNER.from_pretrained(str(path),local_files_only=True,map_location='cpu',strict=True)
    from .tokenization import split_words
    model.data_processor.words_splitter=split_words
    model.eval()
    return model

def predict(text):
    check_input(text)
    if not text.strip():return []
    with LOCK:
        model=load_model()
        # Conservatively reserve capacity for the label prompt; never silently truncate.
        words=list(model.data_processor.words_splitter(text))
        if len(words)>300:raise ValueError('Input exceeds 300 word units. Shorten it; nothing was processed.')
        tokens=model.data_processor.transformer_tokenizer([w[0] for w in words],is_split_into_words=True,add_special_tokens=True)['input_ids']
        if len(tokens)>320:raise ValueError('Input exceeds the model token budget. Shorten it; nothing was processed.')
        import torch
        with torch.inference_mode():
            predictions=model.predict_entities(text,list(LABEL_MAP),threshold=THRESHOLD,flat_ner=True)
    results=[]
    for p in predictions:
        s=Span(int(p['start']),int(p['end']),LABEL_MAP[p['label']])
        validate(text,[s])
        if text[s.start:s.end]!=p['text']:raise RuntimeError('Model offset alignment failed; refusing redaction.')
        results.append({'span':s,'score':float(p['score']),'source':'ai'})
    return results
