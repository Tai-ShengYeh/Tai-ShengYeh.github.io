"""
============================================================================
HPLC 分離最佳化 -- 現代 Python 版（numpy / pandas / scipy / matplotlib）
----------------------------------------------------------------------------
這是下列論文所提方法的重新實作：
    Zisi, Ch., Pappa-Louisi, A., & Nikitas, P. (2020). Separation optimization
    in HPLC analysis implemented in R programming language.
    Journal of Chromatography A, 1617, 460823.

原始 RChromOptim 套件（2019）為 base-R 程式，僅能在 Windows 上以互動方式執行
（choose.files() 選檔、locator() 滑鼠點選圖上的點）。本檔改寫為：
    - 純函式：所有計算函式不印字、不畫圖、不依賴全域狀態，只吃參數吐資料
    - 路徑以參數傳入（可為 None 使用內建範例資料），跨平台、可自動化、可寫進 CI
    - 全面向量化：層析圖模擬、梯度方程式求解皆用 numpy 陣列運算，不寫巢狀迴圈
    - 可重現：無互動輸入、無滑鼠事件，任何人在任何平台執行都得到相同結果

執行環境：Python 3.12.10、numpy 2.2.6、pandas 2.3.3、scipy 1.16.3、
          matplotlib 3.10.8（未安裝 plotly / seaborn，本檔亦不匯入它們）

授權：MIT License. Copyright (c) 2026 Tai-Sheng Yeh (葉泰聖)
      本檔為獨立重新實作，未沿用原套件的任何函式；你可以自由使用、修改、
      散布，只要保留著作權聲明。完整條款見同目錄的 LICENSE。

引用：無論如何重用本程式，都請引用上方那篇原始論文——滯留模型與最佳化方法
      是原作者的科學貢獻。論文全文與其補充材料（Data.xlsx、RChromOptim.RData
      等）之著作權屬原作者與出版者所有，未隨附於此；本檔僅內嵌一份標註出處的
      少量事實性數據摘錄（36 個滯留時間數值，約佔原工作簿 0.014%），
      用途是讓學習者能親手重現論文的已發表結果。
============================================================================
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 非互動後端：不開視窗、可在無顯示環境下存檔

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# 圖表中文字型：優先使用 Windows 內建的正黑體（若不存在則靜默退回預設字型，
# 僅影響圖片上文字是否顯示為方框，不影響任何計算結果）。
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 常數：管柱與峰形 -------------------------------------------------------
# t0 為管柱死時間（分鐘）。峰形參數採論文 i-optim 工作表中模型 1 區塊的代表值：
#   峰高     h = max(0.014, h0 + h1 * tR)
#   峰寬參數 s = s0 + s1 * tR，基底峰寬 w = 4s/sqrt(2)
T0 = 1.4
SHAPE = dict(h0=0.138, h1=-0.0038, s0=0.013, s1=0.0105)


# ---- 範例資料 ---------------------------------------------------------------
def retention_demo() -> pd.DataFrame:
    """回傳內建範例資料：9 個溶質在 4 種有機修飾劑比例下的滯留時間（分鐘）。

    資料出處：Zisi et al. (2020) 補充材料 Data.xlsx，i-ret.fit 工作表。
    管柱 Kinetex 2.6 um XB-C18 150 x 4.6 mm；移動相 乙腈/水 pH 5.7；
    t0 = 1.4 min。此處僅內嵌少量事實性數據以利教學重現，原始檔案未隨附。

    Returns:
        寬格式 DataFrame，欄位為 f, A1, A2, ..., A9。
    """
    return pd.DataFrame(
        {
            "f": [0.40, 0.45, 0.50, 0.60],
            "A1": [3.735, 3.000, 2.537, 2.013],
            "A2": [4.671, 3.650, 3.010, 2.265],
            "A3": [6.646, 5.200, 4.208, 3.000],
            "A4": [7.662, 5.600, 4.349, 2.940],
            "A5": [8.498, 5.900, 4.430, 2.910],
            "A6": [10.760, 6.850, 4.842, 3.061],
            "A7": [11.090, 8.000, 6.051, 3.866],
            "A8": [15.990, 10.380, 7.239, 4.198],
            "A9": [19.000, 12.690, 8.921, 5.085],
        }
    )


def _wide_to_long(wide: pd.DataFrame) -> pd.DataFrame:
    """把寬格式（f + 每個溶質一欄）轉成長格式 solute / f / tR。"""
    wide = wide.rename(columns=lambda c: c.strip())
    f_col = wide.columns[0]
    long = wide.melt(id_vars=f_col, var_name="solute", value_name="tR")
    long = long.rename(columns={f_col: "f"})
    long["solute"] = pd.Categorical(long["solute"], categories=list(wide.columns[1:]), ordered=True)
    return long.reset_index(drop=True)


def read_retention(path: str | Path | None = None) -> pd.DataFrame:
    """讀入 tab 分隔的滯留資料並整理成長格式。

    Args:
        path: 檔案路徑；留白（None）則使用內建範例資料 retention_demo()。
              若指定路徑，以 pandas 讀取 tab 分隔檔（原始檔的標題常帶有多餘
              空白，例如 "  t (min)  "，讀入後會自動去除頭尾空白）。

    Returns:
        長格式 DataFrame，欄位為 solute, f, tR。
    """
    if path is None:
        wide = retention_demo()
    else:
        wide = pd.read_csv(path, sep="\t")
    return _wide_to_long(wide)


# ---- 模型擬合 ---------------------------------------------------------------
def fit_model1(data: pd.DataFrame, t0: float = T0) -> pd.DataFrame:
    """以模型 1 擬合滯留資料：ln k = c0 - c1 * f。

    對每個溶質先算 k = (tR - t0) / t0，取對數後對 f 做普通最小平方線性迴歸。
    斜率取負即為 c1（因模型寫成 c0 - c1*f 而非 c0 + slope*f）。

    Args:
        data: read_retention() 的輸出，需含 solute, f, tR 欄位。
        t0: 管柱死時間。

    Returns:
        DataFrame，欄位為 solute, c0, c1, r_squared, sigma, p_c1, n。
        sigma 為殘差標準誤 sqrt(SSR/(n-2))，p_c1 為 c1（斜率）的 p 值。
    """
    if not (data["tR"] > t0).all():
        raise ValueError("所有 tR 必須大於 t0，否則 ln k 無定義")

    rows = []
    for solute, grp in data.groupby("solute", sort=False, observed=True):
        f = grp["f"].to_numpy(dtype=float)
        lnk = np.log((grp["tR"].to_numpy(dtype=float) - t0) / t0)
        n = len(f)
        res = stats.linregress(f, lnk)
        c0 = res.intercept
        c1 = -res.slope
        fitted = res.intercept + res.slope * f
        ssr = np.sum((lnk - fitted) ** 2)
        sigma = np.sqrt(ssr / (n - 2))
        rows.append(
            dict(
                solute=solute,
                c0=c0,
                c1=c1,
                r_squared=res.rvalue**2,
                sigma=sigma,
                p_c1=res.pvalue,
                n=n,
            )
        )
    return pd.DataFrame(rows)


# ---- 峰與解析度 -------------------------------------------------------------
def peak_sigma(tR: np.ndarray | float, shape: dict = SHAPE) -> np.ndarray | float:
    """峰寬參數 s = s0 + s1 * tR（類高斯峰的標準差尺度）。"""
    return shape["s0"] + shape["s1"] * tR


def peak_height(tR: np.ndarray | float, shape: dict = SHAPE) -> np.ndarray | float:
    """峰高 h = max(0.014, h0 + h1 * tR)（設下限避免晚洗出的峰高變負值）。"""
    return np.maximum(0.014, shape["h0"] + shape["h1"] * tR)


def peak_width(tR: np.ndarray | float, shape: dict = SHAPE) -> np.ndarray | float:
    """基底峰寬 w = 4 * s / sqrt(2)。"""
    return 4 * peak_sigma(tR, shape) / np.sqrt(2)


def predict_isocratic(params: pd.DataFrame, f: float, t0: float = T0) -> pd.DataFrame:
    """由模型 1 參數，預測恆溶劑（isocratic）條件下每個溶質的滯留時間與峰形。

    Args:
        params: fit_model1() 的輸出。
        f: 有機修飾劑比例。
        t0: 管柱死時間。

    Returns:
        DataFrame（依 tR 由小到大排序），欄位為 solute, f, k, tR, s, w, h。
    """
    out = params[["solute", "c0", "c1"]].copy()
    out["f"] = f
    out["k"] = np.exp(out["c0"] - out["c1"] * f)
    out["tR"] = t0 * (1 + out["k"])
    out["s"] = peak_sigma(out["tR"])
    out["w"] = peak_width(out["tR"])
    out["h"] = peak_height(out["tR"])
    out = out.drop(columns=["c0", "c1"]).sort_values("tR").reset_index(drop=True)
    return out


def resolution_table(peaks: pd.DataFrame) -> pd.DataFrame:
    """相鄰峰對（依 tR 排序後相鄰）的解析度。

    Rs = 2 * (tR2 - tR1) / (w1 + w2)

    Args:
        peaks: predict_isocratic() 或 predict_gradient() 的輸出。

    Returns:
        DataFrame，欄位為 pair（"A1/A2" 形式）, Rs。僅含相鄰峰對，共 n-1 列。
    """
    p = peaks.sort_values("tR").reset_index(drop=True)
    solute = p["solute"].astype(str).to_numpy()
    tR = p["tR"].to_numpy(dtype=float)
    w = p["w"].to_numpy(dtype=float)
    pair = [f"{solute[i]}/{solute[i + 1]}" for i in range(len(p) - 1)]
    Rs = 2 * (tR[1:] - tR[:-1]) / (w[1:] + w[:-1])
    return pd.DataFrame({"pair": pair, "Rs": Rs})


def min_resolution(peaks: pd.DataFrame) -> pd.Series:
    """相鄰峰對中解析度最差（最小 Rs）的一對，即該分離條件的瓶頸。

    Returns:
        Series，含 Rs 與 pair。若不足兩個峰則回傳 NaN。
    """
    rt = resolution_table(peaks)
    if rt.empty:
        return pd.Series({"Rs": np.nan, "pair": None})
    return rt.loc[rt["Rs"].idxmin()]


def simulate_chromatogram(peaks: pd.DataFrame, t_max: float | None = None, dt: float = 0.002) -> pd.DataFrame:
    """模擬層析圖：把每個高斯峰加總。

    y(t) = sum_j h_j * exp(-((t - tR_j) / s_j)^2)

    以 numpy 廣播（時間點 x 溶質的外積）向量化計算，不使用 Python 迴圈。

    Args:
        peaks: predict_isocratic() 或 predict_gradient() 的輸出。
        t_max: 模擬時間上限；留白則取 max(tR) * 1.15。
        dt: 時間解析度（分鐘）。

    Returns:
        DataFrame，欄位為 t, signal。
    """
    if t_max is None:
        t_max = float(peaks["tR"].max()) * 1.15
    t = np.arange(0, t_max + dt, dt)
    tR = peaks["tR"].to_numpy(dtype=float)
    s = peaks["s"].to_numpy(dtype=float)
    h = peaks["h"].to_numpy(dtype=float)
    signal = np.sum(h[None, :] * np.exp(-(((t[:, None] - tR[None, :]) / s[None, :]) ** 2)), axis=1)
    return pd.DataFrame({"t": t, "signal": signal})


# ---- 最佳化 -----------------------------------------------------------------
@dataclasses.dataclass
class OptimisationResult:
    """optimise_isocratic() 的回傳結果。"""

    scan: pd.DataFrame
    best: pd.Series | None


def scan_isocratic(
    params: pd.DataFrame,
    f: np.ndarray,
    t0: float = T0,
    shape: dict = SHAPE,
) -> pd.DataFrame:
    """一次算完整個 f 掃描的矩陣版本（對應 R 版的 scan_isocratic）。

    把每個 f 各建一個 DataFrame 再逐一呼叫 predict_isocratic + min_resolution
    的巢狀迴圈，改成單一 (溶質 x f) 矩陣運算：tR 一次算完，逐欄排序，
    解析度用矩陣位移相減求得。比逐一建立 DataFrame 快 1-2 個數量級。

    Args:
        params: fit_model1() 的輸出。
        f: 1-D numpy 陣列，欲掃描的有機修飾劑比例。
        t0: 管柱死時間。
        shape: 峰形參數。

    Returns:
        DataFrame，欄位為 f, Rs, pair, tR_max（每個 f 一列，最難分那對的 Rs）。
    """
    c0 = params["c0"].to_numpy(dtype=float)
    c1 = params["c1"].to_numpy(dtype=float)
    solute = params["solute"].astype(str).to_numpy()

    tR = t0 * (1 + np.exp(c0[:, None] - c1[:, None] * f[None, :]))  # n_solute x n_f
    ord_ = np.argsort(tR, axis=0)                                    # 每欄的沖提順序
    S = np.take_along_axis(tR, ord_, axis=0)
    W = 4 * (shape["s0"] + shape["s1"] * S) / np.sqrt(2)
    Rs = 2 * np.diff(S, axis=0) / (W[1:] + W[:-1])                   # 相鄰峰對解析度
    i = Rs.argmin(axis=0)                                             # 最難分的那一對
    Rs_min = Rs.min(axis=0)

    n_f = f.shape[0]
    pair = [f"{solute[ord_[i[j], j]]}/{solute[ord_[i[j] + 1, j]]}" for j in range(n_f)]
    tR_max = S[-1, :]

    return pd.DataFrame({"f": f, "Rs": Rs_min, "pair": pair, "tR_max": tR_max})


def optimise_isocratic(
    params: pd.DataFrame,
    f_range: tuple[float, float] = (0.30, 0.60),
    df: float = 0.005,
    t_max: float = 20,
    t0: float = T0,
) -> OptimisationResult:
    """掃描 f，找出時間預算內解析度最好的條件（對應原套件的 iopt）。

    Args:
        params: fit_model1() 的輸出。
        f_range: 搜尋範圍 (f_min, f_max)。
        df: 掃描步長。
        t_max: 可接受的最長滯留時間（時間預算，分鐘）。
        t0: 管柱死時間。

    Returns:
        OptimisationResult(scan=掃描表, best=可行解中 Rs 最大的一列)。
        掃描表欄位為 f, Rs, pair, tR_max, feasible。
    """
    f_grid = np.arange(f_range[0], f_range[1] + df / 2, df)
    scan = scan_isocratic(params, f_grid, t0)
    scan["feasible"] = scan["tR_max"] <= t_max

    feasible = scan[scan["feasible"]]
    best = feasible.loc[feasible["Rs"].idxmax()] if not feasible.empty else None
    return OptimisationResult(scan=scan, best=best)


# ---- 梯度沖提 ---------------------------------------------------------------
def predict_gradient_one(
    c0: float,
    c1: float,
    f_start: float,
    f_end: float,
    tG: float,
    tD: float,
    t0: float = T0,
    dt: float = 0.002,
    t_limit: float = 400,
) -> tuple[float, float]:
    """數值求解單一溶質的基本梯度方程式 integral(dt / (t0 * k(t))) = 1。

    phi(t) 為溶質在管柱入口看到的移動相組成：t <= tD 時維持 f_start；
    之後於 tG 分鐘內線性斜坡到 f_end；再之後維持 f_end。
    以 numpy cumsum + searchsorted 求出方程式解，不寫 Python 逐步迴圈。
    當 f_start == f_end 時，此式會退化為恆溶劑的解析解 tR = t0*(1+k)。

    Args:
        c0, c1: 該溶質的模型 1 參數。
        f_start, f_end: 梯度起訖的有機修飾劑比例。
        tG: 梯度斜坡歷時（分鐘）。
        tD: 延遲時間／初始恆溶劑保持時間（分鐘）。
        t0: 管柱死時間。
        dt: 時間步階。
        t_limit: 搜尋上限（分鐘），避免不沖提時無窮迴圈。

    Returns:
        (tR, k_elute)：滯留時間，以及沖提瞬間的 k（供計算梯度峰寬用）。
        若在 t_limit 內未沖提則回傳 (nan, nan)。
    """
    tt = np.arange(0, t_limit + dt, dt)
    phi = np.where(
        tt <= tD,
        f_start,
        np.where((tt - tD) / tG >= 1, f_end, f_start + (f_end - f_start) * (tt - tD) / tG),
    )
    k = np.exp(c0 - c1 * phi)
    prog = np.cumsum(dt / (t0 * k))  # 已走完的管柱比例

    idx = np.searchsorted(prog, 1.0)
    if idx >= len(prog):
        return np.nan, np.nan

    before = prog[idx - 1] if idx > 0 else 0.0
    frac = (1.0 - before) / (prog[idx] - before)
    te = tt[idx] + frac * dt
    k_elute = k[idx]
    return te + t0, k_elute


def predict_gradient(
    params: pd.DataFrame,
    f_start: float,
    f_end: float,
    tG: float,
    tD: float = 0.7,
    t0: float = T0,
    dt: float = 0.002,
    shape: dict = SHAPE,
) -> pd.DataFrame:
    """對每個溶質求解梯度沖提的滯留時間與峰形（向量化版本，對應 R 版 predict_gradient）。

    三個效能重點（與 R 版一致）：
      1. 梯度曲線 phi(t) 對所有溶質都一樣，只算一次（不再每個溶質各自重建
         一份 t_limit=400、200001 點的時間格點）。
      2. K = exp(c0 - c1*phi) 做成 (溶質 x 時間) 矩陣，cumsum 沿時間軸一次算完。
      3. 時間格點上限由 f_end 的恆溶劑滯留時間估出（而非固定配置 400 分鐘），
         若仍有溶質在格點內未沖提，則把上限乘以 3 重算，直到全部沖提或
         上限超過 1000（此時未沖提的溶質回傳 NaN，與原本失敗時的行為一致）。

    峰寬由沖提瞬間的 k 決定（線性溶劑強度理論，LSS）：
    等效滯留時間 t_equiv = t0 * (1 + k_elute)，以此（而非 tR 本身）
    代入 peak_sigma / peak_width / peak_height。

    Args:
        params: fit_model1() 的輸出。
        f_start, f_end: 梯度起訖組成。
        tG: 梯度斜坡歷時（分鐘）。
        tD: 延遲時間（分鐘）。
        t0: 管柱死時間。
        dt: 時間步階。
        shape: 峰形參數。

    Returns:
        DataFrame（依 tR 排序），欄位為 solute, tR, k_elute, t_equiv, s, w, h。
    """
    c0 = params["c0"].to_numpy(dtype=float)
    c1 = params["c1"].to_numpy(dtype=float)
    n = len(c0)

    limit = max(4.0, 3 * np.max(t0 * (1 + np.exp(c0 - c1 * f_end))) + tD + tG)

    while True:
        tt = np.arange(0, limit + dt, dt)
        phi = np.clip((tt - tD) / tG, 0.0, 1.0) * (f_end - f_start) + f_start
        K = np.exp(c0[:, None] - c1[:, None] * phi[None, :])  # n_solute x T
        prog = np.cumsum(dt / (t0 * K), axis=1)  # n_solute x T
        crossed = (prog >= 1).any(axis=1)
        if crossed.all() or limit > 1000:
            break
        limit *= 3

    idx = (prog >= 1).argmax(axis=1)  # 只在 crossed[i] 為真時才有意義
    tR = np.full(n, np.nan)
    k_elute = np.full(n, np.nan)
    for i in range(n):
        if not crossed[i]:
            continue
        j = idx[i]
        before = prog[i, j - 1] if j > 0 else 0.0
        frac = (1.0 - before) / (prog[i, j] - before)
        te = tt[j] + frac * dt
        tR[i] = te + t0
        k_elute[i] = K[i, j]

    out = params[["solute"]].copy()
    out["tR"] = tR
    out["k_elute"] = k_elute
    out["t_equiv"] = t0 * (1 + out["k_elute"])
    out["s"] = peak_sigma(out["t_equiv"], shape)
    out["w"] = peak_width(out["t_equiv"], shape)
    out["h"] = peak_height(out["t_equiv"], shape)
    return out.sort_values("tR").reset_index(drop=True)


# ---- 繪圖（matplotlib） ------------------------------------------------------
def plot_model1(data: pd.DataFrame, params: pd.DataFrame, t0: float = T0) -> plt.Figure:
    """模型 1 的診斷圖：ln k 對 f，實測點 + 擬合直線。"""
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    solutes = list(params["solute"])
    colors = plt.cm.tab10(np.linspace(0, 1, len(solutes)))
    f_line = np.linspace(data["f"].min() - 0.02, data["f"].max() + 0.02, 100)

    for solute, color in zip(solutes, colors):
        grp = data[data["solute"] == solute]
        lnk = np.log((grp["tR"].to_numpy(dtype=float) - t0) / t0)
        ax.scatter(grp["f"], lnk, color=color, s=20, zorder=3)
        row = params.loc[params["solute"] == solute].iloc[0]
        ax.plot(f_line, row["c0"] - row["c1"] * f_line, color=color, linewidth=1.3, label=str(solute))

    ax.set_xlabel("有機修飾劑比例  f")
    ax.set_ylabel("ln k")
    ax.set_title("模型 1：ln k = c0 - c1 · f", fontweight="bold")
    ax.legend(fontsize=7, ncol=3, loc="upper right")
    fig.tight_layout()
    return fig


def plot_chromatogram(peaks: pd.DataFrame, title: str | None = None, t_max: float | None = None) -> plt.Figure:
    """繪製模擬層析圖，並標出最小解析度與各峰的溶質標籤。"""
    chrom = simulate_chromatogram(peaks, t_max)
    worst = min_resolution(peaks)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(chrom["t"], chrom["signal"], color="#0d7377", linewidth=1.0)
    for _, row in peaks.iterrows():
        ax.annotate(str(row["solute"]), (row["tR"], row["h"]), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8, color="grey")
    ax.set_xlabel("時間 t / min")
    ax.set_ylabel("訊號")
    ax.set_title(title or "模擬層析圖", fontweight="bold")
    ax.set_ylim(top=peaks["h"].max() * 1.25)
    subtitle = f"最小 Rs = {worst['Rs']:.3f} ({worst['pair']})，最後出峰 {peaks['tR'].max():.2f} min"
    ax.text(0.5, 1.03, subtitle, transform=ax.transAxes, ha="center", fontsize=8, color="dimgrey")
    fig.tight_layout()
    return fig


def plot_optimisation(opt: OptimisationResult, rs_target: float = 1.5) -> plt.Figure:
    """最佳化掃描圖：最小 Rs 與 tR_max 對 f（對應論文 Fig. 7），雙 y 軸。"""
    scan = opt.scan
    best = opt.best
    fig, ax1 = plt.subplots(figsize=(5.5, 4.5))
    ax1.axhline(rs_target, linestyle="--", color="#2e7d4f", linewidth=1)
    l1, = ax1.plot(scan["f"], scan["Rs"], color="#0d7377", linewidth=1.5, label="最小 Rs")
    ax1.set_xlabel("有機修飾劑比例  f")
    ax1.set_ylabel("最小 Rs", color="#0d7377")

    ax2 = ax1.twinx()
    l2, = ax2.plot(scan["f"], scan["tR_max"], color="#c8632b", linewidth=1.5, label="tR_max")
    ax2.set_ylabel("tR_max / min", color="#c8632b")

    if best is not None:
        ax1.scatter([best["f"]], [best["Rs"]], color="#2e7d4f", s=50, zorder=5)
        title_sub = f"最佳 f = {best['f']:.3f}，Rs = {best['Rs']:.3f}，tR_max = {best['tR_max']:.2f} min"
    else:
        title_sub = "無可行解"

    ax1.set_title("掃描最佳化（對應 iopt）", fontweight="bold")
    ax1.text(0.5, 1.05, title_sub, transform=ax1.transAxes, ha="center", fontsize=8, color="dimgrey")
    ax1.legend(handles=[l1, l2], loc="best", fontsize=8)
    fig.tight_layout()
    return fig


# ---- 示範流程 ---------------------------------------------------------------
if __name__ == "__main__":
    data = read_retention()
    params = fit_model1(data)

    print("== 模型 1 擬合結果 ==")
    display = params.copy()
    for col in ["c0", "c1", "r_squared", "sigma", "p_c1"]:
        display[col] = display[col].round(4)
    print(display.to_string(index=False))

    print(
        f"\nc0 範圍 {params['c0'].min():.4f} - {params['c0'].max():.4f}\n"
        f"c1 範圍 {params['c1'].min():.4f} - {params['c1'].max():.4f}"
    )
    print("論文 i-optim 工作表公布值：c0 3.1404-5.6030，c1 5.9113-8.5366")

    opt20 = optimise_isocratic(params, t_max=20)
    print(
        f"\n== 最佳化 (t_max = 20) ==\n"
        f" f = {opt20.best['f']:.3f}  Rs = {opt20.best['Rs']:.4f}  "
        f"tR_max = {opt20.best['tR_max']:.2f}  最難分 = {opt20.best['pair']}"
    )

    for tm in (15, 10):
        b = optimise_isocratic(params, t_max=tm).best
        print(f" t_max = {tm:2d} -> f = {b['f']:.3f}  Rs = {b['Rs']:.3f}")

    # f = 0.350 附近會出現共沖提（A6/A7 交換出峰順序），Rs 應驟降到接近 0
    worst_350 = min_resolution(predict_isocratic(params, 0.350))
    print(f"\n== f = 0.350 的共沖提檢查 ==\n 最小 Rs = {worst_350['Rs']:.4f}（{worst_350['pair']}）")

    # 數值精度的影響：論文網頁模擬器用四位小數的公布參數，此處用全精度值
    rounded = params.copy()
    rounded["c0"] = rounded["c0"].round(4)
    rounded["c1"] = rounded["c1"].round(4)
    print(
        f"\n== 參數精度的影響 (f = 0.410) ==\n"
        f" 全精度   Rs = {min_resolution(predict_isocratic(params, 0.410))['Rs']:.4f}\n"
        f" 四位小數 Rs = {min_resolution(predict_isocratic(rounded, 0.410))['Rs']:.4f}"
    )

    g = predict_gradient(params, 0.35, 0.70, tG=11, tD=0.7)
    wg = min_resolution(g)
    print(
        f"\n== 梯度 (0.35->0.70, tG=11, tD=0.7) ==\n"
        f" Rs = {wg['Rs']:.4f} ({wg['pair']})  tR_max = {g['tR'].max():.2f}"
    )

    # 正確性檢查：起訖組成相同時，梯度數值解必須退化成恆溶劑解析解
    iso = predict_isocratic(params, 0.45)
    degen = predict_gradient(params, 0.45, 0.45, tG=15)
    iso_sorted = iso.sort_values("solute")["tR"].to_numpy()
    degen_sorted = degen.sort_values("solute")["tR"].to_numpy()
    max_diff = np.max(np.abs(iso_sorted - degen_sorted))
    assert max_diff < 1e-4, f"round-trip 檢查失敗，最大誤差 = {max_diff}"
    print(f"\n檢查通過：f_start == f_end 時梯度解退化為恆溶劑解（最大誤差 {max_diff:.2e} min < 1e-4）")

    best_peaks = predict_isocratic(params, opt20.best["f"])
    # 個別測試用的 Figure（確認各繪圖函式獨立可用）
    fig1 = plot_model1(data, params)
    fig2 = plot_optimisation(opt20)
    fig3 = plot_chromatogram(best_peaks, f"最佳條件 f = {opt20.best['f']:.3f}")
    plt.close(fig1)
    plt.close(fig2)
    plt.close(fig3)

    # 展示用整合圖：直接以 3 個子圖組成一張 PNG
    fig = plt.figure(figsize=(12, 8))
    ax_model1 = fig.add_subplot(2, 2, 1)
    ax_opt = fig.add_subplot(2, 2, 2)
    ax_chrom = fig.add_subplot(2, 1, 2)

    solutes = list(params["solute"])
    colors = plt.cm.tab10(np.linspace(0, 1, len(solutes)))
    f_line = np.linspace(data["f"].min() - 0.02, data["f"].max() + 0.02, 100)
    for solute, color in zip(solutes, colors):
        grp = data[data["solute"] == solute]
        lnk = np.log((grp["tR"].to_numpy(dtype=float) - T0) / T0)
        ax_model1.scatter(grp["f"], lnk, color=color, s=18, zorder=3)
        row = params.loc[params["solute"] == solute].iloc[0]
        ax_model1.plot(f_line, row["c0"] - row["c1"] * f_line, color=color, linewidth=1.2, label=str(solute))
    ax_model1.set_xlabel("f")
    ax_model1.set_ylabel("ln k")
    ax_model1.set_title("模型 1：ln k = c0 - c1 · f", fontweight="bold")
    ax_model1.legend(fontsize=6, ncol=3, loc="upper right")

    scan = opt20.scan
    ax_opt.axhline(1.5, linestyle="--", color="#2e7d4f", linewidth=1)
    ax_opt.plot(scan["f"], scan["Rs"], color="#0d7377", linewidth=1.5, label="最小 Rs")
    ax_opt2 = ax_opt.twinx()
    ax_opt2.plot(scan["f"], scan["tR_max"], color="#c8632b", linewidth=1.5, label="tR_max")
    ax_opt.scatter([opt20.best["f"]], [opt20.best["Rs"]], color="#2e7d4f", s=50, zorder=5)
    ax_opt.set_xlabel("f")
    ax_opt.set_ylabel("最小 Rs", color="#0d7377")
    ax_opt2.set_ylabel("tR_max / min", color="#c8632b")
    ax_opt.set_title(f"掃描最佳化：最佳 f={opt20.best['f']:.3f}, Rs={opt20.best['Rs']:.3f}", fontweight="bold", fontsize=10)

    chrom = simulate_chromatogram(best_peaks)
    ax_chrom.plot(chrom["t"], chrom["signal"], color="#0d7377", linewidth=1.0)
    for _, row in best_peaks.iterrows():
        ax_chrom.annotate(str(row["solute"]), (row["tR"], row["h"]), textcoords="offset points",
                           xytext=(0, 4), ha="center", fontsize=8, color="dimgrey")
    ax_chrom.set_ylim(top=best_peaks["h"].max() * 1.25)
    ax_chrom.set_xlabel("時間 t / min")
    ax_chrom.set_ylabel("訊號")
    ax_chrom.set_title(f"最佳條件下的模擬層析圖 (f = {opt20.best['f']:.3f})", fontweight="bold")

    fig.tight_layout()
    out_png = Path(__file__).with_name("rchromoptim_modern_demo_py.png")
    fig.savefig(out_png, dpi=130)
    print(f"\n圖已存成 {out_png}")
