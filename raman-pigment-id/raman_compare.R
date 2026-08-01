# raman_compare.R
# ==============================================================
# 教學用:CuPc(PB15)vs 亮藍 FCF(三芳基甲烷)拉曼指紋比對(base R 版)
# 對齊 raman_compare.py 的流程,方便逐行對照。
# 需要的檔案(由 raman_compare.py 產生):
#   raman_reference_spectra.csv   欄:wavenumber_cm-1, CuPc, FCF
#   raman_spectral_library.csv    列=光譜,欄=波數,最後一欄 class
# 只用 base R + stats,不需安裝套件。
# 進階版可用 baseline / prospectr / hyperSpec,程式碼末尾有說明。
# ==============================================================

## ---- 1. 讀參考光譜 ----
ref <- read.csv("raman_reference_spectra.csv", check.names = FALSE)
wn   <- ref[["wavenumber_cm-1"]]
cupc <- ref[["CuPc"]]
fcf  <- ref[["FCF"]]

## ---- 2. 畫並排比較圖 ----
png("raman_cupc_vs_fcf_R.png", width = 1100, height = 640, res = 130)
op <- par(mfrow = c(2, 1), mar = c(2, 4, 2, 1), oma = c(3, 0, 2, 0))
four_set <- c(748, 1337, 1453, 1526)   # CuPc pyrrole 四峰組
ring_set <- c(1534, 1587, 1619)        # FCF 芳香環叢集

plot(wn, cupc, type = "l", lwd = 2, col = "#0b7ba6",
     xlab = "", ylab = "Norm. intensity", xlim = c(200, 1750), main = "")
abline(v = four_set, col = "#b3703f", lty = 2)
mtext("CuPc  銅酞菁 (PB15) — pyrrole 四峰組 748/1337/1450/1526",
      side = 3, adj = 0, cex = 0.9, col = "#0b7ba6")

plot(wn, fcf, type = "l", lwd = 2, col = "#c98a3f",
     xlab = "", ylab = "Norm. intensity", xlim = c(200, 1750), main = "")
abline(v = ring_set, col = "#8a5a2a", lty = 2)
mtext("FCF  亮藍 (三芳基甲烷) — 芳香環叢集 1534/1587/1619,無四峰組",
      side = 3, adj = 0, cex = 0.9, col = "#c98a3f")
mtext("Raman shift (cm-1)", side = 1, outer = TRUE, line = 1)
par(op); dev.off()

## ---- 3. ModPoly 基線(Lieber & Mahadevan-Jansen)----
modpoly <- function(x, y, order = 5, it = 24) {
  yw <- y
  xc <- scale(x)                       # 標準化 x,數值穩定
  for (i in seq_len(it)) {
    fit <- lm(yw ~ poly(xc, order, raw = FALSE))
    yhat <- predict(fit)
    yw <- pmin(yw, yhat)
  }
  predict(lm(yw ~ poly(xc, order, raw = FALSE)))
}

## ---- 4. 找峰(區域極大 + 門檻 + 最小間距)----
pick_peaks <- function(x, y, min_h = 0.05, min_dist = 9) {
  n <- length(y)
  is_max <- c(FALSE, y[2:(n-1)] >= y[1:(n-2)] & y[2:(n-1)] > y[3:n], FALSE)
  cand <- which(is_max & y >= min_h)
  cand <- cand[order(-y[cand])]
  keep <- integer(0)
  for (i in cand) if (all(abs(x[i] - x[keep]) >= min_dist)) keep <- c(keep, i)
  sort(keep)
}

## ---- 5. 相關係數比對 ----
corr_match <- function(sample, refs) sapply(refs, function(r) cor(sample, r))

## ---- 6. 對一條「未知」樣品做完整流程 ----
lib <- read.csv("raman_spectral_library.csv", check.names = FALSE)
cls <- lib$class
Xlib <- as.matrix(lib[, setdiff(names(lib), "class")])
unknown <- Xlib[1, ]                    # 取第一條(實為 CuPc)當未知樣

base <- modpoly(wn, unknown)
corr_spec <- pmax(unknown - base, 0)
corr_spec <- corr_spec / max(corr_spec)
pk <- pick_peaks(wn, corr_spec)
scores <- corr_match(corr_spec, list(CuPc = cupc, FCF = fcf))

cat("\n--- 分析示範(未知樣品)---\n")
cat("偵測峰 (cm-1):", head(round(wn[pk]), 12), "\n")
cat("相關係數: CuPc =", round(scores["CuPc"], 3),
    " FCF =", round(scores["FCF"], 3), "\n")
cat("判定:", names(which.max(scores)), "\n")

## ---- 7. PCA + 最近類心分類(示範 Orange 也在做的事)----
pca <- prcomp(Xlib, center = TRUE, scale. = FALSE)
scoresPCA <- pca$x[, 1:5]
centroids <- aggregate(scoresPCA, list(cls), mean)
predict_class <- function(v) {
  d <- apply(centroids[, -1], 1, function(c) sqrt(sum((v - c)^2)))
  centroids[[1]][which.min(d)]
}
pred <- apply(scoresPCA, 1, predict_class)
cat("\nPCA(5) + 最近類心 訓練集正確率:", round(mean(pred == cls), 3), "\n")
cat("(嚴謹評估請用交叉驗證,如 class::knn + caret::train)\n")

# --------------------------------------------------------------
# 進階(需安裝套件):
#   baseline::baseline(spectra, method = "modpolyfit")   # 專業基線
#   prospectr::savitzkyGolay(y, m = 0, p = 2, w = 11)    # 平滑/微分
#   caret::train(class ~ ., data, method = "knn",
#                trControl = trainControl("cv", 5))       # 交叉驗證
# --------------------------------------------------------------
