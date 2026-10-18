"""Windowed entry point; console CLI and MCP remain in pz.exe."""

import sys

if sys.platform == "win32" and getattr(sys, "frozen", False):
    import ctypes

    # Keep the external game's DLL lookup independent of the frozen runtime.
    if not ctypes.windll.kernel32.SetDllDirectoryW(None):
        raise ctypes.WinError()

from pztoolkit.gui import main

if __name__ == "__main__":
    raise SystemExit(main())
