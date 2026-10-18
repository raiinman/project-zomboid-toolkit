param(
    [string]$OutputDirectory = 'dist',
    [string]$SigningThumbprint = '',
    [string]$SignToolPath = '',
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

$ErrorActionPreference = 'Stop'
$originalPath = $env:PATH
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $outputPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
    $uv = (Get-Command uv -CommandType Application).Source
    & $uv sync --frozen --extra mcp --extra exe --python 3.11
    if ($LASTEXITCODE) { throw 'Dependency installation failed' }
    $python = [IO.Path]::GetFullPath('.venv/Scripts/python.exe')
    $runtime = (& $python -I -c 'import json,sys; print(json.dumps({"base":sys.base_prefix,"venv":sys.prefix}))') | ConvertFrom-Json
    if ($LASTEXITCODE -or !$runtime.base -or !$runtime.venv) { throw 'Cannot identify build interpreter' }
    # Exclude unrelated tool/native runtime directories from dependency lookup.
    $env:PATH = @((Join-Path $runtime.venv 'Scripts'), $runtime.base,
        (Join-Path $runtime.base 'DLLs'), (Join-Path $env:SystemRoot 'System32'),
        $env:SystemRoot) -join [IO.Path]::PathSeparator
    foreach ($app in @(@{Name='pz'; Entry='entry.py'; Mode='--console'},
                       @{Name='PZToolkit'; Entry='gui_entry.py'; Mode='--windowed'})) {
        & $python -I -m PyInstaller --noconfirm --clean --onedir --noupx $app.Mode --name $app.Name --paths src --collect-data pztoolkit --collect-data mcp --distpath $outputPath --specpath build --workpath build (Join-Path 'packaging' $app.Entry)
        if ($LASTEXITCODE) { throw "Build failed: $($app.Name)" }
    }
    & $python -I packaging/verify_origins.py --manifest build/pz/Analysis-00.toc --manifest build/pz/EXE-00.toc --manifest build/PZToolkit/Analysis-00.toc --manifest build/PZToolkit/EXE-00.toc --receipt (Join-Path $outputPath 'native-inputs.json')
    if ($LASTEXITCODE) { throw 'Native input provenance failed. Do not run or distribute this candidate.' }
    $bundlePath = Join-Path $outputPath 'pz-windows'
    if (Test-Path -LiteralPath $bundlePath) { throw 'Bundle already exists; use a fresh version/output directory' }
    $bundle = New-Item -ItemType Directory $bundlePath
    Copy-Item (Join-Path $outputPath 'pz'), (Join-Path $outputPath 'PZToolkit') -Destination $bundle.FullName -Recurse
    Copy-Item pztoolkit.example.json -Destination $bundle.FullName
    Copy-Item packaging/QUICKSTART.md -Destination (Join-Path $bundle.FullName 'README.md')
    $licenses = New-Item -ItemType Directory (Join-Path $bundle.FullName 'licenses')
    Copy-Item src/pztoolkit/assets/gui/fonts/OFL-Oxanium.txt -Destination $licenses.FullName
    $signing = 'unsigned'
    if ($SigningThumbprint) {
        & "$PSScriptRoot/sign.ps1" -BundlePath $bundle.FullName -Thumbprint $SigningThumbprint -SignToolPath $SignToolPath -TimestampUrl $TimestampUrl
        $signing = 'verified-authenticode'
    }
    $files = @(Get-ChildItem -LiteralPath $bundle.FullName -File -Recurse | ForEach-Object {
        @{path=[IO.Path]::GetRelativePath($bundle.FullName, $_.FullName); sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
    })
    Compress-Archive -Path "$($bundle.FullName)/*" -DestinationPath (Join-Path $outputPath 'pz-windows.zip')
    @{schema=1; signing=$signing; executionApproved=$false; files=$files; scan='required'; zipSha256=(Get-FileHash -LiteralPath (Join-Path $outputPath 'pz-windows.zip') -Algorithm SHA256).Hash} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $outputPath 'build-receipt.json') -Encoding utf8
    Write-Output "Candidate built ($signing). Run packaging/scan.ps1 before any executable probes. No antivirus clearance is implied."
} finally {
    $env:PATH = $originalPath
    Pop-Location
}
