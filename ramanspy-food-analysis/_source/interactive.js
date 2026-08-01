/* ============================================================
   互動元件（Chart.js）
   資料來自 data.js：合成純物質光譜、真實摻偽劑量曲線、PLS 交叉驗證結果
   ============================================================ */
(function () {
  var R = window.RAMAN;
  if (!R) { console.error('data.js 未載入'); return; }
  var AX = R.axis, N = AX.length;

  var COL = { teal: '#0E7C7B', coral: '#E36414', gold: '#C8941F', violet: '#6A4C93',
              ink: '#1A1A1A', grey: '#A9A092', line: '#D9D2BE' };

  /* ---------- 小工具 ---------- */
  function zeros() { var a = new Array(N); for (var i = 0; i < N; i++) a[i] = 0; return a; }
  function mix(w) {
    var y = zeros();
    for (var k in w) { var c = R[k]; if (!c) continue;
      for (var i = 0; i < N; i++) y[i] += w[k] * c[i]; }
    return y;
  }
  function minmax(y) {
    var lo = Math.min.apply(null, y), hi = Math.max.apply(null, y), d = hi - lo || 1;
    return y.map(function (v) { return (v - lo) / d; });
  }
  function at(y, wn) {   // 取某個波數的強度
    var best = 0, bd = 1e9;
    for (var i = 0; i < N; i++) { var d = Math.abs(AX[i] - wn); if (d < bd) { bd = d; best = i; } }
    return y[best];
  }
  function fwhm(y, wn) {          // 峰的半高寬：平滑過頭時它會變胖
    var c = 0, bd = 1e9, i;
    for (i = 0; i < N; i++) { var d = Math.abs(AX[i] - wn); if (d < bd) { bd = d; c = i; } }
    for (i = Math.max(1, c - 4); i <= Math.min(N - 2, c + 4); i++) if (y[i] > y[c]) c = i;
    var w = 18, lo = Infinity;                       // 以峰兩側 ±72 cm⁻¹ 的最低點當局部基線
    for (i = Math.max(0, c - w); i <= Math.min(N - 1, c + w); i++) if (y[i] < lo) lo = y[i];
    var half = lo + (y[c] - lo) / 2;
    if (!(y[c] > half)) return 0;
    var L = c, Rr = c;
    while (L > 0 && y[L] > half) L--;
    while (Rr < N - 1 && y[Rr] > half) Rr++;
    return Math.abs(AX[Rr] - AX[L]);
  }
  function pts(y) { var o = new Array(N); for (var i = 0; i < N; i++) o[i] = { x: AX[i], y: y[i] }; return o; }

  // 固定亂數（每次重繪的雜訊形狀一樣，才看得出參數的影響）
  var NOISE = (function () { var s = 42, a = []; for (var i = 0; i < N; i++) {
      s = (s * 1103515245 + 12345) % 2147483648; a.push(s / 2147483648 * 2 - 1); } return a; })();

  // 螢光背景（與 Notebook 中模擬儀器輸出的公式相同）
  var BG = (function () { var a = []; for (var i = 0; i < N; i++) {
      var t = (AX[i] - AX[0]) / (AX[N - 1] - AX[0]);
      a.push(0.9 * Math.exp(-2.2 * t) + 0.5 * t * t + 0.25); } return a; })();

  // Savitzky–Golay（係數由 Python 預先算好，polyorder = 3）
  function savgol(y, w) {
    var c = R.sg[String(w)]; if (!c) return y.slice();
    var h = (w - 1) / 2, o = new Array(N);
    for (var i = 0; i < N; i++) { var s = 0;
      for (var j = -h; j <= h; j++) { var k = Math.min(N - 1, Math.max(0, i + j)); s += c[j + h] * y[k]; }
      o[i] = s; }
    return o;
  }

  // ModPoly 基線校正：反覆用多項式擬合，每輪只保留「低於擬合線」的部分
  function polyfit(x, y, deg) {
    var m = deg + 1, A = [], i, j, k;
    for (i = 0; i < m; i++) { A.push(new Array(m + 1).fill(0)); }
    for (i = 0; i < m; i++) {
      for (j = 0; j < m; j++) { var s = 0; for (k = 0; k < x.length; k++) s += Math.pow(x[k], i + j); A[i][j] = s; }
      var t = 0; for (k = 0; k < x.length; k++) t += Math.pow(x[k], i) * y[k]; A[i][m] = t;
    }
    for (i = 0; i < m; i++) {                       // 高斯消去
      var p = i; for (k = i + 1; k < m; k++) if (Math.abs(A[k][i]) > Math.abs(A[p][i])) p = k;
      var tmp = A[i]; A[i] = A[p]; A[p] = tmp;
      if (Math.abs(A[i][i]) < 1e-12) continue;
      for (k = i + 1; k < m; k++) { var f = A[k][i] / A[i][i];
        for (j = i; j <= m; j++) A[k][j] -= f * A[i][j]; }
    }
    var c = new Array(m).fill(0);
    for (i = m - 1; i >= 0; i--) { var v = A[i][m];
      for (j = i + 1; j < m; j++) v -= A[i][j] * c[j];
      c[i] = Math.abs(A[i][i]) < 1e-12 ? 0 : v / A[i][i]; }
    return c;
  }
  var XN = AX.map(function (v) { return (v - AX[0]) / (AX[N - 1] - AX[0]) * 2 - 1; });
  function baselineCorrect(y) {
    var work = y.slice(), c, fit, i, it;
    for (it = 0; it < 22; it++) {
      c = polyfit(XN, work, 5);
      fit = XN.map(function (xv) { var s = 0; for (var d = 0; d < c.length; d++) s += c[d] * Math.pow(xv, d); return s; });
      for (i = 0; i < N; i++) work[i] = Math.min(work[i], fit[i]);
    }
    return y.map(function (v, i2) { return v - fit[i2]; });
  }

  function chart(id, cfg) {
    var el = document.getElementById(id); if (!el) return null;
    return new Chart(el.getContext('2d'), cfg);
  }
  var BASE_OPTS = {
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: 'nearest', intersect: false },
    plugins: { legend: { labels: { font: { size: 12, weight: 700 }, boxWidth: 14 } } },
    elements: { point: { radius: 0 }, line: { borderWidth: 2, tension: 0 } },
    scales: {
      x: { type: 'linear', title: { display: true, text: '拉曼位移 (cm⁻¹)', font: { size: 12, weight: 700 } },
           grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } },
      y: { title: { display: true, text: '強度 (a.u.)', font: { size: 12, weight: 700 } },
           grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } }
    }
  };
  function opts(extra) { return Object.assign(JSON.parse(JSON.stringify(BASE_OPTS)), extra || {}); }
  function bind(id, fn) { var e = document.getElementById(id); if (e) { e.addEventListener('input', fn); } return e; }
  function setTxt(id, v) { var e = document.getElementById(id); if (e) e.textContent = v; }

  /* ============================================================
     互動 1：合成光譜實驗室
     ============================================================ */
  var ASSIGN = [
    [478, '澱粉'], [583, '三聚氰胺'], [676, '三聚氰胺'], [850, '醣類'], [984, '三聚氰胺'],
    [1003, '蛋白質（苯丙胺酸）'], [1008, '類胡蘿蔔素'], [1063, '油脂'], [1085, '醣類'],
    [1125, '醣類'], [1156, '類胡蘿蔔素'], [1240, '蛋白質（醯胺 III）'], [1265, '油脂（不飽和）'],
    [1301, '油脂'], [1340, '蛋白質'], [1380, '澱粉'], [1441, '油脂（CH₂）'], [1460, '醣類'],
    [1523, '類胡蘿蔔素'], [1655, '蛋白質醯胺 I／油脂 C=C'], [1745, '油脂（酯 C=O）']
  ];
  function assignOf(wn) {
    var best = null, bd = 14;
    ASSIGN.forEach(function (a) { var d = Math.abs(a[0] - wn); if (d < bd) { bd = d; best = a; } });
    return best;
  }
  var cMix = chart('cvMix', { type: 'line', data: { datasets: [{ label: '混合光譜', data: [], borderColor: COL.teal, fill: false }] }, options: opts() });
  function updMix() {
    if (!cMix) return;
    var w = {}, ids = { lactose: 'mLac', casein: 'mCas', starch: 'mSta', tg_base: 'mOil', carotene: 'mCar', melamine: 'mMel' };
    for (var k in ids) { var e = document.getElementById(ids[k]); w[k] = e ? (+e.value) / 100 : 0;
      setTxt(ids[k] + 'v', (e ? e.value : 0) + '%'); }
    var y = minmax(mix(w));
    cMix.data.datasets[0].data = pts(y); cMix.update();
    // 找峰並標註歸屬
    var found = [];
    for (var i = 2; i < N - 2; i++) {
      if (y[i] > 0.13 && y[i] >= y[i - 1] && y[i] > y[i + 1] && y[i] - Math.min(y[i - 2], y[i + 2]) > 0.05) {
        var a = assignOf(AX[i]);
        if (a && !found.some(function (f) { return f.wn === a[0]; })) found.push({ wn: a[0], name: a[1], h: y[i] });
      }
    }
    found.sort(function (p, q) { return q.h - p.h; });
    var box = document.getElementById('mixPeaks');
    if (box) {
      box.innerHTML = found.length
        ? found.slice(0, 8).map(function (f) {
            return '<div><b>' + f.wn + '</b><span>' + f.name + '</span></div>'; }).join('')
        : '<div><b>—</b><span>把任一個成分拉上去看看</span></div>';
    }
  }
  ['mLac', 'mCas', 'mSta', 'mOil', 'mCar', 'mMel'].forEach(function (id) { bind(id, updMix); });
  updMix();

  /* ============================================================
     互動 2：前處理實驗台
     ============================================================ */
  var cPrep = chart('cvPrep', {
    type: 'line',
    data: { datasets: [
      { label: '處理前（原始）', data: [], borderColor: COL.grey, borderDash: [5, 4], fill: false, yAxisID: 'y' },
      { label: '處理後', data: [], borderColor: COL.teal, fill: false, yAxisID: 'y1' }
    ] },
    options: opts({ scales: {
      x: BASE_OPTS.scales.x,
      y: { position: 'left', title: { display: true, text: '原始強度', font: { size: 11, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 10 } } },
      y1: { position: 'right', title: { display: true, text: '處理後強度', font: { size: 11, weight: 700 } }, grid: { display: false }, ticks: { font: { size: 10 } } }
    } })
  });
  function updPrep() {
    if (!cPrep) return;
    var fl = +document.getElementById('pFluor').value / 10;
    var nz = +document.getElementById('pNoise').value / 1000;
    var wl = [5, 9, 15, 25, 41, 71][+document.getElementById('pSmooth').value] || 9;
    var doBase = document.getElementById('pBase').checked;
    var doNorm = document.getElementById('pNorm').checked;
    setTxt('pFluorv', fl.toFixed(1) + '×'); setTxt('pNoisev', nz.toFixed(3)); setTxt('pSmoothv', wl + ' 點');

    var clean = mix({ lactose: 1, casein: 0.35, melamine: 0.10 });
    var raw = clean.map(function (v, i) { return v + fl * BG[i] + nz * NOISE[i] * 3; });
    var proc = savgol(raw, wl);
    if (doBase) proc = baselineCorrect(proc);
    var shown = doNorm ? minmax(proc) : proc;

    cPrep.data.datasets[0].data = pts(raw);
    cPrep.data.datasets[1].data = pts(shown);
    cPrep.update();

    // 讀值一律取「歸一化之前」的絕對強度，否則峰被抹平時看不出高度在掉
    setTxt('pOut1085', at(proc, 1085).toFixed(3));
    setTxt('pOut676', at(proc, 676).toFixed(3));
    setTxt('pOutRatio', fwhm(proc, 676).toFixed(0) + ' cm⁻¹');

    var warn = document.getElementById('pWarn');
    if (warn) {
      if (wl >= 25) { warn.className = 'verdict-box hit'; warn.textContent = '⚠ 平滑視窗 ' + wl + ' 點 ＝ ' + (wl * 4) + ' cm⁻¹，已經寬過三聚氰胺 676 cm⁻¹ 的峰寬 —— 你要找的訊號正在被自己的前處理抹掉。'; }
      else if (!doBase && fl > 1.2) { warn.className = 'verdict-box'; warn.textContent = '螢光背景還在，整條光譜坐在一個大駝峰上。把「基線校正」打開看看。'; }
      else if (!doNorm) { warn.className = 'verdict-box'; warn.textContent = '沒有歸一化：換一天測、雷射功率不同，這張圖的絕對高度就不能跟今天比。'; }
      else { warn.className = 'verdict-box miss'; warn.textContent = '✓ 這組設定是合理的：窄峰保留、背景移除、尺度統一，可以進到後面的分析了。'; }
    }
  }
  ['pFluor', 'pNoise', 'pSmooth', 'pBase', 'pNorm'].forEach(function (id) {
    var e = document.getElementById(id); if (e) e.addEventListener('input', updPrep);
  });
  updPrep();

  /* ============================================================
     互動 3：未知樣品判讀器
     ============================================================ */
  var NAMES = { olive: '橄欖油', sunflower: '葵花油', coconut: '椰子油',
                milk_normal: '正常奶粉', milk_melamine: '摻三聚氰胺奶粉', starch: '澱粉' };
  var WHY = {
    olive: '1745（酯）＋1441（CH₂）告訴你是油脂；再看到 1523 與 1156 的類胡蘿蔔素峰 —— 那是特級初榨橄欖油的招牌。',
    sunflower: '油脂骨架齊全，但幾乎沒有 1523 類胡蘿蔔素訊號，而 1265/1441 比值偏高（不飽和度高）。',
    coconut: '有 1745 酯基，但 1265 與 1656 幾乎消失 —— 高度飽和，這是椰子油。',
    milk_normal: '850／1085／1125 的醣類峰配上 1003 苯丙胺酸，是乳糖＋酪蛋白的組合；676 乾淨。',
    milk_melamine: '奶粉基質沒變，但 676 cm⁻¹ 冒出一個基質本來沒有的峰 —— 三嗪環呼吸，三聚氰胺。',
    starch: '478 cm⁻¹ 有明顯強峰而 1745 幾乎沒有訊號 —— 是澱粉，不是油脂。'
  };
  var uIdx = 0, uAnswered = false;
  var cUnk = chart('cvUnk', { type: 'line', data: { datasets: [{ label: '未知樣品', data: [], borderColor: COL.violet, fill: false }] }, options: opts() });
  function showUnk() {
    if (!cUnk) return;
    var s = R.unknown[uIdx];
    cUnk.data.datasets[0].data = pts(s.y);
    cUnk.data.datasets[0].label = '未知樣品 ' + s.id;
    cUnk.update();
    uAnswered = false;
    setTxt('unkId', '樣品 ' + s.id + '（第 ' + (uIdx + 1) + ' / ' + R.unknown.length + ' 個）');
    var fb = document.getElementById('unkFb'); if (fb) fb.className = 'feedback';
    document.querySelectorAll('#unkChoices button').forEach(function (b) { b.className = ''; });
  }
  var cbox = document.getElementById('unkChoices');
  if (cbox) {
    Object.keys(NAMES).forEach(function (k) {
      var b = document.createElement('button'); b.textContent = NAMES[k]; b.dataset.k = k;
      b.addEventListener('click', function () {
        if (uAnswered) return; uAnswered = true;
        var truth = R.unknown[uIdx].ans;
        document.querySelectorAll('#unkChoices button').forEach(function (x) {
          if (x.dataset.k === truth) x.className = 'right';
          else if (x === b) x.className = 'wrong';
        });
        var fb = document.getElementById('unkFb');
        fb.className = 'feedback show';
        fb.innerHTML = (k === truth ? '<b style="color:#0E7C7B">答對了。</b> ' : '<b style="color:#E36414">不是這個。</b> 正確答案是「' + NAMES[truth] + '」。')
          + WHY[truth];
      });
      cbox.appendChild(b);
    });
  }
  var nextBtn = document.getElementById('unkNext');
  if (nextBtn) nextBtn.addEventListener('click', function () { uIdx = (uIdx + 1) % R.unknown.length; showUnk(); });
  showUnk();

  /* ============================================================
     互動 4：摻偽偵測模擬器
     ============================================================ */
  var TH = R.melamine_blank.mean + 3 * R.melamine_blank.sd;
  // 對真實 60 個樣品做線性迴歸，讓滑桿讀值與 Notebook 的結果一致
  var fit = (function () {
    var sx = 0, sy = 0, sxx = 0, sxy = 0, n = R.dose.length;
    R.dose.forEach(function (p) { sx += p[0]; sy += p[1]; sxx += p[0] * p[0]; sxy += p[0] * p[1]; });
    var b = (n * sxy - sx * sy) / (n * sxx - sx * sx);
    return { b: b, a: (sy - b * sx) / n };
  })();
  var LOD = (TH - fit.a) / fit.b;

  var cMel = chart('cvMel', {
    type: 'line',
    data: { datasets: [
      { label: '正常奶粉（0%）', data: [], borderColor: COL.grey, borderDash: [5, 4], fill: false },
      { label: '目前樣品', data: [], borderColor: COL.coral, fill: false }
    ] },
    options: opts({ scales: { x: Object.assign({}, BASE_OPTS.scales.x, { min: 560, max: 820 }), y: BASE_OPTS.scales.y } })
  });
  var cDose = chart('cvDose', {
    type: 'scatter',
    data: { datasets: [
      { label: '60 個實測樣品', data: R.dose.map(function (p) { return { x: p[0], y: p[1] }; }),
        backgroundColor: 'rgba(26,26,26,.35)', pointRadius: 3.5 },
      { label: '目前樣品', data: [], backgroundColor: COL.coral, pointRadius: 8 },
      { label: '判定閾值（空白＋3SD）', type: 'line', data: [{ x: 0, y: TH }, { x: 5, y: TH }],
        borderColor: COL.coral, borderDash: [6, 4], borderWidth: 2, pointRadius: 0, fill: false }
    ] },
    options: opts({ scales: {
      x: { type: 'linear', min: -0.2, max: 5.2, title: { display: true, text: '三聚氰胺濃度 (%)', font: { size: 12, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } },
      y: { title: { display: true, text: '676 cm⁻¹ 峰強度', font: { size: 12, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } }
    } })
  });
  var base0 = minmax(mix({ lactose: 1, casein: 0.35 }));
  function updMel() {
    var pct = +document.getElementById('melPct').value / 100;
    setTxt('melPctv', pct.toFixed(2) + ' %');
    var y = minmax(mix({ lactose: 1, casein: 0.35, melamine: pct / 100 * 8 }));
    if (cMel) { cMel.data.datasets[0].data = pts(base0); cMel.data.datasets[1].data = pts(y); cMel.update(); }
    var h = fit.a + fit.b * pct;
    if (cDose) { cDose.data.datasets[1].data = [{ x: pct, y: h }]; cDose.update(); }
    setTxt('melPeak', h.toFixed(3));
    setTxt('melTh', TH.toFixed(3));
    setTxt('melPpm', Math.round(pct * 10000).toLocaleString() + ' mg/kg');
    var v = document.getElementById('melVerdict');
    if (v) {
      if (pct === 0) { v.className = 'verdict-box miss'; v.textContent = '空白樣品：676 cm⁻¹ 只有雜訊。'; }
      else if (h > TH) { v.className = 'verdict-box hit'; v.textContent = '⚑ 檢出 —— 676 峰高於判定閾值。這個濃度（' + Math.round(pct * 10000).toLocaleString() + ' mg/kg）遠高於 Codex 的 2.5 mg/kg 限量。'; }
      else { v.className = 'verdict-box miss'; v.textContent = '未檢出 —— 但樣品裡確實有 ' + Math.round(pct * 10000).toLocaleString() + ' mg/kg 的三聚氰胺，只是低於本方法的偵測極限（≈ ' + LOD.toFixed(2) + '%）。這就是「未檢出 ≠ 沒有」。'; }
    }
  }
  bind('melPct', updMel);
  setTxt('melLod', LOD.toFixed(2) + ' %');
  updMel();

  /* ============================================================
     互動 5：PLS 潛在變數選擇器
     ============================================================ */
  var LVS = Object.keys(R.pls.lv).map(Number).sort(function (a, b) { return a - b; });
  var bestLV = LVS.reduce(function (b, n) { return R.pls.lv[n].rmsecv < R.pls.lv[b].rmsecv ? n : b; }, LVS[0]);
  var cRms = chart('cvRms', {
    type: 'bar',
    data: { labels: LVS, datasets: [{ label: 'RMSECV (%)', data: LVS.map(function (n) { return R.pls.lv[n].rmsecv; }), backgroundColor: [] }] },
    options: opts({ scales: {
      x: { title: { display: true, text: '潛在變數個數 (LV)', font: { size: 12, weight: 700 } }, grid: { display: false }, ticks: { font: { size: 11 } } },
      y: { title: { display: true, text: 'RMSECV (%)', font: { size: 12, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } }
    }, plugins: { legend: { display: false } } })
  });
  var cScat = chart('cvScat', {
    type: 'scatter',
    data: { datasets: [
      { label: '交叉驗證預測', data: [], backgroundColor: COL.teal, pointRadius: 4 },
      { label: '理想線', type: 'line', data: [{ x: 0, y: 0 }, { x: 50, y: 50 }], borderColor: COL.grey, borderDash: [6, 4], borderWidth: 2, pointRadius: 0, fill: false }
    ] },
    options: opts({ scales: {
      x: { type: 'linear', min: -3, max: 55, title: { display: true, text: '實際摻入葵花油 (%)', font: { size: 12, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } },
      y: { min: -3, max: 55, title: { display: true, text: '模型預測 (%)', font: { size: 12, weight: 700 } }, grid: { color: '#EFEBE0' }, ticks: { font: { size: 11 } } }
    } })
  });
  function updPls() {
    var lv = +document.getElementById('plsLv').value;
    setTxt('plsLvv', 'LV = ' + lv);
    var d = R.pls.lv[lv];
    if (cRms) { cRms.data.datasets[0].backgroundColor = LVS.map(function (n) { return n === lv ? COL.coral : 'rgba(14,124,123,.35)'; }); cRms.update(); }
    if (cScat) { cScat.data.datasets[0].data = R.pls.actual.map(function (a, i) { return { x: a, y: d.pred[i] }; }); cScat.update(); }
    setTxt('plsRmse', d.rmsecv.toFixed(2) + ' %');
    setTxt('plsR2', d.r2.toFixed(3));
    setTxt('plsLimit', '≈ ' + (d.rmsecv * 3).toFixed(0) + ' %');
    var v = document.getElementById('plsVerdict');
    if (v) {
      if (lv < bestLV) { v.className = 'verdict-box'; v.textContent = 'LV 太少：模型還沒抓到足夠的光譜資訊，預測點明顯偏離理想線 —— 這是配適不足（underfitting）。'; }
      else if (lv === bestLV) { v.className = 'verdict-box miss'; v.textContent = '✓ RMSECV 的最低點就在這裡。這是這組資料該選的潛在變數個數。'; }
      else { v.className = 'verdict-box hit'; v.textContent = 'LV 太多：訓練誤差還在下降，但 RMSECV 開始回升 —— 模型正在把雜訊也背下來，這是過度配適（overfitting）。'; }
    }
  }
  bind('plsLv', updPls);
  var lvInit = document.getElementById('plsLv'); if (lvInit) { lvInit.value = bestLV; }
  updPls();

  /* ---------- 導覽高亮 ---------- */
  var links = Array.prototype.slice.call(document.querySelectorAll('nav a[href^="#"]'));
  var secs = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); });
  function syncNav() {
    var y = window.scrollY + 140, cur = -1;
    secs.forEach(function (s, i) { if (s && s.offsetTop <= y) cur = i; });
    links.forEach(function (a, i) { a.classList.toggle('on', i === cur); });
  }
  window.addEventListener('scroll', syncNav, { passive: true });
  syncNav();
})();
