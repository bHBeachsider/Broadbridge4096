"""The owned-local harness must not inherit libpq routing from the host."""
import importlib.util
import os
from pathlib import Path

import pytest


def helper():
    path = Path(__file__).resolve().parents[3] / "scripts/ingestion_local_smoke.py"
    spec = importlib.util.spec_from_file_location("ingestion_local_smoke", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("fail", [False, True])
def test_parent_connection_phase_cannot_inherit_host_routing(monkeypatch, tmp_path, fail):
    module = helper()
    monkeypatch.setenv("PGHOSTADDR", "not-a-local-address")
    monkeypatch.setenv("PGSERVICE", "untrusted-shared-service")
    monkeypatch.setenv("PGPASSFILE", "untrusted-password-file")
    seen = []

    def local_phase(*_args, public_review=False, review_only=False):
        assert public_review is False and review_only is False
        seen.extend(key for key in os.environ if key.upper().startswith("PG"))
        if fail:
            raise RuntimeError("synthetic failure before connecting")
        return {"safe": True}

    monkeypatch.setattr(module, "_run_local", local_phase)
    if fail:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            module.run(tmp_path, tmp_path, tmp_path)
    else:
        assert module.run(tmp_path, tmp_path, tmp_path) == {"safe": True}
    assert seen == []
    assert os.environ["PGHOSTADDR"] == "not-a-local-address"
    assert os.environ["PGSERVICE"] == "untrusted-shared-service"
    assert os.environ["PGPASSFILE"] == "untrusted-password-file"


def test_request_handlers_finish_before_host_routing_is_restored(monkeypatch):
    from contextlib import ExitStack
    from http.server import BaseHTTPRequestHandler
    import threading
    from urllib.request import urlopen
    module = helper()
    monkeypatch.setenv("PGHOSTADDR", "not-a-local-address")
    ready, entered, close_now, release, closed = [threading.Event() for _ in range(5)]
    urls, seen = [], []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_GET(self):
            entered.set()
            release.wait(5)
            seen.append(os.environ.get("PGHOSTADDR"))
            self.send_response(204)
            self.end_headers()
    def owner():
        with module.isolated_libpq_environment(), ExitStack() as stack:
            urls.append(module.serve_http(stack, Handler))
            ready.set()
            close_now.wait(5)
        closed.set()
    owning_thread = threading.Thread(target=owner)
    owning_thread.start()
    assert ready.wait(5)
    def request():
        with urlopen(urls[0], timeout=10) as response:
            assert response.status == 204
    client = threading.Thread(target=request)
    client.start()
    try:
        assert entered.wait(5)
        close_now.set()
        assert not closed.wait(0.8), "HTTP request still runs after environment restoration"
    finally:
        release.set()
        close_now.set()
        client.join(10)
        owning_thread.join(10)
    assert seen == [None]
    assert closed.is_set()
    assert os.environ["PGHOSTADDR"] == "not-a-local-address"
