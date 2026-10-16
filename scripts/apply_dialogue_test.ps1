param(
    [Parameter(Mandatory=$true,Position=0)][string]$SourceRom,
    [Parameter(Position=1)][string]$OutputRom = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Get-BytesSha256([byte[]]$Bytes) {
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}
try {
    $sourcePath = (Get-Item -LiteralPath $SourceRom).FullName
    $patchPath = Join-Path $PSScriptRoot 'TinyToon_dialogue_full.ips'
    if ([string]::IsNullOrWhiteSpace($OutputRom)) { $OutputRom = Join-Path $PSScriptRoot 'output\TinyToon_ko_test_006.nes' }
    $outputPath = [IO.Path]::GetFullPath($OutputRom)
    $receiptPath = $outputPath + '.apply.json'
    if ((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $receiptPath)) { throw 'Output already exists. Select a new output path.' }
    if ($outputPath -eq $sourcePath) { throw 'Source and output paths must differ.' }
    $sourceBytes = [IO.File]::ReadAllBytes($sourcePath)
    $sourceHash = Get-BytesSha256 $sourceBytes
    if ($sourceBytes.Length -ne 262160 -or $sourceHash -ne '73300dc1505564827ef95ba3e2a06c26aa48920e4981195f32b2101c185ef3dd') { throw 'Unsupported source ROM. The required Japan ROM SHA-256 is listed in README_KO.md.' }
    $patchBytes = [IO.File]::ReadAllBytes($patchPath)
    $patchHash = Get-BytesSha256 $patchBytes
    if ($patchHash -ne 'ff6b10f01a323519780bcc2a3f320de8a7ec4a426df00088fc12fbc496f4826c') { throw 'Patch hash mismatch. Restore the test package.' }
    if ([Text.Encoding]::ASCII.GetString($patchBytes,0,5) -ne 'PATCH') { throw 'Invalid IPS header.' }
    [byte[]]$targetBytes = New-Object byte[] 524304
    [Array]::Copy($sourceBytes,0,$targetBytes,0,$sourceBytes.Length)
    $pos = 5; $currentLength = $sourceBytes.Length; $previousEnd = 0; $records = 0
    while ($true) {
        if ($pos + 3 -gt $patchBytes.Length) { throw 'Missing IPS EOF.' }
        if ([Text.Encoding]::ASCII.GetString($patchBytes,$pos,3) -eq 'EOF') { $pos += 3; break }
        if ($pos + 5 -gt $patchBytes.Length) { throw 'Truncated IPS record header.' }
        $offset = [int]$patchBytes[$pos]*65536 + [int]$patchBytes[$pos+1]*256 + [int]$patchBytes[$pos+2]
        $size = [int]$patchBytes[$pos+3]*256 + [int]$patchBytes[$pos+4]; $pos += 5
        if ($size -eq 0 -or $pos + $size -gt $patchBytes.Length) { throw 'Invalid or unsupported RLE record.' }
        if ($offset -lt $previousEnd -or $offset -gt $currentLength -or $offset + $size -gt $targetBytes.Length) { throw 'Overlapping or out-of-range IPS write.' }
        [Array]::Copy($patchBytes,$pos,$targetBytes,$offset,$size)
        $pos += $size; $previousEnd = $offset + $size; $currentLength = [Math]::Max($currentLength,$previousEnd); $records++
    }
    if ($pos -ne $patchBytes.Length -or $currentLength -ne $targetBytes.Length) { throw 'IPS final size or trailer mismatch.' }
    $outputHash = Get-BytesSha256 $targetBytes
    if ($outputHash -ne '6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d') { throw 'Applied ROM hash mismatch. No output was written.' }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
    $stream = [IO.File]::Open($outputPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($targetBytes,0,$targetBytes.Length) } finally { $stream.Dispose() }
    if ((Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $outputHash) { throw 'Written file verification failed.' }
    $receipt = [ordered]@{ status='PASS'; scope='Local test package; full gameplay and final translation review pending'; source_sha256=$sourceHash; patch_sha256=$patchHash; output_sha256=$outputHash; output_size=$targetBytes.Length; IPS_records=$records }
    $receiptBytes = [Text.Encoding]::UTF8.GetBytes(($receipt | ConvertTo-Json) + [Environment]::NewLine)
    $stream = [IO.File]::Open($receiptPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $stream.Write($receiptBytes,0,$receiptBytes.Length) } finally { $stream.Dispose() }
    Write-Host ('PASS: ' + $outputPath)
    Write-Host ('SHA-256: ' + $outputHash)
    exit 0
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message)
    exit 1
}
