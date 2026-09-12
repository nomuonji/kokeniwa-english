/* Progressive enhancements; content and study data remain in their existing sources. */
(function () {
  'use strict';
  var ja = document.documentElement.lang === 'ja';
  function node(tag, cls, text) {
    var element = document.createElement(tag);
    if (cls) element.className = cls;
    if (text) element.textContent = text;
    return element;
  }
  var menu = document.querySelector('.menu-toggle');
  var nav = document.getElementById('main-nav');
  var mobile = matchMedia('(max-width: 760px)');
  function setMenu(open) {
    menu.setAttribute('aria-expanded', String(open));
    nav.hidden = mobile.matches && !open;
  }
  function resizeMenu() { menu.hidden = !mobile.matches; setMenu(false); }
  if (menu && nav) {
    resizeMenu();
    mobile.addEventListener('change', resizeMenu);
    menu.addEventListener('click', function () { setMenu(menu.getAttribute('aria-expanded') !== 'true'); });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && mobile.matches && !nav.hidden) { setMenu(false); menu.focus(); }
    });
  }

  // Local navigation history contains page titles/URLs only, never answers.
  var key = 'kokeniwa:last-practice';
  function rememberPractice() {
    if (!/^\/(?:reading\/(?:\d+|articles\/[^/]+)|quiz\/\d+|vocab\/[^/]+|training\/[^/]+)\/$/.test(location.pathname)
        || location.pathname === '/vocab/adult/') return;
    var heading = document.querySelector('h1');
    var translated = document.querySelector('.reading-title-en');
    var title = !ja && translated ? translated.textContent : heading.textContent;
    try { localStorage.setItem(key, JSON.stringify({ path: location.pathname + location.search + location.hash, title: title })); }
    catch (_) { /* Navigation works without storage. */ }
  }
  try {
    if (location.pathname === '/') {
      var saved = JSON.parse(localStorage.getItem(key) || 'null');
      if (saved && typeof saved.path === 'string' && /^\/(reading|vocab|training|quiz)\//.test(saved.path)
          && !saved.path.startsWith('/vocab/adult/')) {
        var resume = node('aside', 'resume-study');
        var link = node('a', '', (ja ? '前回の学習を開く → ' : 'Continue your last practice → ') + saved.title);
        link.href = saved.path;
        resume.append(link, node('small', '', ja ? '前回開いた学習ページ' : 'Your last practice page'));
        document.querySelector('.home-hero').after(resume);
      }
    } else rememberPractice();
  } catch (_) { /* Storage can be disabled. All practice remains available. */ }
  window.addEventListener('hashchange', rememberPractice);

  function searchable(items, anchor, cards) {
    if (!items.length) return;
    var stateKey = 'kokeniwa:view:' + location.pathname + location.search;
    var state = {};
    try { state = JSON.parse(sessionStorage.getItem(stateKey) || '{}'); } catch (_) {}
    if (!state || typeof state !== 'object') state = {};
    var bar = node('div', 'study-tools');
    var label = node('label', '', cards ? (ja ? '表示中の科目・セットを検索' : 'Search this set: word, meaning or reading') : (ja ? 'この一覧を検索' : 'Search this collection'));
    var input = node('input'); input.type = 'search'; input.id = 'study-search'; label.htmlFor = input.id;
    input.placeholder = ja ? 'キーワードを入力' : 'Type a keyword';
    var clear = node('button', '', ja ? 'クリア' : 'Clear'); clear.type = 'button';
    var count = node('p', 'study-count'); count.setAttribute('role', 'status'); count.setAttribute('aria-live', 'polite');
    bar.append(label, input, clear, count); anchor.before(bar);
    var empty = node('p', 'study-empty', ja ? '見つかりませんでした。別の語句を試すか、検索をクリアしてください。' : 'No matches. Try another keyword or clear the search.');
    var end = cards ? anchor : items[items.length - 1].closest('.post-grid, .reading-article-grid') || items[items.length - 1];
    end.after(empty);
    var more = node('button', 'study-more', ja ? 'さらに48件表示する' : 'Show 48 more'); more.type = 'button'; empty.after(more);
    var limit = Number.isInteger(state.limit) ? Math.max(48, Math.min(items.length, state.limit)) : 48;
    input.value = typeof state.query === 'string' ? state.query : '';
    if (cards && !location.hash && Array.isArray(state.flipped)) {
      items.forEach(function (item) { item.classList.toggle('flipped', state.flipped.includes(item.id)); });
    }
    var text = items.map(function (item) { return item.textContent.normalize('NFKC').toLocaleLowerCase(); });
    var groups = cards ? [] : Array.from(document.querySelectorAll('main .post-grid'));
    function save() {
      var view = { query: input.value, limit: limit };
      if (cards) view.flipped = items.filter(function (item) { return item.classList.contains('flipped'); }).map(function (item) { return item.id; });
      try { sessionStorage.setItem(stateKey, JSON.stringify(view)); } catch (_) {}
    }
    function render() {
      var query = input.value.normalize('NFKC').toLocaleLowerCase().trim();
      var matched = 0, shown = 0;
      items.forEach(function (item, index) {
        var match = text[index].includes(query);
        if (match) matched++;
        item.hidden = !match || (cards && matched > limit);
        if (!item.hidden) shown++;
      });
      groups.forEach(function (group) {
        group.hidden = !Array.from(group.children).some(function (item) { return !item.hidden; });
        var heading = group.previousElementSibling;
        if (heading && heading.classList.contains('section-head')) heading.hidden = group.hidden;
      });
      empty.hidden = matched !== 0;
      more.hidden = !cards || shown >= matched;
      count.textContent = ja ? shown + ' / ' + matched + ' 件を表示（全' + items.length + '件）' : shown + ' of ' + matched + ' matches · ' + items.length + ' total';
      save();
      if (cards) anchor.dispatchEvent(new Event('study:visibility', { bubbles: true }));
    }
    input.addEventListener('input', function () { limit = 48; render(); });
    clear.addEventListener('click', function () { input.value = ''; limit = 48; render(); input.focus(); });
    more.addEventListener('click', function () {
      var previous = items.filter(function (item) { return !item.hidden; }).length;
      limit += 48; render();
      var next = items.filter(function (item) { return !item.hidden; })[previous];
      if (next) next.focus({ preventScroll: true });
      if (next) next.scrollIntoView({ block: 'nearest' });
    });
    var target = items.findIndex(function (item) { return '#' + item.id === location.hash; });
    if (cards && target >= 0) { input.value = ''; limit = Math.max(48, target + 1); }
    render();
    return save;
  }
  var lists = Array.from(document.querySelectorAll('main .list-item'));
  if (lists.length) searchable(lists, lists[0], false);
  else if (location.pathname.startsWith('/blog/') && !document.querySelector('.article-body')) {
    var posts = Array.from(document.querySelectorAll('main .post-featured, main .post-grid > .post-card'));
    if (posts.length > 1) searchable(posts, posts[0], false);
  } else {
    var collection = document.querySelector('.reading-article-grid');
    if (collection && collection.children.length > 3) searchable(Array.from(collection.children), collection, false);
  }
  window.enhanceStudyGrid = function (app) {
    var grid = app.querySelector('.fc-grid');
    if (!grid) return;
    var save = searchable(Array.from(grid.children), grid, true);
    function accessibleFaces() {
      grid.querySelectorAll('.fc-cell').forEach(function (cell) {
        var flipped = cell.classList.contains('flipped');
        cell.setAttribute('aria-pressed', String(flipped));
        cell.querySelector('.fc-cell-front').setAttribute('aria-hidden', String(flipped));
        cell.querySelector('.fc-cell-back').setAttribute('aria-hidden', String(!flipped));
        cell.removeAttribute('aria-label');
      });
      var visible = Array.from(grid.querySelectorAll('.fc-cell:not([hidden])'));
      var allFlipped = visible.length > 0 && visible.every(function (cell) { return cell.classList.contains('flipped'); });
      var flip = app.querySelector('.fc-bar button');
      flip.disabled = visible.length === 0;
      flip.setAttribute('aria-pressed', String(allFlipped));
      flip.textContent = ja ? (allFlipped ? '表示中を英単語に戻す' : '表示中の意味を表示') : (allFlipped ? 'Reset visible cards' : 'Reveal visible cards');
      save();
    }
    if (app.studyFaceListener) {
      app.removeEventListener('click', app.studyFaceListener);
      app.removeEventListener('study:visibility', app.studyFaceListener);
    }
    app.studyFaceListener = accessibleFaces;
    app.addEventListener('click', accessibleFaces);
    app.addEventListener('study:visibility', accessibleFaces);
    accessibleFaces();
  };

  var routeKey = 'kokeniwa:question-selection';
  var questionPattern = /^\/(reading|quiz)\/\d+\/$/;
  if (lists.length) {
    lists.forEach(function (link) {
      if (!questionPattern.test(new URL(link.href).pathname)) return;
      link.addEventListener('click', function () {
        var paths = lists.filter(function (item) { return !item.hidden; }).map(function (item) { return new URL(item.href).pathname; });
        var route = { paths: paths, list: location.pathname, title: document.querySelector('h1').textContent };
        try {
          sessionStorage.setItem(routeKey, JSON.stringify(route));
          link.href = new URL(link.href).pathname + '?practice=1';
        } catch (_) { /* Global previous/next links remain a useful fallback. */ }
      });
    });
  } else if (questionPattern.test(location.pathname) && new URLSearchParams(location.search).get('practice') === '1') {
    try {
      var route = JSON.parse(sessionStorage.getItem(routeKey) || 'null');
      var family = '/' + location.pathname.split('/')[1] + '/';
      if (route && Array.isArray(route.paths) && typeof route.list === 'string' && route.list.startsWith(family)
          && route.paths.every(function (path) { return typeof path === 'string' && questionPattern.test(path) && path.startsWith(family); })) {
        var index = route.paths.indexOf(location.pathname);
        var pager = document.querySelector('.pager');
        if (index >= 0 && pager) {
          pager.replaceChildren();
          [[index - 1, 'prev', ja ? '← 前の問題' : '← Previous'], [index + 1, 'next', ja ? '次の問題 →' : 'Next →']].forEach(function (item) {
            if (!route.paths[item[0]]) return;
            var link = node('a', item[1], item[2]);
            link.href = route.paths[item[0]] + '?practice=1';
            pager.appendChild(link);
          });
          var context = node('p', 'question-context');
          context.appendChild(document.createTextNode((index + 1) + ' / ' + route.paths.length + (ja ? ' 問 · ' : ' questions · ')));
          var back = node('a', '', ja ? '選んだ一覧へ戻る' : 'Back to your selection');
          back.href = route.list; context.appendChild(back);
          document.querySelector('.quiz').before(context);
        }
      }
    } catch (_) { /* A shared link without session history uses the default route. */ }
  }

  var body = document.querySelector('.article-body');
  if (body) {
    var headings = Array.from(body.querySelectorAll('h2'));
    if (headings.length > 2 && !document.querySelector('.toc, .article-toc')) {
      var toc = node('details', 'article-toc');
      toc.append(node('summary', '', ja ? 'この記事の目次' : 'On this page'));
      headings.forEach(function (heading, index) {
        if (!heading.id) heading.id = 'article-section-' + index;
        var link = node('a', '', heading.textContent); link.href = '#' + heading.id; toc.append(link);
      });
      body.before(toc);
    }
  }
})();
