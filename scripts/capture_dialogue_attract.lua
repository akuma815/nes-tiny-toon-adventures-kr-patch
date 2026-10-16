-- Native intro: no controller input; attract intro. No RAM/ROM writes, injection or savestates.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
local delays=0
local pending={}
local full=emu.convertAddress(0xFE8C,emu.memType.nesMemory).address>=0x20000
local bank=full and 18 or 11
local workram={}
local function ramAccess(kind)
 return function(address,value)
  local s=emu.getState();local key=string.format('%s,%04X,%04X',kind,s['cpu.pc'],address)
  workram[key]=(workram[key] or 0)+1
 end
end
emu.addMemoryCallback(ramAccess('read'),emu.callbackType.read,0x6000,0x7FFF,emu.cpuType.nes)
emu.addMemoryCallback(ramAccess('write'),emu.callbackType.write,0x6000,0x7FFF,emu.cpuType.nes)
local pc=full and 0x826E or 0xB276
local reads=assert(io.open(out..'/script_reads.csv','wb'))
reads:write('frame,cpu_pc,cpu_address,file_offset,value,flag\n')
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,first,size)
 local t={};for a=first,first+size-1 do t[#t+1]=string.char(emu.read(a,kind)) end
 save(name,table.concat(t))
end
local function capture(tag)
 save(tag..'.png',emu.takeScreenshot());dump(tag..'_ppu.bin',emu.memType.nesPpuDebug,0,0x4000);dump(tag..'_ram.bin',emu.memType.nesMemory,0,0x800)
 dump(tag..'_patch_ram.bin',emu.memType.nesMemory,0x6000,4)
 local maps={};for a=0,0x1fff,0x400 do local m=emu.convertAddress(a,emu.memType.nesPpuMemory);maps[#maps+1]=string.format('PPU %04X %s %s',a,tostring(m.address),tostring(m.memType)) end
 save(tag..'_mapping.txt',table.concat(maps,'\n'))
end
emu.addMemoryCallback(function(address,value)
 local s=emu.getState()
 if not full and s['cpu.pc']~=pc then return end
 local target=emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y']
 if address~=target then return end
 local m=emu.convertAddress(address,emu.memType.nesMemory)
 reads:write(string.format('%d,%04X,%04X,%05X,%02X,%02X\n',frame,s['cpu.pc'],address,m.address+16,value,emu.read(0x57,emu.memType.nesMemory)))
 if value==0xF7 then delays=delays+1;pending[frame+3]=string.format('delay_%02d_frame_%04d',delays,frame+3) end
end,emu.callbackType.read,bank*0x2000,bank*0x2000+0x1FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
emu.addEventCallback(function()
 frame=frame+1
 if frame%120==0 or frame==3300 then
  capture(string.format('frame_%04d',frame))
 end
 if pending[frame] then capture(pending[frame]);pending[frame]=nil end
 if frame==4200 then
  local f=assert(io.open(out..'/workram_access.csv','wb'));f:write('event,pc,address,count\n')
  for k,v in pairs(workram) do f:write(k..','..tostring(v)..'\n') end
  f:close();reads:close();emu.stop(0)
 end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=false,a=false,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
