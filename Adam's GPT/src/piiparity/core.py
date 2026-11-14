"""Original Unicode-offset baseline. No network calls or input logging."""
from dataclasses import dataclass, asdict
import re
LABELS = ('PERSON', 'EMAIL', 'PHONE', 'LOCATION')
@dataclass(frozen=True, order=True)
class Span:
    start: int
    end: int
    label: str
    def to_dict(self):
        return asdict(self)

def validate(text, spans):
    spans = sorted(spans)
    for i, s in enumerate(spans):
        if s.label not in LABELS or not 0 <= s.start < s.end <= len(text):
            raise ValueError('Invalid label or Unicode code-point offsets')
        if i and spans[i-1].end > s.start:
            raise ValueError('Overlapping spans are not supported')
    return spans

EMAIL = re.compile(r'(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}(?![A-Za-z0-9_\-])')
# Deliberately conservative: international + prefix and 8-15 Unicode digits.
PHONE = re.compile(r'(?<![\w+])\+\d(?:[\d ()\-]{6,30})\d(?!\w)')
def detect(text):
    candidates = [Span(m.start(),m.end(),'EMAIL') for m in EMAIL.finditer(text)]
    for m in PHONE.finditer(text):
        if 8 <= sum(c.isdecimal() for c in m.group()) <= 15:
            candidates.append(Span(m.start(),m.end(),'PHONE'))
    # EMAIL priority for overlaps, then earlier start and longer match.
    selected=[]
    for s in sorted(candidates,key=lambda s:(s.label!='EMAIL',s.start,-s.end)):
        if not any(s.start < t.end and t.start < s.end for t in selected): selected.append(s)
    return validate(text, selected)

def redact(text, spans):
    spans=validate(text,spans)
    for s in reversed(spans): text=text[:s.start]+'['+s.label+']'+text[s.end:]
    return text

def infer(text):
    spans=detect(text)
    return {'detector':'regex-v0.1','entities':[s.to_dict() for s in spans],
            'redacted_text':redact(text,spans),
            'limitations':'PERSON and LOCATION are not detected; missed PII can remain.'}
