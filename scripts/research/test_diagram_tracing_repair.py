import importlib.util
import json
import os
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('diagram_tracing_repair.py')
    assert path.exists(), 'Repair replay not implemented'
    spec=importlib.util.spec_from_file_location('diagram_tracing_repair',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    foundry=os.environ.get('FOUNDRY_REPO')
    if not foundry:pytest.skip('Select FOUNDRY_REPO')
    m=module();modules=m.load(Path(foundry));out=tmp_path/'pilot'
    m.prepare(out,modules)
    return m,modules,out


def test_preparation_preserves_six_images_and_never_sends_references(prepared):
    m,mods,out=prepared
    job=json.loads((out/'job.json').read_bytes());evaluation=json.loads((out/'evaluation.json').read_bytes())
    assert len(job['requests'])==12 and len(evaluation['drawings'])==6
    assert all(q['profile'] in ('connections_v3','arrows_v3') for q in job['requests'])
    assert 'reference' not in job and 'edges' not in job
    for q in job['requests']:
        assert m.sha((out/q['image']).read_bytes())==q['sha256']
        assert set(q)=={'id','image','sha256','model','structured','profile','prompt'}
    with pytest.raises(FileExistsError):m.prepare(out,mods)


def test_no_results_are_never_scored_as_success(prepared):
    m,mods,out=prepared;r=m.report(out,out/'missing',mods)
    assert len(r['rows'])==6 and all(x['check']['status']=='fail' for x in r['rows'])
    assert r['totals']['edge_tp']==0 and r['totals']['edge_fn']==14
    assert r['training_approved'] is False


def fabricate(prepared):
    m,mods,out=prepared
    jobraw=(out/'job.json').read_bytes();job=json.loads(jobraw)
    result=out/'mock';result.mkdir()
    for q in job['requests']:
        obj={'connections':[],'uncertain':False} if q['profile']=='connections_v3' else {'arrows':[],'uncertain':False}
        r={'id':q['id'],'status':'completed','profile':q['profile'],'model':q['model'],
            'model_digest':mods['pins'][q['model']],'job_sha256':m.sha(jobraw),'input_sha256':q['sha256'],
            'prompt_sha256':m.sha(q['prompt'].encode()),'proposal':obj,'elapsed_seconds':1}
        (result/(q['id']+'.json')).write_text(json.dumps(r),encoding='utf-8')
    return result


def test_wrong_bound_receipt_fails_loudly(prepared):
    m,mods,out=prepared;r=fabricate(prepared)
    p=next(r.glob('*.json'));d=json.loads(p.read_bytes());d['prompt_sha256']='a'*64;p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='binding'):m.report(out,r,mods)


def test_missing_or_changed_image_not_ignored(prepared):
    m,mods,out=prepared
    next(out.glob('*.png')).write_bytes(b'changed')
    with pytest.raises(ValueError,match='Image'):m.report(out,out/'missing',mods)


def test_crop_followup_preserves_lineage_and_original_v2_prompt(tmp_path):
    from PIL import Image
    m=module();out=tmp_path/'crops';r=m.prepare_crops(out)
    assert r['images']==4 and r['requests']==4
    job=json.loads((out/'job.json').read_bytes());lineage=json.loads((out/'crop-lineage.json').read_bytes())
    assert all(q['profile']=='connectivity_v2' for q in job['requests'])
    for q in job['requests']:
        record=lineage[q['id']]
        assert m.sha((out/q['image']).read_bytes())==q['sha256']==record['image_sha256']
        x0,y0,x1,y1=record['box'];assert Image.open(out/q['image']).size==((x1-x0)*2,(y1-y0)*2)
        assert q['prompt']==record['parent_prompt']
    with pytest.raises(FileExistsError):m.prepare_crops(out)


@pytest.mark.parametrize('field',['reference','baseline'])
def test_evaluation_edit_cannot_rewrite_gold_or_baseline(prepared,field):
    m,mods,out=prepared;r=fabricate(prepared)
    p=out/'evaluation.json';d=json.loads(p.read_bytes())
    for row in d['drawings']:
        if field=='reference':
            row['reference']['edges']=[]
            row['reference_sha256']=mods['visual_connectivity'].digest(row['reference'])
        else:row['baseline_proposal']['edges']=[]
    p.write_text(json.dumps(d),encoding='utf-8')
    with pytest.raises(ValueError,match='Evaluation'):m.report(out,r,mods)


def test_crop_report_rejects_wrong_model_digest(prepared,tmp_path):
    m,mods,_=prepared;out=tmp_path/'crop';m.prepare_crops(out)
    raw=(out/'job.json').read_bytes();q=json.loads(raw)['requests'][0]
    results=out/'results';results.mkdir()
    r={'id':q['id'],'job_sha256':m.sha(raw),'input_sha256':q['sha256'],
       'prompt_sha256':m.sha(q['prompt'].encode()),'profile':q['profile'],'model':q['model'],
       'model_digest':'0'*64,'status':'completed','elapsed_seconds':1,
       'proposal':{'edges':[],'uncertain':True}}
    (results/(q['id']+'.json')).write_text(json.dumps(r),encoding='utf-8')
    with pytest.raises(ValueError,match='model digest'):m.report_crops(out,results,mods)


def test_legacy_run_requires_explicit_pin_and_discloses_limitation(prepared):
    m,mods,out=prepared
    path=out/'job.json';job=json.loads(path.read_bytes());del job['evaluation_sha256']
    path.write_text(json.dumps(job),encoding='utf-8')
    ep=out/'evaluation.json';e=json.loads(ep.read_bytes());e['job_sha256']=m.sha(path.read_bytes())
    ep.write_text(json.dumps(e),encoding='utf-8');pin=m.sha(ep.read_bytes())
    with pytest.raises(ValueError,match='Evaluation'):m.report(out,out/'missing',mods)
    r=m.report(out,out/'missing',mods,legacy_evaluation_sha256=pin)
    assert 'retrospective' in r['evaluation_binding'] and r['totals']['edge_fn']==14
    with pytest.raises(ValueError,match='Evaluation'):
        m.report(out,out/'missing',mods,legacy_evaluation_sha256='0'*64)
