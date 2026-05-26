import numpy as np

for v in ['left', 'center', 'right']:
    vec = np.load(f'baselines/corp-baselines/{v}-corpus-vector.npy')
    if np.isnan(vec).any():
        print(f"{v}-corpus-vector contains NaNs!")
    else:
        print(f"{v}-corpus-vector is clean.")