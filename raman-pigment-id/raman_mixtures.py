"""
raman_mixtures.py
=================
教學用:混合物與「強散射主成分遮蔽次成分」。

延伸自 raman_compare.py,新增靛藍(Indigo carmine / E132)作第三個參考,
並示範:當某成分的拉曼散射截面大(強散射者,尤其共振增強),
它會在混合光譜裡佔絕大部分訊號 —— 即使它不是質量上的多數 ——
把弱散射的次成分「蓋掉」。

產出:
  fig_three_references.png   三種藍色料的純參考光譜(CuPc / 靛藍 / FCF)
  fig_masking_series.png     強散射者(CuPc)混入弱散射次成分(靛藍)的遮蔽序列
  fig_unmixing_recovery.png  用差譜 + 非負最小平方(NNLS)把被蓋掉的次成分找回來
  raman_mixture_library.csv  不同混合比例的光譜(給 Orange / 迴歸定量)

峰位來源:
  CuPc          — 文獻 + 實測錨定
  Indigo carmine— indigo/indigotin 與 IC 的 Raman/SERRS 文獻峰位(強度示意)
  FCF           — Erioglaucine SERS 文獻峰位(強度示意)
散射強度比為教學參數(真實值依分子與雷射波長之共振而定)。
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
# 峰位表  (wavenumber cm-1, relative intensity 0..1)
# ----------------------------------------------------------------------
CUPC = [(232,0.50),(254,0.55),(480,0.34),(593,0.16),(677,0.54),(748,0.63),
        (773,0.13),(825,0.09),(950,0.22),(1104,0.10),(1140,0.37),(1188,0.20),
        (1211,0.24),(1302,0.19),(1337,0.62),(1404,0.10),(1453,0.24),(1526,1.00)]
# Indigo carmine (indigotin core):強峰在 ~1580
INDIGO = [(547,0.20),(597,0.25),(676,0.30),(819,0.25),(940,0.15),(1015,0.20),
          (1097,0.18),(1130,0.30),(1184,0.35),(1250,0.55),(1311,0.45),(1360,0.50),
          (1462,0.30),(1486,0.35),(1580,1.00),(1631,0.40),(1700,0.45)]
FCF  = [(910,0.35),(1177,0.55),(1294,0.40),(1370,0.60),(1490,0.45),
        (1534,0.50),(1587,0.85),(1619,1.00)]

# 各成分的「相對散射強度」k(教學參數:CuPc 共振增強,設為強散射者)
K = {"CuPc": 8.0, "Indigo": 1.0, "FCF": 1.2}

GRID = np.arange(200, 1751, 1.0)

def build(peaks, x, width=9.0, unit=True):
    y = np.zeros_like(x, dtype=float)
    for cm, inten in peaks:
        y += inten * np.exp(-0.5 * ((x - cm) / width) ** 2)
    return y / y.max() if unit else y

cupc   = build(CUPC, GRID)
indigo = build(INDIGO, GRID)
fcf    = build(FCF, GRID)

BLUE, GREEN, AMBER = "#0b7ba6", "#2a6f5a", "#c98a3f"
COPPER = "#b3703f"

# ======================================================================
# 圖 1:三種純參考光譜
# ======================================================================
fig = plt.figure(figsize=(11, 7.6), dpi=140)
gs = gridspec.GridSpec(3, 1, hspace=0.12)
def refpanel(ax, y, color, name, peaks):
    ax.plot(GRID, y, color=color, lw=1.5)
    for cm, inten in peaks:
        if inten >= 0.3:
            ax.annotate(f"{cm}", (cm, np.interp(cm, GRID, y)),
                        textcoords="offset points", xytext=(0, 3),
                        ha="center", fontsize=7, color="#3f5a63")
    ax.set_xlim(200, 1750); ax.set_ylim(0, 1.18)
    ax.set_ylabel("Norm. int.", fontsize=9)
    ax.text(0.012, 0.82, name, transform=ax.transAxes, fontsize=12,
            fontweight="bold", color=color)
    for s in ("top", "right"): ax.spines[s].set_visible(False)

ax1 = fig.add_subplot(gs[0]); refpanel(ax1, cupc, BLUE,
    "CuPc  銅酞菁 (PB15) — 強散射者 k=8", CUPC); ax1.set_xticklabels([])
ax2 = fig.add_subplot(gs[1]); refpanel(ax2, indigo, GREEN,
    "Indigo carmine  靛藍 (E132) — 弱散射者 k=1", INDIGO); ax2.set_xticklabels([])
ax3 = fig.add_subplot(gs[2]); refpanel(ax3, fcf, AMBER,
    "FCF  亮藍 (三芳基甲烷 / E133) k=1.2", FCF)
ax3.set_xlabel("Raman shift (cm$^{-1}$)", fontsize=11)
fig.suptitle("三種藍色食用色料的拉曼參考指紋", fontsize=13, y=0.925)
plt.savefig("fig_three_references.png", dpi=150, bbox_inches="tight")
print("saved: fig_three_references.png")

# ======================================================================
# 圖 2:遮蔽序列
#   主成分 = CuPc(強散射),次成分 = 靛藍(弱散射)
#   混合訊號 = (1-f)*K_major*S_major + f*K_minor*S_minor
#   f = 次成分(靛藍)的「質量分率」
# ======================================================================
def mixture(f_minor, major=cupc, minor=indigo, kM=K["CuPc"], km=K["Indigo"]):
    sig = (1 - f_minor) * kM * major + f_minor * km * minor
    return sig / sig.max()

fracs = [1.0, 0.7, 0.5, 0.3, 0.1, 0.0]        # 靛藍質量分率
labels = ["純靛藍", "70% 靛藍", "50% 靛藍", "30% 靛藍", "10% 靛藍", "純 CuPc"]
INDIGO_DIAG = [1250, 1580]                     # 靛藍的診斷峰(挑不與 CuPc 重疊的)

fig, ax = plt.subplots(figsize=(11, 6.6), dpi=140)
for d in INDIGO_DIAG:
    ax.axvspan(d - 12, d + 12, color=GREEN, alpha=0.10, zorder=0)
for i, f in enumerate(fracs):
    y = mixture(f) + (len(fracs) - 1 - i) * 1.05
    col = GREEN if f == 1 else (BLUE if f == 0 else "#5a6b70")
    ax.plot(GRID, y, color=col, lw=1.3)
    ax.text(1730, y[-1] + 0.15, labels[i], fontsize=9, ha="right",
            color=col, fontweight="bold")
# 標出靛藍質量分率 vs 訊號分率的落差
ax.text(0.012, 0.02,
        "散射強度比 CuPc:靛藍 = 8:1 → 靛藍即使佔 50% 質量,只貢獻約 11% 訊號;\n"
        "它的診斷峰(綠色帶:1250、1580 cm⁻¹)隨含量下降很快就被 CuPc 蓋掉。",
        transform=ax.transAxes, fontsize=9.5, color="#3f5a63")
ax.set_xlim(200, 1750); ax.set_xlabel("Raman shift (cm$^{-1}$)", fontsize=11)
ax.set_yticks([]); ax.set_ylabel("(offset stack)")
ax.set_title("強散射主成分(CuPc)遮蔽弱散射次成分(靛藍)", fontsize=13)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
plt.savefig("fig_masking_series.png", dpi=150, bbox_inches="tight")
print("saved: fig_masking_series.png")

# ======================================================================
# 圖 3:把被蓋掉的次成分找回來
#   (a) 差譜:混合 − 最佳縮放的主成分參考 → 殘差顯露次成分
#   (b) NNLS 解混:估各成分的訊號貢獻
# ======================================================================
from scipy.optimize import nnls
f_true = 0.30
mix = mixture(f_true)

# (a) 差譜:用主成分參考做最小平方縮放後相減
scale = np.dot(mix, cupc) / np.dot(cupc, cupc)
residual = mix - scale * cupc
residual_n = residual / residual.max()

# (b) NNLS 解混(已知參考庫)
R = np.column_stack([cupc, indigo])
abund, _ = nnls(R, mix)
sig_frac_indigo = abund[1] / abund.sum()

fig, axes = plt.subplots(3, 1, figsize=(11, 7.2), dpi=140, sharex=True)
axes[0].plot(GRID, mix, color="#5a6b70", lw=1.3)
axes[0].set_title(f"觀測混合光譜(靛藍質量分率 {f_true:.0%},但訊號被 CuPc 主導)",
                  fontsize=11)
axes[1].plot(GRID, scale * cupc, color=BLUE, lw=1.2)
axes[1].set_title("扣除項:最佳縮放的 CuPc 參考(已知主成分)", fontsize=11)
axes[2].plot(GRID, residual_n, color=GREEN, lw=1.3)
for d in INDIGO_DIAG:
    axes[2].axvline(d, color=GREEN, ls="--", lw=1, alpha=.6)
    axes[2].annotate(f"{d}", (d, 0.8), fontsize=8, color=GREEN, ha="center")
axes[2].set_title("差譜殘差 → 靛藍的峰(1250 / 1580)重新現身", fontsize=11)
axes[2].set_xlabel("Raman shift (cm$^{-1}$)", fontsize=11)
for ax in axes:
    ax.set_xlim(200, 1750)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.suptitle("找回被遮蔽的次成分:差譜 + NNLS 解混", fontsize=13, y=0.98)
plt.savefig("fig_unmixing_recovery.png", dpi=150, bbox_inches="tight")
print("saved: fig_unmixing_recovery.png")

print(f"\n--- 解混示範(真實靛藍質量分率 {f_true:.0%})---")
print(f"NNLS 估得訊號貢獻:CuPc={abund[0]:.2f}, 靛藍={abund[1]:.2f}")
print(f"→ 靛藍的『訊號分率』約 {sig_frac_indigo:.1%}")
print("注意:訊號分率 ≠ 質量分率。要換算回質量需知道相對散射強度 k(需校正)。")

# ======================================================================
# 匯出混合物光譜庫(給 Orange:迴歸定量 / 分類)
#   每個 f 生 20 條加雜訊,target = 靛藍質量分率
# ======================================================================
rng = np.random.default_rng(7)
rows, y_reg = [], []
for f in np.linspace(0, 1, 11):
    for _ in range(20):
        m = mixture(f) + rng.normal(0, 0.02, GRID.size)
        rows.append(np.clip(m, 0, None)); y_reg.append(f)
X = np.array(rows)
header = ",".join(f"{w:.0f}" for w in GRID) + ",indigo_mass_fraction"
with open("raman_mixture_library.csv", "w") as fh:
    fh.write(header + "\n")
    for i in range(len(X)):
        fh.write(",".join(f"{v:.4f}" for v in X[i]) + f",{y_reg[i]:.3f}\n")
print(f"\nsaved: raman_mixture_library.csv  ({X.shape[0]} spectra, target=靛藍質量分率)")
