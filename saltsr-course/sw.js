/* =========================================================================
   sw.js — SaltsR 課程的 Service Worker
   -------------------------------------------------------------------------
   目的：讓學生在家（有網路時）開一次課程網站，把整套教材與 R 執行環境
         存進瀏覽器快取；之後即使教室完全沒網路，課程照樣能開、R 照樣能跑。

   設計重點：
     * 課程外殼（HTML/CSS/JS/資料）在安裝時就抓好，很小，秒完成。
     * R 執行環境（webr/，數十 MB）不在安裝階段抓，避免第一次進站就卡住。
       改由頁面上的「離線準備」按鈕明確觸發，學生看得到進度。
     * 取用策略：先看快取，沒有才走網路（stale-while-revalidate 的簡化版）。
       教材是靜態的，這樣最快也最耐斷網。
   ========================================================================= */

// BUILD 由部署腳本在每次上線時改寫，用來讓「課程內容」的快取自動更新。
// R 執行環境的快取用另一組名字（跟著 webR 版本走），所以更新講義不會害
// 學生重抓 45 MB。
const BUILD      = '20260809120213';
const WEBR_VER   = '0.5.4';
const SHELL      = 'saltsr-shell-' + BUILD;
const WEBR       = 'saltsr-webr-' + WEBR_VER;
const KEEP       = [SHELL, WEBR];

// 課程外殼：安裝時就要有的東西
const SHELL_FILES = [
  './',
  './index.html',
  './lesson.html',
  './lab.html',
  './quiz.html',
  './assets/course.css',
  './assets/webr-runner.js',
  './assets/salt_engine.js',
  './assets/labs.js',
  './assets/quiz.js',
  './assets/offline.js',
  './assets/saltsr_teaching.R',
  './data/salt_samples.csv',
  './data/salt_balance_full.csv',
  './data/ECOS_phases.csv',
  './data/SaltsRExample20C.txt',
  './data/SaltsR_upload_Example.txt',
  './scripts/install_saltsr.R',
  './scripts/unit01_basics.R',
  './scripts/unit02_vectors.R',
  './scripts/unit03_weight.R',
  './scripts/unit04_equivalents.R',
  './scripts/unit05_balance.R',
  './scripts/unit06_gypsum.R',
  './scripts/unit07_runsalt.R',
  './scripts/unit08_plot.R',
  './scripts/unit09_batch.R'
];

/* ---------------- 安裝：抓課程外殼 ---------------- */
self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    // 逐個抓，單一檔案失敗不要讓整個安裝失敗（例如教師版沒部署）
    await Promise.all(SHELL_FILES.map(async (f) => {
      try { await c.add(new Request(f, { cache: 'reload' })); }
      catch (err) { console.warn('[sw] 略過', f, err); }
    }));
    self.skipWaiting();
  })());
});

/* ---------------- 啟用：清掉舊版本 ---------------- */
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.map((n) => {
      if (n.startsWith('saltsr-') && !KEEP.includes(n)) return caches.delete(n);
    }));
    await self.clients.claim();
  })());
});

/* ---------------- 取用：快取優先 ---------------- */
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' && req.method !== 'HEAD') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // 外部資源（例如字型）不管

  e.respondWith((async () => {
    // ignoreMethod：讓 HEAD 也能命中已快取的 GET 回應，否則離線時探測一定失敗
    const hit = await caches.match(req, { ignoreSearch: true, ignoreMethod: true });
    if (hit) return hit;

    try {
      const res = await fetch(req);
      // 順手把 webr/ 底下抓到的東西存起來，讓「邊用邊快取」也能生效
      if (res && res.ok && url.pathname.includes('/webr/')) {
        const c = await caches.open(WEBR);
        c.put(req, res.clone());
      }
      return res;
    } catch (err) {
      // 斷網又沒快取：導覽請求就回首頁，其餘照實失敗
      if (req.mode === 'navigate') {
        const idx = await caches.match('./index.html');
        if (idx) return idx;
      }
      throw err;
    }
  })());
});

/* ---------------- 與頁面溝通：下載 R 環境 ---------------- */
self.addEventListener('message', (e) => {
  const msg = e.data || {};

  if (msg.type === 'CACHE_WEBR') {
    e.waitUntil(cacheWebr(msg.files || [], e.source));
  }

  if (msg.type === 'STATUS') {
    e.waitUntil((async () => {
      const c = await caches.open(WEBR);
      const keys = await c.keys();
      const shell = await caches.open(SHELL);
      const skeys = await shell.keys();
      reply(e.source, { type: 'STATUS', webrCached: keys.length, shellCached: skeys.length });
    })());
  }

  if (msg.type === 'CLEAR') {
    e.waitUntil((async () => {
      await caches.delete(WEBR);
      reply(e.source, { type: 'CLEARED' });
    })());
  }
});

function reply(client, data) {
  if (client && client.postMessage) client.postMessage(data);
}

async function cacheWebr(files, client) {
  const c = await caches.open(WEBR);
  let done = 0, bytes = 0, failed = 0;
  const total = files.length;

  // 一次抓幾個就好，免得把學生家裡的網路塞爆
  const CONCURRENCY = 6;
  let idx = 0;

  async function worker() {
    while (idx < files.length) {
      const f = files[idx++];
      try {
        const existing = await c.match(f);
        if (existing) {
          const b = await existing.clone().blob();
          bytes += b.size;
        } else {
          const res = await fetch(f, { cache: 'reload' });
          if (!res.ok) throw new Error('HTTP ' + res.status);
          const buf = await res.clone().arrayBuffer();
          bytes += buf.byteLength;
          await c.put(f, res);
        }
      } catch (err) {
        failed++;
        console.warn('[sw] 快取失敗', f, err);
      }
      done++;
      if (done % 3 === 0 || done === total) {
        reply(client, { type: 'PROGRESS', done, total, bytes, failed });
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, worker));
  reply(client, { type: 'DONE', done, total, bytes, failed });
}
