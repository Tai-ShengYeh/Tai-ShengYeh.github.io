# libPLS 實作課程

這是一套完全離線、從入門到進階的繁體中文 HTML 課程，隨 libPLS
套件一起安裝。

## 開啟方式

安裝套件後在 R 執行：

```r
library(libPLS)
libpls_course()
```

或直接以瀏覽器開啟本資料夾的 `index.html`。教材不依賴 CDN、網路字型
或第三方 JavaScript。

## 十章內容

1. 開始使用 libPLS
2. 資料結構與前處理
3. PLS 迴歸建模
4. 交叉驗證與調參
5. PLS-DA 二元分類
6. ROC、PR 與模型評估
7. CARS、MC-UVE 與 MWPLS
8. Random Frog、SPA、IRIV 等進階變數評估
9. OSC、OPLS 與 ECR
10. 完整案例與研究工作流

## 互動功能

- 章節與學習進度保存在瀏覽器 `localStorage`。
- R 程式碼可一鍵複製。
- 每章附一題即時檢核。
- 支援深色模式、字級調整、鍵盤 `Alt+←/→` 換章。
- 桌面、平板及手機響應式版面。
- 可直接用瀏覽器列印為 PDF。

`course_examples.R` 是課程核心程式的快速驗證腳本；其中高計算量的
Monte Carlo 次數刻意縮小，只用來檢查介面與資料流。

