# =============================================================================
#  SaltsR 鹽害分析入門 — 單元 08：畫圖，然後看懂它
#  課程網站：https://tai-shengyeh.github.io/saltsr-course/
#
#  用法：
#    1. 把 saltsr_teaching.R 和 data/ 資料夾放在同一層目錄
#    2. 在 RStudio 開啟本檔，逐行按 Ctrl+Enter（Mac 是 Cmd+Enter）執行
# =============================================================================

source("saltsr_teaching.R")


d <- tidy_runsalt("data/SaltsRExample20C.txt", Temp_value = 20)

# --- base R 版（本課程函式）---------------------------------------------------
graph_runsalt(d, Temp_value = 20)

# --- 結晶 RH 排序：最先結晶的最危險 -------------------------------------------
ct <- crystallisation_table(d)
ct

# --- 標出台灣室內常見的濕度波動帶（55–80 %RH）---------------------------------
graph_runsalt(d, Temp_value = 20)
abline(v = c(55, 80), col = "#E36414", lty = 2, lwd = 2)
risky <- ct[ct$crystallisation_RH >= 55 & ct$crystallisation_RH <= 80, ]
cat("落在 55-80 %RH 波動帶內的鹽（會反覆結晶溶解）：\n")
print(risky)

# --- ggplot2 版（需要 install.packages("ggplot2")）-----------------------------
# library(ggplot2)
# ggplot(d, aes(RH, mol, colour = Salt)) +
#   geom_line(linewidth = 1.4, alpha = .85) +
#   labs(x = "相對濕度 (%)", y = "物質的量 (mol)",
#        title = "ECOS 模型輸出", subtitle = "20 °C") +
#   theme_classic(base_size = 14)

# --- 真正的 SaltsR 套件版（需要 pak::pak("BhavShah01/SaltsR")）------------------
# library(SaltsR)
# graph_salt_balance("data/SaltsRExample20C.txt", Temp_value = 20,
#                    add_crystal = TRUE, add_eqm = FALSE)
