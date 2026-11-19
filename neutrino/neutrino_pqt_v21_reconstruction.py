import numpy as np
from scipy.linalg import eigh

# Experimental Targets
TH12 = np.radians(33.44)
TH23 = np.radians(49.2)
TH13 = np.radians(8.57)
RATIO = 0.0307 

def get_rotation_matrix(th12, th23, th13):
    s12, c12 = np.sin(th12), np.cos(th12)
    s23, c23 = np.sin(th23), np.cos(th23)
    s13, c13 = np.sin(th13), np.cos(th13)
    R12 = np.array([[c12, s12, 0], [-s12, c12, 0], [0, 0, 1]])
    R23 = np.array([[1, 0, 0], [0, c23, s23], [0, -s23, c23]])
    R13 = np.array([[c13, 0, s13], [0, 1, 0], [-s13, 0, c13]])
    return R23 @ R13 @ R12

def reconstruct_K(U, m1, m2, m3):
    D = np.diag([m1**2, m2**2, m3**2])
    return U @ D @ U.T

m3 = 50.0e-3
m2 = np.sqrt(RATIO * m3**2)
m1 = 1e-6

U_target = get_rotation_matrix(TH12, TH23, TH13)
K_target = reconstruct_K(U_target, m1, m2, m3)

print('TARGET K_target:')
print(K_target)

ev = np.linalg.eigvalsh(K_target)
print(f'Eigenvalues: {ev}')

# Linking Number approximation
_, evecs = eigh(K_target)
v3 = evecs[:, 2]
Lk = v3[0] * v3[1] * v3[2]
print(f'Lk Index: {Lk:.6f}')
