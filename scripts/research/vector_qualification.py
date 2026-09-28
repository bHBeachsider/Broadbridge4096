"""CPU-only regression metric contract. This command cannot qualify training.

Revalidates frozen inputs and detector/baseline receipts using the original report,
then adds denominator-explicit Wilson intervals. No extraction or model calls.
"""
import argparse
from collections import Counter,defaultdict
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def legacy_api():
    spec=importlib.util.spec_from_file_location('dd',Path(__file__).with_name('deterministic_diagrams.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def assess(rates,thresholds,*,critical_flags,evidence_complete):
    def meets(field):
        return all(rates[k][field] is not None and rates[k][field]>=target for k,target in thresholds.items())
    clean=critical_flags==0 and evidence_complete
    return {'point_targets_met':clean and meets('estimate'),
            'descriptive_lower_bounds_met':clean and meets('lower_95'),
            'qualification':'not_qualified_regression','training_approved':False}


def summarize_rows(rows,metric_key,summary_function):
    def total(key):return sum(r[metric_key][key] for r in rows)
    raw=metric_key=='metrics'
    rejected=sum(r.get('rules') is not None and r['rules']['status']!='pass' for r in rows)
    violations=sum(r['evidence_rejected_edges'] for r in rows) if raw else 0
    s=summary_function(tp=total('edge_tp'),fp=total('edge_fp'),fn=total('edge_fn'),
        direction_claims=total('direction_claims'),directions_correct=total('direction_correct'),
        reference_directions=total('known_directions'),directions_reversed=total('direction_reversals'),
        unsupported_directions=total('unsupported_directions'),evidence_violations=violations,
        checker_rejections=rejected)
    s.update(drawings=len(rows),reference_edges=total('edge_tp')+total('edge_fn'),
        unknown_directions_on_matched_edges=total('known_direction_unknown'),
        missed_directed_edges=total('known_direction_missing'),
        false_edges_in_crossing_categories=total('false_edges_at_crossings'),
        unbacked_direction_claims=sum(r['arrow_evidence']['unbacked_directions'] for r in rows) if raw else 0,
        checker_rejected_graphs=rejected,
        detector_not_run=sum(r['status']=='not_run' for r in rows),
        extraction_failed=sum(r['status']=='failed' and r['route']!='baseline' for r in rows),
        baseline_without_detector_evidence=sum(r['route']=='baseline' and r['status']=='completed' for r in rows),
        statuses=dict(Counter(r['status'] for r in rows)),
        evidence_complete=(violations==0 and total('edge_tp')+total('edge_fp')>0))
    predicted=total('edge_tp')+total('edge_fp')
    s['evidence_completeness']={'successes':predicted-violations,'denominator':predicted,
                                'estimate':(predicted-violations)/predicted if predicted else None}
    s['critical_error_flags']+=s['false_edges_in_crossing_categories']
    return s


def report(work,detected,baseline,foundry,contract):
    old=legacy_api();legacy=old.report(work,detected,baseline,foundry)
    from src.ingestion.diagram_metrics import summarize
    from src.ingestion.geometry_contract import check_edges
    _,manifest=old.verify(work)
    rows=legacy['rows']
    # Per-edge evidence failures, distinct from whole-drawing rejection counts.
    for row in rows:
        if row['route']=='baseline':row['evidence_rejected_edges']=row['metrics']['edge_tp']+row['metrics']['edge_fp']
        else:
            p=detected/(row['id']+'.'+row['route']+'.json')
            data=json.loads(p.read_bytes()) if p.exists() else {}
            row['evidence_rejected_edges']=sum(check_edges([e],data['detection'])['status']!='pass' for e in data.get('edges',[]))
    policy=json.loads(contract.read_bytes());groups=defaultdict(list)
    for row in rows:groups[row['route']].append(row)
    result={}
    for route,items in groups.items():
        raw=summarize_rows(items,'metrics',summarize)
        accepted=summarize_rows(items,'accepted_metrics',summarize)
        thresholds=policy['routes'].get(route)
        state=assess(raw,thresholds,critical_flags=raw['critical_error_flags'],evidence_complete=raw['evidence_complete']) if thresholds else {'qualification':'historical_baseline_only','training_approved':False}
        result[route]={'raw':raw,'accepted':accepted,'assessment':state,
            'per_family':{'original-simple-line-generator':raw},
            'per_drawing':{r['id']:summarize_rows([r],'metrics',summarize) for r in items},
            'per_failure_category':{category:summarize_rows([r for r in items if r['category']==category],'metrics',summarize) for category in sorted({r['category'] for r in items})}}
    return {'schema':'broadbridge.vector_qualification_report/1','routes':result,
        'manifest_sha256':legacy['manifest_sha256'],'contract_sha256':old.sha(contract.read_bytes()),
        'metric_engine_sha256':old.sha((foundry/'src/ingestion/diagram_metrics.py').read_bytes()),
        'report_script_sha256':old.sha(Path(__file__).read_bytes()),
        'legacy_report_script_sha256':old.sha(Path(old.__file__).read_bytes()),
        'detector_run_sha256':old.sha((detected/'run.json').read_bytes()),
        'evaluation_role':'regression-only','family_partition':'unreviewed synthetic construction families; not independent validation',
        'arrow_eligibility':'construction-known directions; visibility not independently signed',
        'training_approved':False,'gate_eligible':False,
        'blocking_gates':legacy['blocking_gates']+['independent_heldout_families','visible_arrow_eligibility_pinned','cluster_aware_uncertainty_review'],
        'limitations':manifest['limitations']+['Wilson intervals are iid descriptive approximations, not cluster-aware qualification.',
            'Twelve drawings per route are not 36 independent drawings; source formats share geometry.',
            'Critical-error categories may overlap; flag totals are not unique incidents.',
            'Blank or rejected outputs remain in recall denominators; accepted evidence is not training approval.']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('work','detected','baseline','foundry','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--contract',type=Path,default=ROOT/'packs/oil-gas/manifests/diagram_metric_contract.json')
    a=p.parse_args();r=report(a.work,a.detected,a.baseline,a.foundry,a.contract)
    legacy_api().write(a.out,r)
    print(json.dumps({route:{'raw':v['raw'],'assessment':v['assessment']} for route,v in r['routes'].items()},indent=2))


if __name__=='__main__':main()
