-- ---------------------------------------------------------------------------
-- The Minish Cap map explorer, for mGBA's Lua console.
--
-- Load it with the mapexplore ROM running:  Tools > Scripting > Load script
--
-- It gives you three things while you walk:
--
--   * a LIVE PANEL with the room you are in, where you are in it, and the
--     tile you are standing on;
--   * a ROOM CHANGE line in the log every time you cross a door, seam or
--     border - which is the edge list of the world graph, written as you
--     walk it;
--   * a WAYPOINT line on L+R, for pinning a spot you want to come back to.
--
-- The tile line is the one that matters most for the reachability model.
-- "coll" is the collision byte, "type" the tileType the tileset maps that
-- tile index to, and "act" the actTile - the triple the engine itself keys
-- on, and the same triple tools/quickstart/tileclass.py counts. When you
-- find a square that needs an item, note its triple: the requirement is a
-- property of the CLASS, so recording it once teaches the model every tile
-- of that kind in the game.
-- ---------------------------------------------------------------------------

local RC = 0x03000bf0          -- gRoomControls
local PLAYER = 0x03001160      -- gPlayerEntity
local MAP_BOTTOM = 0x02025eb0  -- gMapBottom
local MAP_TOP = 0x0200b650     -- gMapTop
local SAVE = 0x02002a40        -- gSave
local INV = SAVE + 0xF2        -- gSave.inventory, 2 bits per item

local KEY_L, KEY_R = 512, 256

local function rd8(a) return emu:read8(a) end
local function rd16(a) return emu:read16(a) end

local function areaName(a)
  return NAMES.areas[a] or string.format("AREA_%d", a)
end

local function roomName(a, r)
  local t = NAMES.rooms[a]
  return (t and t[r]) or string.format("ROOM_%d", r)
end

-- The engine's own tile triple for one room-local tile position.
local function tileClass(base, tx, ty)
  local pos = tx + ty * 64
  local idx = rd16(base + 0x0004 + pos * 2) % 0x400
  return rd8(base + 0x2004 + pos),                 -- collisionData
         rd16(base + 0x5004 + idx * 2),            -- tileTypes[tileIndex]
         rd8(base + 0xb004 + pos)                  -- actTiles
end

local function state()
  local s = {}
  s.area, s.room = rd8(RC + 4), rd8(RC + 5)
  s.ox, s.oy = rd16(RC + 6), rd16(RC + 8)
  s.w, s.h = rd16(RC + 0x1e), rd16(RC + 0x20)
  s.wx, s.wy = rd16(PLAYER + 0x2e), rd16(PLAYER + 0x32)
  s.layer = rd8(PLAYER + 0x38)
  s.lx, s.ly = s.wx - s.ox, s.wy - s.oy
  s.tx, s.ty = s.lx // 16, s.ly // 16
  s.base = (s.layer == 2) and MAP_TOP or MAP_BOTTOM
  if s.tx >= 0 and s.ty >= 0 and s.tx < 64 and s.ty < 64 then
    s.col, s.typ, s.act = tileClass(s.base, s.tx, s.ty)
  else
    s.col, s.typ, s.act = -1, -1, -1
  end
  return s
end

local function held()
  local out = {}
  for _, it in ipairs(NAMES.items) do
    local name, idx = it[1], it[2]
    local byte = rd8(INV + (idx // 4))
    if ((byte >> ((idx % 4) * 2)) & 3) ~= 0 then
      out[#out + 1] = name
    end
  end
  return out
end

local function where(s)
  return string.format("%s / %s", areaName(s.area), roomName(s.area, s.room))
end

local function tileLine(s)
  if s.col < 0 then
    return "tile        (off the map)"
  end
  return string.format("tile class  coll 0x%02x  type 0x%04x  act 0x%02x", s.col, s.typ, s.act)
end

-- A neighbour's collision, for reading what is blocking you right now.
local function neighbours(s)
  local function at(dx, dy)
    local tx, ty = s.tx + dx, s.ty + dy
    if tx < 0 or ty < 0 or tx >= 64 or ty >= 64 then return -1 end
    return rd8(s.base + 0x2004 + tx + ty * 64)
  end
  return string.format("around      N 0x%02x  S 0x%02x  W 0x%02x  E 0x%02x",
                       at(0, -1) % 256, at(0, 1) % 256, at(-1, 0) % 256, at(1, 0) % 256)
end

-- The buffer is optional: not every mGBA build exposes createBuffer, and
-- on the ones that do not, even ASKING for the field can raise. Everything
-- important goes to console:log anyway, so a missing panel costs nothing.
local buffer = nil
do
  local ok, b = pcall(function() return console:createBuffer("map explorer") end)
  if ok and b then
    buffer = b
    pcall(function() buffer:setSize(64, 14) end)
  end
end

local function paint(s)
  if not buffer then return end
  buffer:clear()
  buffer:print(string.format("%s\n", where(s)))
  buffer:print(string.format("area %d  room %d  layer %d\n", s.area, s.room, s.layer))
  buffer:print(string.format("room        %dx%d px  (%dx%d tiles)  origin (%d,%d)\n",
                             s.w, s.h, s.w // 16, s.h // 16, s.ox, s.oy))
  buffer:print(string.format("player      world (%d,%d)  local (%d,%d)  tile (%d,%d)\n",
                             s.wx, s.wy, s.lx, s.ly, s.tx, s.ty))
  buffer:print(tileLine(s) .. "\n")
  buffer:print(neighbours(s) .. "\n")
  buffer:print("items       " .. table.concat(held(), " ") .. "\n")
  buffer:print("\nL+R logs a waypoint.\n")
end

-- A line you can paste straight into the model: where you are, in the
-- coordinates the tables use, plus the tile class under your feet.
local function stamp(tag, s)
  return string.format("%-9s %s  local (%d,%d)  tile (%d,%d)  layer %d  coll 0x%02x type 0x%04x act 0x%02x",
                       tag, where(s), s.lx, s.ly, s.tx, s.ty, s.layer,
                       s.col % 256, s.typ % 0x10000, s.act % 256)
end

local lastArea, lastRoom = -1, -1
local lastWhere = nil
local waypointHeld = false
local frames = 0

local function onFrame()
  frames = frames + 1
  local s = state()

  if s.area ~= lastArea or s.room ~= lastRoom then
    -- Wait for the room to settle before reporting: mid-transition the
    -- origin has not been rewritten yet, so the local coordinates on the
    -- first frames of a new room are the OLD room's arithmetic.
    if s.w > 0 then
      if lastWhere then
        console:log(string.format("ROOM %s  ->  %s", lastWhere, where(s)))
      else
        console:log(string.format("START     %s", where(s)))
      end
      console:log("  " .. stamp("arrive", s))
      lastArea, lastRoom, lastWhere = s.area, s.room, where(s)
    end
  end

  local keys = emu:getKeys()
  local both = (keys & KEY_L) ~= 0 and (keys & KEY_R) ~= 0
  if both and not waypointHeld then
    console:log(stamp("WAYPOINT", s))
    console:log("  items: " .. table.concat(held(), " "))
  end
  waypointHeld = both

  if frames % 4 == 0 then paint(s) end
end

callbacks:add("frame", onFrame)
console:log("map explorer loaded - walk around; room changes log themselves, L+R pins a waypoint")
