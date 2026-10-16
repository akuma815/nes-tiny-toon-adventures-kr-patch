-- Native intro: no controller input; attract intro. No RAM/ROM writes, injection or savestates.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
local full=emu.convertAddress(0xFE8C,emu.memType.nesMemory).address>=0x20000
local bank=full and 18 or 11
local pc=full and 0x826D or 0xB276
local calls=assert(io.open(out..'/font_calls.csv','wb'))
local writes=assert(io.open(out..'/font_writes.csv','wb'));writes:write('frame,pc,address,value\n')
emu.addMemoryCallback(function(address,value)
 if address~=0xB000 and address~=0xB004 and address~=0xB008 and address~=0xB00C then return end
 local s=emu.getState();writes:write(string.format('%d,%04X,%04X,%02X\n',frame,s['cpu.pc'],address,value))
end,emu.callbackType.write,0xB000,0xB00C,emu.cpuType.nes)
calls:write('frame,event,base,cursor,bank8000,bankA000,chr0\n')
local function trace(event)
 local m=emu.convertAddress(0x8000,emu.memType.nesMemory);local a=emu.convertAddress(0xA000,emu.memType.nesMemory);local c=emu.convertAddress(0,emu.memType.nesPpuMemory)
 calls:write(string.format('%d,%s,%04X,%02X,%d,%d,%d\n',frame,event,emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory),emu.read(0x7A9,emu.memType.nesMemory),m.address,a.address,c.address))
end
local inside=false
emu.addMemoryCallback(function() inside=true;trace('enter') end,emu.callbackType.exec,0xFE8C,0xFE8C,emu.cpuType.nes)
emu.addMemoryCallback(function() if inside then trace('leave');inside=false end end,emu.callbackType.exec,0xFEA7,0xFEA7,emu.cpuType.nes)
local reads=assert(io.open(out..'/script_reads.csv','wb'))
reads:write('frame,cpu_pc,cpu_address,file_offset,value,flag\n')
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,first,size)
 local t={};for a=first,first+size-1 do t[#t+1]=string.char(emu.read(a,kind)) end
 save(name,table.concat(t))
end
emu.addMemoryCallback(function(address,value)
 local s=emu.getState()
 if s['cpu.pc']~=pc then return end
 local target=emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y']
 if address~=target then return end
 local m=emu.convertAddress(address,emu.memType.nesMemory)
 reads:write(string.format('%d,%04X,%04X,%05X,%02X,%02X\n',frame,s['cpu.pc'],address,m.address+16,value,emu.read(0x57,emu.memType.nesMemory)))
end,emu.callbackType.read,bank*0x2000,bank*0x2000+0x1FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
emu.addEventCallback(function()
 frame=frame+1
 if frame%120==0 or frame==3300 then
  local tag=string.format('frame_%04d',frame);save(tag..'.png',emu.takeScreenshot())
  dump(tag..'_ppu.bin',emu.memType.nesPpuDebug,0,0x4000);dump(tag..'_ram.bin',emu.memType.nesMemory,0,0x800)
  local maps={};for a=0,0x1fff,0x400 do local m=emu.convertAddress(a,emu.memType.nesPpuMemory);maps[#maps+1]=string.format('PPU %04X %s %s',a,tostring(m.address),tostring(m.memType)) end
  save(tag..'_mapping.txt',table.concat(maps,'\n'))
 end
 if frame==4200 then reads:close();emu.stop(0) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=false,a=false,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
