-- Source-only font geometry survey. Cold boot and controller input only.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,size)
 local a={};for i=0,size-1 do a[#a+1]=string.char(emu.read(i,kind)) end
 save(name,table.concat(a))
end
emu.addEventCallback(function()
 frame=frame+1
 if frame==840 or frame==960 or frame==1200 or frame==1440 then
  local tag=string.format('frame_%04d',frame)
  save(tag..'.png',emu.takeScreenshot())
  dump(tag..'_ppu.bin',emu.memType.nesPpuDebug,0x4000)
  -- All CPU reads are internal RAM, without I/O side effects.
  dump(tag..'_ram.bin',emu.memType.nesMemory,0x800)
  local maps={}
  for a=0,0x1fff,0x400 do
   local m=emu.convertAddress(a,emu.memType.nesPpuMemory)
   maps[#maps+1]=string.format('%04X %s %s',a,tostring(m.address),tostring(m.memType))
  end
  save(tag..'_chr_mapping.txt',table.concat(maps,'\n'))
  local rows={}
  for k,v in pairs(emu.getState()) do rows[#rows+1]=tostring(k)..'='..tostring(v) end
  table.sort(rows);save(tag..'_state.txt',table.concat(rows,'\n'))
 end
 if frame==1440 then emu.stop(0) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=(frame>=240 and frame<248) or (frame>=600 and frame<608),a=false,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
