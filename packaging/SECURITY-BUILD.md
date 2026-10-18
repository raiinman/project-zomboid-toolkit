# Windows candidate build and signing

Use PowerShell 7 in clean Windows CI from reviewed source and the frozen lockfile. The build
uses separate one-folder native applications with UPX disabled. It deliberately
rejects native inputs from unrelated tools or the Codex/libheif runtime.

```powershell
./packaging/build.ps1 -OutputDirectory dist
./packaging/scan.ps1 -BundlePath dist/pz-windows -BuildReceipt dist/build-receipt.json -ReceiptPath dist/scan-receipt.json
uv run --no-sync python packaging/verify_exe.py dist/pz-windows/pz/pz.exe dist/scan-receipt.json
uv run --no-sync python packaging/verify_gui.py dist/pz-windows/PZToolkit/PZToolkit.exe dist/scan-receipt.json
```

`build.ps1` produces `pz-windows.zip`, `build-receipt.json` (file hashes and
actual signing status) and `native-inputs.json` (native origin/hashes/rejections).
The scan helper performs an ordinary Defender custom scan with default
remediation. It never disables protection, adds exclusions or restores files.
`scan-receipt.json` grants executable probes only after active/current Defender,
successful scan completion, no new/changed detections and unchanged bundle
hashes. It correlates new Defender event 1000/1001 records by Scan ID and exact
scan target, rejecting cancelled/failed scans and unknown event schemas.
Missing/unknown scanner state fails closed. Probe helpers verify all
bundle hashes and a receipt no older than 24 hours before launching anything.
Receipts and scan logs contain local paths; keep them in ignored build output
and restricted CI diagnostics, outside the distributed ZIP and public commits.

Upload binary candidate artifacts only after these gates. Failures may upload
receipts/logs for review, never the failed binaries. A passing scan is a
point-in-time observation, not proof that a previous detection was false.

Signing is separately optional. No signing identity is currently provisioned.
An unsigned candidate must remain labelled unsigned. To sign after acquiring
a trusted Code Signing identity:

```powershell
./packaging/build.ps1 -OutputDirectory dist -SigningThumbprint '<certificate thumbprint>' -SignToolPath '<Windows SDK x64 SignTool path>'
```

The hook requires a private key, Code Signing EKU, valid certificate dates,
trusted chain and online revocation verification. It signs both entry points
using SHA-256 and an RFC3161 SHA-256 timestamp, verifies with SignTool `/pa`,
and requires a valid timestamped Authenticode signature from that identity.
Existing third-party runtime signatures are preserved. It never creates a
self-signed certificate or changes machine trust. Cloud or hardware signing
providers must expose a compatible installed key provider; enrollment and costs
need separate user handling. Signing must happen before scanning and final ZIP
hash verification. Signing does not guarantee Defender acceptance.

Keep quarantined v0.4.1 artifacts quarantined. Do not repeatedly repackage them
until a scan passes. Disputing a detection requires a developer submission and
Microsoft's determination; no private sample upload is part of these scripts.

Sources: [Microsoft developer guidance](https://learn.microsoft.com/en-us/defender-xdr/developer-faq),
[SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool),
[PyInstaller options](https://pyinstaller.org/en/stable/usage.html).
