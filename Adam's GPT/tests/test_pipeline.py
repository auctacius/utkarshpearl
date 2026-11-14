import unittest
from piiparity.core import Span,detect,redact,validate,infer
from piiparity.evaluate import score,metric,evaluate
class PipelineTests(unittest.TestCase):
    def test_email(self): self.assertEqual(infer('Email a@example.com.')['redacted_text'],'Email [EMAIL].')
    def test_unicode_offsets(self):
        t='🙂中文：a@example.com';s=detect(t)[0];self.assertEqual(t[s.start:s.end],'a@example.com');self.assertEqual(s.start,4)
    def test_devanagari_digits(self): self.assertEqual(len(detect('+१-२०२-५५५-०१००')),1)
    def test_negatives(self): self.assertEqual(detect('42 books on 2026-11-14'),[])
    def test_empty(self): self.assertEqual(infer('')['redacted_text'],'')
    def test_repeat(self): self.assertEqual(len(detect('a@example.com a@example.com')),2)
    def test_boundaries(self): self.assertEqual(detect('x+12025550100'),[])
    def test_local_phone_limitation(self): self.assertEqual(detect('202-555-0101'),[])
    def test_name_limitation(self): self.assertEqual(detect('Mira Example'),[])
    def test_bad_offsets(self):
        with self.assertRaises(ValueError): redact('abc',[Span(0,4,'PERSON')])
    def test_overlap(self):
        with self.assertRaises(ValueError): redact('abc',[Span(0,2,'PERSON'),Span(1,3,'LOCATION')])
    def test_exact_scoring(self): self.assertEqual(score([Span(0,3,'PERSON')],[Span(0,2,'PERSON')]),(0,1,1))
    def test_wrong_label(self): self.assertEqual(score([Span(0,3,'PERSON')],[Span(0,3,'LOCATION')]),(0,1,1))
    def test_undefined(self): self.assertIsNone(metric(0,0,0)['f1'])
    def test_multiple_redactions(self):
        self.assertEqual(infer('a@example.com +1-202-555-0100')['redacted_text'],'[EMAIL] [PHONE]')
    def test_dataset(self):
        r=evaluate('data/smoke.jsonl');self.assertEqual(sum(r['documents_by_language'].values()),48)
        self.assertEqual(r['scores']['overall']['all']['fn'],24)
if __name__=='__main__': unittest.main()
