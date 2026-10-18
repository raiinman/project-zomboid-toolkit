"""Offline Lua 5.1 API mocks, not evidence of a running PZ client."""

import json
from pathlib import Path

import pytest
from lupa.lua51 import LuaRuntime


SOURCE = (
    Path(__file__).parents[1]
    / "src/pztoolkit/assets/bridge/42/media/lua/client/PZToolkitBridge.lua"
)
REQUEST_ID = "1234567890abcdef1234567890abcdef"


@pytest.fixture
def bridge():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(
        """
        files = { ['pzt-token.txt'] = 'secret' }
        now = 1000000
        debug_enabled = true
        multiplayer = false
        server = false
        player_present = true
        closed_handles = 0
        open_handles = 0
        printed = {}
        function print(value) printed[#printed + 1] = value end
        function getTimestampMs() return now end
        function getDebug() return debug_enabled end
        function isClient() return multiplayer end
        function isServer() return server end
        function make_player()
            return {
                god_mode = false, god_mode_calls = 0,
                setGodMod = function(self, value)
                    self.god_mode_calls = self.god_mode_calls + 1
                    if self.set_error then error(self.set_error) end
                    if not self.ignore_set then self.god_mode = value end
                end,
                isGodMod = function(self)
                    if self.read_error then error(self.read_error) end
                    return self.god_mode
                end
            }
        end
        player = make_player()
        function getPlayer() if player_present then return player end end
        function getSpecificPlayer(id) if id == 0 then return getPlayer() end end
        function getCore() return {getVersion = function() return '42.20.0' end} end
        function getFileReader(path)
            local value = files[path]
            if value == nil then return nil end
            open_handles = open_handles + 1
            local offset = 1
            return {
                readLine = function()
                    if offset > #value then return nil end
                    local ending = value:find('\\n', offset, true)
                    local line = value:sub(offset, ending and ending - 1 or #value)
                    offset = ending and ending + 1 or #value + 1
                    return line
                end,
                close = function() closed_handles = closed_handles + 1 end
            }
        end
        function getFileWriter(path)
            -- The installed game's writer rejects JSON file extensions.
            if not path:match('%.txt$') then return nil end
            open_handles = open_handles + 1
            return {
                write = function(self, value) files[path] = value end,
                close = function() closed_handles = closed_handles + 1 end
            }
        end
        Events = {
            OnTick = { Add = function(fn) tick = fn end },
            OnCreatePlayer = { Add = function(fn) create_player = fn end }
        }
        """
    )
    lua.execute(SOURCE.read_text(encoding="utf-8"))
    return lua


def request(bridge, source="return 'passed'", token="secret", expiry=1005000, ident=REQUEST_ID):
    bridge.globals().files["pzt-request.txt"] = f"{token}\n{ident}\n{expiry}\n{source}"
    bridge.globals().tick()
    value = bridge.globals().files["pzt-response.txt"]
    return json.loads(value) if value else None


@pytest.mark.parametrize(
    ("source", "ok", "message"),
    [
        ("return 'passed'", True, "passed"),
        ("return false", False, "scenario returned false"),
        ("error('exploded')", False, "runtime error:"),
        ("local = broken syntax", False, "syntax error:"),
        ("return nil", True, "nil"),
    ],
)
def test_scenario_results(bridge, source, ok, message):
    result = request(bridge, source)
    assert result["id"] == REQUEST_ID
    assert result["ok"] is ok
    assert message in result["message"]
    assert bridge.globals().open_handles == bridge.globals().closed_handles
    assert list(bridge.globals().printed.values()) == [
        f"[PZToolkitBridge] BEGIN {REQUEST_ID}",
        f"[PZToolkitBridge] END {REQUEST_ID} {str(ok).lower()}",
    ]


@pytest.mark.parametrize("expiry", [999999, 1000000, "NaN", "inf", "missing"])
def test_expired_or_invalid_request_never_executes(bridge, expiry):
    result = request(bridge, "executed = true", expiry=expiry)
    assert result["ok"] is False
    assert bridge.globals().executed is None


@pytest.mark.parametrize("token", ["", "incorrect"])
def test_authentication_precedes_execution(bridge, token):
    assert request(bridge, "executed = true", token=token) is None
    assert bridge.globals().executed is None
    assert len(bridge.globals().printed) == 0


def test_token_is_read_fresh(bridge):
    request(bridge, "executed = true", token="incorrect")
    bridge.globals().files["pzt-token.txt"] = "incorrect"
    bridge.globals().now += 200
    assert request(bridge, "executed = true", token="secret") is None
    assert bridge.globals().executed is None


@pytest.mark.parametrize("token", [None, ""])
def test_missing_or_empty_token_disables_bridge(bridge, token):
    bridge.globals().files["pzt-token.txt"] = token
    assert request(bridge, "executed = true", token="") is None
    assert bridge.globals().executed is None
    assert json.loads(bridge.globals().files["pzt-status.txt"])["ready"] is False


@pytest.mark.parametrize(
    ("setting", "reason"),
    [
        ("debug_enabled", "debug mode required"),
        ("multiplayer", "single-player world required"),
        ("server", "single-player world required"),
        ("player_present", "player not loaded"),
    ],
)
def test_execution_requires_local_debug_player(bridge, setting, reason):
    bridge.globals()[setting] = setting in {"multiplayer", "server"}
    assert request(bridge, "executed = true") is None
    assert bridge.globals().executed is None
    status = json.loads(bridge.globals().files["pzt-status.txt"])
    assert status["ready"] is False
    assert status["reason"] == reason


@pytest.mark.parametrize("ident", ["", "../bad", "f" * 33, "G" * 32])
def test_invalid_id_rejected(bridge, ident):
    assert request(bridge, "executed = true", ident=ident) is None
    assert bridge.globals().executed is None


def test_replay_never_executes_twice(bridge):
    request(bridge, "count = (count or 0) + 1")
    bridge.globals().now += 200
    request(bridge, "count = (count or 0) + 1")
    assert bridge.globals().count == 1


def test_expired_request_cannot_be_refreshed_with_same_id(bridge):
    request(bridge, "executed = true", expiry=999999)
    bridge.globals().now += 200
    request(bridge, "executed = true")
    assert bridge.globals().executed is None


def test_size_limit_closes_reader_without_execution(bridge):
    assert request(bridge, "executed = true --" + "x" * 65536) is None
    assert bridge.globals().executed is None
    assert bridge.globals().open_handles == bridge.globals().closed_handles


def test_json_escaping_and_status(bridge):
    result = request(bridge, r'''return 'quote" slash\\ tab\t newline\n byte\001' ''')
    assert result["message"] == 'quote" slash\\ tab\t newline\n byte\x01'
    status = json.loads(bridge.globals().files["pzt-status.txt"])
    assert status == {
        "ready": True,
        "timestamp_ms": 1000000,
        "build": "42.20.0",
        "lua_compiler": True,
        "debug": True,
        "single_player": True,
        "player_loaded": True,
        "god_mode": True,
        "reason": "ready",
    }


def test_missing_compiler_reports_unavailable_without_executing(bridge):
    bridge.globals().loadstring = None
    assert request(bridge, "executed = true") is None
    assert bridge.globals().executed is None
    status = json.loads(bridge.globals().files["pzt-status.txt"])
    assert status["ready"] is False
    assert status["lua_compiler"] is False
    assert status["reason"] == "Lua compiler unavailable"


def test_protocol_uses_allowed_text_extension_with_json_content(bridge):
    assert bridge.globals().getFileWriter("pzt-response.json") is None
    assert bridge.globals().getFileWriter("pzt-status.json") is None
    assert request(bridge)["ok"] is True
    assert json.loads(bridge.globals().files["pzt-status.txt"])["ready"] is True


@pytest.mark.parametrize(
    "source",
    ["return string.rep('x', 1048577)", "error(string.rep('x', 1048577))"],
)
def test_oversized_scenario_results_are_explicit_failures(bridge, source):
    result = request(bridge, source)
    assert result == {
        "id": REQUEST_ID,
        "ok": False,
        "message": "scenario result exceeds 32768 bytes",
    }
    assert len(bridge.globals().files["pzt-response.txt"].encode("utf-8")) < 1024


def status(bridge):
    bridge.globals().now += 1000
    bridge.globals().tick()
    return json.loads(bridge.globals().files["pzt-status.txt"])


def test_startup_god_mode_handles_spawn_respawn_and_index_only_event(bridge):
    state = bridge.globals()
    state.create_player(0, state.player)
    assert state.player.god_mode is True
    assert state.player.god_mode_calls == 1
    state.tick()
    assert state.player.god_mode_calls == 1
    bridge.execute("player = make_player()")
    state.create_player(0)
    assert state.player.god_mode is True
    assert state.player.god_mode_calls == 1
    assert status(bridge)["god_mode"] is True


def test_startup_tick_fallback_and_bridge_reload(bridge):
    state = bridge.globals()
    state.tick()
    assert state.player.god_mode is True
    assert state.player.god_mode_calls == 1
    bridge.execute("player.god_mode = false")
    bridge.execute(SOURCE.read_text(encoding="utf-8"))
    state.tick()
    assert state.player.god_mode is True
    assert state.player.god_mode_calls == 2


def test_manual_god_mode_disable_survives_ticks_and_duplicate_spawn_event(bridge):
    state = bridge.globals()
    state.create_player(0, state.player)
    bridge.execute("player.god_mode = false")
    state.create_player(0, state.player)
    assert status(bridge)["god_mode"] is False
    assert state.player.god_mode_calls == 1


@pytest.mark.parametrize("guard", ["debug", "client", "server", "player", "token", "empty_token"])
def test_god_mode_requires_authenticated_local_debug_player(bridge, guard):
    state = bridge.globals()
    if guard == "debug":
        state.debug_enabled = False
    elif guard == "client":
        state.multiplayer = True
    elif guard == "server":
        state.server = True
    elif guard == "player":
        state.player_present = False
    else:
        state.files["pzt-token.txt"] = "" if guard == "empty_token" else None
    state.create_player(0)
    assert status(bridge)["god_mode"] is False
    assert state.player.god_mode_calls == 0
    assert state.player.god_mode is False


def test_guard_can_become_ready_after_creation(bridge):
    state = bridge.globals()
    state.files["pzt-token.txt"] = None
    state.create_player(0, state.player)
    state.files["pzt-token.txt"] = "secret"
    assert status(bridge)["god_mode"] is True
    assert state.player.god_mode_calls == 1


@pytest.mark.parametrize("failure", ["set_error", "read_error", "ignore_set"])
def test_startup_god_mode_failure_is_visible_without_false_success_or_retries(bridge, failure):
    state = bridge.globals()
    state.player[failure] = True if failure == "ignore_set" else "API failed"
    state.create_player(0, state.player)
    result = status(bridge)
    assert result["god_mode"] is False
    assert result["god_mode_error"]
    assert "Startup god mode failed" in state.printed[1]
    status(bridge)
    assert state.player.god_mode_calls == 1


def test_missing_compiler_does_not_block_startup_god_mode(bridge):
    state = bridge.globals()
    state.loadstring = None
    result = status(bridge)
    assert result["ready"] is False
    assert result["reason"] == "Lua compiler unavailable"
    assert result["god_mode"] is True


def test_god_mode_status_observes_actual_state_and_rejects_lost_authorization(bridge):
    state = bridge.globals()
    assert status(bridge)["god_mode"] is True
    state.player.read_error = "read unavailable"
    result = status(bridge)
    assert result["god_mode"] is False
    assert "read unavailable" in result["god_mode_error"]
    state.player.read_error = None
    assert status(bridge)["god_mode"] is True
    state.debug_enabled = False
    assert status(bridge)["god_mode"] is False
    assert state.player.god_mode_calls == 1
