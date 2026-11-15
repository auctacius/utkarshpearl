import unittest
from unittest.mock import patch
from piiparity.core import Span,redact
from piiparity.ai import check_input,predict
from piiparity.system import resolve,run,highlights

def item(start,end,label,score=.9,source='ai'):
    return dict(span=Span(start,end,label),score=score,source=source)
class SystemTests(unittest.TestCase):
    def test_overlap_regex_priority(self):
        a=item(0,9,'PERSON');b=item(2,7,'EMAIL',None,'regex')
        self.assertEqual(resolve([a,b]),[b]);self.assertEqual(resolve([b,a]),[b])
    def test_ai_score_priority(self):
        a=item(0,4,'PERSON',.6);b=item(0,8,'LOCATION',.9)
        self.assertEqual(resolve([a,b]),[b])
    def test_stable_tie(self):
        a=item(0,4,'PERSON');b=item(0,4,'LOCATION')
        self.assertEqual(resolve([a,b]),resolve([b,a]))
    def test_adjacent_spans(self):self.assertEqual(len(resolve([item(0,2,'PERSON'),item(2,4,'LOCATION')])),2)
    def test_hybrid_multiple_types(self):
        t='Mira in London, a@example.com +1-202-555-0100.'
        r=run(t,'Hybrid',ai_predictions=[item(0,4,'PERSON'),item(8,14,'LOCATION')])
        self.assertEqual(r['redacted_text'],'[PERSON] in [LOCATION], [EMAIL] [PHONE].')
        for e in r['entities']:self.assertEqual(t[e['start']:e['end']],e['text'])
    def test_non_sensitive_untouched(self):
        t='🙂  Asha\n  Delhi!';r=run(t,'AI',ai_predictions=[item(3,7,'PERSON'),item(10,15,'LOCATION')])
        self.assertEqual(r['redacted_text'],'🙂  [PERSON]\n  [LOCATION]!')
        self.assertEqual(''.join(x[0] for x in highlights(t,r['entities'])),t)
    def test_empty_no_model_load(self):
        with patch('piiparity.ai.load_model',side_effect=AssertionError):self.assertEqual(predict('  \n'),[])
    def test_regex_without_ai(self):
        with patch('piiparity.system.predict',side_effect=AssertionError):self.assertEqual(run('hello','Regex')['entities'],[])
    def test_bad_type(self):
        for bad in [None,1,[],{}]:
            with self.assertRaises(ValueError):check_input(bad)
    def test_long(self):
        with self.assertRaises(ValueError):check_input('x'*1501)
    def test_invalid_unicode(self):
        with self.assertRaises(ValueError):check_input('\ud800')
    def test_controls(self):
        with self.assertRaises(ValueError):check_input('a\x00b')
    def test_bad_mode(self):
        with self.assertRaises(ValueError):run('hello','other')
    def test_bad_language(self):
        with self.assertRaises(ValueError):run('hello','Regex','xx')
    def test_non_sensitive(self):self.assertEqual(run('There are 42 books.','AI',ai_predictions=[])['redacted_text'],'There are 42 books.')
    def test_no_regex_confidence(self):self.assertIsNone(run('a@example.com','Regex')['entities'][0]['score'])
if __name__=='__main__':unittest.main()

class TokenizationTests(unittest.TestCase):
    def test_combining_marks(self):
        from piiparity.tokenization import split_words
        self.assertEqual([t[0] for t in split_words('आशा शर्मा')],['आशा','शर्मा'])
    def test_han_offsets(self):
        from piiparity.tokenization import split_words
        t='🙂李明在北京';tokens=list(split_words(t))
        self.assertEqual([x[0] for x in tokens],list(t))
        for value,start,end in tokens:self.assertEqual(t[start:end],value)
    def test_multiscript_lossless(self):
        from piiparity.tokenization import split_words
        t='Roj Azad, आशा शर्मा / 李明.'
        self.assertEqual(''.join(x[0] for x in split_words(t)),''.join(t.split()))
