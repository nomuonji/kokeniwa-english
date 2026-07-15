/* 英単語トレーニング（旧 english-learner「こつこつ英単語」の確認＋ディクテーション）。
   軽量JSONを読み、範囲を選んで学ぶ。依存なし。
   - ?ids=1-50,120 … 出題範囲を指定（投稿連動の受け皿。範囲/個別可）
   - 範囲セレクタ    … ?ids未指定時は50語ずつのバッチを選択
   - 確認モード      … 意味・和訳を伏せて表示、めくって確認
   - ディクテーション … 意味から単語を、和訳から例文を入力して判定（表記一致）
   判定は大文字小文字・記号・スペースを無視。言い換えには非対応。 */
(function () {
  "use strict";

  var app = document.getElementById("training-app");
  if (!app) return;

  var src = app.getAttribute("data-src");
  var BATCH = 50;      // ?ids未指定時の1バッチの語数
  var MAX_IDS = 300;   // URLで一度に読み込む上限

  fetch(src)
    .then(function (r) {
      if (!r.ok) throw new Error("load failed");
      return r.json();
    })
    .then(function (data) { init(data.words || []); })
    .catch(function () {
      app.innerHTML = '<p class="lead">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  // ---------- helpers ----------
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function parseIds() {
    var params = new URLSearchParams(location.search);
    var all = params.getAll("ids");
    var raw = all.length > 1 ? all.join(",") : params.get("ids");
    if (!raw) return null;
    var out = [], seen = {};
    String(raw).split(",").forEach(function (part) {
      part = (part || "").trim();
      if (!part) return;
      var m = part.match(/^(\d+)\s*-\s*(\d+)$/);
      if (m) {
        var a = parseInt(m[1], 10), b = parseInt(m[2], 10);
        var s = Math.min(a, b), e = Math.max(a, b);
        for (var i = s; i <= e; i++) push(i);
      } else {
        var n = parseInt(part, 10);
        if (!isNaN(n)) push(n);
      }
    });
    function push(n) { if (n > 0 && !seen[n]) { seen[n] = 1; out.push(n); } }
    return out.slice(0, MAX_IDS);
  }

  function normalize(s) {
    if (!s) return "";
    return s.normalize("NFKC").toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, "") // 発音記号を除去
      .replace(/[~〜]/g, "")                              // phrasal のプレースホルダ
      .replace(/[^a-z0-9]/gi, "");                        // 記号・スペースを無視
  }
  function isCorrect(ans, expected) { return normalize(ans) === normalize(expected); }

  // ---------- state ----------
  var S = {
    all: [],        // 全語
    words: [],      // 出題対象（working set）
    phase: "review", // "review" | "dict"
    index: 0,
    status: {},     // id -> {reviewDone, wordOk, sentOk, revealMeaning, revealJa}
    batch: 0,       // バッチ番号（?ids未指定時）
    fixed: false,   // ?idsで固定された範囲か
  };

  function init(words) {
    S.all = words;
    var ids = parseIds();
    if (ids && ids.length) {
      var map = {};
      words.forEach(function (w) { map[w.id] = w; });
      S.words = ids.map(function (id) { return map[id]; }).filter(Boolean);
      S.fixed = true;
    }
    if (!S.words.length) {
      S.fixed = false;
      S.words = words.slice(0, BATCH);
    }
    render();

    // ←→ で前後（入力中は無効）
    window.addEventListener("keydown", function (e) {
      var t = (e.target && e.target.tagName) || "";
      if (t === "INPUT" || t === "TEXTAREA") return;
      if (e.key === "ArrowRight") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); move(-1); }
    });
  }

  function st(w) { return (S.status[w.id] = S.status[w.id] || {}); }

  function move(d) {
    S.index = Math.max(0, Math.min(S.words.length - 1, S.index + d));
    render();
  }

  function selectBatch(b) {
    S.batch = b;
    S.words = S.all.slice(b * BATCH, b * BATCH + BATCH);
    S.index = 0;
    S.status = {};
    render();
  }

  // ---------- controls ----------
  function buildControls() {
    var bar = el("div", "tr-controls");

    // 範囲セレクタ（?ids固定時は範囲ラベル）
    var rangeWrap = el("div", "tr-range");
    if (S.fixed) {
      rangeWrap.appendChild(el("span", "tr-range-label", "出題範囲: 指定の" + S.words.length + "語"));
    } else {
      var total = S.all.length;
      var nBatches = Math.ceil(total / BATCH);
      var sel = document.createElement("select");
      sel.className = "tr-select";
      sel.setAttribute("aria-label", "出題範囲");
      for (var b = 0; b < nBatches; b++) {
        var lo = b * BATCH + 1, hi = Math.min((b + 1) * BATCH, total);
        var opt = document.createElement("option");
        opt.value = String(b);
        opt.textContent = lo + "–" + hi + " 語";
        if (b === S.batch) opt.selected = true;
        sel.appendChild(opt);
      }
      sel.addEventListener("change", function () { selectBatch(parseInt(sel.value, 10)); });
      rangeWrap.appendChild(el("span", "tr-range-label", "範囲"));
      rangeWrap.appendChild(sel);
    }
    bar.appendChild(rangeWrap);

    // モードタブ
    var tabs = el("div", "tr-tabs");
    ["review", "dict"].forEach(function (p) {
      var label = p === "review" ? "確認" : "ディクテーション";
      var btn = el("button", "tr-tab" + (S.phase === p ? " active" : ""), label);
      btn.type = "button";
      btn.addEventListener("click", function () { S.phase = p; render(); });
      tabs.appendChild(btn);
    });
    bar.appendChild(tabs);

    return bar;
  }

  function buildProgress() {
    var total = S.words.length || 1;
    var wrap = el("div", "tr-progress");
    wrap.appendChild(el("span", "tr-progress-num",
      (Math.min(S.index + 1, total)) + " / " + total));
    var track = el("div", "tr-progress-track");
    var bar = el("div", "tr-progress-bar");
    bar.style.width = Math.round((S.index / total) * 100) + "%";
    track.appendChild(bar);
    wrap.appendChild(track);
    return wrap;
  }

  // ---------- cards ----------
  function reviewCard(w) {
    var s = st(w);
    var card = el("div", "tr-card");
    card.appendChild(el("div", "tr-word", w.w));

    var mBtn = el("button", "reveal-btn tr-reveal", "意味を表示");
    mBtn.type = "button";
    var meaning = el("div", "tr-reveal-box" + (s.revealMeaning ? " open" : ""), w.m);
    mBtn.addEventListener("click", function () {
      s.revealMeaning = true; meaning.classList.add("open"); mBtn.style.display = "none";
      s.reviewDone = !!(s.revealMeaning && s.revealJa); refreshSidebar();
    });
    if (s.revealMeaning) mBtn.style.display = "none";
    card.appendChild(mBtn);
    card.appendChild(meaning);

    card.appendChild(el("p", "tr-example", esc(w.e)));

    var jBtn = el("button", "reveal-btn tr-reveal ghost", "和訳を表示");
    jBtn.type = "button";
    var ja = el("div", "tr-reveal-box" + (s.revealJa ? " open" : ""), w.ej);
    jBtn.addEventListener("click", function () {
      s.revealJa = true; ja.classList.add("open"); jBtn.style.display = "none";
      s.reviewDone = !!(s.revealMeaning && s.revealJa); refreshSidebar();
    });
    if (s.revealJa) jBtn.style.display = "none";
    card.appendChild(jBtn);
    card.appendChild(ja);

    card.appendChild(pager(function () {
      if (S.index + 1 >= S.words.length) { S.phase = "dict"; S.index = 0; render(); }
      else move(1);
    }));
    return card;
  }

  function dictCard(w) {
    var s = st(w);
    var card = el("div", "tr-card");

    card.appendChild(el("div", "tr-label", "意味"));
    card.appendChild(el("div", "tr-given", w.m));

    var wRow = el("div", "tr-input-row");
    var wInput = document.createElement("input");
    wInput.className = "tr-input"; wInput.type = "text";
    wInput.placeholder = "単語を入力（Enterで判定）"; wInput.autocomplete = "off";
    var wBtn = el("button", "reveal-btn", "判定"); wBtn.type = "button";
    wRow.appendChild(wInput); wRow.appendChild(wBtn);
    card.appendChild(wRow);
    var wRes = el("div", "tr-result"); card.appendChild(wRes);

    function checkWord() {
      var ok = isCorrect(wInput.value.trim(), w.w);
      s.wordOk = ok;
      setResult(wRes, ok, w.w, "単語");
      refreshSidebar();
      if (ok) setTimeout(function () { sInput.focus(); }, 0);
    }
    wBtn.addEventListener("click", checkWord);
    wInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); checkWord(); }
    });

    card.appendChild(el("div", "tr-label", "例文 和訳"));
    card.appendChild(el("div", "tr-given", w.ej));

    var sRow = el("div", "tr-input-row");
    var sInput = document.createElement("textarea");
    sInput.className = "tr-input"; sInput.rows = 2;
    sInput.placeholder = "例文（英語）を入力（Enterで判定）";
    var sBtn = el("button", "reveal-btn", "判定"); sBtn.type = "button";
    sRow.appendChild(sInput); sRow.appendChild(sBtn);
    card.appendChild(sRow);
    var sRes = el("div", "tr-result"); card.appendChild(sRes);

    function checkSent() {
      var ok = isCorrect(sInput.value.trim(), w.e);
      s.sentOk = ok;
      setResult(sRes, ok, w.e, "例文");
      refreshSidebar();
    }
    sBtn.addEventListener("click", checkSent);
    sInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); checkSent(); }
    });

    card.appendChild(pager(function () { move(1); }));
    return card;
  }

  function setResult(box, ok, correct, kind) {
    box.classList.remove("ok", "ng");
    box.classList.add(ok ? "ok" : "ng");
    box.textContent = ok ? "正解！" : "模範解答（" + kind + "）: " + correct;
  }

  function pager(onNext) {
    var row = el("div", "tr-pager");
    var prev = el("button", "tr-nav", "← 前へ"); prev.type = "button";
    prev.addEventListener("click", function () { move(-1); });
    var next = el("button", "tr-nav primary", "次へ →"); next.type = "button";
    next.addEventListener("click", onNext);
    row.appendChild(prev); row.appendChild(next);
    return row;
  }

  // ---------- sidebar ----------
  function buildSidebar() {
    var side = el("aside", "tr-sidebar");
    side.appendChild(el("div", "tr-sidebar-head",
      '対象一覧 <span class="tr-muted">' + S.words.length + '語</span>'));
    side.appendChild(el("div", "tr-legend",
      '<span class="tr-muted">確=確認 / 単=単語 / 文=例文</span>'));
    var list = el("ul", "tr-list");
    S.words.forEach(function (w, i) {
      var s = S.status[w.id] || {};
      var li = el("li", "tr-list-item" + (i === S.index ? " current" : ""),
        '<span class="tr-list-num">' + w.id + '</span>'
        + '<span class="tr-list-word">' + esc(w.w) + '</span>'
        + '<span class="tr-pills">'
        + '<span class="tr-pill' + (s.reviewDone ? " ok" : "") + '">確</span>'
        + '<span class="tr-pill' + (s.wordOk ? " ok" : "") + '">単</span>'
        + '<span class="tr-pill' + (s.sentOk ? " ok" : "") + '">文</span>'
        + '</span>');
      li.addEventListener("click", function () { S.index = i; render(); });
      list.appendChild(li);
    });
    side.appendChild(list);
    return side;
  }

  function refreshSidebar() {
    var old = app.querySelector(".tr-sidebar");
    if (old) old.replaceWith(buildSidebar());
  }

  // ---------- render ----------
  function render() {
    app.innerHTML = "";
    app.appendChild(buildControls());
    app.appendChild(buildProgress());

    var layout = el("div", "tr-layout");
    var main = el("div", "tr-main");
    var w = S.words[S.index];
    if (!w) {
      main.appendChild(el("div", "tr-card", "対象がありません"));
    } else {
      main.appendChild(S.phase === "review" ? reviewCard(w) : dictCard(w));
    }
    layout.appendChild(main);
    layout.appendChild(buildSidebar());
    app.appendChild(layout);

    var cur = app.querySelector(".tr-list-item.current");
    if (cur) cur.scrollIntoView({ block: "nearest" });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
})();
