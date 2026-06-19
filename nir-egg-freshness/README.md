# 🥚 NIR-PLS 雞蛋新鮮度預測｜教學包

用近紅外光譜 (740–1070 nm) + PLS 迴歸預測雞蛋的儲存天數。
對應論文 **Coronel-Reyes et al. (2018)**, *Computers and Electronics in Agriculture* 145, 1–10；
資料來自 [Mendeley 6hn67h2trb](https://data.mendeley.com/datasets/6hn67h2trb/2)。

## 檔案說明

| 檔案 | 用途 | 給誰 |
|------|------|------|
| **`pls_egg_freshness_teaching.html`** | 主教材（可單檔分享，圖已內嵌，繁體中文） | 學生閱讀／投影 |
| **`PLS_egg_freshness_colab.ipynb`** | Python 教學筆記本，可在 Google Colab 一鍵執行 | 學生動手（程式） |
| **`egg_storage_orange.tab`** | Orange 專用資料（欄位角色已標好、波長欄位為純數字） | Orange 載入 |
| **`egg_pls_orange.ows`** | Orange 工作流程（七個元件已接好） | Orange 開啟 |
| `dataset_egg_storage.csv` | 原始資料（660×333） | Colab/Python 上傳 |
| `run_analysis.py` | 產生教材中所有圖的完整腳本 | 老師（可重跑/修改） |
| `figures/` | 圖 1–7 的 PNG | 教材用圖 |
| `build_*.py`, `template.html` | 重建教材的輔助腳本 | 老師（進階） |

## 建議使用順序

1. 開 **`pls_egg_freshness_teaching.html`**（瀏覽器雙擊即可）通讀觀念。
2. 用 **Orange** 開 `egg_pls_orange.ows`，拖拉跑一遍，建立直覺。
   - 需先裝 Spectroscopy 外掛：Orange 選單 `Options → Add-ons… → Spectroscopy`。
3. 用 **Google Colab** 開 `PLS_egg_freshness_colab.ipynb`，逐格執行，理解程式細節。

## 主要結果

PLS（Savitzky–Golay 二階微分 + 12 個潛在變數）：

- 隨機 10-fold 交叉驗證：**R² ≈ 0.82，RMSECV ≈ 2.69 天**
- 依蛋分組 GroupKFold（誠實泛化）：R² ≈ 0.81，RMSECV ≈ 2.75 天
- 關鍵波長：~788、821、1002–1007 nm（對應 C–H 與 N–H/O–H）

## 重新產生圖檔（選用）

```bash
cd D:\claude\egg_data
pip install numpy pandas scipy scikit-learn matplotlib
python pls_teaching/run_analysis.py     # 重畫 figures/
python pls_teaching/build_html.py        # 重建自含圖的 HTML
```

> 註：`run_analysis.py` 用微軟正黑體繪製中文；Colab 筆記本內的圖則用英文座標軸（避免 Colab 無中文字型）。
