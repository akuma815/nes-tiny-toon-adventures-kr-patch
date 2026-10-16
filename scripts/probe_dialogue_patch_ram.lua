-- Isolated hardware mapping probe. Explicit temporary RAM writes only.
local out=assert(os.getenv('TTA_QA_OUT'))
local frame=0
emu.addEventCallback(function()
 frame=frame+1
 if frame==1 then
  local map=emu.convertAddress(0x6000,emu.memType.nesMemory)
  local f=assert(io.open(out..'/patch_ram_probe.txt','wb'))
  f:write('address='..tostring(map.address)..' memType='..tostring(map.memType)..'\n')
  for k,v in pairs(emu.memType) do if v==map.memType then f:write('mapped_type='..k..'\n') end end
  assert(map.address>=0,'unmapped patch RAM')
  for a=0x6000,0x6003 do
   local old=emu.read(a,emu.memType.nesMemory);emu.write(a,0x59,emu.memType.nesMemory);assert(emu.read(a,emu.memType.nesMemory)==0x59)
   emu.write(a,0xA6,emu.memType.nesMemory);assert(emu.read(a,emu.memType.nesMemory)==0xA6);emu.write(a,old,emu.memType.nesMemory)
  end
  f:write('temporary_write_read_restore=PASS\n');f:close();emu.stop(0)
 end
end,emu.eventType.endFrame)
