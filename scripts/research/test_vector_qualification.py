import importlib.util
from pathlib import Path


def api():
    spec=importlib.util.spec_from_file_location('vq',Path(__file__).with_name('vector_qualification.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def test_perfect_development_result_never_becomes_qualified():
    rates={name:{'estimate':1.,'lower_95':.999} for name in ('edge_precision','edge_recall','direction_precision','direction_recovery')}
    thresholds={name:.995 for name in rates}
    status=api().assess(rates,thresholds,critical_flags=0,evidence_complete=True)
    assert status['point_targets_met'] and status['descriptive_lower_bounds_met']
    assert status['qualification']=='not_qualified_regression'
    assert status['training_approved'] is False


def test_no_direction_claims_and_any_critical_error_block_point_success():
    rates={name:{'estimate':1.,'lower_95':.999} for name in ('edge_precision','edge_recall','direction_precision','direction_recovery')}
    thresholds={name:.99 for name in rates}
    assert not api().assess(rates,thresholds,critical_flags=1,evidence_complete=True)['point_targets_met']
    assert not api().assess(rates,thresholds,critical_flags=0,evidence_complete=False)['point_targets_met']
    rates['direction_precision']={'estimate':None,'lower_95':None}
    assert not api().assess(rates,thresholds,critical_flags=0,evidence_complete=True)['point_targets_met']


def test_archived_report_all_claims_denominator_and_drawing_count():
    root=Path(__file__).resolve().parents[2]
    import json,sys
    foundry=root.parent/'slm-foundry-worktrees'/'codex-foundry-ingestion-live-http'
    # Same explicit path convention as other offline research tests.
    import os,pytest
    foundry=Path(os.environ.get('FOUNDRY_REPO',foundry))
    if not (foundry/'src/ingestion/diagram_metrics.py').exists():pytest.skip('Matching Foundry metrics checkout not configured')
    sys.path.insert(0,str(foundry))
    from src.ingestion.diagram_metrics import summarize
    legacy=json.loads((root/'docs/evidence/deterministic-diagrams-2026-09-27/results-final.json').read_text())
    rows=[r for r in legacy['rows'] if r['route']=='baseline']
    for r in rows:r['evidence_rejected_edges']=r['metrics']['edge_tp']+r['metrics']['edge_fp']
    result=api().summarize_rows(rows,'metrics',summarize)
    assert result['drawings']==12
    assert result['direction_precision']['denominator']==6
    assert result['direction_recovery']['denominator']==7
    assert result['edge_precision']['denominator']==31
    assert result['unknown_directions_on_matched_edges']==5
    assert result['checker_rejected_graphs']==0
    assert result['baseline_without_detector_evidence']==12


def test_failed_and_missing_outputs_are_not_checker_rejections():
    import copy,sys,os,pytest
    foundry=Path(os.environ.get('FOUNDRY_REPO','missing'))
    if not (foundry/'src/ingestion/diagram_metrics.py').exists():pytest.skip('Matching Foundry checkout not configured')
    sys.path.insert(0,str(foundry))
    from src.ingestion.diagram_metrics import summarize
    import json
    root=Path(__file__).resolve().parents[2]
    row=json.loads((root/'docs/evidence/deterministic-diagrams-2026-09-27/results-final.json').read_text())['rows'][0]
    for status,expected in [('not_run','detector_not_run'),('failed','extraction_failed'),('invalid_evidence','checker_rejected_graphs')]:
        r=copy.deepcopy(row);r['status']=status;r['rules']={'status':'fail'} if status=='invalid_evidence' else None
        r['evidence_rejected_edges']=0
        s=api().summarize_rows([r],'metrics',summarize)
        assert s[expected]==1
        assert s['checker_rejected_graphs']==(status=='invalid_evidence')
        assert s['statuses']=={status:1}


def test_evidence_completeness_has_counts_not_just_a_boolean():
    import os,sys,pytest,json
    foundry=Path(os.environ.get('FOUNDRY_REPO','missing'))
    if not (foundry/'src/ingestion/diagram_metrics.py').exists():pytest.skip('Matching Foundry checkout not configured')
    sys.path.insert(0,str(foundry))
    from src.ingestion.diagram_metrics import summarize
    root=Path(__file__).resolve().parents[2]
    rows=json.loads((root/'docs/evidence/deterministic-diagrams-2026-09-27/results-final.json').read_text())['rows']
    row=next(r for r in rows if r['route']=='dxf' and r['id']=='hop')
    row['evidence_rejected_edges']=7
    r=api().summarize_rows([row],'metrics',summarize)
    assert r['evidence_completeness']=={'successes':1,'denominator':8,'estimate':.125}


def test_final_regression_report_replays_and_never_qualifies():
    import os,json,pytest
    foundry=Path(os.environ.get('FOUNDRY_REPO','missing'))
    if not (foundry/'src/ingestion/diagram_metrics.py').exists():pytest.skip('Matching Foundry checkout not configured')
    root=Path(__file__).resolve().parents[2]
    inputs=root/'docs/evidence/deterministic-diagrams-2026-09-27/inputs'
    archive=root/'docs/evidence/vector-continuity-2026-09-28'
    result=api().report(inputs,archive/'detected-final',inputs/'baseline-v2',foundry,root/'packs/oil-gas/manifests/diagram_metric_contract.json')
    expected=json.loads((archive/'results-final.json').read_text())
    assert result==expected
    assert result['routes']['dxf']['raw']['counts']['fp']==0
    assert result['routes']['dxf']['raw']['counts']['fn']==1
    assert not result['gate_eligible'] and not result['training_approved']
