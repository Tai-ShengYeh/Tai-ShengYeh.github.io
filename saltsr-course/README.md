# SaltsR 鹽害分析入門

給**沒有程式基礎的大一學生**的 R 資料科學課程，主題是文化資產的鹽害分析。
從 R 的第一行寫起，一路帶到能獨立完成
「離子層析 → 電荷平衡校正 → ECOS/Runsalt 模擬 → 濕度控制建議」的完整分析流程。

**所有 R 程式碼都在學生的瀏覽器裡執行**（透過 [webR](https://docs.r-wasm.org/webr/latest/)，
R 編譯成 WebAssembly），不需要安裝 R、RStudio 或註冊任何帳號。

---

## 內容

| 檔案 | 說明 |
|---|---|
| `index.html` | 課程入口（卡片式導覽） |
| `lesson.html` | 十個單元的完整講義，含 28 個可執行的 R 程式碼區塊 |
| `lab.html` | 三個互動實驗室（純 JavaScript，不需要 webR） |
| `quiz.html` | 37 題四階段測驗，即時回饋與自動計分 |
| `teacher.html` | 教師版：解答、時間分配、常見迷思、評分 rubric、答案代號 |
| `assets/` | CSS、webR 執行器、課堂版 R 函式庫、JS 計算引擎、測驗與實驗室邏輯 |
| `data/` | 教學資料集與 SaltsR 官方範例檔 |
| `scripts/` | 各單元的 `.R` 腳本，可下載到 RStudio 執行 |
| `start-course.bat` / `start-course.command` | 本機預覽：按兩下就啟動（Windows / macOS） |
| `serve.py` / `serve.js` | 本機預覽伺服器本體（Python 版 / Node 版） |
| `deploy.ps1` / `deploy.sh` | 部署到 GitHub Pages（Windows / macOS·Linux） |
| `sw.js` / `assets/offline.js` | Service Worker：讓學生把整套課程存進瀏覽器離線使用 |
| `webr/` | 自備的 R 執行環境（選用，約 46 MB，要離線功能才需要） |

### 單元

| # | 主題 |
|---|---|
| 00 | 鹽為什麼會把牆吃掉（結晶壓、潮解循環、水合膨脹；混合鹽效應） |
| 01 | R 的第一行：變數、函式、錯誤訊息 |
| 02 | 向量、資料框與管線 `\|>` |
| 03 | 從 ppm 到重量百分比（式 1） |
| 04 | 當量濃度 mEq/kg（式 2） |
| 05 | 電荷平衡與 Pathway 1／2（式 3–5）**核心單元** |
| 06 | 石膏扣除與 ECOS 輸入檔（式 6–11） |
| 07 | 讀進 Runsalt 輸出檔（寬格式轉長格式） |
| 08 | 繪圖與判讀（結晶 RH、風險判準、濕度建議） |
| 09 | 批次處理與綜合實作 |

### 互動實驗室

1. **電荷平衡即時模擬器** — 七個離子滑桿，即時顯示 Δe、路徑判定與逐級扣除過程
2. **Runsalt 曲線判讀器** — 拖動濕度游標，看哪些鹽是固體、哪些已溶解
3. **石膏飽和度計算機** — 水樣比對數據可信度的影響

---

## 在自己電腦上先看看（重要）

**不要用「按兩下 `index.html`」的方式開啟課程。**
那樣網址會是 `file://`，瀏覽器會禁止網頁讀取旁邊的教材檔案，
R 環境一定會失敗並顯示「Failed to fetch」。

請改用課程附的小型伺服器：

| 系統 | 做法 |
|---|---|
| Windows | 在課程資料夾裡按兩下 `start-course.bat` |
| macOS | 按兩下 `start-course.command` |
| 任何系統（終端機） | `python serve.py` （沒有 Python 就用 `node serve.js`） |

它會印出 `http://localhost:8000/index.html`，並自動開啟瀏覽器。
按 `Ctrl+C` 結束。若 8000 被占用會自動往後找空的埠。

Windows 若要自己在 cmd 裡跑：

```bat
cd /d D:\claude\saltsr-course
py -3 serve.py
```

> 啟動檔刻意用純英文檔名與 ASCII 內容。`cmd.exe` 是用系統的舊字碼頁（繁體中文 Windows 是 cp950）
> 逐位元組讀取 `.bat`，UTF-8 的中文會被拆碎，連同後面的指令一起變成亂碼。

> 部署到 GitHub Pages 之後就沒有這個問題了，因為那本來就是 `https://`。

### 如果換成「連不到 R 執行環境」

代表網頁本身正常，但抓不到 `webr.r-wasm.org`（校園防火牆或 Proxy 常見）。
可換網路重試、請網管把該網域加白名單，
或把 webR 檔案自架後在頁面上設定 `window.WEBR_BASE_URL` 指過去。

---

## 部署到 GitHub Pages

整個課程是純靜態網站，沒有後端、沒有建置步驟，直接放上去就能跑。

**Windows（PowerShell）**

```powershell
cd D:\claude\saltsr-course
.\deploy.ps1 -Repo D:\github\Tai-ShengYeh.github.io
```

若出現「因為這個系統上已停用指令碼執行」，先跑一次：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**macOS / Linux / Git Bash**

```bash
./deploy.sh ~/Tai-ShengYeh.github.io           # 預設放到 saltsr-course/
./deploy.sh ~/Tai-ShengYeh.github.io my-folder # 指定資料夾名稱
```

兩支腳本功能完全相同（產出經比對為位元組相同），都會：
複製檔案 → 建立 `.nojekyll` → `git commit`，然後**印出** push 指令讓你自己確認。
若目標資料夾已存在會先自動備份到 repo 外面（除非加 `-Force` / `--force`）。

推上去之後網址是 `https://tai-shengyeh.github.io/saltsr-course/`。
最後把 `portal-card.html` 的內容貼進網站根目錄 `index.html` 的卡片區。

### 教師版預設不會上線

`teacher.html` 有全部解答、答案代號與評分 rubric，部署時**預設排除**，
四個頁面裡指向它的連結也會一併移除（入口頁的卡片會換成「請向授課教師索取」），
不會留下 404。

真的要公開解答再加參數：

```powershell
.\deploy.ps1 -Repo D:\github\Tai-ShengYeh.github.io -WithTeacher
```

```bash
./deploy.sh ~/Tai-ShengYeh.github.io --with-teacher
```

反過來也成立：之前用 `--with-teacher` 部署過，下次不加就會把線上的 `teacher.html` 移除。

### 讓學生可以離線上課（PWA）

網路慢的教室，最好的解法是**上課當天完全不用網路**。做法：

1. 把 `webr/` 資料夾放進課程資料夾（`saltsr-course/webr/`）。
   離線包裡的 `webr` 就是這個東西，直接搬過來即可。
2. 部署時加上參數，把它一起上線：

```powershell
.\deploy.ps1 -Repo D:\你的路徑\Tai-ShengYeh.github.io -WithWebR
```

```bash
./deploy.sh ~/Tai-ShengYeh.github.io --with-webr
```

3. 請學生**在家或網路順暢時**開課程首頁，按一次「準備離線使用」，
   等進度條跑完（約 46 MB）。

之後這台電腦即使完全沒有網路，四個頁面與 R 都能正常運作 —— 不用安裝任何東西、
不用隨身碟、不用解壓縮。實測方式是用瀏覽器真正切斷網路連線後重新開啟課程。

技術上是 Service Worker 把課程外殼與 `webr/` 存進 Cache Storage。
兩者用不同的快取名稱：更新講義只會讓外殼失效，學生**不會**因此重抓 46 MB。
部署腳本會自動把 `sw.js` 裡的 `__BUILD__` 換成時間戳記，所以每次上線學生都會拿到新版。

> 沒有 `webr/` 也完全能用，只是學生每次都要連 `webr.r-wasm.org`，且無法離線。

### 部署前後的差異

| 項目 | 本機（`serve.py`） | GitHub Pages |
|---|---|---|
| 需要先開伺服器 | 是 | 否，直接給網址 |
| `teacher.html` | 有 | 預設沒有 |
| `serve.py` 等預覽工具 | 有 | 不會上傳 |
| webR 來源 | 有 `webr/` 就用它，否則 CDN | 同左 |
| 學生可離線使用 | — | 有 `--with-webr` 才可以 |

---

## 技術說明

### webR

* 使用 **PostMessage 通道**，因為 GitHub Pages 無法設定 COOP/COEP 標頭
  （沒有 SharedArrayBuffer）。代價是不支援 `readline()` 等阻塞式輸入 —— 課程沒用到。
* 第一次執行需下載約 20 MB（實測 21.7 MB 未壓縮，經 CDN 壓縮後更少），之後由瀏覽器快取。頁面採**延遲載入**：
  使用者捲到程式碼區塊附近才開始下載。
* 中文標籤在 webR 的 canvas 繪圖裝置上可正常顯示（實測 Chromium）。
* 若要改用其他 CDN 或自架，在載入 `webr-runner.js` 前設定
  `window.WEBR_BASE_URL = '…/'` 即可。

### 計算的正確性

課程網頁上的所有數值都經過對原始 SaltsR 套件的逐項驗證：

| 元件 | 驗證方式 | 結果 |
|---|---|---|
| `assets/saltsr_teaching.R` | 200 組隨機參數逐欄比對 | 0 筆不符，最大相對誤差 6.5 × 10⁻¹⁴ |
| `assets/salt_engine.js` | 68 組案例逐欄比對 | 0 筆不符，最大相對誤差 0 |
| 端到端 | MH-01 產生的 ECOS 輸入檔 vs `SaltsR_upload_Example.txt` | 逐位小數完全相同 |

比對涵蓋：路徑判定、各級扣除值、石膏上限、莫耳分率、重量分率、飽和度、警告訊息。

### 課堂版與原套件的刻意差異

* `tibble` → `data.frame`（避免在瀏覽器裡安裝 tidyverse）
* 新增 `$total_salt_content` 與 `$removed_wt`，取代語意容易誤讀的 `total_ion_content`
  （後者實際上是「被校正掉的量減石膏」，不是總離子含量 —— 講義單元 06 有完整說明）
* `tidy_runsalt()` 為 base R 重寫，未實作原套件的 `RH_eqm` 欄

---

## 資料來源

* `SaltsRExample20C.txt`、`SaltsR_upload_Example.txt`、`ECOS_phases.csv`
  — 取自 SaltsR 套件的 `data-raw/`，未經修改。
* `salt_samples.csv` 的八個樣品 — **為本課程設計的教學資料，非真實測量值**。
  設計原則是涵蓋全部教學情境（Pathway 1 的兩種觸發條件、Pathway 2 的兩種扣除深度、
  石膏受限於 SO₄ 與受限於 Ca、一個觸發飽和度警告的樣品）。
  其中 MH-01 刻意與 SaltsR 官方範例完全相同，使整條分析鏈形成可驗證的閉環。
  **這些數字不可引用為實驗證據。**

## 方法出處

* Godts, S.; Steiger, M.; Orr, S. A.; et al. (2022). Charge balance calculations for mixed
  salt systems applied to a large dataset from the built environment.
  *Scientific Data*, 9(1), 324. [doi:10.1038/s41597-022-01445-9](https://doi.org/10.1038/s41597-022-01445-9)
* Godts, S.; Steiger, M.; Orr, S. A.; et al. (2022). Modeling salt behavior with ECOS/RUNSALT:
  Terminology, methodology, limitations, and solutions.
  *Heritage*, 5(4), 3648–3663. [doi:10.3390/heritage5040190](https://doi.org/10.3390/heritage5040190)
* Godts, S.; Orr, S. A.; Steiger, M. (2023). Salt mixtures in stone weathering.
  *Scientific Reports*, 13(1). [doi:10.1038/s41598-023-40590-y](https://doi.org/10.1038/s41598-023-40590-y)
* Rörig-Dalgaard, I. (2021). Direct measurements of the deliquescence relative humidity in
  salt mixtures including the contribution from metastable phases.
  *ACS Omega*, 6(25), 16297–16306. [doi:10.1021/acsomega.1c00538](https://doi.org/10.1021/acsomega.1c00538)
* Price, C. A. (ed.) (2000). *ECOS*. European Commission Research Report No. 11.
* Bionda, D. (2005). *RUNSALT*. <http://science.sdf-eu.org/runsalt/>

## 授權

SaltsR 套件為 Bhavesh Shah、Sebastiaan Godts、Scott Orr 所著，採 **GPL-3** 授權
（<https://github.com/BhavShah01/SaltsR>）。
`assets/saltsr_teaching.R` 改寫自該套件，保留同一授權。
課程的講義文字、互動工具與測驗由葉泰聖（美和科技大學）編寫，供教學使用。

實際的文化資產診斷請使用官方工具與最新演算法：
[PREDICT 鹽含量計算器](https://predict.kikirpa.be/index.php/tools/moisture-and-salt-sample-data-analysis-tool/)。
