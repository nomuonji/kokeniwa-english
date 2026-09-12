"""Intensive reading regression checks. Build and serve dist; override SITE_CHECK_BASE if needed."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import os
import tempfile

root = Path(__file__).resolve().parent.parent
out = Path(tempfile.gettempdir()) / 'kokeniwa-english-reader-review'
out.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    errors = []
    for name, port, source_language in [('english', 8875, 'en')]:
        base = os.environ.get('SITE_CHECK_BASE', f'http://127.0.0.1:{port}').rstrip('/')
        page = browser.new_page(viewport={'width':1440,'height':1000})
        page.route('https://www.googletagmanager.com/**',lambda route: route.abort())
        page.on('pageerror', lambda error: errors.append(str(error)))
        sources = sorted((root/'content/reading').glob('*.json'))
        for source in sources:
            article = json.loads(source.read_text(encoding='utf-8'))
            url = base+'/reading/articles/'+article['slug']+'/'
            page.goto(url)
            page.wait_for_load_state('networkidle')
            text = [s[source_language] for para in article['paragraphs'] for s in para['sentences']]
            assert page.locator('.reading-sentence-line').all_text_contents() == text, ('source text changed',source.name)
            expected = [s['ja' if source_language=='en' else 'en'] for para in article['paragraphs'] for s in para['sentences']]
            assert page.locator('.reading-translation').all_text_contents() == expected
            assert page.locator('.reading-translation:visible').count() == 0
            assert page.locator('.reading-notes[open]').count() == 0
            assert page.locator('.reading-answer[open]').count() == 0
            page.locator('[data-reading-sentence]').first.click()
            assert page.locator('.reading-translation:visible').count() == 1
            page.locator('#reader-translations').click()
            assert page.locator('.reading-translation:visible').count() == len(text)
            page.locator('#reader-translations').click()
            assert page.locator('.reading-translation:visible').count() == 0
            page.locator('.reading-notes > summary').first.click()
            assert page.locator('.reading-notes[open]').count() == 1
            page.locator('[data-paragraph-complete]').first.check()
            assert page.locator('#reader-progress').get_attribute('value') == '1'
            page.reload()
            assert page.locator('[data-paragraph-complete]').first.is_checked()
            assert page.locator('#reader-resume').get_attribute('href') == '#paragraph-2'
            page.locator('[data-paragraph-complete]').first.uncheck()
            for check in page.locator('[data-paragraph-complete]').all(): check.check()
            assert page.locator('#reader-resume').get_attribute('href') == '#study-guide'
            for check in page.locator('[data-paragraph-complete]').all(): check.uncheck()
            if page.locator('#reader-structure').count():
                page.locator('#reader-structure').check()
                assert 'show-structure' in page.locator('.reading-article-shell').get_attribute('class')
                assert page.locator('#structure-help').is_visible()
                page.locator('#reader-structure').uncheck()
            page.locator('#reader-font').select_option('larger')
            page.reload()
            assert page.locator('#reader-font').input_value() == 'larger'
            page.locator('#reader-font').select_option('normal')
            if page.locator('.reading-answer').count():
                page.locator('.reading-answer summary').first.click()
                assert page.locator('.reading-answer[open] p').first.is_visible()
            if page.locator('.guide-topic').count():
                assert page.locator('.guide-topic[open]').count() == 0
                page.locator('.guide-topic > summary').first.click()
                assert page.locator('.guide-topic[open] ul').first.is_visible()
            print(name,source.name,'text, translation, notes, checks and persistence OK',flush=True)
        page.goto(base+'/')
        page.wait_for_load_state('networkidle')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(out/f'{name}-garden-home.png'),full_page=True)
        page.goto(url)
        page.locator('#reader-translations').click()
        page.locator('.reading-notes > summary').first.click()
        page.screenshot(path=str(out/f'{name}-reader-desktop.png'),full_page=True)
        for width in [390,320]:
            page.set_viewport_size({'width':width,'height':844})
            page.goto(base+'/')
            page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(name,width,'home')
            if width==390: page.screenshot(path=str(out/f'{name}-garden-mobile.png'),full_page=True)
            page.goto(url)
            page.locator('#reader-font').select_option('larger')
            if page.locator('#reader-structure').count(): page.locator('#reader-structure').check()
            page.locator('#reader-translations').click()
            page.locator('.reading-notes > summary').first.click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(name,width,'reading')
            if width==390: page.screenshot(path=str(out/f'{name}-reader-mobile.png'),full_page=True)
        page.emulate_media(color_scheme='dark',reduced_motion='reduce')
        page.screenshot(path=str(out/f'{name}-reader-dark.png'),full_page=True)
        nojs=browser.new_page(java_script_enabled=False,viewport={'width':390,'height':844})
        nojs.goto(url)
        nojs.locator('[data-reading-sentence]').first.click()
        assert nojs.locator('.reading-translation:visible').count()==1
        nojs.locator('.reading-notes > summary').first.click()
        assert nojs.locator('.reading-notes[open]').count()==1
        assert nojs.locator('.reader-settings').is_hidden()
        nojs.close()
        blocked=browser.new_page()
        blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new Error('Storage disabled')}})")
        blocked.goto(url)
        blocked.locator('[data-paragraph-complete]').first.check()
        assert blocked.locator('#reader-progress').get_attribute('value')=='1'
        blocked.close()
        page.close()
    assert not errors,errors
    browser.close()
print('All reader and garden checks passed.')
