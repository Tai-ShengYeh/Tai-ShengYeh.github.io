# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 03：從 ppm 到重量百分比（式 1）
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


# --- 3-3 單一離子 -------------------------------------------------------------
cl_ppm <- 50; water_ml <- 100; dry_g <- 1.000
cl_wt_pct <- (cl_ppm * water_ml) / (10000 * dry_g)
cl_wt_pct
fun_salt_wt(cl_ppm, dry_g, water_ml)      # 課程函式，結果相同

# --- 七個離子一次算完（向量化）------------------------------------------------
ppm <- c(chloride=50, nitrate=30, sulfate=20,
         sodium=40, potassium=10, calcium=15, magnesium=5)
wt_pct <- fun_salt_wt(ppm, dry_g, water_ml)
round(wt_pct, 4)
cat("總可溶鹽含量：", round(sum(wt_pct), 3), "wt%\n")

# --- 3-4 自己寫函式 -----------------------------------------------------------
my_wt <- function(ppm, dry_g, water_ml) (ppm * water_ml) / (10000 * dry_g)
my_wt(50, 1.0, 100)
my_wt(c(50, 30, 20), 1.0, 100)

my_wt2 <- function(ppm, dry_g, water_ml = 100) (ppm * water_ml) / (10000 * dry_g)
my_wt2(50, 1.0)
my_wt2(50, 1.0, water_ml = 250)

# --- 陷阱：分率 vs 百分比，差 100 倍 -------------------------------------------
frac <- (50 * (100/1000)) / (1.0 * 1000)   # fun_salt_balance() 內部用的形式
pct  <- (50 * 100) / (10000 * 1.0)         # fun_salt_wt() 用的形式
c(分率 = frac, 百分比 = pct, 倍數 = pct / frac)

# --- 換你做：MH-05 -------------------------------------------------------------
fun_salt_wt(66.824, 0.980, 100)
