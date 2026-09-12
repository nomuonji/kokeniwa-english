/* クイズ・訳表示・語彙の意味隠し。依存ライブラリなし。 */
(function () {
  "use strict";

  // --- 選択式クイズ ---------------------------------------------------
  document.querySelectorAll("[data-quiz]").forEach(function (quiz) {
    var answer = parseInt(quiz.getAttribute("data-answer"), 10);
    var choices = quiz.querySelectorAll(".choice");
    var verdict = quiz.querySelector(".verdict");
    var panel = quiz.querySelector(".answer-panel");
    var done = false;
    var retry = document.createElement("button");
    retry.type = "button";
    retry.className = "quiz-retry";
    retry.textContent = "もう一度解く";
    retry.hidden = true;
    if (verdict) verdict.after(retry);
    else quiz.appendChild(retry);
    retry.addEventListener("click", function () {
      done = false;
      choices.forEach(function (button) {
        button.disabled = false;
        button.classList.remove("correct", "wrong", "dim");
      });
      if (verdict) { verdict.textContent = ""; verdict.classList.remove("ok", "ng"); }
      if (panel) panel.classList.remove("open");
      retry.hidden = true;
      choices[0].focus({ preventScroll: true });
    });

    choices.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (done) return;
        done = true;
        var picked = parseInt(btn.getAttribute("data-index"), 10);
        choices.forEach(function (b) {
          b.disabled = true;
          var i = parseInt(b.getAttribute("data-index"), 10);
          if (i === answer) {
            b.classList.add("correct");
          } else if (i === picked) {
            b.classList.add("wrong");
          } else {
            b.classList.add("dim");
          }
        });
        if (verdict) {
          if (picked === answer) {
            verdict.textContent = "正解です。";
            verdict.classList.add("ok");
          } else {
            verdict.textContent = "正解は「" +
              choices[answer].querySelector(".label").textContent + "」";
            verdict.classList.add("ng");
          }
        }
        if (panel) panel.classList.add("open");
        retry.hidden = false;
        retry.focus({ preventScroll: true });
      });
    });
  });

  // --- 「訳と解説を表示」ボタン ----------------------------------------
  document.querySelectorAll("[data-reveal]").forEach(function (btn) {
    var target = document.getElementById(btn.getAttribute("data-reveal"));
    if (!target) return;
    var original = btn.textContent;
    btn.setAttribute("aria-controls", target.id);
    btn.setAttribute("aria-expanded", "false");
    btn.addEventListener("click", function () {
      var open = target.classList.toggle("open");
      btn.setAttribute("aria-expanded", String(open));
      btn.textContent = open ? "全文訳を隠す" : original;
    });
  });

})();
