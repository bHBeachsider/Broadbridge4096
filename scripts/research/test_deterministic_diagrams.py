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
