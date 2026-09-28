"""Compare proposed direct edges to an independently supplied reference graph.

No image inference or training approval occurs here. Reference authorship and
review identity must be established by the caller's trusted review system, not
by copying these fields from a model. Hashes bind evidence; they do not prove it.
"""
import hashlib
import json
import re
from .local_vision import validate_profile


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,
                                    separators=(',',':'),allow_nan=False).encode()).hexdigest()


def edge_map(edges):
    result={}
    for e in edges:
        a,b=e['a'],e['b']; direction=e['direction']
        if a>b:
            a,b=b,a
            direction={'unknown':'unknown','a_to_b':'b_to_a','b_to_a':'a_to_b'}[direction]
        result[(a,b)]=direction
    return result


def check_connectivity(record, reference, *, expected_reference_sha256, trace_signoff=None):
    """Fail closed on incomplete/invalid output, source mismatch or graph errors.

    A human trace requires a bound independent sign-off supplied by a trusted
    review system. A name alone is insufficient. A pass is not training approval.
    """
    report={'schema':'foundry.connectivity_check/1','status':'fail',
            'training_approved':False,'review_status':'pending',
            'missing_edges':[],'unexpected_edges':[],'direction_errors':[]}
    if reference is None:
        return {**report,'status':'needs_review','reason':'No independent reference graph'}
    try:
        if not isinstance(record,dict): raise ValueError('Invalid connectivity record')
        report['reference_sha256']=digest(reference)
        if not expected_reference_sha256 or report['reference_sha256']!=expected_reference_sha256:
            raise ValueError('Reference hash mismatch')
        fields={'schema','image_sha256','origin','evidence_id','reviewer','nodes','edges'}
        if not isinstance(reference,dict) or set(reference)!=fields:
            raise ValueError('Invalid reference contract')
        if reference['schema']!='foundry.connectivity_reference/1': raise ValueError('Invalid reference schema')
        if not isinstance(reference['image_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',reference['image_sha256']):
            raise ValueError('Invalid image hash')
        if reference['origin'] not in ('synthetic_fixture','reviewed_trace','cad_export'):
            raise ValueError('Invalid reference origin')
        if not isinstance(reference['evidence_id'],str) or not reference['evidence_id'].strip():
            raise ValueError('Missing reference evidence')
        validate_profile({'labels':reference['nodes'],'unreadable_count':0},'labels_v2')
        validate_profile({'edges':reference['edges'],'uncertain':False},'connectivity_v2')
        nodes=set(reference['nodes'])
        if any(e[k] not in nodes for e in reference['edges'] for k in ('a','b')):
            raise ValueError('Reference endpoint missing')
        if record.get('status')!='completed' or record.get('profile')!='connectivity_v2':
            raise ValueError('No completed connectivity proposal')
        if record.get('input_sha256')!=reference['image_sha256']:
            raise ValueError('Image hash mismatch')
        obj=record['proposal'];validate_profile(obj,'connectivity_v2')
        report.update(input_sha256=record['input_sha256'],proposal_sha256=digest(obj))
        if any(e[k] not in nodes for e in obj['edges'] for k in ('a','b')):
            raise ValueError('Proposed endpoint not in reference')
        expected=edge_map(reference['edges']);actual=edge_map(obj['edges'])
        report['missing_edges']=[list(e) for e in sorted(expected.keys()-actual.keys())]
        report['unexpected_edges']=[list(e) for e in sorted(actual.keys()-expected.keys())]
        report['direction_errors']=[{'edge':list(e),'expected':expected[e],'actual':actual[e]}
                                    for e in sorted(expected.keys() & actual.keys()) if expected[e]!=actual[e]]
        report.update(expected_count=len(expected),proposed_count=len(actual))
        if reference['origin']=='reviewed_trace':
            from .reference_graphs import trace_review_state
            report['trace_review_state']=trace_review_state(trace_signoff,reference)
        if any(report[k] for k in ('missing_edges','unexpected_edges','direction_errors')):
            report['reason']='Direct graph mismatch'
        elif obj['uncertain']:
            report.update(status='needs_review',reason='Model reported uncertainty')
        elif report.get('trace_review_state')=='UNREVIEWED':
            report.update(status='needs_review',reason='Signed independent trace review required')
        elif reference['origin']!='synthetic_fixture' and (not isinstance(reference['reviewer'],str) or not reference['reviewer'].strip()):
            report.update(status='needs_review',reason='Independent reference reviewer required')
        else:
            report.update(status='pass',reason='Matches frozen reference; training remains unapproved')
    except (ValueError,TypeError,KeyError) as exc:
        report['reason']=str(exc) if isinstance(exc,ValueError) else 'Invalid connectivity record'
    return report
