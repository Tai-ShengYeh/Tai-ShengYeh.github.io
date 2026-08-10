# ------------------------------------------------------------------
# 注意：本檔內的路徑（/root/work、/tmp/ConSciR、/tmp/SaltsR）是產生教材時
# 那台機器的絕對路徑。要在自己電腦重跑，請先：
#   git clone --depth 1 https://github.com/BhavShah01/ConSciR.git /tmp/ConSciR
#   git clone --depth 1 https://github.com/BhavShah01/SaltsR.git  /tmp/SaltsR
# 再把本檔開頭的 /root/work 改成你放這些腳本的資料夾。
# prelude.R 沒有任何路徑相依，可以直接 source() 使用。
# ------------------------------------------------------------------
source("/root/work/funs.R")
outdir <- "/root/work/out"; dir.create(outdir, showWarnings = FALSE)
set.seed(20260810)

## ---------------------------------------------------------------
## 0. Corrected / teaching versions of two ConSciR functions
## ---------------------------------------------------------------
# calcLM as documented (Michalski 2002): exponent 1.3, Ea in J/mol (~100 kJ/mol),
# and exp(+Ea/R (1/T - 1/T0))
calcLM_fix <- function(Temp, RH, EA = 100000) {
  (50 / RH)^1.3 * exp((EA / 8.314) * (1 / (Temp + 273.15) - 1 / 293.15))
}
# VTT mould index with the k1 parenthesis fixed, M-based (not Mmax-based) switch,
# and the Hukka & Viitanen decline term
mould_VTT_fix <- function(Temp, RH, sensitivity = "sensitive", wood = 0, surface = 0, dt = 1) {
  cf <- switch(sensitivity,
               very = c(1, 7, 2), sensitive = c(0.3, 6, 1),
               medium = c(0, 5, 1.5), resistant = c(0, 3, 1))
  A <- cf[1]; B <- cf[2]; C <- cf[3]
  n <- length(Temp); M <- numeric(n); m <- 0; unfav <- 0
  for (i in seq_len(n)) {
    tt <- Temp[i]; rh <- RH[i]
    if (is.na(tt) || is.na(rh) || tt <= 0) { M[i] <- m; next }
    RHc <- if (tt > 20) 80 else (-0.00267 * tt^3 + 0.160 * tt^2 - 3.13 * tt + 100)
    if (rh >= RHc && tt > 0 && tt < 50) {
      unfav <- 0
      Mmax <- A + B * ((RHc - rh) / (RHc - 100)) - C * ((RHc - rh) / (RHc - 100))^2
      t_m <- exp(-0.68 * log(tt) - 13.9 * log(rh) + 0.14 * wood - 0.33 * surface + 66.02)
      t_v <- exp(-0.74 * log(tt) - 12.72 * log(rh) + 0.06 * wood + 61.50)
      k1 <- if (m < 1) 1 else 2 / (t_v / t_m - 1)
      k2 <- max(1 - exp(2.3 * (m - Mmax)), 0)
      m <- m + k1 * k2 * dt / (7 * t_m)
      if (m > Mmax) m <- Mmax
    } else {
      unfav <- unfav + dt
      dec <- if (unfav <= 6) -0.00133 else if (unfav <= 24) 0 else -0.000667
      m <- max(m + dec * dt, 0)
    }
    M[i] <- m
  }
  M
}
# ConSciR's own VTT, run as a running index (feeding M back in), for comparison
mould_VTT_ConSciR_running <- function(Temp, RH, sensitivity = "sensitive") {
  n <- length(Temp); M <- numeric(n); m <- 0
  for (i in seq_len(n)) {
    v <- suppressWarnings(calcMould_VTT(Temp[i], RH[i], M_prev = m, sensitivity = sensitivity))
    if (is.na(v) || !is.finite(v)) v <- m
    m <- max(v, 0); M[i] <- m
  }
  M
}

## ---------------------------------------------------------------
## 1. Built-in dataset: ConSciR mydata (London, 2024, 15-min)
## ---------------------------------------------------------------
e <- new.env(); load("/tmp/ConSciR/data/mydata.rda", envir = e)
md <- as.data.frame(e$mydata)
md <- md[!is.na(md$Temp) & !is.na(md$RH), ]
md$day <- as.Date(md$Date)
agg <- aggregate(cbind(Temp, RH) ~ day, md, mean)
names(agg) <- c("date", "Temp", "RH")
agg$Tmin <- aggregate(Temp ~ day, md, min)$Temp
agg$Tmax <- aggregate(Temp ~ day, md, max)$Temp
agg$RHmin <- aggregate(RH ~ day, md, min)$RH
agg$RHmax <- aggregate(RH ~ day, md, max)$RH
agg$DP <- calcDP(agg$Temp, agg$RH)
agg$AH <- calcAH(agg$Temp, agg$RH)
agg$LIM <- calcMould_Zeng(agg$Temp, agg$RH)
agg$LM <- calcLM(agg$Temp, agg$RH)
agg$LMfix <- calcLM_fix(agg$Temp, agg$RH)
agg$PI <- calcPI(agg$Temp, agg$RH)
agg$EMC <- calcEMC_wood(agg$Temp, agg$RH)
for (v in c("Temp","RH","Tmin","Tmax","RHmin","RHmax","DP","AH","LIM","LM","LMfix","PI","EMC"))
  agg[[v]] <- round(agg[[v]], 3)
write.csv(agg, file.path(outdir, "builtin_london_daily.csv"), row.names = FALSE)

## ---------------------------------------------------------------
## 2. Simulated subtropical outdoor climate (southern Taiwan), hourly 2025
## ---------------------------------------------------------------
hours <- 8760
t <- seq_len(hours)
doy <- (t - 1) %/% 24 + 1
hod <- (t - 1) %% 24
# seasonal + diurnal + weather noise (AR(1))
seas_T <- 24.6 - 5.6 * cos(2 * pi * (doy - 15) / 365)
diur_T <- 3.4 * sin(2 * pi * (hod - 9) / 24)
w <- numeric(hours); wn <- rnorm(hours, 0, 0.85)
for (i in 2:hours) w[i] <- 0.93 * w[i - 1] + wn[i]
outT <- seas_T + diur_T + w
seas_R <- 74 + 8 * sin(2 * pi * (doy - 100) / 365)
diur_R <- -11 * sin(2 * pi * (hod - 9) / 24)
wr <- numeric(hours); wrn <- rnorm(hours, 0, 2.2)
for (i in 2:hours) wr[i] <- 0.9 * wr[i - 1] + wrn[i]
outRH <- pmin(98, pmax(35, seas_R + diur_R + wr))
# rain events raise RH, drop T (May-Sep)
rain <- rbinom(hours, 1, ifelse(doy > 120 & doy < 275, 0.05, 0.012))
outRH <- pmin(99, outRH + rain * 9); outT <- outT - rain * 1.4
outdoor <- data.frame(h = t, doy = doy, hod = hod,
                      Temp = round(outT, 2), RH = round(outRH, 2))

## ---------------------------------------------------------------
## 3. Scenario 1 -- gallery + display case, mould risk (Jun 1 - Sep 30)
## ---------------------------------------------------------------
i1 <- which(doy >= 152 & doy <= 273)            # Jun 1 .. Sep 30
oT <- outT[i1]; oR <- outRH[i1]; n1 <- length(i1)
hh <- hod[i1]; dd <- doy[i1]
dow <- (dd + 2) %% 7                              # 0 = Monday (museum closed)
hvac <- (dow != 0) & hh >= 9 & hh < 17
fault <- dd >= 222 & dd <= 228                    # 7-day chiller failure in August
hvac[fault] <- FALSE
setT <- 24; setRH <- 55
gT <- numeric(n1); gR <- numeric(n1); gT[1] <- 26; gR[1] <- 62
kT_on <- 0.55; kR_on <- 0.35; kT_off <- 0.08; kR_off <- 0.06
for (i in 2:n1) {
  if (hvac[i]) {
    gT[i] <- gT[i-1] + kT_on * (setT - gT[i-1]) + rnorm(1, 0, 0.05)
    gR[i] <- gR[i-1] + kR_on * (setRH - gR[i-1]) + rnorm(1, 0, 0.3)
  } else {
    gT[i] <- gT[i-1] + kT_off * (oT[i] - 1.2 - gT[i-1]) + rnorm(1, 0, 0.05)
    gR[i] <- gR[i-1] + kR_off * (oR[i] + 2 - gR[i-1]) + rnorm(1, 0, 0.3)
  }
}
gR <- pmin(97, pmax(30, gR))
# display case: first-order lag (silica gel buffered)
cT <- numeric(n1); cR <- numeric(n1); cT[1] <- 26; cR[1] <- 55
tauT <- 5; tauR <- 90     # hours
for (i in 2:n1) {
  cT[i] <- cT[i-1] + (gT[i] - cT[i-1]) / tauT
  cR[i] <- cR[i-1] + (gR[i] - cR[i-1]) / tauR
}
s1 <- data.frame(h = seq_len(n1), doy = dd, hod = hh,
                 out_T = round(oT,2), out_RH = round(oR,2),
                 gal_T = round(gT,2), gal_RH = round(gR,2),
                 case_T = round(cT,2), case_RH = round(cR,2),
                 hvac = as.integer(hvac))
s1$gal_M_fix  <- round(mould_VTT_fix(gT, gR), 4)
s1$case_M_fix <- round(mould_VTT_fix(cT, cR), 4)
s1$gal_M_pkg  <- round(mould_VTT_ConSciR_running(gT, gR), 4)
s1$gal_LIM    <- round(calcMould_Zeng(gT, gR), 2)
s1$case_LIM   <- round(calcMould_Zeng(cT, cR), 2)
s1$gal_DP     <- round(calcDP(gT, gR), 2)
write.csv(s1, file.path(outdir, "s1_gallery_case.csv"), row.names = FALSE)

## ---------------------------------------------------------------
## 4. Scenario 2 -- coastal fort / basement, ion chromatography (8 samples)
## ---------------------------------------------------------------
ions <- data.frame(
  sample_name = c("FT-01","FT-02","FT-03","FT-04","BS-05","BS-06","BS-07","BS-08"),
  location = c("海岸砲台外牆 0.3 m","海岸砲台外牆 0.8 m","海岸砲台外牆 1.5 m",
               "海岸砲台內牆 0.5 m","古厝地下室北牆 0.4 m","古厝地下室北牆 1.0 m",
               "古厝地下室地坪（10 mL 萃取）","古厝地下室地坪（100 mL 萃取，同一均質樣）"),
  dry_g    = c(1.005, 1.012, 0.998, 1.021, 1.008, 1.003, 0.995, 0.995),
  water_ml = c(100, 100, 100, 100, 100, 100, 10, 100),
  chloride_ppm  = c( 62.0,  41.0,  14.5,  18.0,   5.2,   3.4,  340.0,  34.0),
  nitrate_ppm   = c(  4.5,   6.2,   5.8,  26.5,  24.0,  18.5,   96.0,   9.6),
  sulfate_ppm   = c(  9.0,  12.5,  14.0,  10.4,  32.5,  44.0, 2100.0, 210.0),
  sodium_ppm    = c( 37.6,  22.0,  10.2,  12.6,   4.5,   3.8,   38.0,   3.8),
  potassium_ppm = c(  1.9,   2.4,   2.1,  12.0,   6.8,   5.1,   26.0,   2.6),
  calcium_ppm   = c(  2.2,   4.6,   9.5,   6.0,  18.6,  12.4, 1020.0, 102.0),
  magnesium_ppm = c(  2.6,   3.0,   1.6,   4.2,   2.4,   1.8,   16.0,   1.6),
  stringsAsFactors = FALSE
)
res <- do.call(rbind, lapply(seq_len(nrow(ions)), function(i) {
  r <- ions[i, ]
  b <- fun_salt_balance(r$sample_name, r$dry_g, r$water_ml,
                        r$chloride_ppm, r$nitrate_ppm, r$sulfate_ppm,
                        r$sodium_ppm, r$potassium_ppm, r$calcium_ppm, r$magnesium_ppm)
  data.frame(sample_name = r$sample_name,
             total_wt_pct = b$total_wt * 100,
             eani = b$total_mEq_anions, ecat = b$total_mEq_cations,
             de = b$charge_imbalance_initial,
             de_pct = b$charge_imbalance_initial / pmax(b$total_mEq_anions, b$total_mEq_cations) * 100,
             pathway = b$ECOS_pathway,
             gypsum_wt_pct = b$gypsum_content * 100,
             S_gypsum = b$saturation_gypsum_content,
             total_ion_content_pkg = b$total_ion_content * 100,
             ecos_wt_pct = b$total_wt_adj * 100,
             x_Cl = b$chloride_x, x_NO3 = b$nitrate_x, x_SO4 = b$sulfate_x,
             x_Na = b$sodium_x, x_K = b$potassium_x, x_Ca = b$calcium_x, x_Mg = b$magnesium_x,
             w_Cl = b$chloride_wt_adj, w_NO3 = b$nitrate_wt_adj, w_SO4 = b$sulfate_wt_adj,
             w_Na = b$sodium_wt_adj, w_K = b$potassium_wt_adj,
             w_Ca = b$calcium_wt_adj, w_Mg = b$magnesium_wt_adj,
             warn = b$ECOS_warnings, stringsAsFactors = FALSE)
}))
s2 <- merge(ions, res, by = "sample_name", sort = FALSE)
num <- sapply(s2, is.numeric); s2[num] <- lapply(s2[num], function(x) round(x, 6))
write.csv(s2, file.path(outdir, "s2_salt_samples.csv"), row.names = FALSE)

## also verify the package example reproduces
chk <- fun_salt_balance("test", 1.128, 100, 66.824, 332.956, 87.221, 21.471, 211.358, 75.594, 7.582)
cat("salt_test check: pathway =", chk$ECOS_pathway,
    " total_wt% =", round(chk$total_wt*100,4),
    " gypsum% =", round(chk$gypsum_content*100,4), "\n")

## ---------------------------------------------------------------
## 5. Scenario 3 -- paper store, four control strategies (hourly year)
## ---------------------------------------------------------------
strat <- list(
  A = list(name = "A 恆溫恆濕 20°C/50%", T = 20, RH = 50, band_T = 0.5, band_R = 3),
  B = list(name = "B 只除濕 26°C/50%",  T = 26, RH = 50, band_T = 1.5, band_R = 4),
  C = list(name = "C 只降溫 20°C/65%",  T = 20, RH = 65, band_T = 0.8, band_R = 6),
  D = list(name = "D 無空調（隨外氣）", T = NA, RH = NA, band_T = NA, band_R = NA)
)
mk <- function(s) {
  if (is.na(s$T)) { list(T = outT - 0.8, RH = pmin(98, outRH * 0.96 + 2)) }
  else {
    Tt <- s$T + s$band_T * sin(2*pi*hod/24) + 0.25*w
    Rr <- s$RH + s$band_R * sin(2*pi*(hod-4)/24) + 0.4*wr
    list(T = Tt, RH = pmin(95, pmax(20, Rr)))
  }
}
s3rows <- list(); s3daily <- list()
for (k in names(strat)) {
  s <- strat[[k]]; x <- mk(s)
  LMf <- calcLM_fix(x$T, x$RH); PIv <- calcPI(x$T, x$RH)
  EMC <- calcEMC_wood(x$T, x$RH); LIM <- calcMould_Zeng(x$T, x$RH)
  Mf  <- mould_VTT_fix(x$T, x$RH)
  s3rows[[k]] <- data.frame(
    strategy = k, name = s$name,
    T_mean = mean(x$T), RH_mean = mean(x$RH),
    LM_mean = mean(LMf),                      # arithmetic mean of lifetime multiplier
    LM_rate = 1/mean(1/LMf),                  # damage-weighted (harmonic) LM
    PI_TWPI = 1/mean(1/PIv),                  # time-weighted preservation index
    EMC_mean = mean(EMC), EMC_range = max(EMC) - min(EMC),
    mould_hours = sum(x$RH > LIM), M_max = max(Mf),
    RH_over75 = sum(x$RH > 75.3), stringsAsFactors = FALSE)
  dtab <- data.frame(doy = doy, T = x$T, RH = x$RH, LM = LMf, PI = PIv, EMC = EMC)
  ag <- aggregate(cbind(T, RH, LM, PI, EMC) ~ doy, dtab, mean); ag$strategy <- k
  s3daily[[k]] <- ag
}
s3 <- do.call(rbind, s3rows)
num <- sapply(s3, is.numeric); s3[num] <- lapply(s3[num], function(x) round(x, 4))
write.csv(s3, file.path(outdir, "s3_strategies_summary.csv"), row.names = FALSE)
s3d <- do.call(rbind, s3daily)
num <- sapply(s3d, is.numeric); s3d[num] <- lapply(s3d[num], function(x) round(x, 3))
write.csv(s3d, file.path(outdir, "s3_strategies_daily.csv"), row.names = FALSE)

## ---------------------------------------------------------------
## 6. Scenario 4 -- setpoint grid: energy vs risk (integrated lab)
## ---------------------------------------------------------------
V <- 900                      # m3 store
ACH <- 0.4                    # air changes per hour (infiltration + fresh air)
q <- V * ACH / 3600           # m3/s
Tg <- seq(18, 28, by = 0.5)
Rg <- seq(40, 75, by = 1)
grid <- expand.grid(Tset = Tg, RHset = Rg)
h_out <- calcEnthalpy(outT, outRH)
rho_out <- calcAD(outT, outRH)
grid$kWh_cool <- NA; grid$kWh_heat <- NA
for (i in seq_len(nrow(grid))) {
  h_in <- calcEnthalpy(grid$Tset[i], grid$RHset[i])
  dh <- h_out - h_in
  kw <- q * rho_out * pmax(dh, 0)          # kW of cooling+dehumidification
  kwh <- sum(kw)                            # hourly steps -> kWh
  kwr <- q * rho_out * pmax(-dh, 0)
  grid$kWh_cool[i] <- kwh
  grid$kWh_heat[i] <- sum(kwr)
}
grid$LM <- calcLM_fix(grid$Tset, grid$RHset)
grid$PI <- calcPI(grid$Tset, grid$RHset)
grid$EMC <- calcEMC_wood(grid$Tset, grid$RHset)
grid$LIM <- calcMould_Zeng(grid$Tset, grid$RHset)
grid$mould_margin <- grid$LIM - grid$RHset          # >0 = safe
grid$dp <- calcDP(grid$Tset, grid$RHset)
num <- sapply(grid, is.numeric); grid[num] <- lapply(grid[num], function(x) round(x, 4))
write.csv(grid, file.path(outdir, "s4_setpoint_grid.csv"), row.names = FALSE)

## outdoor climate summary for the page
oag <- aggregate(cbind(Temp, RH) ~ doy, outdoor, mean)
oag$Tmax <- aggregate(Temp ~ doy, outdoor, max)$Temp
oag$RHmax <- aggregate(RH ~ doy, outdoor, max)$RH
num <- sapply(oag, is.numeric); oag[num] <- lapply(oag[num], function(x) round(x, 2))
write.csv(oag, file.path(outdir, "outdoor_daily.csv"), row.names = FALSE)

## ---------------------------------------------------------------
## 7. Reference outputs for the webR code blocks
## ---------------------------------------------------------------
sink(file.path(outdir, "expected_outputs.txt"))
cat("### B1 humidity family\n")
print(data.frame(Temp = c(20,24,28,20), RH = c(50,55,80,65),
                 Pws = round(calcPws(c(20,24,28,20)),3),
                 DP = round(calcDP(c(20,24,28,20), c(50,55,80,65)),2),
                 AH = round(calcAH(c(20,24,28,20), c(50,55,80,65)),2),
                 EMC = round(calcEMC_wood(c(20,24,28,20), c(50,55,80,65)),2)))
cat("\n### B2 calcLM documented vs coded\n")
tt <- c(20,25,20,20); rr <- c(50,50,25,65)
print(data.frame(Temp=tt, RH=rr,
                 ConSciR = round(calcLM(tt,rr),4),
                 documented = round(calcLM_fix(tt,rr),4)))
cat("\n### B3 Zeng LIM vs RH\n")
tt <- c(15,20,25,30,35)
print(data.frame(Temp = tt, LIM0 = round(calcMould_Zeng(tt,60),2),
                 LIM1 = round(calcMould_Zeng(tt,60,LIM=1),2)))
cat("\n### B4 salt_test balance\n")
print(t(chk[,c("ECOS_pathway","total_mEq_anions","total_mEq_cations",
               "charge_imbalance_initial","gypsum_content","saturation_gypsum_content",
               "total_ion_content","total_wt")]))
cat("\n### B5 strategy summary\n"); print(s3)
cat("\n### B6 salt samples\n")
print(s2[,c("sample_name","total_wt_pct","de_pct","pathway","gypsum_wt_pct","S_gypsum")])
sink()

cat("\nDONE. Files:\n"); print(list.files(outdir))
cat("\nS1 peaks: gal M_fix max =", max(s1$gal_M_fix), " case M_fix max =", max(s1$case_M_fix),
    " pkg running max =", max(s1$gal_M_pkg), "\n")
print(s3)
cat("\nGrid range kWh_cool:", range(grid$kWh_cool), "\n")

## ---------------------------------------------------------------
## 8. ECOS/RUNSALT input files + ILLUSTRATIVE crystallisation curves
##    (NOT a real ECOS run -- built from literature DRH values at 20 C)
## ---------------------------------------------------------------
ecos_input <- function(nm, b, RHmin = 15, RHmax = 98, Tconst = 20) {
  sprintf(paste0("%.15g   ; Na\n%.15g   ; K\n%.15g   ; Mg\n%.15g   ; Ca\n",
                 "%.15g   ; Cl\n%.15g   ; NO3\n%.15g   ; SO4\n",
                 "%d   ; Tconst\n%d   ; RHmin\n%d   ; RHmax\n50   ; RHconst\n",
                 "-30   ; Tmin\n50   ; Tmax\n0   ; unit (0=mol, 1=weight)\n\"%s\"   ; sample name\n"),
          b$sodium_x, b$potassium_x, b$magnesium_x, b$calcium_x,
          b$chloride_x, b$nitrate_x, b$sulfate_x, Tconst, RHmin, RHmax, nm)
}
ecos_files <- character(0)
for (i in seq_len(nrow(ions))) {
  r <- ions[i, ]
  b <- fun_salt_balance(r$sample_name, r$dry_g, r$water_ml, r$chloride_ppm, r$nitrate_ppm,
                        r$sulfate_ppm, r$sodium_ppm, r$potassium_ppm, r$calcium_ppm, r$magnesium_ppm)
  txt <- ecos_input(r$sample_name, b)
  writeLines(txt, file.path(outdir, paste0("ECOS_input_", r$sample_name, ".txt")))
  ecos_files[r$sample_name] <- txt
}

DRH20 <- c(halite = 75.3, sylvite = 84.3, niter = 93.6, nitratine = 74.3,
           mirabilite = 93.0, epsomite = 90.1, arcanite = 97.3,
           bischofite = 33.1, `Mg(NO3)2.6H2O` = 54.4, `nitromagnesite` = 54.4)
phase_alloc <- function(b) {
  Na <- b$sodium_x; K <- b$potassium_x; Mg <- b$magnesium_x
  Cl <- b$chloride_x; NO3 <- b$nitrate_x; SO4 <- b$sulfate_x
  ph <- c()
  take <- function(a, c2) min(a, c2)
  x <- take(Na, Cl); ph["halite"] <- x; Na <- Na - x; Cl <- Cl - x
  x <- take(K, NO3); ph["niter"] <- x; K <- K - x; NO3 <- NO3 - x
  x <- take(Na, NO3); ph["nitratine"] <- x; Na <- Na - x; NO3 <- NO3 - x
  x <- take(K, Cl); ph["sylvite"] <- x; K <- K - x; Cl <- Cl - x
  x <- take(Mg, Cl / 2); ph["bischofite"] <- x; Mg <- Mg - x; Cl <- Cl - 2 * x
  x <- take(Mg, NO3 / 2); ph["nitromagnesite"] <- x; Mg <- Mg - x; NO3 <- NO3 - 2 * x
  x <- take(Na / 2, SO4); ph["mirabilite"] <- x; Na <- Na - 2 * x; SO4 <- SO4 - x
  x <- take(Mg, SO4); ph["epsomite"] <- x; Mg <- Mg - x; SO4 <- SO4 - x
  x <- take(K / 2, SO4); ph["arcanite"] <- x; K <- K - 2 * x; SO4 <- SO4 - x
  ph[ph > 1e-6]
}
sim_runsalt <- function(nm, b, RHgrid = seq(98, 15, by = -0.5)) {
  ph <- phase_alloc(b)
  if (!length(ph)) return(NULL)
  ord <- order(DRH20[names(ph)], decreasing = TRUE)
  ph <- ph[ord]
  # mixture depression: each successive phase crystallises lower than its pure DRH
  RHc <- DRH20[names(ph)] - 3 - 4 * (seq_along(ph) - 1)
  RHc <- pmax(RHc, 20)
  out <- do.call(rbind, lapply(seq_along(ph), function(j) {
    f <- 1 / (1 + exp((RHgrid - RHc[j]) / 0.9))     # crystallised fraction
    data.frame(sample = nm, Salt = names(ph)[j], RH = RHgrid,
               mol = round(as.numeric(ph[j]) * f, 8), RH_cryst = round(RHc[j], 2))
  }))
  # water in solution: proportional to still-dissolved ions, zero below MDRH
  diss <- sapply(RHgrid, function(rh) sum(as.numeric(ph) * (1 - 1/(1 + exp((rh - RHc)/0.9)))))
  water <- diss * (RHgrid / pmax(100 - RHgrid, 1)) * 2.2
  out <- rbind(out, data.frame(sample = nm, Salt = "water", RH = RHgrid,
                               mol = round(water, 8), RH_cryst = round(min(RHc), 2)))
  out
}
rs <- list()
for (nm in c("FT-01", "BS-05")) {
  r <- ions[ions$sample_name == nm, ]
  b <- fun_salt_balance(nm, r$dry_g, r$water_ml, r$chloride_ppm, r$nitrate_ppm, r$sulfate_ppm,
                        r$sodium_ppm, r$potassium_ppm, r$calcium_ppm, r$magnesium_ppm)
  rs[[nm]] <- sim_runsalt(nm, b)
}
rsdf <- do.call(rbind, rs)
write.csv(rsdf, file.path(outdir, "s2_runsalt_illustrative.csv"), row.names = FALSE)
cat("\nIllustrative crystallisation RH:\n")
print(unique(rsdf[, c("sample","Salt","RH_cryst")]))
cat("\nECOS input FT-01:\n"); cat(ecos_files["FT-01"])
