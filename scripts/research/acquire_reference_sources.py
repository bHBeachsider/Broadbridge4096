"""Acquire ONLY the small public files pinned in the reference research receipt.

No credentials, model weights, full archives or client drawings. Hard ceilings:
15 MB per file / 50 MB total, SHA256 checked, no overwrite. Existing exact files
are reused. Never expands archives. Package installation is a separate step.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler

PER_FILE=15_000_000
TOTAL=50_000_000
HOSTS={'gitlab.com','raw.githubusercontent.com','files.pythonhosted.org','zenodo.org'}


class NoRedirect(HTTPRedirectHandler):
    # Default urllib drains a redirect body without a bound before following it.
    # Pinned final URLs only: never read a redirect body or follow another host.
    def http_error_302(self,req,fp,code,msg,headers):
        fp.close()
        raise ValueError('Redirect refused for pinned public source')
    http_error_301=http_error_303=http_error_307=http_error_308=http_error_302


def bounded_open(url,timeout):
    return build_opener(NoRedirect()).open(url,timeout=timeout)


def acquire(receipt,out,opener=bounded_open):
    records=receipt['files']
    if sum(r['bytes'] for r in records)>TOTAL:raise ValueError('Total download limit')
    names=[]
    for r in records:
        name=r['file'];parsed=urlsplit(r['url'])
        if not isinstance(name,str) or Path(name).name!=name or name in names:raise ValueError('Unsafe filename')
        names.append(name)
        if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
            raise ValueError('Unapproved public source URL')
        if not 0<r['bytes']<=PER_FILE:raise ValueError('Per-file download limit')
    out.mkdir(parents=True,exist_ok=True)
    for r in records:
        path=out/r['file']
        if path.exists():data=path.read_bytes()
        else:
            with opener(r['url'],timeout=30) as response:
                size=response.headers.get('Content-Length')
                if size and int(size)>r['bytes']:raise ValueError('Unexpected download size; stopped')
                data=response.read(r['bytes']+1)
        if len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:
            raise ValueError('Source hash/length mismatch: '+r['file'])
        if not path.exists():
            with path.open('xb') as f:f.write(data)
    return {'verified_files':len(records),'bytes':sum(r['bytes'] for r in records),'training_approved':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('receipt',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args();print(json.dumps(acquire(json.loads(a.receipt.read_bytes()),a.out)))


if __name__=='__main__':main()
