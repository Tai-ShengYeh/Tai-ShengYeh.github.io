# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 09：批次處理與綜合實作
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


samples <- read.csv("data/salt_samples.csv")

# --- 9-1 for 迴圈 -------------------------------------------------------------
for (i in 1:nrow(samples)) cat(samples$sample_name[i], "-", samples$location[i], "\n")

out <- NULL
for (i in 1:nrow(samples)) {
  s <- samples[i, ]
  r <- fun_salt_balance(s$sample_name, s$dry_g, s$water_ml,
                        s$chloride_ppm, s$nitrate_ppm, s$sulfate_ppm,
                        s$sodium_ppm, s$potassium_ppm,
                        s$calcium_ppm, s$magnesium_ppm)
  out <- rbind(out, data.frame(
    樣品 = r$sample_name, 位置 = s$location,
    總鹽_wt = round(r$total_wt * 100, 3),
    陰離子 = round(r$total_mEq_anions, 1),
    陽離子 = round(r$total_mEq_cations, 1),
    Δe = round(r$charge_imbalance_initial, 1),
    Δe_pct = round(r$charge_imbalance_pct, 1),
    路徑 = r$Pathway,
    石膏_wt = round(r$gypsum_content * 100, 3),
    飽和度 = round(r$saturation_gypsum_content, 3),
    可溶鹽_wt = round(r$total_wt_adj * 100, 3),
    stringsAsFactors = FALSE))
}
out

# --- 9-2 lapply 版本 ----------------------------------------------------------
res <- lapply(1:nrow(samples), function(i) { s <- samples[i, ]
  fun_salt_balance(s$sample_name, s$dry_g, s$water_ml, s$chloride_ppm,
                   s$nitrate_ppm, s$sulfate_ppm, s$sodium_ppm,
                   s$potassium_ppm, s$calcium_ppm, s$magnesium_ppm) })
sapply(res, function(r) r$Pathway)
round(sapply(res, function(r) r$charge_imbalance_pct), 2)

# --- 9-3 視覺化 ---------------------------------------------------------------
nm <- sapply(res, function(r) r$sample_name)
an <- sapply(res, function(r) r$total_mEq_anions)
ct <- sapply(res, function(r) r$total_mEq_cations)
pw <- sapply(res, function(r) r$Pathway)

par(mar = c(5, 5, 4, 2))
bp <- barplot(rbind(陰離子 = an, 陽離子 = ct), beside = TRUE,
        names.arg = nm, las = 2, col = c("#E36414", "#3D7EA6"), border = NA,
        ylab = "mEq/kg", main = "各樣品的陰陽離子當量",
        legend.text = TRUE, args.legend = list(x = "topleft", bty = "n"))
text(colMeans(bp), pmax(an, ct) * 1.06,
     labels = sub("Pathway ", "P", pw), cex = .8, font = 2)

# --- 9-4 匯出 -----------------------------------------------------------------
tab <- do.call(rbind, lapply(res, function(r) data.frame(
  sample = r$sample_name, pathway = r$Pathway,
  total_wt_pct = r$total_wt * 100, soluble_wt_pct = r$total_wt_adj * 100,
  gypsum_wt_pct = r$gypsum_content * 100, saturation = r$saturation_gypsum_content,
  x_Na = r$x[["sodium"]], x_K = r$x[["potassium"]], x_Mg = r$x[["magnesium"]],
  x_Ca = r$x[["calcium"]], x_Cl = r$x[["chloride"]],
  x_NO3 = r$x[["nitrate"]], x_SO4 = r$x[["sulfate"]])))
write.csv(tab, "salt_results.csv", row.names = FALSE)
round(tab[, 3:6], 3)

# --- 9-5 混合型態判讀（用校正「前」的組成）------------------------------------
for (r in res) {
  frac <- r$mEq / sum(r$mEq)
  top  <- names(sort(frac, decreasing = TRUE))[1:3]
  cat(sprintf("%-6s 校正前主導離子：%s\n", r$sample_name, paste(top, collapse = " > ")))
}
