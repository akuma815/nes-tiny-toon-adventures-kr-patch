-- Original cold boot, controller input only. Mesen 2.1.1.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
local f=assert(io.open(out..'/script_reads.csv','wb'))
f:write('frame,cpu_pc,cpu_address,file_offset,value\n')
emu.addMemoryCallback(function(address,value)
  local s=emu.getState()
  local target=(emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y'])%65536
  if (s['cpu.pc']==0xB274 or s['cpu.pc']==0xB276) and address==target then
    local m=emu.convertAddress(address,emu.memType.nesMemory)
    f:write(string.format('%d,%04X,%04X,%05X,%02X\n',frame,s['cpu.pc'],address,m.address+16,value))
  end
end,emu.callbackType.read,0x17433,0x17839,emu.cpuType.nes,emu.memType.nesPrgRom)
local function save(name,data)
 local h=assert(io.open(out..'/'..name,'wb'));h:write(data);h:close()
end
emu.addEventCallback(function()
 frame=frame+1
 if frame%120==0 and frame<=1440 then
  local tag=string.format('frame_%04d',frame)
  save(tag..'.png',emu.takeScreenshot())
  local a={};for i=0,0x7ff do a[#a+1]=string.char(emu.read(i,emu.memType.nesMemory)) end
  save(tag..'_ram.bin',table.concat(a))
 end
 if frame==1800 then f:close();emu.stop(0) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=(frame>=240 and frame<248) or (frame>=600 and frame<608),a=frame>=900 and frame%120<8,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
