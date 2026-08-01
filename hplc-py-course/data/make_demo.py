"""Generate the teaching chromatogram shipped with the hplc-py course.

Deliberately SIMULATED with known ground truth so students can check whether
hplc-py recovers the true areas. Parameterised exactly as Eq. 1 of
Chure & Cremer (2024), JOSS 9(94), 6270 -- so A is the peak AREA.
"""
import numpy as np
import pandas as pd
from scipy.special import erf

OUT = r'D:\claude\hplc-py-course\data'

# tau (min), sigma (min), alpha (skew), A (area, mAU*min), label
TRUTH = [
    (4.20, 0.12, 1.5, 95.0, "sucrose"),
    (5.60, 0.14, 2.0, 150.0, "glucose"),
    (5.95, 0.15, 2.0, 58.0, "fructose"),        # shoulder on glucose
    (9.10, 0.18, 3.0, 180.0, "citric acid"),
    (12.80, 0.20, 1.0, 72.0, "benzoic acid"),
    (15.40, 0.22, 0.5, 120.0, "caffeine"),
]


def skew_normal(t, tau, sigma, alpha, A):
    z = (t - tau) / sigma
    return (A / np.sqrt(2 * np.pi * sigma ** 2)) * np.exp(-0.5 * z ** 2) * (
        1 + erf(alpha * z / np.sqrt(2)))


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(20260730)          # deterministic

    t = np.arange(0.0, 20.0 + 1e-9, 0.01)
    baseline = 1.5 + 0.35 * t + 0.012 * t ** 2      # gradient-like drift
    peaks = sum(skew_normal(t, *p[:4]) for p in TRUTH)
    noise = rng.normal(0, 0.8, t.size)
    signal = baseline + peaks + noise

    df = pd.DataFrame({"time": np.round(t, 3), "signal": np.round(signal, 4)})
    df.to_csv(os.path.join(OUT, "demo_chromatogram.csv"), index=False)

    truth = pd.DataFrame(
        [(lab, tau, sig, al, A) for tau, sig, al, A, lab in TRUTH],
        columns=["compound", "retention_time", "scale", "skew", "area"])
    truth.to_csv(os.path.join(OUT, "demo_ground_truth.csv"), index=False)

    print(df.head())
    print("rows:", len(df), " time step:", round(t[1] - t[0], 4), "min")
    print("signal range: %.1f .. %.1f mAU" % (signal.min(), signal.max()))
    print(truth.to_string(index=False))


if __name__ == "__main__":
    main()
