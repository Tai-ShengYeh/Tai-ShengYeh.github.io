# 食品分析｜拉曼光譜與 RamanSPy 入門

給**零程式基礎**的食品營養系大學生設計的三週教學單元。
以 [RamanSPy](https://github.com/barahona-research-group/RamanSPy)（BSD-3-Clause）為工具，
從「畫出第一條光譜」走到「奶粉三聚氰胺篩檢」與「橄欖油摻混定量」。

---

## 檔案結構

三個頁面都是**單檔自帶樣式**：CSS、互動程式與圖檔全部內嵌，
單獨開一個 `.html` 也能正常顯示（與主站 `raman-food-analysis/teaching.html` 的作法一致）。

```
index.html            課程入口（課程地圖、三個學習層次）        自帶樣式
teaching.html         線上教材主體，內含 5 個互動實驗台          自帶樣式＋內嵌圖
quiz.html             線上測驗：30 題，四關卡，自動計分          自帶樣式

_source/              編輯用的原始檔（改這裡，再跑 build.py）
  course.css            共用樣式（色票對齊主站 index.html）
  data.js               互動元件用的光譜資料
  interactive.js        互動元件邏輯（Chart.js）
  index.html / teaching.html / quiz.html   仍以 <link> 引用外部檔的版本
build.py              把 _source/ 組成上面三個單檔頁面

notebooks/
  NB1_intro_spectrum.ipynb        第一條光譜
  NB2_preprocessing.ipynb         前處理
  NB3_peak_assignment.ipynb       峰位判讀
  NB4_melamine_screening.ipynb    奶粉摻偽篩檢
  NB5_oil_authentication.ipynb    油品鑑別與定量
  （部署時會保留原有的 ramanspy_food_beginner.ipynb 暖身本）

data/                 六組光譜資料集 ＋ 教師解答（不會被發布）
img/                  教材用圖檔（9 張，配色與網頁一致）

deploy.sh             一鍵部署／合併更新到 GitHub Pages
portal-card.html      取代主站首頁那張舊卡片的 HTML
make_data.py          重新產生資料集
make_figures.py       重新產生圖檔
make_notebooks.py     重新產生 Notebook
```

### 要修改頁面時

改 `_source/` 裡的檔案，然後：

```bash
python build.py     # 重新組出三個單檔頁面
```

外部只剩兩個 CDN：Chart.js（互動圖表）與 highlight.js（程式碼上色）。
兩者失效時頁面仍可讀，只是圖表不動、程式碼不上色。

### 視覺風格

色票與元件直接對齊 `tai-shengyeh.github.io` 首頁：
`--paper2 #F5F2E9`、`--line #E4DECC`、`--ink-soft #52493b`、`--teal #0E7C7B`、
`--coral #E36414`、`--gold #C8941F`、`--cover #119C9A`；
深色 sticky nav、湖綠封面配金色數字、米色圓角卡片配膠囊標籤、
`.links / .go / .repo` 連結列、深色 ink 頁尾。字型為 Noto Sans TC。

## 五個互動實驗台

| 位置 | 做什麼 | 教到什麼 |
|---|---|---|
| `teaching.html#mix` | 拉六種成分的比例，程式即時標出峰位歸屬 | 混合物光譜是疊加；共振增強讓「強度 ≠ 含量」 |
| `teaching.html#prep` | 調螢光、雜訊、平滑視窗、基線、歸一化 | 平滑視窗從 5 拉到 71 點，676 峰高 0.161→0.063、半高寬 24→116 cm⁻¹ |
| `teaching.html#peaks` | 六個真實未知樣品，選答後說明判讀依據 | 用「哪個峰在／哪個峰不在」推理 |
| `teaching.html#melamine` | 拉三聚氰胺濃度，看何時才判定「檢出」 | 判定閾值、LOD、「未檢出 ≠ 沒有」 |
| `teaching.html#quant` | 拉 PLS 潛在變數，看 RMSECV 曲線與預測散布 | 配適不足 vs 過度配適的分界 |

互動元件的計算（Savitzky–Golay、ModPoly 基線校正）是在瀏覽器裡即時算的，
用的是與 Notebook 相同的演算法與係數；三聚氰胺劑量曲線與 PLS 結果則直接來自
真實跑出來的 60／50 個樣品，所以網頁上的數字與 Notebook 一致。

## 部署（GitHub Pages）

repo 名稱、分支、子資料夾都由 `deploy.sh` 自動處理，你只要給本機 clone 的路徑：

```bash
# 放到新資料夾（與現有 ramanspy-food-analysis/ 並存）
./deploy.sh ~/sites/Tai-ShengYeh.github.io ramanspy-food-analysis-v2

# 或取代現有課程（會先擋下來，確認要覆蓋才加 --force）
./deploy.sh ~/sites/Tai-ShengYeh.github.io ramanspy-food-analysis --force

# 確認後推上去
cd ~/sites/Tai-ShengYeh.github.io && git push
```

腳本會：

1. 從 `git remote` 自動讀出 `帳號/repo` 與目前分支
2. 把 `Tai-ShengYeh/Tai-ShengYeh.github.io` / `main` / `ramanspy-food-analysis` 填成正確值 —— Colab 連結與資料下載網址靠這一步才會通
3. **目標資料夾已有內容時預設中止**，避免誤刪既有教材；要覆蓋必須明確加 `--force`
4. 一律排除 `unknown_answers_TEACHER_ONLY.txt`
5. `git add` + `git commit`，把 `git push` 指令印出來讓你確認

**連到主站首頁**：`portal-card.html` 的卡片沿用你首頁既有的 `.card / .tag / .links / .go / .repo` 樣式，
直接貼進卡片區塊即可；記得把裡面的 `ramanspy-food-analysis` 換成實際資料夾名稱。

三個網頁的導覽列都已加上「↖ 課程總站」連回 `https://tai-shengyeh.github.io/`。

## 學生怎麼用

部署完成後，學生完全不用下載任何東西：

1. 打開課程網址 → 在單元卡右下角點「**在 Colab 開啟 ↗**」
2. Colab 問「要執行外部 Notebook 嗎」→ 按「仍要執行」
3. 從第一格開始一格一格按 ▶（或 `Shift + Enter`）
4. 資料會自動從 GitHub 載入，不需上傳 CSV
5. 五本做完後回課程網站完成 `quiz.html` 測驗，截圖繳交

## 課程設計說明

**三週進度**

| 週次 | 課堂 | 課後 |
|---|---|---|
| 1 | 拉曼原理講述 + NB1、NB2 帶做 | 完成 NB2「換你做」，交截圖 |
| 2 | 特徵峰對照表 + NB3 + 未知樣品分組討論 | 完成 NB3 自我檢核 |
| 3 | NB4、NB5 帶做；以 LOD 與法規限量差距做結論討論 | 線上測驗 + 未知樣品判讀報告 |

**評量比重建議**

| 項目 | 比重 | 評什麼 |
|---|---|---|
| Notebook 執行截圖 | 30% | 是否確實跑完、是否有動手改參數 |
| 線上測驗 | 30% | 觀念與判讀能力，70 分通過 |
| 未知樣品判讀報告 | 40% | 推理過程 ＞ 答對與否；是否引用峰位證據；是否談到方法限制 |

**這套教材真正想教會的一件事**：不是 Python，是「知道自己的方法測不到什麼」。
NB4 算出 LOD ≈ 0.5%，而 Codex 對三聚氰胺的限量是 2.5 mg/kg —— 差了兩千倍以上。
學生若能自己講出「未檢出不等於沒有，要先問方法的偵測極限」，這門課就成功了。

---

## 關於資料

`data/` 裡是**依文獻峰位建立的模擬光譜**，刻意加入螢光背景、宇宙射線尖峰與雜訊，
讓學生在教室裡就能遇到真實儀器會出的狀況，同時濃度與答案完全可控、方便驗算。

用標準流程（Cropper → WhitakerHayes → SavGol → IModPoly → MinMax）跑出來的結果：

| 任務 | 結果 |
|---|---|
| 三聚氰胺篩檢（676 cm⁻¹，空白 + 3SD） | LOD ≈ 0.5%，0.45% 以下漏檢 |
| 四種食用油分類（PCA-LDA，5 折 CV） | 正確率 ≈ 96.7% |
| 橄欖油摻混定量（PLS，5 折 CV） | LV = 4，RMSECV = 3.26%，R² = 0.952 |

這些數字與文獻上一般拉曼（非 SERS）的表現落在同一個數量級。

要更換濃度範圍、基質或摻偽物，改 `make_data.py` 的峰位表後重跑
`make_data.py` → `make_figures.py` 即可。

---

## 字型

`course.css` 依照參考頁的寫法宣告了 GenSeki（源石黑體）的 `@font-face`，
路徑指向 `assets/fonts/`。這三個 otf 檔不在本套件裡，缺檔時會自動退回 Noto Sans TC，
外觀仍然一致。若要與 `raman-food-analysis/teaching.html` 完全相同，把該課程的
`assets/fonts/GenSekiGothic2TW-{H,B,M}.otf` 複製到本資料夾的 `assets/fonts/` 即可。

## 數據來源與文獻

`data/` 內的六組光譜是**依文獻峰位建立的模擬資料，不是實測光譜**（`make_data.py`，亂數種子 `20260801`，可完整重現）。
生成方式與峰位依據見 `teaching.html#data`，完整文獻見 `teaching.html#refs`，五本 Notebook 結尾也各附一份清單。

全部書目已用 **scite** 逐筆查核 DOI／期刊／卷期／頁碼／作者，並以 **Consensus** 補齊共振拉曼增強的原始文獻。
原先引用的專書章節與雜誌專欄（查不到同儕審查來源）已全數改引可查核的期刊論文。

| 課程中的說法 | 依據 |
|---|---|
| 共振拉曼增強現象（類胡蘿蔔素） | Gill, Kilponen & Rimai, *Nature* **1970**, 227, 743–744. doi:10.1038/227743a0 |
| 為何用 532 nm：488/514 增強最強但 532 為最佳折衷 | Lu et al., *J. Photochem. Photobiol. B* **2018**, 179, 18–22. doi:10.1016/j.jphotobiol.2017.12.022 |
| ν₁ 隨共軛鏈長位移 | Withnall et al., *Spectrochim. Acta A* **2003**, 59(10), 2207–2212. doi:10.1016/S1386-1425(03)00064-7 |
| β-胡蘿蔔素 1515/1156/1008；基質會使 C=C 帶位移 | de Oliveira et al., *J. Raman Spectrosc.* **2010**, 41(6), 642–650. doi:10.1002/jrs.2493 |
| 增強因子的定義與量測 | Le Ru & Auguié, *ACS Nano* **2024**, 18(14), 9773–9783. doi:10.1021/acsnano.4c01474 |
| 橄欖油特徵帶 965–1748 cm⁻¹ | Portarena et al., *Food Control* **2019**, 96, 137–145. doi:10.1016/j.foodcont.2018.09.011 |
| 以 1156/1265/1526/1658 定量橄欖油摻混 | Chen et al., *Food Chemistry* **2025**, 470, 142621. doi:10.1016/j.foodchem.2024.142621 |
| 一般拉曼可在奶粉中辨識 1% 三聚氰胺 | Schmidt et al., *Appl. Spectrosc.* **2015**, 69(3), 398–406. doi:10.1366/14-07600 |
| 銀膠 10⁵ 倍增強；牛奶 LOQ 0.5 µg/mL | Zhang et al., *J. Raman Spectrosc.* **2010**, 41(12), 1655–1660. doi:10.1002/jrs.2629 |
| 嬰兒配方 SERS LOD 100 ppb，低於 FDA 1 ppm | Kim et al., *Anal. Chem.* **2012**, 84(21), 9303–9309. doi:10.1021/ac302025q |
| 診斷峰 674 cm⁻¹（開放取用） | Wang et al., *Food Sci. Hum. Wellness* **2024**, 13(5), 2595–2600. doi:10.26599/fshw.2022.9250208 |
| ring breathing II ＝三嗪環面內變形（開放取用） | Cheng et al., *PLoS ONE* **2014**, 9(9), e107770. doi:10.1371/journal.pone.0107770 |
| SERS 下峰位位移的成因（吸附傾角） | Chen et al., *Appl. Spectrosc.* **2013**, 67(5), 491–497. doi:10.1366/12-06838 |
| Codex 限量：粉狀嬰兒配方 1、液態 0.15、其他 2.5 mg/kg | FAO/WHO Codex **CXS 193-1995** |
| RamanSPy | Georgiev et al., *Anal. Chem.* **2024**, 96(21), 8492–8500. doi:10.1021/acs.analchem.4c00383 |

**教學上務必說清楚**：模擬資料的 LOD 與 RMSECV 之所以與文獻同一量級，是因為生成時就把雜訊與變異調到那個範圍。
它證明的是「這條流程會給出合理的數字」，不是「拉曼真的能做到這個數字」。
學生寫報告引用峰位時要引原始文獻，不要引課程網頁。

## 已知環境問題

| 症狀 | 原因與處理 |
|---|---|
| `AttributeError: numpy has no attribute 'trapz'` | `normalise.AUC()` 在 NumPy ≥ 2.0 失效。改用 `MinMax()` 或 `Vector()` |
| `ModuleNotFoundError: ramanspy` | Colab 重新連線後套件消失，回頭跑第一格 |
| 圖上中文變方框 | Colab 缺中文字型，跑第一格的字型設定 |
| `ValueError: window_length must be odd` | SavGol 視窗必須是奇數 |

---

## 引用

Georgiev, D.; Pedersen, S. V.; Xie, R.; Fernández-Galiana, Á.; Stevens, M. M.; Barahona, M.
*RamanSPy: An open-source Python package for integrative Raman spectroscopy data analysis*.
**Anal. Chem.** 2024, 96(21), 8492–8500. DOI: 10.1021/acs.analchem.4c00383
