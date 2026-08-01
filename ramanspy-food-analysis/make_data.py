"""
生成食品分析拉曼光譜教學資料集（合成資料，峰位依文獻設定）。
執行： python make_data.py
"""
import numpy as np
import pandas as pd
import os

rng = np.random.default_rng(20260801)
AX = np.arange(400.0, 1801.0, 2.0)          # 401-1800 cm-1, 2 cm-1 間隔
OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)


def lorentz(x, c, w, a):
    return a / (1.0 + ((x - c) / (w / 2.0)) ** 2)


def build(peaks):
    s = np.zeros_like(AX)
    for c, w, a in peaks:
        s += lorentz(AX, c, w, a)
    return s


# ---------------- 純物質參考光譜（峰位/半高寬/相對強度） ----------------
PURE = {
    # 乳糖：奶粉主要成分
    "lactose":  [(355, 14, .30), (440, 14, .45), (850, 16, .60), (1085, 14, .85),
                 (1125, 14, .60), (1265, 18, .30), (1460, 20, .55)],
    # 酪蛋白：1003 苯丙胺酸環呼吸、1655 醯胺 I
    "casein":   [(1003, 12, .70), (1240, 25, .35), (1340, 20, .30),
                 (1450, 22, .60), (1655, 30, .55)],
    # 三聚氰胺：676 cm-1 三嗪環呼吸為診斷峰
    "melamine": [(583, 12, .35), (676, 14, 1.00), (984, 14, .40), (1435, 18, .30)],
    # 澱粉：478 cm-1 為診斷峰
    "starch":   [(478, 18, .90), (865, 18, .35), (940, 16, .40), (1082, 16, .50),
                 (1126, 16, .45), (1260, 20, .30), (1380, 20, .40), (1460, 22, .45)],
    # 油脂骨架（三酸甘油酯共同峰）
    "tg_base":  [(1063, 18, .30), (1080, 18, .30), (1301, 20, .85),
                 (1441, 20, 1.00), (1745, 20, .45)],
    # 不飽和度相關（順式 C=C）
    "unsat":    [(1265, 18, 1.00), (1656, 20, .95), (3010, 20, .0)],
    # 類胡蘿蔔素（共振增強，特級初榨橄欖油特徵）
    "carotene": [(1008, 12, .35), (1156, 14, .95), (1523, 14, 1.00)],
}
PURE_S = {k: build(v) for k, v in PURE.items()}


def add_realism(y, fluor=1.0, spike_n=0, noise=0.01, seed=None):
    """加入螢光背景、宇宙射線尖峰與雜訊 —— 模擬真實儀器輸出。"""
    r = np.random.default_rng(seed)
    t = (AX - AX.min()) / (AX.max() - AX.min())
    bg = fluor * (0.9 * np.exp(-2.2 * t) + 0.5 * t ** 2 + 0.25)
    y = y + bg
    for _ in range(spike_n):
        i = r.integers(20, len(AX) - 20)
        y[i] += r.uniform(2, 5)
        y[i - 1] += r.uniform(0.3, 1.0)
    y = y + r.normal(0, noise, len(AX))
    return y


def save(name, X, meta_cols):
    df = pd.DataFrame(X, columns=[f"{v:.1f}" for v in AX])
    df = pd.concat([pd.DataFrame(meta_cols), df], axis=1)
    df.to_csv(os.path.join(OUT, name), index=False)
    print(f"  {name}: {df.shape[0]} 列 x {df.shape[1]} 欄")


# ---------------- 1. 單一條「原始」光譜（前處理教學用） ----------------
raw = 1.0 * PURE_S["lactose"] + 0.35 * PURE_S["casein"]
raw = add_realism(raw, fluor=2.5, spike_n=3, noise=0.02, seed=1)
pd.DataFrame({"raman_shift_cm-1": AX, "intensity": raw}).to_csv(
    os.path.join(OUT, "milk_powder_raw_single.csv"), index=False)
print("  milk_powder_raw_single.csv")

# ---------------- 2. 純物質參考光譜 ----------------
ref = pd.DataFrame({"raman_shift_cm-1": AX})
for k in ["lactose", "casein", "melamine", "starch", "tg_base", "carotene"]:
    ref[k] = PURE_S[k]
ref.to_csv(os.path.join(OUT, "reference_spectra.csv"), index=False)
print("  reference_spectra.csv")

# ---------------- 3. 奶粉三聚氰胺摻偽（分類 + 定量） ----------------
X, meta = [], {"sample_id": [], "melamine_pct": [], "label": []}
levels = [0.0] * 20 + list(np.round(np.linspace(0.2, 5.0, 40), 2))
for i, pct in enumerate(levels):
    base = (1.0 + rng.normal(0, .05)) * PURE_S["lactose"] + \
           (0.35 + rng.normal(0, .04)) * PURE_S["casein"]
    y = base + (pct / 100.0) * 8.0 * PURE_S["melamine"]   # 三聚氰胺散射強、靈敏度高
    y = add_realism(y, fluor=rng.uniform(1.5, 3.0),
                    spike_n=rng.integers(0, 3), noise=0.015, seed=100 + i)
    X.append(y)
    meta["sample_id"].append(f"MP{i+1:03d}")
    meta["melamine_pct"].append(pct)
    meta["label"].append("adulterated" if pct > 0 else "normal")
save("milk_powder_melamine.csv", np.array(X), meta)

# ---------------- 4. 四種食用油分類 ----------------
OILS = {   # (不飽和度係數, 類胡蘿蔔素量)
    "olive":     (0.80, 0.22),
    "sunflower": (1.30, 0.02),
    "soybean":   (1.08, 0.04),
    "coconut":   (0.12, 0.00),
}
X, meta = [], {"sample_id": [], "oil_type": []}
k = 0
for name, (u, car) in OILS.items():
    for j in range(15):
        y = PURE_S["tg_base"] * (1 + rng.normal(0, .04)) + \
            PURE_S["unsat"] * (u + rng.normal(0, .030)) + \
            PURE_S["carotene"] * (car + rng.normal(0, .008))
        y = add_realism(y, fluor=rng.uniform(0.8, 2.0),
                        spike_n=rng.integers(0, 2), noise=0.012, seed=300 + k)
        X.append(y)
        meta["sample_id"].append(f"OIL{k+1:03d}")
        meta["oil_type"].append(name)
        k += 1
save("edible_oils.csv", np.array(X), meta)

# ---------------- 5. 橄欖油摻葵花油（定量迴歸） ----------------
X, meta = [], {"sample_id": [], "sunflower_pct": []}
frac = np.round(np.linspace(0, 50, 25), 1)
frac = np.concatenate([frac, frac + rng.uniform(-1, 1, 25)]).clip(0, 50)
for i, f in enumerate(np.round(frac, 2)):
    w = f / 100.0
    u = 0.80 * (1 - w) + 1.30 * w
    car = 0.22 * (1 - w) + 0.02 * w
    y = PURE_S["tg_base"] * (1 + rng.normal(0, .02)) + \
        PURE_S["unsat"] * (u + rng.normal(0, .012)) + \
        PURE_S["carotene"] * (car + rng.normal(0, .004))
    y = add_realism(y, fluor=rng.uniform(0.8, 2.2),
                    spike_n=rng.integers(0, 2), noise=0.012, seed=500 + i)
    X.append(y)
    meta["sample_id"].append(f"ADU{i+1:03d}")
    meta["sunflower_pct"].append(float(f))
save("olive_adulteration.csv", np.array(X), meta)

# ---------------- 6. 期末小考未知樣品 ----------------
X, meta = [], {"sample_id": []}
answers = []
for i in range(6):
    kind = ["olive", "coconut", "milk_normal", "milk_melamine", "sunflower", "starch"][i]
    if kind in OILS:
        u, car = OILS[kind]
        y = PURE_S["tg_base"] + PURE_S["unsat"] * u + PURE_S["carotene"] * car
    elif kind == "milk_normal":
        y = PURE_S["lactose"] + 0.35 * PURE_S["casein"]
    elif kind == "milk_melamine":
        y = PURE_S["lactose"] + 0.35 * PURE_S["casein"] + 0.24 * PURE_S["melamine"]
    else:
        y = PURE_S["starch"]
    y = add_realism(y, fluor=rng.uniform(1.0, 2.5), spike_n=rng.integers(1, 3),
                    noise=0.015, seed=900 + i)
    X.append(y)
    meta["sample_id"].append(f"UNK{i+1}")
    answers.append(kind)
save("unknown_samples.csv", np.array(X), meta)
with open(os.path.join(OUT, "unknown_answers_TEACHER_ONLY.txt"), "w") as f:
    f.write("教師用解答（勿發給學生）\n")
    for sid, a in zip(meta["sample_id"], answers):
        f.write(f"{sid}\t{a}\n")
print("  unknown_samples.csv (+ 教師解答)")
print("完成。")
