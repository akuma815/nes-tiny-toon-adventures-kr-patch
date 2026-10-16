-- Explicit RAM-injected consumer harness. Never label these as native scenes.
local out=assert(os.getenv('TTA_QA_OUT'))
local cfg=dofile(out..'/harness_config.lua')
local frame=0
local localFrame=0
local index=0
local active=false
local doneFrame=nil
local injected=false
local log=assert(io.open(out..'/harness_events.csv','wb'))
log:write('frame,event,page,address,value\n')
local reads=assert(io.open(out..'/script_reads.csv','wb'))
reads:write('frame,page,cpu_pc,file_offset,value\n')
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,first,size)
 local t={};for a=first,first+size-1 do t[#t+1]=string.char(emu.read(a,kind)) end
 save(name,table.concat(t))
end
local function write(a,v)
 emu.write(a,v,emu.memType.nesMemory)
 log:write(string.format('%d,ram_write,%s,%04X,%02X\n',frame,cfg.pages[index].id,a,v))
end
emu.addMemoryCallback(function(address,value)
 if not active then return end
 local s=emu.getState()
 if s['cpu.pc']~=cfg.pc then return end
 local target=emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y']
 if address~=target then return end
 local m=emu.convertAddress(address,emu.memType.nesMemory)
 local p=cfg.pages[index]
 reads:write(string.format('%d,%s,%04X,%05X,%02X\n',frame,p.id,s['cpu.pc'],m.address+16,value))
 if m.address+16==p.last then
  write(0x7A8,0);active=false
  -- Same local frame in both ROMs avoids the selection icon's blink phase.
  assert(localFrame<1100,'page exceeded fixed capture frame')
  doneFrame=frame+(1100-localFrame)
  log:write(string.format('%d,last_glyph,%s,,\n',frame,p.id))
 end
end,emu.callbackType.read,cfg.bank*0x2000,cfg.bank*0x2000+0x1FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
-- Intercept the native initializer's RTS in the first Shirley call, then let
-- the real native frame loop and reader execute normally.
emu.addMemoryCallback(function()
 if injected or localFrame<650 then return end
 index=index+1;injected=true
 local p=cfg.pages[index]
 write(0xBF,p.start%256);write(0xC0,math.floor(p.start/256))
 write(0x7A8,1);write(0x7A9,0);write(0x7AA,4);write(0x7AB,4)
 write(0x7AC,0);write(0x7AD,3);write(0x7AE,0);write(0x7AF,7);write(0x57,2)
 active=true
end,emu.callbackType.exec,0xB22F,0xB22F,emu.cpuType.nes)
emu.addEventCallback(function()
 frame=frame+1;localFrame=localFrame+1
 if doneFrame and frame==doneFrame then
  local id=cfg.pages[index].id
  save(id..'.png',emu.takeScreenshot());dump(id..'_ppu.bin',emu.memType.nesPpuDebug,0,0x4000)
  dump(id..'_ram.bin',emu.memType.nesMemory,0,0x800)
  local maps={}
  for a=0,0x1fff,0x400 do local m=emu.convertAddress(a,emu.memType.nesPpuMemory);maps[#maps+1]=string.format('PPU %04X %s %s',a,tostring(m.address),tostring(m.memType)) end
  save(id..'_mapping.txt',table.concat(maps,'\n'))
  log:write(string.format('%d,capture,%s,,\n',frame,id));doneFrame=nil
  if index==#cfg.pages then reads:close();log:close();emu.stop(0) else localFrame=0;injected=false;emu.reset() end
 end
 if localFrame>2500 then reads:close();log:close();emu.stop(2) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=(localFrame>=240 and localFrame<248) or (localFrame>=600 and localFrame<608),a=false,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
