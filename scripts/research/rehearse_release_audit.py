"""Fabricated acceptance/release rehearsal; mock identities never authorize training."""
import argparse
from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import sys


def sibling(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mock',required=True,action='store_true')
    p.add_argument('--foundry',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args(argv)
    if not a.foundry.is_absolute() or not a.out.is_absolute() or a.out.exists():
        raise ValueError('Use absolute Foundry and a new absolute output directory')
    audit=sibling('audit_openmath')
    review,admission,datasets,contracts=audit.load_foundry(a.foundry,[
        'src.ingestion.synthetic_review','src.ingestion.synthetic_admission','src.ingestion.datasets','src.ingestion.contracts'])
    # Reuse the existing calculation fixture; its original checks remain pending.
    with redirect_stdout(io.StringIO()):
        sibling('rehearse_calculations').main(['--mock','--foundry',str(a.foundry),'--out',str(a.out/'inputs')])
    original=json.loads((a.out/'inputs/ratio.packet.json').read_text())
    documents=json.loads((a.out/'inputs/documents.json').read_text())
    checks=deepcopy(original['checks'])
    for check in checks.values():
        check.update(status='pass',evidence=['FABRICATED SOFTWARE TEST ONLY'],limitation='Not engineering acceptance')
    data=dict(candidate=original['candidate'],normalized_documents=documents,family_history=[],
        recipe=original['recipe'],generation_receipt=original['generation_receipt'],checks=checks)
    packet=review.build_review_packet(**data)
    stamp='2026-09-27T00:00:00Z'
    decision={'status':'approved','reviewer':'independent-fixture@example.invalid','reviewed_at':stamp,
        'packet_sha256':packet['packet_sha256'],'reason':'Fabricated software fixture; no real approval'}
    def accept(pkt,dec,docs,history=(),rehearsal=True):
        return admission.check_acceptance(pkt,dec,actor=dec['reviewer'],normalized_documents=docs,
            family_history=list(history),rehearsal=rehearsal)
    receipt=accept(packet,decision,documents)
    blocked=[]
    for mode in ('self_acceptance','revoked_rights','historical_holdout','edited_candidate','stale_decision','mock_live_acceptance'):
        pkt,dec,docs=deepcopy(packet),deepcopy(decision),deepcopy(documents);history=[]
        if mode=='self_acceptance':dec['reviewer']=pkt['author_id']
        if mode=='revoked_rights':docs[0]['source']['permission']['status']='revoked'
        if mode=='historical_holdout':
            past=deepcopy(pkt['candidate']);past.update(example_id='SYN-OLD-REJECTED',split='locked_test')
            past['review'].update(status='rejected',reviewer='fixture',reviewed_at=stamp);history=[past]
        if mode=='edited_candidate':pkt['candidate']['messages'][-1]['content']='Edited after decision'
        if mode=='stale_decision':dec['packet_sha256']='a'*64
        try:accept(pkt,dec,docs,history,rehearsal=mode!='mock_live_acceptance')
        except ValueError:blocked.append(mode)
        else:raise AssertionError('Expected refusal: '+mode)
    options={'pack_name':'MOCK-ONLY-release-audit','recipe_version':'mock-v1'}
    try:datasets.prepare_release_candidate([original['candidate']],documents,**options)
    except datasets.DatasetError:blocked.append('pending_release')
    else:raise AssertionError('Pending example released')
    # Separate fabricated release decision, not a conversion of real technical review.
    candidate=deepcopy(packet['candidate'])
    candidate['review']={'status':'approved','reviewer':decision['reviewer'],'reviewed_at':stamp,
        'reason':'MOCK ONLY: fabricated builder rehearsal'}
    release=datasets.prepare_release_candidate([candidate],documents,**options)
    approval={'status':'approved','reviewer':'fixture-release@example.invalid','reviewed_at':stamp,
        'candidate_content_hash':release['candidate_content_hash']}
    manifest=datasets.build_release([candidate],documents,a.out/'MOCK-ONLY-release',approval=approval,**options)
    datasets.verify_release(a.out/'MOCK-ONLY-release'/manifest['release_id'])
    changed=deepcopy(candidate);changed['messages'][-1]['content']+=' EDITED'
    try:datasets.build_release([changed],documents,a.out/'stale-must-not-exist',approval=approval,**options)
    except datasets.DatasetError:blocked.append('stale_release_approval')
    else:raise AssertionError('Stale release approval accepted')
    report={'schema':'broadbridge.release_audit_rehearsal/1','training_approved':False,'model_calls':0,
        'blocked':blocked,'mock_release_verified':True,'live_integration_complete':False,
        'acceptance_receipt':receipt,'limitation':'Fabricated identities/rights/checks. Live authenticated review, authoritative complete history and release wiring remain open.'}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
