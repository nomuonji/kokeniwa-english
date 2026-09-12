"""Browser-level checks for install metadata, updates, and offline reading."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    PORT = sock.getsockname()[1]
BASE = f"http://127.0.0.1:{PORT}"
server = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(ROOT / "dist")],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
for _ in range(40):
    try:
        urlopen(BASE + "/", timeout=.25).close()
        break
    except Exception:
        time.sleep(.1)
else:
    raise RuntimeError("Preview server did not start")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(service_workers="allow")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    page.goto(BASE + "/")
    page.evaluate("navigator.serviceWorker.ready")
    page.reload()
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    registration = page.evaluate("""async () => {
      const reg = await navigator.serviceWorker.getRegistration();
      return {scope: reg.scope, active: Boolean(reg.active)};
    }""")
    assert registration["active"] and registration["scope"] == BASE + "/", registration

    manifest_response = page.request.get(BASE + "/static/manifest.webmanifest")
    assert manifest_response.ok
    manifest = json.loads(manifest_response.text())
    assert manifest["display"] == "standalone" and manifest["scope"] == "/"
    assert {icon["sizes"] for icon in manifest["icons"]} >= {"192x192", "512x512"}

    page.route("**/version.json*", lambda route: route.fulfill(
        status=200, content_type="application/json", body='{"version":"new-release"}'))
    page.reload()
    page.locator(".app-update").wait_for(state="visible")
    assert page.locator(".app-update button").text_content() == "更新する"
    page.unroute("**/version.json*")

    page.goto(BASE + "/reading/1/")
    page.wait_for_load_state("networkidle")
    server.terminate()
    server.wait(timeout=5)
    page.reload()
    assert page.locator("main").is_visible()
    page.goto(BASE + "/offline-fallback-check/")
    assert page.locator(".brand").is_visible()

    assert not errors, errors
    print("PWA install, update notice, and offline fallback: OK")
    browser.close()
