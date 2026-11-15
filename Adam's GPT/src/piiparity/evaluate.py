"""Strict entity scoring and union-of-characters redaction scoring."""
import hashlib, json
from collections import defaultdict
from pathlib import Path
from .core import Span, LABELS, detect, redact, validate

def metric(tp, fp, fn):
    p=tp/(tp+fp) if tp+fp else None
    r=tp/(tp+fn) if tp+fn else None
    f=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
    return dict(tp=tp,fp=fp,fn=fn,precision=p,recall=r,f1=f)

def score(gold,pred):
    g=set(gold); p=set(pred)
    return len(g&p),len(p-g),len(g-p)

def chars(spans):
    return {i for s in spans for i in range(s.start,s.end)}

def evaluate(path, detector=detect, detector_name="regex-v0.1"):
    raw=Path(path).read_bytes()
    rows=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if len({r['id'] for r in rows})!=len(rows): raise ValueError('Duplicate IDs')
    if len({r['text'] for r in rows})!=len(rows): raise ValueError('Duplicate texts')
    totals=defaultdict(lambda:[0,0,0]); counts=defaultdict(int); examples=[]
    for row in rows:
        text=row['text']; lang=row['language']
        gold=validate(text,[Span(**s) for s in row['entities']]); pred=validate(text, detector(text))
        counts[lang]+=1
        groups={'all':(gold,pred),'characters':(chars(gold),chars(pred))}
        groups.update({label:([s for s in gold if s.label==label],[s for s in pred if s.label==label]) for label in LABELS})
        for key,(g,p) in groups.items():
            for prefix in [lang,'overall']:
                for i,n in enumerate(score(g,p)): totals[(prefix,key)][i]+=n
        examples.append(dict(id=row['id'],language=lang,input=text,
            gold=[s.to_dict() for s in gold],prediction=[s.to_dict() for s in pred],
            expected_redaction=redact(text,gold),actual_redaction=redact(text,pred)))
    results={lang:{key:metric(*totals[(lang,key)]) for key in ['all',*LABELS,'characters']} for lang in [*sorted(counts),'overall']}
    f1s=[results[l]['all']['f1'] for l in counts if results[l]['all']['f1'] is not None]
    return dict(dataset_sha256=hashlib.sha256(raw).hexdigest(),detector=detector_name,
        evaluation_kind='development smoke fixtures, NOT held-out benchmark',
        documents_by_language=dict(counts),scores=results,
        macro_language_f1=sum(f1s)/len(f1s) if f1s else None,
        language_f1_gap=max(f1s)-min(f1s) if f1s else None,examples=examples)
