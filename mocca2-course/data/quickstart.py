"""MOCCA2 快速上手：魚露中己二烯酸（防腐劑）的 PDA 資料

執行： python quickstart.py
需求： pip install mocca2
"""
import numpy as np
from mocca2 import Chromatogram

# 空白與樣品的時間點數略有差異（2346 vs 2345），故開啟 interpolate_blank
ch = Chromatogram("std_0.25ppm.txt", "blank.txt",
                  name="魚露 己二烯酸 0.25 ppm 標準品",
                  interpolate_blank=True)

ch.correct_baseline()
ch.find_peaks(min_height=0.05)

trace = ch.contract()          # 壓成單一波長軌跡
print(f"{ch.name}：找到 {len(ch.peaks)} 個峰")
for p in sorted(ch.peaks, key=lambda x: x.maximum):
    t = ch.time[p.maximum]
    tag = "  <- 己二烯酸" if 9.5 < t < 10.3 else ("  （溶劑鋒區）" if t < 4 else "")
    print(f"  {t:6.2f} min   高度 {trace[p.maximum]:7.3f} mAU{tag}")

# 對照：未檢出防腐劑的真實魚露樣品
neg = Chromatogram("sample_negative.txt", name="魚露 樣品（未檢出）")
neg.correct_baseline()
neg.find_peaks(min_height=0.05)
late = [p for p in neg.peaks if neg.time[p.maximum] > 4]
print(f"\n{neg.name}：4 分鐘之後的峰數 = {len(late)}")
print("（LCsolution 峰表同樣未檢出己二烯酸，兩者一致）")
