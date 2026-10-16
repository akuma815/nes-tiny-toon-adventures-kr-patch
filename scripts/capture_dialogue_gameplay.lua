-- Controller-only exploratory replay. Read-only captures; no state injection.
local out=assert(os.getenv('TTA_QA_OUT'))
local cfg=dofile(out..'/gameplay_config.lua')
local frame=0
local events=assert(io.open(out..'/events.csv','wb'))
events:write('frame,event,a,base,cursor,mode\n')
local reads=assert(io.open(out..'/script_reads.csv','wb'))
reads:write('frame,file_offset,value\n')
local function save(name,data)
 local f=assert(io.open(out..'/'..name,'wb'));f:write(data);f:close()
end
local function dump(name,kind,first,size)
 local t={};for i=first,first+size-1 do t[#t+1]=string.char(emu.read(i,kind)) end
 save(name,table.concat(t))
end
local function record(event)
 local s=emu.getState()
 events:write(string.format('%d,%s,%d,%04X,%02X,%d\n',frame,event,s['cpu.a'],
 emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory),
 emu.read(0x7A9,emu.memType.nesMemory),emu.read(0x57,emu.memType.nesMemory)))
end
emu.addMemoryCallback(function()
 local m=emu.convertAddress(0xB20E,emu.memType.nesMemory)
 if math.floor(m.address/0x2000)==11 then record('native_initializer') end
end,emu.callbackType.exec,0xB20E,0xB20E,emu.cpuType.nes)
emu.addMemoryCallback(function(address,value)
 local s=emu.getState();if s['cpu.pc']~=cfg.readpc then return end
 local target=(emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y'])%65536
 if address~=target then return end
 local m=emu.convertAddress(address,emu.memType.nesMemory)
 reads:write(string.format('%d,%05X,%02X\n',frame,m.address+16,value))
 if value==0xF7 or value==0xFA then record(string.format('token_%02X',value));cfg.captures[frame+3]=true end
end,emu.callbackType.read,cfg.readbank*0x2000,cfg.readbank*0x2000+0x1FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
local workram=assert(io.open(out..'/workram_access.csv','wb'))
workram:write('frame,event,address,value,pc,prg_offset\n')
for _,event in ipairs({'read','write'}) do
 emu.addMemoryCallback(function(address,value)
  local s=emu.getState();local m=emu.convertAddress(s['cpu.pc'],emu.memType.nesMemory)
  workram:write(string.format('%d,%s,%04X,%02X,%04X,%s\n',frame,event,address,value,s['cpu.pc'],tostring(m.address)))
 end,emu.callbackType[event],0x6000,0x7FFF,emu.cpuType.nes)
end
local previousMode=-1
local fonts=assert(io.open(out..'/font_calls.csv','wb'))
fonts:write('frame,base,cursor,mode,sp_before,sp_after,chr0,chr400\n')
local fontEntry=nil
local seenFonts={}
emu.addMemoryCallback(function()
 if emu.read(0x57,emu.memType.nesMemory)==0 then return end
 local s=emu.getState()
 fontEntry={frame=frame,base=emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory),cursor=emu.read(0x7A9,emu.memType.nesMemory),mode=emu.read(0x57,emu.memType.nesMemory),sp=s['cpu.sp']}
end,emu.callbackType.exec,0xFE8C,0xFE8C,emu.cpuType.nes)
emu.addMemoryCallback(function()
 if not fontEntry then return end
 local s=emu.getState();local p=emu.convertAddress(0,emu.memType.nesPpuMemory).address/1024;local q=emu.convertAddress(0x400,emu.memType.nesPpuMemory).address/1024
 fonts:write(string.format('%d,%04X,%02X,%d,%02X,%02X,%d,%d\n',fontEntry.frame,fontEntry.base,fontEntry.cursor,fontEntry.mode,fontEntry.sp,s['cpu.sp'],p,q))
 local key=string.format('font_%03d_%03d.bin',p,q)
 if not seenFonts[key] then dump(key,emu.memType.nesPpuDebug,0,0x800);seenFonts[key]=true end
 fontEntry=nil
end,emu.callbackType.exec,0xFEB0,0xFEB0,emu.cpuType.nes)
local autoHoldUntil=-1
local autoReleaseUntil=-1
local inputs=assert(io.open(out..'/controller_inputs.csv','wb'))
inputs:write('frame,start,a,b,select,up,down,left,right\n')
emu.addEventCallback(function()
 frame=frame+1
 if cfg.carrots and frame==5800 then
  local old=emu.read(0x7E1,emu.memType.nesMemory)
  emu.write(0x7E1,cfg.carrots,emu.memType.nesMemory)
  record(string.format('explicit_carrot_override_%d_to_%d',old,cfg.carrots))
 end
 local mode=emu.read(0x57,emu.memType.nesMemory)
 if mode~=previousMode then record('mode_change');previousMode=mode end
 if frame%cfg.interval==0 or cfg.captures[frame] then
  local tag=string.format('frame_%05d',frame)
  save(tag..'.png',emu.takeScreenshot())
  dump(tag..'_ram.bin',emu.memType.nesMemory,0,0x800)
  dump(tag..'_ppu.bin',emu.memType.nesPpuDebug,0,0x4000)
 end
 if frame>=cfg.stop then reads:close();events:close();inputs:close();workram:close();fonts:close();emu.stop(0) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 local input={start=false,a=false,b=false,select=false,up=false,down=false,left=false,right=false}
 for _,segment in ipairs(cfg.inputs) do
  if frame>=segment.first and frame<segment.last then
   for _,button in ipairs(segment.buttons) do input[button]=true end
   if segment.period and (frame-(segment.phase or 0))%segment.period<segment.hold then input.a=true end
   if segment.auto_jump then
    if frame>=autoReleaseUntil and emu.read(0x57,emu.memType.nesMemory)==0 and
     emu.read(0x6C,emu.memType.nesMemory)==0 and emu.read(0x6D,emu.memType.nesMemory)==0 then
     autoHoldUntil=frame+segment.auto_jump;autoReleaseUntil=autoHoldUntil+3;record('controller_jump')
    end
    if frame<autoHoldUntil then input.a=true end
   end
  end
 end
 emu.setInput(input,0)
 local values={tostring(frame)}
 for _,button in ipairs({'start','a','b','select','up','down','left','right'}) do values[#values+1]=input[button] and '1' or '0' end
 inputs:write(table.concat(values,',')..'\n')
end,emu.eventType.inputPolled)
