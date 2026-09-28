import importlib.util
from pathlib import Path

import pytest


def api():
    spec = importlib.util.spec_from_file_location('fixture_suite', Path(__file__).with_name('diagram_fixture_suite.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_new_seed_does_not_make_an_independent_family():
    records = [
        {'id': 'a', 'family_id': 'generator-1', 'seed': 1, 'split': 'development'},
        {'id': 'b', 'family_id': 'generator-1', 'seed': 2, 'split': 'reserve_a'},
    ]
    assert api().validate_split(records) == ['family_leakage:generator-1']


def test_cap_includes_existing_twelve():
    with pytest.raises(ValueError, match='50'):
        api().validate_design({'existing_count': 12, 'drawings': [{'id': str(i), 'family_id': 'same', 'seed': i, 'split': 'development'} for i in range(39)]})


def test_traversal_and_duplicate_ids_fail_before_creating_output():
    for ids in [('../evil',), ('same', 'same')]:
        with pytest.raises(ValueError, match='drawing ID'):
            api().validate_design({'existing_count': 12, 'drawings': [
                {'id': i, 'family_id': 'same', 'seed': 1, 'split': 'development'} for i in ids]})


def test_preparation_freezes_without_running_detector(tmp_path):
    import os, json, sys
    foundry = Path(os.environ['FOUNDRY_REPO'])
    # Actual detector modules are never called by preparation.
    out = tmp_path/'suite'
    design = Path(__file__).resolve().parents[2]/'packs/oil-gas/manifests/diagram_fixture_design.json'
    result = api().prepare_suite(out, foundry, design)
    assert result['new_drawings'] == 14
    assert result['program_drawings'] == 26
    assert result['reserves_generated'] == 0
    assert result['detector_runs'] == 0
    assert api().verify_suite(out)['training_approved'] is False
    assert not list(out.glob('*.detected.json'))
    with pytest.raises(FileExistsError):
        api().prepare_suite(out, foundry, design)
    (out/'dev-01.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        api().verify_suite(out)
