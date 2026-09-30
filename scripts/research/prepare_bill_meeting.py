"""Validate the pending DOE package and create a local meeting review bundle.

No network, credentials, model runtime, admission, host start or execution path.
The resulting request describes the proposed run; it is never authorization.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from prepare_pressure_demo import FAMILY, SOURCE, SOURCE_SHA, PACKET_SHA, REVISION

ROOT = Path(__file__).resolve().parents[2]
LIMITS = dict(optimizer_steps=20, training_wall_seconds=1800, host_wall_seconds=5400,
              guest_stop_minute=80, api_stop_minute=85, force_stop_by_minute=87,
              verify_stopped_by_minute=90, comparison_model_calls_max=16,
              max_new_tokens_per_call=384, comparison_phase_seconds_max=900)
ARTIFACTS = {'train_candidates.jsonl', 'demo_prompts.jsonl', 'demo_answer_key.jsonl',
             'response.schema.json', 'proposed_config.json', 'scorecard.md'}
GATES = [
    {'id': 'source_use', 'owner': 'Brad', 'status': 'pending',
     'required': 'Recorded basis permitting internal training on the exact source pages; rights remain TBD.'},
    {'id': 'family_allocation', 'owner': 'Brad', 'status': 'pending',
     'required': 'Approve whole DOE-HDBK-1012 family allocation to demonstration training; retire its independent-test eligibility.'},
    {'id': 'release', 'owner': 'Appointed reviewer and Brad', 'status': 'pending',
     'required': 'Accept exact conversations through admission and create the immutable Foundry dataset release.'},
    {'id': 'host_packet', 'owner': 'Foundry engineering', 'status': 'pending',
     'required': 'Integrate and rehearse the training-capable lifecycle payload against that release. The current host controller is load-only.'},
    {'id': 'execution', 'owner': 'Brad', 'status': 'pending',
     'required': 'Approve the release/config/code/host-packet hashes and one fresh bounded A10G session.'},
]


def require(value, reason):
    if not value:
        raise ValueError(reason)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    raw = Path(path).read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def validate(package):
    package = Path(package)
    m = read_json(package / 'manifest.json')
    require(m['schema'] == 'broadbridge.pressure_demo_preparation/1', 'Unknown preparation contract')
    require(m['status'] == 'prepared_not_released' and m['rights_status'] == 'TBD', 'Pending review package required')
    require(m['training_approved'] is False and m['execution_authorized'] is False
            and m['actual_bill_signoff'] is None and m['model_calls'] == m['optimizer_steps'] == 0,
            'A meeting bundle cannot assert permission, sign-off or observed execution')
    require(m['proposed_limits'] == LIMITS, 'Bounded run limits differ')
    require(m['source']['source_id'] == SOURCE and m['source']['family_id'] == FAMILY
            and m['source']['sha256'] == SOURCE_SHA and m['source']['extraction_sha256'] == PACKET_SHA
            and m['source']['pdf_pages'] == [35, 36, 37],
            'Source binding differs')
    require(m['family_transition']['status'] == 'proposed_not_applied', 'Family allocation must stay pending')
    require(m['comparison']['thinking'] is False and m['comparison']['do_sample'] is False
            and m['comparison']['max_new_tokens'] == 384, 'Comparison settings differ')
    require(set(m['artifacts']) == ARTIFACTS, 'Unexpected or missing package artifact')
    for name, expected in m['artifacts'].items():
        path = package / name
        require(not path.is_symlink() and path.is_file(), 'Missing or linked artifact')
        require(digest(path) == expected, 'Artifact hash/bytes differ: ' + name)
    def lines(name):
        return [json.loads(line) for line in (package / name).read_text(encoding='utf-8').splitlines()]
    rows, probes, keys = map(lines, ['train_candidates.jsonl', 'demo_prompts.jsonl', 'demo_answer_key.jsonl'])
    require(len(rows) == 36 and len({r['example_id'] for r in rows}) == 36, 'Candidate inventory differs')
    require(Counter(r['type'] for r in rows) == dict(calculation=24, brief=3, missing_data=3,
            grounded_explanation=3, abstention=3), 'Candidate task coverage differs')
    response = Draft202012Validator(read_json(package / 'response.schema.json'))
    for r in rows:
        require(r['family_id'] == FAMILY and r['source_sha256'] == SOURCE_SHA
                and r['source_id'] == SOURCE and r['split'] is None and r['proposed_split'] == 'train'
                and r['training_approved'] is False and r['rights_status'] == 'TBD'
                and r['permission_status'] == 'pending', 'Candidate admission or provenance changed')
        require([x['role'] for x in r['messages']] == ['system', 'user', 'assistant'], 'Candidate message roles differ')
        target = json.loads(r['messages'][-1]['content'])
        response.validate(target)
        require(all(x in r['messages'][1]['content'] for x in target['source_ids']), 'Unsupported source citation')
    require(len(probes) == len(keys) == 8 and len({p['question_id'] for p in probes}) == 8
            and len({k['question_id'] for k in keys}) == 8
            and {p['question_id'] for p in probes} == {k['question_id'] for k in keys}, 'Probe question inventory differs')
    answers = {k['question_id']: k['reference_answer'] for k in keys}
    for p in probes:
        require(set(p) == {'question_id', 'type', 'family_id', 'independent_test', 'usage', 'messages'}, 'Unexpected prompt fields')
        require(p['family_id'] == FAMILY and p['independent_test'] is False, 'Probe independence claim is invalid')
        require([x['role'] for x in p['messages']] == ['system', 'user'], 'Answer leaked into prompt')
        require(answers[p['question_id']] not in json.dumps(p), 'Reference answer leaked into prompt')
    require(m['counts'] == dict(train_candidates=36, demo_probes=8, independent_validation=0,
                               independent_test=0), 'Reported counts differ')
    config = read_json(package / 'proposed_config.json')
    require(config['model'] == dict(base='unsloth/Qwen3-8B', revision=REVISION,
            chat_template='qwen-2.5', max_seq_length=2048, load_in_4bit=True), 'Proposed checkpoint or rendering differs')
    require(config['train']['max_steps'] == 20 and config['train']['evaluate'] is False
            and config['train']['per_device_batch_size'] == 1 and config['train']['grad_accum'] == 8,
            'Training budget or evaluation differs')
    return m


def prepare(package, out):
    package, out = Path(package).resolve(), Path(out).absolute()
    require(not out.exists(), 'Use a fresh meeting directory; preserve earlier notes')
    m = validate(package)
    request = {'schema': 'broadbridge.pressure_demo_execution_request/1', 'status': 'proposal_not_authorization',
        'approved_by': None, 'approved_at': None, 'release_id': None, 'host_packet_sha256': None,
        'execution_authorized': False, 'candidate_manifest': digest(package / 'manifest.json'),
        'candidate_artifacts': m['artifacts'], 'source': m['source'],
        'family_allocation': m['family_transition'], 'limits': LIMITS, 'work_cutoff_minute': 78,
        'base': 'unsloth/Qwen3-8B', 'revision': REVISION,
        'host': {'instance_id': 'i-079b24e2b51ef7630', 'region': 'us-east-1', 'profile': 'g5-a10g'},
        'comparison': m['comparison'], 'independent_test_count': 0,
        'success_evidence': ['Actual 20 optimizer steps and finite loss', 'Verified adapter and intermediate checkpoint state',
            'All eight base/adapter answer pairs including failures', 'Reviewer scores and critical errors',
            'Final stopped-state evidence; no automatic rerun'],
        'open_gates': GATES,
        'notice': 'Not accepted by the Foundry training or EC2 controller. No Bill signature is inferred.'}
    result = {'schema': 'broadbridge.bill_meeting_preparation/1', 'status': 'review_ready_execution_blocked',
        'candidate_count': 36, 'probe_count': 8, 'execution_authorized': False,
        'model_calls_observed': 0, 'optimizer_steps_observed': 0, 'open_gates': GATES,
        'candidate_manifest': digest(package / 'manifest.json'),
        'voice': {'local_interviewer': 'observed running and healthy on 2026-09-30',
                  'website_recording': 'not implemented', 'meet_integration': 'not implemented'},
        'demo': 'Deterministic interactive reference walkthrough, not model inference'}
    template = ROOT / 'docs/demos/bill-pressure-walkthrough.html'
    require(template.is_file(), 'Meeting walkthrough missing')
    out.mkdir(parents=True)
    (out / 'index.html').write_bytes(template.read_bytes())
    for name, content in [('execution-request.json', request), ('readiness.json', result)]:
        (out / name).write_text(json.dumps(content, indent=2)+'\n', encoding='utf-8', newline='\n')
    meeting = (ROOT / 'docs/BILL_MEETING_RUNBOOK.md').read_text(encoding='utf-8')
    meeting = meeting.replace('(demos/bill-pressure-walkthrough.html)', '(index.html)')
    for name in ['DOE_TRAINING_DEMO_PACKAGE.md', 'AWS_CACHED_TRAINING_PREPARATION.md']:
        meeting = meeting.replace('(' + name + ')', '(' + (ROOT / 'docs' / name).as_posix() + ')')
    receipt = 'evidence/bill-meeting-2026-09-30/voice-smoke.json'
    meeting = meeting.replace('(' + receipt + ')', '(' + (ROOT / 'docs' / receipt).as_posix() + ')')
    (out / 'MEETING.md').write_text(meeting, encoding='utf-8', newline='\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.package, args.out)))


if __name__ == '__main__':
    main()
