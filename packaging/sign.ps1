param(
    [Parameter(Mandatory)][string]$BundlePath,
    [Parameter(Mandatory)][string]$Thumbprint,
    [Parameter(Mandatory)][string]$SignToolPath,
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $SignToolPath -PathType Leaf)) { throw 'Provide the Windows SDK SignTool executable path' }
if ($Thumbprint -notmatch '^[a-fA-F0-9]{40}$') { throw 'Expected a certificate SHA-1 thumbprint, without spaces' }
$timestamp = [Uri]$TimestampUrl
if ($timestamp.Scheme -notin @('http','https') -or !$timestamp.Host) { throw 'Expected an RFC3161 timestamp service URL' }
$cert = $null
$machine = $false
foreach ($store in @('CurrentUser', 'LocalMachine')) {
    $candidate = Get-Item -LiteralPath "Cert:\$store\My\$Thumbprint" -ErrorAction SilentlyContinue
    if ($candidate) { $cert = $candidate; $machine = ($store -eq 'LocalMachine'); break }
}
if (!$cert -or !$cert.HasPrivateKey) { throw 'No matching signing certificate with private key. No self-signed certificate will be created.' }
$now = Get-Date
if ($cert.NotBefore -gt $now -or $cert.NotAfter -le $now) { throw 'Signing certificate is outside its validity interval' }
if ('1.3.6.1.5.5.7.3.3' -notin @($cert.EnhancedKeyUsageList | ForEach-Object { $_.ObjectId.Value })) { throw 'Certificate lacks Code Signing EKU' }
$chain = [Security.Cryptography.X509Certificates.X509Chain]::new()
try {
    $chain.ChainPolicy.RevocationMode = [Security.Cryptography.X509Certificates.X509RevocationMode]::Online
    $chain.ChainPolicy.ApplicationPolicy.Add([Security.Cryptography.Oid]::new('1.3.6.1.5.5.7.3.3'))
    if (!$chain.Build($cert)) { throw 'Certificate chain or revocation verification failed. No trust changes will be made.' }
} finally { $chain.Dispose() }
foreach ($relative in @('pz/pz.exe', 'PZToolkit/PZToolkit.exe')) {
    $exe = Join-Path $BundlePath $relative
    $arguments = @('sign', '/sha1', $Thumbprint, '/s', 'My', '/fd', 'SHA256', '/tr', $TimestampUrl, '/td', 'SHA256')
    if ($machine) { $arguments += '/sm' }
    & $SignToolPath @arguments $exe
    if ($LASTEXITCODE) { throw "Signing failed: $relative" }
    & $SignToolPath verify /pa /all /tw $exe
    if ($LASTEXITCODE) { throw "SignTool verification failed: $relative" }
    $signature = Get-AuthenticodeSignature -LiteralPath $exe
    if ($signature.Status -ne 'Valid' -or !$signature.TimeStamperCertificate -or $signature.SignerCertificate.Thumbprint -ne $Thumbprint) {
        throw "Trusted timestamped Authenticode signature not verified: $relative"
    }
}
Write-Output 'Both application entry points have verified timestamped Authenticode signatures. This does not guarantee an antivirus verdict.'
