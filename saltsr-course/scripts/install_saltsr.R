# =============================================================================
#  在自己的電腦安裝真正的 SaltsR 套件
# =============================================================================
#  前置作業
#    1. 安裝 R        https://cran.r-project.org/
#    2. 安裝 RStudio  https://posit.co/download/rstudio-desktop/
#    3. Windows 使用者若安裝失敗，請先裝 Rtools
#                     https://cran.r-project.org/bin/windows/Rtools/
# =============================================================================

# --- 方法 1（官方建議）--------------------------------------------------------
install.packages("pak")
pak::pak("BhavShah01/SaltsR")

# --- 方法 2（方法 1 失敗時）--------------------------------------------------
# install.packages("remotes")
# remotes::install_github("BhavShah01/SaltsR")

# --- 驗證 ---------------------------------------------------------------------
library(SaltsR)

# 內建測試資料
salt_test
mol_wts
salt_charges_z

# 完整電荷平衡（和課程網站的結果應完全相同）
fun_salt_balance(
  sample_name = "Example", dry_g = 1, water_ml = 100,
  chloride_ppm = 50, nitrate_ppm = 30, sulfate_ppm = 20,
  sodium_ppm = 40, potassium_ppm = 10,
  calcium_ppm = 15, magnesium_ppm = 5
) |> dplyr::glimpse()

# 互動式 Shiny 應用程式
# runSaltsR_app()

# --- 讀取並繪製 Runsalt 輸出 --------------------------------------------------
# d <- tidyRunsalt("SaltsRExample20C.txt", Temp_value = 20)
# head(d)
# graph_salt_balance("SaltsRExample20C.txt", Temp_value = 20)

# --- 官方資源 -----------------------------------------------------------------
#  套件文件   https://bhavshah01.github.io/SaltsR/
#  線上版     https://oceanonline.shinyapps.io/SaltsRApp/
#  最新演算法 https://predict.kikirpa.be/index.php/tools/
#             moisture-and-salt-sample-data-analysis-tool/
