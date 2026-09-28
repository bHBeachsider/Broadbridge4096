import importlib.util
from pathlib import Path
import pytest
import json


def module():
    path=Path(__file__).with_name('deterministic_diagrams.py')
    assert path.exists(),'Deterministic stress harness missing'
    spec=importlib.util.spec_from_file_location('dd',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_stress_design_is_bounded_and_has_each_failure_type():
    specs=module().specs()
    assert len(specs)==12 and len({s['id'] for s in specs})==12
    assert {s['category'] for s in specs}>={'crossing','hop','tee','no_arrow','reverse','rotated','small_arrow','break'}
    assert all(s['seed']>=2000 and s['training_approved'] is False for s in specs)


def test_original_retrospective_run_is_excluded():
    r=module().historical_disposition()
    assert r['provenance']=='retrospective-checksum' and r['gate_eligible'] is False
    assert 'crop-history metadata pinned' in r['required_before_unblocking']


def test_freeze_rejects_changed_asset_or_manifest(tmp_path):
    m=module();(tmp_path/'x.png').write_bytes(b'original')
    m.write(tmp_path/'manifest.json',{'assets':{'x.png':m.sha(b'original')}})
    m.write(tmp_path/'job.json',{'manifest_sha256':m.sha((tmp_path/'manifest.json').read_bytes())})
    assert m.verify(tmp_path)
    (tmp_path/'x.png').write_bytes(b'changed')
    with pytest.raises(ValueError,match='asset'):m.verify(tmp_path)
    (tmp_path/'manifest.json').write_text('{}')
    with pytest.raises(ValueError,match='Manifest'):m.verify(tmp_path)


def test_metrics_count_reversal_unsupported_and_missing_separately():
    m=module()
    ref=[{'a':'A','b':'B','direction':'a_to_b'},{'a':'B','b':'C','direction':'unknown'}]
    actual=[{'a':'A','b':'B','direction':'b_to_a'},{'a':'B','b':'C','direction':'a_to_b'}]
    r=m.metrics(ref,actual,'crossing')
    assert r['direction_reversals']==1 and r['unsupported_directions']==1
    assert r['known_directions']==1 and r['direction_claims']==2
    missing=m.metrics(ref,[],'crossing')
    assert missing['edge_fn']==2 and missing['direction_correct']==0
    assert missing['known_direction_missing']==1
    unknown=m.metrics(ref,[{'a':'A','b':'B','direction':'unknown'}],'crossing')
    assert unknown['known_direction_unknown']==1 and unknown['known_direction_claims']==0


def test_false_cross_edges_not_hidden_by_recovered_true_edges():
    m=module();ref=[{'a':'A','b':'B','direction':'unknown'}]
    r=m.metrics(ref,ref+[{'a':'A','b':'C','direction':'unknown'}],'hop')
    assert r['false_edges_at_crossings']==1 and r['edge_tp']==1 and r['edge_fp']==1

def test_rejected_geometry_is_counted_in_raw_metrics_not_hidden():
    m=module()
    ref=[{'a':'A','b':'B','direction':'unknown'}]
    actual=ref+[{'a':'A','b':'C','direction':'a_to_b'}]
    row=m.score_prediction(ref,actual,'crossing',{'status':'fail'})
    assert row['metrics']['edge_fp']==1
    assert row['metrics']['unsupported_directions']==1
    assert row['accepted_metrics']['edge_fn']==1
    assert row['accepted_metrics']['edge_tp']==0


def test_missing_result_counts_all_reference_edges_as_missed():
    m=module();ref=[{'a':'A','b':'B','direction':'a_to_b'}]
    row=m.score_prediction(ref,[],'forward',None)
    assert row['metrics']['edge_fn']==1 and row['metrics']['known_directions']==1
    assert row['metrics']['direction_correct']==0


def test_unbacked_direction_is_reported_even_if_it_matches_reference():
    m=module();edge={'a':'A','b':'B','direction':'a_to_b'}
    r=m.evidence_metrics([edge],None)
    assert r=={'direction_claims':1,'unbacked_directions':1,'unbacked_direction_rate':1.0}


@pytest.fixture
def experiment(tmp_path,monkeypatch):
    import os,shutil
    if not os.environ.get('FOUNDRY_REPO'):pytest.skip('Matching Foundry checkout not configured')
    monkeypatch.syspath_prepend(os.environ['FOUNDRY_REPO'])
    source=Path(__file__).parents[2]/'docs/evidence/deterministic-diagrams-2026-09-27'
    dest=tmp_path/'experiment';shutil.copytree(source,dest,ignore=shutil.ignore_patterns('runtime.json'))
    return dest,Path(os.environ['FOUNDRY_REPO'])


def test_archived_results_replay_exactly(experiment):
    root,repo=experiment;m=module()
    result=m.report(root/'inputs',root/'detected-v2',root/'inputs/baseline-v2',repo)
    expected=json.loads((root/'results-final.json').read_bytes())
    assert result==expected
    assert result['gate_eligible'] is False and result['training_approved'] is False
    assert result['summary']['dxf']['edge_fp']==7
    assert result['summary']['png']['known_direction_missing']==6
    assert result['arrow_evidence_summary']['baseline']['unbacked_directions']==6


@pytest.mark.parametrize('kind',['baseline','detector'])
def test_changed_receipt_fails_replay(experiment,kind):
    root,repo=experiment
    path=root/('inputs/baseline-v2/forward.json' if kind=='baseline' else 'detected-v2/forward.pdf.json')
    record=json.loads(path.read_bytes());record['input_sha256']='0'*64
    path.write_text(json.dumps(record),encoding='utf-8')
    with pytest.raises(ValueError,match='binding|changed'):
        module().report(root/'inputs',root/'detected-v2',root/'inputs/baseline-v2',repo)
