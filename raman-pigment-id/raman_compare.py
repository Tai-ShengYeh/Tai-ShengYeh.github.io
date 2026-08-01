"""
raman_compare.py
================
教學用:銅酞菁(CuPc / Pigment Blue 15)與亮藍 FCF(Erioglaucine / 三芳基甲烷)
的拉曼指紋比對。

本腳本做四件事:
  1. 由「峰位表」合成兩種色料的參考拉曼光譜(高斯峰疊加)
  2. 畫出並排比較圖,標出診斷區(CuPc 的 pyrrole 四峰組 vs FCF 的芳香環叢集)
  3. 匯出兩個資料檔:參考光譜(給 R)、含標籤的光譜庫(給 Orange / 機器學習)
  4. 示範分析流程:基線校正 → 找峰 → 與參考庫比對(相關係數)→ 簡單分類

峰位來源:
  CuPc  — 多篇文獻一致的 18 個活性峰;相對強度錨定到實測孔雀藍樣品
  FCF   — Erioglaucine 的 SERS 特徵峰(文獻);相對強度為示意值
"""
import numpy as np
import matplotlib
from matplotlib import font_manager
_cjk = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
try:
    font_manager.fontManager.addfont(_cjk)
    matplotlib.rcParams["font.family"] = font_manager.FontProperties(fname=_cjk).get_name()
except Exception:
    pass
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from matplotlib import gridspec

# ----------------------------------------------------------------------
# 1. 峰位表  peak tables:  (wavenumber cm-1, relative intensity 0..1)
# ----------------------------------------------------------------------
CUPC = [(232,0.50),(254,0.55),(480,0.34),(593,0.16),(677,0.54),(748,0.63),
        (773,0.13),(825,0.09),(950,0.22),(1104,0.10),(1140,0.37),(1188,0.20),
        (1211,0.24),(1302,0.19),(1337,0.62),(1404,0.10),(1453,0.24),(1526,1.00)]

FCF  = [(910,0.35),(1177,0.55),(1294,0.40),(1370,0.60),(1490,0.45),
        (1534,0.50),(1587,0.85),(1619,1.00)]   # intensities illustrative

# 診斷標記
CUPC_FOUR = [748, 1337, 1453, 1526]      # pyrrole / isoindole 四峰組
FCF_RING  = [1534, 1587, 1619]           # 芳香環伸縮叢集

GRID = np.arange(200, 1751, 1.0)         # 共同波數軸


def build_spectrum(peaks, x, width=9.0):
    """由峰位表合成光譜:每個峰一個高斯,寬度 width (cm-1, sigma)。"""
    y = np.zeros_like(x, dtype=float)
    for cm, inten in peaks:
        y += inten * np.exp(-0.5 * ((x - cm) / width) ** 2)
    return y / y.max()


cupc = build_spectrum(CUPC, GRID)
fcf  = build_spectrum(FCF,  GRID)

# ----------------------------------------------------------------------
# 2. 並排比較圖
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(11, 6.4), dpi=140)
gs = gridspec.GridSpec(2, 1, hspace=0.08)
BLUE, COPPER, AMBER = "#0b7ba6", "#b3703f", "#c98a3f"

def panel(ax, x, y, color, title, diag, diag_color, diag_label):
    for cm in diag:
        ax.axvspan(cm-14, cm+14, color=diag_color, alpha=0.12, zorder=0)
    ax.plot(x, y, color=color, lw=1.6)
    peaks = CUPC if title.startswith("CuPc") else FCF
    for cm, inten in peaks:
        ax.annotate(f"{cm}", (cm, np.interp(cm, x, y)),
            textcoords="offset points", xytext=(0, 4), ha="center",
            fontsize=7.5, color="#3f5a63")
    ax.set_xlim(200, 1750); ax.set_ylim(0, 1.18)
    ax.set_ylabel("Norm. intensity", fontsize=10)
    ax.text(0.012, 0.9, title, transform=ax.transAxes, fontsize=13,
            fontweight="bold", color=color)
    ax.text(0.012, 0.74, diag_label, transform=ax.transAxes, fontsize=9,
            color=diag_color)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

ax1 = fig.add_subplot(gs[0])
panel(ax1, GRID, cupc, BLUE, "CuPc  ·  銅酞菁 (PB15)", CUPC_FOUR, COPPER,
      "診斷:pyrrole/isoindole 四峰組 748 · 1337 · 1450 · 1526")
ax1.set_xticklabels([])

ax2 = fig.add_subplot(gs[1])
panel(ax2, GRID, fcf, AMBER, "FCF  ·  亮藍 (三芳基甲烷 / Erioglaucine)",
      FCF_RING, "#8a5a2a",
      "診斷:芳香環伸縮叢集 1534 · 1587 · 1619(無 pyrrole 四峰組)")
ax2.set_xlabel("Raman shift (cm$^{-1}$)", fontsize=11)

fig.suptitle("Raman 參考指紋比較 — CuPc vs 三芳基甲烷 (FCF)",
             fontsize=13, y=0.95)
fig.text(0.5, 0.005,
         "峰位:CuPc 文獻+實測錨定;FCF 為 Erioglaucine SERS 文獻峰位(強度示意)。"
         "光譜由峰位表合成,供教學比對。", ha="center", fontsize=7.5, color="#888")
plt.savefig("raman_cupc_vs_fcf.png", dpi=150, bbox_inches="tight")
print("saved figure: raman_cupc_vs_fcf.png")

# ----------------------------------------------------------------------
# 3. 匯出資料檔
# ----------------------------------------------------------------------
# (a) 參考光譜  reference spectra — 給 R / 一般檢視
np.savetxt("raman_reference_spectra.csv",
           np.column_stack([GRID, cupc, fcf]),
           delimiter=",", header="wavenumber_cm-1,CuPc,FCF",
           comments="", fmt="%.4f")
print("saved: raman_reference_spectra.csv")

# (b) 含標籤的光譜庫 — 給 Orange / 監督式分類
#     每個 class 生 30 條:加雜訊 + 小幅波數位移(模擬儀器/樣品變異)
rng = np.random.default_rng(42)
def replicates(peaks, n=30, noise=0.02, shift_sd=2.0):
    out = []
    for _ in range(n):
        sh = rng.normal(0, shift_sd)
        p = [(cm + sh, inten * rng.normal(1, 0.05)) for cm, inten in peaks]
        y = build_spectrum(p, GRID) + rng.normal(0, noise, GRID.size)
        out.append(np.clip(y, 0, None))
    return np.array(out)

Xc, Xf = replicates(CUPC), replicates(FCF)
X = np.vstack([Xc, Xf])
y = np.array(["CuPc"] * len(Xc) + ["FCF"] * len(Xf))
# 欄名 = 波數(Orange 光譜外掛會辨識成連續特徵),最後一欄 class
header = ",".join(f"{w:.0f}" for w in GRID) + ",class"
rows = [",".join(f"{v:.4f}" for v in X[i]) + "," + y[i] for i in range(len(X))]
with open("raman_spectral_library.csv", "w") as fh:
    fh.write(header + "\n" + "\n".join(rows) + "\n")
print(f"saved: raman_spectral_library.csv  ({X.shape[0]} spectra x {GRID.size} pts)")

# ----------------------------------------------------------------------
# 4. 分析示範:基線 → 找峰 → 相關比對 → 分類
# ----------------------------------------------------------------------
def modpoly(x, y, order=5, it=24):
    """ModPoly 基線 (Lieber & Mahadevan-Jansen)。"""
    yw = y.copy()
    for _ in range(it):
        c = np.polyfit(x, yw, order)
        yw = np.minimum(yw, np.polyval(c, x))
    return np.polyval(np.polyfit(x, yw, order), x)

def pick_peaks(x, y, min_h=0.05, min_dist=9):
    idx = np.where((y[1:-1] >= y[:-2]) & (y[1:-1] > y[2:]) & (y[1:-1] >= min_h))[0] + 1
    idx = idx[np.argsort(-y[idx])]
    keep = []
    for i in idx:
        if all(abs(x[i] - x[j]) >= min_dist for j in keep):
            keep.append(i)
    return sorted(keep)

def corr_match(sample, refs):
    """與每個參考光譜的皮爾森相關係數。"""
    return {name: float(np.corrcoef(sample, r)[0, 1]) for name, r in refs.items()}

# 取庫中第一條 CuPc 樣品當「未知」樣品示範
unknown = X[0]
base = modpoly(GRID, unknown)
corr = np.clip(unknown - base, 0, None)
corr = corr / corr.max()
peaks = pick_peaks(GRID, corr)
scores = corr_match(corr, {"CuPc": cupc, "FCF": fcf})
print("\n--- 分析示範(未知樣品)---")
print("偵測峰 (cm-1):", [int(GRID[i]) for i in peaks][:12])
print("相關係數:", {k: round(v, 3) for k, v in scores.items()})
print("判定:", max(scores, key=scores.get))

# 簡單監督式分類(PCA + kNN),示範 Orange 也在做的事
try:
    from sklearn.decomposition import PCA
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import make_pipeline
    clf = make_pipeline(PCA(n_components=5), KNeighborsClassifier(3))
    acc = cross_val_score(clf, X, y, cv=5).mean()
    print(f"\nPCA(5)+kNN 5-fold 交叉驗證正確率: {acc:.3f}")
except ImportError:
    print("\n(未安裝 scikit-learn,略過分類示範)")
