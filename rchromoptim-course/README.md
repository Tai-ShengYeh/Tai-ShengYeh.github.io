# HPLC 分離最佳化教學（RChromOptim）

食品營養系取向的 HPLC 分離最佳化互動教材，從「讀懂一張層析圖」一路到「用 R／Python 跑完整套最佳化流程」。

**線上閱讀：<https://tai-shengyeh.github.io/rchromoptim-course/>**

22 節、8 個可拖曳模擬器、10 道測驗，全部使用論文的真實數據即時重算。

---

## 檔案

| 檔案 | 說明 |
|---|---|
| `index.html` | 教材本體。單一自包含檔案，無外部相依，可離線雙擊開啟 |
| `rchromoptim_modern.R` | 現代 R 重寫版（R 4.6.1／tidyverse 2.0／ggplot2 4.0） |
| `rchromoptim_modern.py` | Python 版（3.12／numpy／pandas／scipy／matplotlib） |
| `rchromoptim_tutorial.qmd` | Quarto 互動筆記本（R），含留白練習 |
| `rchromoptim_tutorial.ipynb` | Jupyter 互動筆記本（Python），含留白練習 |
| `rchromoptim_modern_demo*.png` | 兩份腳本實際跑出來的輸出圖 |

### 怎麼跑

```bash
# R
install.packages(c("tidyverse", "patchwork"))
Rscript rchromoptim_modern.R

# Python
pip install numpy pandas scipy matplotlib
python rchromoptim_modern.py
```

範例資料已內嵌在腳本裡，**不需要另外準備檔案**。要換成自己的資料時，把 tab 分隔的
`.txt` 路徑傳給 `read_retention("你的檔案.txt")` 即可。

---

## 授權

本目錄採**雙授權**：

| 內容 | 授權 |
|---|---|
| **程式碼**（`.R`、`.py`、筆記本中的程式區塊） | [MIT](LICENSE) |
| **教材內容**（`index.html`、筆記本敘述文字、輸出圖） | [CC BY-NC 4.0](LICENSE-CONTENT.md) |

程式碼用 MIT 而非 CC，是因為 Creative Commons 官方建議不要用 CC 授權軟體。

---

## 引用與第三方素材

本教材重新實作的方法出自：

> Zisi, Ch., Pappa-Louisi, A., & Nikitas, P. (2020). Separation optimization in
> HPLC analysis implemented in R programming language. *Journal of Chromatography A*,
> 1617, 460823. <https://doi.org/10.1016/j.chroma.2019.460823>

**不論依 MIT 或 CC BY-NC 重用，都請引用上述原始論文**——滯留模型與最佳化方法是原作者的
科學貢獻，本專案的貢獻只是重新實作與教學設計。

程式碼是**獨立重新實作**，並未沿用原套件的任何函式；原論文全文與其補充材料
（`Data.xlsx`、`RChromOptim.RData` 等）**未包含在本專案中**，請自行透過期刊合法取得。
腳本中僅內嵌一份標註出處的少量事實性數據摘錄（36 個滯留時間數值），
用途是讓學習者能親手驗證論文的已發表結果。詳見 [`LICENSE-CONTENT.md`](LICENSE-CONTENT.md)。
