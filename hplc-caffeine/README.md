# HPLC 咖啡因定量 · 從層析圖到濃度

用一批真實的 Shimadzu LabSolutions 層析資料（6 個標準品 + 4 個未知樣品），
完整走過 HPLC 外標法定量：**峰面積 → 檢量線 → 樣品濃度**。

| 頁面 | 對象 | 內容 |
|---|---|---|
| [入門版](https://tai-shengyeh.github.io/hplc-caffeine/) | 第一次接觸 HPLC 定量 | 五步驟、零背景知識，含計算練習與小測驗 |
| [進階版](https://tai-shengyeh.github.io/hplc-caffeine/advanced.html) | 想知道細節與陷阱 | 九步驟，含基線校正、峰對齊、殘差診斷、14 篇參考文獻 |

兩頁都是單一 HTML 檔、無外部相依，所有圖形由內嵌的原始 721 點資料即時繪製。

---

## 資料

| 檔案 | 用途 | 標稱濃度 (ppm) |
|---|---|---|
| `std-0.txt` … `std-200.txt` | 標準品 | 0, 25, 50, 100, 150, 200 |
| `sample-1.txt` … `sample-4.txt` | 未知樣品 | — |

Shimadzu LabSolutions ASCII 匯出檔（Big5 編碼）。條件：Detector A-Ch1、280 nm、
注射量 10 µL、Sample Amount = 1、Dilution Factor = 1、跑程 6 min、取樣 721 點（每 0.5 秒）。
採集於 2016/10/14 與 2016/10/17 兩批次。

## 結果

檢量線（n = 6，含 0 ppm 空白）：

```
Area = 48,393.42 × C − 111,613.06        R² = 0.999435
C (ppm) = (Area + 111,613.06) / 48,393.42
```

LOD = 6.76 ppm、LOQ = 20.49 ppm。各標準品回算濃度誤差 −1.7% ~ +3.1%。

| 樣品 | 滯留時間 (min) | 峰面積 | 咖啡因濃度 (ppm) | 95% CI |
|---|---|---|---|---|
| sample-1 | 4.446 | 4,378,116 | **92.78** | 86.63 – 98.92 |
| sample-2 | 4.428 | 3,952,115 | **83.97** | 77.83 – 90.12 |
| sample-3 | 4.594 | 4,085,132 | **86.72** | 80.58 – 92.87 |
| sample-4 | 4.578 | 4,114,384 | **87.33** | 81.18 – 93.47 |

濃度單位同標準品配製單位（ppm = µg/mL）。Dilution Factor = 1；若前處理有稀釋須再乘稀釋倍數。

## 這批資料的三個教學重點

1. **儀器的自動判峰會錯。** std-25 指到 4.177 min 的小峰（實際咖啡因在 4.653 min，面積差 6 倍）；
   sample-3 指到 3.242 min 面積僅 21,355 的雜訊峰。照用儀器的 `Conc.` 欄位，
   sample-3、sample-4 會得到**負濃度**。本專案改以滯留時間視窗內最大峰判定。
2. **基線畫在哪裡直接改變答案。** airPLS 的平滑度 λ 太小會讓基線爬進峰底下（峰高只剩 98.8%、
   檢量線斜率低 2.7%）；太大則跟不上真實漂移。進階版可拖 λ 滑桿即時觀察。
3. **滯留時間會漂移。** 樣品峰比標準品早 0.06–0.23 min。不校正就用固定積分視窗，
   濃度會隨視窗寬度大幅擺動（全距平均 27.3 ppm）；用 alignDE 對齊後降到 4.7 ppm。

## 自己重跑

```bash
# 主定量（R 與 Python 兩套，結果一致）
python caffeine_calibration.py
Rscript caffeine_calibration.R

# 峰對齊（需 R 套件 alignDE，相依 DEoptim、Matrix）
Rscript align_chromatograms.R

# 基線校正參數測試（需 R 套件 airPLS）
Rscript baseline_airpls.R

# 重新產生兩個教學頁
python build_teaching_html.py
```

Python 需 `numpy / pandas / scipy / matplotlib`；`caffeine_calibration.R` 只用 base R。

| 檔案 | 角色 |
|---|---|
| `hplc_io.R` | Shimadzu 匯出檔解析器（R 各程式共用） |
| `caffeine_calibration.py` / `.R` | 主定量流程：判峰、積分、檢量線、樣品濃度 |
| `align_chromatograms.R` | alignDE 峰對齊 + 對齊後定量 |
| `baseline_airpls.R` | airPLS 基線校正參數掃描與可行性測試 |
| `build_teaching_html.py` | 產生兩個教學頁（`--site DIR` 可產生網站版） |

## 主要參考文獻

書目經 Crossref 以 DOI 核對。完整清單見進階版頁面。

- Zhang, Z.-M., Chen, S., & Liang, Y.-Z. (2011). Peak alignment using wavelet pattern matching and differential evolution. *Talanta*, 83(4), 1108–1117. https://doi.org/10.1016/j.talanta.2010.08.008
- Zhang, Z.-M., Chen, S., & Liang, Y.-Z. (2010). Baseline correction using adaptive iteratively reweighted penalized least squares. *The Analyst*, 135(5), 1138–1146. https://doi.org/10.1039/b922045c
- Eilers, P. H. C. (2003). A perfect smoother. *Analytical Chemistry*, 75(14), 3631–3636. https://doi.org/10.1021/ac034173t
- Danzer, K., & Currie, L. A. (1998). Guidelines for calibration in analytical chemistry. Part I (IUPAC Recommendations 1998). *Pure and Applied Chemistry*, 70(4), 993–1014. https://doi.org/10.1351/pac199870040993
- DiNunzio, J. E. (1985). Determination of caffeine in beverages by high performance liquid chromatography. *Journal of Chemical Education*, 62(5), 446. https://doi.org/10.1021/ed062p446
