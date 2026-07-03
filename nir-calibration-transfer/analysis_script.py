
import pathlib, urllib.request, zipfile
import numpy as np
import pandas as pd
import scipy.io as sio
from scipy.signal import savgol_filter
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

BASE = pathlib.Path('/home/administrator/nir_calibration_transfer_teaching') if pathlib.Path('/home/administrator/nir_calibration_transfer_teaching').exists() else pathlib.Path('.')
DATA = BASE/'data'
OUT = BASE/'outputs'
DATA.mkdir(exist_ok=True, parents=True); OUT.mkdir(exist_ok=True, parents=True)

url = 'https://eigenvector.com/wp-content/uploads/2019/06/corn.mat_.zip'
zip_path = DATA/'corn.mat_.zip'
mat_path = DATA/'corn.mat'
if not mat_path.exists():
    urllib.request.urlretrieve(url, zip_path)
    with zipfile.ZipFile(zip_path) as z: z.extractall(DATA)

mat = sio.loadmat(mat_path, squeeze_me=True, struct_as_record=False)
wavelengths = np.arange(1100, 2500, 2)
instruments = ['m5', 'mp5', 'mp6']
X = {inst: mat[f'{inst}spec'].data.astype(float) for inst in instruments}
y_names = ['Moisture','Oil','Protein','Starch']
y = pd.DataFrame(mat['propvals'].data.astype(float), columns=y_names)
y.insert(0, 'sample_id', np.arange(1, len(y)+1))

def export_wide_csv(path):
    rows=[]
    for inst in instruments:
        df = pd.DataFrame(X[inst], columns=[f'wl_{int(w)}' for w in wavelengths])
        df.insert(0,'instrument',inst)
        df.insert(0,'sample_id',np.arange(1,81))
        for c in y_names: df[c]=y[c]
        rows.append(df)
    all_df = pd.concat(rows, ignore_index=True)
    all_df.to_csv(path, index=False)
    return all_df
all_df = export_wide_csv(DATA/'corn_nir_3instruments_wide.csv')
# Orange-friendly: put target and meta columns first; wavelength columns are continuous features.
all_df.to_csv(BASE/'orange'/'corn_nir_for_orange.csv', index=False)

def snv(A):
    return (A - A.mean(axis=1, keepdims=True)) / A.std(axis=1, keepdims=True)

def preprocess(A):
    # smoothing + SNV: classroom-friendly baseline, not claimed as universally optimal
    return snv(savgol_filter(A, window_length=15, polyorder=2, axis=1))

def rmsep(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

# Teaching split: master calibration, transfer standards, slave independent test.
cal_idx = np.arange(0,50)       # build model on master m5
std_idx = np.arange(50,60)      # paired transfer standards, no y needed for DS/PDS
test_idx = np.arange(60,80)     # independent slave test
response = 'Protein'
yv = y[response].to_numpy()

Xm5 = preprocess(X['m5']); Xmp5 = preprocess(X['mp5']); Xmp6 = preprocess(X['mp6'])

pls = PLSRegression(n_components=8, scale=False)
pls.fit(Xm5[cal_idx], yv[cal_idx])
base_pred = pls.predict(Xmp5[test_idx]).ravel()

# Direct Standardization (global linear map): slave -> master using transfer standards.
def fit_ds(Xs_std, Xm_std, alpha=1e-6):
    # Add intercept column; solve ridge least-squares B where [Xs,1] @ B ~= Xm
    Xaug = np.c_[Xs_std, np.ones(Xs_std.shape[0])]
    I = np.eye(Xaug.shape[1]); I[-1,-1] = 0
    B = np.linalg.solve(Xaug.T @ Xaug + alpha*I, Xaug.T @ Xm_std)
    return B

def apply_ds(Xs, B):
    return np.c_[Xs, np.ones(Xs.shape[0])] @ B

Bds = fit_ds(Xmp5[std_idx], Xm5[std_idx], alpha=1e-3)
mp5_ds_test = apply_ds(Xmp5[test_idx], Bds)
ds_pred = pls.predict(mp5_ds_test).ravel()

# Piecewise Direct Standardization: local wavelength windows. Uses ridge because standard count is small.
def fit_pds(Xs_std, Xm_std, half_window=3, alpha=1e-3):
    n_features = Xs_std.shape[1]
    models = []
    for j in range(n_features):
        lo, hi = max(0, j-half_window), min(n_features, j+half_window+1)
        Xloc = np.c_[Xs_std[:, lo:hi], np.ones(Xs_std.shape[0])]
        I = np.eye(Xloc.shape[1]); I[-1,-1] = 0
        coef = np.linalg.solve(Xloc.T @ Xloc + alpha*I, Xloc.T @ Xm_std[:, j])
        models.append((lo, hi, coef))
    return models

def apply_pds(Xs, models):
    out = np.empty((Xs.shape[0], len(models)))
    for j, (lo, hi, coef) in enumerate(models):
        out[:, j] = np.c_[Xs[:, lo:hi], np.ones(Xs.shape[0])] @ coef
    return out

pds_models = fit_pds(Xmp5[std_idx], Xm5[std_idx], half_window=4, alpha=1e-2)
mp5_pds_test = apply_pds(Xmp5[test_idx], pds_models)
pds_pred = pls.predict(mp5_pds_test).ravel()

# Optional: slope/bias correction uses y for standards, so label as response-level correction.
std_pred = pls.predict(Xmp5[std_idx]).ravel()
slope, intercept = np.polyfit(std_pred, yv[std_idx], 1)
sbc_pred = slope * base_pred + intercept

results = pd.DataFrame({
    'method': ['No transfer: m5 model -> mp5 spectra', 'SBC: slope/bias on standard predictions', 'DS: direct standardization spectra', 'PDS: piecewise direct standardization spectra'],
    'needs_paired_spectra': ['No', 'Yes', 'Yes', 'Yes'],
    'needs_y_for_standards': ['No', 'Yes', 'No', 'No'],
    'RMSEP_protein': [rmsep(yv[test_idx], base_pred), rmsep(yv[test_idx], sbc_pred), rmsep(yv[test_idx], ds_pred), rmsep(yv[test_idx], pds_pred)],
    'R2_test': [r2_score(yv[test_idx], base_pred), r2_score(yv[test_idx], sbc_pred), r2_score(yv[test_idx], ds_pred), r2_score(yv[test_idx], pds_pred)]
})
results.to_csv(OUT/'calibration_transfer_results.csv', index=False)

# Figures
plt.figure(figsize=(9,5))
for inst, A in [('m5',X['m5']),('mp5',X['mp5']),('mp6',X['mp6'])]:
    plt.plot(wavelengths, A[:10].T, alpha=0.25, lw=0.8)
plt.xlabel('Wavelength (nm)'); plt.ylabel('Absorbance')
plt.title('Corn NIR spectra from three instruments: raw examples')
plt.tight_layout(); plt.savefig(OUT/'raw_spectra_examples.png', dpi=160); plt.close()

plt.figure(figsize=(6,6))
truth = yv[test_idx]
for label, pred, marker in [('No transfer',base_pred,'o'),('SBC',sbc_pred,'s'),('DS',ds_pred,'^'),('PDS',pds_pred,'x')]:
    plt.scatter(truth, pred, label=label, alpha=0.8, marker=marker)
lo, hi = min(truth.min(), base_pred.min(), ds_pred.min(), pds_pred.min()), max(truth.max(), base_pred.max(), ds_pred.max(), pds_pred.max())
plt.plot([lo,hi],[lo,hi],'k--',lw=1)
plt.xlabel('Reference protein (%)'); plt.ylabel('Predicted protein (%)')
plt.title('Slave instrument mp5 test prediction')
plt.legend(); plt.tight_layout(); plt.savefig(OUT/'prediction_comparison.png', dpi=160); plt.close()

print('Dataset rows:', all_df.shape[0], 'columns:', all_df.shape[1])
print('Wavelengths:', wavelengths[0], wavelengths[-1], len(wavelengths))
print(results.to_string(index=False))
