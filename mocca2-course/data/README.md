# 魚露防腐劑 PDA 資料集（MOCCA2 可直接讀取）

本實驗室自行量測的 **HPLC-PDA** 原始資料，已轉換成 `mocca2.load_data2d()` 能直接讀取的格式。
用途：練習 MOCCA2 的基線校正、找峰、峰純度判斷與去卷積。

---

## 檔案

| 檔案 | 內容 | 時間 × 波長 |
|---|---|---|
| `blank.txt` | 空白（std 0），供扣背景用 | 2346 × 27 |
| `std_0.25ppm.txt` | 己二烯酸 0.25 ppm 標準品 | 2345 × 27 |
| `sample_positive.txt` | 真實魚露樣品，**檢出**己二烯酸 | 1408 × 27 |
| `sample_negative.txt` | 真實魚露樣品，**未檢出** | 1408 × 27 |
| `quickstart.py` | 可直接執行的範例 | — |
| `convert_labsolutions_pda.py` | 原始檔轉換腳本（見下方說明） | — |

**量測條件**：Shimadzu HPLC + PDA 偵測器，波長 228.9–260.5 nm（27 點），
取樣間隔 640 ms，標準品 25 分鐘 / 樣品 15 分鐘。訊號單位 mAU。

---

## 快速開始

```bash
pip install mocca2
python quickstart.py
```

```python
from mocca2 import Chromatogram

# 空白與樣品的時間點數略有差異（2346 vs 2345），需開 interpolate_blank
ch = Chromatogram("std_0.25ppm.txt", "blank.txt", interpolate_blank=True)
ch.correct_baseline()
ch.find_peaks(min_height=0.05)

trace = ch.contract()
for p in sorted(ch.peaks, key=lambda x: x.maximum):
    print(f"{ch.time[p.maximum]:6.2f} min  {trace[p.maximum]:7.3f} mAU")
```

預期輸出（已實測）：己二烯酸出現在 **9.93 min**，與 LCsolution 峰表報告的 9.930 min 一致；
陰性樣品在 4 分鐘之後找不到任何峰，也與峰表一致。

---

## 這批資料適合練什麼

1. **扣空白與基線校正** — 溶劑鋒在 2–3 分鐘造成大幅擾動（含負峰），是基線演算法的好考驗。
2. **峰純度（peak purity）** — 有 27 個波長通道，可檢查 9.93 min 的峰底下是否只有一個成分。
3. **陽性／陰性對照** — 兩個真實樣品，一個檢出一個未檢出，可練習判斷「找不到峰」是真的沒有還是門檻設太高。
4. **與峰表對照** — 原始 LCsolution 已有廠商軟體的積分結果，可用來驗證你的自動化流程。

> **注意**：2–3 分鐘的溶劑鋒區域內，積分軟體會切出數個「峰」並報告彼此的解析度
> （Rs 約 1.0–1.2）。那些是**注射擾動造成的積分假影，不是層析分離**，
> 不要把它們當成真實的分離不良案例。

---

## 資料怎麼來的

原始檔是 Shimadzu LCsolution 的 `.txt` 匯出檔（Big5/cp950 編碼），
MOCCA2 內建的 `labsolutions` 解析器**無法直接讀取**，原因有二：

1. 解析器預期**逗號分隔**，原始檔是 **tab 分隔**；
2. 解析器抓檔案中第一個出現的 `R.Time (min)`，但原始檔在 `[PDA 3D]` 之前
   還有 `[LC Status Trace]` 與 `[PDA Multi Chromatogram]` 兩個區段，會抓錯位置。

`convert_labsolutions_pda.py` 只做兩件事：**擷取 `[PDA 3D]` 區段、改成逗號分隔**。
**數值一個都沒有改動**，波長與時間軸也原樣保留。

若要轉換你自己的 LCsolution PDA 檔：

```bash
python convert_labsolutions_pda.py 輸出資料夾
```

（腳本開頭的 `SRC` 與 `PICK` 改成你的路徑與檔名即可。）

---

## 授權

本資料集為本實驗室自行量測，採 **CC BY-NC 4.0**；
轉換腳本與 `quickstart.py` 採 **MIT**。
使用時請註明來源：<https://tai-shengyeh.github.io/mocca2-course/>
