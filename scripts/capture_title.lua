-- Mesen 2.1.1 headless capture. No ROM/RAM modifications; only controller input.
local out = os.getenv('TTA_QA_OUT')
assert(out, 'TTA_QA_OUT is required')
local function save(name, data)
  local f = assert(io.open(out .. '/' .. name, 'wb'))
  f:write(data); f:close()
end
local function dump(name, kind, first, size)
  local data = {}
  for i = first, first + size - 1 do data[#data+1] = string.char(emu.read(i, kind)) end
  save(name, table.concat(data))
end
local frame = 0
local captures = {[120]=true,[240]=true,[360]=true,[600]=true,[900]=true,[960]=true,[1200]=true,[1500]=true,[1620]=true,[1800]=true,[2100]=true}
local function capture()
  frame = frame + 1
  if captures[frame] then
    local tag = string.format('frame_%04d', frame)
    save(tag .. '.png', emu.takeScreenshot())
    dump(tag .. '_ppu.bin', emu.memType.nesPpuDebug, 0, 0x4000)
    dump(tag .. '_oam.bin', emu.memType.nesSpriteRam, 0, 256)
    local rows = {}
    for k,v in pairs(emu.getState()) do rows[#rows+1] = tostring(k) .. '=' .. tostring(v) end
    table.sort(rows); save(tag .. '_state.txt', table.concat(rows, '\n'))
    local maps = {}
    for a=0,0x1fff,0x400 do
      local m=emu.convertAddress(a,emu.memType.nesPpuMemory)
      maps[#maps+1]=string.format('%04X %s %s',a,tostring(m.address),tostring(m.memType))
    end
    save(tag .. '_chr_mapping.txt',table.concat(maps,'\n'))
  end
  if frame == 1500 then emu.reset() end
  if frame == 2100 then emu.stop(0) end
end
emu.addEventCallback(capture, emu.eventType.endFrame)
emu.addEventCallback(function()
  emu.setInput({start=(frame>=240 and frame<248) or (frame>=600 and frame<608),select=false,a=frame>=900 and frame%120<8,b=false,up=false,down=false,left=false,right=false},0)
end, emu.eventType.inputPolled)
