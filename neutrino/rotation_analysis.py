import numpy as np
from scipy.linalg import eigh

TH12_V10 = np.radians(32.9)
TH23_V10 = np.radians(58.7)
TH13_V10 = np.radians(8.5)

TH12_EXP = np.radians(33.44)
TH23_EXP = np.radians(49.2)
TH13_EXP = np.radians(8.57)

def get_U(th12, th23, th13):
    s12, c12 = np.sin(th12), np.cos(th12)
    s23, c23 = np.sin(th23), np.cos(th23)
    s13, c13 = np.sin(th13), np.cos(th13)
    R12 = np.array([[c12, s12, 0], [-s12, c12, 0], [0, 0, 1]])
    R23 = np.array([[1, 0, 0], [0, c23, s23], [0, -s23, c23]])
    R13 = np.array([[c13, 0, s13], [0, 1, 0], [-s13, 0, c13]])
    return R23 @ R13 @ R12

if __name__ == "__main__":
    U_v10 = get_U(TH12_V10, TH23_V10, TH13_V10)
    U_exp = get_U(TH12_EXP, TH23_EXP, TH13_EXP)
    R = U_exp @ U_v10.T
    phi_rot = np.degrees(np.arctan2(R[1, 2], R[1, 1]))
    print(phi_rot)
    print(np.pi / np.radians(abs(phi_rot)))
