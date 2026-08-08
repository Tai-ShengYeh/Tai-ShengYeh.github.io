# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 02：向量、資料框與管線
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


# --- 2-1 向量 -----------------------------------------------------------------
ppm <- c(50, 30, 20, 40, 10, 15, 5)
names(ppm) <- c("chloride","nitrate","sulfate",
                "sodium","potassium","calcium","magnesium")
ppm
ppm["calcium"]
ppm[1]
ppm[c(1,2,3)]
ppm * 2
ppm / 1000

M <- c(chloride=35.4527, nitrate=62.0049, sulfate=96.064,
       sodium=22.989768, potassium=39.0983, calcium=40.078, magnesium=24.305)
round(ppm / M, 4)

sum(ppm)
sum(ppm[c("chloride","nitrate","sulfate")])
mean(ppm); length(ppm)

# --- 2-2 資料框 ---------------------------------------------------------------
samples <- read.csv("data/salt_samples.csv")
samples
str(samples)
nrow(samples); names(samples)

samples$chloride_ppm
samples[1, ]
samples[, "chloride_ppm"]
samples[3, "nitrate_ppm"]
samples[samples$chloride_ppm > 60, c("sample_name","chloride_ppm")]

samples$cl_wt_pct <- samples$chloride_ppm * samples$water_ml /
                     (10000 * samples$dry_g)
samples[, c("sample_name","chloride_ppm","cl_wt_pct")]

# --- 2-3 管線 -----------------------------------------------------------------
round(sqrt(sum(ppm)), 3)
ppm |> sum() |> sqrt() |> round(3)
c(3.7, 1.2, 9.9) |> sort() |> rev()

# --- 換你做：找出最髒的樣品（答案 MH-08）---------------------------------------
ions <- c("chloride_ppm","nitrate_ppm","sulfate_ppm",
          "sodium_ppm","potassium_ppm","calcium_ppm","magnesium_ppm")
samples$total_ppm <- rowSums(samples[, ions])
samples[which.max(samples$total_ppm), c("sample_name","location","total_ppm")]
