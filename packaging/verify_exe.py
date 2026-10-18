"""Smoke-test the frozen binary in a clean working directory with bundled assets."""

import asyncio
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def main():
    executable = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="pz-exe-") as directory:
        root = Path(directory)
        config = root / "config.json"
        config.write_text(json.dumps({"game_dir": str(root / "game"),
                                     "profile_dir": str(root / "profile"),
                                     "workspace_dir": str(root / "workspace")}), encoding="utf-8")

        def call(*args):
            result = subprocess.run([str(executable), "--config", str(config), *args],
                                    cwd=root, capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stderr
            return json.loads(result.stdout)

        schemas = call("tools")
        assert len(schemas) == 11
        assert any(tool["name"] == "lua_execute" for tool in schemas)
        assert not {"mod_create", "mod_check", "mod_deploy", "folders_detect", "harness_run", "profile_prepare"} & {
            tool["name"] for tool in schemas}
        call("call", "bridge_install")
        doctor = call("call", "doctor")
        bridge = root / "profile/mods/PZToolkitBridge"
        assert (bridge / "42/media/lua/client/PZToolkitBridge.lua").is_file()
        assert (bridge / "common/README.txt").is_file()

        async def protocol():
            params = StdioServerParameters(command=str(executable),
                                           args=["--config", str(config), "serve"], cwd=str(root))
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    remote = await session.list_tools()
                    assert {tool.name: tool.inputSchema for tool in remote.tools} == {
                        tool["name"]: tool["inputSchema"] for tool in schemas}
                    result = await session.call_tool("doctor", {})
                    assert not result.isError
                    assert json.loads(result.content[0].text) == doctor
                    assert (await session.call_tool("god_mode", {"enabled": 1})).isError

        asyncio.run(asyncio.wait_for(protocol(), timeout=60))
    print("Executable CLI, bundled bridge, MCP handshake, schemas and invocation passed")


if __name__ == "__main__":
    main()
