/* 語彙フラッシュカード。JSONを読み、科目単位で全語をカードで並べる。依存なし。
   各カードは表(英単語)⇄裏(意味)を個別に反転。全体を一覧しつつ覚えたい語だけめくれる。
   - ?subject=far … 科目チップで切替
   - #w{id}       … 投稿連動。その語の科目を開き、その語のカードへスクロール＆反転
   - カード面は選択不可（casualなコピペ抽出を抑止）。例文はデータに含めない（Kindle版の価値に残す）。 */
(function () {
  "use strict";

  var app = document.getElementById("vocab-app");
  if (!app) return;

  var src = app.getAttribute("data-src");
  var base = app.getAttribute("data-base") || "/vocab/";

  fetch(src)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      init(data);
      // ハッシュだけ変わった場合（同一ページ内遷移）も科目を切り替えて再描画
      window.addEventListener("hashchange", function () { init(data); });
    })
    .catch(function () {
      app.innerHTML = '<p class="lead">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
    });

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function init(data) {
    var subjectKeys = Object.keys(data.subjects);
    var params = new URLSearchParams(location.search);
    var subjectParam = (params.get("subject") || "").toUpperCase();
    var hashMatch = /^#w(\d+)$/.exec(location.hash);
    var targetId = hashMatch ? parseInt(hashMatch[1], 10) : null;

    // 表示する科目（hash優先 → ?subject → 先頭科目）
    var active;
    if (targetId != null) {
      var tw = data.words.filter(function (w) { return w.id === targetId; })[0];
      active = tw ? tw.s : subjectKeys[0];
    } else if (subjectParam && data.subjects[subjectParam]) {
      active = subjectParam;
    } else {
      active = subjectKeys[0];
    }

    app.innerHTML = "";

    // --- 科目チップ ---
    var chips = el("div", "chip-row");
    subjectKeys.forEach(function (key) {
      var meta = data.subjects[key];
      var n = data.words.filter(function (w) { return w.s === key; }).length;
      var a = el("a", "chip" + (key === active ? " active" : ""));
      a.href = base + "?subject=" + meta.slug;
      a.appendChild(document.createTextNode(meta.name + "｜" + meta.ja));
      a.appendChild(el("span", "count", String(n)));
      chips.appendChild(a);
    });
    app.appendChild(chips);

    var words = data.words.filter(function (w) { return w.s === active; });

    // --- 操作バー ---
    var bar = el("div", "fc-bar");
    var flipAllBtn = el("button", "fc-btn", "すべて意味を表示");
    flipAllBtn.type = "button";
    flipAllBtn.setAttribute("aria-pressed", "false");
    bar.appendChild(flipAllBtn);
    bar.appendChild(el("span", "fc-bar-note", "カードをタップで裏返し"));
    app.appendChild(bar);

    // --- カードグリッド ---
    var grid = el("div", "fc-grid");
    words.forEach(function (w) {
      var cell = el("button", "fc-cell");
      cell.type = "button";
      cell.id = "w" + w.id;
      cell.setAttribute("aria-label", w.t + " の意味を表示");

      var inner = el("div", "fc-cell-inner");
      var front = el("div", "fc-cell-face fc-cell-front");
      front.appendChild(el("span", "fc-cell-num", String(w.id)));
      var term = el("span", "fc-cell-term", w.t);
      term.lang = "en";
      front.appendChild(term);

      var back = el("div", "fc-cell-face fc-cell-back");
      back.appendChild(el("span", "fc-cell-num", String(w.id)));
      back.appendChild(el("span", "fc-cell-meaning", w.m));

      inner.appendChild(front);
      inner.appendChild(back);
      cell.appendChild(inner);

      cell.addEventListener("click", function () {
        cell.classList.toggle("flipped");
        var f = cell.classList.contains("flipped");
        cell.setAttribute("aria-label", w.t + (f ? " の表に戻す" : " の意味を表示"));
      });

      grid.appendChild(cell);
    });
    app.appendChild(grid);

    // --- すべて表示/裏返し ---
    var allFlipped = false;
    flipAllBtn.addEventListener("click", function () {
      allFlipped = !allFlipped;
      flipAllBtn.setAttribute("aria-pressed", String(allFlipped));
      flipAllBtn.textContent = allFlipped ? "すべて英単語に戻す" : "すべて意味を表示";
      grid.querySelectorAll(".fc-cell").forEach(function (c) {
        c.classList.toggle("flipped", allFlipped);
      });
    });

    // --- 投稿連動: 該当カードへスクロール＆反転＆強調 ---
    if (targetId != null) {
      var target = document.getElementById("w" + targetId);
      if (target) {
        target.classList.add("flipped", "target");
        target.setAttribute("aria-label", target.getAttribute("aria-label"));
        requestAnimationFrame(function () {
          target.scrollIntoView({ behavior: "smooth", block: "center" });
        });
      }
    }
  }
})();
