# Neutrino Physics & Formalization Package (`neutrino/`)

This directory contains computational scripts, analytical reductions, and formal documentation for the Process Quantum Theory neutrino mass matrix, PMNS mixing angles, and renormalization group (RG) flow.

---

## 1. Overview of Key Components

* **Mass-Basis Operators & Parameter Scans:**
  - `neutrino_pqt_v10.py` / `neutrino_pqt_v20.py`: Mass matrix reconstruction, singular value decomposition (SVD), normal ordering verification, and mixing angle extractions.
  - `neutrino_pqt_audit.py` / `neutrino_pqt_calc.py`: Automated consistency audits and high-precision calculations.
  - `pqt_emergent_metric.py`: Mapping from neutrino mass matrix geometry to emergent spacetime metric perturbations.
* **Renormalization Group (RG) Evolution:**
  - `pqt_neutrino_rg_v2.py`: One-loop running of neutrino masses and mixing parameters from GUT/high scales down to the electroweak scale.
* **Documentation & Results:**
  - `PQT_NEUTRINO_RESULTS_v1.md`, `PQT_NEUTRINO_RG_RESULTS.md`: Detailed tables of mass eigenvalues, $\Delta m_{21}^2$, $\Delta m_{31}^2$, and PMNS angles ($\theta_{12}, \theta_{23}, \theta_{13}, \delta_{\text{CP}}$).
  - `PQT_FULL_FORMALIZATION_v1.md`: Axiomatic mathematical write-up.
  - `PQT_AUDIT_MANIFEST_v1.json`: Cryptographic integrity hashes of the formalization package.
