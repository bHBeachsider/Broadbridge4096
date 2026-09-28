import hashlib
import importlib.util
import io
from email.message import Message
from urllib.request import Request
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('acquire_refs',Path(__file__).with_name('acquire_reference_sources.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def entry():return {'file':'small.xml','url':'https://gitlab.com/example','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}


def test_replay_and_hash_validation(tmp_path):
    class Reply(io.BytesIO):headers={}
    calls=[]
    def opener(url,timeout):calls.append(url);return Reply(b'abc')
    r={'files':[entry()]}
    assert m.acquire(r,tmp_path,opener)['verified_files']==1
    m.acquire(r,tmp_path,opener);assert len(calls)==1
    (tmp_path/'small.xml').write_bytes(b'bad')
    with pytest.raises(ValueError,match='hash'):m.acquire(r,tmp_path,opener)


@pytest.mark.parametrize('key,value',[('bytes',1_000_000_001),('file','../escape'),('url','https://private.invalid/key')])
def test_unsafe_download_never_contacts_network(tmp_path,key,value):
    e=entry();e[key]=value
    with pytest.raises(ValueError):m.acquire({'files':[e]},tmp_path,lambda *a,**k:pytest.fail('network attempted'))


def test_oversize_response_rejected_before_read(tmp_path):
    class Reply:
        headers={'Content-Length':'9303633645'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):pytest.fail('body read')
    with pytest.raises(ValueError,match='size'):m.acquire({'files':[entry()]},tmp_path,lambda *a,**k:Reply())


@pytest.mark.parametrize('code',[301,302,303,307,308])
def test_redirect_never_reads_body_or_follows_location(code):
    class Body:
        def read(self,*args):pytest.fail('Unbounded redirect body read')
        def close(self):pass
    headers=Message();headers['Location']='http://127.0.0.1/private'
    handler=m.NoRedirect()
    with pytest.raises(ValueError,match='Redirect'):
        getattr(handler,'http_error_'+str(code))(Request('https://gitlab.com/example'),Body(),code,'redirect',headers)
