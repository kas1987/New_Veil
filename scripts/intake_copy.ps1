# Copy a relative path from a named source into 90_intake.
# Usage:
#   .\scripts\intake_copy.ps1 -Source viel_small_town -RelPath 12_metaphysics
#   .\scripts\intake_copy.ps1 -Source the_veil -RelPath design

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        'the_veil',
        'viel_small_town',
        'veil_core',
        'center_mass_games_veil',
        'center_mass_docs',
        'zelex_sigil_pack',
        'veil_design_skill'
    )]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$RelPath
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourcesPath = Join-Path $Root '90_intake\sources.json'
$map = Get-Content -LiteralPath $sourcesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$entry = $map.sources | Where-Object { $_.id -eq $Source } | Select-Object -First 1
if (-not $entry) { throw "Unknown source id: $Source" }

$src = Join-Path $entry.path $RelPath
if (-not (Test-Path -LiteralPath $src)) { throw "Missing source path: $src" }

$bucket = $entry.intake_bucket
$dest = Join-Path $Root "90_intake\$bucket\$RelPath"
$destParent = Split-Path $dest -Parent
New-Item -ItemType Directory -Path $destParent -Force | Out-Null
Copy-Item -LiteralPath $src -Destination $dest -Recurse -Force
Write-Host "Copied:`n  $src`n-> $dest"
Write-Host "Review, then promote keepers into the matching numbered plane."
