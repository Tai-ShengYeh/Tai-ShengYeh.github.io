/* =========================================================================
   webr-runner.js — 把頁面上的 <div class="runner"> 變成可執行的 R 主控台
   -------------------------------------------------------------------------
   使用方式（HTML）：
     <div class="runner" data-title="單元 3 練習">
       <textarea>1 + 1</textarea>
     </div>
   會自動加上工具列、執行按鈕、輸出區與繪圖區。

   技術說明：
     使用 webR（R 編譯成 WebAssembly）在瀏覽器裡跑真正的 R。
     GitHub Pages 無法設定 COOP/COEP 標頭，所以固定採用 PostMessage 通道，
     這個通道不需要 SharedArrayBuffer，代價是不支援 readline() 等互動輸入。
   ========================================================================= */

(function () {
  'use strict';

  const WEBR_BASE = window.WEBR_BASE_URL ||
    'https://webr.r-wasm.org/v0.5.4/';
  const ASSET_BASE = window.SALTSR_ASSET_BASE || 'assets/';
  const DATA_BASE  = window.SALTSR_DATA_BASE  || 'data/';

  // 開機時載入到 webR 虛擬檔案系統的資料檔
  const DATA_FILES = [
    'SaltsRExample20C.txt',
    'SaltsR_upload_Example.txt',
    'salt_samples.csv',
    'ECOS_phases.csv'
  ];

  let webR = null;
  let bootPromise = null;
  let statusEl = null;

  // 用 file:// 直接開啟網頁時，瀏覽器會封鎖 fetch()，課程一定載不起來。
  const IS_FILE = location.protocol === 'file:';

  /* ---------------- 載入失敗說明卡 ---------------- */
  function helpCard(title, bodyHTML) {
    let el = document.getElementById('webr-help');
    if (!el) {
      el = document.createElement('div');
      el.id = 'webr-help';
      document.body.appendChild(el);
    }
    el.innerHTML = '<button class="x" type="button" aria-label="關閉">&times;</button>' +
      '<h4>' + title + '</h4>' + bodyHTML;
    el.querySelector('.x').addEventListener('click', () => el.remove());
    return el;
  }

  const FILE_PROTOCOL_HELP =
    '<p>你是用「按兩下 HTML 檔」的方式開啟課程的。瀏覽器基於安全規定，' +
    '不允許這種頁面讀取旁邊的教材檔案，所以 R 環境沒辦法啟動。</p>' +
    '<p><b>解法：用課程附的小型伺服器打開</b></p>' +
    '<ol>' +
    '<li>Windows：在課程資料夾裡按兩下 <code>start-course.bat</code></li>' +
    '<li>macOS：按兩下 <code>start-course.command</code></li>' +
    '<li>或在資料夾裡開終端機執行 <code>python serve.py</code></li>' +
    '</ol>' +
    '<p>接著改用它印出的 <code>http://localhost:8000</code> 這個網址瀏覽即可。' +
    '部署到 GitHub Pages 後也不會有這個問題。</p>';

  const NETWORK_HELP =
    '<p>網頁本身正常，但抓不到 R 執行環境（<code>webr.r-wasm.org</code>）。' +
    '通常是網路連線、校園防火牆或 Proxy 擋掉了。</p>' +
    '<p>可以試試：</p>' +
    '<ol>' +
    '<li>換一個網路（例如手機熱點）再重新整理</li>' +
    '<li>請網管把 <code>webr.r-wasm.org</code> 加進白名單</li>' +
    '<li>把 webR 檔案下載到自己的伺服器，再於頁面設定 ' +
    '<code>window.WEBR_BASE_URL</code> 指向該位置</li>' +
    '</ol>';

  /* ---------------- 狀態列 ---------------- */
  function status(msg, cls) {
    if (!statusEl) {
      statusEl = document.createElement('div');
      statusEl.id = 'webr-status';
      document.body.appendChild(statusEl);
    }
    statusEl.className = cls || '';
    statusEl.innerHTML = (cls === 'ready' || cls === 'err' ? '' : '<i class="spin"></i>') +
      '<span></span>';
    statusEl.querySelector('span').textContent = msg;
    if (cls === 'ready') setTimeout(() => { if (statusEl) statusEl.style.display = 'none'; }, 2600);
    else statusEl.style.display = '';
  }

  /* ---------------- 啟動 webR ---------------- */
  async function boot() {
    if (bootPromise) return bootPromise;
    bootPromise = (async () => {
      if (IS_FILE) {
        const err = new Error(
          '請不要直接按兩下 HTML 檔開啟課程，改用課程附的 serve.py 從 http://localhost 瀏覽。'
        );
        err.saltsrHelp = ['無法在 file:// 下執行 R', FILE_PROTOCOL_HELP];
        throw err;
      }
      status('正在下載 R 執行環境（約 30 MB，第一次比較久）…');
      let mod;
      try {
        mod = await import(WEBR_BASE + 'webr.mjs');
      } catch (e) {
        const err = new Error('連不到 R 執行環境（' + WEBR_BASE + '）。');
        err.saltsrHelp = ['下載 R 環境失敗', NETWORK_HELP];
        err.cause = e;
        throw err;
      }
      const { WebR, ChannelType } = mod;
      webR = new WebR({ baseUrl: WEBR_BASE, channelType: ChannelType.PostMessage });
      await webR.init();

      status('正在載入課程用的 SaltsR 函式…');
      await webR.FS.mkdir('/course').catch(() => {});
      await webR.FS.mkdir('/course/data').catch(() => {});

      const rlib = await (await fetch(ASSET_BASE + 'saltsr_teaching.R')).text();
      await webR.FS.writeFile('/course/saltsr_teaching.R',
        new TextEncoder().encode(rlib));

      await Promise.all(DATA_FILES.map(async (f) => {
        try {
          const buf = await (await fetch(DATA_BASE + f)).arrayBuffer();
          await webR.FS.writeFile('/course/data/' + f, new Uint8Array(buf));
        } catch (e) { console.warn('資料檔載入失敗：', f, e); }
      }));

      const sh = await new webR.Shelter();
      await sh.captureR(`
        setwd("/course")
        source("/course/saltsr_teaching.R")
        options(digits = 7, width = 96, warn = 1)
        DATA <- function(f) file.path("/course/data", f)
      `, { captureStreams: true });
      sh.purge();

      status('R 環境就緒 ✓', 'ready');
      return webR;
    })().catch((e) => {
      status('R 環境載入失敗：' + (e && e.message ? e.message : e), 'err');
      const help = e && e.saltsrHelp;
      if (help) helpCard(help[0], help[1]);
      else if (String(e && e.message).indexOf('Failed to fetch') >= 0) {
        helpCard('下載 R 環境失敗', NETWORK_HELP);
      }
      console.error('[SaltsR] webR 啟動失敗：', e);
      bootPromise = null;
      throw e;
    });
    return bootPromise;
  }

  /* ---------------- 執行單一程式碼區塊 ---------------- */
  async function runCode(code, outEl, plotEl, btn) {
    outEl.textContent = '';
    outEl.style.display = '';
    plotEl.innerHTML = '';
    plotEl.style.display = 'none';
    btn.disabled = true;
    const origLabel = btn.textContent;
    btn.textContent = '執行中…';

    try {
      await boot();
      const shelter = await new webR.Shelter();
      let res;
      try {
        res = await shelter.captureR(code, {
          withAutoprint: true,
          captureStreams: true,
          captureConditions: false,
          captureGraphics: { width: 900, height: 600, bg: 'white' }
        });

        const frag = document.createDocumentFragment();
        res.output.forEach((o) => {
          const span = document.createElement('span');
          if (o.type === 'stderr') span.className = 'err';
          span.textContent = String(o.data) + '\n';
          frag.appendChild(span);
        });
        outEl.appendChild(frag);
        if (!res.output.length) {
          const s = document.createElement('span');
          s.className = 'ok';
          s.textContent = '（執行完成，沒有文字輸出）';
          outEl.appendChild(s);
        }

        if (res.images && res.images.length) {
          plotEl.style.display = '';
          res.images.forEach((img) => {
            const cv = document.createElement('canvas');
            cv.width = img.width; cv.height = img.height;
            cv.style.width = 'min(100%, ' + Math.round(img.width / 2) + 'px)';
            cv.getContext('2d').drawImage(img, 0, 0);
            plotEl.appendChild(cv);
          });
        }
      } finally {
        shelter.purge();
      }
    } catch (e) {
      const s = document.createElement('span');
      s.className = 'err';
      s.textContent = '✗ ' + (e && e.message ? e.message : String(e));
      outEl.appendChild(s);
    } finally {
      btn.disabled = false;
      btn.textContent = origLabel;
    }
  }

  /* ---------------- 把 .runner 元素接上介面 ---------------- */
  function enhance(box) {
    const ta = box.querySelector('textarea');
    if (!ta || box.dataset.ready) return;
    box.dataset.ready = '1';

    const original = ta.value.replace(/^\n+/, '').replace(/\s+$/, '');
    ta.value = original;
    autosize(ta);
    ta.addEventListener('input', () => autosize(ta));
    ta.setAttribute('spellcheck', 'false');
    ta.setAttribute('aria-label', 'R 程式碼編輯區');

    const bar = document.createElement('div');
    bar.className = 'runner-bar';
    bar.innerHTML =
      '<span class="rtitle">' + (box.dataset.title || '在瀏覽器裡執行 R') + '</span>' +
      '<button class="btn btn-run" type="button">▶ 執行</button>' +
      '<button class="btn btn-ghost btn-reset" type="button">↺ 還原</button>' +
      '<button class="btn btn-ghost btn-copy" type="button">⧉ 複製</button>';

    const out = document.createElement('div');
    out.className = 'runner-out';
    out.style.display = 'none';
    const plot = document.createElement('div');
    plot.className = 'runner-plot';
    plot.style.display = 'none';

    box.insertBefore(bar, ta);
    box.appendChild(out);
    box.appendChild(plot);

    const runBtn = bar.querySelector('.btn-run');
    runBtn.addEventListener('click', () => runCode(ta.value, out, plot, runBtn));
    bar.querySelector('.btn-reset').addEventListener('click', () => {
      ta.value = original; autosize(ta);
      out.style.display = 'none'; out.textContent = '';
      plot.style.display = 'none'; plot.innerHTML = '';
    });
    bar.querySelector('.btn-copy').addEventListener('click', (e) => {
      navigator.clipboard.writeText(ta.value).then(() => {
        e.target.textContent = '✓ 已複製';
        setTimeout(() => { e.target.textContent = '⧉ 複製'; }, 1400);
      });
    });

    // Ctrl/Cmd + Enter 執行；Tab 縮排而非跳出欄位
    ta.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); runBtn.click(); }
      if (e.key === 'Tab') {
        e.preventDefault();
        const s = ta.selectionStart, t = ta.selectionEnd;
        ta.value = ta.value.slice(0, s) + '  ' + ta.value.slice(t);
        ta.selectionStart = ta.selectionEnd = s + 2;
      }
    });
  }

  function autosize(ta) {
    ta.style.height = 'auto';
    ta.style.height = Math.min(Math.max(ta.scrollHeight, 70), 620) + 'px';
  }

  /* ---------------- 初始化 ---------------- */
  function init() {
    const boxes = document.querySelectorAll('.runner');
    if (!boxes.length) return;
    boxes.forEach(enhance);

    // file:// 開啟時不必等使用者按執行，一進頁面就把原因和解法講清楚
    if (IS_FILE) {
      status('無法在 file:// 下執行 R —— 請見右側說明', 'err');
      helpCard('無法在 file:// 下執行 R', FILE_PROTOCOL_HELP);
      return;
    }

    // 使用者第一次捲到任何執行區塊附近才開始下載 webR，避免拖慢首次進站
    let started = false;
    const io = new IntersectionObserver((entries) => {
      if (started) return;
      if (entries.some((e) => e.isIntersecting)) {
        started = true; io.disconnect();
        boot().catch(() => {});
      }
    }, { rootMargin: '400px' });
    boxes.forEach((b) => io.observe(b));

    const warm = document.getElementById('webr-warmup');
    if (warm) warm.addEventListener('click', (e) => {
      e.preventDefault(); started = true; io.disconnect(); boot().catch(() => {});
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.SaltsRWebR = { boot, get instance() { return webR; } };
})();
