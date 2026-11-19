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
K_t = get_K(33.44, 49.2, 8.57)
K_v = get_K(32.9, 58.7, 8.5)
diff = K_t - K_v
print('GAP:')
print(diff)
ev, evc = eigh(diff)
print('EV:', ev)
