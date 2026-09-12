"""User-journey regressions. Build and serve dist first; optionally set SITE_CHECK_BASE."""
from pathlib import Path
import json
import os
import tempfile
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent.parent
out=Path(tempfile.gettempdir()) / 'kokeniwa-english-user-journeys'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    errors=[]
    for name,port,vocab in [('english', 8875, '/training/eiken-pre1/')]:
        base=os.environ.get('SITE_CHECK_BASE', f'http://127.0.0.1:{port}').rstrip('/')
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.route('https://www.googletagmanager.com/**',lambda route: route.abort())
        page.on('pageerror',lambda error: errors.append(str(error)))
        page.goto(base+'/blog/')
        page.wait_for_load_state('networkidle')
        posts=page.locator('main .post-featured, main .post-grid > .post-card')
        total=posts.count()
        assert total>3
        for index in [0,total//2,total-1]:
            title=posts.nth(index).locator('.post-title').text_content()
            page.locator('#study-search').fill(title)
            assert posts.nth(index).is_visible(),(name,'missed article',title)
            assert page.locator('main .post-featured:visible, main .post-grid > .post-card:visible').count()==1
        page.locator('#study-search').fill('zzzz-does-not-exist-xxxxx')
        assert page.locator('main .post-featured:visible, main .post-grid > .post-card:visible').count()==0
        assert page.locator('.study-empty').is_visible()
        page.locator('.study-tools button').click()
        assert page.locator('main .post-featured:visible, main .post-grid > .post-card:visible').count()==total
        print(name,'all blog groups and featured article searchable:',total,flush=True)

        page.goto(base+vocab)
        page.wait_for_selector('.fc-cell')
        assert page.locator('.fc-cell:visible').count()==48
        page.locator('.fc-bar button').click()
        assert page.locator('.fc-cell.flipped:visible').count()==48
        page.locator('.study-more').click()
        assert page.locator('.fc-cell:visible').count()==96
        assert page.locator('.fc-bar button').get_attribute('aria-pressed')=='false'
        page.locator('.fc-bar button').click()
        assert page.locator('.fc-cell.flipped:visible').count()==96
        page.reload()
        page.wait_for_selector('.fc-cell')
        assert page.locator('.fc-cell:visible').count()==96
        assert page.locator('.fc-cell.flipped:visible').count()==96
        first_word=page.locator('.fc-cell-term').first.text_content()
        page.locator('#study-search').fill(first_word)
        count=page.locator('.fc-cell:visible').count()
        page.goto(base+'/books/')
        page.go_back()
        page.wait_for_selector('.fc-cell')
        assert page.locator('#study-search').input_value()==first_word
        assert page.locator('.fc-cell:visible').count()==count
        page.locator('#study-search').fill('zzzz-does-not-exist-xxxxx')
        assert page.locator('.fc-bar button').is_disabled()
        page.goto(base+vocab+'#w100')
        page.wait_for_selector('#w100.flipped')
        assert page.locator('#w100').is_visible()
        assert page.locator('#study-search').input_value()==''
        print(name,'card state, mixed bulk flip, no-match and deep-link override OK',flush=True)

        page.goto(base+'/reading/')
        category=page.locator('.chip[href*="/category/"]').first.get_attribute('href')
        page.goto(base+category)
        expected=page.locator('.list-item').evaluate_all('(links)=>links.map(link=>new URL(link.href).pathname)')
        assert len(expected)>1
        page.locator('.list-item').first.click()
        page.wait_for_load_state('networkidle')
        page.locator('.question-context').wait_for()
        assert page.locator('.question-context').is_visible()
        assert page.locator('.pager .next').get_attribute('href')==expected[1]+'?practice=1'
        page.locator('.pager .next').click()
        page.wait_for_url(base+expected[1]+'?practice=1')
        page.wait_for_load_state('networkidle')
        assert page.locator('.question-context').text_content().startswith('2 / '+str(len(expected)))
        page.locator('.question-context a').click()
        page.wait_for_url(base+category)
        assert page.url==base+category
        # The retry must remove answer cues and allow a different choice.
        source=[json.loads(line) for line in (root/'data/reading_problems.jsonl').read_text(encoding='utf-8').splitlines() if line]
        question=next(item for item in source if item['format']=='quiz')
        path='/reading/'+str(question['id'])+'/'
        page.goto(base+path)
        page.locator('.choice').first.click()
        assert page.locator('.quiz-retry').is_visible()
        assert page.locator('.answer-panel.open').is_visible()
        page.locator('.quiz-retry').click()
        assert page.locator('.choice:disabled').count()==0
        assert page.locator('.choice.correct, .choice.wrong, .choice.dim').count()==0
        assert page.locator('.answer-panel.open').count()==0
        page.locator('.choice').nth(question['answer_index']).click()
        assert page.locator('.verdict.ok').is_visible()
        assert page.locator('#announce').count()==0
        print(name,'category sequence, question retry and quiet exercise screens OK',flush=True)

        nojs=browser.new_page(java_script_enabled=False)
        nojs.goto(base+path)
        assert nojs.locator('.answer-panel').is_visible()
        assert nojs.locator('.choices').is_hidden()
        nojs.close()
        for width in [1440,768,390,320]:
            page.set_viewport_size({'width':width,'height':844})
            for path in ['/', '/blog/', '/reading/',vocab,'/books/']:
                page.goto(base+path)
                page.wait_for_load_state('networkidle')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(name,width,path,'overflow')
        page.goto(base+'/blog/')
        page.screenshot(path=str(out/f'{name}-blog-mobile.png'),full_page=True)
        page.close()
    assert not errors,errors
    browser.close()
print('All critical user journeys passed.')
