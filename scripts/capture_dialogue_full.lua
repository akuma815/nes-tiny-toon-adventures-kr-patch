-- Full-dialogue cold boot; controller-only input; read-only state trace.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
local calls=assert(io.open(out..'/selector_calls.csv','wb'))
calls:write('frame,event,flag,base,cursor,sp,a000_prg,ppu0_chr,ppu400_chr\n')
local function selectorEvent(event)
 local s=emu.getState()
 local a=emu.convertAddress(0xA000,emu.memType.nesMemory)
 local p=emu.convertAddress(0,emu.memType.nesPpuMemory)
 local q=emu.convertAddress(0x400,emu.memType.nesPpuMemory)
 calls:write(string.format('%d,%s,%02X,%04X,%02X,%02X,%s,%s,%s\n',frame,event,
  emu.read(0x57,emu.memType.nesMemory),
  emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory),
  emu.read(0x7A9,emu.memType.nesMemory),s['cpu.sp'],tostring(a.address),tostring(p.address),tostring(q.address)))
end
local insideFont=false
emu.addMemoryCallback(function() insideFont=true;selectorEvent('enter') end,emu.callbackType.exec,0xFE8C,0xFE8C,emu.cpuType.nes)
emu.addMemoryCallback(function() if insideFont then selectorEvent('leave');insideFont=false end end,emu.callbackType.exec,0xFEB0,0xFEB0,emu.cpuType.nes)
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,first,size)
 local t={};for i=first,first+size-1 do t[#t+1]=string.char(emu.read(i,kind)) end
 save(name,table.concat(t))
end
local mapper=assert(io.open(out..'/mapper_writes.csv','wb'))
mapper:write('frame,pc,cpu_address,value,prg_offset\n')
emu.addMemoryCallback(function(address,value)
 local s=emu.getState();local m=emu.convertAddress(s['cpu.pc'],emu.memType.nesMemory)
 mapper:write(string.format('%d,%04X,%04X,%02X,%s\n',frame,s['cpu.pc'],address,value,tostring(m.address)))
end,emu.callbackType.write,0x8000,0xEFFF,emu.cpuType.nes)
local reads=assert(io.open(out..'/script_reads.csv','wb'))
reads:write('frame,cpu_pc,cpu_address,file_offset,value\n')
emu.addMemoryCallback(function(address,value)
 local s=emu.getState()
 local target=(emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y'])%65536
 if address==target then
  local m=emu.convertAddress(address,emu.memType.nesMemory)
  reads:write(string.format('%d,%04X,%04X,%05X,%02X\n',frame,s['cpu.pc'],address,m.address+16,value))
 end
end,emu.callbackType.read,0x24000,0x25FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
local captures={[240]=true,[600]=true,[720]=true,[780]=true,[810]=true,[840]=true,[881]=true,[882]=true,[888]=true,[891]=true,[892]=true,[893]=true,[900]=true,[960]=true,[992]=true,[1050]=true,[1063]=true,[1072]=true,[1073]=true,[1074]=true,[1200]=true,[1440]=true,[1800]=true,[2100]=true,[2400]=true,[2700]=true,[3000]=true,[3300]=true}
for _,f in ipairs({1080,1121,1140,1176,1177,1178,1499,1510,1559,1570,1801,1807,1808,1810,1836,1907}) do captures[f]=true end
emu.addEventCallback(function()
 frame=frame+1
 if captures[frame] then
  local tag=string.format('frame_%04d',frame)
  save(tag..'.png',emu.takeScreenshot())
  dump(tag..'_ppu.bin',emu.memType.nesPpuDebug,0,0x4000)
  dump(tag..'_ram.bin',emu.memType.nesMemory,0,0x800)
  dump(tag..'_cpu_rom.bin',emu.memType.nesMemory,0x8000,0x8000)
  local maps={}
  for a=0,0x1fff,0x400 do
   local m=emu.convertAddress(a,emu.memType.nesPpuMemory)
   maps[#maps+1]=string.format('PPU %04X %s %s',a,tostring(m.address),tostring(m.memType))
  end
  for a=0x8000,0xE000,0x2000 do
   local m=emu.convertAddress(a,emu.memType.nesMemory)
   maps[#maps+1]=string.format('CPU %04X %s %s',a,tostring(m.address),tostring(m.memType))
  end
  save(tag..'_mapping.txt',table.concat(maps,'\n'))
 end
 if frame==3060 then emu.reset() end
 if frame==3300 then mapper:close();reads:close();calls:close();emu.stop(0) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=(frame>=240 and frame<248) or (frame>=600 and frame<608),
  a=frame>=1800 and frame<3000 and frame%120<8,b=false,select=false,up=false,down=false,
  left=frame>=1560 and frame<1568,right=frame>=1500 and frame<1508},0)
end,emu.eventType.inputPolled)
