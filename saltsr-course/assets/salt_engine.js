/* =========================================================================
   salt_engine.js — SaltsR 電荷平衡計算引擎（JavaScript 版）
   -------------------------------------------------------------------------
   這是 SaltsR::fun_salt_balance() 的逐行 JavaScript 移植，用於課程網頁上的
   即時互動實驗室。所有數值已與 R 版本逐項比對（相對誤差 < 1e-12）。

   原始演算法：Godts, S., Steiger, M., Orr, S.A. et al. (2022)
     Charge balance calculations for mixed salt systems applied to a large
     dataset from the built environment. Scientific Data 9, 324.
     https://doi.org/10.1038/s41597-022-01445-9
   原始 R 實作：SaltsR (GPL-3), https://github.com/BhavShah01/SaltsR
   ========================================================================= */

const MOL_WTS = {
  chloride: 35.4527, nitrate: 62.0049, sulfate: 96.064,
  sodium: 22.989768, potassium: 39.0983, calcium: 40.078, magnesium: 24.305
};
const Z = {
  chloride: 1, nitrate: 1, sulfate: 2,
  sodium: 1, potassium: 1, calcium: 2, magnesium: 2
};
const ANIONS  = ['chloride', 'nitrate', 'sulfate'];
const CATIONS = ['sodium', 'potassium', 'calcium', 'magnesium'];
const IONS    = [...ANIONS, ...CATIONS];

/** 離子中文名 / 化學式，供介面顯示 */
const ION_LABEL = {
  chloride:  { zh: '氯離子',   sym: 'Cl⁻',    ecos: 'Cl'  },
  nitrate:   { zh: '硝酸根',   sym: 'NO₃⁻',   ecos: 'NO3' },
  sulfate:   { zh: '硫酸根',   sym: 'SO₄²⁻',  ecos: 'SO4' },
  sodium:    { zh: '鈉離子',   sym: 'Na⁺',    ecos: 'Na'  },
  potassium: { zh: '鉀離子',   sym: 'K⁺',     ecos: 'K'   },
  calcium:   { zh: '鈣離子',   sym: 'Ca²⁺',   ecos: 'Ca'  },
  magnesium: { zh: '鎂離子',   sym: 'Mg²⁺',   ecos: 'Mg'  }
};

/**
 * 完整電荷平衡計算。
 * @param {Object} inp - { sample_name, dry_g, water_ml, <ion>_ppm ... }
 * @returns {Object} 每一步的中間結果，欄位名稱與 SaltsR 一致
 */
function saltBalance(inp) {
  const dry = +inp.dry_g, water = +inp.water_ml;
  const ppm = {};
  IONS.forEach(i => { ppm[i] = +inp[i + '_ppm'] || 0; });

  // ---- Eqn 1. 重量分率 w_i (kg/kg) -------------------------------------
  const wt = {};
  IONS.forEach(i => { wt[i] = (ppm[i] * (water / 1000)) / (dry * 1000); });
  const total_wt = IONS.reduce((s, i) => s + wt[i], 0);

  // ---- Eqn 2. 當量濃度 e_i (mEq/kg) ------------------------------------
  const mEq = {};
  IONS.forEach(i => { mEq[i] = ((wt[i] * Z[i]) / (MOL_WTS[i] / 1000)) * 1000; });
  const total_mEq_anions  = ANIONS.reduce((s, i) => s + mEq[i], 0);
  const total_mEq_cations = CATIONS.reduce((s, i) => s + mEq[i], 0);

  // ---- Eqn 3. 初始電荷不平衡 → 決定 Pathway -----------------------------
  const charge_imbalance_initial = Math.abs(total_mEq_cations - total_mEq_anions);
  const imbalance_allocation = total_mEq_cations > total_mEq_anions
    ? 'dExcess Cations' : 'dExcess Anions';
  const Pathway1 =
    (charge_imbalance_initial <= Math.max(total_mEq_cations, total_mEq_anions) * 0.02) ||
    (total_mEq_anions > total_mEq_cations);
  const Pathway = Pathway1 ? 'Pathway 1' : 'Pathway 2';

  // ---- Eqn 4. Pathway I：陰陽離子各自等比例調整到中點 ---------------------
  const sum2 = total_mEq_anions + total_mEq_cations;
  const p1 = {};
  if (Pathway === 'Pathway 1') {
    ANIONS.forEach(i  => { p1[i] = mEq[i] * sum2 / (2 * total_mEq_anions); });
    CATIONS.forEach(i => { p1[i] = mEq[i] * sum2 / (2 * total_mEq_cations); });
  } else {
    IONS.forEach(i => { p1[i] = NaN; });
  }

  // ---- Eqn 5a–5d. Pathway II：依溶解度序 Ca → Mg → Na → K 逐級扣除 --------
  const EPS = 0.000001;
  const steps = [];        // 給教學介面顯示每一級的過程
  const p2 = {};
  let imb_Ca = NaN, imb_Mg = NaN, imb_Na = NaN, imb_K = NaN;

  if (Pathway === 'Pathway 2') {
    IONS.forEach(i => { p2[i] = mEq[i]; });

    // 5a — 鈣
    const before_Ca = p2.calcium;
    p2.calcium = Math.max(p2.calcium - charge_imbalance_initial, 0);
    imb_Ca = recheck(p2, EPS);
    steps.push(mkStep('Ca²⁺', 'calcium', before_Ca, p2.calcium, charge_imbalance_initial, imb_Ca));

    // 5b — 鎂
    const before_Mg = p2.magnesium;
    p2.magnesium = Math.max(p2.magnesium - imb_Ca, 0);
    imb_Mg = recheck(p2, EPS);
    steps.push(mkStep('Mg²⁺', 'magnesium', before_Mg, p2.magnesium, imb_Ca, imb_Mg));

    // 5c — 鈉
    const before_Na = p2.sodium;
    p2.sodium = Math.max(p2.sodium - imb_Mg, 0);
    imb_Na = recheck(p2, EPS);
    steps.push(mkStep('Na⁺', 'sodium', before_Na, p2.sodium, imb_Mg, imb_Na));

    // 5d — 鉀
    const before_K = p2.potassium;
    p2.potassium = Math.max(p2.potassium - imb_Na, 0);
    imb_K = recheck(p2, EPS);
    steps.push(mkStep('K⁺', 'potassium', before_K, p2.potassium, imb_Na, imb_K));
  } else {
    IONS.forEach(i => { p2[i] = NaN; });
  }

  // ---- 選定路徑後的調整值 -----------------------------------------------
  const mEq_adj = {};
  IONS.forEach(i => { mEq_adj[i] = (Pathway === 'Pathway 1') ? p1[i] : p2[i]; });

  // ---- Eqn 6. 石膏上限 = min(SO4, Ca) -----------------------------------
  const gypsum_content_limit = Math.min(mEq_adj.sulfate, mEq_adj.calcium);

  // ---- Eqn 7. 扣除石膏（ECOS/Runsalt 模型不處理 CaSO₄） -------------------
  const mEq_final = {};
  IONS.forEach(i => { mEq_final[i] = mEq_adj[i]; });
  mEq_final.sulfate -= gypsum_content_limit;
  mEq_final.calcium -= gypsum_content_limit;

  const charge_imbalance_final = Math.abs(
    ANIONS.reduce((s, i) => s + mEq_final[i], 0) -
    CATIONS.reduce((s, i) => s + mEq_final[i], 0)) < EPS;

  // ---- Eqn 8. 莫耳濃度與莫耳分率（ECOS 輸入） ----------------------------
  const molkg = {};
  IONS.forEach(i => { molkg[i] = mEq_final[i] / Z[i] / 1000; });
  const molsum = IONS.reduce((s, i) => s + molkg[i], 0);
  const x = {};
  IONS.forEach(i => { x[i] = molkg[i] / molsum; });

  // ---- Eqn 9. 校正幅度（占原始陽離子總和的比例） -------------------------
  const catsum0 = CATIONS.reduce((s, i) => s + mEq[i], 0);
  const fraction = {};
  CATIONS.forEach(i => {
    fraction[i] = (Pathway === 'Pathway 1') ? 0 : (mEq[i] - mEq_adj[i]) / catsum0;
  });

  // ---- Eqn 10. 校正後重量分率（ECOS 的 weight 輸入） ---------------------
  const wt_adj = {};
  IONS.forEach(i => {
    wt_adj[i] = ((mEq_final[i] * (MOL_WTS[i] / 1000)) / Z[i]) * 0.001;
  });
  const total_wt_adj = IONS.reduce((s, i) => s + wt_adj[i], 0);

  // ---- Eqn 11. 石膏含量與飽和度 ----------------------------------------
  const removed_wt   = total_wt - total_wt_adj;               // 被扣掉的部分
  const gypsum_content = gypsum_content_limit *
    (0.5 * (MOL_WTS.sulfate + MOL_WTS.calcium)) * 0.000001;
  const gypsum_capacity = (0.214 * water / 10000) / dry * 100; // 20 °C 溶解上限
  const saturation_gypsum_content = gypsum_content / gypsum_capacity;

  // SaltsR 原始欄位（注意：此欄實為「扣除量 − 石膏」，見課程單元 06 的說明）
  const total_ion_content_SaltsR = removed_wt - gypsum_content;
  // 課程建議自行計算的「總鹽含量」
  const total_salt_content = total_wt_adj + gypsum_content;

  const hypothetical_CO3 = (Pathway === 'Pathway 2')
    ? ((imb_Mg + imb_Na + imb_K) / 1000000) * (60.01 / 2) : NaN;

  const ECOS_warnings = saturation_gypsum_content > 1
    ? '石膏可能已達飽和，實際含量恐更高，建議提高稀釋倍率後重測。'
    : '無警告';

  return {
    sample_name: inp.sample_name ?? 'sample', dry_g: dry, water_ml: water,
    ppm, wt, total_wt, mEq, total_mEq_anions, total_mEq_cations,
    charge_imbalance_initial,
    charge_imbalance_pct:
      100 * charge_imbalance_initial / Math.max(total_mEq_anions, total_mEq_cations),
    imbalance_allocation, Pathway, Pathway1, Pathway2: !Pathway1,
    p1, p2, steps, mEq_adj,
    gypsum_content_limit, mEq_final, charge_imbalance_final,
    molkg, x, fraction, wt_adj, total_wt_adj,
    removed_wt, gypsum_content, gypsum_capacity, saturation_gypsum_content,
    total_ion_content_SaltsR, total_salt_content,
    hypothetical_CO3, ECOS_warnings,
    imb_Ca, imb_Mg, imb_Na, imb_K
  };

  function recheck(cur, eps) {
    const a = ANIONS.reduce((s, i) => s + cur[i], 0);
    const c = CATIONS.reduce((s, i) => s + cur[i], 0);
    return Math.abs(c - a) < eps ? 0 : c - a;
  }
  function mkStep(sym, key, before, after, subtract, leftover) {
    return {
      sym, key, before, after,
      subtract, leftover,
      absorbed: before - after,
      exhausted: after === 0 && before < subtract
    };
  }
}

/** 產生 Runsalt / ECOS 的輸入檔文字（與 SaltsR_upload_Example.txt 同格式） */
function ecosInputFile(r, opts = {}) {
  const o = Object.assign(
    { Tconst: 20, RHmin: 15, RHmax: 98, RHconst: 50, Tmin: -30, Tmax: 50, unit: 0 }, opts);
  const v = (n) => (o.unit === 0 ? r.x[n] : r.wt_adj[n]);
  return [
    `${v('sodium')}   ; Na`,
    `${v('potassium')}   ; K`,
    `${v('magnesium')}   ; Mg`,
    `${v('calcium')}   ; Ca`,
    `${v('chloride')}   ; Cl`,
    `${v('nitrate')}   ; NO3`,
    `${v('sulfate')}   ; SO4`,
    `${o.Tconst}   ; Tconst`,
    `${o.RHmin}   ; RHmin`,
    `${o.RHmax}   ; RHmax`,
    `${o.RHconst}   ; RHconst`,
    `${o.Tmin}   ; Tmin`,
    `${o.Tmax}   ; Tmax`,
    `${o.unit}   ; unit (0=mol, 1=weight)`,
    `"${r.sample_name}"   ; sample name`
  ].join('\n') + '\n';
}

/** 解析 Runsalt「Export Plot Data…」輸出檔 → [{salt, points:[{rh,mol}]}] */
function parseRunsalt(text) {
  const rows = {};
  text.split(/\r?\n/).forEach(line => {
    const t = line.trim();
    if (!t) return;
    const parts = t.split(/\s+/);
    const head = parts.shift();
    const m = head.match(/^(.*)_([XY])$/);
    if (!m) return;
    const [, salt, which] = m;
    (rows[salt] = rows[salt] || {})[which] = parts.map(Number).filter(v => !Number.isNaN(v));
  });
  return Object.entries(rows)
    .filter(([, v]) => v.X && v.Y)
    .map(([salt, v]) => {
      const n = Math.min(v.X.length, v.Y.length);
      const points = [];
      for (let i = 0; i < n; i++) points.push({ rh: v.X[i], mol: v.Y[i] });
      points.sort((a, b) => a.rh - b.rh);
      // 結晶點：該鹽存在的最高 RH（再高就全部溶解）
      const crystallisation = points.length ? points[points.length - 1].rh : null;
      return { salt, points, crystallisation };
    })
    .sort((a, b) => (b.crystallisation ?? 0) - (a.crystallisation ?? 0));
}

const SaltEngine = { saltBalance, ecosInputFile, parseRunsalt,
                     MOL_WTS, Z, IONS, ANIONS, CATIONS, ION_LABEL };

if (typeof module !== 'undefined' && module.exports) module.exports = SaltEngine;
if (typeof window !== 'undefined') window.SaltEngine = SaltEngine;
