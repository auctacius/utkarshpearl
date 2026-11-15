"""Exercise the live local Gradio API with fictional data only."""
import datetime,json,time
from pathlib import Path
from gradio_client import Client
from piiparity.app import EXAMPLES
c=Client('http://127.0.0.1:7860',verbose=False)
rows=[]
for language,text in EXAMPLES:
    started=time.perf_counter();r=c.predict(text,language,'Hybrid',api_name='/analyze')
    assert len(r)==7
    for e in r[5]: assert text[e['start']:e['end']]==e['text']
    rows.append(dict(language=language,mode='Hybrid',seconds=time.perf_counter()-started,redacted=r[1],entities=r[5]))
for mode in ['Regex','AI']:
    r=c.predict(EXAMPLES[0][1],'English',mode,api_name='/analyze')
    assert r[1]==r[2 if mode=='Regex' else 3]
    rows.append(dict(language='English',mode=mode,redacted=r[1]))
r=c.predict('','English','Hybrid',api_name='/analyze');assert r[1]=='' and r[5]==[]
rows.append(dict(case='empty',passed=True))
r=c.predict('There are 42 books.','English','Hybrid',api_name='/analyze');assert r[1]=='There are 42 books.'
rows.append(dict(case='non_sensitive',passed=True))
try:c.predict('x'*1501,'English','Hybrid',api_name='/analyze')
except Exception as e:
    assert '1,500' in str(e)
    rows.append(dict(case='overlong',passed=True,error=str(e)))
else:raise AssertionError('Overlong input was not rejected')
P=Path(__file__).resolve().parents[1]
(P/'reports/phase2_ui_checks.json').write_text(json.dumps(dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=rows,total=len(rows)),ensure_ascii=False,indent=2)+'\n')
print('Live Gradio checks passed:',len(rows))
