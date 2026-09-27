import importlib.util
import json
from pathlib import Path

import pytest

MODULE = Path(__file__).parent / 'vision/prepare.py'


def api():
    assert MODULE.exists(), 'Implement frozen vision-pilot jobs'
    spec = importlib.util.spec_from_file_location('vision_prepare', MODULE)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_manifest_covers_failures_and_models():
    m = api(); refs = m.references()
    assert len(refs) == 7
    assert len({r['family_id'] for r in refs}) == 5
    assert {'crossing','unreadable','direction','basis'} <= {r.get('challenge') for r in refs}
    assert all(r['training_approved'] is False for r in refs)
    assert all(r['review_status'] == 'pending' for r in refs)
    assert set(m.MODELS) == {'granite','qwen'}


def test_job_does_not_leak_reference_answers(tmp_path):
    m = api(); refs = m.references()
    for r in refs: (tmp_path/(r['id']+'.png')).write_bytes(b'image')
    job = m.make_job(tmp_path, refs)
    assert len(job['requests']) == 14
    for req in job['requests']:
        assert 'expected' not in req and 'reference_answer' not in req
        assert req['sha256'] == m.sha(b'image')
        assert len(req['id']) < 80
    assert job['references_sha256'] == m.sha(m.encode(refs))


def test_receipt_does_not_turn_text_matches_into_approval():
    r = api().match_text('P_abs = P_atm + P_gauge', ['P_abs', 'P_atm', 'P_gauge'])
    assert r['found'] == 3 and r['total'] == 3
    assert r['engineering_verified'] is False


def test_missing_response_is_not_a_pass():
    r = api().match_text('', ['P-101'])
    assert r['found'] == 0 and r['total'] == 1


def test_different_unit_or_operator_not_equivalent():
    r = api().match_text('psig; x - y', ['psia','x + y'])
    assert r['found'] == 0


def test_reference_tamper_rejected(tmp_path):
    m = api(); refs=m.references()
    (tmp_path/'references.json').write_bytes(m.encode(refs))
    (tmp_path/'job.json').write_text(json.dumps({'references_sha256':'0'*64}),encoding='utf-8')
    with pytest.raises(ValueError,match='reference'):
        m.verify_references(tmp_path)


def test_missing_runs_stay_in_report_denominator(tmp_path):
    m=api(); refs=m.references()
    for r in refs: (tmp_path/(r['id']+'.png')).write_bytes(b'image')
    (tmp_path/'references.json').write_bytes(m.encode(refs))
    (tmp_path/'job.json').write_bytes(m.encode(m.make_job(tmp_path,refs)))
    out=tmp_path/'results';out.mkdir()
    assert hasattr(m,'build_report'), 'Implement complete-denominator reporting'
    report=m.build_report(tmp_path,out)
    assert len(report['rows'])==14
    assert all(r['status']=='not_run' for r in report['rows'])
    assert report['engineering_verified'] is False


def test_wrong_job_output_rejected(tmp_path):
    m=api(); refs=m.references()
    for r in refs: (tmp_path/(r['id']+'.png')).write_bytes(b'image')
    job=m.make_job(tmp_path,refs)
    (tmp_path/'references.json').write_bytes(m.encode(refs))
    (tmp_path/'job.json').write_bytes(m.encode(job))
    out=tmp_path/'results';out.mkdir()
    (out/(job['requests'][0]['id']+'.json')).write_text(json.dumps({'job_sha256':'0'*64}))
    assert hasattr(m,'build_report'), 'Implement receipt binding'
    with pytest.raises(ValueError,match='job'):
        m.build_report(tmp_path,out)


def test_multiple_runs_keep_full_denominator_and_reject_duplicates(tmp_path):
    m=api();refs=m.references()
    for r in refs: (tmp_path/(r['id']+'.png')).write_bytes(b'image')
    job=m.make_job(tmp_path,refs);raw=m.encode(job)
    (tmp_path/'references.json').write_bytes(m.encode(refs));(tmp_path/'job.json').write_bytes(raw)
    dirs=[tmp_path/'first',tmp_path/'remaining']
    for d in dirs: d.mkdir()
    item=job['requests'][0]
    record={'job_sha256':m.sha(raw),'input_sha256':item['sha256'],'status':'failed','elapsed_seconds':240}
    (dirs[0]/(item['id']+'.json')).write_bytes(m.encode(record))
    report=m.build_report(tmp_path,dirs)
    assert len(report['rows'])==14 and report['rows'][0]['status']=='failed'
    (dirs[1]/(item['id']+'.json')).write_bytes(m.encode(record))
    with pytest.raises(ValueError,match='Duplicate'):
        m.build_report(tmp_path,dirs)


@pytest.mark.parametrize('tamper',['none','bytes','source'])
def test_doe_source_receipt_binding(tmp_path,tamper):
    m=api();files=[]
    for page in (35,36,37):
        for ext in ('png','txt'):
            name=f'page-{page:03}.{ext}';(tmp_path/name).write_bytes(b'original')
            files.append({'path':name,'sha256':m.sha(b'original')})
    receipt={'source_sha256':'3c4ef4ad700cfd64444677404956ec2237bb5e24e31f7e591b1767526ec0b2c9','files':files}
    if tamper=='bytes': (tmp_path/'page-035.png').write_bytes(b'changed')
    if tamper=='source': receipt['source_sha256']='0'*64
    (tmp_path/'receipt.json').write_bytes(m.encode(receipt))
    assert hasattr(m,'read_doe_inputs'), 'Verify source-chain receipt before freezing input'
    if tamper=='none': assert len(m.read_doe_inputs(tmp_path))==6
    else:
        with pytest.raises(ValueError):m.read_doe_inputs(tmp_path)
