import numpy as np
from scipy.linalg import eigh

TH12 = np.radians(33.44)
TH13 = np.radians(8.57)
RATIO = 0.0307 

def get_U(th23_deg):
    th23 = np.radians(th23_deg)
    s12, c12 = np.sin(TH12), np.cos(TH12)
    s23, c23 = np.sin(th23), np.cos(th23)
    s13, c13 = np.sin(TH13), np.cos(TH13)
    R12 = np.array([[c12, s12, 0], [-s12, c12, 0], [0, 0, 1]])
    R23 = np.array([[1, 0, 0], [0, c23, s23], [0, -s23, c23]])
    R13 = np.array([[c13, 0, s13], [0, 1, 0], [-s13, 0, c13]])
    return R23 @ R13 @ R12

m3 = 50.0e-3
m2 = np.sqrt(RATIO * m3**2)
m1 = 1e-6

for th in np.linspace(54.0, 56.0, 11):
    U = get_U(th)
    K = U @ np.diag([m1**2, m2**2, m3**2]) @ U.T
    _, evecs = eigh(K)
    v3 = evecs[:, 2]
    Lk = v3[0] * v3[1] * v3[2]
    print(f'th23={th:6.2f} | Lk={Lk:10.6f}')
