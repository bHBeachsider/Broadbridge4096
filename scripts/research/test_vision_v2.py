import importlib.util
import json
from pathlib import Path
import pytest

def api():
    path=Path(__file__).parent/'vision/prepare_v2.py'
    assert path.exists(), 'Implement frozen v2 development protocol'
    spec=importlib.util.spec_from_file_location('prepare_v2',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def setup(root):
    m=api()
    for name in m.IMAGES: (root/name).write_bytes(b'image')
    refs=m.references(root)
    job=m.make_job(root,refs)
    (root/'references.json').write_bytes(m.encode(refs))
    (root/'job.json').write_bytes(m.encode(job))
    return m,refs,job

def test_nine_requests_separate_tasks_no_reference_answers(tmp_path):
    m,refs,job=setup(tmp_path)
    assert len(job['requests'])==9
    assert len({r['id'] for r in job['requests']})==9
    for r in job['requests']:
        assert set(r)=={'id','model','image','sha256','structured','profile','prompt'}
        assert 'A-101' not in r['prompt'] and 'expected_edges' not in r['prompt']
    assert job['references_sha256']==m.sha(m.encode(refs))
    assert all(not r['training_approved'] for r in refs.values())

def test_reference_geometry_keeps_crossing_separate(tmp_path):
    _,refs,_=setup(tmp_path)
    graph=refs['syn-crossing.png']['graph']
    pairs={frozenset((e['a'],e['b'])) for e in graph['edges']}
    assert len(pairs)==5
    assert frozenset(('A-101','C-101')) not in pairs
    assert frozenset(('G-201','J-201')) in pairs
    assert refs['syn-basis.png']['graph']['edges']==[]

def test_reference_tamper_fails(tmp_path):
    m,_,_=setup(tmp_path)
    (tmp_path/'references.json').write_text('{}')
    with pytest.raises(ValueError,match='reference'):m.report(tmp_path,[],None)

def test_missing_outputs_stay_in_denominator(tmp_path):
    m,_,_=setup(tmp_path)
    report=m.report(tmp_path,[],None)
    assert len(report['rows'])==9 and all(r['status']=='not_run' for r in report['rows'])
    assert report['training_approved'] is False

@pytest.mark.parametrize('tamper',['job','image','prompt','profile','model','id'])
def test_result_must_match_frozen_request(tmp_path,tamper):
    m,_,job=setup(tmp_path);q=job['requests'][0]
    r={'job_sha256':m.sha(m.encode(job)),'input_sha256':q['sha256'],
       'prompt_sha256':m.sha(q['prompt'].encode()),'profile':q['profile'],
       'id':q['id'],'model':q['model'],'status':'failed','elapsed_seconds':1}
    key={'job':'job_sha256','image':'input_sha256','prompt':'prompt_sha256'}.get(tamper,tamper)
    r[key]='changed'
    out=tmp_path/'result';out.mkdir();(out/(q['id']+'.json')).write_bytes(m.encode(r))
    with pytest.raises(ValueError,match='binding'):m.report(tmp_path,[out],None)

def test_image_mutation_rejected(tmp_path):
    m,_,_=setup(tmp_path)
    (tmp_path/'syn-crossing.png').write_bytes(b'changed')
    with pytest.raises(ValueError,match='image'):m.report(tmp_path,[],None)
