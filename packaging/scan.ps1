param(
    [Parameter(Mandatory)][string]$BundlePath,
    [Parameter(Mandatory)][string]$BuildReceipt,
    [Parameter(Mandatory)][string]$ReceiptPath
)
# Ordinary Defender custom scan. Never change protection or remediation settings.
$ErrorActionPreference = 'Stop'
$report = @{schema=1; ok=$false; executionApproved=$false; timestamp=[DateTime]::UtcNow.ToString('o')}
function Get-BundleHashes([string]$Root) {
    $result = @{}
    $rootItem = Get-Item -LiteralPath $Root -Force
    if ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked bundle root is not permitted' }
    foreach ($file in Get-ChildItem -LiteralPath $Root -Force -Recurse) {
        if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked bundle files are not permitted' }
        if ($file.PSIsContainer) { continue }
        $relative = [IO.Path]::GetRelativePath($Root, $file.FullName)
        $result[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
    if (!$result.Count) { throw 'Bundle is empty' }
    return $result
}
function Assert-Zip([string]$ZipPath, $Expected, [string]$Hash) {
    if ($Hash -notmatch '^[A-Fa-f0-9]{64}$' -or (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash -ne $Hash) { throw 'ZIP differs from build receipt' }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zipFile = [IO.Compression.ZipFile]::OpenRead($ZipPath)
    $seen = @{}
    try {
        foreach ($entry in $zipFile.Entries) {
            if ($entry.FullName.EndsWith('/')) { continue }
            $name = $entry.FullName.Replace('/', [IO.Path]::DirectorySeparatorChar)
            if (!$Expected.ContainsKey($name) -or $seen.ContainsKey($name)) { throw "Unexpected or duplicate ZIP member: $name" }
            $stream = $entry.Open()
            $hashAlgorithm = [Security.Cryptography.SHA256]::Create()
            try { $entryHash = [Convert]::ToHexString($hashAlgorithm.ComputeHash($stream)) }
            finally { $stream.Dispose(); $hashAlgorithm.Dispose() }
            if ($entryHash -ne $Expected[$name]) { throw "ZIP member differs from bundle: $name" }
            $seen[$name] = $true
        }
        if ($seen.Count -ne $Expected.Count) { throw 'ZIP is missing bundle files' }
    } finally { $zipFile.Dispose() }
}
function Assert-Hashes($Actual, $Expected) {
    if ($Actual.Count -ne $Expected.Count) { throw 'Bundle file list changed or does not match build receipt' }
    foreach ($name in $Expected.Keys) {
        if (!$Actual.ContainsKey($name) -or $Actual[$name] -ne $Expected[$name]) { throw "Missing or changed bundle file: $name" }
    }
}
function Get-DetectionKeys {
    return @(Get-MpThreatDetection -ErrorAction Stop | ForEach-Object {
        "$($_.DetectionID)|$($_.ThreatID)|$($_.InitialDetectionTime.ToUniversalTime().ToString('o'))|$($_.LastThreatStatusChangeTime.ToUniversalTime().ToString('o'))"
    })
}
function Get-CompletedScan([long]$AfterRecord, [string]$Target) {
    $log = 'Microsoft-Windows-Windows Defender/Operational'
    $xpath = "*[System[(EventRecordID > $AfterRecord) and (EventID=1000 or EventID=1001 or EventID=1002 or EventID=1005)]]"
    for ($attempt = 0; $attempt -lt 5; $attempt++) {
        try { $eventRecords = @(Get-WinEvent -LogName $log -FilterXPath $xpath -ErrorAction Stop) }
        catch {
            if ($_.FullyQualifiedErrorId -notlike 'NoMatchingEventsFound*') { throw }
            $eventRecords = @()
        }
        $events = @($eventRecords | ForEach-Object {
            $xml = [xml]$_.ToXml()
            $data = @{}
            foreach ($field in $xml.Event.EventData.Data) { $data[$field.Name] = $field.'#text' }
            @{record=$_.RecordId; event=$_.Id; data=$data}
        })
        $start = @($events | Where-Object {
            $_.event -eq 1000 -and $_.data['Scan ID'] -and
            $_.data['Scan Resources'].Trim().TrimEnd('\','/') -eq $Target.TrimEnd('\','/')
        } | Sort-Object record -Descending | Select-Object -First 1)
        if ($start.Count) {
            $scanId = $start[0].data['Scan ID']
            $matching = @($events | Where-Object { $_.data['Scan ID'] -eq $scanId -and $_.record -gt $start[0].record })
            if (@($matching | Where-Object { $_.event -in @(1002,1005) }).Count) { throw 'Defender scan was cancelled or failed according to its event log' }
            $end = @($matching | Where-Object { $_.event -eq 1001 } | Select-Object -First 1)
            if ($end.Count) { return @{target=$Target; scanId=$scanId; startRecord=$start[0].record; endRecord=$end[0].record} }
        }
        Start-Sleep -Milliseconds 200
    }
    throw 'Cannot correlate Defender scan-start and scan-complete events for the exact target; verdict unknown'
}
try {
    $bundle = [IO.Path]::GetFullPath($BundlePath)
    $receipt = Get-Content -LiteralPath $BuildReceipt -Raw | ConvertFrom-Json
    if ($receipt.schema -ne 1 -or !$receipt.files) { throw 'Unknown or empty build receipt' }
    $expected = @{}
    foreach ($file in $receipt.files) {
        if (!$file.path -or $file.sha256 -notmatch '^[A-Fa-f0-9]{64}$' -or $expected.ContainsKey($file.path)) { throw 'Invalid build file receipt' }
        $expected[$file.path] = $file.sha256
    }
    $before = Get-BundleHashes $bundle
    Assert-Hashes $before $expected
    $zip = Join-Path (Split-Path $bundle -Parent) 'pz-windows.zip'
    Assert-Zip $zip $expected $receipt.zipSha256
    $status = Get-MpComputerStatus -ErrorAction Stop
    if (!$status.AMServiceEnabled -or !$status.AntivirusEnabled -or !$status.RealTimeProtectionEnabled -or $status.AMRunningMode -ne 'Normal' -or $status.DefenderSignaturesOutOfDate) {
        throw 'Defender must be active in Normal mode with current signatures; scan verdict is unknown'
    }
    if (!$status.AntivirusSignatureVersion -or !$status.AntivirusSignatureLastUpdated) { throw 'Defender signature state unavailable' }
    $report.defender = @{mode=$status.AMRunningMode; engine=$status.AMEngineVersion; signature=$status.AntivirusSignatureVersion; signatureUpdated=$status.AntivirusSignatureLastUpdated.ToUniversalTime().ToString('o')}
    $detectionsBefore = @(Get-DetectionKeys)
    $platform = Join-Path $env:ProgramData 'Microsoft/Windows Defender/Platform'
    $scanner = @(Get-ChildItem -LiteralPath $platform -Filter MpCmdRun.exe -File -Recurse -ErrorAction Stop | Sort-Object FullName -Descending | Select-Object -First 1)
    if (!$scanner) { throw 'Defender command-line scanner unavailable; no execution permitted' }
    $scannerPath = $scanner[0].FullName
    $scannerSignature = Get-AuthenticodeSignature -LiteralPath $scannerPath
    if ($scannerSignature.Status -ne 'Valid' -or $scannerSignature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') { throw 'Cannot verify Microsoft Defender scanner publisher' }
    $scanOutput = @()
    $report.scans = @()
    foreach ($target in @($bundle, $zip)) {
        $lastEvent = Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents 1 -ErrorAction Stop
        if (!$lastEvent) { throw 'Defender operational event log unavailable' }
        $scanOutput += & $scannerPath -Scan -ScanType 3 -File $target 2>&1
        $scanExit = $LASTEXITCODE
        if ($scanExit -ne 0) { break }
        $report.scans += Get-CompletedScan $lastEvent.RecordId $target
    }
    $scanOutput | Out-String | Set-Content -LiteralPath "$ReceiptPath.log" -Encoding utf8
    $report.scanExitCode = $scanExit
    if ($scanExit -ne 0) { throw "Defender scan did not return a clean completion (exit $scanExit)" }
    $detectionsAfter = @(Get-DetectionKeys)
    $newDetections = @($detectionsAfter | Where-Object { $_ -notin $detectionsBefore })
    if ($newDetections.Count) { $report.newDetections=$newDetections; throw 'Defender recorded a new or changed detection during scanning' }
    $after = Get-BundleHashes $bundle
    Assert-Hashes $after $expected
    $afterStatus = Get-MpComputerStatus -ErrorAction Stop
    if (!$afterStatus.AntivirusEnabled -or !$afterStatus.RealTimeProtectionEnabled -or $afterStatus.AMRunningMode -ne 'Normal') { throw 'Protection changed during scanning' }
    $report.files = $after
    $report.signing = $receipt.signing
    $report.bundlePath = $bundle
    Assert-Zip $zip $expected $receipt.zipSha256
    $report.zipSha256 = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
    $report.ok = $true
    $report.executionApproved = $true
} catch {
    $report.error = $_.Exception.Message
} finally {
    if ($scanOutput) { $scanOutput | Out-String | Set-Content -LiteralPath "$ReceiptPath.log" -Encoding utf8 }
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding utf8
}
if (!$report.ok) { throw "Security scan gate failed: $($report.error). Review $ReceiptPath. Do not run this candidate." }
Write-Output 'Normal Defender scan completed without new detections or changed bundle files. This records a point-in-time result, not a safety guarantee.'
