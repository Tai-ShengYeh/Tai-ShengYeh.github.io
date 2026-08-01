"""把 Shimadzu LCsolution 匯出的 [PDA 3D] 區段轉成 MOCCA2 可直接讀取的檔案。

MOCCA2 的 labsolutions 解析器預期：
  - 逗號分隔（原始檔是 tab）
  - 檔案中第一個出現的 "R.Time (min)" 就是 PDA 3D 的表頭
    （原始檔在此之前還有 LC Status Trace 與 PDA Multi Chromatogram 兩段，會誤導解析器）
本轉換只保留 PDA 3D 區段並改成逗號分隔，數值一個都不動。
"""
import io, os, sys

SRC = "D:/claude/fishsauce_hplc_data"

def convert(src_path, dst_path):
    raw = io.open(src_path, encoding="cp950", errors="replace").read().splitlines()
    i = [k for k, l in enumerate(raw) if l.startswith("[PDA 3D]")]
    if not i:
        return None
    i = i[0]
    meta = {}
    j = i + 1
    while j < len(raw) and not raw[j].startswith("R.Time (min)"):
        if "\t" in raw[j]:
            k, *v = raw[j].split("\t")
            meta[k.strip()] = v[0].strip() if v else ""
        j += 1
    j += 1                                  # 跳過 "R.Time (min)" 那一行
    wl_row = raw[j].split("\t")             # 波長列（第一格是空的）
    nwl = int(meta.get("# of Wavelength Axis Points", 0))
    ntime = int(meta.get("# of Time Axis Points", 0))

    out = ["R.Time (min)"]
    out.append(",".join([""] + [c.strip() for c in wl_row[1:nwl + 1]]))
    n = 0
    for l in raw[j + 1:]:
        c = l.split("\t")
        if len(c) < 2: break
        try: float(c[0])
        except ValueError: break
        out.append(",".join(c[:nwl + 1]))
        n += 1
    io.open(dst_path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    return dict(time_points=n, wavelengths=nwl,
                t_start=meta.get("Start Time(min)"), t_end=meta.get("End Time(min)"),
                wl_start=meta.get("Start Wavelength(nm)"), wl_end=meta.get("End Wavelength(nm)"))


if __name__ == "__main__":
    dst_dir = sys.argv[1] if len(sys.argv) > 1 else "pda_out"
    os.makedirs(dst_dir, exist_ok=True)
    # 空白（blank）＋ 標準品 ＋ 一個檢出 SA 的樣品 ＋ 一個未檢出的樣品
    PICK = {"std 0.txt": "blank.txt", "std 0.25.txt": "std_0.25ppm.txt",
            "sample15.txt": "sample_positive.txt", "sample 1.txt": "sample_negative.txt"}
    for src, dst in PICK.items():
        info = convert(os.path.join(SRC, src), os.path.join(dst_dir, dst))
        if info:
            print(f"  {src:<16} -> {dst:<22} {info['time_points']} x {info['wavelengths']}"
                  f"  t {info['t_start']}-{info['t_end']} min  λ {info['wl_start']}-{info['wl_end']} nm")
        else:
            print(f"  {src:<16} 無 PDA 3D 區段，略過")
