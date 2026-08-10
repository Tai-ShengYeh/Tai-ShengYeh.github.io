# ------------------------------------------------------------------
# 注意：本檔內的路徑（/root/work、/tmp/ConSciR、/tmp/SaltsR）是產生教材時
# 那台機器的絕對路徑。要在自己電腦重跑，請先：
#   git clone --depth 1 https://github.com/BhavShah01/ConSciR.git /tmp/ConSciR
#   git clone --depth 1 https://github.com/BhavShah01/SaltsR.git  /tmp/SaltsR
# 再把本檔開頭的 /root/work 改成你放這些腳本的資料夾。
# prelude.R 沒有任何路徑相依，可以直接 source() 使用。
# ------------------------------------------------------------------
Sys.setlocale("LC_CTYPE", "C.UTF-8")
source("/root/work/prelude.R")

B <- list()
B[["b1"]] <- list(title="濕度家族：一次算完整張表", code='
# 四個典型狀態：庫房、展廳、夏季外氣、偏濕的地下室
df <- data.frame(Temp = c(20, 24, 28, 20), RH = c(50, 55, 80, 65))

df$Pws <- round(calcPws(df$Temp), 2)          # 飽和水氣壓 hPa
df$Pw  <- round(calcPw(df$Temp, df$RH), 2)    # 實際水氣壓 hPa
df$DP  <- round(calcDP(df$Temp, df$RH), 2)    # 露點 °C
df$AH  <- round(calcAH(df$Temp, df$RH), 2)    # 絕對濕度 g/m3
df$h   <- round(calcEnthalpy(df$Temp, df$RH), 1)   # 焓 kJ/kg
df$EMC <- round(calcEMC_wood(df$Temp, df$RH), 2)   # 木材平衡含水率 %
df

# 練習：把第 2 列（24 °C / 55%）降到 19 °C，AH 不變，RH 會變成多少？
Pw24 <- calcPw(24, 55)
round(Pw24 / calcPws(19) * 100, 1)
')

B[["b2"]] <- list(title="風險欄位：四個指標一起看", code='
s <- strategies
s$LIM   <- round(calcMould_Zeng(s$Temp, s$RH), 1)   # 長黴門檻 %RH
s$mould <- ifelse(s$RH > s$LIM, "有長黴條件", "安全")
s$PI    <- round(calcPI(s$Temp, s$RH), 1)           # 預期壽命（年）
s$LM_ConSciR <- round(calcLM(s$Temp, s$RH), 3)      # 套件原版
s$LM_fix     <- round(calcLM_fix(s$Temp, s$RH), 3)  # 修正版
s$EMC   <- round(calcEMC_wood(s$Temp, s$RH), 2)
s[, c("strategy","Temp","RH","LIM","mould","PI","LM_ConSciR","LM_fix","EMC")]

# 注意：D 用的是「全年平均」的 T 與 RH。平均值看起來安全，
# 但逐時資料裡有 3,670 小時超過門檻 —— 平均會把風險藏起來。
')

B[["b3"]] <- list(title="跑套件內建的 salt_test", code='
b <- fun_salt_balance("test", 1.128, 100,
                      chloride_ppm = 66.824, nitrate_ppm = 332.956, sulfate_ppm = 87.221,
                      sodium_ppm = 21.471, potassium_ppm = 211.358,
                      calcium_ppm = 75.594, magnesium_ppm = 7.582)

cat("總離子含量 total_wt      :", round(b$total_wt * 100, 3), "wt%\n")
cat("陰離子當量 e_ani         :", round(b$total_mEq_anions, 1), "mEq/kg\n")
cat("陽離子當量 e_cat         :", round(b$total_mEq_cations, 1), "mEq/kg\n")
cat("電荷差   Delta-e         :", round(b$charge_imbalance_initial, 1), "mEq/kg\n")
cat("校正路徑                 :", b$ECOS_pathway, "\n")
cat("石膏含量                 :", round(b$gypsum_content * 100, 3), "wt%\n")
cat("石膏飽和度 S             :", round(b$saturation_gypsum_content, 3), "\n")
cat("欄位 total_ion_content   :", round(b$total_ion_content * 100, 4), "wt%  <-- 注意這不是總離子含量\n")

# ECOS 輸入用的七個莫耳分率
round(c(Na = b$sodium_x, K = b$potassium_x, Mg = b$magnesium_x, Ca = b$calcium_x,
        Cl = b$chloride_x, NO3 = b$nitrate_x, SO4 = b$sulfate_x), 6)
')

B[["b4"]] <- list(title="黴菌指數：單步、累積、與修正版", code='
# 240 小時的恆定條件：25 °C / 85% RH
Temp <- rep(25, 240); RH <- rep(85, 240)

# (1) 直接把整欄丟進去 -- 這是 add_conservation_calcs() 的做法
tail(calcMould_VTT(Temp, RH), 1)

# (2) 把 M 餵回去才會累積
m <- 0
for (i in 1:240) m <- calcMould_VTT(25, 85, M_prev = m)
m

# (3) 修正 RHcrit 與衰退項後的版本，敏感度設成與 ConSciR 預設相同的 "very"
#     -> 在 25 °C / 85% 這個條件下兩個修正都不會作用（RHcrit 走 T>20 的常數 80 分支，
#        RH 也從未低於門檻），所以結果應該幾乎相同。差異要到 (4) 的低溫條件才出現。
tail(mould_VTT_fix(Temp, RH, sensitivity = "very"), 1)

# 換成本教材預設的 "sensitive"，上限 M_max 較低
tail(mould_VTT_fix(Temp, RH, sensitivity = "sensitive"), 1)

# (4) 低溫的差別：15 °C / 75% RH 在模型裡「不應該長黴」
m2 <- 0
for (i in 1:720) m2 <- calcMould_VTT(15, 75, M_prev = m2)
cat("ConSciR 30 天後 M =", round(m2, 3),
    " / 修正版 =", round(tail(mould_VTT_fix(rep(15,720), rep(75,720), sensitivity = "very"), 1), 3),
    " / 該溫度的 RHcrit =", round(RHcrit_fix(15), 1), "%\n")
')

B[["b5"]] <- list(title="八個樣品一次跑完", code='
res <- run_balance(ions)
res

# 只看需要重做萃取的樣品
subset(res, S > 1)

# 兩條路徑各幾個
table(res$pathway)
')

B[["b6"]] <- list(title="四種控制策略的年度指標", code='
s <- strategies
s$LM_fix <- round(calcLM_fix(s$Temp, s$RH), 3)
s$PI     <- round(calcPI(s$Temp, s$RH), 1)
s$EMC    <- round(calcEMC_wood(s$Temp, s$RH), 2)
s$margin <- round(calcMould_Zeng(s$Temp, s$RH) - s$RH, 1)   # 距長黴門檻
s[, c("strategy","Temp","RH","LM_fix","PI","EMC","margin")]

# 只除濕 (B) 和只降溫 (C) 哪個好？
cat("B / C 的壽命倍數比 =", round(calcLM_fix(26,50) / calcLM_fix(20,65), 3), "\n")

# 「降 1 °C」相當於「RH 減幾個百分點」？（在 24 °C / 50% 附近）
r <- calcLM_fix(23, 50) / calcLM_fix(24, 50)
f <- function(x) calcLM_fix(24, x) / calcLM_fix(24, 50) - r
cat("降 1 °C 的效果 =", round(r, 4), "倍；等效 RH =",
    round(uniroot(f, c(20, 50))$root, 1), "%（即減少",
    round(50 - uniroot(f, c(20, 50))$root, 1), "個百分點）\n")
')

B[["b7"]] <- list(title="自己驗證 1.4 節的五個問題", code='
# (1) calcLM 對不對得上 Michalski 的口訣？
tt <- c(20, 15, 25, 20); rr <- c(50, 50, 50, 25)
data.frame(Temp = tt, RH = rr,
           ConSciR = round(calcLM(tt, rr), 4),
           documented = round(calcLM_fix(tt, rr), 4))

# (2) RHcrit 的一次項符號
data.frame(Temp = c(5, 10, 15, 20),
           ConSciR = round(-0.00267*c(5,10,15,20)^3 + 0.160*c(5,10,15,20)^2 +
                             3.13*c(5,10,15,20) + 100, 2),
           published = round(RHcrit_fix(c(5, 10, 15, 20)), 2))

# (3) calcMould_VTT 整欄丟進去會不會累積？（見上一個區塊）

# (4) calcSensibleHeatRatio 的位置引數
cat("calcTotalHeating(30,22,75,55,0.5)  =", round(calcTotalHeating(30,22,75,55,0.5), 2), "\n")
cat("calcTotalHeating(30,22,0.5,75,55)  =", round(calcTotalHeating(30,22,0.5,75,55), 2), "\n")
cat("calcSensibleHeatRatio(30,22,75,55,0.5) =", calcSensibleHeatRatio(30,22,75,55,0.5), "\n")

# (5) total_ion_content 欄位到底是什麼
b <- fun_salt_balance("FT-01", 1.005, 100, 62, 4.5, 9, 37.6, 1.9, 2.2, 2.6)
cat("total_wt          =", round(b$total_wt*100, 4), "wt%\n")
cat("total_wt_adj      =", round(b$total_wt_adj*100, 4), "wt%\n")
cat("gypsum_content    =", round(b$gypsum_content*100, 4), "wt%\n")
cat("total_ion_content =", round(b$total_ion_content*100, 4), "wt%   <-- 殘差，不是總離子含量\n")

# PI 通不通過「降 5 度壽命約增為 1.8-2 倍」的檢驗？
cat("calcPI(15,50)/calcPI(20,50) =", round(calcPI(15,50)/calcPI(20,50), 3), "\n")
')

esc <- function(s) {
  s <- gsub("\\\\", "\\\\\\\\", s); s <- gsub("\"", "\\\\\"", s)
  s <- gsub("\n", "\\\\n", s); s <- gsub("\r", "", s); s <- gsub("\t", "\\\\t", s); s
}
out <- character(0)
for (id in names(B)) {
  code <- B[[id]]$code
  res <- tryCatch(paste(capture.output({
    ev <- parse(text = code)
    for (e in ev) { v <- withVisible(eval(e, envir = globalenv())); if (v$visible) print(v$value) }
  }), collapse = "\n"), error = function(e) paste("ERROR:", conditionMessage(e)))
  out <- c(out, sprintf('"%s":{"title":"%s","code":"%s","out":"%s"}',
                        id, esc(B[[id]]$title), esc(trimws(code, "left")), esc(res)))
  cat("=====", id, "=====\n", res, "\n\n", sep = "")
}
cat(paste0("{", paste(out, collapse = ","), "}"), file = "/root/work/out/rblocks.json")
