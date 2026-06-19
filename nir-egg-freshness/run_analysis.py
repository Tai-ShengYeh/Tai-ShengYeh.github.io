# -*- coding: utf-8 -*-
"""
雞蛋新鮮度 NIR-PLS 教學分析腳本
資料：dataset_egg_storage.csv （SCiO 手持式近紅外光譜儀，740-1070 nm）
論文：Coronel-Reyes et al. (2018), Computers and Electronics in Agriculture 145, 1-10
產出：figures/ 內的所有教學圖檔 + 終端機列印的關鍵指標
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_predict, KFold, GroupKFold, train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.decomposition import PCA

RNG = 42
FIG = "pls_teaching/figures"
plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 120, "font.size": 11,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white",
    # 繁體中文字型（Windows 內建微軟正黑體），避免方框亂碼
    "font.sans-serif": ["Microsoft JhengHei", "Microsoft YaHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
})

# ----------------------------------------------------------------------
# 1. 讀取資料
# ----------------------------------------------------------------------
df = pd.read_csv("egg_scio_2017/dataset_egg_storage.csv")
wl = np.array([int(c.split("_")[1]) for c in df.columns if c.startswith("Spectra_")])
Xcols = [c for c in df.columns if c.startswith("Spectra_")]
X = df[Xcols].values.astype(float)
y = df["storage_days"].values.astype(float)
groups = df["sample"].values  # 蛋的編號 (1-30)，用於 group 驗證
print(f"X shape={X.shape}, y range={y.min():.0f}-{y.max():.0f}, n_eggs={len(np.unique(groups))}")

results = {}  # 收集要傳給 HTML 的數字

# ----------------------------------------------------------------------
# 2. 前處理函式
# ----------------------------------------------------------------------
def snv(spectra):
    """Standard Normal Variate：逐樣本扣平均除標準差，去散射"""
    m = spectra.mean(axis=1, keepdims=True)
    s = spectra.std(axis=1, keepdims=True)
    return (spectra - m) / s

def sg(spectra, deriv=0, window=15, poly=2):
    """Savitzky-Golay 平滑/微分"""
    return savgol_filter(spectra, window_length=window, polyorder=poly,
                         deriv=deriv, axis=1)

PRE = {
    "Raw (原始反射率)":            lambda s: s,
    "SNV":                         lambda s: snv(s),
    "SavGol 1st deriv (一階微分)": lambda s: sg(s, deriv=1, window=15, poly=2),
    "SavGol 2nd deriv (二階微分)": lambda s: sg(s, deriv=2, window=15, poly=2),
}

# ----------------------------------------------------------------------
# 圖 1：不同儲存天數的平均光譜 (重現論文 Fig.4)
# ----------------------------------------------------------------------
day_groups = [0, 1, 3, 7, 14, 21]
cmap = plt.cm.viridis(np.linspace(0, 0.95, len(day_groups)))
fig, ax = plt.subplots(figsize=(8, 5))
for c, d in zip(cmap, day_groups):
    ax.plot(wl, X[y == d].mean(axis=0), color=c, lw=2, label=f"{d} 天")
ax.set_xlabel("波長 Wavelength (nm)"); ax.set_ylabel("平均反射率 Mean reflectance")
ax.set_title("圖1　不同儲存天數的平均 NIR 光譜（重現論文 Fig.4）")
for x0, txt in [(890, "CH 3rd"), (960, "OH 2nd"), (1020, "NH 2nd")]:
    ax.axvline(x0, color="gray", ls=":", lw=1)
    ax.text(x0, ax.get_ylim()[1], txt, fontsize=8, ha="center", va="bottom", color="gray")
ax.legend(title="儲存天數", ncol=2, fontsize=9)
fig.tight_layout(); fig.savefig(f"{FIG}/fig1_mean_spectra.png", bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------
# 圖 2：四種前處理的效果比較
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
for axp, (name, fn) in zip(axes.ravel(), PRE.items()):
    Xp = fn(X)
    for c, d in zip(cmap, day_groups):
        axp.plot(wl, Xp[y == d].mean(axis=0), color=c, lw=1.5, label=f"{d}d")
    axp.set_title(name); axp.set_xlabel("Wavelength (nm)")
axes[0, 0].legend(title="day", ncol=2, fontsize=7)
fig.suptitle("圖2　四種光譜前處理對「平均光譜隨天數變化」的影響", y=1.0)
fig.tight_layout(); fig.savefig(f"{FIG}/fig2_preprocessing.png", bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------
# 3. 選元件數：每種前處理跑 10-fold CV，記錄「每一折」的 RMSE
#    -> 可畫誤差棒，並用「一倍標準誤法則 (1-SE rule)」挑出最精簡的模型
# ----------------------------------------------------------------------
def rmse(a, b):
    return float(np.sqrt(mean_squared_error(a, b)))

def cv_rmse_per_fold(Xp, y, k, cv):
    """回傳每一折的 RMSE 陣列"""
    scores = []
    for tr, te in cv.split(Xp, y):
        mdl = PLSRegression(n_components=k, scale=True).fit(Xp[tr], y[tr])
        scores.append(rmse(y[te], mdl.predict(Xp[te]).ravel()))
    return np.array(scores)

max_lv = 20
kf = KFold(n_splits=10, shuffle=True, random_state=RNG)

curves = {}   # name -> dict(mean, se, k_min, k_1se)
fig, ax = plt.subplots(figsize=(8.5, 5.2))
for (name, fn), color in zip(PRE.items(), ["#888888", "#1f77b4", "#d62728", "#2ca02c"]):
    Xp = fn(X)
    means, ses = [], []
    for k in range(1, max_lv + 1):
        s = cv_rmse_per_fold(Xp, y, k, kf)
        means.append(s.mean()); ses.append(s.std(ddof=1) / np.sqrt(len(s)))
    means, ses = np.array(means), np.array(ses)
    k_min = int(means.argmin() + 1)
    # 一倍標準誤法則：在「最小 RMSECV + 1SE」門檻內，選最小的 LV
    thresh = means[k_min - 1] + ses[k_min - 1]
    k_1se = int(np.argmax(means <= thresh) + 1)
    curves[name] = dict(mean=means.tolist(), se=ses.tolist(),
                        k_min=k_min, k_1se=k_1se,
                        rmse_min=float(means[k_min - 1]),
                        rmse_1se=float(means[k_1se - 1]))
    ax.errorbar(range(1, max_lv + 1), means, yerr=ses, color=color, ms=3.5,
                fmt="o-", capsize=2, lw=1.3, alpha=0.9,
                label=f"{name}: 1-SE→{k_1se}LV ({means[k_1se-1]:.2f}d)")
    ax.plot(k_1se, means[k_1se - 1], "*", color=color, ms=15, zorder=5)
ax.set_xlabel("PLS 潛在變數數量 n_components (LV)")
ax.set_ylabel("RMSECV (天)  ± 標準誤")
ax.set_title("圖3　10-fold RMSECV vs 潛在變數數量（★ = 一倍標準誤法則選出的精簡模型）")
ax.legend(fontsize=8.5); ax.set_xticks(range(1, max_lv + 1, 2))
fig.tight_layout(); fig.savefig(f"{FIG}/fig3_rmsecv.png", bbox_inches="tight"); plt.close(fig)
results["curves"] = curves
print("各前處理 k_min / k_1se / RMSECV:")
for n, c in curves.items():
    print(f"  {n}: k_min={c['k_min']}({c['rmse_min']:.3f})  k_1se={c['k_1se']}({c['rmse_1se']:.3f})")

# 選出整體最佳前處理（以 1-SE 模型的 RMSECV 為準 -> 兼顧準確與精簡）
best_pre = min(curves, key=lambda k: curves[k]["rmse_1se"])
best_fn = PRE[best_pre]
best_k = curves[best_pre]["k_1se"]
results["best_pre"] = best_pre
results["best_k"] = best_k
print(f"==> 最佳前處理 = {best_pre}, 精簡 n_components = {best_k}")

# ----------------------------------------------------------------------
# 4. 兩種驗證情境（教學重點：隨機 vs 依蛋分組）
# ----------------------------------------------------------------------
Xp = best_fn(X)

# (A) 隨機 train/test split（貼近論文）
Xtr, Xte, ytr, yte = train_test_split(Xp, y, test_size=0.2, random_state=RNG)
m = PLSRegression(n_components=best_k, scale=True).fit(Xtr, ytr)
yhat_te = m.predict(Xte).ravel()
yhat_cv = cross_val_predict(PLSRegression(n_components=best_k, scale=True), Xp, y, cv=kf).ravel()
scen_random = {
    "r2_test": float(r2_score(yte, yhat_te)),
    "rmse_test": rmse(yte, yhat_te),
    "r2_cv": float(r2_score(y, yhat_cv)),
    "rmsecv": rmse(y, yhat_cv),
    "mae_cv": float(mean_absolute_error(y, yhat_cv)),
}

# (B) GroupKFold 依「蛋」分組（誠實評估對新蛋的泛化）
gkf = GroupKFold(n_splits=10)
yhat_grp = cross_val_predict(PLSRegression(n_components=best_k, scale=True),
                             Xp, y, cv=gkf, groups=groups).ravel()
scen_group = {
    "r2_cv": float(r2_score(y, yhat_grp)),
    "rmsecv": rmse(y, yhat_grp),
    "mae_cv": float(mean_absolute_error(y, yhat_grp)),
}
results["scen_random"] = scen_random
results["scen_group"] = scen_group
print("隨機CV:", scen_random)
print("依蛋分組CV:", scen_group)

# ----------------------------------------------------------------------
# 圖 4：預測 vs 實際（重現論文 Fig.9a）
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 6))
ax.scatter(y, yhat_cv, s=22, alpha=0.5, edgecolor="none", color="#1f77b4", label="10-fold CV 預測")
lims = [-1, 22]
ax.plot(lims, lims, "k--", lw=1, label="理想 y=x")
z = np.polyfit(y, yhat_cv, 1)
ax.plot(np.array(lims), np.polyval(z, lims), "r-", lw=1.5, label=f"擬合線 slope={z[0]:.2f}")
ax.set_xlim(lims); ax.set_ylim(lims)
ax.set_xlabel("實際儲存天數 Actual (days)"); ax.set_ylabel("預測儲存天數 Predicted (days)")
ax.set_title(f"圖4　預測 vs 實際（{best_pre}, {best_k} LV）\n"
             f"R²={scen_random['r2_cv']:.3f}  RMSECV={scen_random['rmsecv']:.2f} 天")
ax.legend(loc="upper left", fontsize=9); ax.set_aspect("equal")
fig.tight_layout(); fig.savefig(f"{FIG}/fig4_pred_vs_actual.png", bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------
# 圖 5：殘差直方圖（重現論文 Fig.9b）
# ----------------------------------------------------------------------
resid = y - yhat_cv
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.hist(resid, bins=np.arange(-8, 8.5, 1), color="#f0c000", edgecolor="black")
ax.axvline(0, color="red", lw=1.5)
ax.set_xlabel("殘差 (實際 − 預測, 天)"); ax.set_ylabel("樣本數")
ax.set_title(f"圖5　預測誤差分布（平均偏差 bias={resid.mean():+.2f} 天）")
fig.tight_layout(); fig.savefig(f"{FIG}/fig5_residuals.png", bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------
# 圖 6：PLS 回歸係數 + VIP，找關鍵波長
# ----------------------------------------------------------------------
def vip(model, X):
    t = model.x_scores_; w = model.x_weights_; q = model.y_loadings_
    p, h = w.shape
    s = np.diag(t.T @ t @ q.T @ q).reshape(h, -1)
    total_s = s.sum()
    vips = np.sqrt(p * ((w / np.linalg.norm(w, axis=0)) ** 2 @ s).ravel() / total_s)
    return vips

m_full = PLSRegression(n_components=best_k, scale=True).fit(Xp, y)
coef = m_full.coef_.ravel()
vips = vip(m_full, Xp)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
a1.plot(wl, coef, color="#1f77b4"); a1.axhline(0, color="gray", lw=0.8)
a1.set_ylabel("回歸係數"); a1.set_title("圖6　PLS 回歸係數與 VIP（關鍵波長）")
a2.plot(wl, vips, color="#d62728"); a2.axhline(1, color="gray", ls="--", lw=1, label="VIP=1 門檻")
a2.set_ylabel("VIP"); a2.set_xlabel("波長 Wavelength (nm)"); a2.legend(fontsize=9)
for x0, txt in [(890, "CH"), (960, "OH"), (1020, "NH")]:
    for a in (a1, a2):
        a.axvline(x0, color="green", ls=":", lw=1)
    a2.text(x0, vips.max(), txt, fontsize=8, ha="center", color="green")
top_wl = wl[np.argsort(vips)[::-1][:8]]
results["top_wl"] = sorted(int(w) for w in top_wl)
fig.tight_layout(); fig.savefig(f"{FIG}/fig6_vip.png", bbox_inches="tight"); plt.close(fig)
print("VIP 最高的 8 個波長 (nm):", results["top_wl"])

# ----------------------------------------------------------------------
# 圖 7：PCA score plot（探索 + 離群值）
# ----------------------------------------------------------------------
pca = PCA(n_components=2).fit(snv(X))
sc = pca.transform(snv(X))
fig, ax = plt.subplots(figsize=(7, 5.5))
sca = ax.scatter(sc[:, 0], sc[:, 1], c=y, cmap="viridis", s=25, alpha=0.8)
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
ax.set_title("圖7　PCA 得分圖（SNV 前處理，顏色=儲存天數）")
plt.colorbar(sca, label="儲存天數")
fig.tight_layout(); fig.savefig(f"{FIG}/fig7_pca.png", bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------------
# 存出指標 JSON 供 HTML 使用
# ----------------------------------------------------------------------
results["n_samples"] = int(X.shape[0])
results["n_wl"] = int(X.shape[1])
results["n_eggs"] = int(len(np.unique(groups)))
results["pca_var"] = [float(v) for v in pca.explained_variance_ratio_[:2]]
with open("pls_teaching/figures/results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n=== 全部完成，results.json ===")
print(json.dumps(results, ensure_ascii=False, indent=2))
