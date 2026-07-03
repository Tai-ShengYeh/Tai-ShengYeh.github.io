# Orange Data Mining 教學：NIR calibration transfer（Corn dataset）

檔案：`corn_nir_for_orange.csv`

## 建議 workflow（手動拖拉，不需寫程式）

1. **File**：載入 `corn_nir_for_orange.csv`。
2. **Select Columns**：
   - Features：所有 `wl_1100` 到 `wl_2498`。
   - Target：`Protein`（或 Moisture/Oil/Starch）。
   - Meta：`sample_id`, `instrument`。
3. **Data Table**：檢查 240 rows = 80 samples × 3 instruments。
4. **PCA**：用 `instrument` 著色，觀察 instrument shift。
5. **Data Sampler / Select Rows**：分出 m5 建模資料與 mp5/mp6 測試資料。
6. **Continuize + Preprocess Spectra（若有 Orange Spectroscopy add-on）**：可做 SNV、Savitzky–Golay。
7. **PLS Regression / Linear Regression / Random Forest**：先在 m5 建模，再用 mp5 測試，觀察誤差增加。
8. **Calibration transfer 概念活動**：Orange GUI 不易完整實作 PDS；請搭配 Python notebook 的 DS/PDS 程式，讓學生比較「視覺化探索」與「演算法實作」各自適合的工具。

## Orange 課堂重點

- Orange 很適合教 PCA、儀器差異視覺化、欄位角色、train/test 分割。
- PDS/DS 屬於矩陣轉換演算法，建議在 Python 實作後，把轉換後 CSV 再匯回 Orange 做視覺化。
