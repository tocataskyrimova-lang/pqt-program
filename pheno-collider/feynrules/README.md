# FeynRules Model Definitions & UFO Export Scripts (`pheno-collider/feynrules`)

## 1. Overview & Provenance
This directory contains the theoretical FeynRules Lagrangian definitions and Mathematica export scripts for the Prema-Quantum Theory (PQT) memory sector in the mass eigenstate basis.

* **Source Archive:** Recovered from `C:\AGIOLD\AGI\` during the November 2026 repository audit.
* **Model Files:**
  - `PQT_MemorySector_massbasis.fr`: Standalone mass-basis scalar model definition with light scalar $S$ (PDG 9000006) and heavy scalar $H_2$ (PDG 9000007), including gauge and Yukawa coupling specifications.
  - `PQT_MemorySector_massbasis_SMext.fr`: Standard Model extension file designed to load alongside FeynRules Standard Model (`SM.fr`). Implements $SZZ$, $SW^+W^-$, $H_2ZZ$, and $H_2W^+W^-$ vertices for Vector Boson Fusion (VBF) phenomenology.
* **Export Scripts:**
  - `export_sm_pqt_ufo.wls`: WolframScript batch job to load `SM.fr` + `PQT_MemorySector_massbasis_SMext.fr` and output the combined Universal FeynRules Output (UFO) format.
  - `export_massbasis_ufo.wls`: Standalone export script for mass-basis UFO generation.
  - `validate_ufo_massbasis.py`: Pre-flight audit script checking particle codes and coupling symbols.

## 2. Requirements for UFO Regeneration
To re-export the UFO model from these `.fr` sources:
1. **Wolfram Mathematica / Wolfram Engine** with `wolframscript` CLI available on PATH.
2. **FeynRules 2.3.49+** installed (historically located at `C:\AGIOLD\AGI\feynrules-current\`).
3. Execution command:
   ```bash
   wolframscript -file export_sm_pqt_ufo.wls <path_to_feynrules> <path_to_model_dir> <output_ufo_dir>
   ```

## 3. Epistemic Claim Boundaries
These source files define the tree-level interaction vertices and kinetic terms for theoretical simulation in MadGraph5_aMC@NLO. They do not constitute experimental validation or claim LHC exclusion limits without detector simulation (Delphes) and full statistical analysis.
