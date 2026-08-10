# ------------------------------------------------------------------
# 注意：本檔內的路徑（/root/work、/tmp/ConSciR、/tmp/SaltsR）是產生教材時
# 那台機器的絕對路徑。要在自己電腦重跑，請先：
#   git clone --depth 1 https://github.com/BhavShah01/ConSciR.git /tmp/ConSciR
#   git clone --depth 1 https://github.com/BhavShah01/SaltsR.git  /tmp/SaltsR
# 再把本檔開頭的 /root/work 改成你放這些腳本的資料夾。
# prelude.R 沒有任何路徑相依，可以直接 source() 使用。
# ------------------------------------------------------------------
# --- Source ConSciR base-R calc functions (no package deps) ---
src <- "/tmp/ConSciR/R"
for (f in c("calcPws.R","calcPw.R","calcAH.R","calcDP.R","calcFP.R","calcAD.R","calcMR.R",
            "calcSH.R","calcHR.R","calcEnthalpy.R","calcRH_AH.R","calcRH_DP.R","calcTemp.R",
            "calcLM.R","calcPI.R","calcEMC_wood.R","calcMould_Zeng.R","calcMould_VTT.R",
            "calcCoolingPower.R","calcSensibleHeating.R","calcTotalHeating.R",
            "calcCoolingCapacity.R","calcSensibleHeatRatio.R","calcFtoC.R")) {
  source(file.path(src, f))
}
# --- SaltsR fun_salt_balance with tibble stripped (arithmetic untouched) ---
sb <- readLines("/tmp/SaltsR/R/fun_salt_balance.R")
sb <- gsub("tibble::tibble\\(", "data.frame(", sb)
sb <- sub("^(\\s*ECOS_warnings),\\s*$", "\\1", sb)
writeLines(sb, "/root/work/salt_balance_patched.R")
source("/root/work/salt_balance_patched.R")
