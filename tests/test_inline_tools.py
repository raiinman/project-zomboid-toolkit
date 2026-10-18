"""Offline inline command transport. These fixtures never run a game."""

import json
import threading
import time

import pytest

from pztoolkit.core import GAME_TOOL_NAMES, TOOL_NAMES, Toolkit, atomic_text


@pytest.fixture
def toolkit(tmp_path):
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'game_dir': 'game', 'profile_dir': 'profile',
                                  'workspace_dir': 'workspace'}), encoding='utf-8')
    instance = Toolkit(config)
    instance.profile_prepare()
    atomic_text(instance.profile / 'Lua/pzt-status.txt', json.dumps({
        'ready': True, 'timestamp_ms': time.time() * 1000, 'build': 'fixture'}))
    return instance


def fake_response(toolkit, ok=True, message='done', malformed=False):
    requests = []

    def respond():
        deadline = time.monotonic() + 3
        path = toolkit.profile / 'Lua/pzt-request.txt'
        while time.monotonic() < deadline:
            if path.exists():
                content = path.read_text(encoding='utf-8')
                lines = content.splitlines()
                if len(lines) >= 4:
                    requests.append('\n'.join(lines[3:]))
                    atomic_text(toolkit.profile / 'Lua/pzt-response.txt', json.dumps({
                        'id': lines[1], 'ok': 'bad' if malformed else ok, 'message': message}))
                    return
            time.sleep(.01)

    worker = threading.Thread(target=respond)
    worker.start()
    return requests, worker


@pytest.mark.parametrize('ok', [True, False])
def test_inline_transport_returns_game_result_without_workspace_or_report_files(toolkit, ok):
    requests, worker = fake_response(toolkit, ok=ok, message='game result')
    result = toolkit.lua_execute("return 'inline'", timeout=2)
    worker.join()
    assert requests == ["return 'inline'"]
    assert result['ok'] is ok
    assert result['status'] == ('passed' if ok else 'failed')
    assert result['message'] == 'game result'
    assert 'report' not in result and 'scenario' not in result
    assert not toolkit.workspace.exists()
    assert not (toolkit.profile / 'reports').exists()
    assert (toolkit.profile / 'Lua/pzt-request.txt').read_text() == ''
    assert not (toolkit.profile / 'Lua/pzt-run.lock').exists()
    assert not toolkit.game.exists()


def test_inline_timeout_clears_pending_work_without_a_report(toolkit):
    result = toolkit.lua_execute('return true', timeout=.1)
    assert result['status'] == 'timed_out'
    assert result['ok'] is False
    assert not (toolkit.profile / 'reports').exists()
    assert (toolkit.profile / 'Lua/pzt-request.txt').read_text() == ''
    assert not (toolkit.profile / 'Lua/pzt-run.lock').exists()


@pytest.mark.parametrize('code', ['', '  ', 'x' * (60 * 1024 + 1), '界' * (21 * 1024)],
                         ids=['empty', 'whitespace', 'oversized_ascii', 'oversized_utf8'])
def test_inline_rejects_empty_and_oversized_utf8_code_before_writes(toolkit, code):
    with pytest.raises(ValueError):
        toolkit.lua_execute(code)
    assert not (toolkit.profile / 'Lua/pzt-request.txt').exists()


@pytest.mark.parametrize('timeout', [0, 301, float('nan'), float('inf'), True])
def test_inline_timeout_validation(toolkit, timeout):
    with pytest.raises(ValueError):
        toolkit.lua_execute('return true', timeout)


def test_inline_requires_a_fresh_ready_bridge(toolkit):
    atomic_text(toolkit.profile / 'Lua/pzt-status.txt', '{"ready":false}')
    with pytest.raises(ValueError, match='not ready'):
        toolkit.lua_execute('return true')
    assert not (toolkit.profile / 'Lua/pzt-request.txt').exists()


def test_inline_malformed_correlated_response_is_not_a_pass(toolkit):
    _, worker = fake_response(toolkit, malformed=True)
    result = toolkit.lua_execute('return true', timeout=2)
    worker.join()
    assert result['status'] == 'invalid_response'
    assert result['ok'] is False


@pytest.mark.parametrize('enabled', [True, False])
def test_god_mode_uses_verified_inline_command(toolkit, enabled):
    requests, worker = fake_response(toolkit)
    assert toolkit.call('god_mode', {'enabled': enabled})['ok'] is True
    worker.join()
    value = str(enabled).lower()
    assert f'player:setGodMod({value})' in requests[0]
    assert f'player:isGodMod() == {value}' in requests[0]
    assert not toolkit.workspace.exists()


@pytest.mark.parametrize('enabled', [0, 1, 'true', None])
def test_god_mode_strict_boolean(toolkit, enabled):
    with pytest.raises(ValueError):
        toolkit.call('god_mode', {'enabled': enabled})
    with pytest.raises(ValueError):
        toolkit.god_mode(enabled)
    assert not (toolkit.profile / 'Lua/pzt-request.txt').exists()


def test_god_mode_schema_is_boolean_with_true_default(toolkit):
    schema = next(item for item in toolkit.schemas() if item['name'] == 'god_mode')
    assert schema['inputSchema']['properties']['enabled'] == {'type': 'boolean', 'default': True}


def test_editor_list_is_read_only_and_open_requests_only_allowlisted_api(toolkit):
    metadata = toolkit.debug_editors()
    assert {item['id'] for item in metadata['editors']} == {
        'debug', 'vehicle', 'attachment', 'animation', 'world_map'}
    assert not toolkit.workspace.exists()
    assert not (toolkit.profile / 'Lua/pzt-request.txt').exists()
    requests, worker = fake_response(toolkit)
    assert toolkit.editor_open('vehicle')['ok'] is True
    worker.join()
    assert 'showVehicleEditor(nil)' in requests[0]
    assert 'visibility is not verified' in requests[0]


@pytest.mark.parametrize('editor', ['unknown', "vehicle'); error('injected", '../vehicle', ''])
def test_unknown_editor_never_reaches_wire(toolkit, editor):
    with pytest.raises(ValueError, match='Unknown editor'):
        toolkit.editor_open(editor)
    assert not (toolkit.profile / 'Lua/pzt-request.txt').exists()


def test_game_toolbelt_filter_keeps_one_registry_and_hides_legacy_authoring(toolkit):
    game_tools = Toolkit(toolkit.config_path, tool_names=GAME_TOOL_NAMES)
    assert tuple(game_tools.tools()) == GAME_TOOL_NAMES
    assert len(game_tools.schemas()) == 11
    assert len(toolkit.tools()) == len(TOOL_NAMES) == 17
    assert 'mod_create' not in game_tools.tools()
    with pytest.raises(ValueError, match='Unknown tool'):
        game_tools.call('mod_create', {'name': 'Hidden'})
    assert not game_tools.workspace.exists()


@pytest.mark.parametrize('action', ['bridge_install', 'profile_prepare'])
def test_install_refuses_tracked_running_game_without_mutation(toolkit, monkeypatch, action):
    import os
    import subprocess
    atomic_text(toolkit.profile / 'pzt-game.pid', '12345')
    before = {p.relative_to(toolkit.profile).as_posix(): p.read_bytes()
              for p in toolkit.profile.rglob('*') if p.is_file()}
    if os.name == 'nt':
        monkeypatch.setattr(subprocess, 'run', lambda *a, **kw:
                            subprocess.CompletedProcess(a, 0, '"ProjectZomboid64.exe","12345"'))
    else:
        monkeypatch.setattr(os, 'kill', lambda *a: None)
    with pytest.raises(ValueError, match='already running'):
        getattr(toolkit, action)()
    after = {p.relative_to(toolkit.profile).as_posix(): p.read_bytes()
             for p in toolkit.profile.rglob('*') if p.is_file()}
    assert after == before
