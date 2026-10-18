"""CLI adapter for the shared tool registry."""

import argparse
import json
from pathlib import Path
import sys

from .core import Toolkit


def main() -> int:
    parser = argparse.ArgumentParser(description="Project Zomboid MCP, CLI, and in-game mod harness")
    parser.add_argument("--config", default="pztoolkit.local.json", help="Path to toolkit JSON configuration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tools", help="List shared tool names, descriptions, and JSON input schemas")
    call = commands.add_parser("call", help="Invoke any shared tool")
    call.add_argument("tool")
    inputs = call.add_mutually_exclusive_group()
    inputs.add_argument("--args", default="{}", help="JSON object containing tool arguments")
    inputs.add_argument("--args-file", help="UTF-8 JSON argument file, avoiding shell quoting")
    commands.add_parser("serve", help="Run the MCP server over stdio")
    args = parser.parse_args()
    try:
        toolkit = Toolkit(args.config)
        if args.command == "serve":
            from .server import serve
            serve(toolkit)
            return 0
        if args.command == "tools":
            result = toolkit.schemas()
        else:
            raw = args.args
            if args.args_file:
                path = Path(args.args_file)
                if path.stat().st_size > 65536:
                    raise ValueError("Argument file exceeds 64 KiB")
                raw = path.read_text(encoding="utf-8-sig")
            result = toolkit.call(args.tool, json.loads(raw))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if isinstance(result, dict) and result.get("ok") is False else 0
    except (OSError, ValueError, ImportError) as exc:
        print(json.dumps({"error": {"message": str(exc)}}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
