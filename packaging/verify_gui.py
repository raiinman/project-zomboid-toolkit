"""Verify the frozen app has a windowed PE header and boots real Tk widgets."""

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile


executable = Path(sys.argv[1]).resolve()
image = executable.read_bytes()
pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
assert image[:2] == b"MZ" and image[pe_offset:pe_offset + 4] == b"PE\0\0"
assert struct.unpack_from("<H", image, pe_offset + 24 + 68)[0] == 2, "Expected windowed GUI subsystem"

with tempfile.TemporaryDirectory(prefix="pz-gui-exe-") as directory:
    root = Path(directory)
    config = root / "config.json"
    config.write_text(json.dumps({"game_dir": "game", "workspace_dir": "workspace", "profile_dir": "profile"}))
    report = root / "smoke.json"
    result = subprocess.run([str(executable), "--config", str(config), "--smoke-report", str(report)],
                            cwd=root, timeout=60, capture_output=True)
    assert result.returncode == 0, result.stderr
    evidence = json.loads(report.read_text())
    assert evidence["ok"] and evidence["window_mapped"] and evidence["bridge_assets"], evidence
    assert evidence["branding_loaded"] and evidence["display_font"] == "Oxanium SemiBold", evidence
    assert evidence["tabs"] == ["Setup", "Mods", "In-game tests"]
    assert evidence["navigation"] == ["Mods", "In-game tests", "Setup"]
    assert evidence["guide_steps"] == 8
    assert evidence["setup_controls_fit"], "Setup buttons must fit at minimum window size"

print("Windowed executable, native widgets, background tool dispatch and bundled bridge passed")
