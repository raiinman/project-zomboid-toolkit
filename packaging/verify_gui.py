"""Map fixture Tk widgets on CI; frozen candidates additionally require a scan."""

import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from require_scan import assert_scanned


source_mode = sys.argv[1:] == ["--source"]
if source_mode:
    command = [sys.executable, "-m", "pztoolkit.gui"]
else:
    executable = Path(sys.argv[1]).resolve()
    assert_scanned(executable, sys.argv[2])
    image = executable.read_bytes()
    pe_offset = struct.unpack_from("<I", image, 0x3C)[0]
    assert image[:2] == b"MZ" and image[pe_offset:pe_offset + 4] == b"PE\0\0"
    assert struct.unpack_from("<H", image, pe_offset + 24 + 68)[0] == 2, "Expected windowed GUI subsystem"
    command = [str(executable)]

with tempfile.TemporaryDirectory(prefix="pz-gui-exe-") as directory:
    root = Path(directory)
    config = root / "config.json"
    config.write_text(json.dumps({"game_dir": "game", "workspace_dir": "workspace", "profile_dir": "profile"}))
    report = root / "smoke.json"
    result = subprocess.run([*command, "--config", str(config), "--smoke-report", str(report)],
                            cwd=root, timeout=60, capture_output=True)
    assert result.returncode == 0, result.stderr
    evidence = json.loads(report.read_text())
    assert evidence["ok"] and evidence["window_mapped"] and evidence["bridge_assets"], evidence
    assert evidence["branding_loaded"] and evidence["display_font"] == "Oxanium SemiBold", evidence
    assert evidence["tabs"] == ["Offline tools", "Connection", "Game tools"]
    assert evidence["navigation"] == ["Offline tools", "Connection", "Game tools"]
    assert evidence["default_page"] == "Offline tools" and not evidence["profile_created"], evidence
    assert evidence["details_collapsed"]
    assert set(evidence["tools"]) == {"doctor", "bridge_install", "game_launch", "bridge_status", "logs_read", "source_search", "source_read", "lua_execute", "god_mode", "debug_editors", "editor_open"}
    assert all(evidence["bounds"].values()), evidence

print("Offline-first mapped GUI, control bounds, shared registry and bundled bridge passed")
