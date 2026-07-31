# 課程範例資料

## 檔案

| 檔案 | 內容 |
|---|---|
| `demo_chromatogram.csv` | 教學用層析圖，2001 點，`time` (min) + `signal` (mAU) |
| `demo_ground_truth.csv` | 這張圖的**正確答案**：6 個峰的真實參數 |

## 這是模擬資料，不是真實量測

`demo_chromatogram.csv` 是**電腦生成**的，不是真的跑出來的樣品。這樣做是刻意的：
因為知道正確答案，學生才能檢查 hplc-py 到底有沒有算對。真實資料沒有這個好處。

化合物名稱（蔗糖、葡萄糖、果糖、檸檬酸、苯甲酸、咖啡因）是為了讓食品科學情境
好懂而標的，**不代表這些化合物在真實管柱上會是這個出峰順序**。

峰形採用 Chure & Cremer (2024) JOSS 論文 Eq. 1 的 skew-normal 參數化，
所以 `area` 欄位就是該峰的真實積分面積（mAU·min）。

生成設定：基線漂移 `1.5 + 0.35t + 0.012t²` mAU、高斯雜訊 σ = 0.8 mAU、
亂數種子 20260730（固定，可重現）。

## 正確答案

| 化合物 | retention_time (min) | scale | skew | area (mAU·min) |
|---|---|---|---|---|
| sucrose | 4.20 | 0.12 | 1.5 | 95 |
| glucose | 5.60 | 0.14 | 2.0 | 150 |
| fructose | 5.95 | 0.15 | 2.0 | 58 |
| citric acid | 9.10 | 0.18 | 3.0 | 180 |
| benzoic acid | 12.80 | 0.20 | 1.0 | 72 |
| caffeine | 15.40 | 0.22 | 0.5 | 120 |

glucose (5.60) 與 fructose (5.95) 只差 0.35 min，會形成明顯肩峰——
這組是給「重疊峰與 known_peaks」那一章用的。

## 已驗證的執行結果（hplc-py 0.2.8）

### 必須設定 `approx_peak_width`

用**預設參數**跑這份資料，6 個峰都會被找到、參數也很準，但 `assess_fit()`
會判定 `invalid`：

| `approx_peak_width` | peak windows | reconstruction score | status |
|---|---|---|---|
| 0.2 | 6 | 0.998 – 1.034 | 部分 invalid |
| **0.5** | **5** | **0.996 – 1.006** | **全部 valid** |
| 1.0 | 4 | 0.966 – 0.983 | 全部 invalid |
| 5.0（預設） | 1 | 0.940 | invalid |

原因：這份資料的峰寬約 0.5 min，而預設值假設 5 min。SNIP 基線估計把
「比 5 min 窄的東西」都當成訊號，於是基線被低估、峰窗被合併成一個。

**這正是「參數要由峰寬決定，不能沿用預設」的實例。**

### 回收準確度（`approx_peak_width=0.5`）

| 化合物 | 真實 area | hplc-py `amplitude` | 誤差 |
|---|---|---|---|
| sucrose | 95 | 95.58 | +0.6 % |
| glucose | 150 | 149.07 | −0.6 % |
| fructose | 58 | 56.86 | −2.0 % |
| citric acid | 180 | 179.72 | −0.2 % |
| benzoic acid | 72 | 69.83 | −3.0 % |
| caffeine | 120 | 112.21 | −6.5 % |

重疊的 fructose 與最不對稱的 caffeine 誤差最大——**重疊與拖尾會讓定量變差**，
這個結論可以直接用資料證明給學生看。

### `area` 與 `amplitude` 的單位陷阱（重要）

實測結果：

```
peaks["area"] * 0.01 == peaks["amplitude"]     # 0.01 min 是取樣間隔
```

也就是說 `area` 是「訊號 × 取樣點數」，**不是**「訊號 × 分鐘」。
`amplitude` 才是以時間為單位的積分面積。

同一台儀器、同一個取樣率下，兩者只差一個常數，檢量線會自動吸收掉；
但**跨儀器或改變取樣率時，`area` 不可直接比較**。

## 重新生成

```bash
python make_demo.py     # 需要 numpy, pandas, scipy
```
