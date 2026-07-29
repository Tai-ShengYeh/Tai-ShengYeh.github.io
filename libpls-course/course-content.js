/* libPLS 互動教材內容
 * 所有範例皆對照 libPLS 1.95.0 的實際 R 介面撰寫。
 * 為了能完全離線使用，這個檔案不載入任何外部函式庫。
 */
(function () {
  "use strict";

  const escapeHTML = (text) => String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const highlightR = (text) => escapeHTML(text)
    .replace(/(#.*)$/gm, '<span class="co">$1</span>')
    .replace(/(&quot;.*?&quot;)/g, '<span class="st">$1</span>')
    .replace(/\b(library|data|str|dim|head|names|plot|matplot|print|predict|set\.seed|which\.min|length|seq_along|order|abs|intersect|data\.frame|cbind|round|with|mean|sd|table|confusionMatrix)\b/g,
      '<span class="fn">$1</span>')
    .replace(/\b(function|if|else|for|in|TRUE|FALSE|NULL)\b/g,
      '<span class="kw">$1</span>')
    .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="nu">$1</span>');

  const code = (text, label = "R") => `
    <div class="code-block">
      <div class="code-header">
        <span>${label}</span>
        <button class="copy-button" type="button" aria-label="複製程式碼">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="8" y="8" width="11" height="11" rx="1"/>
            <path d="M16 8V5H5v11h3"/>
          </svg>
          <span>複製</span>
        </button>
      </div>
      <pre><code>${highlightR(text)}</code></pre>
    </div>`;

  const callout = (title, body, type = "") => `
    <aside class="callout ${type}">
      <strong>${title}</strong>
      <p>${body}</p>
    </aside>`;

  const table = (headers, rows) => `
    <div class="table-wrap">
      <table>
        <thead><tr>${headers.map(x => `<th>${x}</th>`).join("")}</tr></thead>
        <tbody>${rows.map(row =>
          `<tr>${row.map(x => `<td>${x}</td>`).join("")}</tr>`).join("")}
        </tbody>
      </table>
    </div>`;

  function spectrumSVG() {
    const waves = [];
    for (let s = 0; s < 7; s += 1) {
      const points = [];
      for (let i = 0; i <= 100; i += 1) {
        const x = 48 + i * 6.55;
        const peak = (mu, w, h) => h * Math.exp(-Math.pow((i - mu) / w, 2));
        const baseline = 164 - .43 * i - s * 5.2;
        const y = baseline - peak(18, 6, 26) - peak(48, 7, 34)
          - peak(66, 5, 52) - peak(87, 8, 40) + Math.sin(i / 5 + s) * 2.3;
        points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
      }
      waves.push(`<polyline class="chart-line${s === 5 ? " accent" : ""}"
                    points="${points.join(" ")}"/>`);
    }
    return `<figure class="visual">
      <figcaption>corn_m51 近紅外光譜（教學示意；紅線代表其中一個樣品）</figcaption>
      <svg viewBox="0 0 760 230" role="img"
           aria-label="多條玉米近紅外光譜曲線">
        <line class="chart-axis" x1="48" y1="15" x2="48" y2="190"/>
        <line class="chart-axis" x1="48" y1="190" x2="715" y2="190"/>
        ${[70, 110, 150].map(y =>
          `<line class="chart-grid" x1="48" y1="${y}" x2="715" y2="${y}"/>`
        ).join("")}
        ${waves.join("")}
        ${[1100, 1400, 1700, 2000, 2300].map((v, i) =>
          `<text class="chart-text" x="${58 + i * 153}" y="212">${v}</text>`
        ).join("")}
        <text class="chart-text" x="345" y="226">波長 (nm)</text>
        <text class="chart-text" transform="translate(15 145) rotate(-90)">log(1/R)</text>
      </svg>
    </figure>`;
  }

  function rmsecvSVG() {
    return `<figure class="visual">
      <figcaption>潛在變數數目與交叉驗證誤差</figcaption>
      <svg viewBox="0 0 760 230" role="img" aria-label="RMSECV 隨成分數下降後回升">
        <line class="chart-axis" x1="58" y1="20" x2="58" y2="190"/>
        <line class="chart-axis" x1="58" y1="190" x2="720" y2="190"/>
        ${[55, 95, 135, 175].map(y =>
          `<line class="chart-grid" x1="58" y1="${y}" x2="720" y2="${y}"/>`
        ).join("")}
        <polyline class="chart-line accent"
          points="80,48 145,79 210,113 275,142 340,160 405,168 470,163 535,153 600,137 665,114"/>
        <circle cx="405" cy="168" r="5" fill="#e63220"/>
        <line class="chart-mark" x1="405" y1="30" x2="405" y2="190"/>
        <text class="chart-text" x="388" y="22">optLV</text>
        ${Array.from({length: 10}, (_, i) =>
          `<text class="chart-text" x="${76 + i * 65}" y="212">${i + 1}</text>`
        ).join("")}
        <text class="chart-text" x="350" y="228">PLS 成分數</text>
        <text class="chart-text" transform="translate(17 146) rotate(-90)">RMSECV</text>
      </svg>
    </figure>`;
  }

  function rocSVG() {
    return `<figure class="visual">
      <figcaption>ROC 與 PR 曲線：分類器不能只看 accuracy</figcaption>
      <svg viewBox="0 0 760 240" role="img" aria-label="ROC 與精確率召回率曲線">
        <g transform="translate(15 0)">
          <line class="chart-axis" x1="45" y1="20" x2="45" y2="195"/>
          <line class="chart-axis" x1="45" y1="195" x2="340" y2="195"/>
          <line class="chart-grid" x1="45" y1="195" x2="340" y2="20"/>
          <path class="chart-line accent" d="M45 195 C55 112 90 64 160 42 S275 23 340 20"/>
          <text class="chart-text" x="163" y="225">1 − specificity</text>
          <text class="chart-text" x="125" y="16">ROC</text>
          <text class="chart-text" transform="translate(10 135) rotate(-90)">sensitivity</text>
        </g>
        <g transform="translate(390 0)">
          <line class="chart-axis" x1="25" y1="20" x2="25" y2="195"/>
          <line class="chart-axis" x1="25" y1="195" x2="320" y2="195"/>
          <path class="chart-line accent" d="M25 38 C88 40 110 55 160 72 S250 116 320 160"/>
          <text class="chart-text" x="155" y="225">recall</text>
          <text class="chart-text" x="135" y="16">PR</text>
          <text class="chart-text" transform="translate(-7 130) rotate(-90)">precision</text>
        </g>
      </svg>
    </figure>`;
  }

  function selectionSVG() {
    const paths = Array.from({length: 18}, (_, s) => {
      const pts = Array.from({length: 32}, (_, i) => {
        const x = 45 + i * 21;
        const fade = Math.max(0, (i - 7) / 24);
        const signal = s % 6 === 0 ? Math.sin(i / 4 + s) * 48 * fade
                                  : Math.sin(i / 4 + s) * 14 * (1 - fade);
        return `${x},${112 - signal}`;
      });
      return `<polyline class="chart-line${s % 6 === 0 ? " accent" : ""}"
                points="${pts.join(" ")}"/>`;
    }).join("");
    return `<figure class="visual">
      <figcaption>CARS 係數路徑：淘汰弱變數，保留穩定訊號</figcaption>
      <svg viewBox="0 0 760 230" role="img" aria-label="CARS 變數係數路徑">
        <line class="chart-axis" x1="45" y1="112" x2="720" y2="112"/>
        <line class="chart-mark" x1="505" y1="18" x2="505" y2="205"/>
        ${paths}
        <text class="chart-text" x="486" y="16">最佳子集</text>
        <text class="chart-text" x="315" y="224">Monte Carlo 抽樣次數</text>
      </svg>
    </figure>`;
  }

  const lessons = [
    {
      id: 1,
      title: "開始使用 libPLS",
      shortTitle: "開始使用 libPLS",
      level: "入門",
      duration: "約 20 分鐘",
      objective: "認識套件功能、載入兩組範例資料，並建立一個可重現的分析環境。",
      keyPoints: [
        "分清楚迴歸與分類資料",
        "確認 X 與 y 的維度",
        "所有隨機流程固定 seed",
        "從 help 與 demo 找範例"
      ],
      sections: [
        {
          title: "1.1 套件定位",
          body: `<p class="lead">libPLS 是 MATLAB libPLS 1.95 的原生 R 移植版，涵蓋
            PLS 迴歸、PLS-DA、交叉驗證、變數選擇、ROC/PR、OSC 與 ECR。
            它特別適合光譜等「變數多、共線性高」的化學計量資料。</p>
            ${spectrumSVG()}
            ${table(
              ["問題", "主要函數", "典型資料"],
              [
                ["連續值預測", "<code>pls()</code>、<code>plscv()</code>", "水分、蛋白質、濃度"],
                ["二元分類", "<code>plslda()</code>、<code>plsldacv()</code>", "陽性/陰性、品種 A/B"],
                ["變數篩選", "<code>carspls()</code>、<code>mcuvepls()</code>", "波長、感測器特徵"],
                ["模型評估", "<code>plsval()</code>、<code>roccurve()</code>", "獨立測試集"]
              ])}`
        },
        {
          title: "1.2 安裝與載入",
          body: `${code(`# 從本專案建置後安裝
install.packages("libPLS_1.95.0.tar.gz", repos = NULL, type = "source")

# 每次分析工作階段
library(libPLS)
packageVersion("libPLS")
help(package = "libPLS")
demo(package = "libPLS")`)}
            ${callout("Windows 提醒",
              "若命令列找不到 Rscript，可使用 C:/Program Files/R/R-4.6.1/bin/Rscript.exe。套件本身只依賴 R 內建的 graphics、grDevices、stats 與 utils。")}`
        },
        {
          title: "1.3 認識範例資料",
          body: `${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

dim(X)       # 80 × 700：80 個樣品、700 個波長
length(y)    # 80 個水分參考值
range(y)

# 分類資料：96 個樣品、40 個變數，類別編碼為 -1 / 1
data(DM2)
dim(DM2$Xcal)
table(DM2$ycal)`)}
            ${callout("第一個資料檢查原則",
              "X 必須是純數值矩陣，列代表樣品、欄代表變數；y 的長度必須等於 nrow(X)。分類函數目前要求二元類別以 -1 與 1 編碼。",
              "warning")}`
        },
        {
          title: "1.4 可重現分析骨架",
          body: `${code(`set.seed(195)
data(corn_m51)

X <- as.matrix(corn_m51$X)
y <- as.numeric(corn_m51$y)

stopifnot(
  is.numeric(X),
  nrow(X) == length(y),
  all(is.finite(X)),
  all(is.finite(y))
)

sessionInfo()`)}
            <p>libPLS 的隨機演算法提供 <code>seed</code> 參數，而且不會永久改變
            呼叫端的全域亂數狀態。研究報告仍應記錄 R、套件版本、seed 與資料切分。</p>`
        }
      ],
      quiz: {
        question: "對 corn_m51 而言，X 的一列與一欄分別代表什麼？",
        options: [
          "一列是波長、一欄是樣品",
          "一列是樣品、一欄是波長變數",
          "一列是模型、一欄是潛在變數"
        ],
        answer: 1,
        explanation: "正確。光譜矩陣通常採樣品 × 波長；因此 nrow(X) 必須等於 length(y)。"
      }
    },
    {
      id: 2,
      title: "資料結構與前處理",
      shortTitle: "資料結構與前處理",
      level: "入門",
      duration: "約 30 分鐘",
      objective: "掌握 centering、autoscaling、Pareto 等前處理，並避免資料洩漏。",
      keyPoints: [
        "只用校正集估計參數",
        "驗證集沿用相同中心與尺度",
        "光譜不一定需要 autoscaling",
        "先畫圖再決定前處理"
      ],
      sections: [
        {
          title: "2.1 為什麼需要前處理",
          body: `<p>PLS 會依 X 與 y 的共變異尋找方向。若不同欄位尺度差異很大，
            大尺度變數可能支配模型。<strong>中心化</strong>移除平均值；
            <strong>自動標準化</strong>再除以標準差。</p>
            <div class="formula">x′<sub>ij</sub> =
              (x<sub>ij</sub> − μ<sub>j</sub>) / s<sub>j</sub></div>
            ${table(
              ["method", "處理", "適用情境"],
              [
                ["<code>center</code>", "減去平均值", "同一量測尺度的連續光譜；常用預設"],
                ["<code>autoscaling</code>", "中心化後除以 SD", "不同單位的描述變數"],
                ["<code>pareto</code>", "除以 √SD", "介於中心化與 autoscaling"],
                ["<code>unilength</code>", "欄向量單位化", "需要比較向量方向"],
                ["<code>minmax</code>", "縮放至固定範圍", "邊界明確的特徵"],
                ["<code>none</code>", "不轉換", "資料已在外部妥善處理"]
              ])}`
        },
        {
          title: "2.2 配適與套用參數",
          body: `${code(`data(corn_m51)
X <- corn_m51$X

# 校正集：同時傳回中心與尺度
cal_id <- 1:60
test_id <- 61:80
prep_cal <- pretreat(
  X[cal_id, ],
  method = "autoscaling",
  return_parameters = TRUE
)

# 測試集只能沿用校正集參數，不能重新估計
Xtest_scaled <- pretreat(
  X[test_id, ],
  method = "autoscaling",
  para1 = prep_cal$para1,
  para2 = prep_cal$para2
)

dim(prep_cal$X)
dim(Xtest_scaled)`)}
            ${callout("避免資料洩漏",
              "不可先對完整資料做 autoscaling 再切校正/測試集。測試集平均與標準差若參與配適，評估會過度樂觀。",
              "warning")}`
        },
        {
          title: "2.3 與 PLS 模型整合",
          body: `${code(`# pls() 會在模型內保存 X 與 y 的前處理參數
fit_center <- pls(X[cal_id, ], corn_m51$y[cal_id],
                  A = 5, method = "center")
fit_auto <- pls(X[cal_id, ], corn_m51$y[cal_id],
                A = 5, method = "autoscaling")

# predict()/plsval() 會使用模型中保存的參數處理新資料
pred_center <- predict(fit_center, X[test_id, ])
pred_auto <- predict(fit_auto, X[test_id, ])

c(
  center_RMSEP = sqrt(mean((pred_center - corn_m51$y[test_id])^2)),
  auto_RMSEP   = sqrt(mean((pred_auto   - corn_m51$y[test_id])^2))
)`)}
            <p>前處理不是越多越好。應在相同資料切分與 CV 設計下比較，而不是只看
            校正集擬合誤差。</p>`
        }
      ],
      quiz: {
        question: "下列哪一個測試集處理方式可以避免資料洩漏？",
        options: [
          "對完整 X autoscaling 後再切資料",
          "各自計算校正集與測試集的平均值",
          "只從校正集估計平均與尺度，再套用到測試集"
        ],
        answer: 2,
        explanation: "正確。任何會從資料學得的參數，都只能由校正/訓練資料估計。"
      }
    },
    {
      id: 3,
      title: "PLS 迴歸建模",
      shortTitle: "PLS 迴歸建模",
      level: "基礎",
      duration: "約 35 分鐘",
      objective: "理解潛在變數，配適 PLS1 模型並正確預測新樣品。",
      keyPoints: [
        "A 是成分數，不是變數數",
        "PLS 同時考量 X 與 y",
        "預測新資料使用 predict",
        "先 CV 選 A，再報獨立 RMSEP"
      ],
      sections: [
        {
          title: "3.1 PLS 在做什麼",
          body: `<p>主成分分析只尋找 X 變異最大的方向；PLS 則尋找與 y
            共變異最大的潛在方向。這使它適合高度共線、p 接近或大於 n 的資料。</p>
            <div class="formula">X = TPᵀ + E　　y = Tq + f</div>
            <p><code>T</code> 是樣品 scores、<code>P</code> 是 X loadings、
            <code>W</code> 是 weights，<code>q</code> 描述 scores 與 y 的關係。</p>`
        },
        {
          title: "3.2 配適與檢查模型",
          body: `${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

fit <- pls(X, y, A = 5, method = "center")
print(fit)
names(fit)

# 重要矩陣及維度
dim(fit$X_scores)       # scores
dim(fit$X_loadings)     # loadings
dim(fit$Wstar)          # 投影權重
length(fit$regcoef_original) # 迴歸係數（含截距）

# 訓練資料的擬合值
head(fit$y_fit)`)}
            ${callout("不要用 RMSEC 選成分數",
              "增加成分通常會讓校正誤差下降，但不代表新樣品預測更好。成分數必須由交叉驗證決定。",
              "warning")}`
        },
        {
          title: "3.3 新樣品預測",
          body: `${code(`set.seed(195)
rank_id <- ks(X)       # Kennard–Stone：均勻涵蓋 X 空間
cal <- rank_id[1:60]
test <- rank_id[61:80]

fit <- pls(X[cal, ], y[cal], A = 5, method = "center")

# S3 predict 方法
ypred <- predict(fit, X[test, ])
RMSEP <- sqrt(mean((ypred - y[test])^2))

# plsval() 回傳預測值與 RMSEP；R2 可由測試殘差計算
val <- plsval(fit, X[test, ], y[test])
R2_test <- 1 - sum((val$ypred - y[test])^2) /
  sum((y[test] - mean(y[test]))^2)
c(RMSEP = val$RMSEP, R2 = R2_test)

plot(y[test], val$ypred,
     xlab = "Reference", ylab = "Predicted")
abline(0, 1, col = "red", lty = 2)`)}
            <p><code>ks()</code> 依 X 空間距離挑選代表性樣品，但它不是隨機抽樣。
            若要估計一般化誤差的不確定性，還需重複抽樣或外部驗證。</p>`
        }
      ],
      quiz: {
        question: "PLS 的成分數 A 最合理的選擇依據是什麼？",
        options: [
          "讓訓練資料 RMSEC 最小",
          "使用交叉驗證的 RMSECV 並考量模型簡潔度",
          "固定等於原始變數數目"
        ],
        answer: 1,
        explanation: "正確。通常選 RMSECV 最低或在誤差近似時較簡單的模型。"
      }
    },
    {
      id: 4,
      title: "交叉驗證與調參",
      shortTitle: "交叉驗證與調參",
      level: "基礎",
      duration: "約 40 分鐘",
      objective: "使用 K-fold、Monte Carlo 與雙層交叉驗證，選擇成分數並避免樂觀偏差。",
      keyPoints: [
        "optLV 來自驗證資料",
        "明確設定 fold order",
        "調參與最終評估分層",
        "報告 RMSECV 的設計"
      ],
      sections: [
        {
          title: "4.1 K-fold 交叉驗證",
          body: `${rmsecvSVG()}
            ${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

cv <- plscv(
  X, y,
  A = 10,             # 最多嘗試 10 個成分
  K = 10,
  method = "center",
  PROCESS = FALSE,
  order = 1,          # 0: 依 y 排序，1: 隨機，2: 原順序
  seed = 195
)

cv$optLV
cv$RMSECV
plot(seq_along(cv$RMSECV), cv$RMSECV, type = "b",
     xlab = "Number of components", ylab = "RMSECV")`)}
            ${callout("順序參數很重要",
              "若資料列依批次、濃度或時間排序，order = 2 可能產生不均衡 fold；order = 1 應同時提供 seed。")}`
        },
        {
          title: "4.2 Monte Carlo 與重複雙層 CV",
          body: `${code(`# 重複隨機校正/驗證切分
mccv <- plsmccv(
  X, y, A = 8, method = "center",
  N = 100, ratio = 0.8, OPT = FALSE, seed = 195
)

# 雙層 CV：外層估計泛化誤差，內層選成分數
dcv <- plsdcv(
  X, y, A = 8, K = 5, method = "center",
  order = 1, seed = 195
)

# 重複雙層 CV：計算較多，但更能反映切分不確定性
rdcv <- plsrdcv(
  X, y, A = 8, K = 5, method = "center",
  Nmcs = 10, OPT = FALSE, seed = 195
)`)}
            ${table(
              ["函數", "用途", "代價"],
              [
                ["<code>plscv</code>", "快速選 optLV", "低"],
                ["<code>plsmccv</code>", "觀察多次隨機切分", "中"],
                ["<code>plsdcv</code>", "調參與評估分離", "高"],
                ["<code>plsrdcv</code>", "估計切分不確定性", "很高"]
              ])}`
        },
        {
          title: "4.3 一個正確的評估流程",
          body: `${code(`set.seed(195)
id <- sample(seq_len(nrow(X)))
train <- id[1:60]
test <- id[61:80]

# 1. 只在 train 內選成分
cv <- plscv(X[train, ], y[train], A = 10, K = 5,
            method = "center", PROCESS = FALSE,
            order = 1, seed = 195)

# 2. 用選到的成分重建 train 模型
fit <- pls(X[train, ], y[train],
           A = cv$optLV, method = "center")

# 3. test 只使用一次，估計最終表現
test_result <- plsval(fit, X[test, ], y[test])
round(c(RMSEP = test_result$RMSEP,
        R2 = test_result$R2), 4)`)}
            ${callout("研究報告至少要寫",
              "樣品數、切分方法、fold 數、重複次數、前處理、成分上限、optLV 規則、seed，以及最終評估是否為真正未參與調參的資料。",
              "success")}`
        }
      ],
      quiz: {
        question: "為什麼雙層交叉驗證通常比單層 CV 更適合估計最終表現？",
        options: [
          "它會使用更多 PLS 成分",
          "外層測試 fold 不參與內層調參，降低樂觀偏差",
          "它不需要前處理"
        ],
        answer: 1,
        explanation: "正確。內層負責選模型，外層只負責評估，角色分離較公平。"
      }
    },
    {
      id: 5,
      title: "PLS-DA 二元分類",
      shortTitle: "PLS-DA 分類",
      level: "中階",
      duration: "約 40 分鐘",
      objective: "完成二元 PLS-LDA 建模、交叉驗證、預測與混淆矩陣解讀。",
      keyPoints: [
        "類別編碼為 -1 / 1",
        "類別不平衡考慮 weight",
        "分數與最終類別要分開",
        "驗證資料不參與建模"
      ],
      sections: [
        {
          title: "5.1 載入分類資料",
          body: `${code(`data(DM2)
X <- DM2$Xcal
y <- DM2$ycal

dim(X)
table(y)
stopifnot(all(sort(unique(y)) == c(-1, 1)))`)}
            <p>libPLS 的 PLS-DA 實作先用 PLS 將資料投影到低維 score，
            再以 LDA 建立分類邊界。輸入 y 必須是二元 <code>-1</code> 與
            <code>1</code>。</p>`
        },
        {
          title: "5.2 選成分並配適 PLS-LDA",
          body: `${code(`cv_da <- plsldacv(
  X, y,
  A = 8,
  K = 5,
  method = "autoscaling",
  weight = 0,
  OPT = FALSE,
  order = 1,
  seed = 195
)

fit_da <- plslda(
  X, y,
  A = cv_da$optLV,
  method = "autoscaling",
  weight = 0
)

c(
  error = fit_da$error,
  sensitivity = fit_da$sensitivity,
  specificity = fit_da$specificity
)`)}
            ${callout("何時使用 weight = 1？",
              "當兩類樣品數差異大，而且兩類錯分代價相近時，可用等類別權重。若錯分代價不同，應另外設計決策閾值與評估指標。")}`
        },
        {
          title: "5.3 獨立驗證與混淆矩陣",
          body: `${code(`set.seed(195)
train <- sample(seq_len(nrow(X)), 72)
test <- setdiff(seq_len(nrow(X)), train)

inner <- plsldacv(
  X[train, ], y[train], A = 6, K = 5,
  method = "autoscaling", OPT = FALSE,
  order = 1, seed = 195
)
model <- plslda(X[train, ], y[train],
                A = inner$optLV, method = "autoscaling")
val <- plsldaval(model, X[test, ], y[test])

pred_class <- sign(val$ypred)
table(reference = y[test], predicted = pred_class)
c(
  error = val$error,
  sensitivity = mean(pred_class[y[test] == 1] == 1),
  specificity = mean(pred_class[y[test] == -1] == -1)
)`)}
            <p>accuracy 可能掩蓋少數類別表現。至少同時報告 sensitivity、
            specificity 與混淆矩陣；下一章再加入 ROC 與 PR。</p>`
        }
      ],
      quiz: {
        question: "若資料有 90 個陰性與 10 個陽性，只報 accuracy 有何風險？",
        options: [
          "accuracy 不能介於 0 與 1",
          "全部預測為陰性也有 90% accuracy，卻完全抓不到陽性",
          "accuracy 只能用於迴歸"
        ],
        answer: 1,
        explanation: "正確。類別不平衡時要同時看 sensitivity、specificity、ROC/PR。"
      }
    },
    {
      id: 6,
      title: "ROC、PR 與模型評估",
      shortTitle: "模型評估指標",
      level: "中階",
      duration: "約 30 分鐘",
      objective: "從連續分類分數建立 ROC 與 PR 曲線，選擇與問題相符的指標。",
      keyPoints: [
        "ROC 使用 sensitivity/specificity",
        "PR 關注陽性預測品質",
        "曲線輸入應是連續 score",
        "AUC 不能取代外部驗證"
      ],
      sections: [
        {
          title: "6.1 ROC 曲線",
          body: `${rocSVG()}
            ${code(`data(DM2)
X <- DM2$Xcal
y <- DM2$ycal

fit <- plslda(X, y, A = 3, method = "autoscaling")

# yfit 是連續判別分數；flag = FALSE 不自動畫圖
roc <- roccurve(fit$yfit, y, flag = FALSE)
roc$AUC

# 若要使用套件內建繪圖
roccurve(fit$yfit, y, flag = TRUE)`)}
            <div class="formula">sensitivity = TP/(TP+FN)　　specificity = TN/(TN+FP)</div>`
        },
        {
          title: "6.2 Precision–Recall 曲線",
          body: `${code(`pr <- prcurve(fit$yfit, y, nbin = 100)
pr$auprc

plot(pr$recall, pr$precision, type = "l",
     xlab = "Recall", ylab = "Precision")`)}
            <p>當陽性類別稀少時，PR 曲線通常比 ROC 更直接反映「找出的陽性有多少是真的」。
            但 AUPRC 會隨陽性比例改變，跨資料集比較時要說明 prevalence。</p>`
        },
        {
          title: "6.3 指標選擇",
          body: `${table(
              ["指標", "適合回答", "注意"],
              [
                ["Sensitivity", "陽性有多少被找出？", "忽略 FP"],
                ["Specificity", "陰性有多少被排除？", "忽略 FN"],
                ["ROC AUC", "隨機陽性分數高於陰性的機率", "嚴重不平衡時可能過度樂觀"],
                ["Precision", "預測陽性有多少是真的？", "受陽性比例影響"],
                ["PR AUC", "不同 recall 下的 precision", "須報告基準 prevalence"]
              ])}
            ${callout("重要限制",
              "用訓練資料 fit$yfit 計算的 AUC 只是示範。正式報告應使用外層 CV 或獨立測試資料的 out-of-sample 分數。",
              "warning")}`
        }
      ],
      quiz: {
        question: "PR 曲線應優先傳入哪一種預測？",
        options: [
          "已經切成 -1/1 的最終類別",
          "連續判別分數或陽性機率",
          "樣品編號"
        ],
        answer: 1,
        explanation: "正確。曲線要掃描不同閾值，因此需要連續分數。"
      }
    },
    {
      id: 7,
      title: "變數選擇：CARS、MC-UVE、MWPLS",
      shortTitle: "變數選擇（CARS）",
      level: "中階",
      duration: "約 50 分鐘",
      objective: "比較三種光譜變數選擇方法，並以固定 seed 建立可重現的 CARS 子集。",
      keyPoints: [
        "變數選擇放在 CV 內",
        "CARS 使用係數競爭淘汰",
        "MC-UVE 看係數穩定度",
        "MWPLS 保留連續波長區段"
      ],
      sections: [
        {
          title: "7.1 CARS 的核心概念",
          body: `${selectionSVG()}
            <p>CARS 在多次 Monte Carlo 抽樣中建立 PLS，依迴歸係數絕對值進行
            指數遞減與自適應重加權，最後以 RMSECV 選出最佳變數子集。</p>
            ${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

cars <- carspls(
  X, y,
  A = 8,
  fold = 5,
  method = "center",
  num = 50,
  selectLV = 0,
  originalVersion = 1,
  order = 1,
  seed = 195,
  process = FALSE
)

cars$iterOPT
cars$optLV
length(cars$vsel)
head(cars$vsel)  # R 的變數索引從 1 開始
plotcars(cars)`)}`
        },
        {
          title: "7.2 MC-UVE 與 MWPLS",
          body: `${code(`# MC-UVE：係數平均值相對於標準差的可靠度
uve <- mcuvepls(
  X, y, A = 6, method = "center",
  N = 100, ratio = 0.8, seed = 195
)
head(uve$SortedVariable)
plot(abs(uve$RI), type = "l",
     ylab = "|Reliability index|")

# MWPLS：沿著連續波長視窗建立局部模型
mw <- mwpls(X, y, A = 6, width = 15)
matplot(mw$WP, mw$RMSEF, type = "l",
        xlab = "Window position", ylab = "RMSEF")`)}
            ${table(
              ["方法", "選擇單位", "解讀"],
              [
                ["CARS", "個別變數子集", "係數競爭 + RMSECV"],
                ["MC-UVE", "個別變數排序", "係數穩定度"],
                ["MWPLS", "連續視窗", "局部波段的建模誤差"]
              ])}`
        },
        {
          title: "7.3 無偏的選擇流程",
          body: `${code(`set.seed(195)
id <- sample(seq_len(nrow(X)))
train <- id[1:60]
test <- id[61:80]

# 變數選擇只能看 train
cars_train <- carspls(
  X[train, ], y[train],
  A = 8, fold = 5, num = 50,
  method = "center", selectLV = 0,
  originalVersion = 1, order = 1,
  seed = 195
)
v <- cars_train$vsel

# 選成分、配適與最終測試也都使用相同 v
cv <- plscv(X[train, v], y[train], A = 8, K = 5,
            method = "center", PROCESS = FALSE,
            order = 1, seed = 195)
fit <- pls(X[train, v], y[train],
           A = cv$optLV, method = "center")
val <- plsval(fit, X[test, v], y[test])
val$RMSEP`)}
            ${callout("最常見的選擇偏差",
              "先用全部資料做 CARS，再對同一資料交叉驗證，會讓測試 fold 的 y 影響變數子集。嚴格評估必須在每個外層訓練 fold 內重新選變數。",
              "warning")}`
        }
      ],
      quiz: {
        question: "在外部測試集存在時，CARS 應在哪些資料上執行？",
        options: [
          "完整資料，因為樣品越多越穩定",
          "只在訓練資料內，測試集到最後才使用",
          "只在測試資料內"
        ],
        answer: 1,
        explanation: "正確。選變數也是模型訓練的一部分，不能看到測試集。"
      }
    },
    {
      id: 8,
      title: "進階變數評估與樣品選擇",
      shortTitle: "進階主題",
      level: "進階",
      duration: "約 55 分鐘",
      objective: "理解 Random Frog、SPA、IRIV、PHADIA、VCN、IRF 與 Kennard–Stone 的用途邊界。",
      keyPoints: [
        "SPA 此處指 subwindow permutation",
        "方法輸出常是排序或機率",
        "高 N 運算要記錄 seed",
        "先定義選擇目標再挑方法"
      ],
      sections: [
        {
          title: "8.1 隨機搜尋：Random Frog",
          body: `${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

rf <- randomfrog_pls(
  X, y,
  A = 6,
  method = "center",
  N = 1000,       # 正式研究常使用更大的 N
  Q = 20,
  seed = 195,
  process = FALSE
)

head(rf$Vrank)
plot(rf$probability, type = "h",
     xlab = "Variable", ylab = "Selection probability")`)}
            <p>Random Frog 以馬可夫鏈式的變數子集移動估計選取機率。高機率表示變數
            經常出現在可接受的模型中，但不等於因果重要性。</p>`
        },
        {
          title: "8.2 分類變數評估：SPA",
          body: `${code(`data(DM2)
Xc <- DM2$Xcal
yc <- DM2$ycal

# 此套件的 SPA 是 subwindow permutation analysis，
# 不是 successive projections algorithm。
spa_fit <- spa(
  Xc, yc,
  A = 3, K = 5, Q = 10,
  N = 100,
  ratio = 0.75,
  method = "autoscaling",
  seed = 195,
  process = FALSE
)

head(spa_fit$RankedVariable)
plotspa(spa_fit)`)}
            ${callout("名稱辨識",
              "光譜文獻中 SPA 也常指 successive projections algorithm；libPLS 1.95 的 spa() 是 subwindow permutation analysis，解讀前務必確認。",
              "warning")}`
        },
        {
          title: "8.3 其他策略與樣品選擇",
          body: `${table(
              ["函數", "核心概念", "主要輸出用途"],
              [
                ["<code>iriv()</code>", "反覆保留有資訊變數", "精煉變數子集"],
                ["<code>phadia()</code>", "置換 + 分布評估", "變數顯著性/方向"],
                ["<code>vcn()</code>", "variable combination normalization", "組合式評估"],
                ["<code>irf()</code>", "iteratively retaining informative variables", "逐輪淘汰"],
                ["<code>ks()</code>", "Kennard–Stone 距離覆蓋", "代表性校正樣品"],
                ["<code>mcs()</code>", "Monte Carlo sampling", "樣品/模型穩定度"]
              ])}
            ${code(`# Kennard–Stone 排序
rank_id <- ks(X)
cal <- rank_id[1:60]
test <- rank_id[61:80]

# 計算量較高的方法：先用小 N 測試流程，再提高 N
iriv_fit <- iriv(
  X, y, A_max = 6, fold = 5,
  method = "center", seed = 195,
  max_rounds = 3, row = 20,
  max_backward = 5, process = FALSE
)
iriv_fit$SelectedVariables`)}
            ${callout("計算資源策略",
              "先用小 N 做程式與資料形狀 smoke test，確認無誤後再提高到研究規模；不要把小 N 的選取頻率當成穩定的科學結論。")}`
        }
      ],
      quiz: {
        question: "libPLS 的 spa() 指的是哪一種方法？",
        options: [
          "Successive projections algorithm",
          "Subwindow permutation analysis",
          "Spectral principal averaging"
        ],
        answer: 1,
        explanation: "正確。這是很容易混淆的同名縮寫。"
      }
    },
    {
      id: 9,
      title: "OSC、OPLS 與 ECR",
      shortTitle: "進階建模",
      level: "進階",
      duration: "約 50 分鐘",
      objective: "使用正交訊號校正與彈性成分迴歸，並理解方法驗證上的額外責任。",
      keyPoints: [
        "OSC 參數只由校正資料估計",
        "ECR 用 alpha 控制成分彈性",
        "所有額外處理都放入 CV",
        "複雜方法要與簡單基準比較"
      ],
      sections: [
        {
          title: "9.1 OSC 與 OPLS",
          body: `<p>Orthogonal Signal Correction 移除 X 中與 y 正交的系統變異。
            這可能改善可解釋性，但若在完整資料上先做 OSC，就會造成嚴重洩漏。</p>
            ${code(`data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

cal <- 1:60
test <- 61:80

# 三種 OSC 介面都同時接收 Xcal、Ycal、Xtest，
# 確保校正參數來自校正集。
osc_wold <- oscwold(
  X[cal, ], y[cal],
  X[test, ],
  nOSC = 1
)

osc_fearn <- oscfearn(
  X[cal, ], y[cal],
  X[test, ],
  nOSC = 1
)

opls_fit <- opls(
  X[cal, ], y[cal],
  X[test, ],
  nOSC = 1
)`)}
            ${callout("實作限制",
              "原 MATLAB oscwold.m 依賴缺少的 pls_nipals；R 版重建一成分權重更新並增加收斂與符號對齊保護。跨語言結果應比較合理不變量，不應假設每個元素完全相同。",
              "warning")}`
        },
        {
          title: "9.2 Elastic Component Regression",
          body: `${code(`set.seed(195)
n <- 25
p <- 50
x <- pretreat(matrix(runif(n * p), n, p), "center")
s <- svd(x)
Tscore <- x %*% s$v[, 1:5]
X0 <- Tscore %*% t(s$v[, 1:5])
Xsim <- cbind(X0, matrix(runif(n * 50), n, 50))
ysim <- drop(Tscore %*% c(5, 4, 3, 2, 1))

ecr_cv <- ecrcv(
  Xsim, ysim, A = 5, K = 5,
  method = "center", OPT = FALSE, order = 0
)

fit <- ecr(
  Xsim[1:15, ], ysim[1:15],
  A = 5, method = "center", alpha = 0.5
)
pred <- ecrpred(fit, Xsim[16:25, ], ysim[16:25])
pred$RMSEP`)}
            <p><code>alpha</code> 控制成分建構的彈性。它本身也是超參數；
            若嘗試多個 alpha，必須在內層 CV 選擇。</p>`
        },
        {
          title: "9.3 模型路徑與基準比較",
          body: `${code(`path <- modelpath(
  Xsim, ysim,
  A = 5,
  method = "center",
  alpha = seq(0, 1, by = 0.1)
)
plotpath(path)

# 最少與一個簡單 PLS 基準比較
base_cv <- plscv(
  Xsim, ysim, A = 5, K = 5,
  method = "center", PROCESS = FALSE,
  order = 1, seed = 195
)`)}
            ${callout("進階方法的證據門檻",
              "模型更複雜不代表更準。應在相同外層切分、前處理與評估指標下，與簡單 PLS 基準比較，並報告變異與失敗案例。",
              "success")}`
        }
      ],
      quiz: {
        question: "OSC 最安全的使用方式是？",
        options: [
          "先在全部資料估計 OSC，再做 CV",
          "在每個訓練 fold 內估計 OSC，套用到對應驗證 fold",
          "只對 y 做 OSC"
        ],
        answer: 1,
        explanation: "正確。OSC 是會學習資料結構的步驟，必須包含在重抽樣流程內。"
      }
    },
    {
      id: 10,
      title: "完整案例與研究工作流",
      shortTitle: "總結與延伸學習",
      level: "整合",
      duration: "約 60 分鐘",
      objective: "把資料檢查、切分、CARS、調參、獨立驗證與可重現報告串成完整流程。",
      keyPoints: [
        "先固定研究問題與終點",
        "測試集保持不可見",
        "保存模型、索引與 sessionInfo",
        "限制與不確定性一起報告"
      ],
      sections: [
        {
          title: "10.1 端到端 corn moisture 案例",
          body: `${code(`library(libPLS)
set.seed(195)
data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y

# 1. 建立一次性的外部測試集
id <- sample(seq_len(nrow(X)))
train <- id[1:60]
test <- id[61:80]

# 2. 只在 train 內進行 CARS
cars <- carspls(
  X[train, ], y[train],
  A = 8, fold = 5, method = "center",
  num = 100, selectLV = 0,
  originalVersion = 1, order = 1,
  seed = 195, process = FALSE
)
v <- cars$vsel

# 3. 在選定變數上用內層 CV 選 PLS 成分
cv <- plscv(
  X[train, v], y[train],
  A = min(8, length(v)), K = 5,
  method = "center", PROCESS = FALSE,
  order = 1, seed = 196
)

# 4. 重建模型並只評估一次測試集
fit <- pls(
  X[train, v], y[train],
  A = cv$optLV, method = "center"
)
val <- plsval(fit, X[test, v], y[test])

result <- data.frame(
  n_train = length(train),
  n_test = length(test),
  n_variables = length(v),
  n_components = cv$optLV,
  RMSEP = val$RMSEP,
  R2 = 1 - sum((val$ypred - y[test])^2) /
    sum((y[test] - mean(y[test]))^2)
)
print(result)`)}`
        },
        {
          title: "10.2 保存可重現成果",
          body: `${code(`analysis <- list(
  seed = 195,
  train_index = train,
  test_index = test,
  selected_variables = v,
  wavelengths_nm = 1100 + 2 * (v - 1),
  cv = cv,
  model = fit,
  validation = val,
  summary = result
)

saveRDS(analysis, "corn_cars_pls_analysis.rds")
write.csv(result, "corn_cars_pls_summary.csv", row.names = FALSE)
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")

# 新工作階段可重新載入
restored <- readRDS("corn_cars_pls_analysis.rds")
predict(restored$model, X[test, v])`)}
            ${callout("索引轉波長",
              "corn_m51 有 700 個波長，從 1100 到 2498 nm、間隔 2 nm，因此第 j 欄對應 1100 + 2 × (j − 1) nm。")}`
        },
        {
          title: "10.3 最終檢核表",
          body: `${table(
              ["階段", "必做檢查", "常見錯誤"],
              [
                ["問題定義", "連續/分類、主要指標、樣品獨立性", "把技術重複當獨立樣品"],
                ["資料處理", "缺失值、尺度、批次、異常值", "先看測試集才決定處理"],
                ["切分", "群組/時間/批次結構、固定索引", "同一來源進入 train 與 test"],
                ["調參", "只在訓練資料內完成", "用 test 選 A 或變數"],
                ["評估", "外層 CV 或獨立測試", "只報訓練 R²"],
                ["重現", "seed、版本、索引、程式、輸出", "只保存圖，不保存模型"],
                ["報告", "不確定性、限制、失敗案例", "把小資料結果過度推廣"]
              ])}
            ${code(`# 套件內建示範
demo("pls_regression", package = "libPLS")
demo("pls_discriminant", package = "libPLS")
demo("ecr", package = "libPLS")

# 完整函數索引
help(package = "libPLS")

# 再次開啟本教材（安裝套件後）
libpls_course()`)}
            ${callout("你已完成核心路徑",
              "下一步不是一次使用所有演算法，而是用同一個無偏評估設計，比較少數有科學理由的候選流程。",
              "success")}`
        }
      ],
      quiz: {
        question: "完整流程中，外部測試集最適合在什麼時候使用？",
        options: [
          "選 CARS 參數時反覆查看",
          "選 PLS 成分數時使用",
          "所有處理與調參鎖定後，只做最終一次評估"
        ],
        answer: 2,
        explanation: "正確。測試集的角色是估計最終泛化表現，不是協助做決策。"
      }
    }
  ];

  window.LIBPLS_COURSE = {
    title: "libPLS 實作課程",
    version: "1.95.0",
    lessons,
    helpers: { code, callout, table }
  };
})();

