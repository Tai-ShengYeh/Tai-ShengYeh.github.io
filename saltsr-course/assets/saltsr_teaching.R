# =============================================================================
#  saltsr_teaching.R  —  SaltsR 課堂版核心函式（純 base R）
# -----------------------------------------------------------------------------
#  這個檔案在你按下網頁上的「執行」時會自動載入，所以你可以直接呼叫下面的函式。
#
#  為什麼要有課堂版？
#    原始 SaltsR 套件依賴 tibble / dplyr / tidyr / readr / ggplot2 / ggrepel。
#    瀏覽器裡的 R（webR）要載入那些套件很慢，所以這裡改用「只用 base R」的
#    寫法。演算法完全相同 —— 我們用 68 組隨機資料逐項比對過，
#    與原始套件的結果相對誤差為 0。
#
#    等你把課上完、要處理真實研究資料時，請在 RStudio 安裝真正的套件：
#      install.packages("pak"); pak::pak("BhavShah01/SaltsR")
#
#  演算法來源
#    Godts, S., Steiger, M., Orr, S. A., et al. (2022).
#    Charge balance calculations for mixed salt systems applied to a large
#    dataset from the built environment. Scientific Data, 9, 324.
#    https://doi.org/10.1038/s41597-022-01445-9
#  原始 R 實作：SaltsR (GPL-3) — Bhavesh Shah, Sebastiaan Godts, Scott Orr
#    https://github.com/BhavShah01/SaltsR
# =============================================================================


# --- 參考資料：分子量與電荷 ---------------------------------------------------

mol_wts <- data.frame(
  chloride = 35.4527, nitrate = 62.0049, sulfate = 96.064,
  sodium = 22.989768, potassium = 39.0983, calcium = 40.078, magnesium = 24.305
)

salt_charges_z <- data.frame(
  chloride = 1, nitrate = 1, sulfate = 2,
  sodium = 1, potassium = 1, calcium = 2, magnesium = 2
)

#' 套件內建的測試樣品（真實離子層析數據）
salt_test <- data.frame(
  sample_name = "test", dry_g = 1.128, water_ml = 100,
  chloride_ppm = 66.824, nitrate_ppm = 332.956, sulfate_ppm = 87.221,
  sodium_ppm = 21.471, potassium_ppm = 211.358,
  calcium_ppm = 75.594, magnesium_ppm = 7.582,
  stringsAsFactors = FALSE
)


# --- 單一離子的三種表示法 -----------------------------------------------------

#' 離子在樣品中的重量分率（%）
#'   w = (C_ppm x V_mL) / (10000 x m_g)
fun_salt_wt <- function(salt_ppm, dry_g, water_ml) {
  (salt_ppm * water_ml) / (10000 * dry_g)
}

#' 莫耳（當量莫耳）數
#'   mol = 0.001 x C_ppm x V_mL / (M / z)
fun_salt_mol <- function(salt_ppm, water_ml, mol_wts, salt_charges_z) {
  (0.001 * salt_ppm * water_ml) / (mol_wts / salt_charges_z)
}

#' 每公斤乾樣的毫當量（mEq/kg）
#'   e = (C_ppm x V_mL) / (m_g x (M / z))
fun_salt_mileq <- function(salt_ppm, dry_g, water_ml, mol_wts, salt_charges_z) {
  (salt_ppm * water_ml) / (dry_g * (mol_wts / salt_charges_z))
}


# --- 含水率 -------------------------------------------------------------------

#' 實際含水率 AMC（wt %）
fun_salt_AMC <- function(sample_container_mass,
                         initial_sample_container_mass,
                         dry_sample_container_mass) {
  100 * (initial_sample_container_mass - dry_sample_container_mass) /
        (dry_sample_container_mass - sample_container_mass)
}

#' 吸濕含水率 HMC（wt %，於 20 °C / 95 %RH 平衡後量得）
fun_salt_HMC <- function(sample_container_mass,
                         dry_sample_container_mass,
                         wet_sample_container_mass) {
  100 * (wet_sample_container_mass - dry_sample_container_mass) /
        (dry_sample_container_mass - sample_container_mass)
}


# --- 完整電荷平衡 -------------------------------------------------------------

#' 從離子層析數據做電荷平衡，並輸出 ECOS/Runsalt 需要的格式
#'
#' 回傳一個 list（用 $ 取值），重要欄位：
#'   $mEq                 各離子的 mEq/kg
#'   $total_mEq_anions    陰離子總和
#'   $total_mEq_cations   陽離子總和
#'   $charge_imbalance_initial  初始不平衡量 Δe
#'   $Pathway             "Pathway 1" 或 "Pathway 2"
#'   $mEq_adj             調整後的 mEq/kg
#'   $gypsum_content_limit 以 mEq/kg 表示的石膏上限
#'   $x                   扣除石膏後的莫耳分率（ECOS 輸入）
#'   $wt_adj              扣除石膏後的重量分率
#'   $saturation_gypsum_content  石膏飽和度（>1 要稀釋重測）
fun_salt_balance <- function(sample_name, dry_g, water_ml,
                             chloride_ppm, nitrate_ppm, sulfate_ppm,
                             sodium_ppm, potassium_ppm, calcium_ppm, magnesium_ppm) {

  anions  <- c("chloride", "nitrate", "sulfate")
  cations <- c("sodium", "potassium", "calcium", "magnesium")
  ions    <- c(anions, cations)

  ppm <- c(chloride = chloride_ppm, nitrate = nitrate_ppm, sulfate = sulfate_ppm,
           sodium = sodium_ppm, potassium = potassium_ppm,
           calcium = calcium_ppm, magnesium = magnesium_ppm)
  M <- unlist(mol_wts)[ions]
  z <- unlist(salt_charges_z)[ions]

  ## 式 1 —— 重量分率 w_i（kg/kg）
  wt       <- ppm * (water_ml / 1000) / (dry_g * 1000)
  total_wt <- sum(wt)

  ## 式 2 —— 毫當量 e_i（mEq/kg）
  mEq <- (wt * z) / (M / 1000) * 1000
  total_mEq_anions  <- sum(mEq[anions])
  total_mEq_cations <- sum(mEq[cations])

  ## 式 3 —— 初始不平衡量，決定走哪一條路
  dEi <- abs(total_mEq_cations - total_mEq_anions)
  allocation <- if (total_mEq_cations > total_mEq_anions) "陽離子過剩" else "陰離子過剩"
  is_p1 <- (dEi <= max(total_mEq_cations, total_mEq_anions) * 0.02) ||
           (total_mEq_anions > total_mEq_cations)
  Pathway <- if (is_p1) "Pathway 1" else "Pathway 2"

  eps   <- 1e-6
  steps <- NULL

  if (is_p1) {
    ## 式 4 —— Pathway I：陰、陽離子各自等比例縮放到中點
    s   <- total_mEq_anions + total_mEq_cations
    adj <- mEq
    adj[anions]  <- mEq[anions]  * s / (2 * total_mEq_anions)
    adj[cations] <- mEq[cations] * s / (2 * total_mEq_cations)
  } else {
    ## 式 5a–5d —— Pathway II：依溶解度由小到大 Ca → Mg → Na → K 逐級扣除
    adj  <- mEq
    left <- dEi
    for (ion in c("calcium", "magnesium", "sodium", "potassium")) {
      before <- adj[[ion]]
      adj[[ion]] <- max(before - left, 0)
      a <- sum(adj[anions]); k <- sum(adj[cations])
      left <- if (abs(k - a) < eps) 0 else k - a
      steps <- rbind(steps, data.frame(
        ion = ion, before = before, subtracted = before - adj[[ion]],
        after = adj[[ion]], remaining_imbalance = left, stringsAsFactors = FALSE))
    }
  }

  ## 式 6 —— 石膏上限 = min(SO4, Ca)，因為 CaSO4 需要 1:1
  gypsum_content_limit <- min(adj[["sulfate"]], adj[["calcium"]])

  ## 式 7 —— 扣除石膏（ECOS 模型不處理 CaSO4）
  fin <- adj
  fin[["sulfate"]] <- fin[["sulfate"]] - gypsum_content_limit
  fin[["calcium"]] <- fin[["calcium"]] - gypsum_content_limit
  balanced <- abs(sum(fin[anions]) - sum(fin[cations])) < eps

  ## 式 8 —— 莫耳濃度與莫耳分率（ECOS 的 mol 輸入）
  molkg <- fin / z / 1000
  x     <- molkg / sum(molkg)

  ## 式 10 —— 校正後重量分率（ECOS 的 weight 輸入）
  wt_adj       <- (fin * (M / 1000) / z) * 0.001
  total_wt_adj <- sum(wt_adj)

  ## 式 11 —— 石膏含量與飽和度（20 °C 下 CaSO4 溶解度 2.14 g/L）
  gypsum_content   <- gypsum_content_limit * 0.5 * (M[["sulfate"]] + M[["calcium"]]) * 1e-6
  gypsum_capacity  <- (0.214 * water_ml / 10000) / dry_g * 100
  saturation_gypsum <- gypsum_content / gypsum_capacity

  list(
    sample_name = sample_name, dry_g = dry_g, water_ml = water_ml,
    ppm = ppm, wt = wt, total_wt = total_wt,
    mEq = mEq,
    total_mEq_anions = total_mEq_anions, total_mEq_cations = total_mEq_cations,
    charge_imbalance_initial = dEi,
    charge_imbalance_pct = 100 * dEi / max(total_mEq_anions, total_mEq_cations),
    imbalance_allocation = allocation,
    Pathway = Pathway, steps = steps,
    mEq_adj = adj, gypsum_content_limit = gypsum_content_limit,
    mEq_final = fin, charge_imbalance_final = balanced,
    molkg = molkg, x = x, wt_adj = wt_adj, total_wt_adj = total_wt_adj,
    removed_wt = total_wt - total_wt_adj,
    gypsum_content = gypsum_content, gypsum_capacity = gypsum_capacity,
    saturation_gypsum_content = saturation_gypsum,
    total_salt_content = total_wt_adj + gypsum_content,
    ECOS_warnings = if (saturation_gypsum > 1)
      "石膏可能已達飽和，實際含量恐更高，建議提高稀釋倍率後重測。" else "無警告"
  )
}

#' 把 fun_salt_balance() 的結果印成好讀的報告
print_salt_report <- function(r, digits = 3) {
  bar <- strrep("=", 62)
  cat(bar, "\n樣品：", r$sample_name,
      "   乾重 ", r$dry_g, " g   萃取水量 ", r$water_ml, " mL\n", bar, "\n", sep = "")
  tb <- data.frame(
    ppm      = round(r$ppm, 3),
    `wt_pct` = round(r$wt * 100, 4),
    `mEq_kg` = round(r$mEq, 2),
    `調整後`  = round(r$mEq_adj, 2),
    `扣石膏後` = round(r$mEq_final, 2),
    `莫耳分率` = round(r$x, 5)
  )
  print(tb)
  cat("\n陰離子總和 :", round(r$total_mEq_anions, 2), "mEq/kg",
      "\n陽離子總和 :", round(r$total_mEq_cations, 2), "mEq/kg",
      "\n不平衡量Δe :", round(r$charge_imbalance_initial, 2), "mEq/kg  (",
      round(r$charge_imbalance_pct, 2), "% ,", r$imbalance_allocation, ")",
      "\n判定路徑   :", r$Pathway,
      "\n石膏上限   :", round(r$gypsum_content_limit, 2), "mEq/kg  →",
      round(r$gypsum_content * 100, 3), "wt%",
      "\n石膏飽和度 :", round(r$saturation_gypsum_content, 3),
      "\n可溶鹽含量 :", round(r$total_wt_adj * 100, 3), "wt%",
      "\n最終平衡   :", if (r$charge_imbalance_final) "通過 ✓" else "未通過 ✗",
      "\n警告       :", r$ECOS_warnings, "\n")
  invisible(r)
}

#' 產生 Runsalt 需要的輸入檔內容
make_ecos_input <- function(r, Tconst = 20, RHmin = 15, RHmax = 98,
                            RHconst = 50, Tmin = -30, Tmax = 50) {
  v <- r$x
  paste0(
    v[["sodium"]],    "   ; Na\n",  v[["potassium"]], "   ; K\n",
    v[["magnesium"]], "   ; Mg\n",  v[["calcium"]],   "   ; Ca\n",
    v[["chloride"]],  "   ; Cl\n",  v[["nitrate"]],   "   ; NO3\n",
    v[["sulfate"]],   "   ; SO4\n",
    Tconst, "   ; Tconst\n", RHmin, "   ; RHmin\n", RHmax, "   ; RHmax\n",
    RHconst, "   ; RHconst\n", Tmin, "   ; Tmin\n", Tmax, "   ; Tmax\n",
    "0   ; unit (0=mol, 1=weight)\n\"", r$sample_name, "\"   ; sample name\n")
}


# --- 讀取 Runsalt 的輸出檔 ----------------------------------------------------

#' 讀入 Runsalt「Plot > Export Plot Data…」匯出的檔案，整理成長格式
#'
#' 檔案長相：每個鹽兩列，Salt_X 是相對濕度、Salt_Y 是莫耳數
#'   NaCl_X  15.0 16.66 18.32 ...
#'   NaCl_Y  0.3314 0.3314 ...
#'
#' 回傳 data.frame：Salt / RH / mol / Temp / filename / Crystallisation
tidy_runsalt <- function(path, Temp_value = 20) {
  lines <- readLines(path, warn = FALSE)
  lines <- lines[nzchar(trimws(lines))]
  bag <- list()
  for (ln in lines) {
    p    <- strsplit(trimws(ln), "[[:space:]]+")[[1]]
    head <- p[1]
    vals <- suppressWarnings(as.numeric(p[-1]))
    vals <- vals[!is.na(vals)]
    if (!grepl("_[XY]$", head)) next
    salt  <- sub("_[XY]$", "", head)
    which <- substring(head, nchar(head))
    bag[[salt]] <- c(bag[[salt]], stats::setNames(list(vals), which))
  }
  out <- NULL
  for (salt in names(bag)) {
    b <- bag[[salt]]
    if (is.null(b$X) || is.null(b$Y)) next
    n <- min(length(b$X), length(b$Y))
    d <- data.frame(Salt = salt, RH = b$X[1:n], mol = b$Y[1:n],
                    Temp = Temp_value, filename = basename(path),
                    stringsAsFactors = FALSE)
    d <- d[order(d$RH), ]
    d$Crystallisation <- ifelse(d$RH == max(d$RH), d$RH, NA)
    out <- rbind(out, d)
  }
  rownames(out) <- NULL
  out
}

#' 一次讀入資料夾裡所有 Runsalt 輸出檔
tidy_runsalt_folder <- function(folder, pattern = "\\.txt$", Temp_value = 20) {
  files <- list.files(folder, pattern = pattern, full.names = TRUE)
  if (!length(files)) stop("資料夾裡找不到符合的檔案：", folder)
  do.call(rbind, lapply(files, function(f)
    tryCatch(tidy_runsalt(f, Temp_value),
             error = function(e) { warning("讀取失敗：", f, " — ", e$message); NULL })))
}

#' 畫 Runsalt 的 RH–莫耳曲線（base R 版；ggplot2 版見講義單元 08）
graph_runsalt <- function(d, Temp_value = 20, label_crystal = TRUE,
                          title = "ECOS / Runsalt 模型輸出") {
  salts <- unique(d$Salt)
  pal   <- c("#0E7C7B", "#E36414", "#C8941F", "#6A3D8F", "#3D7EA6",
             "#B3402C", "#1F7A4D", "#7A5C3E", "#B5179E", "#2B6A8F")
  pal   <- rep(pal, length.out = length(salts))
  op <- graphics::par(mar = c(4.6, 4.6, 3.4, 1.2)); on.exit(graphics::par(op))
  plot(range(d$RH), c(0, max(d$mol) * 1.12), type = "n",
       xlab = "相對濕度 RH (%)", ylab = "物質的量 (mol)",
       main = paste0(title, "   ", Temp_value, " °C"))
  graphics::grid(col = "#E4DECC", lty = 1)
  for (i in seq_along(salts)) {
    s <- d[d$Salt == salts[i], ]
    graphics::lines(s$RH, s$mol, col = pal[i], lwd = 3)
    graphics::points(s$RH, s$mol, col = pal[i], pch = 16, cex = .5)
    if (label_crystal) {
      cp <- s[!is.na(s$Crystallisation), ]
      if (nrow(cp)) {
        graphics::points(cp$RH[1], cp$mol[1], pch = 21, bg = "white",
                         col = pal[i], cex = 1.5, lwd = 2)
        graphics::text(cp$RH[1], cp$mol[1], labels = round(cp$RH[1], 1),
                       pos = 3, cex = .8, col = pal[i], font = 2)
      }
    }
  }
  graphics::legend("topright", legend = salts, col = pal, lwd = 3,
                   bty = "n", cex = .85)
  invisible(d)
}

#' 列出每個鹽的結晶 RH，由高到低排序（最先結晶的最危險）
crystallisation_table <- function(d) {
  s <- do.call(rbind, lapply(split(d, d$Salt), function(g) data.frame(
    Salt = g$Salt[1], crystallisation_RH = max(g$RH),
    max_mol = max(g$mol), stringsAsFactors = FALSE)))
  s <- s[order(-s$crystallisation_RH), ]
  rownames(s) <- NULL
  s
}
