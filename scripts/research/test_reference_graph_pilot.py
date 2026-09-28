import importlib.util
import json
import os
import shutil
from pathlib import Path
import pytest

SPEC=importlib.util.spec_from_file_location('reference_pilot',Path(__file__).with_name('reference_graph_pilot.py'))
pilot=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(pilot)


def test_generator_specs_are_original_bounded_and_repeatable():
    specs=pilot.specs()
    assert 0<len(specs)<=25
    assert specs==pilot.specs()
    assert len({s['seed'] for s in specs})==len(specs)
    assert all(s['family_id'].startswith('original-dexpi-') for s in specs)
    assert all(s['allowed_use']=='eval-only' and not s['training_approved'] for s in specs)


def test_unknown_license_cannot_train():
    manifest=json.loads((Path(__file__).parents[2]/'packs/oil-gas/manifests/reference_graph_sources.json').read_text())
    pilot.validate_sources(manifest)
    unknown=next(s for s in manifest['sources'] if s['license']['spdx']=='UNKNOWN')
    unknown['allowed_use']='train'
    with pytest.raises(ValueError,match='UNKNOWN'):pilot.validate_sources(manifest)


def test_non_topology_sources_cannot_be_gold():
    entry={'id':'symbols','license':{'spdx':'MIT'},'allowed_use':'eval-only',
           'topology':'none','role':'topology-gold'}
    with pytest.raises(ValueError,match='topology'):pilot.validate_sources({'sources':[entry]})


@pytest.mark.skipif(not os.environ.get('FOUNDRY_REPO'),reason='Matching Foundry checkout not configured')
def test_invalid_completed_proposal_cannot_receive_accuracy_credit(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(os.environ['FOUNDRY_REPO'])
    from src.ingestion import reference_graphs as rg
    committed=Path(__file__).parents[2]/'docs/evidence/reference-graphs-2026-09-27/pilot'
    root=tmp_path/'pilot';shutil.copytree(committed,root)
    path=root/'results-qwen/forward-chain.json';record=json.loads(path.read_bytes())
    record['proposal']['edges'].append(record['proposal']['edges'][0])
    path.write_text(json.dumps(record),encoding='utf-8')
    row=pilot.report(root,root/'results-qwen',rg)['rows'][0]
    assert row['check_status']=='fail'
    assert row['metrics']['edge_tp']==0 and row['metrics']['edge_recall']==0
