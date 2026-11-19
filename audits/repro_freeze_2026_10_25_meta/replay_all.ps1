param(
    [ValidateSet('quick','extended')][string]$Mode = 'quick',
    [string]$Python = 'python',
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
& $Python -B (Join-Path $PSScriptRoot 'replay\verify_hashes.py')
if ($LASTEXITCODE -ne 0) { throw 'Bundle integrity verification failed' }
& $Python -B -X utf8 (Join-Path $PSScriptRoot 'replay\replay.py') --mode $Mode --output $Output
if ($LASTEXITCODE -ne 0) { throw 'Scientific replay failed; inspect replay_results.json' }
