"""Three explicit inference modes built on the unchanged baseline."""
from .core import detect, redact, validate
from .ai import predict,check_input,MODEL_ID,MODEL_REVISION
LANGUAGES={'English':'en','Kurmanji (experimental)':'ku','Hindi':'hi','Simplified Chinese':'zh','Spanish':'es','Turkish':'tr'}
MODES=('Regex','AI','Hybrid')

def resolve(candidates):
    """Regex structured spans first, then AI score, length, start, label."""
    ranked=sorted(candidates,key=lambda c:(c['source']!='regex',-(c['score'] or 0),-(c['span'].end-c['span'].start),c['span'].start,c['span'].label))
    keep=[]
    for c in ranked:
        s=c['span']
        if not any(s.start<k['span'].end and k['span'].start<s.end for k in keep):keep.append(c)
    return sorted(keep,key=lambda c:(c['span'].start,c['span'].end,c['span'].label))

def make_result(text,candidates,mode,language):
    selected=resolve(candidates);spans=validate(text,[c['span'] for c in selected])
    return dict(mode=mode,language=language,model=MODEL_ID if mode!='Regex' else None,
        revision=MODEL_REVISION if mode!='Regex' else None,
        entities=[dict(**c['span'].to_dict(),text=text[c['span'].start:c['span'].end],
            score=c['score'],source=c['source']) for c in selected],
        redacted_text=redact(text,spans),dropped_overlaps=len(candidates)-len(selected),
        warning='May miss identifying information. Scores are uncalibrated model outputs, not probabilities of safety.')

def run(text,mode='Hybrid',language='en',ai_predictions=None):
    check_input(text)
    if mode not in MODES:raise ValueError('Unknown detector mode.')
    if language not in LANGUAGES.values():raise ValueError('Unknown language selection.')
    candidates=[]
    if mode in ('Regex','Hybrid'):candidates.extend(dict(span=s,score=None,source='regex') for s in detect(text))
    if mode in ('AI','Hybrid'):candidates.extend(predict(text) if ai_predictions is None else ai_predictions)
    return make_result(text,candidates,mode,language)

def compare(text,language='en'):
    check_input(text)
    predictions=predict(text)
    return {mode:run(text,mode,language,predictions) for mode in MODES}

def highlights(text,entities):
    chunks=[];cursor=0
    for e in entities:
        if cursor<e['start']:chunks.append((text[cursor:e['start']],None))
        chunks.append((text[e['start']:e['end']],e['label']));cursor=e['end']
    if cursor<len(text):chunks.append((text[cursor:],None))
    return chunks
