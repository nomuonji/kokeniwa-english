"""Browser regression checks. Build and serve dist first; set SITE_CHECK_BASE if needed."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os
import tempfile

out = Path(tempfile.gettempdir()) / 'kokeniwa-english-review'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    errors = []
    for port, name, vocab in [(8875, 'english', '/training/eiken-pre1/')]:
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('https://www.googletagmanager.com/**', lambda route: route.abort())
        base = os.environ.get('SITE_CHECK_BASE', f'http://127.0.0.1:{port}').rstrip('/')
        for route in ['/', '/reading/', '/reading/articles/', '/reading/1/', '/vocab/', vocab, '/blog/', '/books/', '/404.html']:
            print(name, route, flush=True)
            page.goto(base + route)
            page.wait_for_load_state('networkidle')
            assert page.locator('h1').count() == 1, route
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), route
        page.goto(base + vocab)
        page.wait_for_selector('.fc-cell')
        assert page.locator('.fc-cell:visible').count() == 48
        page.locator('#study-search').fill('zzzz-no-such-word-xxxx')
        assert page.locator('.fc-cell:visible').count() == 0
        assert page.locator('.study-empty').is_visible()
        page.locator('.study-tools button').click()
        page.locator('.study-more').click()
        assert page.locator('.fc-cell:visible').count() == 96
        cell = page.locator('.fc-cell:visible').first
        cell.click()
        assert cell.get_attribute('aria-pressed') == 'true'
        assert cell.locator('.fc-cell-back').get_attribute('aria-hidden') == 'false'
        page.locator('.fc-bar button').click()
        assert page.locator('.fc-cell.flipped:visible').count() == 96
        page.goto(base + vocab + '#w100')
        page.wait_for_selector('#w100.flipped')
        assert page.locator('#w100').is_visible()
        page.goto(base + '/')
        assert page.locator('.resume-study a').is_visible()
        page.locator('img[loading="lazy"]').evaluate_all('(images) => images.forEach(image => image.loading = "eager")')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(out / f'{name}-desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.reload()
        assert page.locator('#main-nav').is_hidden()
        page.locator('.menu-toggle').click()
        assert page.locator('#main-nav').is_visible()
        page.keyboard.press('Escape')
        assert page.locator('#main-nav').is_hidden()
        page.screenshot(path=str(out / f'{name}-mobile.png'), full_page=True)
        for route in ['/reading/', '/reading/articles/', vocab, '/books/', '/blog/']:
            page.goto(base + route)
            page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, route, 'mobile overflow')
        page.goto(base + '/reading/1/')
        reveal = page.locator('[data-reveal]')
        if reveal.count():
            reveal.click()
            assert reveal.get_attribute('aria-expanded') == 'true'
            reveal.click()
            assert reveal.get_attribute('aria-expanded') == 'false'
        else:
            page.locator('.choice').first.click()
            assert page.locator('.answer-panel.open').is_visible()
        page.goto(base + '/reading/')
        page.locator('#study-search').fill('zzzzz-unmatched')
        assert page.locator('.list-item:visible').count() == 0
        page.locator('.study-tools button').click()
        assert page.locator('.list-item:visible').count() > 0
        page.emulate_media(color_scheme='dark', reduced_motion='reduce')
        page.goto(base + vocab)
        page.wait_for_selector('.fc-cell')
        page.screenshot(path=str(out / f'{name}-cards-dark.png'), full_page=True)
        page.goto(base + '/reading/articles/')
        page.locator('.reading-article-card').first.click()
        page.wait_for_load_state('networkidle')
        sentence = page.locator('[data-reading-sentence]').first
        sentence.click()
        target = sentence.get_attribute('aria-controls')
        assert page.locator('#' + target).is_visible()
        sentence.click()
        assert page.locator('#' + target).is_hidden()
        page.screenshot(path=str(out / f'{name}-reading-mobile.png'), full_page=True)
        page.set_viewport_size({'width': 320, 'height': 700})
        for route in ['/', vocab, '/books/', '/reading/articles/']:
            page.goto(base + route)
            page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (name, route, '320px overflow')
        page.route('**/static/data/**', lambda route: route.fulfill(status=503, body='Unavailable'))
        page.goto(base + vocab)
        retry = page.locator('#vocab-app > button, #training-app > button')
        retry.wait_for()
        page.unroute('**/static/data/**')
        retry.click()
        page.wait_for_selector('.fc-cell')
        if name == 'english':
            page.goto(base + '/vocab/uscpa/?subject=aud#w100')
            page.wait_for_selector('#w100.flipped')
            assert page.locator('#w100').is_visible()
            assert page.locator('.chip.active').count() == 1
        nojs = browser.new_page(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        nojs.goto(base + '/')
        assert nojs.locator('#main-nav').is_visible()
        assert nojs.locator('.menu-toggle').is_hidden()
        nojs.close()
        print(name + ': desktop/mobile, navigation, search, pagination, deep links, answers, resume and dark mode OK')
        page.close()
    assert not errors, errors
    browser.close()
