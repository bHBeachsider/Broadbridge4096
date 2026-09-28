import importlib.util
import json
import os
from pathlib import Path
import socket
import pytest


def module():
    path=Path(__file__).with_name('rehearse_release_audit.py')
    assert path.exists(), 'Release audit rehearsal not implemented'
    spec=importlib.util.spec_from_file_location('rehearse_release_audit',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_mock_release_admission_rehearsal(tmp_path,monkeypatch):
    foundry=os.environ.get('SLM_FOUNDRY_PATH')
    if not foundry:pytest.skip('Select Foundry with SLM_FOUNDRY_PATH')
    monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('No network'))
    out=tmp_path/'audit'
    assert module().main(['--mock','--foundry',foundry,'--out',str(out)])==0
    report=json.loads((out/'report.json').read_text())
    assert report['training_approved'] is False and report['model_calls']==0
    assert set(report['blocked'])=={'self_acceptance','revoked_rights','historical_holdout','edited_candidate','stale_decision','pending_release','stale_release_approval','mock_live_acceptance'}
    assert report['mock_release_verified'] is True
    assert report['live_integration_complete'] is False
    with pytest.raises(ValueError):module().main(['--mock','--foundry',foundry,'--out',str(out)])


def test_explicit_mock_required():
    with pytest.raises(SystemExit):module().main(['--foundry','x','--out','x'])
