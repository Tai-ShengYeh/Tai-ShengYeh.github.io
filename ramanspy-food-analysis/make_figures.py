"""產生教學網頁用圖檔。 python make_figures.py"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ramanspy as rp
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA as skPCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_squared_error, r2_score

# ---------- 課程視覺樣式 ----------
CY = ["#0E7C7B", "#E36414", "#C8941F", "#6A4C93", "#1A1A1A", "#7BA05B"]
plt.rcParams.update({
    "text.color": "#1A1A1A",
    "font.sans-serif": ["Noto Sans CJK TC", "Noto Sans CJK JP", "WenQuanYi Zen Hei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "savefig.facecolor": "#FFFFFF",
    "axes.prop_cycle": plt.cycler(color=CY),
    "axes.edgecolor": "#D9D2BE",
    "axes.linewidth": .9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelcolor": "#403a30",
    "axes.labelsize": 9.5,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 9,
    "axes.grid": True,
    "grid.color": "#EFEBE0",
    "grid.linewidth": .7,
    "grid.linestyle": "-",
    "xtick.color": "#8a8172",
    "ytick.color": "#8a8172",
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "lines.linewidth": 1.3,
    "lines.solid_capstyle": "round",
})

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)

C = dict(main="#0E7C7B", accent="#E36414", ok="#0E7C7B", grey="#A9A092", warn="#C8941F", violet="#6A4C93")


def load(fn):
    df = pd.read_csv(os.path.join(D, fn))
    meta = [c for c in df.columns if not c.replace(".", "", 1).isdigit()]
    ax = np.array([float(c) for c in df.columns if c not in meta])
    return df[meta].reset_index(drop=True), rp.SpectralContainer(df.drop(columns=meta).values, ax)


def pipeline():
    return rp.preprocessing.Pipeline([
        rp.preprocessing.misc.Cropper(region=(450, 1800)),
        rp.preprocessing.despike.WhitakerHayes(),
        rp.preprocessing.denoise.SavGol(window_length=9, polyorder=3),
        rp.preprocessing.baseline.IModPoly(),
        rp.preprocessing.normalise.MinMax(),
    ])


# ---------- fig01 原始光譜的三個問題 ----------
raw = pd.read_csv(os.path.join(D, "milk_powder_raw_single.csv"))
x, y = raw.iloc[:, 0].values, raw.iloc[:, 1].values
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.plot(x, y, lw=.9, color=C["main"])
sp = np.argsort(y)[-3:]
ax.annotate("宇宙射線尖峰\n(cosmic ray)", xy=(x[sp[-1]], y[sp[-1]]), xytext=(x[sp[-1]] + 60, y[sp[-1]] * .92),
            color=C["accent"], fontsize=9, arrowprops=dict(arrowstyle="->", color=C["accent"]))
ax.annotate("螢光背景\n(fluorescence background)", xy=(560, 2.6), xytext=(760, 3.4),
            color=C["warn"], fontsize=9, arrowprops=dict(arrowstyle="->", color=C["warn"]))
ax.annotate("真正的拉曼峰", xy=(1085, y[np.argmin(abs(x - 1085))]), xytext=(1180, 1.4),
            color=C["ok"], fontsize=9, arrowprops=dict(arrowstyle="->", color=C["ok"]))
ax.set_xlabel("拉曼位移 Raman shift (cm$^{-1}$)")
ax.set_ylabel("強度 (a.u.)")
ax.set_title("儀器直接輸出的原始光譜：三個必須先處理的問題")
fig.savefig(os.path.join(IMG, "fig01_raw.png"))
plt.close(fig)

# ---------- fig02 前處理五步驟 ----------
sp0 = rp.Spectrum(y, x)
steps = [
    ("① 原始光譜", None),
    ("② 裁切 Cropper(450–1800)", rp.preprocessing.misc.Cropper(region=(450, 1800))),
    ("③ 去尖峰 WhitakerHayes", rp.preprocessing.despike.WhitakerHayes()),
    ("④ 平滑 SavGol(9, 3)", rp.preprocessing.denoise.SavGol(window_length=9, polyorder=3)),
    ("⑤ 基線校正 IModPoly", rp.preprocessing.baseline.IModPoly()),
    ("⑥ 歸一化 MinMax", rp.preprocessing.normalise.MinMax()),
]
fig, axes = plt.subplots(2, 3, figsize=(11, 5.2))
cur = sp0
for a, (t, st) in zip(axes.ravel(), steps):
    if st is not None:
        cur = st.apply(cur)
    a.plot(cur.spectral_axis, cur.spectral_data, lw=.9, color=C["main"])
    a.set_title(t, fontsize=10)
    a.tick_params(labelsize=8)
fig.supxlabel("拉曼位移 (cm$^{-1}$)", fontsize=10)
fig.supylabel("強度 (a.u.)", fontsize=10)
fig.suptitle("前處理流程：每一步在做什麼", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig02_steps.png"))
plt.close(fig)

# ---------- fig03 過度平滑 ----------
ref = pd.read_csv(os.path.join(D, "reference_spectra.csv"))
rx = ref["raman_shift_cm-1"].values
mel = ref["melamine"].values + np.random.default_rng(0).normal(0, .01, len(rx))
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.plot(rx, mel, lw=.9, color=C["grey"], label="未平滑")
for wl, col in [(9, C["ok"]), (31, C["warn"]), (71, C["accent"])]:
    s = rp.preprocessing.denoise.SavGol(window_length=wl, polyorder=3).apply(rp.Spectrum(mel, rx))
    ax.plot(s.spectral_axis, s.spectral_data, lw=1.3, color=col, label=f"window_length={wl}")
ax.set_xlim(560, 1100)
ax.axvline(676, ls=":", color="k", lw=.8)
ax.text(680, ax.get_ylim()[1] * .9, "676 cm$^{-1}$ 三聚氰胺診斷峰", fontsize=9)
ax.legend(fontsize=8)
ax.set_xlabel("拉曼位移 (cm$^{-1}$)")
ax.set_ylabel("強度 (a.u.)")
ax.set_title("平滑視窗開太大 → 窄峰被抹平（訊號被自己毀掉）")
fig.savefig(os.path.join(IMG, "fig03_oversmooth.png"))
plt.close(fig)

# ---------- fig04 純物質指紋 ----------
# 每條光譜先壓到固定高度再堆疊，讓每一層上方都留出放標籤的淨空
names = {"lactose": ("乳糖 Lactose", [850, 1085]), "casein": ("酪蛋白 Casein", [1003, 1655]),
         "melamine": ("三聚氰胺 Melamine", [676]), "starch": ("澱粉 Starch", [478]),
         "tg_base": ("油脂骨架 Triglyceride", [1441, 1745]),
         "carotene": ("類胡蘿蔔素 Carotenoid", [1156, 1523])}

TRACE_H, GAP = 0.78, 1.30          # 波形高度 / 每層間距 → 上方淨空 0.52 單位
fig, ax = plt.subplots(figsize=(8.6, 6.9))
for i, (k, (lab, marks)) in enumerate(names.items()):
    base = i * GAP
    yy = ref[k].values / ref[k].values.max() * TRACE_H + base
    color = CY[i % len(CY)]
    ax.axhline(base, color="#EFEBE0", lw=.8, zorder=0)          # 每層的基線
    ax.plot(rx, yy, lw=1.2, color=color, zorder=3)
    ax.text(1815, base + TRACE_H / 2, lab, fontsize=9.5, va="center",
            color=color, fontweight="bold")
    for mkr in marks:
        j = int(np.argmin(abs(rx - mkr)))
        j = max(0, j - 4) + int(np.argmax(yy[max(0, j - 4):j + 5]))  # 對到真正的峰頂
        ax.annotate(f"{mkr}", xy=(rx[j], yy[j]), xytext=(0, 9),
                    textcoords="offset points", ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold", color=C["accent"], zorder=5,
                    arrowprops=dict(arrowstyle="-", lw=.8, color=C["accent"],
                                    shrinkA=1.5, shrinkB=2.5))
ax.set_xlim(400, 1800)
ax.set_ylim(-0.18, (len(names) - 1) * GAP + TRACE_H + 0.46)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.grid(axis="y", visible=False)
ax.set_xlabel("拉曼位移 (cm$^{-1}$)")
ax.set_title("食品常見成分的拉曼「指紋」")
fig.savefig(os.path.join(IMG, "fig04_fingerprints.png"))
plt.close(fig)

# ---------- fig05/06 三聚氰胺 ----------
meta, cont = load("milk_powder_melamine.csv")
proc = pipeline().apply(cont)
X, ax_ = proc.spectral_data, proc.spectral_axis
i676 = np.argmin(abs(ax_ - 676))

fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
order = meta.melamine_pct.values
show = [np.argmin(abs(order - v)) for v in [0, 0.5, 1.5, 3.0, 5.0]]
cmap = plt.cm.viridis(np.linspace(0, .85, len(show)))
for c_, idx in zip(cmap, show):
    axs[0].plot(ax_, X[idx], lw=.9, color=c_, label=f"{order[idx]:.1f}%")
    axs[1].plot(ax_, X[idx], lw=1.3, color=c_)
axs[0].legend(title="三聚氰胺", fontsize=8, title_fontsize=8)
axs[0].set_title("奶粉光譜（前處理後）")
axs[1].set_xlim(620, 740)
axs[1].axvline(676, ls=":", color=C["accent"])
axs[1].set_title("放大 676 cm$^{-1}$ 診斷峰")
for a in axs:
    a.set_xlabel("拉曼位移 (cm$^{-1}$)")
    a.set_ylabel("強度 (a.u.)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig05_melamine.png"))
plt.close(fig)

v = X[:, i676]
norm = v[meta.label == "normal"]
thr = norm.mean() + 3 * norm.std()
fig, ax = plt.subplots(figsize=(7.2, 3.8))
ax.scatter(meta.melamine_pct, v, s=26, c=np.where(v > thr, C["accent"], C["grey"]), zorder=3)
ax.axhline(thr, ls="--", color=C["accent"], lw=1)
ax.text(3.4, thr * 1.06, f"判定閾值 = 空白均值 + 3SD = {thr:.3f}", color=C["accent"], fontsize=9)
det = meta.melamine_pct[(v > thr) & (meta.melamine_pct > 0)].min()
ax.axvline(det, ls=":", color=C["ok"])
ax.text(det + .1, v.max() * .5, f"實務偵測極限 ≈ {det:.1f}%", color=C["ok"], fontsize=9)
ax.set_xlabel("加入的三聚氰胺濃度 (%)")
ax.set_ylabel("676 cm$^{-1}$ 峰強度（歸一化後）")
ax.set_title("劑量–反應關係與偵測極限（LOD）")
fig.savefig(os.path.join(IMG, "fig06_lod.png"))
plt.close(fig)

# ---------- fig07 PCA ----------
proj, comps = rp.analysis.decompose.PCA(n_components=2).apply(proc)
pc1, pc2 = proj
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
s = axs[0].scatter(pc1, pc2, c=meta.melamine_pct, cmap="plasma", s=34, edgecolor="w", lw=.4)
plt.colorbar(s, ax=axs[0], label="三聚氰胺 (%)")
axs[0].set_xlabel("PC1")
axs[0].set_ylabel("PC2")
axs[0].set_title("PCA 分數圖：樣品自動排成一條濃度軸")
axs[1].plot(ax_, comps[0], lw=1, color=C["main"], label="PC1 loading")
axs[1].axvline(676, ls=":", color=C["accent"])
axs[1].text(690, comps[0].max() * .8, "676 cm$^{-1}$", color=C["accent"], fontsize=9)
axs[1].legend(fontsize=8)
axs[1].set_xlabel("拉曼位移 (cm$^{-1}$)")
axs[1].set_title("PC1 負荷量：模型看的是哪個峰？")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig07_pca.png"))
plt.close(fig)

# ---------- fig08 油品分類 ----------
ometa, ocont = load("edible_oils.csv")
op = pipeline().apply(ocont)
Xo, axo = op.spectral_data, op.spectral_axis
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
labs = {"olive": "橄欖油", "sunflower": "葵花油", "soybean": "大豆油", "coconut": "椰子油"}
for k, lab in labs.items():
    axs[0].plot(axo, Xo[ometa.oil_type == k].mean(0), lw=1.1, label=lab)
for w in [1265, 1441, 1523, 1656]:
    axs[0].axvline(w, ls=":", lw=.7, color="grey")
axs[0].legend(fontsize=8)
axs[0].set_title("四種食用油的平均光譜")
axs[0].set_xlabel("拉曼位移 (cm$^{-1}$)")
p2, _ = rp.analysis.decompose.PCA(n_components=2).apply(op)
for k, lab in labs.items():
    m_ = (ometa.oil_type == k).values
    axs[1].scatter(np.array(p2[0])[m_], np.array(p2[1])[m_], s=34, label=lab, edgecolor="w", lw=.4)
axs[1].legend(fontsize=8)
axs[1].set_xlabel("PC1")
axs[1].set_ylabel("PC2")
acc = cross_val_score(make_pipeline(skPCA(n_components=6), LinearDiscriminantAnalysis()),
                      Xo, ometa.oil_type.values, cv=5).mean()
axs[1].set_title(f"PCA 分數圖（PCA-LDA 交叉驗證正確率 {acc*100:.1f}%）")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig08_oils.png"))
plt.close(fig)

# ---------- fig09 PLS ----------
ameta, acont = load("olive_adulteration.csv")
ap = pipeline().apply(acont)
Xa, ya = ap.spectral_data, ameta.sunflower_pct.values
rms = []
for n in range(1, 9):
    yp = cross_val_predict(PLSRegression(n_components=n), Xa, ya, cv=5).ravel()
    rms.append(mean_squared_error(ya, yp) ** .5)
best = int(np.argmin(rms)) + 1
yp = cross_val_predict(PLSRegression(n_components=best), Xa, ya, cv=5).ravel()
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
axs[0].plot(range(1, 9), rms, "o-", color=C["main"])
axs[0].plot(best, rms[best - 1], "o", ms=12, mfc="none", mec=C["accent"], mew=2)
axs[0].set_xlabel("潛在變數個數 (LV)")
axs[0].set_ylabel("RMSECV (%)")
axs[0].set_title(f"選幾個潛在變數？→ 最低點 LV = {best}")
axs[1].scatter(ya, yp, s=34, color=C["main"], edgecolor="w", lw=.4)
lim = [-2, 55]
axs[1].plot(lim, lim, "--", color=C["grey"])
axs[1].set_xlim(lim)
axs[1].set_ylim(lim)
axs[1].set_xlabel("實際摻入葵花油 (%)")
axs[1].set_ylabel("模型預測 (%)")
axs[1].set_title(f"RMSECV = {rms[best-1]:.2f}% , R² = {r2_score(ya, yp):.3f}")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig09_pls.png"))
plt.close(fig)

print("圖檔完成：", sorted(os.listdir(IMG)))
print(f"[數據摘要] LOD={det:.2f}%  油品正確率={acc*100:.1f}%  PLS LV={best} RMSECV={rms[best-1]:.2f} R2={r2_score(ya,yp):.3f}")
