#!/usr/bin/env python3
"""Observe the automatic three-round loadout in the actual regional ROM.

Only title seed and fresh private SRAM are explicit fixtures. Every choice is
real menu input. Inventory, menus, completion, gameplay state, camera and pixels
are never assigned. This test qualifies the opening, not all regional content.
"""
import argparse
import json
from pathlib import Path

from regional_native_support import NativeRun,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seeds',nargs='+',default=['0xb4a7','0xdeadbeef','7'])
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    checks=[];cases=[]
    def check(name,ok,detail=None):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
        print(('PASS ' if ok else 'FAIL ')+name,flush=True)
    for raw in a.seeds:
        seed=int(raw,0);run=NativeRun(a.bundle,a.out/f'seed-{seed:08x}')
        initial=run.start(seed)
        selected=run.finish_draft()
        final=run.snapshot()
        check('three actual choices '+raw,[x['round'] for x in selected]==[0,1,2],selected)
        check('three distinct offers in every round '+raw,
              all(len(set(x['before']['draft']['options']))==3 for x in selected),
              [x['before']['draft']['options'] for x in selected])
        check('draft complete in ordinary Drain '+raw,
              final['draft']['state']==run.abi['enum_draft_done'] and final['draft']['round']==3 and
              final['area']==run.abi['enum_sewer'] and final['state']==run.abi['enum_play'],final)
        check('original starting equipment retained '+raw,
              all((before&after)==before for before,after in zip(initial['inventory']['owned'],final['inventory']['owned'])) and
              (final['inventory']['skills']&initial['inventory']['skills'])==initial['inventory']['skills'],
              dict(before=initial['inventory'],after=final['inventory']))
        check('opening sentinel released '+raw,final['starting_draft']==0,final['starting_draft'])
        run.keys([],180)
        idle=run.snapshot()
        check('idle does not reopen or reroll draft '+raw,
              idle['draft']==final['draft'] and idle['starting_draft']==0 and not idle['text'],idle)
        run.image('finished-opening')
        report=dict(**run.report_identity(),method=__doc__,selected=selected,
                    initial=initial,final=final,idle=idle,inputs=run.inputs)
        (run.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        cases.append(dict(seed=seed,identity=run.report_identity(),path=run.out.name,
                          selected_items=[x['item'] for x in selected]))
    report=dict(method=__doc__,tool_sha256=sha(__file__),checks=checks,cases=cases,
                passed=sum(c['passed'] for c in checks),total=len(checks),
                rom_sha256=sha(a.bundle/'bartgame.gba'),
                source_commit=(a.bundle/'source-commit.txt').read_text().strip(),
                limits=['This opening-only pass does not establish cold Continue; the save regression must qualify that separately.',
                        'Selection identity and state changes are observed; alternate offer eligibility is separately host-qualified.'])
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(report['passed']!=report['total'])


if __name__=='__main__':main()
