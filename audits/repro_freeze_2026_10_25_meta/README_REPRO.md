# PQT-AUDIT-001 · Reproducible Evidence Freeze · 2026-10-25

This is a frozen evidence bundle, not a release of PQT or a claim of physical validation.
Start with REPRO_INDEX.md, CLAIMS.json, RELEASE_NOTES.md and metadata/PRIMARY_SOURCE_GAPS.json.
CODEX and HIX historical files retain their separate authorship and exact bytes. Generated portable adapters are new Codex work.

## Offline Windows x64 setup

The recorded environment is CPython 3.14.4 x64. All 18 locked wheels, including pip, are included.
An optional **unexecuted** official CPython installer is in environment/python-installer; its SHA is in environment/PYTHON_INSTALLER.json and matches the official release-page digest.
It is a reproducibility bootstrap, not a recommendation to replace an existing Python installation. If needed, install it yourself to a chosen local folder without changing global PATH or enabling other options. Python is PSF-licensed; third-party licenses remain embedded in wheels.

Extract this bundle into a new location with enough room for the bundle, environment, outputs and a 10 GiB free-space reserve. Do not run in a canon/source directory. Replace the example paths below with your own. No automatic deletion or cleanup is performed.

```powershell
$Bundle = 'D:\PQT-reproduction\BUNDLE'
$TaskPython = 'D:\Python3144\python.exe'
# Standard-library-only SHA verification before dependency installation:
& $TaskPython -B "$Bundle\replay\verify_hashes.py"
# Create a new isolated environment from the bundled wheels, with no network:
& "$Bundle\setup_offline.ps1" -Python $TaskPython `
  -EnvironmentPath 'D:\PQT-reproduction\venv' -TempPath 'D:\PQT-reproduction\install-temp'
$ReplayPython = 'D:\PQT-reproduction\venv\Scripts\python.exe'
& "$Bundle\verify_hashes.ps1" -Python $ReplayPython
& "$Bundle\replay_all.ps1" -Python $ReplayPython -Mode quick `
  -Output 'D:\PQT-reproduction\quick-results-001'
& "$Bundle\replay_all.ps1" -Python $ReplayPython -Mode extended `
  -Output 'D:\PQT-reproduction\extended-results-001'
```

Choose new output directories for each run; the runner refuses overwrites and refuses outputs inside the immutable bundle.
If script execution is disabled by local PowerShell policy, invoke the same Python scripts directly; no machine policy changes are needed.
Direct equivalent: `python -B -X utf8 replay/replay.py --mode quick --output <new-external-folder>`.
The Windows-specific binary wheelhouse is not suitable for Linux/macOS. For another platform acquire the exact pinned package versions and archive its platform-specific wheel hashes separately.

## What quick and extended do

Quick reconstructs original v10 using an explicit safe AST subset, checks the 16D source reduction, rank/singular branches, old-basis dependence and symmetric projector identity, all eight mode-sign assignments, CP counterexamples, saved Bari SVG/PNG geometry, exact source EFT poles/residues, the exact HIX proposal on memory/copies only, API13 and V1 bitwise9/9, a negative-eigenvalue regression, reverse-patch rollback, frozen Cornell inputs, the integrity incident, and recorded fresh Wolfram results.

Extended additionally re-executes the archived Codex historical and Bari pseudo-fit/constraint protocols and HIX H4/H4B fit/constraint protocols with their original seeds/bounds/tolerances. It captures **every new HIX optimizer return**, including failure and infeasibility, in ALL_OPTIMIZER_RETURNS.json. Original historical files sometimes retained only best/feasible results; this gap is not silently filled by fresh results. Optimization minima remain SCAN_ONLY; tolerances and floating-point paths do not establish global optimality.

Machine-readable results are replay_results.json and replay_results.csv. Any unexpected assertion failure gives nonzero exit status. A test PASS may establish that a scientific claim FAIL is correctly reproduced; inspect CLAIMS.json rather than treating test success as physical acceptance.
The packed clean extended run passed 10 groups / 227 adapter assertions. Source Wolfram checks are counted separately; the Python group verifying their records is not a second kernel execution.

## Wolfram

Nine authoritative WL input files and the original historical tool responses are preserved. They were freshly re-executed through the connected Wolfram service for this freeze: 187 boolean checks, with kernel metadata in environment/WOLFRAM_CURRENT_KERNEL.json and complete responses in validation/wolfram.
That current version must not be backdated to the earlier historical calls. Some historical attempts contain diagnostics or failed/truncated formatting; the authoritative files are listed by replay_wolfram.ps1.

No Wolfram binaries, credentials or license are shipped. Fresh local-kernel replay is SKIPPED unless you provide a separately licensed kernel. With a working `wolframscript`:

```powershell
& "$Bundle\replay_wolfram.ps1" -WolframScript 'C:\path\wolframscript.exe' `
  -Output 'D:\PQT-reproduction\wolfram-results-001'
```

Inspect the boolean maps, not just the process exit code. `0.e-55` in a Wolfram RawJSON response is a zero with a nonstandard JSON spelling; the frozen parser changes only that numeric spelling to `0e-55`. Raw responses remain unchanged.

## Evidence boundaries

Do not execute all historical Python scripts directly: several contain absolute historical paths, top-level scans or downloads. Only the portable adapters are designed for isolated offline replay. Source snapshots are data, not permission to write canon or run production.
Bari inputs are the archived preliminary release, not live/current measurements. Marginal graphical estimates, correlated-contour membership and a true joint likelihood are distinct. No exact official 2D chi-square, calibrated 99.73% two-dof exclusion, global no-go or whole-PQT rejection is asserted.

H2E remains proposal-only. The runner verifies patch application and rollback in isolated memory/output copies. No original source is changed, and no activation, release or merge is authorized.

The Round4 Markdown integrity exception is quarantined with both variants, neutral UNKNOWN change provenance, exact reconstructed original digest and diff. Historical conclusions must be read with errata and the later reports.
Original neutrino/scalar sources and contributor directories were not edited by this packaging task.

## Integrity and final report

EVIDENCE_MANIFEST.json enumerates every payload file except itself and MANIFEST.sha256. MANIFEST.sha256 contains the evidence-manifest digest; its own digest and the ZIP digest are in the external acceptance packet and NLA Forum. This explicit self-exclusion avoids impossible circular self-hashes.
The external FINAL_REPRO_FREEZE_REPORT.md records the final ZIP path/SHA and post-extraction verification. The ZIP has deterministic entry timestamps and contains this self-contained index and the recorded validation. Its checksum is necessarily supplied outside the ZIP.
Do not alter a freeze in place. Any future correction belongs in a new version/addendum with new hashes.
