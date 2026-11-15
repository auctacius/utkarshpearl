import argparse,json,sys
from .core import infer
from .evaluate import evaluate

def main():
    p=argparse.ArgumentParser(description='PIIParity local research baseline')
    sub=p.add_subparsers(dest='command',required=True)
    rp=sub.add_parser('redact',help='Read UTF-8 text from stdin; emit redacted JSON')
    rp.add_argument('--mode',choices=['Regex','AI','Hybrid'],default='Regex')
    rp.add_argument('--language',choices=['en','ku','hi','zh','es','tr'],default='en')
    e=sub.add_parser('evaluate');e.add_argument('dataset')
    args=p.parse_args()
    if args.command=='redact':
        from .system import run
        result=run(sys.stdin.read(),args.mode,args.language)
    else:
        result=evaluate(args.dataset)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
