# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 04：當量濃度 mEq/kg（式 2）
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


ppm <- c(chloride=50, nitrate=30, sulfate=20,
         sodium=40, potassium=10, calcium=15, magnesium=5)
M <- c(chloride=35.4527, nitrate=62.0049, sulfate=96.064,
       sodium=22.989768, potassium=39.0983, calcium=40.078, magnesium=24.305)
z <- c(chloride=1, nitrate=1, sulfate=2,
       sodium=1, potassium=1, calcium=2, magnesium=2)
dry_g <- 1.000; water_ml <- 100

# 當量重 = M / z
round(M / z, 2)

# --- 式 2 ---------------------------------------------------------------------
mEq <- (ppm * water_ml) / (dry_g * (M / z))
round(mEq, 3)

anions  <- c("chloride","nitrate","sulfate")
cations <- c("sodium","potassium","calcium","magnesium")
cat("陰離子總和：", round(sum(mEq[anions]),  3), "mEq/kg\n")
cat("陽離子總和：", round(sum(mEq[cations]), 3), "mEq/kg\n")
cat("差額 Δe   ：", round(abs(sum(mEq[cations]) - sum(mEq[anions])), 3), "mEq/kg\n")

# 注意這個反轉：看 ppm 陰離子多，看 mEq 陽離子反而多 36 %
cat("\nppm 比較：陰", sum(ppm[anions]), " 陽", sum(ppm[cations]), "\n")
cat("mEq 比較：陰", round(sum(mEq[anions]),1), " 陽", round(sum(mEq[cations]),1), "\n")

# --- 含水率 -------------------------------------------------------------------
fun_salt_AMC(8.45, 15.619, 15.198)    # 實際含水率 wt%
fun_salt_HMC(8.45, 15.198, 15.837)    # 吸濕含水率 wt%

# --- 換你做：全部設成 100 ppm，比較誰的當量最大 --------------------------------
eq100 <- (rep(100, 7) * 100) / (1 * (M / z))
names(eq100) <- names(M)
sort(round(eq100, 1), decreasing = TRUE)
