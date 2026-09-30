import importlib.util
import hashlib
import json
from pathlib import Path
import pytest


def module():
    path=Path(__file__).with_name('prepare_first_dataset_review.py')
    spec=importlib.util.spec_from_file_location('first_review',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def test_draft_never_confers_acceptance_or_splits_a_family():
    m=module();p=m.build_proposal('a'*64)
    assert p['training_approved'] is False and p['status']=='pending_independent_review'
    assert p['split'] is None and p['family_id']=='DOE-HDBK-1012'
    assert len(p['questions'])==15 and len(p['exception_proposals'])==9
    assert {q['type'] for q in p['questions']}=={'brief','missing_data','calculation','grounded_explanation','abstention'}
    assert all(q['review']['reviewer'] is None and q['review']['status']=='pending' for q in p['questions'])
    assert all(q['family_id']==p['family_id'] and q['split'] is None for q in p['questions'])
    assert p['gate_0_case_questions_added']==0
    assert p['rights_review']['status']=='pending'
    assert 'hydrostatic' in ' '.join(p['excluded_scope']).lower()


@pytest.mark.parametrize('mode,atm,value,expected',[('gauge','14.2','36.8','51.0'),('gauge','14.5','-2.1','12.4'),('vacuum','14.7','5.0','9.7')])
def test_calculation_answers_recomputed_without_a_model(mode,atm,value,expected):
    assert module().pressure_result(mode,atm,value)==expected


@pytest.mark.parametrize('mode,atm,value',[('gauge','unknown','1'),('vacuum','14.7','-1'),('gauge','0','1'),('gauge','14.7','-20'),('other','14.7','1'),('gauge','NaN','1')])
def test_missing_or_inconsistent_calculation_inputs_rejected(mode,atm,value):
    with pytest.raises(ValueError):module().pressure_result(mode,atm,value)


def test_reference_answer_and_critical_errors_stay_out_of_prompt():
    m=module();p=m.build_proposal('b'*64)
    for q in p['questions']:
        message=m.question_prompt(q)
        assert set(message)=={'question_id','question','source_id','evidence_ids'}
        assert 'reference_answer' not in json.dumps(message)
        assert 'hard_fail_criteria' not in json.dumps(message)


def test_all_math_is_illustrative_and_tolerance_not_sensor_accuracy():
    p=module().build_proposal('c'*64)
    for q in p['questions']:
        if q['type']=='calculation':
            assert 'Illustrative' in q['question']
            assert q['calculation']['unit']=='psia'
            assert 'not instrument accuracy' in q['tolerance']


def test_existing_output_preserved_before_input_read(tmp_path):
    out=tmp_path/'existing';out.mkdir();(out/'keep').write_text('keep')
    with pytest.raises(ValueError,match='new absolute'):
        module().main(['--packet-dir',str(tmp_path/'missing'),'--out',str(out)])
    assert (out/'keep').read_text()=='keep'


def test_modified_extraction_receipt_is_not_accepted(tmp_path):
    packet=tmp_path/'packet';packet.mkdir()
    (packet/'packet.json').write_text('{}')
    (packet/'receipt.json').write_text(json.dumps({'schema':'broadbridge.doe_extraction_receipt/1','source_sha256':'wrong','files':[]}))
    with pytest.raises(ValueError):module().verify_extraction(packet)


@pytest.fixture
def extraction(tmp_path):
    """Fabricated extraction envelope to test integrity, not PDF accuracy."""
    m = module()
    root = tmp_path / 'extraction'
    root.mkdir()
    packet = {'schema': 'broadbridge.source_review_packet/1',
              'source': {'sha256': m.SOURCE_SHA, 'family_id': m.FAMILY},
              'pages': [{'pdf_page': p} for p in m.PAGES],
              'training_approved': False}
    (root / 'packet.json').write_text(json.dumps(packet), encoding='utf-8')
    for name in ['REVIEW.md', 'review.csv'] + [
        f'page-{n:03}{suffix}' for n in m.PAGES for suffix in ('.png', '.txt', '.layout.txt')
    ]:
        (root / name).write_bytes(b'fabricated test fixture')
    receipt = {'schema': 'broadbridge.doe_extraction_receipt/1',
               'source_sha256': m.SOURCE_SHA, 'pdf_pages': m.PAGES,
               'training_approved': False, 'model_calls': 0,
               'files': [{'path': p.name, 'bytes': p.stat().st_size,
                          'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                         for p in sorted(root.iterdir())]}
    (root / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
    return root


def test_builder_writes_review_only_outputs_and_verifiable_receipt(extraction, tmp_path):
    m = module()
    out = tmp_path / 'review'
    assert m.main(['--packet-dir', str(extraction), '--out', str(out)]) == 0
    assert {p.name for p in out.iterdir()} == {'proposal.json', 'REVIEW.md', 'review.csv', 'receipt.json'}
    assert all(b'\r' not in p.read_bytes() for p in out.iterdir())
    receipt = json.loads((out / 'receipt.json').read_text())
    assert receipt['training_examples_admitted'] == receipt['model_calls'] == 0
    for row in receipt['files']:
        assert m.digest(out / row['path']) == row['sha256']
        assert (out / row['path']).stat().st_size == row['bytes']
    import csv
    with (out / 'review.csv').open(newline='') as stream:
        reviews = list(csv.DictReader(stream))
    assert len(reviews) == 27
    assert all(not r['reviewer'] and not r['disposition'] for r in reviews)


@pytest.mark.parametrize('name', ['page-036.png', 'packet.json', 'review.csv'])
def test_changed_evidence_or_review_not_reused(extraction, name):
    (extraction / name).write_text('changed')
    with pytest.raises(ValueError, match='changed'):
        module().verify_extraction(extraction)


@pytest.mark.parametrize('replacement', ['../outside.txt', 'packet.json', 'C:/outside.txt'])
def test_receipt_paths_cannot_escape_or_repeat(extraction, replacement):
    path = extraction / 'receipt.json'
    receipt = json.loads(path.read_text())
    row = next(row for row in receipt['files'] if row['path'] == 'page-035.txt')
    row['path'] = replacement
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match='Missing, repeated or unexpected'):
        module().verify_extraction(extraction)


def test_bad_evidence_creates_no_output(extraction, tmp_path):
    (extraction / 'page-035.txt').unlink()
    out = tmp_path / 'review'
    with pytest.raises(ValueError):
        module().main(['--packet-dir', str(extraction), '--out', str(out)])
    assert not out.exists()
