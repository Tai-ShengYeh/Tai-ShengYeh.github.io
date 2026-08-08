# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 06：石膏扣除與 ECOS 輸入（式 6–11）
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


# --- 6-3 產生 ECOS 輸入檔 -----------------------------------------------------
r <- fun_salt_balance("MH-01", 1.0, 100, 50, 30, 20, 40, 10, 15, 5)

round(r$x, 6)
sum(r$x)                     # 必須等於 1
cat(make_ecos_input(r))

# 存成檔案，就能直接匯入 Runsalt
writeLines(make_ecos_input(r), "MH-01_ecos_input.txt")

# 跟官方範例逐字比對
official <- readLines("data/SaltsR_upload_Example.txt")
mine     <- strsplit(make_ecos_input(r), "\n")[[1]]
data.frame(官方 = head(official, 7), 我們算的 = head(mine, 7))

# --- 三種石膏情境 -------------------------------------------------------------
cases <- list(
  `MH-01 (Ca 先被扣光, 無石膏)` = c(1.0, 100, 50, 30, 20, 40, 10, 15, 5),
  `MH-02 (SO4 限量)`            = c(1.128, 100, 180, 420, 60, 120, 45, 95, 25),
  `MH-08 (Ca 限量, 飽和警告)`   = c(1.0, 100, 40, 25, 1600, 30, 10, 700, 8)
)
for (nm in names(cases)) {
  a <- cases[[nm]]
  rr <- fun_salt_balance(nm, a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9])
  cat(sprintf("%-30s %-10s SO4adj=%8.2f Caadj=%8.2f gypL=%8.2f gyp=%6.3f wt%% sat=%.3f\n",
      nm, rr$Pathway, rr$mEq_adj[["sulfate"]], rr$mEq_adj[["calcium"]],
      rr$gypsum_content_limit, rr$gypsum_content*100, rr$saturation_gypsum_content))
}

# --- 6-4 飽和度與稀釋 ---------------------------------------------------------
for (w in c(100, 150, 200, 250, 300)) {
  rr <- fun_salt_balance("MH-08", 1.0, w, 40, 25, 1600, 30, 10, 700, 8)
  cat(sprintf("水量 %3d mL -> 飽和度 %.4f   %s\n",
              w, rr$saturation_gypsum_content, rr$ECOS_warnings))
}

# --- 6-5 注意 total_ion_content 的定義 ----------------------------------------
cat("\n校正前總量  :", round(r$total_wt * 100, 3), "wt%\n")
cat("校正後總量  :", round(r$total_wt_adj * 100, 3), "wt%  <- 這才是可溶鹽含量\n")
cat("被校正掉    :", round(r$removed_wt * 100, 3), "wt%\n")
cat("石膏        :", round(r$gypsum_content * 100, 3), "wt%\n")
cat("總鹽含量    :", round(r$total_salt_content * 100, 3), "wt%\n")
