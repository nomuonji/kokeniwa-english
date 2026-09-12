(function () {
  'use strict';

  if (!('serviceWorker' in navigator)) return;

  var versionMeta = document.querySelector('meta[name="app-version"]');
  var currentVersion = versionMeta ? versionMeta.content : '';
  var registration;
  var updateShown = false;
  var refreshing = false;
  var japanese = document.documentElement.lang.toLowerCase().startsWith('ja');

  function showUpdate() {
    if (updateShown) return;
    updateShown = true;
    var notice = document.createElement('div');
    notice.className = 'app-update';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    notice.innerHTML = japanese
      ? '<p>新しい内容を利用できます。</p><button type="button">更新する</button>'
      : '<p>A new version is ready.</p><button type="button">Update</button>';
    document.body.appendChild(notice);
    notice.querySelector('button').addEventListener('click', applyUpdate);
  }

  async function applyUpdate(event) {
    var button = event.currentTarget;
    button.disabled = true;
    button.textContent = japanese ? '更新中…' : 'Updating…';
    refreshing = true;
    try {
      if (registration) await registration.update();
      if (registration && registration.waiting) {
        registration.waiting.postMessage({type: 'SKIP_WAITING'});
        window.setTimeout(function () { location.reload(); }, 1800);
      } else {
        location.reload();
      }
    } catch (_) {
      location.reload();
    }
  }

  async function checkVersion() {
    if (!currentVersion || !navigator.onLine) return;
    try {
      var response = await fetch('/version.json?t=' + Date.now(), {cache: 'no-store'});
      if (!response.ok) return;
      var data = await response.json();
      if (data.version && data.version !== currentVersion) showUpdate();
    } catch (_) {
      // Offline use is expected; the cached site remains available.
    }
  }

  navigator.serviceWorker.addEventListener('controllerchange', function () {
    if (refreshing) location.reload();
  });

  window.addEventListener('load', async function () {
    try {
      registration = await navigator.serviceWorker.register('/sw.js', {updateViaCache: 'none'});
      await checkVersion();
    } catch (_) {
      // The website still works when service workers are unavailable.
    }
  });
  window.addEventListener('online', checkVersion);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') checkVersion();
  });
  window.setInterval(checkVersion, 30 * 60 * 1000);
}());
