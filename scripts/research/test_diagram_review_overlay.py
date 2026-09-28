import importlib.util
import json
from pathlib import Path

import pytest


def api():
    spec = importlib.util.spec_from_file_location('overlay',Path(__file__).with_name('diagram_review_overlay.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def inputs(tmp_path):
    from PIL import Image
    source=tmp_path/'drawing.png';Image.new('RGB',(120,80),'white').save(source)
    import hashlib
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    detected=tmp_path/'detected.json'
    detected.write_text(json.dumps({'input_sha256':sha,'edges':[{
        'a':'secret-proposal</script><img src=x onerror=alert(1)>','b':'B',
        'direction':'unknown','path':[[1,2],[100,70]],'arrow_id':None}],
        'detection':{'arrows':[],'warnings':['review-contact']}}),encoding='utf-8')
    ref=tmp_path/'reference.json';ref.write_text('{"edges":[],"answer":"SECRET-GOLD"}',encoding='utf-8')
    return source,detected,ref


def test_source_only_bundle_contains_no_prediction_or_gold(tmp_path):
    source,detected,ref=inputs(tmp_path)
    out=tmp_path/'source-only'
    result=api().build_review_bundle(source,detected,None,out,revision='r1')
    assert result['mode']=='source_only'
    for path in out.glob('*'):
        if path.suffix in ('.html','.json'):
            raw=path.read_text(encoding='utf-8')
            assert 'secret-proposal' not in raw and 'SECRET-GOLD' not in raw


def test_overlay_is_local_escaped_and_preserves_pixel_coordinates(tmp_path):
    source,detected,ref=inputs(tmp_path);out=tmp_path/'overlay'
    result=api().build_review_bundle(source,detected,ref,out,revision='r1')
    html=(out/'review.html').read_text(encoding='utf-8')
    assert 'viewBox="0 0 120 80"' in html
    assert 'points="1,2 100,70"' in html
    assert '<img src=x' not in html
    assert 'SECRET-GOLD' not in html  # Reviewed reference is pinned, never embedded in browser.
    assert 'pending_authenticated_review' in html
    assert '<script src=' not in html and '<link href="http' not in html
    assert result['training_approved'] is False


def test_changed_source_is_refused_and_existing_bundle_not_overwritten(tmp_path):
    source,detected,ref=inputs(tmp_path);out=tmp_path/'overlay'
    api().build_review_bundle(source,detected,ref,out,revision='r1')
    with pytest.raises(FileExistsError):api().build_review_bundle(source,detected,ref,out,revision='r1')
    from PIL import Image
    Image.new('RGB',(120,80),'black').save(source)
    with pytest.raises(ValueError,match='source hash'):
        api().build_review_bundle(source,detected,ref,tmp_path/'bad',revision='r1')
    assert not (tmp_path/'bad').exists()


def test_correction_stays_pending_and_binds_revision_and_before_hash(tmp_path):
    source,detected,ref=inputs(tmp_path);out=tmp_path/'overlay'
    bundle=api().build_review_bundle(source,detected,ref,out,revision='r1')
    proposal={**bundle['proposal_template'],'reviewer':'Bill','after':[], 'comment':'remove false edge'}
    assert api().validate_proposal(proposal,bundle)==[]
    proposal['revision']='r2'
    assert 'stale_revision' in api().validate_proposal(proposal,bundle)
    proposal['revision']='r1';proposal['status']='signed'
    assert 'unauthenticated_status' in api().validate_proposal(proposal,bundle)
