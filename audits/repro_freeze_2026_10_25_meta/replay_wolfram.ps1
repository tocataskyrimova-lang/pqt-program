param(
    [string]$WolframScript = 'wolframscript',
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Output) { throw 'Choose a new Output directory' }
New-Item -ItemType Directory -Path $Output | Out-Null
$Files = @(
 'evidence\CODEX\HIX_REVIEW\REVIEW_CHECKS.wl',
 'evidence\CODEX\NEUTRINO_SOURCE_REPLAY\NEUTRINO_REPLAY.wl',
 'evidence\CODEX\NEUTRINO_SOURCE_REPLAY\STRUCTURE_CHECKS.wl',
 'evidence\CODEX\ROUND3_COMPLEX_PHASE\COMPLEX_LITERAL_REPLAY.wl',
 'evidence\CODEX\ROUND3_COMPLEX_PHASE\PROJECTOR_AND_PHASE_PROOFS.wl',
 'evidence\CODEX\ROUND3_COMPLEX_PHASE\FIXED90_COUNTEREXAMPLE.wl',
 'evidence\CODEX\ROUND4_CP_RESIDUES\CP_REPLAY.wl',
 'evidence\CODEX\ROUND4_CP_RESIDUES\EFT_RESIDUES_EXACT.wl',
 'evidence\CODEX\ROUND5_2D_AND_SOURCE_POLES\GEOMETRY_AND_SOURCE_POLES.wl'
)
foreach ($File in $Files) {
    $Name = $File.Replace('\','__') + '.txt'
    & $WolframScript -file (Join-Path $PSScriptRoot $File) 2>&1 | Out-File -LiteralPath (Join-Path $Output $Name) -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw ('Kernel execution failed: ' + $File) }
}
# Read boolean check maps in outputs. An exit code alone is not scientific PASS.
