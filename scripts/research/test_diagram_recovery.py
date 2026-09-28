import importlib.util
from pathlib import Path


def api():
    import os,sys
    sys.path.insert(0,os.environ['FOUNDRY_REPO'])
    spec=importlib.util.spec_from_file_location('recovery',Path(__file__).with_name('diagram_recovery.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_rejected_graph_still_loses_all_accepted_recall():
    reference=[{'a':'A','b':'B','direction':'a_to_b'}]
    proposed=[{'a':'A','b':'B','direction':'b_to_a'}]
    row=api().score(reference,{'edges':proposed,'rules':{'status':'fail'}},'arrow')
    assert row['raw']['edge_tp']==1 and row['raw']['direction_reversals']==1
    assert row['accepted']['edge_tp']==0 and row['accepted']['edge_fn']==1


def test_empty_bucket_and_assisted_ports_are_not_reported_as_success():
    result=api().aggregate([])
    assert result['edge_precision']['estimate'] is None
    assert result['direction_recovery']['denominator']==0
    assert result['qualified'] is False
    assert result['port_tag_detection']['status']=='unmeasured_supplied_ports'


def test_failed_extraction_counts_as_misses_not_rejection():
    row=api().score([{'a':'A','b':'B','direction':'unknown'}],{'status':'failed','edges':[]},'break')
    assert row['raw']['edge_fn']==1
    assert row['checker_rejected']==0
    assert row['extraction_failed']==1


def test_false_crossing_edge_is_a_critical_flag_even_if_structurally_accepted():
    row=api().score([{'a':'A','b':'B','direction':'unknown'}],
        {'edges':[{'a':'A','b':'C','direction':'unknown'}],'rules':{'status':'pass'}},'crossing')
    assert api().aggregate([row])['critical_error_flags']==1


def test_cpu_report_binds_source_snapshots(tmp_path):
    import os,json,hashlib
    root=Path(__file__).resolve().parents[2]/'docs/evidence/diagram-target-recovery-2026-09-28/development'
    api().run(root,tmp_path/'run',Path(os.environ['FOUNDRY_REPO']),'development',2)
    receipt=json.loads((tmp_path/'run/run.json').read_bytes())
    assert receipt['model_calls']==0
    assert receipt['versions']['opencv']
    for name,expected in receipt['source_snapshot'].items():
        assert hashlib.sha256((tmp_path/'run/source-snapshot'/name).read_bytes()).hexdigest()==expected
