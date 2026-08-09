/* =========================================================================
   offline.js — 註冊 Service Worker，並提供「離線準備」介面
   -------------------------------------------------------------------------
   給學生的使用情境：
     在家（網路正常）進到課程首頁 → 按一次「準備離線使用」→ 等進度跑完
     → 上課時就算完全沒網路，整套課程與 R 都還能用。

   只在 https:// 或 localhost 下有效（Service Worker 的安全性限制），
   用 file:// 開啟時整段會安靜地不做事。
   ========================================================================= */

(function () {
  'use strict';

  const SUPPORTED = ('serviceWorker' in navigator) &&
    (location.protocol === 'https:' || /^(localhost|127\.0\.0\.1)$/.test(location.hostname));

  const MB = (n) => (n / 1048576).toFixed(1) + ' MB';

  let reg = null;
  let ui  = null;

  /* ---------------- 介面 ---------------- */
  function panel() {
    if (ui) return ui;
    ui = document.createElement('div');
    ui.id = 'offline-panel';
    ui.innerHTML =
      '<div class="op-head">' +
        '<b>離線使用</b>' +
        '<span class="op-state">檢查中…</span>' +
      '</div>' +
      '<p class="op-desc">把整套課程與 R 執行環境存進這台電腦的瀏覽器，' +
        '之後沒有網路也能上課。建議在家或網路順暢時先做一次。</p>' +
      '<div class="op-bar"><i></i></div>' +
      '<div class="op-actions">' +
        '<button type="button" class="btn btn-teal op-go">準備離線使用</button>' +
        '<button type="button" class="btn btn-ghost op-clear">清除</button>' +
      '</div>';
    return ui;
  }

  // 只有放了 <div id="offline-slot"> 的頁面（課程入口）才顯示面板，
  // 其他頁面單純把 Service Worker 註冊起來就好。
  function mount() {
    const host = document.getElementById('offline-slot');
    if (!host) return null;
    const p = panel();
    if (!p.isConnected) host.appendChild(p);
    return p;
  }

  function setState(txt, cls) {
    const el = ui && ui.querySelector('.op-state');
    if (el) { el.textContent = txt; el.className = 'op-state' + (cls ? ' ' + cls : ''); }
  }

  function setBar(pct) {
    const el = ui && ui.querySelector('.op-bar i');
    if (el) el.style.width = Math.max(0, Math.min(100, pct)) + '%';
  }

  /* ---------------- 與 Service Worker 溝通 ---------------- */
  function send(msg) {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage(msg);
    } else if (reg && reg.active) {
      reg.active.postMessage(msg);
    }
  }

  function onMessage(e) {
    const m = e.data || {};
    const files = window.SALTSR_WEBR_FILES || [];
    const totalBytes = window.SALTSR_WEBR_BYTES || 0;

    if (m.type === 'STATUS') {
      if (m.webrCached >= files.length && files.length > 0) {
        setState('已可離線使用 ✓', 'ok');
        setBar(100);
      } else if (m.webrCached > 0) {
        setState('部分完成（' + m.webrCached + '/' + files.length + '）', 'warn');
        setBar(m.webrCached / files.length * 100);
      } else {
        setState('尚未準備', '');
        setBar(0);
      }
    }

    if (m.type === 'PROGRESS') {
      setState('下載中 ' + m.done + '/' + m.total + '（' + MB(m.bytes) + '）', 'warn');
      setBar(m.done / m.total * 100);
    }

    if (m.type === 'DONE') {
      if (m.failed > 0) {
        setState('完成，但有 ' + m.failed + ' 個檔案失敗，請再按一次', 'warn');
      } else {
        setState('已可離線使用 ✓（' + MB(m.bytes) + '）', 'ok');
        setBar(100);
      }
      const btn = ui && ui.querySelector('.op-go');
      if (btn) { btn.disabled = false; btn.textContent = '重新檢查'; }
    }

    if (m.type === 'CLEARED') {
      setState('已清除', '');
      setBar(0);
    }
  }

  /* ---------------- 啟動 ---------------- */
  async function init() {
    if (!SUPPORTED) return;

    const p = mount();

    navigator.serviceWorker.addEventListener('message', onMessage);

    try {
      reg = await navigator.serviceWorker.register('sw.js', { scope: './' });
      await navigator.serviceWorker.ready;
    } catch (e) {
      setState('這個瀏覽器不支援離線功能', 'warn');
      console.warn('[offline] 註冊失敗', e);
      return;
    }

    if (!p) return;   // 這一頁不顯示面板，註冊完就結束

    const desc = p.querySelector('.op-desc');
    if (window.SALTSR_WEBR_BYTES) {
      desc.textContent += '（需要約 ' + MB(window.SALTSR_WEBR_BYTES) + ' 的空間）';
    }

    // 這份部署到底有沒有附 webR？沒有的話按下去只會失敗上百次，
    // 不如一開始就講清楚。
    let hasLocalWebr = false;
    try {
      const r = await fetch('webr/webr.mjs', { cache: 'no-store' });
      hasLocalWebr = r.ok;
    } catch (e) { hasLocalWebr = false; }

    if (!hasLocalWebr) {
      setState('這份課程沒有附 R 環境', 'warn');
      desc.textContent =
        '這個網站沒有附帶 R 執行環境（webr/ 資料夾），所以無法離線使用 —— ' +
        '每次執行 R 都需要連上網路。若你是授課教師，部署時加上 ' +
        '-WithWebR（PowerShell）或 --with-webr（bash）就會一併上線。';
      const go = p.querySelector('.op-go');
      go.disabled = true;
      go.textContent = '無法離線使用';
      p.querySelector('.op-clear').style.display = 'none';
      return;
    }

    send({ type: 'STATUS' });

    p.querySelector('.op-go').addEventListener('click', (ev) => {
      const files = (window.SALTSR_WEBR_FILES || []).map((f) => 'webr/' + f);
      if (!files.length) { setState('找不到檔案清單', 'warn'); return; }
      ev.target.disabled = true;
      ev.target.textContent = '下載中…';
      setState('準備中…', 'warn');
      send({ type: 'CACHE_WEBR', files: files });
    });

    p.querySelector('.op-clear').addEventListener('click', () => {
      send({ type: 'CLEAR' });
    });

    // 回到線上／離線時更新提示
    window.addEventListener('offline', () => setState('目前離線中', 'warn'));
    window.addEventListener('online',  () => send({ type: 'STATUS' }));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
