-- Forced roots: only A at native initializer. Every control runs to native FA.
local out=assert(os.getenv('TTA_QA_OUT'))
local cfg=dofile(out..'/roots_config.lua')
local frame=0
local localFrame=0
local root=0
local injected=false
local active=false
local captureAt=nil
local log=assert(io.open(out..'/root_events.csv','wb'));log:write('frame,event,root,old_a,new_a\n')
local reads=assert(io.open(out..'/script_reads.csv','wb'));reads:write('frame,root,cpu_pc,file_offset,value\n')
emu.addMemoryCallback(function()
 if injected or localFrame<650 then return end
 local s=emu.getState();log:write(string.format('%d,inject_A,%d,%02X,%02X\n',frame,root,s['cpu.a'],root))
 emu.setState({['cpu.a']=root});injected=true;active=true
end,emu.callbackType.exec,0xB20E,0xB20E,emu.cpuType.nes)
emu.addMemoryCallback(function(address,value)
 if not active then return end
 local s=emu.getState();if s['cpu.pc']~=cfg.pc then return end
 local target=emu.read(0xBF,emu.memType.nesMemory)+256*emu.read(0xC0,emu.memType.nesMemory)+s['cpu.y']
 if address~=target then return end
 local m=emu.convertAddress(address,emu.memType.nesMemory)
 reads:write(string.format('%d,%d,%04X,%05X,%02X\n',frame,root,s['cpu.pc'],m.address+16,value))
 if value==0xFA then active=false;captureAt=frame+3;log:write(string.format('%d,native_FA,%d,,\n',frame,root)) end
end,emu.callbackType.read,cfg.bank*0x2000,cfg.bank*0x2000+0x1FFF,emu.cpuType.nes,emu.memType.nesPrgRom)
emu.addEventCallback(function()
 frame=frame+1;localFrame=localFrame+1
 if captureAt and frame==captureAt then
  local f=assert(io.open(out..string.format('/root_%02d.png',root),'wb'));f:write(emu.takeScreenshot());f:close();captureAt=nil
  if root==25 then reads:close();log:close();emu.stop(0) else root=root+1;injected=false;localFrame=0;emu.reset() end
 end
 if localFrame>3000 then reads:close();log:close();emu.stop(2) end
end,emu.eventType.endFrame)
emu.addEventCallback(function()
 emu.setInput({start=(localFrame>=240 and localFrame<248) or (localFrame>=600 and localFrame<608),a=false,b=false,select=false,up=false,down=false,left=false,right=false},0)
end,emu.eventType.inputPolled)
