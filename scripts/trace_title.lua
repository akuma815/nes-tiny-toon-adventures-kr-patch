-- Read-only consumer trace for the known title RLE extent, Mesen 2.1.1.
local out=assert(os.getenv('TTA_QA_OUT'))
local f=assert(io.open(out..'/title_rle_reads.csv','wb'))
f:write('frame,cpu_pc,cpu_read_address,prg_relative_offset,file_offset,value\n')
local frame=0
emu.addMemoryCallback(function(address,value)
  local mapped=emu.convertAddress(address,emu.memType.nesMemory)
  f:write(string.format('%d,%04X,%04X,%05X,%05X,%02X\n',frame,emu.getState()['cpu.pc'],address,mapped.address,mapped.address+16,value))
end,emu.callbackType.read,0x3644,0x37ea,emu.cpuType.nes,emu.memType.nesPrgRom)
emu.addEventCallback(function()
  frame=frame+1
  if frame==120 then f:close();emu.stop(0) end
end,emu.eventType.endFrame)
