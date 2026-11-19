# UFO Model: `PQT_MemorySector_massbasis`

## 1. Overview
This package is the Universal FeynRules Output (UFO) representation of the Standard Model extended with the Prema-Quantum Theory (PQT) memory sector in the mass eigenstate basis. It is directly loadable by MadGraph5_aMC@NLO (`import model PQT_MemorySector_massbasis`).

* **Provenance:** Generated via FeynRules from `SM.fr` + `PQT_MemorySector_massbasis_SMext.fr` (recovered from `C:\AGIOLD\AGI\UFO\PQT_MemorySector_massbasis`).
* **Python Compatibility:** Python 2.7 and Python 3.8+ (validated up to Python 3.14).

## 2. Particle Content
The model includes the complete Standard Model spectrum (43 SM particles including gauge bosons, quarks, leptons, and ghosts) plus two physical scalar states:
- **`S`** (PDG `9000006`): Light physical memory scalar ($M_S$, default $200.0\text{ GeV}$).
- **`H2`** (PDG `9000007`): Heavy physical scalar ($M_{H2}$, default $700.0\text{ GeV}$).

## 3. Key Parameters & Vertices
- **Parameters:**
  - `sint` (`sinth`): Mixing angle parameter $\sin\theta$, default $0.01$.
  - `cost` (`costh`): Derived parameter $\cos\theta = \sqrt{1 - \sin^2\theta}$.
  - `MS`, `MH2`: Scalar masses (GeV).
  - `WS`, `WH2`: Decay widths (GeV, default `Auto` in `restrict_default.dat`).
- **Interaction Vertices (157 total):**
  - SM electroweak, QCD, and Higgs vertices (153).
  - PQT extension vertices (4):
    - `V_154`: $S - Z - Z$ with coupling `GC_PQT_1 = i * sint * (2 * MZ^2 / vev)`
    - `V_155`: $S - W^- - W^+$ with coupling `GC_PQT_2 = i * sint * (2 * MW^2 / vev)`
    - `V_156`: $H_2 - Z - Z$ with coupling `GC_PQT_3 = i * cost * (2 * MZ^2 / vev)`
    - `V_157`: $H_2 - W^- - W^+$ with coupling `GC_PQT_4 = i * cost * (2 * MW^2 / vev)`

## 4. Restriction Cards
- `restrict_default.dat`: Sets `DECAY 9000006 Auto` and `DECAY 9000007 Auto`, enabling automatic tree-level partial width calculations within MadGraph5.
