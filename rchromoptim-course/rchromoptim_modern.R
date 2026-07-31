#' ============================================================================
#' HPLC 分離最佳化 — 現代 R 版（tidyverse + ggplot2）
#' ----------------------------------------------------------------------------
#' 這是 Zisi, Ch., Pappa-Louisi, A., & Nikitas, P. (2020) 所提方法的重新實作：
#'   Separation optimization in HPLC analysis implemented in R programming
#'   language. Journal of Chromatography A, 1617, 460823.
#'
#' 原始 RChromOptim 套件為 2019 年的 base R 程式，採互動式設計
#' （choose.files()、locator() 滑鼠點選），僅能在 Windows 上手動執行。
#' 本檔以 R 4.1+ 語法與 tidyverse 重寫為「純函式 + 可重現腳本」：
#'   - 檔案路徑用參數傳入，跨平台、可自動化、可寫進 CI
#'   - 函式回傳資料（tibble），不以列印或畫圖為副作用
#'   - 以 ggplot2 取代 base graphics
#'   - 向量化，無巢狀重複的輔助函式
#'
#' 執行環境：R 4.6.1、tidyverse 2.0.0、ggplot2 4.0.3
#' 授權：本重新實作為教學用途之獨立程式碼。
#'       論文本文與其補充材料之著作權屬原出版者所有，未隨附於此。
#' ============================================================================

library(tidyverse)
library(patchwork)

# ---- 常數：管柱與峰形 -------------------------------------------------------
# t0 為管柱死時間（分鐘）。峰形參數採論文 i-optim 工作表中模型 1 區塊的代表值：
#   峰高   h = h0 + h1 * tR
#   峰寬參數 s = s0 + s1 * tR，基底峰寬 w = 4s/sqrt(2)（與 fitshape 定義相同）
T0    <- 1.4
SHAPE <- list(h0 = 0.138, h1 = -0.0038, s0 = 0.013, s1 = 0.0105)

# ---- 範例資料 ---------------------------------------------------------------
# 9 個溶質在 4 種有機修飾劑比例下的滯留時間（分鐘）。
# 資料出處：Zisi et al. (2020) 補充材料 Data.xlsx，i-ret.fit 工作表。
# 管柱 Kinetex 2.6 um XB-C18 150 x 4.6 mm；移動相 乙腈/水 pH 5.7；t0 = 1.4 min。
# 此處僅內嵌少量事實性數據以利教學重現，原始檔案未隨附。
retention_demo <- function() {
  tibble::tribble(
    ~f,   ~A1,   ~A2,   ~A3,   ~A4,   ~A5,    ~A6,    ~A7,    ~A8,    ~A9,
    0.40, 3.735, 4.671, 6.646, 7.662, 8.498, 10.760, 11.090, 15.990, 19.000,
    0.45, 3.000, 3.650, 5.200, 5.600, 5.900,  6.850,  8.000, 10.380, 12.690,
    0.50, 2.537, 3.010, 4.208, 4.349, 4.430,  4.842,  6.051,  7.239,  8.921,
    0.60, 2.013, 2.265, 3.000, 2.940, 2.910,  3.061,  3.866,  4.198,  5.085
  )
}

#' 讀入 tab 分隔的滯留資料並整理成長格式
#'
#' @param path 檔案路徑；留白則使用內建範例資料
#' @return tibble，欄位為 solute / f / tR
read_retention <- function(path = NULL) {
  wide <- if (is.null(path)) retention_demo() else readr::read_tsv(path, show_col_types = FALSE)
  # 原始檔的標題常帶有多餘空白（例如 "  t (min)  "），先清乾淨
  names(wide) <- stringr::str_trim(names(wide))
  wide |>
    tidyr::pivot_longer(-1, names_to = "solute", values_to = "tR") |>
    dplyr::rename(f = 1) |>
    dplyr::mutate(solute = forcats::fct_inorder(solute))
}

# ---- 模型擬合 ---------------------------------------------------------------

#' 以模型 1 擬合滯留資料：ln k = c0 - c1 * f
#'
#' 對每個溶質先算 k = (tR - t0)/t0，取對數後對 f 做線性迴歸。
#' 使用 nest + map + broom，取代原程式的迴圈。
#'
#' @param data read_retention() 的輸出
#' @param t0 死時間
#' @return tibble：solute, c0, c1, r_squared, sigma, p_c1, n
fit_model1 <- function(data, t0 = T0) {
  stopifnot(all(data$tR > t0))
  data |>
    dplyr::mutate(lnk = log((tR - t0) / t0)) |>
    tidyr::nest(.by = solute) |>
    dplyr::mutate(
      fit   = purrr::map(data, \(d) stats::lm(lnk ~ f, data = d)),
      tidy  = purrr::map(fit, broom::tidy),
      glance = purrr::map(fit, broom::glance)
    ) |>
    dplyr::mutate(
      c0   = purrr::map_dbl(tidy, \(x) x$estimate[x$term == "(Intercept)"]),
      c1   = purrr::map_dbl(tidy, \(x) -x$estimate[x$term == "f"]),  # 斜率取負
      p_c1 = purrr::map_dbl(tidy, \(x) x$p.value[x$term == "f"]),
      r_squared = purrr::map_dbl(glance, "r.squared"),
      sigma     = purrr::map_dbl(glance, "sigma"),
      n         = purrr::map_int(data, nrow),
      .keep = "unused"
    ) |>
    dplyr::select(solute, c0, c1, r_squared, sigma, p_c1, n)
}

# ---- 峰與解析度 -------------------------------------------------------------

peak_sigma  <- function(tR, shape = SHAPE) shape$s0 + shape$s1 * tR
peak_height <- function(tR, shape = SHAPE) pmax(0.014, shape$h0 + shape$h1 * tR)
peak_width  <- function(tR, shape = SHAPE) 4 * peak_sigma(tR, shape) / sqrt(2)

#' 由模型 1 參數預測恆溶劑條件下的滯留時間
predict_isocratic <- function(params, f, t0 = T0) {
  params |>
    dplyr::mutate(
      f  = f,
      k  = exp(c0 - c1 * f),
      tR = t0 * (1 + k),
      w  = peak_width(tR),
      s  = peak_sigma(tR),
      h  = peak_height(tR)
    ) |>
    dplyr::arrange(tR)
}

#' 相鄰峰對的解析度，並回報最小值（least resolved pair）
#'
#' Rs = 2 * (tR2 - tR1) / (w1 + w2)
resolution_table <- function(peaks) {
  peaks |>
    dplyr::arrange(tR) |>
    dplyr::mutate(
      pair  = paste(solute, dplyr::lead(solute), sep = "/"),
      Rs    = 2 * (dplyr::lead(tR) - tR) / (w + dplyr::lead(w))
    ) |>
    dplyr::filter(!is.na(Rs)) |>
    dplyr::select(pair, Rs)
}

min_resolution <- function(peaks) {
  rt <- resolution_table(peaks)
  if (nrow(rt) == 0) return(tibble::tibble(Rs = NA_real_, pair = NA_character_))
  dplyr::slice_min(rt, Rs, n = 1, with_ties = FALSE)
}

#' 模擬層析圖：把每個高斯峰加總
#'
#' y = sum_j h_j * exp(-((t - tR_j)/s_j)^2)
simulate_chromatogram <- function(peaks, t_max = NULL, dt = 0.002) {
  t_max <- t_max %||% (max(peaks$tR) * 1.15)
  tibble::tibble(t = seq(0, t_max, by = dt)) |>
    dplyr::mutate(
      signal = purrr::map_dbl(t, \(tt) sum(peaks$h * exp(-((tt - peaks$tR) / peaks$s)^2)))
    )
}

# ---- 最佳化 -----------------------------------------------------------------

#' 掃描 f，找出時間預算內解析度最好的條件（對應原套件的 iopt）
#'
#' @param params fit_model1() 的輸出
#' @param f_range 搜尋範圍
#' @param df 步長
#' @param t_max 可接受的最長滯留時間（時間預算）
#' @return list(scan = 掃描表, best = 最佳列)
#' 掃描時把所有條件一次算成矩陣
#'
#' tR 是一個 (溶質 x f) 矩陣，一行算完；解析度用矩陣位移相減求得。
#' 這比「對每個 f 各建一個資料框」快 2-3 個數量級，
#' 在 df 變小或要做二維掃描（f x pH、tG x f）時差別非常明顯。
scan_isocratic <- function(params, f, t0 = T0, shape = SHAPE) {
  tR  <- t0 * (1 + exp(params$c0 - outer(params$c1, f)))   # n_solute x n_f
  ord <- apply(tR, 2, order)                               # 每欄的沖提順序
  S   <- apply(tR, 2, sort)
  W   <- 4 * (shape$s0 + shape$s1 * S) / sqrt(2)
  n   <- nrow(S)
  Rs  <- 2 * (S[-1, , drop = FALSE] - S[-n, , drop = FALSE]) /
             (W[-1, , drop = FALSE] + W[-n, , drop = FALSE])
  i   <- apply(Rs, 2, which.min)                           # 最難分的那一對
  sol <- as.character(params$solute)
  tibble::tibble(
    f      = f,
    Rs     = Rs[cbind(i, seq_along(f))],
    pair   = paste(sol[ord[cbind(i, seq_along(f))]],
                   sol[ord[cbind(i + 1L, seq_along(f))]], sep = "/"),
    tR_max = S[n, ]
  )
}

optimise_isocratic <- function(params, f_range = c(0.30, 0.60), df = 0.005,
                               t_max = 20, t0 = T0) {
  scan <- scan_isocratic(params, seq(f_range[1], f_range[2], by = df), t0) |>
    dplyr::mutate(feasible = tR_max <= t_max)
  best <- scan |>
    dplyr::filter(feasible) |>
    dplyr::slice_max(Rs, n = 1, with_ties = FALSE)
  list(scan = scan, best = best)
}

# ---- 梯度沖提 ---------------------------------------------------------------

#' 數值求解基本梯度方程式 integral(dt / (t0 * k(t))) = 1
#'
#' phi(t) 為溶質在管柱入口看到的組成，已含延遲時間 tD。
#' 回傳滯留時間，以及沖提瞬間的 k（決定梯度峰寬，線性溶劑強度理論）。
#' 當 f_start == f_end 時本式自動退化為恆溶劑解析解 tR = t0*(1+k)。
predict_gradient_one <- function(c0, c1, f_start, f_end, tG, tD, t0 = T0,
                                 dt = 0.002, t_limit = 400) {
  tt   <- seq(0, t_limit, by = dt)
  phi  <- dplyr::case_when(
    tt <= tD              ~ f_start,
    (tt - tD) / tG >= 1   ~ f_end,
    TRUE                  ~ f_start + (f_end - f_start) * (tt - tD) / tG
  )
  k    <- exp(c0 - c1 * phi)
  prog <- cumsum(dt / (t0 * k))          # 已走完的管柱比例
  i    <- which(prog >= 1)[1]
  if (is.na(i)) return(tibble::tibble(tR = NA_real_, k_elute = NA_real_))
  # 第 i 步涵蓋時間區間 [tt[i], tt[i] + dt]（k 在區間起點取值），
  # prog[i-1] 是進入這一步之前已走完的比例；在區間內線性內插求沖提時刻。
  before <- if (i > 1) prog[i - 1] else 0
  frac   <- (1 - before) / (prog[i] - before)
  te     <- tt[i] + frac * dt
  tibble::tibble(tR = te + t0, k_elute = k[i])
}

#' 一次算完所有溶質的梯度滯留時間
#'
#' 三個效能重點：
#'  1. 梯度曲線 phi(t) 對所有溶質都一樣，只算一次（原本每個溶質重算一遍）
#'  2. k 做成 (溶質 x 時間) 矩陣，cumsum 以 vapply 逐列向量化
#'  3. 時間格點上限由 f_end 的恆溶劑滯留時間估出，不再固定配置 400 分鐘
#' 數值結果與逐一呼叫 predict_gradient_one() 完全相同。
predict_gradient <- function(params, f_start, f_end, tG, tD = 0.7, t0 = T0,
                             dt = 0.002, shape = SHAPE) {
  n     <- nrow(params)
  limit <- max(4, 3 * max(t0 * (1 + exp(params$c0 - params$c1 * f_end))) + tD + tG)
  repeat {
    tt   <- seq(0, limit, by = dt)
    phi  <- pmin(pmax((tt - tD) / tG, 0), 1) * (f_end - f_start) + f_start
    K    <- exp(params$c0 - outer(params$c1, phi))                 # n x T
    prog <- vapply(seq_len(n), \(i) cumsum(dt / (t0 * K[i, ])), numeric(length(tt)))  # T x n
    if (all(prog[nrow(prog), ] >= 1) || limit > 1000) break
    limit <- limit * 3
  }
  idx    <- apply(prog >= 1, 2, \(v) which(v)[1])
  before <- vapply(seq_len(n), \(i) if (idx[i] > 1) prog[idx[i] - 1, i] else 0, numeric(1))
  cur    <- vapply(seq_len(n), \(i) prog[idx[i], i], numeric(1))
  ke     <- vapply(seq_len(n), \(i) K[i, idx[i]], numeric(1))
  te     <- tt[idx] + dt * (1 - before) / (cur - before)
  t_equiv <- t0 * (1 + ke)          # 峰寬由沖提瞬間的 k 決定（LSS 理論）
  params |>
    dplyr::mutate(tR = te + t0, k_elute = ke,
                  s = peak_sigma(t_equiv),
                  w = peak_width(t_equiv),
                  h = peak_height(t_equiv)) |>
    dplyr::arrange(tR)
}

# ---- 繪圖（ggplot2） --------------------------------------------------------

theme_chrom <- function(base_size = 12) {
  ggplot2::theme_minimal(base_size = base_size) +
    ggplot2::theme(
      panel.grid.minor = ggplot2::element_blank(),
      plot.title       = ggplot2::element_text(face = "bold"),
      plot.subtitle    = ggplot2::element_text(colour = "grey35"),
      legend.position  = "bottom"
    )
}

#' 模型 1 的診斷圖：ln k 對 f，實測點 + 擬合直線
plot_model1 <- function(data, params, t0 = T0) {
  pts <- dplyr::mutate(data, lnk = log((tR - t0) / t0))
  lines <- tidyr::expand_grid(
    params |> dplyr::select(solute, c0, c1),
    f = seq(min(pts$f) - 0.02, max(pts$f) + 0.02, length.out = 100)
  ) |>
    dplyr::mutate(lnk = c0 - c1 * f)

  ggplot2::ggplot(pts, ggplot2::aes(f, lnk, colour = solute)) +
    ggplot2::geom_line(data = lines, linewidth = 0.7) +
    ggplot2::geom_point(size = 2) +
    ggplot2::labs(
      title    = "模型 1：ln k = c0 - c1 · f",
      subtitle = "點為實測值，線為線性迴歸擬合",
      x = "有機修飾劑比例  f", y = "ln k", colour = NULL
    ) +
    theme_chrom()
}

#' 模擬層析圖
plot_chromatogram <- function(peaks, title = NULL, t_max = NULL, label = TRUE) {
  chrom <- simulate_chromatogram(peaks, t_max)
  worst <- min_resolution(peaks)
  p <- ggplot2::ggplot(chrom, ggplot2::aes(t, signal)) +
    ggplot2::geom_line(colour = "#0d7377", linewidth = 0.6) +
    ggplot2::labs(
      title    = title %||% "模擬層析圖",
      subtitle = sprintf("最小 Rs = %.3f (%s)，最後出峰 %.2f min",
                         worst$Rs, worst$pair, max(peaks$tR)),
      x = "時間 t / min", y = "訊號"
    ) +
    theme_chrom()
  if (label) {
    p <- p + ggplot2::geom_text(
      data = peaks, ggplot2::aes(x = tR, y = h, label = solute),
      inherit.aes = FALSE, vjust = -0.6, size = 3, colour = "grey30"
    ) + ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0.02, 0.12)))
  }
  p
}

#' 最佳化掃描圖：Rs 與 tR_max 對 f（對應論文 Fig. 7）
plot_optimisation <- function(opt, rs_target = 1.5) {
  best <- opt$best
  scale_factor <- max(opt$scan$Rs, na.rm = TRUE) / max(opt$scan$tR_max, na.rm = TRUE)
  ggplot2::ggplot(opt$scan, ggplot2::aes(f)) +
    ggplot2::geom_hline(yintercept = rs_target, linetype = "dashed", colour = "#2e7d4f") +
    ggplot2::geom_line(ggplot2::aes(y = Rs, colour = "最小 Rs"), linewidth = 0.8) +
    ggplot2::geom_line(ggplot2::aes(y = tR_max * scale_factor, colour = "tR_max"),
                       linewidth = 0.8) +
    ggplot2::geom_point(data = best, ggplot2::aes(y = Rs), size = 3, colour = "#2e7d4f") +
    ggplot2::scale_y_continuous(
      name = "最小 Rs",
      sec.axis = ggplot2::sec_axis(~ . / scale_factor, name = "tR_max / min")
    ) +
    ggplot2::scale_colour_manual(values = c("最小 Rs" = "#0d7377", "tR_max" = "#c8632b")) +
    ggplot2::labs(
      title = "掃描最佳化（對應 iopt）",
      subtitle = sprintf("最佳 f = %.3f，Rs = %.3f，tR_max = %.2f min",
                         best$f, best$Rs, best$tR_max),
      x = "有機修飾劑比例  f", colour = NULL
    ) +
    theme_chrom()
}

# ---- 示範流程 ---------------------------------------------------------------
if (sys.nframe() == 0) {
  data   <- read_retention()
  params <- fit_model1(data)

  cat("== 模型 1 擬合結果 ==\n")
  print(params |> dplyr::mutate(dplyr::across(where(is.numeric), \(x) round(x, 4))), n = Inf)
  cat(sprintf("\nc0 範圍 %.4f - %.4f\nc1 範圍 %.4f - %.4f\n",
              min(params$c0), max(params$c0), min(params$c1), max(params$c1)))
  cat("論文 i-optim 工作表公布值：c0 3.1404-5.6030，c1 5.9113-8.5366\n")

  opt <- optimise_isocratic(params, t_max = 20)
  cat(sprintf("\n== 最佳化 (t_max = 20) ==\n f = %.3f  Rs = %.3f  tR_max = %.2f  最難分 = %s\n",
              opt$best$f, opt$best$Rs, opt$best$tR_max, opt$best$pair))

  for (tm in c(15, 10)) {
    b <- optimise_isocratic(params, t_max = tm)$best
    cat(sprintf(" t_max = %2d -> f = %.3f  Rs = %.3f\n", tm, b$f, b$Rs))
  }

  # 數值精度：網頁模擬器用的是論文公布的四位小數參數，此處用 lm() 的全精度值。
  # 兩者是同一組擬合，差別只在參數取到幾位小數。
  rounded <- dplyr::mutate(params, c0 = round(c0, 4), c1 = round(c1, 4))
  cat(sprintf("\n== 參數精度的影響 (f = 0.410) ==\n 全精度   Rs = %.4f\n 四位小數 Rs = %.4f\n",
              min_resolution(predict_isocratic(params, 0.410))$Rs,
              min_resolution(predict_isocratic(rounded, 0.410))$Rs))

  g <- predict_gradient(params, 0.35, 0.70, tG = 11)
  wg <- min_resolution(g)
  cat(sprintf("\n== 梯度 (0.35->0.70, tG=11, tD=0.7) ==\n Rs = %.3f (%s)  tR_max = %.2f\n",
              wg$Rs, wg$pair, max(g$tR)))

  # 正確性檢查：起訖組成相同時，梯度數值解必須退化成恆溶劑解析解
  iso  <- predict_isocratic(params, 0.45)
  degen <- predict_gradient(params, 0.45, 0.45, tG = 15)
  stopifnot(all(abs(sort(iso$tR) - sort(degen$tR)) < 1e-4))
  cat(" 檢查通過：f_start == f_end 時梯度解退化為恆溶劑解（誤差 < 1e-4 min）\n")

  best_peaks <- predict_isocratic(params, opt$best$f)
  p <- (plot_model1(data, params) | plot_optimisation(opt)) /
       plot_chromatogram(best_peaks, sprintf("最佳條件 f = %.3f", opt$best$f))
  ggplot2::ggsave("rchromoptim_modern_demo.png", p, width = 12, height = 8, dpi = 130)
  cat("\n圖已存成 rchromoptim_modern_demo.png\n")
}
