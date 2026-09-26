"""The domain runner uses fabricated fixtures; Bill has approved no recipe here."""
import importlib.util
import json
import os
from pathlib import Path
import socket

import pytest


def module():
    path=Path(__file__).with_name('rehearse_synthetic_batch.py')
    assert path.exists(), 'SD-03 domain rehearsal is not implemented'
    spec=importlib.util.spec_from_file_location('rehearse_synthetic_batch', path)
    value=importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def test_two_fabricated_jobs_end_pending_with_no_network(tmp_path, monkeypatch):
    foundry=os.environ.get('SLM_FOUNDRY_PATH')
    if not foundry: pytest.skip('Select an absolute Foundry checkout with SLM_FOUNDRY_PATH')
    monkeypatch.setattr(socket.socket, 'connect', lambda *a: pytest.fail('No network'))
    root=tmp_path/'run'
    assert module().main(['--mock','--foundry',foundry,'--out',str(root)])==0
    report=json.loads((root/'report.json').read_text())
    assert report['mock_role_calls']==4 and report['external_model_calls']==0
    assert report['pending_packets']==2 and report['release_blocked_without_review'] is True
    assert report['priority_decision']=='awaiting_bill'
    for f in (root/'batch').glob('*.packet.json'):
        packet=json.loads(f.read_text())
        assert packet['status']=='pending' and packet['training_approved'] is False
        assert packet['generation_receipt']['mode']=='mock'
    for f in (root/'batch').glob('*.started.json'):
        assert 'PRIVATE SYNTHETIC HINDSIGHT' not in f.read_text()
        assert 'PRIVATE SYNTHETIC REFERENCE' not in f.read_text()
    with pytest.raises(ValueError, match='new absolute'):
        module().main(['--mock','--foundry',foundry,'--out',str(root)])


def test_rehearsal_has_no_live_or_implicit_mode(tmp_path):
    with pytest.raises(SystemExit): module().main(['--foundry','relative','--out',str(tmp_path/'r')])


def test_draft_curriculum_cannot_be_used_as_live_approval():
    import yaml
    root=Path(__file__).resolve().parents[2]
    data=yaml.safe_load((root/'packs/oil-gas/synthetic/recipes.yaml').read_text())
    assert data['priority_decision']['status']=='awaiting_bill'
    assert data['priority_decision']['decision_record'] is None
    assert all(row['status']=='draft' for row in data['recipes'])
