"""Execute real CPU inference on fictional diagnostics; never a held-out benchmark."""
import json,time,platform,importlib.metadata,datetime
from pathlib import Path
from piiparity.ai import load_model,MODEL_ID,MODEL_REVISION,predict
from piiparity.app import EXAMPLES
from piiparity.system import compare,LANGUAGES,run
from piiparity.core import Span
from piiparity.evaluate import evaluate
P=Path(__file__).resolve().parents[1]
start=time.perf_counter();load_model();load_seconds=time.perf_counter()-start
rows=[]
for language,text in EXAMPLES:
    start=time.perf_counter();r=compare(text,LANGUAGES[language])
    for result in r.values():
        for e in result['entities']:assert text[e['start']:e['end']]==e['text']
    rows.append(dict(language=language,text=text,seconds=time.perf_counter()-start,results=r))
    print(language, r['AI']['redacted_text'],flush=True)
assert any(e['label']=='PERSON' for row in rows for e in row['results']['AI']['entities'])
assert any(e['label']=='LOCATION' for row in rows for e in row['results']['AI']['entities'])
checks={}
for text in ['', 'There are 42 books on the shelf.']:
    r=compare(text);checks[text]=r
    if not text:assert all(not x['entities'] for x in r.values())
# Diagnostic only: false positives on benign inputs are recorded, not hidden.
report=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),model=MODEL_ID,revision=MODEL_REVISION,platform=platform.platform(),load_seconds=load_seconds,examples=rows,edge_cases=checks,
 dependencies={n:importlib.metadata.version(n) for n in ['torch','transformers','gliner','gradio','sentencepiece']},evaluation_kind='development diagnostics; not independent benchmark')
(P/'reports/phase2_inference.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for mode in ['AI','Hybrid']:
    def detector(text):return [Span(e['start'],e['end'],e['label']) for e in run(text,mode)['entities']]
    result=evaluate(P/'data/smoke.jsonl',detector=detector,detector_name=mode+' GLiNER')
    (P/f'reports/phase2_{mode.lower()}_smoke.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(mode,result['scores']['overall']['all'],flush=True)
