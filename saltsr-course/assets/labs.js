/* =========================================================================
   labs.js — 三個互動實驗室的行為
   1) 電荷平衡即時模擬器
   2) Runsalt RH–莫耳曲線判讀器
   3) 石膏飽和度與稀釋計算機
   計算全部委託 salt_engine.js（已與 R 版逐項比對）
   ========================================================================= */
(function () {
  'use strict';

  const { saltBalance, ecosInputFile, parseRunsalt, IONS, ANIONS, CATIONS, ION_LABEL } = window.SaltEngine;
  const DATA_BASE = window.SALTSR_DATA_BASE || 'data/';
  const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : v.toFixed(d);

  const PALETTE = ['#0E7C7B', '#E36414', '#C8941F', '#6A3D8F',
                   '#3D7EA6', '#B3402C', '#1F7A4D', '#7A5C3E', '#B5179E'];

  /* ================= 預設情境 ================= */
  const PRESETS = {
    'MH-01': { dry_g:1.000, water_ml:100, chloride_ppm:50, nitrate_ppm:30, sulfate_ppm:20,
               sodium_ppm:40, potassium_ppm:10, calcium_ppm:15, magnesium_ppm:5,
               note:'官方範例。陽離子過剩 26.8 % → Pathway 2，鈣被扣光、鎂再扣一部分，沒有石膏。' },
    'MH-02': { dry_g:1.128, water_ml:100, chloride_ppm:180, nitrate_ppm:420, sulfate_ppm:60,
               sodium_ppm:120, potassium_ppm:45, calcium_ppm:95, magnesium_ppm:25,
               note:'硝酸鹽主導。Δe 僅 0.52 %，落在 2 % 容忍範圍內 → Pathway 1 等比例調整。' },
    'MH-04': { dry_g:1.000, water_ml:100, chloride_ppm:120, nitrate_ppm:80, sulfate_ppm:45,
               sodium_ppm:60, potassium_ppm:15, calcium_ppm:25, magnesium_ppm:10,
               note:'陰離子過剩 → 無論差多少都走 Pathway 1。硫酸根全部變成石膏。' },
    'MH-08': { dry_g:1.000, water_ml:100, chloride_ppm:40, nitrate_ppm:25, sulfate_ppm:1600,
               sodium_ppm:30, potassium_ppm:10, calcium_ppm:700, magnesium_ppm:8,
               note:'石膏 22.2 wt%，飽和度 1.04 → 觸發稀釋警告。這筆數據不可直接使用。' },
    'salt_test': { dry_g:1.128, water_ml:100, chloride_ppm:66.824, nitrate_ppm:332.956,
               sulfate_ppm:87.221, sodium_ppm:21.471, potassium_ppm:211.358,
               calcium_ppm:75.594, magnesium_ppm:7.582,
               note:'SaltsR 套件內建的真實測試樣品。鉀與硝酸根都非常高（莫耳分率各約 0.38）。' }
  };

  const RANGE = {
    chloride:[0,600], nitrate:[0,600], sulfate:[0,2000],
    sodium:[0,500], potassium:[0,400], calcium:[0,800], magnesium:[0,250]
  };

  /* ================= 實驗室 1：電荷平衡模擬器 ================= */
  function initLab1() {
    const root = document.getElementById('lab1-body');
    if (!root) return;
    const state = Object.assign({}, PRESETS['MH-01']);

    // --- 建控制項 ---
    const ctrls = document.createElement('div');
    ctrls.className = 'ctrl-grid';
    ctrls.innerHTML =
      mkNum('dry_g', '乾樣重 (g)', state.dry_g, 0.05, 0.1, 10) +
      mkNum('water_ml', '萃取水量 (mL)', state.water_ml, 5, 10, 500) +
      IONS.map((i) => mkSlider(i, state[i + '_ppm'])).join('');
    root.appendChild(ctrls);

    const presetRow = document.createElement('div');
    presetRow.className = 'pill-row';
    presetRow.style.marginTop = '14px';
    presetRow.innerHTML = '<span class="small muted" style="align-self:center">載入情境：</span>' +
      Object.keys(PRESETS).map((k) =>
        `<button class="btn btn-teal" data-preset="${k}" type="button">${k}</button>`).join('');
    root.appendChild(presetRow);

    const note = document.createElement('p');
    note.className = 'small muted';
    note.style.margin = '10px 0 0';
    root.appendChild(note);

    const view = document.createElement('div');
    root.appendChild(view);

    function mkSlider(ion, val) {
      const L = ION_LABEL[ion], [lo, hi] = RANGE[ion];
      const cls = ANIONS.includes(ion) ? 'ion-an' : (ion === 'calcium' || ion === 'magnesium' ? 'ion-ca' : '');
      return `<div class="ctrl ${cls}">
        <label for="s_${ion}">${L.zh} ${L.sym}
          <span class="v" id="v_${ion}">${val} ppm</span></label>
        <input type="range" id="s_${ion}" min="${lo}" max="${hi}" step="0.5" value="${val}">
      </div>`;
    }
    function mkNum(key, label, val, step, lo, hi) {
      return `<div class="ctrl">
        <label for="n_${key}">${label}<span class="v" id="v_${key}">${val}</span></label>
        <input type="number" id="n_${key}" value="${val}" step="${step}" min="${lo}" max="${hi}">
      </div>`;
    }

    IONS.forEach((ion) => {
      document.getElementById('s_' + ion).addEventListener('input', (e) => {
        state[ion + '_ppm'] = +e.target.value;
        document.getElementById('v_' + ion).textContent = e.target.value + ' ppm';
        note.textContent = '';
        render();
      });
    });
    ['dry_g', 'water_ml'].forEach((k) => {
      document.getElementById('n_' + k).addEventListener('input', (e) => {
        const v = parseFloat(e.target.value);
        if (!Number.isFinite(v) || v <= 0) return;
        state[k] = v;
        document.getElementById('v_' + k).textContent = v;
        render();
      });
    });
    presetRow.addEventListener('click', (e) => {
      const k = e.target.dataset.preset;
      if (!k) return;
      Object.assign(state, PRESETS[k]);
      IONS.forEach((i) => {
        const s = document.getElementById('s_' + i);
        if (state[i + '_ppm'] > +s.max) s.max = Math.ceil(state[i + '_ppm'] * 1.2);
        s.value = state[i + '_ppm'];
        document.getElementById('v_' + i).textContent = state[i + '_ppm'] + ' ppm';
      });
      ['dry_g', 'water_ml'].forEach((k2) => {
        document.getElementById('n_' + k2).value = state[k2];
        document.getElementById('v_' + k2).textContent = state[k2];
      });
      note.innerHTML = '<strong>' + k + '：</strong>' + PRESETS[k].note;
      render();
    });

    function render() {
      const r = saltBalance(Object.assign({ sample_name: '互動樣品' }, state));
      const total = r.total_mEq_anions + r.total_mEq_cations;
      const wA = 100 * r.total_mEq_anions / total, wC = 100 - wA;
      const p1 = r.Pathway === 'Pathway 1';

      let stepsHTML = '';
      if (!p1) {
        stepsHTML = `<h4>Pathway 2 的逐級扣除過程</h4><div class="tbl-wrap"><table>
          <thead><tr><th>級</th><th>離子</th><th class="num">扣除前</th><th class="num">扣掉</th>
          <th class="num">扣除後</th><th class="num">剩餘差額</th><th>狀態</th></tr></thead><tbody>` +
          r.steps.map((s, i) => `<tr>
            <td>5${'abcd'[i]}</td><td>${s.sym}</td>
            <td class="num">${fmt(s.before)}</td>
            <td class="num">${s.absorbed > 1e-9 ? fmt(s.absorbed) : '—'}</td>
            <td class="num ${s.after === 0 && s.absorbed > 0 ? 'hi' : ''}">${fmt(s.after)}</td>
            <td class="num">${fmt(s.leftover)}</td>
            <td class="small">${s.absorbed <= 1e-9 ? '未動用'
              : (s.after === 0 ? '<strong style="color:var(--coral)">扣光了，差額往下傳</strong>'
                               : '<strong style="color:var(--teal)">吸收完畢，結束</strong>')}</td>
          </tr>`).join('') + '</tbody></table></div>';
      } else {
        const k = (r.total_mEq_anions + r.total_mEq_cations) / 2;
        stepsHTML = `<h4>Pathway 1 的等比例調整</h4>
          <p class="small">陰離子全體乘以 <code>${fmt((r.total_mEq_anions + r.total_mEq_cations) / (2 * r.total_mEq_anions), 4)}</code>、
          陽離子全體乘以 <code>${fmt((r.total_mEq_anions + r.total_mEq_cations) / (2 * r.total_mEq_cations), 4)}</code>，
          兩邊都變成 <code>${fmt(k)}</code> mEq/kg。每個離子彼此的比例保持不變。</p>`;
      }

      view.innerHTML = `
        <hr class="sep">
        <div class="balbar" title="陰離子 vs 陽離子當量比例">
          <div class="b-an" style="width:${wA}%">陰 ${fmt(r.total_mEq_anions, 1)}</div>
          <div class="b-cat" style="width:${wC}%">陽 ${fmt(r.total_mEq_cations, 1)}</div>
        </div>
        <p class="tiny muted" style="margin:0 0 14px">
          長條的長度比例就是兩邊當量的比例。兩塊一樣長 = 已經平衡。</p>

        <div class="readout">
          <div class="ro"><div class="k">總可溶鹽（校正前）</div><div class="v">${fmt(r.total_wt * 100, 3)}<span class="tiny"> wt%</span></div></div>
          <div class="ro ${r.charge_imbalance_pct > 20 ? 'bad' : (r.charge_imbalance_pct > 2 ? 'warnv' : 'good')}">
            <div class="k">不平衡量 Δe</div><div class="v">${fmt(r.charge_imbalance_initial, 1)}</div></div>
          <div class="ro ${r.charge_imbalance_pct > 20 ? 'bad' : (r.charge_imbalance_pct > 2 ? 'warnv' : 'good')}">
            <div class="k">占較大側比例</div><div class="v">${fmt(r.charge_imbalance_pct, 2)}<span class="tiny"> %</span></div></div>
          <div class="ro"><div class="k">過剩的一側</div><div class="v" style="font-size:.95rem">${
            r.imbalance_allocation === 'dExcess Cations' ? '陽離子' : '陰離子'}</div></div>
          <div class="ro ${r.gypsum_content_limit > 0 ? 'warnv' : ''}">
            <div class="k">石膏</div><div class="v">${fmt(r.gypsum_content * 100, 3)}<span class="tiny"> wt%</span></div></div>
          <div class="ro ${r.saturation_gypsum_content > 1 ? 'bad' : 'good'}">
            <div class="k">石膏飽和度</div><div class="v">${fmt(r.saturation_gypsum_content, 3)}</div></div>
          <div class="ro good"><div class="k">可溶鹽（校正後）</div><div class="v">${fmt(r.total_wt_adj * 100, 3)}<span class="tiny"> wt%</span></div></div>
          <div class="ro"><div class="k">被校正掉</div><div class="v">${fmt(r.removed_wt * 100, 3)}<span class="tiny"> wt%</span></div></div>
        </div>

        <p style="margin:6px 0 4px">判定路徑：<span class="pathbadge ${p1 ? 'p1' : 'p2'}">${r.Pathway}</span>
          <span class="small muted" style="margin-left:10px">${
            p1 ? (r.total_mEq_anions > r.total_mEq_cations
                  ? '因為陰離子過剩 → 沒有「漏測陰離子」的現成解釋，歸因於分析誤差'
                  : '因為 Δe = ' + fmt(r.charge_imbalance_pct, 2) + ' % ≤ 2 % → 視為分析誤差')
               : '因為陽離子過剩且 Δe = ' + fmt(r.charge_imbalance_pct, 2) + ' % &gt; 2 % → 歸因於未測到的碳酸根'}</span></p>

        ${r.saturation_gypsum_content > 1
          ? `<div class="callout warn" style="margin:14px 0"><span class="ct">⚠ 飽和度警告</span>
             <p style="margin:0">${r.ECOS_warnings}<br>
             <span class="small">試試把「萃取水量」往上拉，看要多少水才能讓飽和度降到 1 以下。
             但別忘了：真正的解法是回實驗室重新萃取，不是改計算參數。</span></p></div>` : ''}

        <div class="tbl-wrap"><table>
          <thead><tr><th>離子</th><th class="num">ppm</th><th class="num">wt %</th>
            <th class="num">mEq/kg</th><th class="num">校正後</th>
            <th class="num">扣石膏後</th><th class="num">莫耳分率 x</th></tr></thead>
          <tbody>${IONS.map((i) => `<tr>
            <td>${ION_LABEL[i].zh} <span class="muted">${ION_LABEL[i].sym}</span></td>
            <td class="num">${fmt(r.ppm[i], 1)}</td>
            <td class="num">${fmt(r.wt[i] * 100, 3)}</td>
            <td class="num">${fmt(r.mEq[i])}</td>
            <td class="num ${Math.abs(r.mEq_adj[i] - r.mEq[i]) > 1e-6 ? 'hi' : ''}">${fmt(r.mEq_adj[i])}</td>
            <td class="num ${Math.abs(r.mEq_final[i] - r.mEq_adj[i]) > 1e-6 ? 'hi' : ''}">${fmt(r.mEq_final[i])}</td>
            <td class="num">${fmt(r.x[i], 5)}</td></tr>`).join('')}
            <tr style="border-top:2px solid var(--ink);font-weight:700">
              <td>合計</td><td class="num">${fmt(IONS.reduce((s, i) => s + r.ppm[i], 0), 1)}</td>
              <td class="num">${fmt(r.total_wt * 100, 3)}</td>
              <td class="num">陰 ${fmt(r.total_mEq_anions, 1)} / 陽 ${fmt(r.total_mEq_cations, 1)}</td>
              <td class="num">—</td><td class="num">${r.charge_imbalance_final ? '✓ 平衡' : '✗'}</td>
              <td class="num">${fmt(IONS.reduce((s, i) => s + r.x[i], 0), 4)}</td></tr>
          </tbody></table></div>

        ${stepsHTML}

        <details><summary>看產生的 ECOS / Runsalt 輸入檔</summary>
          <pre style="margin-top:0"><code>${ecosInputFile(r).replace(/</g, '&lt;')}</code></pre>
          <p class="small muted" style="margin-bottom:10px">
            把這段文字存成 <code>.txt</code>，就能直接在 Runsalt 的 <em>File → Open</em> 匯入。</p>
        </details>`;
    }

    note.innerHTML = '<strong>MH-01：</strong>' + PRESETS['MH-01'].note;
    render();
  }

  /* ================= 實驗室 2：Runsalt 曲線判讀器 ================= */
  function initLab2() {
    const root = document.getElementById('lab2-body');
    if (!root) return;

    root.innerHTML = `
      <p class="muted small">載入中…</p>`;

    fetch(DATA_BASE + 'SaltsRExample20C.txt')
      .then((r) => r.text())
      .then((txt) => build(parseRunsalt(txt)))
      .catch(() => { root.innerHTML = '<p class="muted">資料載入失敗，請重新整理頁面。</p>'; });

    function build(salts) {
      const rhMin = Math.min(...salts.flatMap((s) => s.points.map((p) => p.rh)));
      const rhMax = Math.max(...salts.flatMap((s) => s.points.map((p) => p.rh)));
      const molMax = Math.max(...salts.flatMap((s) => s.points.map((p) => p.mol)));

      root.innerHTML = `
        <div class="ctrl" style="max-width:520px">
          <label for="rhSlider">環境相對濕度
            <span class="v" id="rhVal">60.0 %RH</span></label>
          <input type="range" id="rhSlider" min="${rhMin}" max="${Math.min(rhMax + 6, 98)}"
                 step="0.2" value="60">
        </div>
        <div class="chartbox tall"><canvas id="lab2canvas"></canvas></div>
        <div id="lab2read"></div>
        <div class="tbl-wrap"><table>
          <thead><tr><th>鹽相</th><th>礦物／俗名</th><th class="num">結晶臨界 RH (%)</th>
            <th class="num">最大量 (mol)</th><th>此濕度下</th></tr></thead>
          <tbody id="lab2tbody"></tbody></table></div>`;

      const NAMES = {
        'NaCl':'岩鹽 halite', 'NaNO3':'鈉硝石 nitratine', 'KNO3':'硝石 niter',
        'Na2SO4':'無水芒硝 thenardite', 'Na2SO4.10H2O':'芒硝 mirabilite',
        'MgSO4.4H2O':'starkeyite', 'MgSO4.1H2O':'kieserite', 'MgSO4.6H2O':'hexahydrite',
        'MgSO4.7H2O':'瀉鹽 epsomite', 'Na2SO4.MgSO4.4H2O':'鈉鎂礬 blödite',
        'KCl':'鉀鹽 sylvite', 'K2SO4':'鉀芒硝 arcanite', 'NaCl.2H2O':'水氯鈉石 hydrohalite'
      };

      const cv = document.getElementById('lab2canvas');
      const slider = document.getElementById('rhSlider');
      const rhVal = document.getElementById('rhVal');
      const readEl = document.getElementById('lab2read');
      const tbody = document.getElementById('lab2tbody');

      function molAt(s, rh) {
        const p = s.points;
        if (rh < p[0].rh) return p[0].mol;          // 更乾：維持固體
        if (rh > p[p.length - 1].rh) return 0;      // 超過臨界：全溶
        for (let i = 1; i < p.length; i++) {
          if (rh <= p[i].rh) {
            const t = (rh - p[i - 1].rh) / (p[i].rh - p[i - 1].rh || 1);
            return p[i - 1].mol + t * (p[i].mol - p[i - 1].mol);
          }
        }
        return 0;
      }

      function draw(rh) {
        const dpr = window.devicePixelRatio || 1;
        const box = cv.parentElement.getBoundingClientRect();
        cv.width = box.width * dpr; cv.height = box.height * dpr;
        cv.style.width = box.width + 'px'; cv.style.height = box.height + 'px';
        const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0);
        const W = box.width, H = box.height;
        const m = { l: 58, r: 132, t: 16, b: 44 };
        const x0 = +slider.min, x1 = +slider.max;
        const X = (v) => m.l + (v - x0) / (x1 - x0) * (W - m.l - m.r);
        const Y = (v) => H - m.b - (v / (molMax * 1.08)) * (H - m.t - m.b);

        g.clearRect(0, 0, W, H);
        g.fillStyle = '#FFFFFF'; g.fillRect(0, 0, W, H);

        // grid
        g.strokeStyle = '#E4DECC'; g.lineWidth = 1; g.font = '11px system-ui'; g.fillStyle = '#8A8070';
        for (let v = Math.ceil(x0 / 10) * 10; v <= x1; v += 10) {
          g.beginPath(); g.moveTo(X(v), m.t); g.lineTo(X(v), H - m.b); g.stroke();
          g.textAlign = 'center'; g.fillText(v + '%', X(v), H - m.b + 16);
        }
        for (let k = 0; k <= 5; k++) {
          const v = molMax * 1.08 * k / 5;
          g.beginPath(); g.moveTo(m.l, Y(v)); g.lineTo(W - m.r, Y(v)); g.stroke();
          g.textAlign = 'right'; g.fillText(v.toFixed(2), m.l - 6, Y(v) + 4);
        }
        g.fillStyle = '#52493B'; g.textAlign = 'center';
        g.font = '12px system-ui';
        g.fillText('相對濕度 RH (%)', m.l + (W - m.l - m.r) / 2, H - 6);
        g.save(); g.translate(14, m.t + (H - m.t - m.b) / 2); g.rotate(-Math.PI / 2);
        g.fillText('固體鹽的量 (mol)', 0, 0); g.restore();

        // curves
        salts.forEach((s, i) => {
          const c = PALETTE[i % PALETTE.length];
          g.strokeStyle = c; g.lineWidth = 2.6; g.beginPath();
          s.points.forEach((p, j) => { j ? g.lineTo(X(p.rh), Y(p.mol)) : g.moveTo(X(p.rh), Y(p.mol)); });
          g.stroke();
          // 結晶點
          const last = s.points[s.points.length - 1];
          g.fillStyle = '#fff'; g.strokeStyle = c; g.lineWidth = 2.2;
          g.beginPath(); g.arc(X(last.rh), Y(last.mol), 4.5, 0, 7); g.fill(); g.stroke();
          // legend
          const ly = m.t + 14 + i * 17;
          g.fillStyle = c; g.fillRect(W - m.r + 8, ly - 7, 14, 3);
          g.fillStyle = '#1A1A1A'; g.font = '11px system-ui'; g.textAlign = 'left';
          g.fillText(s.salt.length > 15 ? s.salt.slice(0, 14) + '…' : s.salt, W - m.r + 26, ly - 2);
        });

        // RH 游標
        g.strokeStyle = '#1A1A1A'; g.lineWidth = 2; g.setLineDash([5, 4]);
        g.beginPath(); g.moveTo(X(rh), m.t); g.lineTo(X(rh), H - m.b); g.stroke();
        g.setLineDash([]);
        g.fillStyle = '#1A1A1A';
        g.beginPath(); g.moveTo(X(rh), m.t - 2); g.lineTo(X(rh) - 5, m.t - 10);
        g.lineTo(X(rh) + 5, m.t - 10); g.closePath(); g.fill();
        salts.forEach((s, i) => {
          const v = molAt(s, rh);
          if (v > 1e-6) {
            g.fillStyle = PALETTE[i % PALETTE.length];
            g.beginPath(); g.arc(X(rh), Y(v), 3.6, 0, 7); g.fill();
          }
        });
      }

      function update() {
        const rh = +slider.value;
        rhVal.textContent = rh.toFixed(1) + ' %RH';
        draw(rh);

        const solid = salts.filter((s) => molAt(s, rh) > 1e-6);
        const dissolved = salts.filter((s) => molAt(s, rh) <= 1e-6);
        const nextUp = salts.filter((s) => s.crystallisation > rh)
                            .sort((a, b) => a.crystallisation - b.crystallisation)[0];
        const nextDown = salts.filter((s) => s.crystallisation <= rh)
                              .sort((a, b) => b.crystallisation - a.crystallisation)[0];

        readEl.innerHTML = `<div class="readout">
          <div class="ro good"><div class="k">仍為固體</div><div class="v">${solid.length}<span class="tiny"> / ${salts.length}</span></div></div>
          <div class="ro"><div class="k">已完全溶解</div><div class="v">${dissolved.length}</div></div>
          <div class="ro warnv"><div class="k">固體總量</div><div class="v">${
            fmt(salts.reduce((a, s) => a + molAt(s, rh), 0), 3)}<span class="tiny"> mol</span></div></div>
          <div class="ro bad"><div class="k">${nextDown ? '再乾 ' + fmt(rh - nextDown.crystallisation, 1) + ' % 就會析出' : '下方無鹽相'}</div>
            <div class="v" style="font-size:.9rem">${nextDown ? nextDown.salt : '—'}</div></div>
        </div>
        <div class="callout" style="margin-top:4px"><span class="ct">此刻的判讀</span>
          <p style="margin:0">${
            nextUp ? `再<strong>加濕 ${fmt(nextUp.crystallisation - rh, 1)} %</strong>（到 ${fmt(nextUp.crystallisation, 1)} %RH）
                     就會讓 <strong>${nextUp.salt}</strong> 完全溶解 —— 它是目前<strong>最接近溶解</strong>的鹽，
                     對濕度上升最敏感。`
                   : '所有鹽相在此濕度都已溶解 —— 這是相對安全的高濕區，但材料會長期潮濕，須留意生物危害。'}
            ${nextDown ? `反過來，只要<strong>乾燥 ${fmt(rh - nextDown.crystallisation, 1)} %</strong>
                     （降到 ${fmt(nextDown.crystallisation, 1)} %RH），<strong>${nextDown.salt}</strong>
                     就會開始結晶。` : ''}
            ${solid.length ? `目前有 <strong>${solid.length}</strong> 種鹽以固體存在，
              其中 <strong>${solid.slice().sort((a, b) => b.crystallisation - a.crystallisation)[0].salt}</strong>
              的臨界值最高（${fmt(Math.max(...solid.map((s) => s.crystallisation)), 1)} %RH），
              也就是在乾燥過程中<strong>最早析出</strong>的鹽 —— 通常也是主要威脅。` : ''}</p></div>`;

        tbody.innerHTML = salts.map((s) => {
          const v = molAt(s, rh);
          const st = v <= 1e-6 ? '<span style="color:var(--teal)">已溶解</span>'
            : (Math.abs(v - s.points[0].mol) < 1e-9
               ? '<span style="color:var(--ink-soft)">完全固體</span>'
               : `<strong style="color:var(--coral)">部分溶解 ${fmt(100 * v / s.points[0].mol, 0)} %</strong>`);
          return `<tr><td><code>${s.salt}</code></td><td>${NAMES[s.salt] || '—'}</td>
            <td class="num ${s.crystallisation >= 55 && s.crystallisation <= 80 ? 'hi' : ''}">${fmt(s.crystallisation, 2)}</td>
            <td class="num">${fmt(Math.max(...s.points.map((p) => p.mol)), 4)}</td>
            <td>${st}</td></tr>`;
        }).join('');
      }

      slider.addEventListener('input', update);
      window.addEventListener('resize', () => draw(+slider.value));
      update();
    }
  }

  /* ================= 實驗室 3：石膏飽和度計算機 ================= */
  function initLab3() {
    const root = document.getElementById('lab3-body');
    if (!root) return;
    const st = { dry_g: 1.0, water_ml: 100, sulfate_ppm: 1600, calcium_ppm: 700 };

    root.innerHTML = `
      <div class="ctrl-grid">
        <div class="ctrl"><label for="g_dry">乾樣重 (g)<span class="v" id="gv_dry">1.00</span></label>
          <input type="range" id="g_dry" min="0.2" max="5" step="0.02" value="1"></div>
        <div class="ctrl"><label for="g_water">萃取水量 (mL)<span class="v" id="gv_water">100</span></label>
          <input type="range" id="g_water" min="25" max="500" step="5" value="100"></div>
        <div class="ctrl ion-an"><label for="g_so4">硫酸根 (ppm)<span class="v" id="gv_so4">1600</span></label>
          <input type="range" id="g_so4" min="0" max="3000" step="10" value="1600"></div>
        <div class="ctrl ion-ca"><label for="g_ca">鈣 (ppm)<span class="v" id="gv_ca">700</span></label>
          <input type="range" id="g_ca" min="0" max="1500" step="5" value="700"></div>
      </div>
      <div id="lab3out"></div>`;

    const map = { g_dry: 'dry_g', g_water: 'water_ml', g_so4: 'sulfate_ppm', g_ca: 'calcium_ppm' };
    Object.keys(map).forEach((id) => {
      document.getElementById(id).addEventListener('input', (e) => {
        st[map[id]] = +e.target.value;
        document.getElementById(id.replace('g_', 'gv_')).textContent =
          (id === 'g_dry') ? (+e.target.value).toFixed(2) : e.target.value;
        render();
      });
    });

    function render() {
      const r = saltBalance(Object.assign({
        sample_name: 'gypsum', chloride_ppm: 40, nitrate_ppm: 25,
        sodium_ppm: 30, potassium_ppm: 10, magnesium_ppm: 8
      }, st));
      const sat = r.saturation_gypsum_content;
      const bad = sat > 1;
      // 需要多少水才能讓飽和度 = 1？ sat ∝ 1/water → water_need = water * sat
      const needWater = st.water_ml * sat;
      const needDry = st.dry_g / Math.max(sat, 1e-9);

      document.getElementById('lab3out').innerHTML = `
        <div class="readout">
          <div class="ro"><div class="k">石膏上限 min(SO₄, Ca)</div>
            <div class="v">${fmt(r.gypsum_content_limit, 1)}<span class="tiny"> mEq/kg</span></div></div>
          <div class="ro"><div class="k">限量者</div><div class="v" style="font-size:1rem">${
            r.mEq_adj.sulfate < r.mEq_adj.calcium ? '硫酸根 SO₄²⁻' : '鈣 Ca²⁺'}</div></div>
          <div class="ro ${bad ? 'bad' : 'warnv'}"><div class="k">石膏含量</div>
            <div class="v">${fmt(r.gypsum_content * 100, 3)}<span class="tiny"> wt%</span></div></div>
          <div class="ro"><div class="k">此水樣比的溶解上限</div>
            <div class="v">${fmt(r.gypsum_capacity * 100, 3)}<span class="tiny"> wt%</span></div></div>
          <div class="ro ${bad ? 'bad' : 'good'}"><div class="k">飽和度 S</div>
            <div class="v">${fmt(sat, 3)}</div></div>
        </div>
        <div class="balbar" style="height:26px">
          <div style="width:${Math.min(sat, 1) * 100}%;background:${bad ? 'var(--coral)' : 'var(--teal)'}">
            ${fmt(Math.min(sat, 1) * 100, 0)} %</div>
          <div style="width:${Math.max(0, (1 - sat)) * 100}%;background:#D9D2BE;color:#52493B">剩餘溶解能力</div>
        </div>
        <p class="tiny muted">長條滿格代表萃取水已被石膏飽和 —— 再多的石膏都溶不進去，也就測不到。</p>
        ${bad
          ? `<div class="callout warn"><span class="ct">⚠ 數據不可信</span>
             <p style="margin:0">石膏已達飽和，離子層析測到的鈣與硫酸根<strong>低於實際值</strong>，
             而且你無法從數據本身知道低了多少。<br>
             要讓飽和度降到 1 以下，需要：
             <strong>水量提高到約 ${fmt(needWater, 0)} mL</strong>（目前 ${st.water_ml} mL），
             或<strong>乾樣重降到約 ${fmt(needDry, 2)} g</strong>（目前 ${fmt(st.dry_g, 2)} g）。<br>
             <span class="small">實務上通常提高水量比減少樣品量安全，因為樣品太少會放大秤重誤差。
             但要記得：正確做法是<em>重新萃取</em>，不是在計算裡改參數。</span></p></div>`
          : `<div class="callout"><span class="ct">✓ 數據可用</span>
             <p style="margin:0">目前的水樣比足以溶解全部石膏，飽和度 ${fmt(sat, 3)}。
             還有 ${fmt((1 - sat) * 100, 0)} % 的溶解餘裕。<br>
             <span class="small">試試把「萃取水量」往下拉，看什麼時候會亮紅燈。</span></p></div>`}
        <details><summary>飽和度是怎麼算的</summary>
          <p>20 °C 下 CaSO₄·2H₂O 的溶解度約 <strong>2.14 g/L</strong>。所以在 ${st.water_ml} mL 的水裡，
          最多能溶 ${fmt(0.214 * st.water_ml / 100, 4)} g 的石膏。<br>
          把它換算成「占乾樣重的百分比」：
          <code>(0.214 × ${st.water_ml} / 10000) / ${fmt(st.dry_g, 2)} × 100 = ${fmt(r.gypsum_capacity * 100, 3)} wt%</code><br>
          再拿樣品實際的石膏含量 ${fmt(r.gypsum_content * 100, 3)} wt% 去除，就得到飽和度
          <code>${fmt(sat, 4)}</code>。</p>
          <p style="margin-bottom:10px" class="small muted">
          這個算式假設萃取液裡只有石膏在爭奪溶解度。實際上其他離子的存在會透過離子強度效應
          略微提高石膏的溶解度，所以這是個<strong>保守</strong>的估計 —— 保守在這裡是好事。</p>
        </details>`;
    }
    render();
  }

  function init() { initLab1(); initLab2(); initLab3(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
