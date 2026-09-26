"""Check selected excerpts against original public HTML, without a model or DB.

Default requires an existing local cache. --fetch downloads only the fixed ten
allowlisted agency URLs into a new cache. Changing source content never silently
changes the sample; a drift report requires a new reviewed sample version.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import requests

from public_document_evaluation import SAMPLE, load_sample


def verify(sample, cache, fetch=False):
    if fetch: cache.mkdir(parents=True, exist_ok=False)
    rows=[]
    for source in sample['sources']:
        target=cache/(source['source_id']+'.html')
        if fetch:
            with requests.get(source['url'], timeout=45, allow_redirects=False, stream=True) as r:
                r.raise_for_status()
                if r.status_code != 200: raise ValueError('Source redirect requires review')
                chunks=[]; size=0
                for chunk in r.iter_content(8192):
                    size += len(chunk)
                    if size > 2_000_000: raise ValueError('Public source download too large')
                    chunks.append(chunk)
            target.write_bytes(b''.join(chunks))
        raw=target.read_bytes()
        soup=BeautifulSoup(raw,'html.parser')
        for tag in soup(['script','style','nav','header','footer']): tag.decompose()
        visible=re.sub(r'\s+', ' ', soup.get_text(' ',strip=True)).strip()
        exact_hash=hashlib.sha256(raw).hexdigest()==source['raw_sha256']
        normalized_hash=hashlib.sha256(visible.encode()).hexdigest()==source['normalized_sha256']
        present=all(b['text'] in visible for b in source['blocks'])
        locations=all(visible[b['location']['start']:b['location']['end']]==b['text'] for b in source['blocks'])
        rows.append({'source_id':source['source_id'],'raw_hash_matches':exact_hash,
            'normalized_hash_matches':normalized_hash,'all_excerpts_exact':present,
            'all_locations_match':locations,'blocks':len(source['blocks'])})
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True); p.add_argument('--fetch',action='store_true')
    p.add_argument('--report',type=Path,required=True); args=p.parse_args()
    if args.report.exists(): p.error('--report must be new; preserve earlier evidence')
    rows=verify(load_sample(SAMPLE),args.cache,args.fetch)
    args.report.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    for row in rows:
        print(row['source_id'], 'exact excerpts' if row['all_excerpts_exact'] else 'EXCERPT DRIFT',
              'same source snapshot' if row['raw_hash_matches'] else 'SOURCE SNAPSHOT CHANGED')
    if not all(all(r[k] for k in ('raw_hash_matches','normalized_hash_matches','all_excerpts_exact','all_locations_match')) for r in rows):
        raise SystemExit('Source drift; review the report before using a new source version.')


if __name__=='__main__': main()
