"""Declared RAM-only scene skips into the original stage/ending dispatchers."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--case',choices=['stage1','stage2','stage3','stage4','stage5','stage6','ending'],required=True)
    ap.add_argument('--source',action='store_true')
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();rom=a.rom.resolve();out=a.output.resolve()
    out.relative_to(ROOT/'qa/dialogue');out.mkdir(parents=True,exist_ok=False)
    asm=json.loads((ROOT/'build/dialogue_full_006/assembly.json').read_text())
    pc=0xb276 if a.source else asm['helper_symbols']['READ_NEW']+2
    bank=11 if a.source else 18
    level={'stage1':0,'stage2':5,'stage3':10,'stage4':15,'stage5':20,'stage6':21,'ending':23}[a.case]
    inputs=[(240,248,['start']),(600,608,['start'])]
    if a.case=='ending':
        stop=10000
        inputs += [(f,f+8,['a']) for f in range(1500,9500,400)]
    else:
        stop=4200
        inputs += [(2200,2208,['right']),(2260,2268,['left']),(3000,3008,['a'])]
    segments=','.join('{first=%d,last=%d,buttons={%s}}'%(first,last,','.join(json.dumps(x) for x in buttons)) for first,last,buttons in inputs)
    (out/'gameplay_config.lua').write_text('return {readpc=%d,readbank=%d,stop=%d,interval=60,captures={},inputs={%s}}\n'%(pc,bank,stop,segments))
    ending=a.case=='ending'
    injection='''
local skipped=false
local skipLog=assert(io.open(out..'/scene_skip.csv','wb'))
skipLog:write('frame,address,old_value,new_value,reason\\n')
local function skipWrite(address,value,reason)
 local old=emu.read(address,emu.memType.nesMemory)
 emu.write(address,value,emu.memType.nesMemory)
 skipLog:write(string.format('%d,%04X,%02X,%02X,%s\\n',frame,address,old,value,reason));skipLog:flush()
end
-- D57C reads $4C and dispatches the original scene handler. No PC/A/text
-- pointer substitution, sprite copies, ROM writes, or savestate loading.
emu.addMemoryCallback(function()
 if skipped or frame<600 or emu.read(0x4C,emu.memType.nesMemory)~=2 then return end
 skipped=true
 skipWrite(0x53,LEVEL,'selected_stage_index')
 ENDING_WRITES
 record('declared_scene_skip')
end,emu.callbackType.exec,0xD57C,0xD57C,emu.cpuType.nes)
'''.replace('LEVEL',str(level)).replace('ENDING_WRITES',"skipWrite(0x4C,16,'original_ending_dispatcher');skipWrite(0x5BA,0,'original_ending_initial_state');skipWrite(0x5BB,0,'original_ending_substate')" if ending else '')
    base=(ROOT/'scripts/capture_dialogue_gameplay.lua').read_text(encoding='utf-8')
    base=base.replace('-- Controller-only exploratory replay. Read-only captures; no state injection.','-- Declared RAM-only scene skip; original resources and scene code execute.')
    base=base.replace('local previousMode=-1',injection+'\nlocal previousMode=-1')
    script=out/'capture_script_snapshot.lua';script.write_text(base,encoding='utf-8')
    exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
    env=os.environ.copy();env['TTA_QA_OUT']=str(out)
    cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=120','--enableStdout']
    p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=135)
    (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
    scope='One declared $53 level-index RAM write before the original scene dispatcher; original stage-specific Shirley initialization, script selection, resources, controller selection and stage entry. Controlled scene skip, not full gameplay.' if not ending else 'Four declared RAM writes ($53/$4C/$05BA/$05BB) before the original scene dispatcher to start its real ending at initial state0. Original ending resource loading, portrait/background sequence, roots22..25, text/IRQ and continuation. Controlled ending skip, not a native final-boss victory.'
    report={'exit_code':p.returncode,'command':cmd,'case':a.case,'mode':scope,'rom_sha256':sha(rom),'emulator_sha256':sha(exe),'capture_script_sha256':sha(script),'files':{x.name:sha(x) for x in sorted(out.iterdir()) if x.is_file()}}
    (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n')
    assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
    assert len((out/'scene_skip.csv').read_text().splitlines())==(5 if ending else 2)
    print(json.dumps({'status':'CAPTURE_COMPLETE','case':a.case,'output':str(out)}))
if __name__=='__main__':main()
