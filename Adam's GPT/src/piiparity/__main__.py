import argparse,json,sys
from .core import infer
from .evaluate import evaluate

def main():
    p=argparse.ArgumentParser(description='PIIParity local research baseline')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('redact',help='Read UTF-8 text from stdin; emit redacted JSON')
    e=sub.add_parser('evaluate');e.add_argument('dataset')
    args=p.parse_args()
    result=infer(sys.stdin.read()) if args.command=='redact' else evaluate(args.dataset)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
