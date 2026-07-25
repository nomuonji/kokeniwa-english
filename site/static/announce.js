/* アナウンスバー。
 *
 * サーバー側は hidden で出力し、閉じていない場合だけJSで表示する。
 * こうすると「一度表示されてから消える」ちらつきが起きない。
 * 閉じた記録は localStorage に告知IDごとに残すので、
 * layout.py の ANNOUNCE.id を変えれば全員に再表示される。
 */
(function () {
  var el = document.getElementById('announce');
  if (!el) return;

  var id = el.dataset.announceId || 'default';
  var key = 'announce-dismissed:' + id;

  var dismissed = false;
  try {
    dismissed = localStorage.getItem(key) === '1';
  } catch (e) {
    /* プライベートモード等で localStorage が使えない場合は毎回表示する */
  }
  if (dismissed) return;

  el.hidden = false;

  var btn = el.querySelector('.announce-close');
  if (!btn) return;
  btn.addEventListener('click', function () {
    el.hidden = true;
    try {
      localStorage.setItem(key, '1');
    } catch (e) {
      /* 保存できなくても閉じる動作自体は成立させる */
    }
  });
})();
