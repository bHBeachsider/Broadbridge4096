import hashlib
import importlib.util
import json
from pathlib import Path
import pytest


def module():
    path = Path(__file__).with_name('audit_openmath.py')
    assert path.exists(), 'OpenMath audit not implemented'
    spec = importlib.util.spec_from_file_location('audit_openmath', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    raw = [{'problem': 'Synthetic problem', 'generated_solution': 'Synthetic solution', 'expected_answer': '3'}]
    family = hashlib.sha256(b'synthetic problem').hexdigest()
    bucket = int(family[:8],16)%10
    split = 'train' if bucket<8 else 'val' if bucket==8 else 'test'
    candidate = {'source_row_index':0, 'family_id':family, 'split':split, 'expected_answer':'3',
        'messages':[{'role':'user','content':raw[0]['problem']},{'role':'assistant','content':raw[0]['generated_solution']}]}
    return raw, {s: [candidate] if s==split else [] for s in ('train','val','test')}, []


def test_history_never_invents_split_for_excluded_rows(tmp_path):
    raw,splits,rejected=fixture(tmp_path)
    raw.append(dict(raw[0])); rejected.append({'row_index':1,'reason':'duplicate_normalized_problem'})
    rows=module().audit_inputs(raw,splits,rejected)
    assert len(rows)==2 and rows[1]['historical_splits']==[] and rows[1]['excluded']
    assert len(rows[0]['historical_splits'])==1


@pytest.mark.parametrize('mode',['edited_answer','edited_question','lost_rejection','duplicate_row','wrong_family','wrong_split'])
def test_original_candidate_correspondence_is_enforced(tmp_path,mode):
    raw,splits,rejected=fixture(tmp_path)
    c=next(rows[0] for rows in splits.values() if rows)
    if mode=='edited_answer': c['expected_answer']='99'
    if mode=='edited_question': c['messages'][0]['content']='different'
    if mode=='lost_rejection': raw.append(dict(raw[0]))
    if mode=='duplicate_row': next(rows for rows in splits.values() if rows).append(c)
    if mode=='wrong_family': c['family_id']='a'*64
    if mode=='wrong_split': c['split']='locked_test'
    with pytest.raises(ValueError): module().audit_inputs(raw,splits,rejected)


def test_hash_check_refuses_changed_bytes_and_path_escape(tmp_path):
    p=tmp_path/'a';p.write_bytes(b'original')
    m=module()
    with pytest.raises(ValueError): m.checked_file(tmp_path,'a','0'*64)
    with pytest.raises(ValueError): m.checked_file(tmp_path,'../a','0'*64)
    assert m.checked_file(tmp_path,'a',hashlib.sha256(b'original').hexdigest())==p


def test_independent_counterexamples_do_not_use_dataset_expected_answer():
    findings=module().independent_results()
    # n^3 = 125 (mod 1000) implies n = 5 (mod 40): 125..965, 22 terms.
    assert findings[1]['result']==(125+965)*22//2 and findings[1]['count']==22
    assert findings[599]['witness_1'][4]!=findings[599]['witness_2'][4]
    assert sum(findings[599]['witness_1'])==sum(findings[599]['witness_2'])==80
    # If the question means an integer average after EACH shelf, it contradicts
    # itself: the first seven shelves would total 68, not divisible by seven.
    assert findings[599]['prefix_seven_total']==68
    assert findings[599]['prefix_seven_remainder']==5
    assert findings[1199]['height_squared_from_volume']==400
    assert findings[1199]['height_squared_from_diagonal']==125


def test_wrong_raw_snapshot_cannot_receive_precomputed_spotcheck(tmp_path):
    with pytest.raises(ValueError,match='pinned'):
        module().spot_checks([{'problem':'arbitrary','expected_answer':'45'}]*1200,'0'*64)
