"""Require the exact candidate bundle's passing scan before frozen probes."""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import stat
import zipfile


def assert_scanned(executable, receipt_path):
    executable = Path(executable).absolute()
    report = json.loads(Path(receipt_path).read_text(encoding="utf-8-sig"))
    if (report.get("schema") != 1 or report.get("ok") is not True
            or report.get("executionApproved") is not True or report.get("scanExitCode") != 0):
        raise ValueError("A successful normal Defender scan receipt is required before executable probes")
    timestamp = datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - timestamp
    if not timedelta(0) <= age <= timedelta(days=1):
        raise ValueError("Scan receipt is stale or has a future timestamp")
    root = Path(report["bundlePath"]).absolute()
    archive = root.parent / "pz-windows.zip"
    completed = {Path(item["target"]).absolute() for item in report.get("scans", [])
                 if item.get("scanId") and item.get("endRecord", 0) > item.get("startRecord", 0) > 0}
    if completed != {root, archive}:
        raise ValueError("Scan completion evidence missing for bundle or ZIP")
    expected = {name.replace("\\", "/"): value.lower() for name, value in report["files"].items()}
    if not executable.is_relative_to(root) or executable.relative_to(root).as_posix() not in expected:
        raise ValueError("Executable was not part of the scanned bundle")
    actual = {}
    for path in [root, *root.rglob("*")]:
        if path.is_symlink() or (getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("Linked paths in scan bundle are not permitted")
        if path.is_file():
            with path.open("rb") as stream:
                actual[path.relative_to(root).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError("Bundle differs from the scanned files; do not execute")
    with archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != report["zipSha256"].lower():
            raise ValueError("ZIP differs from the scanned distribution")
    members = {}
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            if entry.is_dir():
                continue
            name = entry.filename.replace("\\", "/")
            if name in members or name not in expected:
                raise ValueError("Unexpected or duplicate ZIP member")
            with bundle.open(entry) as stream:
                members[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    if members != expected:
        raise ValueError("ZIP members differ from the scanned bundle")
