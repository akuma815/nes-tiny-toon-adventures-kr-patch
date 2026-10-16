param([string]$RomPath)
$ErrorActionPreference = 'Stop'
try {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $manifestPath = Join-Path $projectRoot 'manifests/source_rom.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.schema_version -ne 1 -or $manifest.sha256 -notmatch '^[0-9a-fA-F]{64}$' -or $manifest.size_bytes -le 0) {
        throw 'Invalid source manifest.'
    }
    if ([string]::IsNullOrWhiteSpace($RomPath)) {
        $RomPath = Join-Path $projectRoot $manifest.path
    }
    $rom = Get-Item -LiteralPath $RomPath
    if ($rom.PSIsContainer) { throw 'ROM path must be a file.' }
    if ($rom.Length -ne $manifest.size_bytes) { throw "Source size mismatch: $($rom.Length)" }
    $actualHash = (Get-FileHash -LiteralPath $rom.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $manifest.sha256) { throw "Source SHA-256 mismatch: $actualHash" }
    [ordered]@{
        status = 'PASS'
        path = $rom.FullName
        size_bytes = $rom.Length
        sha256 = $actualHash
        scope = 'Source identity only; no build or runtime verification.'
    } | ConvertTo-Json
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
