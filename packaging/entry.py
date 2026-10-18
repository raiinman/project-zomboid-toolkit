"""Frozen console entry point, sharing the installed CLI implementation."""

import sys

# Child game processes must not inherit the bootloader's bundled DLL directory.
if sys.platform == "win32" and getattr(sys, "frozen", False):
    import ctypes

    if not ctypes.windll.kernel32.SetDllDirectoryW(None):
        raise ctypes.WinError()

from pztoolkit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
