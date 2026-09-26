"""Local Chromium acceptance: real generated report, no app server or credentials."""
import importlib.util
import json
from pathlib import Path
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("demo_browser_review", ROOT / "review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("document-review-browser")
    assert review.main(["--out", str(root / "demo")]) == 0
    second = review.analyze(ROOT / "fixtures")
    second["report_id"] = "different-fixture-report"
    (root / "demo" / "different.html").write_text(review.render_html(second), encoding="utf-8")
    unsafe = review.analyze(ROOT / "fixtures")
    unsafe["documents"][0]["records"][0]["values"]["file"] = '<img src=x onerror="window.injected=true">'
    (root / "demo" / "unsafe.html").write_text(review.render_html(unsafe), encoding="utf-8")
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(root)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/demo", root
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def page(site):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(4000)
        yield page
        browser.close()


def test_filter_and_follow_exact_source_record(page, site):
    from playwright.sync_api import expect
    page.goto(site[0] + "/report.html")
    expect(page.locator(".finding")).to_have_count(10)
    expect(page.locator("#diagram button")).to_have_count(12)
    page.get_by_label("Find tag, field or rule").fill("E-202")
    expect(page.locator(".finding")).to_have_count(1)
    page.locator(".finding .evidence-link").first.click()
    expect(page.locator(".source-record.highlight")).to_have_count(1)
    expect(page.locator(".source-record.highlight")).to_contain_text("E-202")
    page.get_by_role("button", name="Clear filters").click()
    expect(page.locator(".finding")).to_have_count(10)
    page.get_by_label("Finding category").select_option("needs_review")
    expect(page.locator(".finding")).to_have_count(3)


def test_review_persists_exports_and_is_bound_to_report(page, site):
    from playwright.sync_api import expect
    page.goto(site[0] + "/report.html")
    page.get_by_label("Reviewer name", exact=True).fill("Demo reviewer")
    page.get_by_label("Find tag, field or rule").fill("E-202")
    page.get_by_label("Disposition for E-202").select_option("needs_information")
    page.get_by_label("Notes for E-202").fill("Check which temperature is current.")
    page.reload()
    page.get_by_label("Find tag, field or rule").fill("E-202")
    expect(page.get_by_label("Disposition for E-202")).to_have_value("needs_information")
    expect(page.get_by_label("Notes for E-202")).to_have_value("Check which temperature is current.")
    with page.expect_download() as download:
        page.get_by_role("button", name="Export review notes").click()
    payload = json.loads(Path(download.value.path()).read_text())
    assert payload["reviewer"] == "Demo reviewer"
    row = next(r for r in payload["findings"] if r["tag"] == "E-202")
    assert row["disposition"] == "needs_information"
    assert row["notes"] == "Check which temperature is current."
    assert payload["synthetic"] is True and payload["engineering_signoff"] is False
    assert len(payload["report_id"]) == 64
    page.goto(site[0] + "/different.html")
    page.get_by_label("Find tag, field or rule").fill("E-202")
    expect(page.get_by_label("Notes for E-202")).to_have_value("")
    expect(page.get_by_label("Disposition for E-202")).to_have_value("pending")


def test_local_storage_failure_is_visible_and_export_still_works(page, site):
    from playwright.sync_api import expect
    page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    page.goto(site[0] + "/report.html")
    expect(page.locator(".finding")).to_have_count(10)
    expect(page.locator("#storage-status")).to_contain_text("not saved")
    with page.expect_download():
        page.get_by_role("button", name="Export review notes").click()


def test_source_markup_is_inert_and_no_external_requests(page, site):
    from playwright.sync_api import expect
    requests, errors = [], []
    page.on("request", lambda req: requests.append(req.url))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(site[0] + "/unsafe.html")
    expect(page.locator(".finding")).to_have_count(10)
    page.locator("#sources details").first.locator("summary").click()
    expect(page.locator("#sources")).to_contain_text('<img src=x onerror="window.injected=true">')
    assert page.evaluate("window.injected") is None
    assert not errors
    assert all(u.startswith(site[0]) for u in requests)


def test_mobile_layout_and_keyboard_controls(page, site):
    from playwright.sync_api import expect
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(site[0] + "/report.html")
    expect(page.locator(".finding")).to_have_count(10)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_label("Find tag, field or rule").focus()
    page.keyboard.type("not-a-tag")
    expect(page.locator("#findings")).to_contain_text("No findings match")
    page.get_by_role("button", name="Clear filters").click()
    expect(page.locator(".finding")).to_have_count(10)
    page.screenshot(path=str(site[1] / "mobile.png"), full_page=True)
