import numpy as np
from scipy.linalg import eigh

def get_K(th12_d, th23_d, th13_d):
    th12, th23, th13 = np.radians(th12_d), np.radians(th23_d), np.radians(th13_d)
    s12, c12 = np.sin(th12), np.cos(th12)
    s23, c23 = np.sin(th23), np.cos(th23)
    s13, c13 = np.sin(th13), np.cos(th13)
    R12 = np.array([[c12, s12, 0], [-s12, c12, 0], [0, 0, 1]])
    R23 = np.array([[1, 0, 0], [0, c23, s23], [0, -s23, c23]])
    R13 = np.array([[c13, 0, s13], [0, 1, 0], [-s13, 0, c13]])
    U = R23 @ R13 @ R12
    D = np.diag([1e-10, 0.00007675, 0.0025])
    return U @ D @ U.T

K_exp = get_K(33.44, 49.2, 8.57)
K_v10 = get_K(32.9, 58.7, 8.5)
gap = K_exp - K_v10
ev_gap, evec_gap = eigh(gap)

print('--- PQT MATRIX RECONSTRUCTION REPORT ---')
print(f'Trace(Gap): {np.trace(gap):.2e}')
print(f'Gap Eigenvalues: {ev_gap}')
print(f'Rotation Gap: {58.7 - 49.2:.2f} deg')
print(f'Ratio 180/Gap: {180.0/(58.7 - 49.2):.4f}')
ev_exp = np.linalg.eigvalsh(K_exp)
print(f'Target Eigenvalues: {ev_exp}')
