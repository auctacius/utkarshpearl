"""Fetch pinned public assets only; no user text is sent. Run once before offline inference."""
import hashlib,json,os
from pathlib import Path
import requests
P=Path(__file__).resolve().parents[1]
SPECS=[('urchade/gliner_multi-v2.1','443d26d654e0324125a96bebd8e796c14ff2efe6','gliner',['README.md','gliner_config.json','model.safetensors']),('microsoft/mdeberta-v3-base','a0484667b22365f84929a935b5e50a51f71f159d','encoder',['README.md','config.json','tokenizer_config.json','spm.model'])]
def main():
    manifest=[]
    for repo,revision,folder,files in SPECS:
        dest=P/'data/models'/folder;dest.mkdir(parents=True,exist_ok=True)
        for filename in files:
            target=dest/filename
            if filename=='gliner_config.json':target=dest/'gliner_config.upstream.json'
            url=f'https://huggingface.co/{repo}/resolve/{revision}/{filename}'
            if not target.exists():
                print('Downloading',repo,filename,flush=True)
                with requests.get(url,stream=True,timeout=(30,120)) as response:
                    response.raise_for_status()
                    with target.with_suffix(target.suffix+'.part').open('wb') as out:
                        for chunk in response.iter_content(1024*1024):out.write(chunk)
                target.with_suffix(target.suffix+'.part').replace(target)
            h=hashlib.sha256()
            with target.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
            manifest.append(dict(repo=repo,revision=revision,file=filename,sha256=h.hexdigest(),bytes=target.stat().st_size))
    config=json.loads((P/'data/models/gliner/gliner_config.upstream.json').read_text())
    config['model_name']=str((P/'data/models/encoder').resolve())
    (P/'data/models/gliner/gliner_config.json').write_text(json.dumps(config,indent=2)+'\n')
    (P/'reports/model_assets.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Pinned assets ready; local config points to pinned encoder tokenizer/config.',flush=True)
if __name__=='__main__':main()
