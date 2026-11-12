#!/usr/bin/env python3
"""Host-only actual-C regression for pause inventory coverage and pagination.

The fixture sets inventory records in a host process, never a running ROM.
It compiles the current menu.c and ROM metadata directly, uses the unchanged
pure legacy ownership/lookup functions extracted verbatim from legacy_items.c,
and supplies journal's actual gold-half metadata through a limited lookup stub.
No screen or gameplay capture is manufactured by this test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def block(source, marker):
    """Retain one exact balanced C function/initializer from the source."""
    start = source.index(marker)
    first = source.index('{', start)
    depth = 0
    quote = None
    escape = False
    for i in range(first, len(source)):
        c = source[i]
        if quote:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == quote:
                quote = None
            continue
        if c in ('"', "'"):
            quote = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if not depth:
                end = i + 1
                if end < len(source) and source[end] == ';':
                    end += 1
                return source[start:end]
    raise ValueError(marker)


HARNESS = r'''
extern int printf(const char*,...);
#include "menu.c"
#include "menu_layouts_a.c"
#include "journal.h"
PlayerState gPl;
LegacyInventory gLegacyInventory;
HandoffState gHandoffState;
GameState gGame;
World gWorld;
u16 gKeysHeld,gKeysDown,gKeysUp;
#include "legacy_items_metadata.inc"
@PURE@
@GOLD@
bool8 journal_entry(int page,int id,JournalEntry* out) {
    if(page || id<JI_GOLD_FLOW || id>=JI_GOLD_FLOW+4)return FALSE;
    *out=sGoldHalves[id-JI_GOLD_FLOW];return TRUE;
}
static int checks,failed;
static void check(const char* name,int pass,int actual,int expected) {
    checks++;if(!pass)failed++;
    printf("{\"name\":\"%s\",\"passed\":%s,\"actual\":%d,\"expected\":%d}\n",name,pass?"true":"false",actual,expected);
}
static void zero(void* ptr,unsigned size) {u8* p=ptr;while(size--)*p++=0;}
static void reset(void) {
    zero(&gPl,sizeof(gPl));zero(&gLegacyInventory,sizeof(gLegacyInventory));
    zero(&gHandoffState,sizeof(gHandoffState));
    zero(sStudyOwned,sizeof(sStudyOwned));zero(sStudyCoreOwned,sizeof(sStudyCoreOwned));
    sPage=PG_ITEMS;sCursor=0;sStudyFocus[0]=sStudyFocus[1]=0;
    sStudy=menu_layout_a(1);gKeysDown=0;
}
static void grant_host(int item) {gLegacyInventory.owned[item>>5]|=1u<<(item&31);}
/* Independent policy list: the original visible entries already represent
   these catalog aliases, and the source-only helpers must never be listed. */
static int alias(int item) {
    static const int ids[]={LI_SMITH_SWORD,LI_SHIELD,LI_BOMBS,LI_LANTERN_OFF,
      LI_LANTERN_ON,LI_ROCS_CAPE,LI_BOW,LI_POWER_BRACELETS,LI_MAP,LI_COMPASS,
      LI_HEART_PIECE,LI_SMALL_KEY};
    unsigned i;for(i=0;i<sizeof(ids)/sizeof(ids[0]);i++)if(item==ids[i])return 1;
    return 0;
}
static void full_inventory(void) {
    int p,i;reset();gPl.items=0x7f;gPl.items2=0x1f;
    for(i=0;i<4;i++)gLegacyInventory.owned[i]=~0u;
    gHandoffState.gold_owned=15;
    for(p=0;p<2;p++) {
        struct {u8 before[8],ids[MS_LIST_MAX],after[8];} output;
        int expected[256]={0},seen[256]={0},base=p?KEY_COUNT:ITEM_COUNT,n,want=base,ok=1;
        for(i=0;i<8;i++)output.before[i]=output.after[i]=0xa5;
        for(i=0;i<base;i++)expected[i]=1;
        for(i=1;i<LI_COUNT;i++) {
            const LegacyItemDef* d=&gLegacyItemDefs[i];
            if(alias(i)||(d->flags&LIF_HIDDEN)||((d->equip!=EQ_NONE)!=(p==PG_ITEMS)))continue;
            expected[base+i]=1;want++;
        }
        if(p==PG_KEYS)for(i=0;i<4;i++){expected[base+LI_COUNT+i]=1;want++;}
        sPage=p;n=ms_gather(p,output.ids);
        check(p?"full keepsake count":"full tool count",n==want,n,want);
        for(i=0;i<n;i++) {int id=output.ids[i];if(!expected[id]||seen[id]++)ok=0;}
        for(i=0;i<256;i++)if(expected[i]&&seen[i]!=1)ok=0;
        check(p?"every keepsake appears exactly once":"every tool appears exactly once",ok,n,want);
        ok=1;for(i=0;i<8;i++)if(output.before[i]!=0xa5||output.after[i]!=0xa5)ok=0;
        check("full inventory leaves output guards untouched",ok,ok,1);
        ok=1;for(i=0;i<n;i++)if(output.ids[i]>=128)ok=0;
        check("all compact IDs fit seven-bit range",ok,ok,1);
        /* Explore every actual spatial D-pad transition, including each
           next/previous seven-slot boundary and the shortened final page. */
        {
            int reached[MS_LIST_MAX]={0},queue[MS_LIST_MAX],head=0,tail=0;
            const int keys[4]={KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT};
            queue[tail++]=0;reached[0]=1;ok=1;
            while(head<tail) {
                int from=queue[head++],k;
                for(k=0;k<4;k++) {
                    sCursor=from;gKeysDown=keys[k];ms_move(n,output.ids);
                    if(sCursor>=n){ok=0;continue;}
                    if(!reached[sCursor]){reached[sCursor]=1;queue[tail++]=sCursor;}
                }
            }
            check("all D-pad moves remain within owned inventory",ok,ok,1);
            check(p?"all keepsake pages reachable and returnable":"all tool pages reachable and returnable",tail==n,tail,n);
            /* Reverse search ensures each page has a real way back. */
            for(i=0;i<n;i++) {
                int at=i,limit=1000;
                while(at>0&&limit--) {
                    int prior=at;
                    sCursor=at;gKeysDown=KEY_LEFT;ms_move(n,output.ids);at=sCursor;
                    if(at==prior){gKeysDown=KEY_UP;ms_move(n,output.ids);at=sCursor;}
                    if(at==prior)break;
                }
                if(at!=0)ok=0;
            }
            check("every populated slot can navigate back to first",ok,ok,1);
        }
        if(p==PG_KEYS)for(i=0;i<4;i++) {
            const MenuItem* item=ms_item(PG_KEYS,KEY_COUNT+LI_COUNT+i);
            check("gold half resolves its real journal frame",item&&item->icon==118+i&&item->eq==EQ_NONE,item?item->icon:-1,118+i);
        }
    }
}
static void independent_bits(void) {
    const int bits[4]={ITEM2_BOW,ITEM2_HUBCAP,ITEM2_MAP,ITEM2_ASTROLABE};
    int b;for(b=0;b<4;b++) {
        reset();gPl.items2=bits[b];
        check("bow ownership uses its independent bit",owned(&sItems[5])==(b==0),owned(&sItems[5]),b==0);
        check("drain cap ownership uses its independent bit",owned(&sItems[6])==(b==1),owned(&sItems[6]),b==1);
        check("map ownership uses its independent bit",owned(&sKeys[4])==(b==2),owned(&sKeys[4]),b==2);
        check("astrolabe ownership uses its independent bit",owned(&sKeys[5])==(b==3),owned(&sKeys[5]),b==3);
    }
}
static void focus_and_counters(void) {
    u8 ids[MS_LIST_MAX];int n,i,found=0;const MenuItem* item;
    reset();gPl.items=ITEM_SWORD|ITEM_SHIELD;grant_host(LI_MOLE_MITTS);
    ms_owned_snapshot(TRUE);n=ms_gather(sPage,ids);ms_focus_cursor(sPage,ids,n);
    item=ms_item(sPage,ids[sCursor]);
    check("first pause focuses newly awarded noncore tool",sPage==PG_ITEMS&&item->legacy==LI_MOLE_MITTS,item->legacy,LI_MOLE_MITTS);
    grant_host(LI_SKILL_PERIL_BEAM);ms_owned_snapshot(FALSE);n=ms_gather(sPage,ids);ms_focus_cursor(sPage,ids,n);item=ms_item(sPage,ids[sCursor]);
    check("new passive immediately selects its owned page",sPage==PG_KEYS&&item->legacy==LI_SKILL_PERIL_BEAM,item->legacy,LI_SKILL_PERIL_BEAM);
    gHandoffState.gold_owned=8;ms_owned_snapshot(FALSE);n=ms_gather(sPage,ids);ms_focus_cursor(sPage,ids,n);item=ms_item(sPage,ids[sCursor]);
    check("new gold half immediately selects its owned page",sPage==PG_KEYS&&item->legacy==LI_COUNT+3,item->legacy,LI_COUNT+3);
    reset();gLegacyInventory.kinstones[1]=3;n=ms_gather(PG_KEYS,ids);
    for(i=0;i<n;i++)if(ids[i]==KEY_COUNT+LI_KINSTONE)found++;
    check("counter-only Kinstones appear without a stale owned bit",found==1,found,1);
    check("inventory gathering never writes acquired item flags",gLegacyInventory.owned[LI_KINSTONE>>5]==0,gLegacyInventory.owned[LI_KINSTONE>>5],0);
    reset();n=ms_gather(PG_ITEMS,ids);sCursor=0;gKeysDown=KEY_RIGHT;
    check("empty tool page has no movement",n==0&&!ms_move(n,ids),n,0);
}
int main(void) {
    full_inventory();independent_bits();focus_and_counters();
    printf("{\"summary\":true,\"checks\":%d,\"failed\":%d}\n",checks,failed);
    return failed?1:0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('/workspace/setup/pause-repair/host'))
    parser.add_argument('--assets', type=Path, default=Path('/workspace/setup/cream-selected/frozen/assets.h'))
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    legacy = (ROOT/'src/legacy_items.c').read_text()
    journal = (ROOT/'src/journal.c').read_text()
    pure = '\n'.join(block(legacy, marker) for marker in (
        'static bool8 valid(int item)', 'bool8 legacy_item_owned(int item)',
        'const LegacyItemDef* legacy_item_def(int item)'))
    pure = next(line for line in legacy.splitlines() if line.startswith('#define BIT_HAS')) + '\n' + pure
    unit = HARNESS.replace('@PURE@', pure).replace('@GOLD@', block(journal, 'static const JournalEntry sGoldHalves[4]'))
    (out/'fixture.c').write_text(unit)
    shutil_header = out/'assets.h'
    shutil_header.write_bytes(args.assets.read_bytes())
    command = ['gcc','-std=c99','-O2','-w','-ffunction-sections','-fdata-sections',
               '-I',str(out),'-I',str(ROOT/'src'),str(out/'fixture.c'),
               '-Wl,--gc-sections','-o',str(out/'fixture')]
    result = subprocess.run(command, text=True, capture_output=True)
    (out/'compile.log').write_text(result.stdout+result.stderr)
    result.check_returncode()
    run = subprocess.run([str(out/'fixture')], text=True, capture_output=True)
    (out/'run.log').write_text(run.stdout+run.stderr)
    rows = [json.loads(line) for line in run.stdout.splitlines() if line.startswith('{')]
    checks = [row for row in rows if not row.get('summary')]
    report = dict(method='Host-only fixture compiles actual menu.c and metadata; extracted pure legacy functions are verbatim. Gold journal lookup uses the actual source array. No emulated gameplay or screenshots are fabricated.',
                  source_files={str(p.relative_to(ROOT)):sha(p) for p in (
                      ROOT/'src/menu.c',ROOT/'src/legacy_items.c',ROOT/'src/legacy_items_metadata.inc',
                      ROOT/'src/journal.c',ROOT/'src/menu_layouts_a.c')},
                  fixture_sha256=sha(out/'fixture.c'), assets_header_sha256=sha(args.assets),
                  command=command, checks=checks, complete=run.returncode==0 and bool(checks) and all(c['passed'] for c in checks))
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'complete':report['complete'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},indent=2))
    return int(not report['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
