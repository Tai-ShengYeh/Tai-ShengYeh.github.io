## =====================================================================
## ConSciR 與 SaltsR 的函式定義（直接取自 GitHub 原始碼，未更動算式）
## 這樣可以在瀏覽器的 webR 裡執行，而不需要安裝套件。
## =====================================================================

calcPws <- function(Temp, P_atm = 1013.25, method = c("Buck", "IAPWS", "Magnus", "VAISALA")) {
  method <- match.arg(method)

  TempK = Temp + 273.15

  if (method == "Buck") {

    # Saturation vapor pressure over water in hPa
    Pws_water = 6.1121 * exp((18.678 - (Temp / 234.5)) * (Temp / (257.14 + Temp)))
    # Saturation vapor pressure over ice in hPa
    Pws_ice = 6.1115 * exp((23.036 - (Temp / 333.7)) * (Temp / (279.82 + Temp)))

    Pws = ifelse(Temp < 0, Pws_ice, Pws_water)

  } else if (method == "IAPWS") {

    # IAPWS formulation
    Tc = 647.096
    Pc = 220640  # Critical pressure
    C1 = -7.85951783
    C2 = 1.84408259
    C3 = -11.7866497
    C4 = 22.6807411
    C5 = -15.9618719
    C6 = 1.80122502

    veta = 1 - (TempK / Tc)

    lnPwsPc = (Tc / TempK) * (C1 * veta + C2 * (veta^1.5) + C3 * (veta^3) +
                                 C4 * (veta^3.5) + C5 * (veta^4) + C6 * (veta^7.5))

    Pws = Pc * exp(lnPwsPc)


  } else if (method == "Magnus") {

    # August-Roche-Magnus approximation
    Pws = 6.1094 * exp((17.625 * Temp) / (243.04 + Temp))

    # Pressure correction factor
    Pws = Pws * (P_atm / 1013.25)


  } else if (method == "VAISALA") {

    a0_w = 1 # Pa
    a1_w = -6096.9385 # K
    a2_w = 21.2409642 #
    a3_w = -0.02711193 # K-1
    a4_w = 1.673952e-05 # K-2
    a5_w = 2.433502
    a6_w = 1 # K-1

    a0_i = 1 # Pa
    a1_i = -6024.5282 # K
    a2_i = 29.32707 #
    a3_i = 0.010613868 # K-1
    a4_i = -1.3198825e-05 # K-2
    a5_i = -0.4938258
    a6_i = 1 # K-1

    # Saturation vapor pressure over water in Pa
    Pws_water = a0_w * exp((a1_w / TempK) + a2_w + (a3_w * TempK) +
                             (a4_w * TempK^2) + (a5_w * log(a6_w * TempK)))
    # Saturation vapor pressure over ice in Pa
    Pws_ice = a0_i * exp((a1_i / TempK) + a2_i + (a3_i * TempK) +
                                       (a4_i * TempK^2) + (a5_i * log(a6_i * TempK)))

    Pws = ifelse(Temp < 0, Pws_ice, Pws_water) / 100 # return in hPa

  } else {
    stop("Invalid method. Choose 'IAPWS', 'Buck' or 'Magnus'.")
  }

  # If lower accuracy or a limited temperature range can be tolerated a simpler formula can be used for the water vapour saturation pressure over water (and over ice):
  # A = 6.116441
  # m = 7.591386
  # Tn = 240.7263
  # Pws = A * 10 ^ ( (m * Temp) / (Temp + Tn) )

  return(Pws)
}

calcPw <- function(Temp, RH, ...) {
  Pw = calcPws(Temp, ...) * RH / 100
  return(Pw)
}

calcAH <- function(Temp, RH, P_atm = 1013.25, method = c("Buck_EF", "Buck", "IAPWS", "Magnus", "VAISALA")) {
  method <- match.arg(method)

  if (method == "Buck_EF") {
    # Buck formula with enhancement factor
    A <- 2165  # Constant for water vapor
    P_atm_Pa <- P_atm * 100  # convert hPa to Pa
    T_ratio <- 1 - (373.15 / (273.15 + Temp))
    exponent <- (-0.1299 * T_ratio - 0.6445) * T_ratio - 1.976
    Pv <- P_atm_Pa * exp((exponent * T_ratio + 13.3185) * T_ratio)
    AH <- (A * (RH * (Pv / 1000) / 100)) / (Temp + 273.15)

  } else {
    # Use calcPws for saturation vapor pressure
    Pws <- calcPws(Temp, P_atm = P_atm, method = method)
    Pw <- RH / 100 * Pws  # actual vapor pressure (hPa)
    R_v <- 461.5  # J/(kg·K), specific gas constant for water vapor
    Temp_K <- Temp + 273.15
    AH <- (Pw * 100) / (R_v * Temp_K) * 1000  # g/m³

    # VAISALA
    # AH0 = ((RH * (1.10461E-15 * Temp^10 +
    #               -1.187682E-13 * Temp^9 +
    #               3.089754E-12 * Temp^8 +
    #               7.150535E-11 * Temp^7 +
    #               -3.770916E-9 * Temp^6 +
    #               4.760219E-9 * Temp^5 +
    #               1.725056E-6 * Temp^4 +
    #               1.746817E-5 * Temp^3 +
    #               0.001223148 * Temp^2 +
    #               0.04660427 * Temp +
    #               0.6072509) * 1000) / 100 / (Temp + 273.15)) * (18.01528 / 8.31441)
  }

  return(AH)
}

calcDP <- function(Temp, RH, method = c("Magnus", "Buck")) {
  method <- match.arg(method)

  if (method == "Magnus") {
    # August-Roche-Magnus approximation
    a <- 17.625
    b <- 243.04
    DP <- (b * (log(RH / 100) + ((a * Temp) / (b + Temp)))) /
      (a - log(RH / 100) - ((a * Temp) / (b + Temp)))

  } else if (method == "Buck") {
    # Arden Buck equation with Bögel modification
    a <- 6.1121  # in mbar, not used directly here
    b <- 18.678
    c <- 257.14  # °C
    d <- 234.5   # °C

    # Calculate modified saturation vapor pressure factor
    Ef <- log((RH / 100) * exp((b - (Temp / d)) * (Temp / (c + Temp))))
    DP <- (c * Ef) / (b - Ef)
  }

  return(DP)

  ## Dew Point August-Roche-Magnus
  ## Source: https://bmcnoldy.earth.miami.edu/Humidity.html
  ## Based on the August-Roche-Magnus approximation, valid for:
  ## 0C < T < 60C, 1% < RH < 100%, 0C < DP < 50C
  # a = 17.625
  # b = 243.04
  # DP =
  #   (b * (log(RH / 100) + ((a * Temp) / (b + Temp)))) /
  #   (a - (log(RH / 100)) - ((a * Temp) / (b + Temp)))
  # DP = 243.04 * (log(RH / 100) + ((17.625 * Temp) / (243.04 + Temp))) /
  #   (17.625 - log(RH / 100) - ((17.625 * Temp) / (243.04 + Temp)))
  # return(DP)

  ## Arden Buck equation
  ## Ps(T) (and therefore γ(T, RH)) can be enhanced, using part of the Bögel modification, also known as the Arden Buck equation:
  ## -30C < T < 60C, 1% < RH < 100%
  # a = 6.1121 # mbar
  # b = 18.678
  # c = 257.14 # °C
  # d = 234.5 # °C
  # # Modified vapour pressure (mbar)
  # Ps = a * exp((b - (Temp / d)) * (Temp / (c + Temp)))
  # # Enhancement factor γ(T, RH)
  # Ef = log((RH / 100) * exp((b - (Temp / d)) * (Temp / (c + Temp))))
  # Td = (c * Ef) / (b - Ef)
  # return(Td)

  ## Coefficients, source Wikipedia
  ## a = 6.112 mbar, b = 17.67, c = 243.5 °C # 1980 paper by David Bolton in the Monthly Weather Review
  ## a = 6.112 mbar, b = 17.62, c = 243.12 °C; for −45 °C ≤ T ≤ 60 °C (error ±0.35 °C) # Sonntag 1990
  ## a = 6.105 mbar, b = 17.27, c = 237.7 °C; for 0 °C ≤ T ≤ 60 °C (error ±0.4 °C) # 1974 Psychrometry and Psychrometric Charts
  ## Journal of Applied Meteorology and Climatology, Arden Buck, for different temperature ranges:
  ## a = 6.1121 mbar, b = 17.368, c = 238.88 °C; for 0 °C ≤ T ≤ 50 °C (error ≤ 0.05%)
  ## a = 6.1121 mbar, b = 17.966, c = 247.15 °C; for −40 °C ≤ T ≤ 0 °C (error ≤ 0.06%)

}

calcFP <- function(Temp, RH) {

  # Arden Buck (1981, 1996) coefficients for ice
  a_ice <- 6.1115
  b_ice <- 23.036
  c_ice <- 279.82
  d_ice <- 333.7

  # Partial vapour pressure
  Pws_ice <- a_ice * exp((b_ice - Temp / d_ice) * (Temp / (c_ice + Temp))) # Buck
  Pw_ice <- Pws_ice * RH / 100

  # Frost point (Tf)
  # Tf = (c_ice * log(Pw / a_ice)) / (b_ice - log(Pw / a_ice))
  Tf <- (c_ice * log(Pw_ice / a_ice)) / (b_ice - log(Pw_ice / a_ice))

  return(Tf)

}

calcAD <- function(Temp, RH, P_atm = 1013.25, R_dry = 287.058, R_vap = 461.495, ...) {

  # Convert Temperature to Kelvin
  TempK <- Temp + 273.15

  # Partial pressure of water vapour (Pw) in hPa
  Pws <- calcPws(Temp, ...)        # Saturation vapour pressure (hPa)
  Pw <- Pws * RH / 100             # Actual vapour pressure (hPa)

  # Partial pressure of dry air (Pd) in hPa
  Pd <- P_atm - Pw

  # Convert hPa to Pa for calculation (1 hPa = 100 Pa)
  Pd_Pa <- Pd * 100
  Pw_Pa <- Pw * 100

  # Air density calculation in kg/m³
  AirDensity <- (Pd_Pa / (R_dry * TempK)) + (Pw_Pa / (R_vap * TempK))

  return(AirDensity)
}

calcMR <- function(Temp, RH, P_atm = 1013.25, B = 621.9907, ...) {
  Pw = calcPws(Temp, ...) * RH / 100
  X = (B * Pw) / (P_atm - Pw)
  return(X)
}

calcSH <- function(Temp, RH, P_atm = 1013.25, B = 621.9907, ...) {
  MR = calcMR(Temp, RH, P_atm, B)
  SH = MR / (1 + MR)
  return(SH)
}

calcHR <- function(Temp, RH, P_atm = 1013.25, B = 621.9907, ...) {
  HR = calcMR(Temp, RH, P_atm, B)
  return(HR)
}

calcEnthalpy <- function(Temp, RH, ...) {
  MR = calcMR(Temp, RH, ...)
  h = Temp * (1.01 + 0.00189 * MR) + 2.5 * MR
  return(h)

  # # Standard Enthalpy Formula
  # MR = calcMR(Temp, RH, ...)
  # MR_kg <- MR / 1000  # Convert to kg/kg
  # # Standard psychrometric enthalpy equation
  # h <- 1.006 * Temp + MR_kg * (2501 + 1.86 * Temp)
  # return(h)
}

calcRH_AH <- function(Temp, AH, P_atm = 1013.25) {

  # Constants
  T0 <- 373.15  # Reference temperature in Kelvin

  # Convert temperature to Kelvin
  TempK <- Temp + 273.15

  # Convert atmospheric pressure from hPa to Pa
  P0 <- P_atm * 100  # Convert hPa to Pa

  # Calculate the ratio of T0 to T
  T_ratio <- T0 / TempK

  # Calculate the exponent for vapor pressure equation
  exponent <- ((-0.1299 * (1 - T_ratio) - 0.6445) * (1 - T_ratio) - 1.976) * (1 - T_ratio) + 13.3185

  # Calculate vapor pressure
  vapor_pressure <- P0 * exp(exponent * (1 - T_ratio))

  # Convert vapor pressure from Pa to kPa
  vapor_pressure_kPa <- vapor_pressure / 1000

  # Calculate saturation vapor density
  saturation_vapor_density <- 2165 * (vapor_pressure_kPa / 100) / TempK

  # Calculate relative humidity
  RH <- 1 / (saturation_vapor_density / AH)

  return(RH)

  ## Alternative function (NOAA)
  # RH = (1/(2165*(((101325*exp((((-0.1299*(1 - (373.15/(273.16 + Temp))) - 0.6445)*(1 - (373.15/(273.15 + Temp))) - 1.976)*(1 - (373.15/(273.15 + Temp))) + 13.3185)*(1 - (373.15/(273.15 + Temp)))))/1000)/100)/(Temp + 273.15)/Abs) ) # * 1000
  # return(RH)

}

calcRH_DP <- function(Temp, DewP, method = c("Magnus", "Buck")) {
  method = match.arg(method)

  if (method == "Magnus") {
    a = 17.625
    b = 243.04
    RH = 100 * (exp((a * DewP)/(b + DewP)) /
                  exp((a * Temp) / (b + Temp)))

  } else if (method == "Buck") {
    a = 6.1121  # mbar
    b = 18.678
    c = 257.14  # °C
    d = 234.5   # °C
    # Enhancement factor γ(T, RH)
    Ef = exp((b - (Temp / d)) * (Temp / (c + Temp)))
    # Scaled natural logarithm of the saturation vapour pressure at dew point
    lnPw = (DewP * b) / (c + DewP)
    RH = 100 * exp(lnPw) / Ef
  }

  return(RH)
}

calcTemp <- function(RH, DewP, method = c("Magnus", "Buck")) {
  method = match.arg(method)

  if (method == "Magnus") {
    a = 17.625
    b = 243.04
    Temp = (b * (( (a * DewP) / (b + DewP)) - log(RH / 100))) /
      (a + log(RH / 100) - ((a * DewP) / (b + DewP)))

  } else if (method == "Buck") {
    a = 6.1121  # mbar
    b = 18.678
    c = 257.14  # °C
    d = 234.5   # °C

    # Vapor pressure at dew point
    lnPw = (DewP * b) / (c + DewP)
    Pw = a * exp(lnPw)

    # Function to find root: difference between calculated and given RH
    Temp_fun = function(Temp) {
      Ef = exp((b - (Temp / d)) * (Temp / (c + Temp)))
      RH_calc = 100 * (Pw / (a * Ef))
      return(RH_calc - RH)
    }

    # Numerically solve for Temp between -40 and 60 °C
    res = stats::uniroot(Temp_fun, lower = -40, upper = 60)
    Temp = res$root
  }

  return(Temp)
}

calcLM = function(Temp, RH, EA = 100) {

  # EA = Activation energy J/mol
  # R = 8.314 J/K.mol

  TempK = Temp + 273.15

  LM = (50 / RH) ^ (1/3) * exp((-EA / 8.314) * (1 / TempK - 1 / 293.15))

  return(LM)
}

calcPI <- function(Temp, RH, EA = 90300) {

  # k is expressed as the fraction of expected lifetime per year of the degradation
  k = RH * 5.9e12 * exp(-EA / (8.314 * (Temp + 273.15) ))

  # The expected lifetime, PI, is 1/k
  PI = 1/k

  return(PI)
}

calcEMC_wood <- function(Temp, RH) {

  RH_percent = RH / 100

  # Constants
  W = 349 + 1.29 * Temp + 0.0135 * Temp^2
  K = 0.805 + 0.000736 * Temp - 0.00000273 * Temp^2
  K1 = 6.27 - 0.00938 * Temp - 0.000303 * Temp^2
  K2 = 1.91 + 0.0407 * Temp - 0.000293 * Temp^2

  # Calculate EMC
  EMC = (1800 / W) * (
        ((K * RH_percent) / (1 - K * RH_percent)) +
        (K1 * K * RH_percent + 2 * K1 * K2 * K^2 * RH_percent^2) /
          (1 + K1 * K * RH_percent + K1 * K2 * K^2 * RH_percent^2)
        )

  return(EMC)

}

calcMould_Zeng <- function(Temp, RH, LIM = 0, label = FALSE) {

  Temp_crit = 30

  LIM0    = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.7153 # Low limit of mould growth
  LIM0.1  = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.7300 # 0.1 mm/day growth rate (u)
  LIM0.5  = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.7675 # 0.5 mm/day growth rate (u)
  LIM1    = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.7950 # 1 mm/day growth rate (u)
  LIM2    = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.8250 # 2 mm/day growth rate (u)
  LIM3    = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.8502 # 3 mm/day growth rate (u)
  LIM4    = 0.02633 * cosh(0.10083 * (Temp - Temp_crit)) + 0.8701 # 4 mm/day growth rate (u)


  LIM = switch(
    as.character(LIM),
    "0" = LIM0,
    "0.1" = LIM0.1,
    "0.5" = LIM0.5,
    "1" = LIM1,
    "2" = LIM2,
    "3" = LIM3,
    "4" = LIM4,
    {
      warning("Invalid LIM value. Please select from the following options: 0, 0.1, 0.5, 1, 2, 3, 4")
      return(NA)
    }
  )


  RH = RH / 100 # convert to decimal

  # Sautour relationship between the mould growth rate (mm/day) and relative humidity
  # Mould growth rate (u) = (9.016 * (RH - 0.975) * (RH - 0.742)^2) / (0.231 * (0.231 * (RH - 0.973)) - (-0.002) * (1.715 - 2 * RH))

  if (label) {
    # result <- ifelse(is.na(RH), "NA",
    #             ifelse(RH >= LIM4, "Above LIM4",
    #             ifelse(RH >= LIM3, "4 mm/day growth rate",
    #             ifelse(RH >= LIM2, "3 mm/day growth rate",
    #             ifelse(RH >= LIM1, "2 mm/day growth rate",
    #             ifelse(RH >= LIM0.5, "1 mm/day growth rate",
    #             ifelse(RH >= LIM0.1, "0.5 mm/day growth rate",
    #             ifelse(RH >= LIM0, "0.1 mm/day growth rate",
    #                                 "0 Below LIM0"))))))))


    result <- ifelse(is.na(RH), "NA",
               ifelse(RH >= LIM4, 5,
                ifelse(RH >= LIM3, 4,
                 ifelse(RH >= LIM2, 3,
                  ifelse(RH >= LIM1, 2,
                   ifelse(RH >= LIM0.5, 1,
                    ifelse(RH >= LIM0.1, 0.5,
                     ifelse(RH >= LIM0, 0.1,
                      0))))))))

    return(result)

  } else {

    return(LIM * 100)
  }


}

calcMould_VTT <- function(Temp, RH, M_prev = 0, sensitivity = "very", wood = 0, surface = 0) {

  # Constants for M based on sensitivity
  sensitivity_df <- data.frame(
    "Sensitivity" = c("very", "sensitive", "medium", "resistant"),
    "A" = c(1, 0.3, 0, 0),
    "B" = c(7, 6, 5, 3),
    "C" = c(2, 1, 1.5, 1)
  )

  constants <- sensitivity_df[sensitivity_df$Sensitivity == tolower(sensitivity), ]
  if (nrow(constants) == 0) {
    stop("Invalid sensitivity: choose from 'very', 'sensitive', 'medium', or 'resistant'.")
  }

  A <- constants$A
  B <- constants$B
  C <- constants$C

  # Vectorized function to handle NA values
  calc_mould <- function(temp, rh, m_prev) {
    if (is.na(temp) || is.na(rh)) {
      return(NA)
    }

    # Conditions favourable to initiation of mould growth (0-50C)
    RH_crit <-
      ifelse(
        temp > 20,
        80,
        -0.00267 * temp^3 + 0.160 * temp^2 + 3.13 * temp + 100)

    # Maximum Mould growth index M
    M_max <- A + B * ((RH_crit - rh) / (RH_crit - 100)) - C * ((RH_crit - rh) / (RH_crit - 100))^2

    # Response times Viitanen (1997a)
    t_m <- exp(-0.68 * log(temp) - 13.9 * log(rh) + 0.14 * wood + 66.02)
    t_v <- exp(-0.74 * log(temp) - 12.72 * log(rh) + 0.06 * wood + 61.50)

    # Correction coefficients
    k1 <- ifelse(M_max < 1, 1,  2 / (t_v / (t_m - 1)))
    # Coefficient for the retardation of growth in the later stages
    k2 <- max(1 - exp(2.3 * (m_prev - M_max)), 0)

    # Calculate mould growth rate
    dM_dt <- k1 * k2 * (1 / (7 * exp(-0.68 * log(temp) -
                                       13.9 * log(rh) +
                                       0.14 * wood -
                                       0.33 * surface +
                                       66.02)))

    # Update mould index
    M_new <- m_prev + dM_dt

    return(M_new)
  }

  # Vectorized function
  mapply(calc_mould, Temp, RH, M_prev)
}

calcCoolingPower <- function(Temp1, Temp2, RH1, RH2, volumeFlowRate) {
  h1 <- calcEnthalpy(Temp1, RH1)
  h2 <- calcEnthalpy(Temp2, RH2)
  rho <- calcAD(Temp1, RH1)
  massFlowRate <- volumeFlowRate * rho
  coolingPowerWatts <- massFlowRate * (h1 - h2)
  coolingPowerKW <- coolingPowerWatts / 1000
  coolingPowerKW <- pmax(coolingPowerKW, 0)
  return(coolingPowerKW)
}

calcSensibleHeating <- function(Temp1, Temp2, RH = 50, volumeFlowRate) {
    Cp_air <- 1.006  # kJ/(kg·K)
    rho_air <- calcAD(Temp1, RH)
    deltaT <- Temp2 - Temp1
    sensibleHeat <- rho_air * Cp_air * volumeFlowRate * deltaT
    sensibleHeat <- pmax(sensibleHeat, 0)
    return(sensibleHeat)
}

calcTotalHeating <- function(Temp1, Temp2, RH1, RH2, volumeFlowRate) {

  # Calculate air density using calcAD function
  rho_air <- calcAD(Temp1, RH1)

  # Calculate enthalpies
  h1 <- calcEnthalpy(Temp1, RH1)
  h2 <- calcEnthalpy(Temp2, RH2)

  # Calculate total heat in kW
  totalHeat <- rho_air * volumeFlowRate * (h2 - h1)

  return(totalHeat)
}

calcSensibleHeatRatio <- function(Temp1, Temp2, RH1, RH2, volumeFlowRate) {

  sensibleHeat <- calcSensibleHeating(Temp1, Temp2, volumeFlowRate, RH1)

  totalHeat <- calcTotalHeating(Temp1, Temp2, volumeFlowRate, RH1, RH2)

  SHR <- 100 * sensibleHeat / totalHeat

  # Return 0 if the sensible heat is negative
  if (SHR < 0) {
    return(0)
  } else {
    return(SHR)
  }
}

calcFtoC <- function(TempF) {
  # Temperature Celcius to Fahrenheit
  TempC = (TempF - 32) * 5/9
  return(TempC)
}

## --- SaltsR：唯一的修改是 tibble::tibble( -> data.frame( 並移除結尾多餘逗號 ---
fun_salt_balance <- function(

  sample_name,
  dry_g,
  water_ml,
  chloride_ppm,
  nitrate_ppm,
  sulfate_ppm,
  sodium_ppm,
  potassium_ppm,
  calcium_ppm,
  magnesium_ppm

) {

  # # Load molecular weights and ion charges (z)
  # data("mol_wts", envir = environment())
  # data("salt_charges_z", envir = environment())

  mol_wts <- data.frame(
    chloride = 35.4527,
    nitrate = 62.0049,
    sulfate = 96.064,
    sodium = 22.989768,
    potassium = 39.0983,
    calcium = 40.078,
    magnesium = 24.305
  )

  salt_charges_z <- data.frame(
    chloride = 1,
    nitrate = 1,
    sulfate = 2,
    sodium = 1,
    potassium = 1,
    calcium = 2,
    magnesium = 2
  )

  # Eqn 1. Weight fractions (displayed as weight percents)
  # Eqn 1. Ion content in the sample (w\%)
  # ms (g) | Vw (mL) | c (mg L-1) -> wCl (kg/kg (-))
  chloride_wt = (chloride_ppm * (water_ml / 1000)) / (dry_g * 1000)
  nitrate_wt = (nitrate_ppm * (water_ml / 1000)) / (dry_g * 1000)
  sulfate_wt = (sulfate_ppm * (water_ml / 1000)) / (dry_g * 1000)
  sodium_wt = (sodium_ppm * (water_ml / 1000)) / (dry_g * 1000)
  potassium_wt = (potassium_ppm * (water_ml / 1000)) / (dry_g * 1000)
  calcium_wt = (calcium_ppm * (water_ml / 1000)) / (dry_g * 1000)
  magnesium_wt = (magnesium_ppm * (water_ml / 1000)) / (dry_g * 1000)
  total_wt = chloride_wt + nitrate_wt + sulfate_wt +
    sodium_wt + potassium_wt + calcium_wt + magnesium_wt


  # Eqn 2. Amount of substance converted to mEq
  # e (mEq/kg) | eani  (mEq/kg) | ecat  (mEq/kg)
  chloride_mEq = ((chloride_wt * salt_charges_z$chloride) / (mol_wts$chloride / 1000)) * 1000
  nitrate_mEq = ((nitrate_wt * salt_charges_z$nitrate) / (mol_wts$nitrate / 1000)) * 1000
  sulfate_mEq = ((sulfate_wt * salt_charges_z$sulfate) / (mol_wts$sulfate / 1000)) * 1000
  sodium_mEq = ((sodium_wt * salt_charges_z$sodium) / (mol_wts$sodium / 1000)) * 1000
  potassium_mEq = ((potassium_wt * salt_charges_z$potassium) / (mol_wts$potassium / 1000)) * 1000
  calcium_mEq = ((calcium_wt * salt_charges_z$calcium) / (mol_wts$calcium / 1000)) * 1000
  magnesium_mEq = ((magnesium_wt * salt_charges_z$magnesium) / (mol_wts$magnesium / 1000)) * 1000
  total_mEq_anions = chloride_mEq + nitrate_mEq + sulfate_mEq
  total_mEq_cations = sodium_mEq + potassium_mEq + calcium_mEq + magnesium_mEq


  # Eqn 3. Initial balance to decide Pathway
  # Δe  (mEq/kg) | Δecat or Δeani | pI | pII
  charge_imbalance_initial = abs(total_mEq_cations - total_mEq_anions)
  imbalance_allocation = ifelse(total_mEq_cations > total_mEq_anions,
                                "dExcess Cations", "dExcess Anions")
  Pathway1 = ifelse(
    charge_imbalance_initial <= max(total_mEq_cations, total_mEq_anions) * 0.02 |
      total_mEq_anions > total_mEq_cations, TRUE, FALSE)
  Pathway2 = ifelse(
    charge_imbalance_initial > total_mEq_cations * 0.02 &
      total_mEq_cations > total_mEq_anions, TRUE, FALSE)
  Pathway = ifelse(Pathway1 == TRUE, "Pathway 1", "Pathway 2")


  # Eqn 4. Pathway I - Adjustment of all ions equally
  # e,adj (mEq/kg) eq4
  chloride_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (chloride_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_anions)), NA)
  nitrate_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (nitrate_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_anions)), NA)
  sulfate_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (sulfate_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_anions)), NA)
  sodium_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (sodium_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_cations)), NA)
  potassium_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (potassium_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_cations)), NA)
  calcium_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (calcium_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_cations)), NA)
  magnesium_mEq_Path1 = ifelse(
    Pathway == "Pathway 1",
    (magnesium_mEq * (total_mEq_anions + total_mEq_cations) / (2 * total_mEq_cations)), NA)


  # Eqn 5a. Pathway II - Excess is assumed to relate to the least soluble salt: Calcium adjustment
  # e (mEq/kg) eq5a
  chloride_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", chloride_mEq, NA)
  nitrate_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", nitrate_mEq, NA)
  sulfate_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", sulfate_mEq, NA)
  sodium_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", sodium_mEq, NA)
  potassium_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", potassium_mEq, NA)
  calcium_mEq_Path2Ca =
    ifelse(Pathway == "Pathway 2",
           (ifelse(calcium_mEq - charge_imbalance_initial >= 0,
                   calcium_mEq - charge_imbalance_initial, 0)), NA)
  magnesium_mEq_Path2Ca = ifelse(Pathway == "Pathway 2", magnesium_mEq, NA)
  # Re-balance post Ca (5a)
  total_mEq_anions_Path2Ca = chloride_mEq_Path2Ca + nitrate_mEq_Path2Ca + sulfate_mEq_Path2Ca
  total_mEq_cations_Path2Ca = sodium_mEq_Path2Ca + potassium_mEq_Path2Ca + calcium_mEq_Path2Ca + magnesium_mEq_Path2Ca
  charge_imbalance_CaAdj =
    ifelse(Pathway == "Pathway 2",
           ifelse(
             abs(total_mEq_cations_Path2Ca - total_mEq_anions_Path2Ca) < 0.000001,
             0, total_mEq_cations_Path2Ca - total_mEq_anions_Path2Ca), NA)


  # Eqn 5b. Pathway II - Excess is assumed to relate to the least soluble salt: Magnesium adjustment
  # e (mEq/kg) eq5b
  chloride_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", chloride_mEq_Path2Ca, NA)
  nitrate_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", nitrate_mEq_Path2Ca, NA)
  sulfate_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", sulfate_mEq_Path2Ca, NA)
  sodium_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", sodium_mEq_Path2Ca, NA)
  potassium_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", potassium_mEq_Path2Ca, NA)
  calcium_mEq_Path2Mg = ifelse(Pathway == "Pathway 2", calcium_mEq_Path2Ca, NA)
  magnesium_mEq_Path2Mg =
    ifelse(Pathway == "Pathway 2",
           (ifelse(magnesium_mEq_Path2Ca - charge_imbalance_CaAdj >= 0,
                   magnesium_mEq_Path2Ca - charge_imbalance_CaAdj, 0)), NA)
  # Re-balance post Mg (5b)
  total_mEq_anions_Path2Mg = chloride_mEq_Path2Mg + nitrate_mEq_Path2Mg + sulfate_mEq_Path2Mg
  total_mEq_cations_Path2Mg = sodium_mEq_Path2Mg + potassium_mEq_Path2Mg + calcium_mEq_Path2Mg + magnesium_mEq_Path2Mg
  charge_imbalance_MgAdj =
    ifelse(Pathway == "Pathway 2",
           ifelse(
             abs(total_mEq_cations_Path2Mg - total_mEq_anions_Path2Mg) < 0.000001,
             0, total_mEq_cations_Path2Mg - total_mEq_anions_Path2Mg), NA)


  # Eqn 5c. Pathway II - Excess is assumed to relate to the least soluble salt: Sodium adjustment
  # e (mEq/kg) eq5c
  chloride_mEq_Path2Na = ifelse(Pathway == "Pathway 2", chloride_mEq_Path2Mg, NA)
  nitrate_mEq_Path2Na = ifelse(Pathway == "Pathway 2", nitrate_mEq_Path2Mg, NA)
  sulfate_mEq_Path2Na = ifelse(Pathway == "Pathway 2", sulfate_mEq_Path2Mg, NA)
  sodium_mEq_Path2Na =
    ifelse(Pathway == "Pathway 2",
           (ifelse(
             sodium_mEq_Path2Mg - charge_imbalance_MgAdj >= 0,
             sodium_mEq_Path2Mg - charge_imbalance_MgAdj, 0)), NA)
  potassium_mEq_Path2Na = ifelse(Pathway == "Pathway 2", potassium_mEq_Path2Mg, NA)
  calcium_mEq_Path2Na = ifelse(Pathway == "Pathway 2", calcium_mEq_Path2Mg, NA)
  magnesium_mEq_Path2Na = ifelse(Pathway == "Pathway 2", magnesium_mEq_Path2Mg, NA)
  # Re-balance post Na (5c)
  total_mEq_anions_Path2Na = chloride_mEq_Path2Na + nitrate_mEq_Path2Na + sulfate_mEq_Path2Na
  total_mEq_cations_Path2Na = sodium_mEq_Path2Na + potassium_mEq_Path2Na + calcium_mEq_Path2Na + magnesium_mEq_Path2Na
  charge_imbalance_NaAdj =
    ifelse(Pathway == "Pathway 2",
           ifelse(
             abs(total_mEq_cations_Path2Na - total_mEq_anions_Path2Na) < 0.000001,
             0, total_mEq_cations_Path2Na - total_mEq_anions_Path2Na), NA)


  # Eqn 5d. Pathway II - Excess is assumed to relate to the least soluble salt: Potassium adjustment
  # e,adj (mEq/kg) eq5d
  chloride_mEq_Path2K = ifelse(Pathway == "Pathway 2", chloride_mEq_Path2Na, NA)
  nitrate_mEq_Path2K = ifelse(Pathway == "Pathway 2", nitrate_mEq_Path2Na, NA)
  sulfate_mEq_Path2K = ifelse(Pathway == "Pathway 2", sulfate_mEq_Path2Na, NA)
  sodium_mEq_Path2K = ifelse(Pathway == "Pathway 2", sodium_mEq_Path2Na, NA)
  potassium_mEq_Path2K =
    ifelse(Pathway == "Pathway 2",
           ifelse(
             potassium_mEq_Path2Na - charge_imbalance_NaAdj >= 0,
             potassium_mEq_Path2Na - charge_imbalance_NaAdj, 0), NA)
  calcium_mEq_Path2K = ifelse(Pathway == "Pathway 2", calcium_mEq_Path2Na, NA)
  magnesium_mEq_Path2K = ifelse(Pathway == "Pathway 2", magnesium_mEq_Path2Na, NA)
  # Re-balance post K (5d)
  total_mEq_anions_Path2K = chloride_mEq_Path2K + nitrate_mEq_Path2K + sulfate_mEq_Path2K
  total_mEq_cations_Path2K = sodium_mEq_Path2K + potassium_mEq_Path2K + calcium_mEq_Path2K + magnesium_mEq_Path2K
  charge_imbalance_KAdj =
    ifelse(Pathway == "Pathway 2",
           ifelse(
             abs(total_mEq_cations_Path2K - total_mEq_anions_Path2K) < 0.000001,
             0, total_mEq_cations_Path2K - total_mEq_anions_Path2K), NA)


  # Adjusted Values (after either Pathway I or Pathway II) for gypsum removal
  # e,adj (mEq/kg) pI or pII
  chloride_mEq_adj = ifelse(Pathway == "Pathway 1", chloride_mEq_Path1, chloride_mEq_Path2K)
  nitrate_mEq_adj = ifelse(Pathway == "Pathway 1", nitrate_mEq_Path1, nitrate_mEq_Path2K)
  sulfate_mEq_adj = ifelse(Pathway == "Pathway 1", sulfate_mEq_Path1, sulfate_mEq_Path2K)
  sodium_mEq_adj = ifelse(Pathway == "Pathway 1", sodium_mEq_Path1, sodium_mEq_Path2K)
  potassium_mEq_adj = ifelse(Pathway == "Pathway 1", potassium_mEq_Path1, potassium_mEq_Path2K)
  calcium_mEq_adj = ifelse(Pathway == "Pathway 1", calcium_mEq_Path1, calcium_mEq_Path2K)
  magnesium_mEq_adj = ifelse(Pathway == "Pathway 1", magnesium_mEq_Path1, magnesium_mEq_Path2K)


  # Eqn 6. Amount of Calcium or Sulfate that limits CaSO4 production
  # Determination of gypsum content
  # elim,CaSO4 (mEq/kg) eq6
  gypsum_content_limit = min(sulfate_mEq_adj, calcium_mEq_adj)


  # Eqn 7. Removal of gypsum ECOS/Runsalt model specific
  # e,adj (mEq/kg) eq7
  chloride_mEq_adj_SO4 = chloride_mEq_adj
  nitrate_mEq_adj_SO4 = nitrate_mEq_adj
  sulfate_mEq_adj_SO4 = sulfate_mEq_adj - gypsum_content_limit
  sodium_mEq_adj_SO4 = sodium_mEq_adj
  potassium_mEq_adj_SO4 = potassium_mEq_adj
  calcium_mEq_adj_SO4 = calcium_mEq_adj - gypsum_content_limit
  magnesium_mEq_adj_SO4 = magnesium_mEq_adj

  # Final Balance check
  # Δef (mEq/kg)
  charge_imbalance_final = ifelse(
    abs((chloride_mEq_adj_SO4 + nitrate_mEq_adj_SO4 + sulfate_mEq_adj_SO4) -
          (sodium_mEq_adj_SO4 + potassium_mEq_adj_SO4 + calcium_mEq_adj_SO4 + magnesium_mEq_adj_SO4))
    < 0.000001, TRUE, FALSE)


  # Eqn 8 part 1. Balanced Molar Concentrations excluding gypsum
  # c,adj (mol/kg)
  chloride_molkg = chloride_mEq_adj_SO4 / salt_charges_z$chloride / 1000
  nitrate_molkg = nitrate_mEq_adj_SO4 / salt_charges_z$nitrate / 1000
  sulfate_molkg = sulfate_mEq_adj_SO4 / salt_charges_z$sulfate / 1000
  sodium_molkg = sodium_mEq_adj_SO4 / salt_charges_z$sodium / 1000
  potassium_molkg = potassium_mEq_adj_SO4 / salt_charges_z$potassium / 1000
  calcium_molkg = calcium_mEq_adj_SO4 / salt_charges_z$calcium / 1000
  magnesium_mmolkg = magnesium_mEq_adj_SO4 / salt_charges_z$magnesium / 1000


  # Eqn 8 part 2. ECOS INPUTS: Adjusted amounts excluding gypsum as mole fraction (ion values as mole fraction)
  # x,adj (-) eq8
  chloride_x = chloride_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  nitrate_x = nitrate_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  sulfate_x = sulfate_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  sodium_x = sodium_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  potassium_x = potassium_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  calcium_x = calcium_molkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)
  magnesium_x = magnesium_mmolkg / (chloride_molkg + nitrate_molkg + sulfate_molkg + sodium_molkg + potassium_molkg + calcium_molkg + magnesium_mmolkg)


  # Eqn 9. Assessment of Correction Degree as a Fraction of Initial Cation Sum, displayed as percent
  # Degree of adjustments as a fraction
  # f Δe  amount of substance in excess as a fraction
  # fΔe (-) eq9
  calcium_fraction = ifelse(
    Pathway == "Pathway 1", 0,
    (calcium_mEq - calcium_mEq_adj) / (sodium_mEq + potassium_mEq + calcium_mEq + magnesium_mEq))
  magnesium_fraction =ifelse(
    Pathway == "Pathway 1", 0,
    (magnesium_mEq - magnesium_mEq_adj) / (sodium_mEq + potassium_mEq + calcium_mEq + magnesium_mEq))
  sodium_fraction =ifelse(
    Pathway == "Pathway 1", 0,
    (sodium_mEq - sodium_mEq_adj) / (sodium_mEq + potassium_mEq + calcium_mEq + magnesium_mEq))
  potassium_fraction =ifelse(
    Pathway == "Pathway 1", 0,
    (potassium_mEq - potassium_mEq_adj) / (sodium_mEq + potassium_mEq + calcium_mEq + magnesium_mEq))


  # Eqn 10. ECOS input: Adjusted contents as Weight Fraction Relative to the Dry Sample Mass, displayed as a weight percent
  # final corrected amount of substance as weight fraction per individual ion in the dry sample mass, wi,f
  # w,f (-) eq10
  chloride_wt_adj = ((chloride_mEq_adj_SO4 * (mol_wts$chloride / 1000)) / salt_charges_z$chloride) * 0.001
  nitrate_wt_adj = ((nitrate_mEq_adj_SO4 * (mol_wts$nitrate / 1000)) / salt_charges_z$nitrate) * 0.001
  sulfate_wt_adj = ((sulfate_mEq_adj_SO4 * (mol_wts$sulfate / 1000)) / salt_charges_z$sulfate) * 0.001
  sodium_wt_adj = ((sodium_mEq_adj_SO4 * (mol_wts$sodium / 1000)) / salt_charges_z$sodium) * 0.001
  potassium_wt_adj = ((potassium_mEq_adj_SO4 * (mol_wts$potassium / 1000)) / salt_charges_z$potassium) * 0.001
  calcium_wt_adj = ((calcium_mEq_adj_SO4 * (mol_wts$calcium / 1000)) / salt_charges_z$calcium) * 0.001
  magnesium_wt_adj = ((magnesium_mEq_adj_SO4 * (mol_wts$magnesium / 1000)) / salt_charges_z$magnesium) * 0.001
  total_wt_adj = chloride_wt_adj + nitrate_wt_adj + sulfate_wt_adj +
    sodium_wt_adj + potassium_wt_adj + calcium_wt_adj + magnesium_wt_adj


  # Eqn 11. Evaluation of the corrected Ion and Gypsum Content displayed as a weight percent
  # total ion content adjusted as a fraction compared to the dry sample mass,
  # wtot,adj
  # wtot,adj + wCaSO4(-) eq11
  total_wt_adj_gypsum = (total_wt - total_wt_adj)
  # Gypsum content
  # wCaSO4 (-)
  gypsum_content = ((gypsum_content_limit) * (0.5 * (mol_wts$sulfate + mol_wts$calcium)) * 0.000001)

  # saturation degree of determined  gypsum content in given sample/water ratio (considering 2.14g/L 20C)
  # SCaSO4 (%)
  saturation_gypsum_content = gypsum_content / ((0.214 * water_ml / 10000) / dry_g * 100)

  # Total amount of the adjusted ion content (excluding gypsum)
  # wtot,adj (-) eq11
  total_ion_content = total_wt_adj_gypsum - gypsum_content

  # adjusted content sum Na+, K+
  # wMg,Na,K,adj (-)
  sodium_potassium_content_adj = ifelse(
    Pathway == "Pathway 2", abs((sodium_wt_adj + potassium_wt_adj) - (sodium_wt + potassium_wt)), NA)

  # adjusted content Mg2+
  # wMg,adj (-)
  magnessium_content_adj = ifelse(
    Pathway == "Pathway 2", (((abs(magnesium_mEq_adj - magnesium_mEq)) * 0.024305) / 2) * 0.001, NA)

  # adjusted content Ca2+
  # wCa,adj (-)2
  calcium_content_adj =ifelse(
    Pathway == "Pathway 2", (((abs(calcium_mEq_adj - calcium_mEq)) * 0.040078) / 2) * 0.001, NA)

  # hypothetical CO32- content related to Na+, K+
  # wCO3,h (-)
  hypothetical_CO3 = ifelse(
    Pathway == "Pathway 2", ((charge_imbalance_MgAdj + charge_imbalance_NaAdj + charge_imbalance_KAdj) / 1000000) * (60.01 / 2),
    NA)

  # ECOS outputs
  # Eqn 8b. Mols
  chloride_ECOS_mol = chloride_x
  nitrate_ECOS_mol = nitrate_x
  sulfate_ECOS_mol = sulfate_x
  sodium_ECOS_mol = sodium_x
  potassium_ECOS_mol = potassium_x
  calcium_ECOS_mol = calcium_x
  magnesium_ECOS_mol = magnesium_x

  # Eqn 10. Weights
  chloride_ECOS_weight = chloride_wt_adj
  nitrate_ECOS_weight = nitrate_wt_adj
  sulfate_ECOS_weight = sulfate_wt_adj
  sodium_ECOS_weight = sodium_wt_adj
  potassium_ECOS_weight = potassium_wt_adj
  calcium_ECOS_weight = calcium_wt_adj
  magnesium_ECOS_weight = magnesium_wt_adj

  ECOS_pathway = Pathway
  ECOS_warnings = ifelse(
    saturation_gypsum_content > 1,
    "The true gypsum content is likely to be higher and dilution is needed.",
    "No warnings")



  # RESULTS Output dataframe with results of all calculations
  salt_balance <- data.frame(
    # salt_balance <- c(
    sample_name,
    dry_g,
    water_ml,
    chloride_ppm,
    nitrate_ppm,
    sulfate_ppm,
    sodium_ppm,
    potassium_ppm,
    calcium_ppm,
    magnesium_ppm,

    # Eqn 1
    chloride_wt,
    nitrate_wt,
    sulfate_wt,
    sodium_wt,
    potassium_wt,
    calcium_wt,
    magnesium_wt,
    total_wt,

    # Eqn 2
    chloride_mEq,
    nitrate_mEq,
    sulfate_mEq,
    sodium_mEq,
    potassium_mEq,
    calcium_mEq,
    magnesium_mEq,
    total_mEq_anions,
    total_mEq_cations,

    # Eqn 3
    charge_imbalance_initial,
    imbalance_allocation,
    Pathway1,
    Pathway2,
    # Pathway,

    # Eqn 4
    chloride_mEq_Path1,
    nitrate_mEq_Path1,
    sulfate_mEq_Path1,
    sodium_mEq_Path1,
    potassium_mEq_Path1,
    calcium_mEq_Path1,
    magnesium_mEq_Path1,

    # Eqn 5a
    chloride_mEq_Path2Ca,
    nitrate_mEq_Path2Ca,
    sulfate_mEq_Path2Ca,
    sodium_mEq_Path2Ca,
    potassium_mEq_Path2Ca,
    calcium_mEq_Path2Ca,
    magnesium_mEq_Path2Ca,
    total_mEq_anions_Path2Ca,
    total_mEq_cations_Path2Ca,
    charge_imbalance_CaAdj,

    # Eqn 5b
    chloride_mEq_Path2Mg,
    nitrate_mEq_Path2Mg,
    sulfate_mEq_Path2Mg,
    sodium_mEq_Path2Mg,
    potassium_mEq_Path2Mg,
    calcium_mEq_Path2Mg,
    magnesium_mEq_Path2Mg,
    total_mEq_anions_Path2Mg,
    total_mEq_cations_Path2Mg,
    charge_imbalance_MgAdj,

    # Eqn 5c
    chloride_mEq_Path2Na,
    nitrate_mEq_Path2Na,
    sulfate_mEq_Path2Na,
    sodium_mEq_Path2Na,
    potassium_mEq_Path2Na,
    calcium_mEq_Path2Na,
    magnesium_mEq_Path2Na,
    total_mEq_anions_Path2Na,
    total_mEq_cations_Path2Na,
    charge_imbalance_NaAdj,

    # Eqn 5d
    chloride_mEq_Path2K,
    nitrate_mEq_Path2K,
    sulfate_mEq_Path2K,
    sodium_mEq_Path2K,
    potassium_mEq_Path2K,
    calcium_mEq_Path2K,
    magnesium_mEq_Path2K,
    total_mEq_anions_Path2K,
    total_mEq_cations_Path2K,
    charge_imbalance_KAdj,

    # Adjusted for gypsum removal
    chloride_mEq_adj,
    nitrate_mEq_adj,
    sulfate_mEq_adj,
    sodium_mEq_adj,
    potassium_mEq_adj,
    calcium_mEq_adj,
    magnesium_mEq_adj,

    # Eqn 6
    gypsum_content_limit,

    # Eqn 7
    chloride_mEq_adj_SO4,
    nitrate_mEq_adj_SO4,
    sulfate_mEq_adj_SO4,
    sodium_mEq_adj_SO4,
    potassium_mEq_adj_SO4,
    calcium_mEq_adj_SO4,
    magnesium_mEq_adj_SO4,
    charge_imbalance_final,

    # Eqn 8 pt1
    chloride_molkg,
    nitrate_molkg,
    sulfate_molkg,
    sodium_molkg,
    potassium_molkg,
    calcium_molkg,
    magnesium_mmolkg,

    # Eqn 8 pt2
    ## ECOS INPUTS
    chloride_x,
    nitrate_x,
    sulfate_x,
    sodium_x,
    potassium_x,
    calcium_x,
    magnesium_x,

    # Eqn 9
    calcium_fraction,
    magnesium_fraction,
    sodium_fraction,
    potassium_fraction,

    # Eqn 10
    chloride_wt_adj,
    nitrate_wt_adj,
    sulfate_wt_adj,
    sodium_wt_adj,
    potassium_wt_adj,
    calcium_wt_adj,
    magnesium_wt_adj,
    total_wt_adj,

    # Eqn 11
    total_wt_adj_gypsum,
    gypsum_content,
    saturation_gypsum_content,
    total_ion_content,
    sodium_potassium_content_adj,
    magnessium_content_adj,
    calcium_content_adj,
    hypothetical_CO3,

    # ECOS outputs
    # Mols
    sodium_ECOS_mol,
    potassium_ECOS_mol,
    magnesium_ECOS_mol,
    calcium_ECOS_mol,
    chloride_ECOS_mol,
    nitrate_ECOS_mol,
    sulfate_ECOS_mol,

    # Weight
    sodium_ECOS_weight,
    potassium_ECOS_weight,
    magnesium_ECOS_weight,
    calcium_ECOS_weight,
    chloride_ECOS_weight,
    nitrate_ECOS_weight,
    sulfate_ECOS_weight,

    # Description and warnings
    ECOS_pathway,
    ECOS_warnings
  )

  return(salt_balance)
}

## --- 本教材補上的修正版（見 1.4 節） ---
calcLM_fix <- function(Temp, RH, EA = 100000) {
  (50 / RH)^1.3 * exp((EA / 8.314) * (1 / (Temp + 273.15) - 1 / 293.15))
}
RHcrit_fix <- function(Temp) {
  ifelse(Temp > 20, 80, -0.00267 * Temp^3 + 0.160 * Temp^2 - 3.13 * Temp + 100)
}
mould_VTT_fix <- function(Temp, RH, sensitivity = "sensitive", dt = 1) {
  cf <- switch(sensitivity, very = c(1,7,2), sensitive = c(0.3,6,1),
               medium = c(0,5,1.5), resistant = c(0,3,1))
  A <- cf[1]; B <- cf[2]; C <- cf[3]
  n <- length(Temp); M <- numeric(n); m <- 0; unfav <- 0
  for (i in seq_len(n)) {
    tt <- Temp[i]; rh <- RH[i]
    if (is.na(tt) || is.na(rh) || tt <= 0 || tt >= 50) { M[i] <- m; next }
    RHc <- RHcrit_fix(tt)
    if (rh >= RHc) {
      unfav <- 0
      r <- (RHc - rh) / (RHc - 100)
      Mmax <- A + B * r - C * r^2
      t_m <- exp(-0.68 * log(tt) - 13.9 * log(rh) + 66.02)
      t_v <- exp(-0.74 * log(tt) - 12.72 * log(rh) + 61.50)
      k1 <- if (m < 1) 1 else 2 / (t_v / t_m - 1)
      k2 <- max(1 - exp(2.3 * (m - Mmax)), 0)
      m <- min(m + k1 * k2 * dt / (7 * t_m), Mmax)
    } else {
      unfav <- unfav + dt
      dec <- if (unfav <= 6) -0.00133 else if (unfav <= 24) 0 else -0.000667
      m <- max(m + dec * dt, 0)
    }
    M[i] <- m
  }
  M
}


## --- 教材資料集（模擬，種子 20260810） ---
ions <- data.frame(
  sample_name   = c("FT-01", "FT-02", "FT-03", "FT-04", "BS-05", "BS-06", "BS-07", "BS-08"),
  dry_g         = c(1.005, 1.012, 0.998, 1.021, 1.008, 1.003, 0.995, 0.995),
  water_ml      = c(100, 100, 100, 100, 100, 100, 10, 100),
  chloride_ppm  = c(62, 41, 14.5, 18, 5.2, 3.4, 340, 34),
  nitrate_ppm   = c(4.5, 6.2, 5.8, 26.5, 24, 18.5, 96, 9.6),
  sulfate_ppm   = c(9, 12.5, 14, 10.4, 32.5, 44, 2100, 210),
  sodium_ppm    = c(37.6, 22, 10.2, 12.6, 4.5, 3.8, 38, 3.8),
  potassium_ppm = c(1.9, 2.4, 2.1, 12, 6.8, 5.1, 26, 2.6),
  calcium_ppm   = c(2.2, 4.6, 9.5, 6, 18.6, 12.4, 1020, 102),
  magnesium_ppm = c(2.6, 3, 1.6, 4.2, 2.4, 1.8, 16, 1.6),
  stringsAsFactors = FALSE)

salt_test <- data.frame(sample_name = "test", dry_g = 1.128, water_ml = 100,
  chloride_ppm = 66.824, nitrate_ppm = 332.956, sulfate_ppm = 87.221,
  sodium_ppm = 21.471, potassium_ppm = 211.358, calcium_ppm = 75.594,
  magnesium_ppm = 7.582, stringsAsFactors = FALSE)

mol_wts <- data.frame(chloride = 35.4527, nitrate = 62.0049, sulfate = 96.064,
  sodium = 22.989768, potassium = 39.0983, calcium = 40.078, magnesium = 24.305)
salt_charges_z <- data.frame(chloride = 1, nitrate = 1, sulfate = 2,
  sodium = 1, potassium = 1, calcium = 2, magnesium = 2)

strategies <- data.frame(
  strategy = c("A","B","C","D"),
  label = c("A 恆溫恆濕 20C/50%", "B 只除濕 26C/50%", "C 只降溫 20C/65%", "D 無空調"),
  Temp = c(20, 26, 20, 23.6), RH = c(50, 50, 65, 73.3), stringsAsFactors = FALSE)

run_balance <- function(df) {
  do.call(rbind, lapply(seq_len(nrow(df)), function(i) {
    r <- df[i, ]
    b <- fun_salt_balance(r$sample_name, r$dry_g, r$water_ml, r$chloride_ppm,
                          r$nitrate_ppm, r$sulfate_ppm, r$sodium_ppm,
                          r$potassium_ppm, r$calcium_ppm, r$magnesium_ppm)
    data.frame(sample = r$sample_name,
               total_wt_pct = round(b$total_wt * 100, 3),
               eani = round(b$total_mEq_anions, 1),
               ecat = round(b$total_mEq_cations, 1),
               de_pct = round(b$charge_imbalance_initial /
                                pmax(b$total_mEq_anions, b$total_mEq_cations) * 100, 2),
               pathway = b$ECOS_pathway,
               gypsum_pct = round(b$gypsum_content * 100, 3),
               S = round(b$saturation_gypsum_content, 3),
               stringsAsFactors = FALSE)
  }))
}
