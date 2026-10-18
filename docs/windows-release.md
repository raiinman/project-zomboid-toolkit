# Windows distribution

Version 0.4.1 is blocked after Defender quarantined its CLI as
`Trojan:Win32/Bearfoos.A!ml`. The classification is not established as a false
positive. Preserve quarantine and do not add exclusions or install trust roots.
Passing functional tests or matching release hashes does not clear a detection.

The build audit found 43 native dependencies collected from a Codex runtime
outside the locked Python environment. This is a provenance defect, not proof
of malware or a confirmed explanation for the detection.

## Candidate workflow

1. Build reviewed source and locked dependencies in a fresh Windows CI runner
   with a controlled build path. Enforce native dependency origin checks.
2. Package ordinary one-folder GUI and CLI applications with support files.
   Users still open native EXEs without a separate Python installation.
3. If a trusted signing identity is available, sign the final executable bytes
   with SHA-256 and an RFC 3161 timestamp; verify Authenticode trust. Otherwise
   mark the candidate unsigned. Do not generate a self-signed trust workaround.
4. Scan the exact candidate with ordinary Defender protection. Missing scanner,
   inactive protection, new detections or changed/removed files block execution.
5. Run executable probes only after the scan gate. Retain provenance, hashes,
   signature state and scan receipts with the candidate.
6. Verify the same bundle on the actual PC before installation and repeat the
   ordinary scan there. A clean result is evidence for those bytes at that time,
   not a guarantee against later detections.

If clean CI cannot meet the active/current Defender prerequisite before scanning,
the private workflow may retain a two-day `UNSCANNED-security-staging-<commit>`
artifact for scanning on the user's PC. CI remains failed, executable probes stay
blocked, and no release or installation is approved by this artifact. Other scan
failures are ineligible. The same exact-bundle and ZIP gate must pass on the PC
before execution or installation. Command-line maintenance must not control the
mouse, activate windows or launch the GUI while the user is working.

Do not upload private binaries or source to review services without explicit
authorization. Microsoft accepts developer submissions for disputed detections;
the affected old build stays blocked pending a determination.

## Signing prerequisite

The PC has the Windows SDK SignTool but no code-signing certificate with a
private key. The user confirmed there is no existing signing identity.
Trusted signing needs publisher enrollment with a certificate authority or
signing service. Identity verification, account creation and any billing remain
user steps. Do not claim the app is signed until verification actually passes.

Microsoft explains that consistent trusted signing helps identify a publisher
but does not guarantee antivirus acceptance. SmartScreen reputation and Defender
malware detection are separate systems.

- [Microsoft developer FAQ](https://learn.microsoft.com/en-us/defender-xdr/developer-faq)
- [SignTool signing and verification](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Microsoft Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/overview)
- [PyInstaller distribution options](https://pyinstaller.org/en/stable/usage.html)
