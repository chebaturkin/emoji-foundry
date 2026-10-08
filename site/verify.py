"""Browser smoke test for the built Fondy workshop.

Run ``site/build.py`` and ``site/serve.py`` first. The check stays local and
writes a small report plus two screenshots to ``site/previews/workshop``.
"""

from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:8799"
OUT = ROOT / "previews" / "workshop"
OUT.mkdir(parents=True, exist_ok=True)
WIDTHS = (320, 390, 768, 1024, 1440)
report: dict[str, object] = {"pages": [], "interactions": [], "errors": [], "routes": {}}


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(reduced_motion="reduce")
    page.on("pageerror", lambda error: report["errors"].append(str(error)))

    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 960})
        response = page.goto(BASE + "/", wait_until="networkidle")
        assert response and response.status == 200
        page.evaluate("document.fonts.ready")
        result = page.evaluate(
            """() => ({
                overflow: document.documentElement.scrollWidth > innerWidth,
                h1: document.querySelectorAll('h1').length,
                main: document.querySelectorAll('main').length,
                scenes: [...document.querySelectorAll('[data-workshop-scene]')].filter(node => !node.hidden).length,
                brokenImages: [...document.images].filter(image => !image.naturalWidth).map(image => image.src),
                unnamedButtons: [...document.querySelectorAll('button')].filter(button => !(button.getAttribute('aria-label') || button.textContent).trim()).length,
                fonts: document.fonts.check('16px "EF Onest"') && document.fonts.check('16px "EF Dela"')
            })"""
        )
        assert not result["overflow"] and result["h1"] == 1 and result["main"] == 1
        assert result["scenes"] == 1 and not result["brokenImages"] and not result["unnamedButtons"] and result["fonts"], result
        report["pages"].append({"width": width, **result})
        if width in (390, 1440):
            page.screenshot(path=str(OUT / f"workshop-{width}.png"), full_page=True)

    page.goto(BASE + "/", wait_until="networkidle")
    tabs = page.locator('[role="tab"]')
    tabs.nth(0).focus()
    page.keyboard.press("ArrowRight")
    assert page.locator('[role="tab"][data-workshop-mode="pause"]').get_attribute("aria-selected") == "true"
    assert page.locator('[data-workshop-scene="pause"]').is_visible()
    report["interactions"].append("scene tabs: ArrowRight moves focus and selection")

    page.locator('[role="tab"][data-workshop-mode="signal"]').click()
    for heart in ("01-heart", "02-heart-double", "03-heart-open", "27-ira-heart", "01-heart"):
        page.locator(f'.heart-choice[data-heart="{heart}"]').click()
    assert page.locator('[data-signal-count]').inner_text() == "4 / 4"
    assert len(page.evaluate("() => window.__fondyWorkshop.getState().signal")) == 4
    page.locator('[data-signal-undo]').click()
    assert len(page.evaluate("() => window.__fondyWorkshop.getState().signal")) == 3
    report["interactions"].append("signal: four-heart cap, add, and undo")

    page.locator('[role="tab"][data-workshop-mode="letter"]').click()
    page.locator('[data-letter-note]').fill("Я рядом 👩‍🚀")
    page.locator('[data-note-heart="27-ira-heart"]').click()
    page.locator('[data-letter-form]').locator('button[type="submit"]').click()
    letter_state = page.evaluate("() => window.__fondyWorkshop.getState()")
    assert letter_state["note"] == "Я рядом 👩‍🚀"
    assert letter_state["noteHeart"] == "27-ira-heart"
    assert page.locator('[data-envelope-heart]').get_attribute("src").endswith("27-ira-heart.png")
    signal_before_envelope_click = letter_state["signal"][:]
    page.locator('[data-envelope-heart]').click()
    assert page.evaluate("() => window.__fondyWorkshop.getState().signal") == signal_before_envelope_click
    report["interactions"].append("letter: grapheme-safe note and selected artwork")

    page.locator('[role="tab"][data-workshop-mode="pause"]').click()
    for step in range(1, 5):
        page.locator(f'[data-pause-step="{step}"]').click()
    assert page.locator('[data-pause-progress]').get_attribute("value") == "4"
    report["interactions"].append("pause: all four hold/release steps")

    page.locator('[role="tab"][data-workshop-mode="rhythm"]').click()
    for key in ("1", "4", "2"):
        page.keyboard.press(key)
    rhythm_state = page.evaluate("() => window.__fondyWorkshop.getState()")
    assert rhythm_state["rhythm"][-3:] == [1, 4, 2]
    saved_hash = page.evaluate("() => location.hash")
    page.reload(wait_until="networkidle")
    assert page.evaluate("() => window.__fondyWorkshop.getState().rhythm.slice(-3)") == [1, 4, 2]
    assert page.evaluate("() => location.hash") == saved_hash
    report["interactions"].append("rhythm: keyboard sequence 1-4-2")
    report["interactions"].append("state: URL hash survives a reload")

    page.locator('[data-workshop-action="copy"]').click()
    expect(page.locator('[data-workshop-status]')).to_contain_text("адрес")
    report["interactions"].append("copy: local-only address explanation")

    with page.expect_download() as download_info:
        page.locator('[data-workshop-action="portable"]').click()
    assert download_info.value.suggested_filename == "fondy-workshop.html"
    with page.expect_download() as download_info:
        page.locator('[data-workshop-action="export"]').click()
    assert download_info.value.suggested_filename in {"fondy-workshop.png", "fondy-workshop.svg"}
    report["interactions"].append("exports: portable HTML and image download")

    page.emulate_media(reduced_motion="reduce")
    assert page.locator('.workshop-mascot').evaluate("node => getComputedStyle(node).animationName") == "none"
    report["interactions"].append("reduced motion: idle animation is disabled")

    for route in ("/editor", "/sections/workshop.html", "/assets/../README.md"):
        route_response = page.request.get(BASE + route)
        report["routes"][route] = route_response.status
        assert route_response.status == 404

    browser.close()

assert not report["errors"], report["errors"]
(OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Verified {len(report['pages'])} viewport combinations and {len(report['interactions'])} interactions.")
