"""Security receipts and provenance checks, never execute fixture PE contents."""

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_helper(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "packaging" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


origins = load_helper("verify_origins")
scan = load_helper("require_scan")


def manifest(tmp_path, inputs):
    path = tmp_path / "Analysis-00.toc"
    path.write_text(repr(([], inputs)), encoding="utf-8")
    return path


def test_native_origin_gate_hashes_allowed_inputs_and_rejects_outside(tmp_path):
    runtime = tmp_path / "python"
    runtime.mkdir()
    dll = runtime / "python311.dll"
    dll.write_bytes(b"fixture runtime")
    outside = tmp_path / "unrelated.dll"
    outside.write_bytes(b"unrelated")
    report = origins.inspect([manifest(tmp_path, [
        (dll.name, str(dll), "BINARY"), (outside.name, str(outside), "BINARY")
    ])], [runtime])
    assert report["ok"] is False
    assert report["inputs"][0]["sha256"] == hashlib.sha256(b"fixture runtime").hexdigest()
    assert [item["name"] for item in report["rejected"]] == ["unrelated.dll"]


@pytest.mark.parametrize("relative", ["codex-primary-runtime/a.dll", "native/libheif/bin/a.dll"])
def test_known_polluted_origins_rejected_even_under_allowed_root(tmp_path, relative):
    dll = tmp_path / relative
    dll.parent.mkdir(parents=True)
    dll.write_bytes(b"not executed")
    report = origins.inspect([manifest(tmp_path, [(dll.name, str(dll), "EXTENSION")])], [tmp_path])
    assert report["ok"] is False


def test_origin_gate_fails_closed_for_missing_inputs_and_empty_manifests(tmp_path):
    report = origins.inspect([manifest(tmp_path, [("a.dll", str(tmp_path / "a.dll"), "BINARY")])], [tmp_path])
    assert report["ok"] is False
    with pytest.raises(ValueError, match="No native inputs"):
        origins.inspect([manifest(tmp_path, [])], [tmp_path])
    with pytest.raises(ValueError, match="No PyInstaller"):
        origins.inspect([], [tmp_path])


def scanned_fixture(tmp_path):
    root = tmp_path / "bundle"
    exe = root / "pz/pz.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"fixture, not executable")
    support = root / "pz/_internal/python311.dll"
    support.parent.mkdir()
    support.write_bytes(b"fixture dependency")
    report = {"schema": 1, "ok": True, "executionApproved": True, "scanExitCode": 0,
              "timestamp": datetime.now(timezone.utc).isoformat(), "bundlePath": str(root),
              "files": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in [exe, support]}}
    archive = root.parent / "pz-windows.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for path in [exe, support]:
            bundle.write(path, path.relative_to(root).as_posix())
    report["zipSha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    report["scans"] = [{"target": str(target), "scanId": str(index), "startRecord": 1, "endRecord": 2}
                       for index, target in enumerate([root, archive])]
    receipt = tmp_path / "scan.json"
    receipt.write_text(json.dumps(report))
    return exe, support, receipt, report


def test_scan_receipt_accepts_exact_complete_bundle(tmp_path):
    exe, _, receipt, _ = scanned_fixture(tmp_path)
    scan.assert_scanned(exe, receipt)


@pytest.mark.parametrize("field,value", [("ok", False), ("executionApproved", False),
                                        ("schema", 2), ("scanExitCode", 2)])
def test_scan_receipt_rejects_failed_or_unknown_verdict(tmp_path, field, value):
    exe, _, receipt, report = scanned_fixture(tmp_path)
    report[field] = value
    receipt.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Defender scan receipt"):
        scan.assert_scanned(exe, receipt)


@pytest.mark.parametrize("change", ["executable", "support", "removed", "injected"])
def test_scan_receipt_rejects_any_bundle_mutation(tmp_path, change):
    exe, support, receipt, _ = scanned_fixture(tmp_path)
    if change == "executable":
        exe.write_bytes(b"changed")
    elif change == "support":
        support.write_bytes(b"changed")
    elif change == "removed":
        support.unlink()
    else:
        (support.parent / "injected.dll").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="differs"):
        scan.assert_scanned(exe, receipt)


def test_scan_receipt_rejects_stale_scan_and_unscanned_executable(tmp_path):
    exe, _, receipt, report = scanned_fixture(tmp_path)
    outside = tmp_path / "other.exe"
    with pytest.raises(ValueError, match="not part"):
        scan.assert_scanned(outside, receipt)
    report["timestamp"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    receipt.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="stale"):
        scan.assert_scanned(exe, receipt)


def test_scan_receipt_rejects_mutated_archive(tmp_path):
    exe, _, receipt, _ = scanned_fixture(tmp_path)
    (tmp_path / "pz-windows.zip").write_bytes(b"replacement archive")
    with pytest.raises(ValueError, match="ZIP differs"):
        scan.assert_scanned(exe, receipt)


def test_scan_receipt_requires_correlated_completion_for_both_targets(tmp_path):
    exe, _, receipt, report = scanned_fixture(tmp_path)
    report["scans"].pop()
    receipt.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="completion"):
        scan.assert_scanned(exe, receipt)


@pytest.mark.parametrize("mutation", ["content", "extra", "duplicate"])
def test_scan_receipt_rejects_archive_member_drift_even_with_updated_zip_hash(tmp_path, mutation):
    exe, support, receipt, report = scanned_fixture(tmp_path)
    archive = tmp_path / "pz-windows.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("pz/pz.exe", b"tampered" if mutation == "content" else exe.read_bytes())
        bundle.writestr("pz/_internal/python311.dll", support.read_bytes())
        if mutation == "extra":
            bundle.writestr("extra.dll", b"unexpected")
        elif mutation == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate name"):
                bundle.writestr("pz/pz.exe", exe.read_bytes())
    report["zipSha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    receipt.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="ZIP"):
        scan.assert_scanned(exe, receipt)
