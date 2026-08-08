# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 05：電荷平衡與兩條路徑（式 3–5）
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


M <- c(chloride=35.4527, nitrate=62.0049, sulfate=96.064,
       sodium=22.989768, potassium=39.0983, calcium=40.078, magnesium=24.305)
z <- c(chloride=1, nitrate=1, sulfate=2,
       sodium=1, potassium=1, calcium=2, magnesium=2)
an <- c("chloride","nitrate","sulfate")
ct <- c("sodium","potassium","calcium","magnesium")

to_mEq <- function(ppm, dry_g, water_ml) (ppm * water_ml) / (dry_g * (M / z))

# =============================================================================
#  Pathway 1 —— 等比例調整（MH-04，陰離子過剩）
# =============================================================================
ppm4 <- c(chloride=120, nitrate=80, sulfate=45,
          sodium=60, potassium=15, calcium=25, magnesium=10)
mEq <- to_mEq(ppm4, 1.0, 100)
Sa <- sum(mEq[an]); Sc <- sum(mEq[ct])
cat("陰離子", round(Sa,2), " 陽離子", round(Sc,2),
    " Δe =", round(abs(Sc-Sa),2),
    " 佔比", round(100*abs(Sc-Sa)/max(Sa,Sc),2), "%\n")

adj <- mEq
adj[an] <- mEq[an] * (Sa+Sc) / (2*Sa)
adj[ct] <- mEq[ct] * (Sa+Sc) / (2*Sc)
round(rbind(原始=mEq, 調整後=adj), 2)
cat("調整後：陰", round(sum(adj[an]),4), " 陽", round(sum(adj[ct]),4), "\n\n")

# =============================================================================
#  Pathway 2 —— 逐級扣除 Ca → Mg → Na → K（MH-01）
# =============================================================================
ppm1 <- c(chloride=50, nitrate=30, sulfate=20,
          sodium=40, potassium=10, calcium=15, magnesium=5)
mEq  <- to_mEq(ppm1, 1.0, 100)
adj  <- mEq
left <- abs(sum(mEq[ct]) - sum(mEq[an]))
cat("待扣除的過剩陽離子 Δe =", round(left, 3), "mEq/kg\n\n")

for (ion in c("calcium","magnesium","sodium","potassium")) {
  before <- adj[[ion]]
  adj[[ion]] <- max(before - left, 0)
  used <- before - adj[[ion]]
  left <- max(sum(adj[ct]) - sum(adj[an]), 0)
  cat(sprintf("%-10s %8.3f  - %8.3f  ->  %8.3f   還剩 %8.3f\n",
              ion, before, used, adj[[ion]], left))
}
round(rbind(原始=mEq, 校正後=adj), 3)

# =============================================================================
#  一次做完
# =============================================================================
r <- fun_salt_balance("MH-01", 1.000, 100, 50, 30, 20, 40, 10, 15, 5)
print_salt_report(r)
print(round(r$steps[, 2:5], 3))

# --- 換你做：把硝酸根往上調，找出路徑翻轉的臨界值 -------------------------------
for (no3 in c(30, 60, 90, 120, 150, 180)) {
  rr <- fun_salt_balance("test", 1.0, 100, 50, no3, 20, 40, 10, 15, 5)
  cat(sprintf("NO3 = %3d ppm  ->  Δe = %7.2f (%5.2f%%)  %s  鈣 = %.2f\n",
      no3, rr$charge_imbalance_initial, rr$charge_imbalance_pct,
      rr$Pathway, rr$mEq_adj[["calcium"]]))
}
