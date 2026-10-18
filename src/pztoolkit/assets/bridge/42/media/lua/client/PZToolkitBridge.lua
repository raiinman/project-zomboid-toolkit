-- Trusted local scenarios only. pcall catches errors, but cannot stop an infinite loop.
local MAX_REQUEST_BYTES = 65536
local MAX_MESSAGE_BYTES = 32768
local POLL_MS = 200
local seen_ids = {}
local next_poll = 0
local next_status = 0
local writer_warnings = {}
-- One startup attempt per player instance. Later manual changes remain intact.
local startup_players = setmetatable({}, { __mode = 'k' })

local function json_string(value)
    local escaped = tostring(value):gsub('[%z\1-\31\\"]', function(char)
        if char == '"' then return '\\"' end
        if char == '\\' then return '\\\\' end
        return string.format('\\u%04x', string.byte(char))
    end)
    return '"' .. escaped .. '"'
end

local function write_file(path, content)
    local writer = getFileWriter(path, true, false)
    if not writer then
        if not writer_warnings[path] then
            print('[PZToolkitBridge] Cannot write protocol file: ' .. path)
            writer_warnings[path] = true
        end
        return false
    end
    local ok = pcall(function() writer:write(content) end)
    local closed = pcall(function() writer:close() end)
    return ok and closed
end

local function read_lines(path, max_bytes)
    local reader = getFileReader(path, false)
    if not reader then return nil end
    local lines = {}
    local bytes = 0
    local ok, message = pcall(function()
        while true do
            local line = reader:readLine()
            if line == nil then break end
            bytes = bytes + #line + 1
            if bytes > max_bytes then error('request exceeds size limit') end
            lines[#lines + 1] = line
        end
    end)
    local closed = pcall(function() reader:close() end)
    if not ok or not closed then return nil, tostring(message or 'read failed') end
    return lines
end

local function local_debug_player(token, player)
    return token ~= nil and #token > 0 and getDebug() == true
        and not isClient() and not isServer() and player ~= nil
end

local function enable_startup_god_mode(player, token)
    if not local_debug_player(token, player) or startup_players[player] then return end
    local state = {}
    startup_players[player] = state
    local ok, message = pcall(function()
        player:setGodMod(true)
        if player:isGodMod() ~= true then error('player did not enable god mode') end
    end)
    if not ok then
        state.error = tostring(message):sub(1, 1024)
        print('[PZToolkitBridge] Startup god mode failed: ' .. state.error)
    end
end

local function god_mode_status(player, token)
    if not local_debug_player(token, player) then return false, nil end
    local ok, value = pcall(function() return player:isGodMod() end)
    local state = startup_players[player]
    if not ok or type(value) ~= 'boolean' then
        local message = ok and 'player god mode state unavailable' or tostring(value):sub(1, 1024)
        if state and state.read_error ~= message then
            print('[PZToolkitBridge] Cannot read god mode: ' .. message)
            state.read_error = message
        end
        return false, message
    end
    return value, state and state.error
end

Events.OnCreatePlayer.Add(function(player_num, player)
    local ok, message = pcall(function()
        local token_lines = read_lines('pzt-token.txt', 1024)
        player = player or getSpecificPlayer(player_num)
        enable_startup_god_mode(player, token_lines and token_lines[1])
    end)
    if not ok then print('[PZToolkitBridge] Startup god mode failed: ' .. tostring(message)) end
end)

local function respond(id, ok, message)
    message = tostring(message)
    if #message > MAX_MESSAGE_BYTES then
        ok = false
        message = 'scenario result exceeds 32768 bytes'
    end
    print('[PZToolkitBridge] END ' .. id .. ' ' .. tostring(ok))
    write_file('pzt-response.txt', '{"id":' .. json_string(id)
        .. ',"ok":' .. tostring(ok) .. ',"message":' .. json_string(message) .. '}')
end

local function poll(now, token)
    local lines = read_lines('pzt-request.txt', MAX_REQUEST_BYTES)
    if not lines or lines[1] ~= token then return end
    local id = lines[2]
    if not id or #id ~= 32 or not id:match('^[0-9a-f]+$') then return end
    if seen_ids[id] then return end
    -- Claim before compilation, including rejected expiry, so the request cannot replay.
    seen_ids[id] = true
    local expiry = tonumber(lines[3])
    if not expiry or expiry ~= expiry or expiry == math.huge or expiry <= now then
        respond(id, false, 'request expired or expiry is invalid')
        return
    end
    local source = table.concat(lines, '\n', 4)
    print('[PZToolkitBridge] BEGIN ' .. id)
    local compiled, chunk, compile_error = pcall(loadstring, source, 'pzt-scenario-' .. id)
    if not compiled or not chunk then
        respond(id, false, 'syntax error: ' .. tostring(compile_error or chunk))
        return
    end
    local ok, result = pcall(chunk)
    if not ok then
        respond(id, false, 'runtime error: ' .. tostring(result))
    elseif result == false then
        respond(id, false, 'scenario returned false')
    else
        respond(id, true, tostring(result))
    end
end

local function on_tick()
    local now = getTimestampMs()
    if now < next_poll then return end
    next_poll = now + POLL_MS
    local token_lines = read_lines('pzt-token.txt', 1024)
    local token = token_lines and token_lines[1]
    local player = getPlayer()
    -- Also covers loading this bridge after the player creation event.
    enable_startup_god_mode(player, token)
    local compiler_available = type(loadstring) == 'function'
    local reason = 'ready'
    if not compiler_available then
        reason = 'Lua compiler unavailable'
    elseif getDebug() ~= true then
        reason = 'debug mode required'
    elseif isClient() or isServer() then
        reason = 'single-player world required'
    elseif player == nil then
        reason = 'player not loaded'
    elseif token == nil or #token == 0 then
        reason = 'authentication token unavailable'
    end
    local ready = reason == 'ready'
    if now >= next_status then
        next_status = now + 1000
        local god_mode, god_mode_error = god_mode_status(player, token)
        write_file('pzt-status.txt', '{"ready":' .. tostring(ready)
            .. ',"timestamp_ms":' .. string.format('%.0f', now)
            .. ',"build":' .. json_string(getCore():getVersion())
            .. ',"lua_compiler":' .. tostring(compiler_available)
            .. ',"debug":' .. tostring(getDebug() == true)
            .. ',"single_player":' .. tostring(not isClient() and not isServer())
            .. ',"player_loaded":' .. tostring(player ~= nil)
            .. ',"god_mode":' .. tostring(god_mode)
            .. (god_mode_error and ',"god_mode_error":' .. json_string(god_mode_error) or '')
            .. ',"reason":' .. json_string(reason) .. '}')
    end
    if ready then poll(now, token) end
end

Events.OnTick.Add(function()
    local ok, message = pcall(on_tick)
    if not ok then print('[PZToolkitBridge] ' .. tostring(message)) end
end)
