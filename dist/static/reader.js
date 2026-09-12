/* Personal reading preferences and paragraph checks. No content is written. */
(function () {
  'use strict';
  const reader = document.querySelector('.reading-article-shell');
  if (!reader) return;
  const ja = document.documentElement.lang === 'ja';
  const translations = [...reader.querySelectorAll('.sentence-translation')];
  const checks = [...reader.querySelectorAll('[data-paragraph-complete]')];
  const size = document.getElementById('reader-font');
  const structure = document.getElementById('reader-structure');
  const all = document.getElementById('reader-translations');
  const progress = document.getElementById('reader-progress');
  const status = document.getElementById('reader-progress-text');
  const resume = document.getElementById('reader-resume');
  const settingsKey = 'kokeniwa:reading-settings';
  const progressKey = 'kokeniwa:reading-progress:' + location.pathname;
  let storageAvailable = true;
  function read(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; }
    catch (_) { storageAvailable = false; return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch (_) { storageAvailable = false; }
    storageNote();
  }
  function storageNote() {
    if (!storageAvailable) {
      reader.querySelector('.reader-storage-note').textContent = ja
        ? 'このブラウザでは保存できません。チェックはこのページを開いている間だけ使えます。'
        : 'Storage is unavailable. Your checks work for this visit but will not be saved.';
    }
  }
  const settings = read(settingsKey, {});
  const saved = read(progressKey, []);
  size.value = ['normal', 'large', 'larger'].includes(settings.size) ? settings.size : 'normal';
  if (structure) structure.checked = settings.structure === true;
  checks.forEach(check => { check.checked = Array.isArray(saved) && saved.includes(check.dataset.paragraphComplete); });
  function updateSettings(save) {
    reader.dataset.font = size.value;
    const enabled = Boolean(structure && structure.checked);
    reader.classList.toggle('show-structure', enabled);
    document.getElementById('structure-help').hidden = !enabled;
    if (save) write(settingsKey, { size: size.value, structure: enabled });
  }
  function updateProgress(save) {
    const done = checks.filter(check => check.checked);
    progress.value = done.length;
    status.textContent = ja ? done.length + ' / ' + checks.length + ' 段落を確認' : done.length + ' / ' + checks.length + ' paragraphs understood';
    checks.forEach(check => check.closest('.reading-study-block').classList.toggle('is-understood', check.checked));
    const next = checks.find(check => !check.checked);
    resume.href = next ? '#paragraph-' + next.dataset.paragraphComplete : '#study-guide';
    resume.textContent = next ? (ja ? '段落 ' + next.dataset.paragraphComplete + ' へ ↓' : 'Paragraph ' + next.dataset.paragraphComplete + ' ↓')
      : (ja ? '理解チェックへ ↓' : 'Review questions ↓');
    if (save) write(progressKey, done.map(check => check.dataset.paragraphComplete));
  }
  function updateTranslations() {
    const opened = translations.every(detail => detail.open);
    all.setAttribute('aria-pressed', String(opened));
    all.textContent = ja ? (opened ? 'すべての訳を閉じる' : 'すべての訳を開く') : (opened ? 'Close all translations' : 'Open all translations');
    translations.forEach(detail => detail.querySelector('summary').setAttribute('aria-expanded', String(detail.open)));
  }
  all.addEventListener('click', () => {
    const open = !translations.every(detail => detail.open);
    translations.forEach(detail => { detail.open = open; });
    updateTranslations();
  });
  translations.forEach(detail => detail.addEventListener('toggle', updateTranslations));
  size.addEventListener('change', () => updateSettings(true));
  if (structure) structure.addEventListener('change', () => updateSettings(true));
  checks.forEach(check => check.addEventListener('change', () => updateProgress(true)));
  updateSettings(false);
  updateProgress(false);
  updateTranslations();
  storageNote();
  reader.querySelectorAll('[data-reader-enhancement]').forEach(element => { element.hidden = false; });
})();
