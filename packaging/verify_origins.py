"""Inspect PyInstaller input manifests without loading bundled code or binaries."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys


NATIVE_TYPES = {"BINARY", "EXTENSION", "EXECUTABLE"}


def native_entries(value):
    if isinstance(value, (tuple, list)):
        if (len(value) == 3 and all(isinstance(item, str) for item in value)
                and value[2] in NATIVE_TYPES):
            yield value
        else:
            for item in value:
                yield from native_entries(item)


def inspect(manifests, allowed_roots):
    roots = [Path(root).resolve() for root in allowed_roots]
    if not roots:
        raise ValueError("No trusted native input roots supplied")
    records, rejected = [], []
    for manifest in manifests:
        entries = list(native_entries(ast.literal_eval(Path(manifest).read_text(encoding="utf-8"))))
        if not entries:
            raise ValueError(f"No native inputs found in {manifest}")
        for name, source, kind in entries:
            path = Path(source).resolve()
            folded = str(path).replace("\\", "/").casefold()
            permitted = any(path.is_relative_to(root) for root in roots)
            if "codex-primary-runtime" in folded or "/libheif/" in folded:
                permitted = False
            record = {"name": name, "source": str(path), "kind": kind}
            if not permitted or not path.is_file():
                rejected.append({**record, "reason": "Unexpected or missing native input"})
            else:
                with path.open("rb") as stream:
                    record["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
            records.append(record)
    if not records:
        raise ValueError("No PyInstaller manifests supplied")
    return {"ok": not rejected, "allowed_roots": [str(root) for root in roots],
            "inputs": records, "rejected": rejected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    system = Path(os.environ["SystemRoot"])
    roots = [sys.prefix, sys.base_prefix, system / "System32", system / "SysWOW64", system / "WinSxS"]
    try:
        report = inspect(args.manifest, roots)
    except (ValueError, OSError, SyntaxError) as exc:
        report = {"ok": False, "error": str(exc)}
    Path(args.receipt).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report["ok"]:
        print(f"Native dependency gate failed. Review {args.receipt}; use a clean Python environment and PATH.", file=sys.stderr)
        return 1
    print(f"Native dependency origins verified: {len(report['inputs'])} inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
