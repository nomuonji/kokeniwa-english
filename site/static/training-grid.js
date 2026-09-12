/* 英単語トレーニング（一覧フラッシュカード）。JSONを読み、全語をカードで並べる。依存なし。
   USCPA/法律の語彙と同じUI。各カードは表(英単語)⇄裏(意味)を個別に反転。
   - #w{id} … 投稿連動の受け皿。その語のカードへスクロール＆反転＆強調
   - カード面は選択不可（casualなコピペ抽出を抑止）。 */
(function () {
  "use strict";

  var app = document.getElementById("training-app");
  if (!app) return;

  var src = app.getAttribute("data-src");

  function load() {
  app.innerHTML = '<p class="lead" role="status">読み込み中…</p>';
  fetch(src)
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      init(data.words || []);
      // ハッシュだけ変わった場合（同一ページ内遷移）も再描画
      window.addEventListener("hashchange", function () { init(data.words || []); });
    })
    .catch(function () {
      app.innerHTML = '<p class="lead">データの読み込みに失敗しました。時間をおいて再度お試しください。</p>';
      var retry = el("button", "fc-btn", "再読み込み");
      retry.type = "button"; retry.addEventListener("click", load); app.appendChild(retry);
    });
  }
  load();

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function init(words) {
    var hashMatch = /^#w(\d+)$/.exec(location.hash);
    var targetId = hashMatch ? parseInt(hashMatch[1], 10) : null;

    app.innerHTML = "";

    // --- 操作バー ---
    var bar = el("div", "fc-bar");
    var flipAllBtn = el("button", "fc-btn", "表示中の意味を表示");
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
      allFlipped = !Array.from(grid.querySelectorAll(".fc-cell:not([hidden])")).every(function (cell) { return cell.classList.contains("flipped"); });
      flipAllBtn.setAttribute("aria-pressed", String(allFlipped));
      flipAllBtn.textContent = allFlipped ? "表示中を英単語に戻す" : "表示中の意味を表示";
      grid.querySelectorAll(".fc-cell:not([hidden])").forEach(function (c) {
        c.classList.toggle("flipped", allFlipped);
      });
    });

    // --- 投稿連動: 該当カードへスクロール＆反転＆強調 ---
    if (targetId != null) {
      var target = document.getElementById("w" + targetId);
      if (target) {
        target.classList.add("flipped", "target");
        requestAnimationFrame(function () {
          target.scrollIntoView({ behavior: "smooth", block: "center" });
        });
      }
    }
    if (window.enhanceStudyGrid) window.enhanceStudyGrid(app);
  }
})();
