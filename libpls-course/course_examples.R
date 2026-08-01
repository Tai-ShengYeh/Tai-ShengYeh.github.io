# Smoke validation for the core examples in the libPLS HTML course.
# Small repetition counts verify APIs and data flow, not scientific results.

library(libPLS)
set.seed(195)

# Lessons 1-4: data, preprocessing, PLS, and cross-validation
data(corn_m51)
X <- corn_m51$X
y <- corn_m51$y
stopifnot(identical(dim(X), c(80L, 700L)), length(y) == 80L)

prep <- pretreat(X[1:60, ], "autoscaling", return_parameters = TRUE)
Xtest_scaled <- pretreat(
  X[61:80, ], "autoscaling", prep$para1, prep$para2
)
stopifnot(identical(dim(prep$X), c(60L, 700L)),
          identical(dim(Xtest_scaled), c(20L, 700L)))

cv <- plscv(
  X[1:60, ], y[1:60], A = 5, K = 5, method = "center",
  PROCESS = FALSE, order = 1, seed = 195
)
fit <- pls(X[1:60, ], y[1:60], A = cv$optLV, method = "center")
val <- plsval(fit, X[61:80, ], y[61:80])
stopifnot(is.finite(val$RMSEP), length(val$ypred) == 20L)

mccv <- plsmccv(
  X, y, A = 3, method = "center", N = 3,
  ratio = 0.8, OPT = FALSE, seed = 195
)
dcv <- plsdcv(
  X, y, A = 3, K = 4, method = "center",
  OPT = FALSE, order = 1, seed = 195
)
rdcv <- plsrdcv(
  X, y, A = 3, K = 4, method = "center",
  Nmcs = 2, OPT = FALSE, seed = 195
)
stopifnot(length(mccv$optLV) == 1L, is.finite(dcv$RMSECV),
          length(rdcv$RMSEP) > 0L)

# Lessons 5-6: PLS-DA, ROC, and PR
data(DM2)
Xd <- DM2$Xcal
yd <- DM2$ycal
cv_da <- plsldacv(
  Xd, yd, A = 4, K = 4, method = "autoscaling",
  OPT = FALSE, order = 1, seed = 195
)
fit_da <- plslda(Xd, yd, A = cv_da$optLV, method = "autoscaling")
roc <- roccurve(fit_da$yfit, yd, flag = FALSE)
pr <- prcurve(fit_da$yfit, yd, nbin = 50)
stopifnot(is.finite(roc$AUC), is.finite(pr$auprc))

# Lessons 7-8: variable selection; small N is an API smoke test only
cars <- carspls(
  X, y, A = 4, fold = 4, method = "center",
  num = 8, selectLV = 0, originalVersion = 0,
  order = 0, seed = 195, process = FALSE
)
uve <- mcuvepls(
  X, y, A = 3, method = "center", N = 5,
  ratio = 0.75, seed = 195, process = FALSE
)
mw <- mwpls(X, y, A = 3, width = 15, verbose = FALSE)
stopifnot(length(cars$vsel) > 0L, length(uve$RI) == ncol(X),
          nrow(mw$RMSEF) > 0L)

rf <- randomfrog_pls(
  X[, 1:30], y, A = 3, N = 5, Q = 5,
  seed = 195, process = FALSE
)
spa_fit <- spa(
  Xd[, 1:12], yd, A = 2, K = 3, Q = 4, N = 5,
  seed = 195, process = FALSE
)
stopifnot(length(rf$Vrank) == 30L,
          length(spa_fit$RankedVariable) == 12L)

# Lesson 9: OSC and ECR
osc <- oscwold(X[1:60, 1:30], y[1:60], X[61:80, 1:30], nOSC = 1)
stopifnot(identical(dim(osc$Zcal), c(60L, 30L)),
          identical(dim(osc$Ztest), c(20L, 30L)))

set.seed(195)
Xs <- matrix(rnorm(25 * 20), 25, 20)
ys <- Xs[, 1] - 0.5 * Xs[, 2] + rnorm(25, sd = 0.1)
ecr_fit <- ecr(Xs[1:18, ], ys[1:18], A = 3, alpha = 0.5)
ecr_val <- ecrpred(ecr_fit, Xs[19:25, ], ys[19:25])
stopifnot(is.finite(ecr_val$RMSEP))

message("All libPLS course smoke examples passed.")

