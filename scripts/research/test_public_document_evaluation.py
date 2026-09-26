import csv
import json
import os
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import public_document_evaluation as evaluate


def sample():
    return evaluate.load_sample(evaluate.SAMPLE)


def test_sample_has_ten_documents_thirty_questions_and_five_types():
    value = sample()
    assert len(value['sources']) == 10
    assert len(value['questions']) == 30
    assert {t: sum(q['type'] == t for q in value['questions']) for t in evaluate.TYPES} == dict.fromkeys(evaluate.TYPES, 6)
    assert all(q['permitted_use'] == 'testing_only' and q['split'] == 'dev' for q in value['questions'])


def test_reference_and_criteria_are_not_transmitted():
    value = sample()
    for q in value['questions']:
        q['reference_answer'] = 'SECRET_REFERENCE_SENTINEL'
        q['hard_fail_criteria'] = 'SECRET_CRITERIA_SENTINEL'
        q['tolerance'] = {'SECRET_TOLERANCE_SENTINEL': True}
    rendered = json.dumps(evaluate.messages_for(value, value['sources'][0]))
    assert 'SECRET_' not in rendered
    assert 'reference_answer' not in rendered
    payload = json.loads(evaluate.messages_for(value, value['sources'][0])[1]['content'])
    assert set(payload) == {'source_id', 'source_title', 'publication_context', 'blocks', 'questions'}
    assert all(set(q) == {'question_id', 'type', 'question'} for q in payload['questions'])


@pytest.mark.parametrize('mutation', ['internal', 'not-permitted', 'training', 'hash', 'url', 'family', 'duplicate', 'source-ref'])
def test_ineligible_or_inconsistent_sample_fails_before_http(mutation):
    value = sample()
    if mutation == 'internal': value['sources'][0]['confidentiality'] = 'internal'
    if mutation == 'not-permitted': value['sources'][0]['rights']['cloud_evaluation_allowed'] = False
    if mutation == 'training': value['questions'][0]['permitted_use'] = 'training'
    if mutation == 'hash': value['sources'][0]['blocks'][0]['text'] += ' changed'
    if mutation == 'url': value['sources'][0]['url'] = 'https://private.example/secret'
    if mutation == 'family': value['questions'][0]['family_id'] = 'wrong-family'
    if mutation == 'duplicate': value['questions'][1]['question_id'] = value['questions'][0]['question_id']
    if mutation == 'source-ref': value['questions'][0]['evidence_ids'] = ['nonexistent']
    with pytest.raises(ValueError): evaluate.validate_sample(value)


@pytest.mark.parametrize('bad', ['invented-quote', 'invented-source', 'duplicate-id', 'missing-answer'])
def test_response_ids_and_exact_quotes_checked(bad):
    value = sample(); source = value['sources'][0]
    response = evaluate.mock_value(value, source)
    if bad == 'invented-quote': response['answers'][0]['evidence'][0]['quote'] = 'not in source'
    if bad == 'invented-source': response['answers'][0]['evidence'][0]['source_id'] = 'not-a-source'
    if bad == 'duplicate-id': response['answers'][1]['question_id'] = response['answers'][0]['question_id']
    if bad == 'missing-answer': response['answers'].pop()
    assert evaluate.check_answers(value, source, response)


def test_mock_creates_sixty_blank_scores_and_no_training_candidates(tmp_path):
    run = tmp_path / 'mock'
    evaluate.run_sample(sample(), run, mode='mock')
    assert len(list(run.glob('scorecard_*.md'))) == 10
    rows = list(csv.DictReader((run/'scores.csv').open(encoding='utf-8', newline='')))
    assert len(rows) == 60
    assert all(not r['score'] and not r['reviewer'] for r in rows)
    result = json.loads((run/'run.json').read_text())
    assert result['calls_attempted'] == 0
    assert result['mode'] == 'mock'
    assert result['training_approved'] is False
    assert 'unreviewed' in (run/'scores_summary.md').read_text()
    assert not list(run.rglob('*candidate*'))


def test_partial_scores_are_not_approval_and_critical_error_cannot_be_averaged(tmp_path):
    run = tmp_path/'review'; evaluate.run_sample(sample(), run, mode='prepare')
    record = json.loads((run/'run.json').read_text())
    record['mode'] = 'live'
    (run/'run.json').write_text(json.dumps(record))
    rows = list(csv.DictReader((run/'scores.csv').open(encoding='utf-8', newline='')))
    rows[0].update(score='0', critical_error='YES', reviewer='test-reviewer', review_date='2026-09-26', notes='Matched criterion')
    evaluate.write_csv(run/'scores.csv', rows)
    result = evaluate.summarize(run)
    assert result['reviewed_responses'] == 1
    assert result['unreviewed_responses'] == 59
    assert result['critical_errors_observed'] == 1
    assert result['training_approved'] is False
    assert result['decision'] == 'HOLD'
    rows[0]['score'] = '2'; evaluate.write_csv(run/'scores.csv', rows)
    with pytest.raises(ValueError, match='critical'): evaluate.summarize(run)


def test_score_identity_changes_and_duplicate_rows_are_rejected(tmp_path):
    run=tmp_path/'review'; evaluate.run_sample(sample(), run, mode='prepare')
    rows=list(csv.DictReader((run/'scores.csv').open(encoding='utf-8', newline='')))
    rows[0]['question_id']='WRONG'; evaluate.write_csv(run/'scores.csv',rows)
    with pytest.raises(ValueError, match='identity'): evaluate.summarize(run)


def test_not_run_slot_cannot_receive_positive_quality_grade(tmp_path):
    run=tmp_path/'review'; evaluate.run_sample(sample(), run, mode='prepare')
    record=json.loads((run/'run.json').read_text()); record['mode']='live'
    (run/'run.json').write_text(json.dumps(record))
    rows=list(csv.DictReader((run/'scores.csv').open(encoding='utf-8', newline='')))
    rows[0].update(score='2',critical_error='NO',reviewer='test',review_date='2026-09-26',notes='test')
    evaluate.write_csv(run/'scores.csv',rows)
    with pytest.raises(ValueError,match='missing/not-run'): evaluate.summarize(run)


def test_live_requires_exact_approval_hash_before_client_creation(tmp_path):
    with pytest.raises(ValueError, match='approval'):
        evaluate.run_sample(sample(), tmp_path/'live', mode='live', approve_hash='wrong')


def test_mock_scores_cannot_establish_model_quality(tmp_path):
    run=tmp_path/'mock'; evaluate.run_sample(sample(), run, mode='mock')
    rows=list(csv.DictReader((run/'scores.csv').open(encoding='utf-8', newline='')))
    rows[0].update(score='2',critical_error='NO',reviewer='someone',review_date='2026-09-26',notes='test')
    evaluate.write_csv(run/'scores.csv',rows)
    with pytest.raises(ValueError,match='live'): evaluate.summarize(run)


def test_runtime_leak_assert_catches_reference_in_prompt():
    value=sample(); source=value['sources'][0]
    messages=evaluate.messages_for(value,source)
    messages[1]['content'] += value['questions'][0]['reference_answer']
    with pytest.raises(ValueError,match='reference'): evaluate.assert_no_reference_leak(value,source,messages)


@pytest.mark.parametrize('failure', [None, 'unknown_cost', 'output_limit'])
def test_live_http_boundary_is_bounded_and_preserves_failures(monkeypatch, tmp_path, failure):
    foundry = os.environ.get('SLM_FOUNDRY_PATH')
    if not foundry: pytest.skip('Set SLM_FOUNDRY_PATH to test the actual shared transport offline')
    sys.path.insert(0, foundry)
    import requests
    monkeypatch.setenv('OPENROUTER_API_KEY','mock-key-not-a-secret')
    value=sample(); calls=[]
    def post(url, **kwargs):
        payload=kwargs['json']; calls.append(payload)
        body=json.loads(payload['messages'][1]['content'])
        source=next(s for s in value['sources'] if s['source_id']==body['source_id'])
        content=evaluate.mock_value(value,source)
        data={'model':payload['model'],'provider':payload['provider']['only'][0],
            'choices':[{'finish_reason':'stop','message':{'content':json.dumps(content)}}],
            'usage':{'cost':0.00001,'prompt_tokens':100,'completion_tokens':60}}
        if len(calls)==1 and failure=='unknown_cost': del data['usage']['cost']
        if len(calls)==1 and failure=='output_limit': data['choices'][0]['finish_reason']='length'
        r=requests.Response(); r.status_code=200; r._content=json.dumps(data).encode(); r._content_consumed=True
        return r
    monkeypatch.setattr(requests,'post',post)
    output=tmp_path/'live-mock-http'
    result=evaluate.run_sample(value,output,mode='live',foundry=Path(foundry),approve_hash=evaluate.digest(value))
    expected={None:20,'unknown_cost':1,'output_limit':11}[failure]
    assert len(calls)==expected
    assert result['calls_attempted']==expected
    assert result['training_approved'] is False
    assert all(p['provider']['enforce_distillable_text'] and not p['provider']['allow_fallbacks'] for p in calls)
    assert all('reference_answer' not in json.dumps(p['messages']) for p in calls)
    assert 'mock-key-not-a-secret' not in (output/'results.json').read_text()
    if failure:
        records=json.loads((output/'results.json').read_text())
        assert records[0]['status']=='transport_failure'
        assert any(r['status']=='stopped_no_retry' for r in records)
    else:
        for i in range(0,20,2): assert calls[i]['messages']==calls[i+1]['messages']
