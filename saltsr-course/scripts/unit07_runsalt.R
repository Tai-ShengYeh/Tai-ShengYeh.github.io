# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 07：讀進 Runsalt 的輸出檔
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


# --- 7-3 一行讀完 -------------------------------------------------------------
d <- tidy_runsalt("data/SaltsRExample20C.txt", Temp_value = 20)
str(d)
head(d, 8)
cat("共", nrow(d), "列，", length(unique(d$Salt)), "個鹽相\n")
unique(d$Salt)

# --- 7-3 拆開來看它在做什麼 ---------------------------------------------------
lines <- readLines("data/SaltsRExample20C.txt")
lines <- lines[nzchar(trimws(lines))]
length(lines)
lines[1]

p <- strsplit(trimws(lines[1]), "[[:space:]]+")[[1]]
p[1]                                    # 標頭
salt  <- sub("_[XY]$", "", p[1]); salt  # 鹽名
which <- substring(p[1], nchar(p[1])); which
vals  <- as.numeric(p[-1]); head(vals, 5)

# --- 7-4 整個資料夾 -----------------------------------------------------------
# all <- tidy_runsalt_folder("runsalt_outputs/", Temp_value = 20)
# table(all$filename)

# --- 換你做：找出每個鹽的結晶 RH ----------------------------------------------
tapply(d$RH, d$Salt, max)
crystallisation_table(d)
