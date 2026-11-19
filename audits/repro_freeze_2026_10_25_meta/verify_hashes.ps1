param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python -B (Join-Path $PSScriptRoot 'replay\verify_hashes.py')
if ($LASTEXITCODE -ne 0) { throw 'Bundle integrity verification failed' }
