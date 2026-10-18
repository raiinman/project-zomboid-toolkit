param([string]$OutputDirectory = 'dist')

$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $outputPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputDirectory))
    uv sync --frozen --extra mcp --extra exe --python 3.11
    if ($LASTEXITCODE) { throw 'Dependency installation failed' }
    uv run --no-sync pyinstaller --noconfirm --clean --onefile --console --name pz --paths src --collect-data pztoolkit --collect-data mcp --distpath $outputPath --specpath build packaging/entry.py
    if ($LASTEXITCODE) { throw 'Executable build failed' }
    uv run --no-sync pyinstaller --noconfirm --clean --onefile --windowed --name PZToolkit --paths src --collect-data pztoolkit --distpath $outputPath --specpath build packaging/gui_entry.py
    if ($LASTEXITCODE) { throw 'Desktop application build failed' }
    $bundle = New-Item -ItemType Directory -Force (Join-Path $outputPath 'pz-windows')
    Copy-Item (Join-Path $outputPath 'pz.exe'), (Join-Path $outputPath 'PZToolkit.exe'), pztoolkit.example.json -Destination $bundle.FullName -Force
    Copy-Item examples -Destination $bundle.FullName -Recurse -Force
    Copy-Item packaging/QUICKSTART.md -Destination (Join-Path $bundle.FullName 'README.md') -Force
    $licenses = New-Item -ItemType Directory -Force (Join-Path $bundle.FullName 'licenses')
    Copy-Item src/pztoolkit/assets/gui/fonts/OFL-Oxanium.txt -Destination $licenses.FullName -Force
    Compress-Archive -Path "$($bundle.FullName)/*" -DestinationPath (Join-Path $outputPath 'pz-windows.zip') -Force
} finally {
    Pop-Location
}
