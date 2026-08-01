"""建立 5 本教學 Jupyter Notebook。 python make_notebooks.py"""
import os
import nbformat as nbf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "notebooks")
os.makedirs(OUT, exist_ok=True)

SETUP = '''# ===== 第一次執行請先跑這一格（大約 1 分鐘）=====
# 在 Google Colab 上，套件不是永久安裝的，每次重開都要跑一次。
!pip install -q ramanspy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ramanspy as rp

# 讓圖上的中文正常顯示（Colab 用）
!wget -q -O TaipeiSans.ttf https://drive.google.com/uc?id=1eGAsTN1HBpJAkeVM57_C7ccp7hbgSz3_ 2>/dev/null
import matplotlib
try:
    matplotlib.font_manager.fontManager.addfont("TaipeiSans.ttf")
    matplotlib.rc("font", family="Taipei Sans TC Beta")
except Exception:
    pass
matplotlib.rcParams["axes.unicode_minus"] = False

print("準備完成！")
'''

LOADER = '''# ===== 資料載入設定 =====
# 這一行由老師部署時自動填入正確的 GitHub 網址，學生不用改。
DATA_BASE = "https://raw.githubusercontent.com/Tai-ShengYeh/Tai-ShengYeh.github.io/main/ramanspy-food-analysis/data/"

# 若你把 CSV 直接上傳到 Colab 左側「檔案」，把上面那行改成： DATA_BASE = ""
# 若你在自己電腦跑，且 data 資料夾就在旁邊，改成：       DATA_BASE = "data/"

def load_spectra(filename):
    """讀 CSV → 回傳 (樣品資訊表 meta, ramanspy 光譜物件 spectra)"""
    df = pd.read_csv(DATA_BASE + filename)
    meta_cols = [c for c in df.columns if not c.replace(".", "", 1).isdigit()]
    axis = np.array([float(c) for c in df.columns if c not in meta_cols])
    spectra = rp.SpectralContainer(df.drop(columns=meta_cols).values, axis)
    return df[meta_cols].reset_index(drop=True), spectra

print("load_spectra() 已定義，資料來源：", DATA_BASE or "（Colab 本機檔案）")
'''

PIPE = '''# 本課程統一使用的標準前處理流程
pipeline = rp.preprocessing.Pipeline([
    rp.preprocessing.misc.Cropper(region=(450, 1800)),          # 裁切
    rp.preprocessing.despike.WhitakerHayes(),                    # 去宇宙射線
    rp.preprocessing.denoise.SavGol(window_length=9, polyorder=3),  # 平滑
    rp.preprocessing.baseline.IModPoly(),                        # 基線校正
    rp.preprocessing.normalise.MinMax(),                         # 歸一化
])
'''


def nb(cells):
    n = nbf.v4.new_notebook()
    n["cells"] = cells
    n["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
    }
    return n


def md(t):
    return nbf.v4.new_markdown_cell(t)


def code(t):
    return nbf.v4.new_code_cell(t)


HEADER = """# {title}

**食品分析｜拉曼光譜與 RamanSPy 入門系列（第 {no} 本，共 5 本）**

{intro}

---
### 這一本你會學到
{goals}

> 💡 **完全沒寫過程式也沒關係。** 你只要做三件事：
> 1. 用滑鼠點每一格左邊的 ▶ 播放鍵（或按 `Shift + Enter`）
> 2. 看下面跑出來的圖和數字
> 3. 遇到 `# 👉 換你做` 的地方，照提示改一個數字或一個字，再跑一次
"""

# ============================================================ NB1
nb1 = nb([
    md(HEADER.format(no=1, title="NB1｜第一條光譜：認識工具與資料",
                     intro="拉曼光譜像是分子的「指紋」。這一本先讓你把電腦環境準備好，並成功畫出人生第一條拉曼光譜。",
                     goals="- 在 Google Colab 執行 Python（不用安裝任何東西）\n"
                           "- 知道拉曼光譜的 X 軸、Y 軸各代表什麼\n"
                           "- 用 `ramanspy` 讀進一條光譜並畫出來\n"
                           "- 看懂「原始光譜」上的三個問題")),
    md("## 0. 暖身：Python 到底在做什麼？\n\n"
       "把 Python 想成一台很聽話但很笨的實驗助理：\n\n"
       "| 你在實驗室說 | 在 Python 寫成 |\n|---|---|\n"
       "| 「把這個叫做 A」 | `A = 3` |\n"
       "| 「把這張表讀進來」 | `pd.read_csv(\"檔名.csv\")` |\n"
       "| 「畫成圖給我看」 | `rp.plot.spectra(...)` |\n"
       "| 「這是註解，你不用理」 | `# 前面加井字號` |\n\n"
       "只要照著跑，看得懂結果，就達到這門課的目標了。"),
    md("## 1. 環境準備\n\n點下面這一格左邊的 ▶ 執行。第一次會跑約 1 分鐘。"),
    code(SETUP),
    md("## 2. 拉曼光譜的兩個軸\n\n"
       "- **X 軸：拉曼位移（Raman shift, cm⁻¹）** — 對應「哪一種化學鍵在振動」。這是分子的身分證號碼，跟雷射波長無關。\n"
       "- **Y 軸：強度（Intensity, a.u.）** — 大致對應「這種鍵有多少」。但**單位是任意單位**，不同天、不同儀器不能直接比大小，所以後面一定要做歸一化。\n\n"
       "食品裡最常用到的區段是 **400–1800 cm⁻¹**，叫做**指紋區（fingerprint region）**。"),
    md("## 3. 讀入一條真實感的奶粉光譜"),
    code(LOADER),
    code('''raw = pd.read_csv(DATA_BASE + "milk_powder_raw_single.csv")
raw.head()      # 看前 5 列：第一欄是拉曼位移，第二欄是強度'''),
    code('''print("總共有", len(raw), "個資料點")
print("拉曼位移範圍：", raw.iloc[:, 0].min(), "~", raw.iloc[:, 0].max(), "cm-1")'''),
    md("### 建立 ramanspy 的光譜物件\n\n"
       "`rp.Spectrum(強度, 拉曼位移)` 會把兩欄數字包成一個「光譜物件」，之後所有分析都吃這個物件。\n\n"
       "⚠️ **順序不要寫反**：先強度、後 X 軸。"),
    code('''x = raw["raman_shift_cm-1"].values     # X 軸
y = raw["intensity"].values           # Y 軸

spectrum = rp.Spectrum(y, x)

rp.plot.spectra(spectrum, title="奶粉（原始光譜）")
rp.plot.show()'''),
    md("## 4. 看圖說故事：這張圖有三個問題\n\n"
       "仔細看剛剛那張圖：\n\n"
       "| 問題 | 長什麼樣 | 為什麼會有 | 之後怎麼解決 |\n|---|---|---|---|\n"
       "| **螢光背景** | 整條線像坐在一個大駝峰上 | 食品裡的色素、蛋白質受雷射激發放螢光，強度是拉曼訊號的數百倍 | 基線校正（baseline correction）|\n"
       "| **宇宙射線尖峰** | 一兩根又高又細的針 | 高能粒子直接打到 CCD 偵測器 | 去尖峰（despiking）|\n"
       "| **隨機雜訊** | 線條毛毛的 | 偵測器本身的電子雜訊 | 平滑（smoothing）|\n\n"
       "只有把這三個拿掉，剩下的凸起才是**真正的化學資訊**。這正是 NB2 要做的事。"),
    md("## 5. 👉 換你做\n\n把下面 `START` 和 `END` 改成不同數字，看看不同區段。\n"
       "試著找出：**哪一個區段的峰最多？**"),
    code('''START = 800     # 👉 換你做：改改看，例如 400 / 1000 / 1400
END   = 1200    # 👉 換你做：改改看，例如 700 / 1300 / 1800

plt.figure(figsize=(7, 3))
mask = (x >= START) & (x <= END)
plt.plot(x[mask], y[mask])
plt.xlabel("拉曼位移 (cm$^{-1}$)")
plt.ylabel("強度 (a.u.)")
plt.title(f"{START}–{END} cm$^{{-1}}$")
plt.show()'''),
    md("### 🧪 自我檢核（做完再往下）\n\n"
       "1. 拉曼位移的單位是什麼？它跟雷射波長有沒有關係？\n"
       "2. 為什麼 Y 軸的強度不能直接拿來比較兩天測的樣品？\n"
       "3. 原始光譜上那根又高又細的針，是樣品裡的化學成分嗎？\n\n"
       "<details><summary>▶ 點開看參考答案</summary>\n\n"
       "1. cm⁻¹（波數）。拉曼位移是「入射光與散射光的能量差」，**與雷射波長無關**，所以同一物質用不同雷射測，峰位一樣。\n"
       "2. 因為 Y 軸是任意單位（a.u.），受雷射功率、曝光時間、聚焦深度影響。要比較必須先歸一化。\n"
       "3. 不是。那是宇宙射線打到偵測器造成的假訊號，特徵是**極窄（只有 1–2 個資料點）**，真正的拉曼峰至少有數個點寬。\n\n</details>"),
])

# ============================================================ NB2
nb2 = nb([
    md(HEADER.format(no=2, title="NB2｜前處理：把難看的光譜變成能判讀的光譜",
                     intro="在食品分析裡，**前處理沒做好，後面所有結果都是垃圾**。這一本一步一步拆解 RamanSPy 的五個前處理步驟。",
                     goals="- 逐步做完裁切、去尖峰、平滑、基線校正、歸一化\n"
                           "- 理解每一步「解決什麼問題」「做過頭會怎樣」\n"
                           "- 用 `rp.preprocessing.Pipeline` 把五步驟串成一條生產線\n"
                           "- 一次處理 60 個樣品")),
    code(SETUP),
    code(LOADER),
    code('''raw = pd.read_csv(DATA_BASE + "milk_powder_raw_single.csv")
x = raw["raman_shift_cm-1"].values
y = raw["intensity"].values
spectrum = rp.Spectrum(y, x)

rp.plot.spectra(spectrum, title="① 原始光譜")
rp.plot.show()'''),
    md("## 步驟 1｜裁切 Cropper — 只留下有用的區段\n\n"
       "**解決什麼**：光譜兩端常常只有雜訊或濾片造成的假訊號。\n\n"
       "**食品分析的慣例**：留 **400–1800 cm⁻¹**（指紋區）。若要看油脂的 C–H 伸縮則另外看 2800–3000。"),
    code('''cropper = rp.preprocessing.misc.Cropper(region=(450, 1800))
s1 = cropper.apply(spectrum)

rp.plot.spectra(s1, title="② 裁切後")
rp.plot.show()
print("資料點從", len(spectrum.spectral_data), "變成", len(s1.spectral_data))'''),
    md("## 步驟 2｜去尖峰 WhitakerHayes — 清掉宇宙射線\n\n"
       "**解決什麼**：宇宙射線造成的假峰。\n\n"
       "**原理（一句話）**：真的拉曼峰有寬度，假的尖峰只有 1–2 點寬。演算法看「相鄰點的差值」異常大就判定為尖峰，用鄰居的值補回去。\n\n"
       "**做過頭會怎樣**：門檻設太嚴格，真的窄峰也會被當成尖峰刪掉。"),
    code('''despiker = rp.preprocessing.despike.WhitakerHayes()
s2 = despiker.apply(s1)

fig, axes = plt.subplots(1, 2, figsize=(11, 3))
axes[0].plot(s1.spectral_axis, s1.spectral_data); axes[0].set_title("去尖峰前")
axes[1].plot(s2.spectral_axis, s2.spectral_data); axes[1].set_title("去尖峰後")
plt.show()'''),
    md("## 步驟 3｜平滑 SavGol — 壓掉雜訊\n\n"
       "**解決什麼**：毛毛的隨機雜訊。\n\n"
       "**兩個參數**：\n"
       "- `window_length`：一次看幾個點來平均（必須是**奇數**）\n"
       "- `polyorder`：用幾次多項式去擬合（通常 2 或 3）\n\n"
       "**做過頭會怎樣**：`window_length` 開太大 → **窄峰被抹平**。下面就是這個災難的現場。"),
    code('''fig, axes = plt.subplots(1, 3, figsize=(13, 3))
for ax, wl in zip(axes, [9, 31, 71]):
    s = rp.preprocessing.denoise.SavGol(window_length=wl, polyorder=3).apply(s2)
    ax.plot(s.spectral_axis, s.spectral_data)
    ax.set_title(f"window_length = {wl}")
    ax.set_xlim(600, 1200)
plt.suptitle("平滑視窗越大，峰越矮、越胖 —— 訊號被自己毀掉")
plt.show()

s3 = rp.preprocessing.denoise.SavGol(window_length=9, polyorder=3).apply(s2)   # 採用 9'''),
    md("### 👉 換你做\n\n把 `WL` 改成 5、15、41、101，觀察 1085 cm⁻¹ 的乳糖峰高度如何變化。\n\n"
       "**思考**：如果你的目標是偵測一個很窄的摻偽物峰，平滑視窗該大還小？"),
    code('''WL = 9      # 👉 換你做

s_test = rp.preprocessing.denoise.SavGol(window_length=WL, polyorder=3).apply(s2)
i = np.argmin(abs(s_test.spectral_axis - 1085))
print(f"window_length={WL} → 1085 cm-1 峰高 = {s_test.spectral_data[i]:.3f}")'''),
    md("## 步驟 4｜基線校正 — 拿掉螢光背景（最關鍵的一步）\n\n"
       "**解決什麼**：螢光造成的大駝峰。\n\n"
       "**原理（一句話）**：演算法反覆猜一條「只走在光譜底下」的平滑曲線當作背景，再把它減掉。\n\n"
       "RamanSPy 提供十幾種方法，食品樣品常用：\n\n"
       "| 方法 | 特性 | 適用 |\n|---|---|---|\n"
       "| `IModPoly()` | 多項式迭代，穩定、快 | 一般食品樣品（本課程預設）|\n"
       "| `ASPLS()` / `ASLS()` | 懲罰最小平方，彈性大 | 背景形狀複雜時 |\n"
       "| `AIRPLS()` | 自適應加權 | 螢光極強時 |\n\n"
       "**做過頭會怎樣**：基線抓太緊 → 把寬的真實峰也一起減掉（例如蛋白質的醯胺 I 帶）。"),
    code('''from ramanspy.preprocessing import baseline

fig, axes = plt.subplots(1, 3, figsize=(13, 3))
for ax, (name, method) in zip(axes, [("IModPoly", baseline.IModPoly()),
                                     ("ASPLS", baseline.ASPLS()),
                                     ("AIRPLS", baseline.AIRPLS())]):
    s = method.apply(s3)
    ax.plot(s.spectral_axis, s.spectral_data)
    ax.set_title(name)
plt.suptitle("不同基線校正方法的結果比較")
plt.show()

s4 = baseline.IModPoly().apply(s3)'''),
    md("## 步驟 5｜歸一化 — 讓不同樣品可以互相比較\n\n"
       "**解決什麼**：Y 軸是任意單位。雷射功率變一點，整條光譜就整體變高變矮。\n\n"
       "| 方法 | 做法 | 什麼時候用 |\n|---|---|---|\n"
       "| `MinMax()` | 壓到 0–1 之間 | 最直覺，畫圖比較用 |\n"
       "| `Vector()` | 向量長度 = 1 | 做 PCA / PLS 前的標準做法 |\n"
       "| `MaxIntensity()` | 除以最大值 | 有明確參考峰時 |\n\n"
       "⚠️ **注意**：`AUC()`（面積歸一化）在新版 NumPy（2.0 以上）會報 `np.trapz` 錯誤，本課程避開不用。"),
    code('''s5 = rp.preprocessing.normalise.MinMax().apply(s4)

rp.plot.spectra(s5, title="⑥ 前處理完成")
rp.plot.show()
print("強度範圍：", round(s5.spectral_data.min(), 3), "~", round(s5.spectral_data.max(), 3))'''),
    md("## 把五步驟串成一條生產線 Pipeline\n\n"
       "上面我們一步一步做，是為了讓你看懂。實務上一行搞定，而且**順序很重要**：\n\n"
       "```\n裁切 → 去尖峰 → 平滑 → 基線校正 → 歸一化\n```\n\n"
       "**為什麼是這個順序？**\n"
       "- 去尖峰要在平滑**之前**：否則尖峰會被抹開變成一個小丘，反而更難刪。\n"
       "- 歸一化一定放**最後**：否則後面的步驟又會改變強度尺度。"),
    code(PIPE + '''
result = pipeline.apply(spectrum)
rp.plot.spectra(result, title="Pipeline 一行完成")
rp.plot.show()'''),
    md("## 一次處理 60 個樣品\n\n同一條 pipeline 可以直接套在整批資料上，不用寫迴圈。"),
    code('''meta, spectra = load_spectra("milk_powder_melamine.csv")
print("原始資料：", spectra.spectral_data.shape, "→ (樣品數, 波數點數)")

processed = pipeline.apply(spectra)
print("處理後  ：", processed.spectral_data.shape)

rp.plot.mean_spectra(processed, title="60 個奶粉樣品的平均光譜 ± 分佈")
rp.plot.show()'''),
    md("### 🧪 自我檢核\n\n"
       "1. 為什麼「去尖峰」一定要排在「平滑」前面？\n"
       "2. 為什麼「歸一化」一定要排在最後？\n"
       "3. 你要偵測一個半高寬只有 8 cm⁻¹ 的窄峰，`SavGol(window_length=71)` 合適嗎？\n"
       "4. 基線校正做過頭，最可能誤傷哪一種峰？\n\n"
       "<details><summary>▶ 點開看參考答案</summary>\n\n"
       "1. 平滑會把 1–2 點寬的尖峰抹成一個小丘，形狀變得像真的峰，之後就刪不掉了。\n"
       "2. 歸一化是把強度尺度定下來；如果後面還做基線校正或平滑，尺度又會被改變，等於白做。\n"
       "3. 不合適。資料點間隔 2 cm⁻¹ 時，71 點 = 142 cm⁻¹ 的視窗，遠寬於 8 cm⁻¹ 的峰，峰會被完全抹平。應該用 5–11。\n"
       "4. 寬帶的真實峰，例如蛋白質的醯胺 I 帶（約 1655 cm⁻¹）、水的寬帶。它們形狀跟螢光背景相似，容易被當成背景減掉。\n\n</details>"),
])

# ============================================================ NB3
nb3 = nb([
    md(HEADER.format(no=3, title="NB3｜峰位判讀：食品分子的指紋",
                     intro="會跑程式還不夠 —— 食品分析師真正的價值，是**看懂峰位代表什麼分子**。這一本把光譜和化學連起來。",
                     goals="- 用 `rp.plot.peaks()` 自動找出峰位\n"
                           "- 對照食品成分的特徵峰表\n"
                           "- 理解「強度 ≠ 含量」這個常見誤解\n"
                           "- 判讀一個未知樣品")),
    code(SETUP),
    code(LOADER),
    code(PIPE),
    md("## 1. 六種食品成分的純物質光譜"),
    code('''ref = pd.read_csv(DATA_BASE + "reference_spectra.csv")
rx = ref["raman_shift_cm-1"].values

names = {"lactose": "乳糖", "casein": "酪蛋白", "melamine": "三聚氰胺",
         "starch": "澱粉", "tg_base": "油脂骨架", "carotene": "類胡蘿蔔素"}

plt.figure(figsize=(9, 6))
for i, (k, label) in enumerate(names.items()):
    plt.plot(rx, ref[k] / ref[k].max() + i * 1.2, lw=1.1)
    plt.text(1810, i * 1.2 + 0.3, label, fontsize=10)
plt.xlim(400, 1800); plt.yticks([])
plt.xlabel("拉曼位移 (cm$^{-1}$)")
plt.title("食品常見成分的拉曼指紋")
plt.show()'''),
    md("## 2. 食品分析必背的特徵峰對照表\n\n"
       "| 波數 (cm⁻¹) | 歸屬 | 在食品裡代表 |\n|---|---|---|\n"
       "| 478 | C–C–O / 環變形 | **澱粉**（診斷峰）|\n"
       "| 676 | 三嗪環呼吸 | **三聚氰胺**（摻偽物診斷峰）|\n"
       "| 850 / 1085 / 1125 | C–C、C–O 伸縮 | 醣類（乳糖、蔗糖）|\n"
       "| 1003 | 苯環呼吸（苯丙胺酸）| **蛋白質**（強度穩定，常當內標）|\n"
       "| 1156 / 1523 | C–C（ν₂）/ C=C（ν₁）共軛鏈 | **類胡蘿蔔素**（共振增強，超強）|\n"
       "| 1265 | =C–H 面內變形（順式）| 油脂**不飽和度** |\n"
       "| 1301 | CH₂ 扭曲 | 油脂飽和鏈長 |\n"
       "| 1441 | CH₂ 剪式變形 | 油脂總量（常當內標）|\n"
       "| 1655 | C=C 伸縮 / 醯胺 I | 不飽和脂肪 **或** 蛋白質二級結構 |\n"
       "| 1745 | C=O 伸縮（酯）| 三酸甘油酯 |\n\n"
       "> ⚠️ **1655 是陷阱題**：在油脂樣品裡它是 C=C；在蛋白質樣品裡它是醯胺 I。**必須先知道基質是什麼**才能判讀。"),
    md("## 3. 讓程式自動找峰\n\n`rp.plot.peaks()` 用 `prominence`（突出度）決定「多凸才算一個峰」。"),
    code('''meta, spectra = load_spectra("milk_powder_melamine.csv")
processed = pipeline.apply(spectra)

# 挑一個摻了 5% 三聚氰胺的樣品
idx = int(meta.melamine_pct.idxmax())
one = rp.Spectrum(processed.spectral_data[idx], processed.spectral_axis)

ax, peaks, props = rp.plot.peaks(one, prominence=0.05, return_peaks=True)
rp.plot.show()
print("找到的峰位 (cm-1)：", peaks)'''),
    md("### 👉 換你做\n\n把 `PROM` 改成 0.01、0.02、0.15、0.3，觀察找到的峰數量。\n\n"
       "**思考**：`prominence` 太小會怎樣？太大會怎樣？"),
    code('''PROM = 0.05     # 👉 換你做

ax, peaks, props = rp.plot.peaks(one, prominence=PROM, return_peaks=True)
rp.plot.show()
print(f"prominence={PROM} → 找到 {len(peaks)} 個峰：{peaks}")'''),
    md("## 4. 重要觀念：強度 ≠ 含量\n\n"
       "類胡蘿蔔素在橄欖油裡只佔 **百萬分之幾**，但它的 1523 cm⁻¹ 峰卻是整張圖最強的。為什麼？\n\n"
       "因為 532 nm 綠光雷射剛好落在類胡蘿蔔素的電子吸收帶內，產生**共振拉曼增強（resonance Raman scattering）**。\n"
       "文獻上類胡蘿蔔素的共振增強倍率**約為五個數量級（~10⁵）**，最高可達六個數量級。\n\n"
       "**實務推論**：\n"
       "- 峰很強 ≠ 含量很多 → **不能用峰高直接當濃度**\n"
       "- 想定量一定要**做檢量線**（NB5 會做）\n"
       "- 強散射體會**遮蔽**弱散射體 → 主成分的峰可能把摻偽物的峰蓋掉"),
    code('''# 用油品資料看共振增強的威力
ometa, ospectra = load_spectra("edible_oils.csv")
oproc = pipeline.apply(ospectra)

plt.figure(figsize=(9, 3.5))
for k, label in [("olive", "橄欖油（含類胡蘿蔔素）"), ("coconut", "椰子油（幾乎不含）")]:
    m = (ometa.oil_type == k).values
    plt.plot(oproc.spectral_axis, oproc.spectral_data[m].mean(0), label=label)
plt.axvline(1523, ls=":", color="r"); plt.text(1530, 0.6, "1523 cm$^{-1}$", color="r")
plt.legend(); plt.xlabel("拉曼位移 (cm$^{-1}$)"); plt.title("共振增強：含量極少，訊號極強")
plt.show()'''),
    md("## 5. 實戰：判讀未知樣品\n\n下面有 6 個未知樣品。跑出來後，用上面的對照表推理它們是什麼。"),
    code('''umeta, uspectra = load_spectra("unknown_samples.csv")
uproc = pipeline.apply(uspectra)

fig, axes = plt.subplots(3, 2, figsize=(11, 8))
for i, ax in enumerate(axes.ravel()):
    ax.plot(uproc.spectral_axis, uproc.spectral_data[i], lw=.9)
    ax.set_title(umeta.sample_id[i])
    for w in [478, 676, 1003, 1085, 1441, 1523, 1745]:
        ax.axvline(w, ls=":", lw=.6, color="grey")
plt.tight_layout(); plt.show()'''),
    code('''# 幫你把幾個關鍵波數的強度列成表，方便判讀
key = [478, 676, 1003, 1085, 1441, 1523, 1656, 1745]
tab = pd.DataFrame({f"{w}": uproc.spectral_data[:, np.argmin(abs(uproc.spectral_axis - w))].round(3)
                    for w in key})
tab.insert(0, "sample", umeta.sample_id)
tab'''),
    md("### 🧪 自我檢核\n\n"
       "1. 某樣品在 478 cm⁻¹ 有強峰、1745 cm⁻¹ 幾乎沒有訊號 —— 最可能是什麼？\n"
       "2. 某奶粉樣品在 676 cm⁻¹ 出現明顯峰 —— 代表什麼？可以直接下結論說「摻了 5%」嗎？\n"
       "3. 兩個油品樣品，A 的 1265 / 1441 比值比 B 高，哪一個比較不飽和？\n"
       "4. 為什麼「1523 cm⁻¹ 峰很強」不能推論「類胡蘿蔔素含量很高」？\n\n"
       "<details><summary>▶ 點開看參考答案</summary>\n\n"
       "1. 澱粉類（478 是澱粉診斷峰，1745 酯基缺席表示不是油脂）。\n"
       "2. 代表**檢出三聚氰胺**（定性）。但不能直接說濃度 —— 定量必須先用已知濃度的標準品建立檢量線，並確認在線性範圍內。\n"
       "3. A。1265 cm⁻¹ 對應順式 =C–H，比值越高不飽和度越高；1441（CH₂）當內標。\n"
       "4. 因為共振拉曼增強。訊號強度同時取決於「含量」和「散射截面」，共振物種的散射截面可以大好幾個數量級。\n\n</details>"),
])

# ============================================================ NB4
nb4 = nb([
    md(HEADER.format(no=4, title="NB4｜應用一：奶粉三聚氰胺摻偽篩檢",
                     intro="2008 年中國毒奶粉事件中，不肖業者加入三聚氰胺以虛增蛋白質檢驗值（凱氏定氮法只測總氮）。拉曼光譜能不能當快篩工具？這一本用 60 個樣品實際檢驗。",
                     goals="- 用診斷峰 + 3SD 法則建立判定閾值\n"
                           "- 求出實務偵測極限（LOD）並誠實面對它的限制\n"
                           "- 用 PCA 做無監督的整體樣貌檢視\n"
                           "- 用 KMeans 分群，並解釋為什麼它「分錯」")),
    code(SETUP),
    code(LOADER),
    code(PIPE),
    md("## 1. 載入資料\n\n60 個奶粉樣品：20 個正常、40 個摻入 0.2–5.0% 三聚氰胺。"),
    code('''meta, spectra = load_spectra("milk_powder_melamine.csv")
processed = pipeline.apply(spectra)

print(meta.label.value_counts())
meta.head()'''),
    code('''X = processed.spectral_data
axis = processed.spectral_axis

plt.figure(figsize=(11, 3.5))
for pct in [0, 0.5, 1.5, 3.0, 5.0]:
    i = int((meta.melamine_pct - pct).abs().idxmin())
    plt.plot(axis, X[i], lw=.9, label=f"{meta.melamine_pct[i]:.1f}%")
plt.axvline(676, ls=":", color="r")
plt.legend(title="三聚氰胺"); plt.xlabel("拉曼位移 (cm$^{-1}$)")
plt.title("摻偽濃度越高，676 cm$^{-1}$ 越明顯")
plt.show()'''),
    md("## 2. 診斷峰法：抓 676 cm⁻¹\n\n三聚氰胺的三嗪環呼吸振動在 676 cm⁻¹，而奶粉基質（乳糖、酪蛋白）在這裡剛好沒有峰 —— 這叫**乾淨的分析視窗**，是好的診斷峰的必要條件。"),
    code('''i676 = np.argmin(abs(axis - 676))
peak676 = X[:, i676]

plt.figure(figsize=(7, 4))
plt.scatter(meta.melamine_pct, peak676, s=30)
plt.xlabel("加入的三聚氰胺 (%)"); plt.ylabel("676 cm$^{-1}$ 強度")
plt.title("劑量–反應關係")
plt.show()'''),
    md("## 3. 判定閾值與偵測極限（LOD）\n\n"
       "分析化學的標準做法：**閾值 = 空白樣品的平均值 + 3 × 標準差**。\n\n"
       "超過這條線就判定「檢出」，落在線下就是「未檢出」。"),
    code('''blank = peak676[meta.label == "normal"]
threshold = blank.mean() + 3 * blank.std()
print(f"空白樣品 676 強度：平均 {blank.mean():.4f}，標準差 {blank.std():.4f}")
print(f"判定閾值 = {threshold:.4f}")

detected = peak676 > threshold
lod = meta.melamine_pct[detected & (meta.melamine_pct > 0)].min()
missed = sorted(meta.melamine_pct[(~detected) & (meta.melamine_pct > 0)].values)

print(f"\\n實務偵測極限 LOD ≈ {lod:.2f} %")
print(f"漏檢的濃度（偽陰性）：{missed}")
print(f"偽陽性（正常品被誤判）：{int((detected & (meta.label=='normal')).sum())} 個")'''),
    code('''plt.figure(figsize=(7, 4))
plt.scatter(meta.melamine_pct, peak676, s=32, c=np.where(detected, "crimson", "grey"))
plt.axhline(threshold, ls="--", color="crimson")
plt.text(3.2, threshold * 1.05, "判定閾值（空白 + 3SD）", color="crimson")
plt.axvline(lod, ls=":", color="green")
plt.text(lod + 0.1, peak676.max() * 0.5, f"LOD ≈ {lod:.1f}%", color="green")
plt.xlabel("加入的三聚氰胺 (%)"); plt.ylabel("676 cm$^{-1}$ 強度")
plt.title("紅點 = 判定檢出")
plt.show()'''),
    md("## 4. ⚠️ 最重要的一課：這個方法夠用嗎？\n\n"
       "我們算出 LOD ≈ 0.5%，也就是 **5,000 mg/kg**。\n\n"
       "而國際食品法典（Codex, CXS 193-1995）對三聚氰胺的限量是：\n\n"
       "| 品項 | 限量 |\n|---|---|\n"
       "| 粉狀嬰兒配方 | 1 mg/kg |\n"
       "| 液態嬰兒配方 | 0.15 mg/kg |\n"
       "| 其他食品與飼料 | 2.5 mg/kg |\n\n"
       "**差距大約 2,000 倍以上。**\n\n"
       "所以正確的結論是：\n"
       "- ✅ 一般拉曼光譜可以當作**現場快篩**，抓出「明目張膽的大量摻假」\n"
       "- ❌ 它**不能**取代 LC-MS/MS 這類法規確認方法\n"
       "- 💡 要逼近法規限值，需要 **SERS（表面增強拉曼）**；文獻報導可將牛奶中三聚氰胺的 LOD 壓到 0.02–1 mg/L\n\n"
       "> **「未檢出」不等於「沒有」。** 任何檢驗報告都必須同時標示方法的偵測極限，否則這句話沒有意義。"),
    md("## 5. PCA：不告訴電腦答案，它能自己看出什麼？\n\n"
       "PCA（主成分分析）把 676 個波數壓縮成 2–3 個新座標，是探索資料的第一步。\n\n"
       "⚠️ **RamanSPy 的回傳格式要注意**：`projections` 是一個 list，`projections[0]` 是所有樣品的 PC1 分數。"),
    code('''pca = rp.analysis.decompose.PCA(n_components=3)
projections, components = pca.apply(processed)

pc1, pc2, pc3 = projections      # 每個都是長度 60 的陣列

plt.figure(figsize=(6.5, 4.5))
sc = plt.scatter(pc1, pc2, c=meta.melamine_pct, cmap="plasma", s=45, edgecolor="w")
plt.colorbar(sc, label="三聚氰胺 (%)")
plt.xlabel("PC1"); plt.ylabel("PC2")
plt.title("PCA 分數圖：樣品自動排成一條濃度軸")
plt.show()

print("PC1 與濃度的相關係數 =", round(np.corrcoef(pc1, meta.melamine_pct)[0, 1], 3))'''),
    md("### 一定要看負荷量（loadings）！\n\n"
       "分數圖分得開，不代表模型是對的 —— 有可能它抓到的是「量測那天溼度不同」之類的假訊號。\n"
       "**看負荷量，確認模型盯的是化學上說得通的峰。**"),
    code('''plt.figure(figsize=(9, 3.2))
plt.plot(axis, components[0], lw=1)
plt.axvline(676, ls=":", color="r"); plt.text(690, components[0].max()*0.8, "676 cm$^{-1}$", color="r")
plt.xlabel("拉曼位移 (cm$^{-1}$)"); plt.title("PC1 負荷量：模型主要在看 676 cm$^{-1}$ ✔")
plt.show()'''),
    md("## 6. KMeans 分群：以及它為什麼「分錯」"),
    code('''kmeans = rp.analysis.cluster.KMeans(n_clusters=2)
distances, centers = kmeans.apply(processed)

# distances[0]、distances[1] 是到兩個群中心的距離 → 取較近的那一群
labels = np.argmin(np.array(distances), axis=0)

print(pd.crosstab(labels, meta.label, rownames=["分群結果"], colnames=["真實標籤"]))
print()
for g in [0, 1]:
    print(f"第 {g} 群的三聚氰胺濃度範圍：{meta.melamine_pct[labels==g].min():.2f} – {meta.melamine_pct[labels==g].max():.2f} %")'''),
    md("### 為什麼分群結果和標籤對不起來？\n\n"
       "因為 KMeans 是**無監督**的 —— 它不知道「正常 / 摻偽」這個定義，它只會照**光譜的相似度**分堆。\n\n"
       "而摻了 0.2% 的樣品，光譜長得幾乎和正常品一模一樣（低於 LOD），所以被歸到同一群，**這在光譜上是正確的**。\n\n"
       "**結論**：分群結果對不上標籤，通常不是演算法壞掉，而是在告訴你 **「這兩類在你量的訊號上本來就分不開」**。這是一個非常有價值的資訊。"),
    md("### 🧪 自我檢核\n\n"
       "1. 為什麼選 676 cm⁻¹ 當診斷峰，而不是三聚氰胺其他的峰？\n"
       "2. 閾值用「空白 + 3SD」，這代表偽陽性率大約多少？\n"
       "3. 檢驗報告寫「三聚氰胺未檢出」，一個食品分析師應該追問什麼？\n"
       "4. PCA 分數圖把兩組分得很開，可以直接發表說「拉曼能區分摻偽奶粉」嗎？\n\n"
       "<details><summary>▶ 點開看參考答案</summary>\n\n"
       "1. 因為 676 cm⁻¹ 同時滿足兩個條件：(a) 它是三聚氰胺最強的峰；(b) 奶粉基質在該處沒有干擾峰（乾淨的分析視窗）。診斷峰的價值來自「強」+「不重疊」。\n"
       "2. 常態分佈下超過 +3SD 的機率約 0.13%，所以偽陽性率約 0.1%。（3SD 對應 LOD；定量極限 LOQ 通常用 10SD。）\n"
       "3. 追問**方法的偵測極限是多少**，以及是否低於法規限量。用 LOD = 0.5% 的方法測出「未檢出」，對 2.5 mg/kg 的法規限量完全沒有意義。\n"
       "4. 不行。必須 (a) 檢查負荷量確認抓到的是化學訊號、(b) 用獨立的驗證集或交叉驗證，而不是只看訓練資料的分數圖。分數圖分得開很容易，過度配適也很容易。\n\n</details>"),
])

# ============================================================ NB5
nb5 = nb([
    md(HEADER.format(no=5, title="NB5｜應用二：食用油鑑別與摻混定量",
                     intro="橄欖油摻入便宜的葵花油是全球最常見的食品詐欺之一。這一本做兩件食品分析師的核心工作：**分類（是什麼油）** 和 **定量（摻了多少）**。",
                     goals="- 用 PCA + LDA 分辨四種食用油\n"
                           "- 用 PLS 迴歸建立摻混比例的檢量線\n"
                           "- 學會用交叉驗證選模型、用 RMSECV / R² 評估\n"
                           "- 理解「模型看的是哪個峰」為什麼比準確率更重要")),
    code(SETUP),
    code(LOADER),
    code(PIPE),
    md("## Part A｜分類：這是哪一種油？"),
    code('''meta, spectra = load_spectra("edible_oils.csv")
proc = pipeline.apply(spectra)
X, axis = proc.spectral_data, proc.spectral_axis
y = meta.oil_type.values

print(meta.oil_type.value_counts())'''),
    code('''labels = {"olive": "橄欖油", "sunflower": "葵花油", "soybean": "大豆油", "coconut": "椰子油"}

plt.figure(figsize=(10, 4))
for k, lab in labels.items():
    plt.plot(axis, X[meta.oil_type == k].mean(0), lw=1.1, label=lab)
for w, txt in [(1265, "=C-H"), (1441, "CH$_2$"), (1523, "類胡蘿蔔素"), (1656, "C=C"), (1745, "C=O")]:
    plt.axvline(w, ls=":", lw=.7, color="grey")
    plt.text(w, 1.02, txt, fontsize=8, rotation=90, va="bottom")
plt.legend(); plt.xlabel("拉曼位移 (cm$^{-1}$)"); plt.title("四種食用油的平均光譜")
plt.show()'''),
    md("### 先用「化學家的方法」：算一個比值\n\n"
       "不用機器學習，光是 **1265 / 1441 比值**（不飽和度指標）就能分開大部分油品。\n"
       "**做分析永遠先試最簡單的方法。**"),
    code('''i1265 = np.argmin(abs(axis - 1265))
i1441 = np.argmin(abs(axis - 1441))
ratio = X[:, i1265] / X[:, i1441]

for k, lab in labels.items():
    v = ratio[(meta.oil_type == k).values]
    print(f"{lab}：1265/1441 = {v.mean():.3f} ± {v.std():.3f}")

plt.figure(figsize=(7, 3.5))
plt.boxplot([ratio[(meta.oil_type == k).values] for k in labels])
plt.xticks(range(1, 5), list(labels.values()))
plt.ylabel("1265 / 1441 比值（不飽和度指標）")
plt.show()'''),
    md("### 再用機器學習：PCA + LDA\n\n"
       "- **PCA** 先把 676 個波數壓成 6 個主成分（避免變數比樣品還多而過度配適）\n"
       "- **LDA** 再找出最能分開四類的方向\n"
       "- **交叉驗證**：把資料切 5 份，輪流拿 1 份當考卷、4 份當課本 —— 這才是誠實的成績"),
    code('''from sklearn.decomposition import PCA as skPCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import confusion_matrix

model = make_pipeline(skPCA(n_components=6), LinearDiscriminantAnalysis())

scores = cross_val_score(model, X, y, cv=5)
print("5 折交叉驗證正確率：", scores.round(3))
print("平均 = %.1f%%" % (scores.mean() * 100))

pred = cross_val_predict(model, X, y, cv=5)
cm = pd.DataFrame(confusion_matrix(y, pred), index=sorted(set(y)), columns=sorted(set(y)))
print("\\n混淆矩陣（列 = 真實，欄 = 預測）"); print(cm)'''),
    md("### 👉 換你做\n\n"
       "把 `N_PC` 改成 2、3、10、20，看正確率怎麼變。\n\n"
       "**思考**：主成分不是越多越好，為什麼？（提示：只有 60 個樣品）"),
    code('''N_PC = 6      # 👉 換你做

m = make_pipeline(skPCA(n_components=N_PC), LinearDiscriminantAnalysis())
print(f"n_components={N_PC} → 交叉驗證正確率 = {cross_val_score(m, X, y, cv=5).mean()*100:.1f}%")'''),
    md("## Part B｜定量：橄欖油裡摻了多少葵花油？\n\n"
       "50 個樣品，摻入比例 0–50%。這是典型的**多變量校正**問題，標準工具是 **PLS 迴歸**。\n\n"
       "**PLS 一句話**：同時壓縮光譜和濃度，找出「跟濃度最相關」的光譜變化方向。"),
    code('''ameta, aspectra = load_spectra("olive_adulteration.csv")
aproc = pipeline.apply(aspectra)
Xa, ya = aproc.spectral_data, ameta.sunflower_pct.values

print("樣品數：", len(ya), "｜ 摻入比例範圍：", ya.min(), "-", ya.max(), "%")'''),
    md("### 步驟 1：決定要用幾個潛在變數（LV）\n\n"
       "- LV 太少 → **配適不足**，模型抓不到訊息\n"
       "- LV 太多 → **過度配適**，模型把雜訊也背起來，對新樣品失準\n\n"
       "做法：畫 **RMSECV vs LV** 曲線，取最低點（或最低點附近最小的 LV）。"),
    code('''from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import mean_squared_error, r2_score

rmsecv = []
for n in range(1, 11):
    pred = cross_val_predict(PLSRegression(n_components=n), Xa, ya, cv=5).ravel()
    rmsecv.append(mean_squared_error(ya, pred) ** 0.5)

best_lv = int(np.argmin(rmsecv)) + 1

plt.figure(figsize=(6, 3.5))
plt.plot(range(1, 11), rmsecv, "o-")
plt.plot(best_lv, rmsecv[best_lv-1], "o", ms=13, mfc="none", mec="crimson", mew=2)
plt.xlabel("潛在變數個數 (LV)"); plt.ylabel("RMSECV (%)")
plt.title(f"最佳 LV = {best_lv}")
plt.show()

for n, r in enumerate(rmsecv, 1):
    print(f"LV={n:2d}  RMSECV = {r:.2f} %")'''),
    md("### 步驟 2：建立模型並評估"),
    code('''pls = PLSRegression(n_components=best_lv)
pred = cross_val_predict(pls, Xa, ya, cv=5).ravel()

rmse = mean_squared_error(ya, pred) ** 0.5
r2 = r2_score(ya, pred)

plt.figure(figsize=(5, 5))
plt.scatter(ya, pred, s=35)
plt.plot([0, 50], [0, 50], "--", color="grey")
plt.xlabel("實際摻入葵花油 (%)"); plt.ylabel("模型預測 (%)")
plt.title(f"RMSECV = {rmse:.2f} % ，R² = {r2:.3f}")
plt.show()

print(f"平均而言，模型的預測誤差約 ± {rmse:.1f} 個百分點。")
print(f"→ 也就是說，摻入 5% 以下的樣品，這個方法很可能抓不出來。")'''),
    md("### 步驟 3：檢查模型在看哪裡（絕對不能跳過）"),
    code('''pls.fit(Xa, ya)
coef = pls.coef_.ravel()

plt.figure(figsize=(10, 3.5))
plt.plot(aproc.spectral_axis, coef, lw=1)
plt.axhline(0, color="grey", lw=.6)
for w in [1265, 1441, 1523, 1656]:
    plt.axvline(w, ls=":", lw=.8, color="crimson")
    plt.text(w, coef.max()*0.85, str(w), fontsize=8, rotation=90, color="crimson")
plt.xlabel("拉曼位移 (cm$^{-1}$)"); plt.ylabel("PLS 迴歸係數")
plt.title("模型倚重哪些波數？")
plt.show()'''),
    md("**判讀**：係數的大值應該落在 **1265（不飽和度）、1523（類胡蘿蔔素）、1656（C=C）** 附近 —— 這些正是橄欖油與葵花油真正的化學差異。\n\n"
       "如果模型的大係數落在光譜的空白區或邊緣，那就是它抓到了雜訊或某種假相關，**準確率再高也不能信**。"),
    md("## Part C｜綜合實作：判讀 6 個未知樣品"),
    code('''umeta, uspectra = load_spectra("unknown_samples.csv")
uproc = pipeline.apply(uspectra)
Xu = uproc.spectral_data
uaxis = uproc.spectral_axis

key = {"478 澱粉": 478, "676 三聚氰胺": 676, "1003 蛋白質": 1003,
       "1085 醣類": 1085, "1441 油脂": 1441, "1523 類胡蘿蔔素": 1523, "1745 酯": 1745}
tab = pd.DataFrame({k: Xu[:, np.argmin(abs(uaxis - w))].round(3) for k, w in key.items()})
tab.insert(0, "樣品", umeta.sample_id)
tab'''),
    code('''# 👉 換你做：先自己從上表推理，再跑這一格看模型怎麼說
model.fit(X, y)                      # 用 Part A 的油品模型
油品判定 = model.predict(Xu)

for sid, p, oil_signal in zip(umeta.sample_id, 油品判定, Xu[:, np.argmin(abs(uaxis - 1745))]):
    note = labels.get(p, p) if oil_signal > 0.15 else "→ 1745 訊號太弱，恐怕不是油品，勿用此模型"
    print(f"{sid}：{note}")'''),
    md("> ⚠️ **上面示範了機器學習最危險的陷阱**：模型只會在它學過的四類裡挑一個，**它不會說「我不知道」**。\n"
       "> 奶粉樣品丟進油品分類器，一樣會得到一個看起來很肯定的答案。\n"
       "> 所以實務上一定要先做**樣品是否落在模型適用範圍內**的檢查（例如殘差、馬氏距離，或像這裡用 1745 cm⁻¹ 判斷是不是油）。"),
    md("### 🧪 自我檢核\n\n"
       "1. RMSECV = 3.3%，代表這個方法能不能可靠偵測 2% 的摻混？\n"
       "2. 為什麼要用交叉驗證，而不是直接看模型對訓練資料的預測有多準？\n"
       "3. PLS 的 LV 從 4 增加到 10，訓練誤差一定變小，但 RMSECV 卻上升 —— 這叫什麼現象？\n"
       "4. 一個分類模型交叉驗證正確率 99%，但迴歸係數的大值落在光譜邊緣的空白區。你會怎麼做？\n"
       "5. 把一個奶粉樣品丟進油品分類器，會發生什麼事？實務上怎麼防？\n\n"
       "<details><summary>▶ 點開看參考答案</summary>\n\n"
       "1. 不能。誤差 ±3.3 個百分點，2% 的摻混完全落在誤差範圍內。一般以 RMSECV 的 3 倍左右估計實用偵測下限，大約 10%。\n"
       "2. 因為模型對自己看過的資料一定準（甚至可以 100%），那個數字不能代表它對新樣品的表現。交叉驗證模擬「遇到沒看過的樣品」。\n"
       "3. 過度配適（overfitting）。模型開始把雜訊當成訊息記下來。\n"
       "4. 不能採用。要回頭檢查是不是有系統性偏差（例如兩類樣品在不同天測、用不同批容器），這種假相關在真實實驗室非常常見。\n"
       "5. 模型會硬把它歸到四類油之一，而且可能給出很高的信心值。要防範就要加上適用範圍（applicability domain）檢查：光譜殘差過大、或馬氏距離超出訓練集範圍時，回報「超出模型適用範圍」而不是給答案。\n\n</details>"),
    md("---\n## 🎓 課程結束\n\n"
       "你已經完成了一個完整的食品拉曼分析流程：\n\n"
       "```\n讀資料 → 前處理 → 峰位判讀 → 定性篩檢 → 定量校正 → 檢查模型合理性\n```\n\n"
       "**請到課程網站完成線上測驗，確認自己真的掌握了。**"),
])

for _n in [nb1, nb2, nb3, nb4, nb5]:
    _n["cells"].append(md("\n---\n### 📚 這一本用到的資料與文獻\n\n**資料**：`data/` 內的光譜為**依文獻峰位建立的模擬資料**（`make_data.py`，亂數種子 20260801），刻意加入螢光背景、宇宙射線與雜訊。可用於教學演練，**不可引用為實驗證據**。\n\n**主要文獻**\n\n- Georgiev, D. et al. *RamanSPy: An Open-Source Python Package for Integrative Raman Spectroscopy Data Analysis*. **Anal. Chem.** 2024, 96(21), 8492–8500. doi:10.1021/acs.analchem.4c00383\n- Gill, D.; Kilponen, R. G.; Rimai, L. *Resonance Raman Scattering … in Intact Plant Tissues*. **Nature** 1970, 227, 743–744. doi:10.1038/227743a0\n- Lu, L. et al. *Resonance Raman scattering of β-carotene … second singlet state*. **J. Photochem. Photobiol. B** 2018, 179, 18–22. doi:10.1016/j.jphotobiol.2017.12.022\n- Withnall, R. et al. *Raman spectra of carotenoids in natural products*. **Spectrochim. Acta A** 2003, 59(10), 2207–2212. doi:10.1016/S1386-1425(03)00064-7\n- de Oliveira, V. E. et al. *Carotenes and carotenoids in natural biological samples*. **J. Raman Spectrosc.** 2010, 41(6), 642–650. doi:10.1002/jrs.2493\n- Portarena, S. et al. *Cultivar discrimination, fatty acid profile and carotenoid characterization of monovarietal olive oils by Raman spectroscopy at a single glance*. **Food Control** 2019, 96, 137–145. doi:10.1016/j.foodcont.2018.09.011\n- Chen, Y. et al. *Quantitative analysis of β-carotene and unsaturated fatty acids in blended olive oil via Raman spectroscopy combined with model prediction*. **Food Chemistry** 2025, 470, 142621. doi:10.1016/j.foodchem.2024.142621\n- Schmidt, W. et al. *Continuous Temperature-Dependent Raman Spectroscopy of Melamine and Structural Analog Detection in Milk Powder*. **Appl. Spectrosc.** 2015, 69(3), 398–406. doi:10.1366/14-07600\n- Zhang, X. et al. *Detection of melamine in liquid milk using SERS*. **J. Raman Spectrosc.** 2010, 41(12), 1655–1660. doi:10.1002/jrs.2629\n- Kim, A. et al. *Melamine Sensing in Milk Products by Using SERS*. **Anal. Chem.** 2012, 84(21), 9303–9309. doi:10.1021/ac302025q\n- FAO/WHO Codex Alimentarius. *General Standard for Contaminants and Toxins in Food and Feed*, **CXS 193-1995**.\n\n完整清單見課程網站的「數據來源」與「參考文獻」兩節。"))

for name, n in [("NB1_intro_spectrum.ipynb", nb1), ("NB2_preprocessing.ipynb", nb2),
                ("NB3_peak_assignment.ipynb", nb3), ("NB4_melamine_screening.ipynb", nb4),
                ("NB5_oil_authentication.ipynb", nb5)]:
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        nbf.write(n, f)
    print("已建立", name)
