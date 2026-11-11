/* The Curdled Cream: two real terrace components per room, a directed
   climbing/drop/cave puzzle, and capability-state verification. */
#include "cream_world.h"

CreamWorld gCreamWorld EWRAM_BSS;

static u32 random_next(u32* state) {
    u32 x=*state;
    x^=x<<13;x^=x>>17;x^=x<<5;
    *state=x;
    return x;
}
static u32 mix(u32 x) {
    x^=x>>16;x*=0x7feb352du;x^=x>>15;x*=0x846ca68bu;x^=x>>16;
    return x;
}
static int pick(u32* state,int n) {return (int)(random_next(state)%(u32)n);}
static u8 prefix(int stage) {return (u8)((1u<<stage)-1);}

int cream_edge_count(int node) {
    return node>=0 && node<CC_NODES ? gCreamWorld.degree[node] : 0;
}
const CreamEdge* cream_edge(int node,int index) {
    if(node<0 || node>=CC_NODES || index<0 || index>=gCreamWorld.degree[node]) return NULL;
    return &gCreamWorld.edges[node][index];
}
int cream_find_edge(int from,int target) {
    int i;
    if(from<0 || from>=CC_NODES) return -1;
    for(i=0;i<gCreamWorld.degree[from];i++)
        if(gCreamWorld.edges[from][i].target==target) return i;
    return -1;
}
u8 cream_reward_bit(int node) {
    int i;
    for(i=0;i<3;i++) if(gCreamWorld.reward_node[i]==node) return 1<<i;
    return 0;
}
u8 cream_collect_tokens(int node,u8 tokens) {
    int i;
    tokens&=CC_TOKEN_ALL;
    for(i=0;i<3;i++) if(gCreamWorld.reward_node[i]==node &&
        (tokens&prefix(i))==prefix(i)) tokens|=1<<i;
    return tokens;
}
bool8 cream_edge_open(const CreamEdge* edge,u8 tokens) {
    return edge && (tokens&edge->require)==edge->require;
}

static void clear_world(u32 seed) {
    int n,i;
    gCreamWorld.seed=seed;
    gCreamWorld.entry_node=gCreamWorld.goal_node=CC_NO_NODE;
    for(i=0;i<3;i++)gCreamWorld.reward_node[i]=CC_NO_NODE;
    gCreamWorld.attempts=gCreamWorld.fallback=0;
    gCreamWorld.required_rooms=0;gCreamWorld.required_steps=0;
    for(n=0;n<CC_NODES;n++) {
        gCreamWorld.degree[n]=0;gCreamWorld.content[n]=0;gCreamWorld.stage[n]=255;
        for(i=0;i<CC_EDGE_MAX;i++) {
            CreamEdge* e=&gCreamWorld.edges[n][i];
            e->target=CC_NO_NODE;e->kind=e->require=e->flags=0;
        }
    }
    for(n=0;n<CC_ROOMS;n++)gCreamWorld.corruption[n]=0;
}
static bool8 add_edge(int from,int to,int kind,int require,int flags) {
    int i=gCreamWorld.degree[from];CreamEdge* e;
    if(i>=CC_EDGE_MAX)return FALSE;
    e=&gCreamWorld.edges[from][i];e->target=to;e->kind=kind;e->require=require;e->flags=flags;
    gCreamWorld.degree[from]++;
    return TRUE;
}
static void remove_edge(int from,int to) {
    int at=cream_find_edge(from,to),i;
    if(at<0)return;
    for(i=at;i+1<gCreamWorld.degree[from];i++)gCreamWorld.edges[from][i]=gCreamWorld.edges[from][i+1];
    gCreamWorld.degree[from]--;
    gCreamWorld.edges[from][gCreamWorld.degree[from]].target=CC_NO_NODE;
    gCreamWorld.edges[from][gCreamWorld.degree[from]].kind=0;
    gCreamWorld.edges[from][gCreamWorld.degree[from]].require=0;
    gCreamWorld.edges[from][gCreamWorld.degree[from]].flags=0;
}
static int row_of(int node) {return cream_cell(node)/CC_WIDTH;}
static int col_of(int node) {return cream_cell(node)%CC_WIDTH;}
static int altitude(int node) {return (CC_HEIGHT-1-row_of(node))*2+cream_terrace(node);}
static int grid_neighbor(int node,int dir) {
    int room=cream_cell(node),terrace=cream_terrace(node),col=room%CC_WIDTH,row=room/CC_WIDTH;
    if(dir==0) {
        if(terrace==CC_LOWER)return node+1;
        return row ? cream_node(room-CC_WIDTH,CC_LOWER) : -1;
    }
    if(dir==1)return col+1<CC_WIDTH ? node+2 : -1;
    if(dir==2) {
        if(terrace==CC_UPPER)return node-1;
        return row+1<CC_HEIGHT ? cream_node(room+CC_WIDTH,CC_UPPER) : -1;
    }
    return col ? node-2 : -1;
}
static void add_grid_pair(int a,int b) {
    int h=altitude(b)-altitude(a);
    add_edge(a,b,h>0?CC_CLIMB:h<0?CC_DROP:CC_WALK,0,0);
    add_edge(b,a,h>0?CC_DROP:h<0?CC_CLIMB:CC_WALK,0,0);
}
static void tree(u32* state) {
    u8 stack[CC_NODES],visited[CC_NODES];int sp=0,n,i;
    for(i=0;i<CC_NODES;i++)visited[i]=0;
    stack[sp++]=gCreamWorld.entry_node;visited[gCreamWorld.entry_node]=1;
    while(sp) {
        int cand[4],count=0,cur=stack[sp-1];
        for(i=0;i<4;i++) {n=grid_neighbor(cur,i);if(n>=0 && !visited[n])cand[count++]=n;}
        if(!count) {sp--;continue;}
        n=cand[pick(state,count)];add_grid_pair(cur,n);visited[n]=1;stack[sp++]=n;
    }
}
/* Directed BFS, omitting the late return cave and optionally one cut pair.
   The other links form a tree, so the path is exact rather than heuristic. */
static int path_between(int start,int goal,u8* path,int cut_a,int cut_b) {
    u8 queue[CC_NODES],parent[CC_NODES];int head=0,tail=0,i,n,count=0;
    for(i=0;i<CC_NODES;i++)parent[i]=255;
    queue[tail++]=start;parent[start]=start;
    while(head<tail) {
        int cur=queue[head++];
        if(cur==goal)break;
        for(i=0;i<gCreamWorld.degree[cur];i++) {
            const CreamEdge* e=&gCreamWorld.edges[cur][i];n=e->target;
            if(e->flags&CC_LATE_SHORTCUT)continue;
            if((cur==cut_a && n==cut_b)||(cur==cut_b && n==cut_a))continue;
            if(parent[n]!=255)continue;
            parent[n]=cur;queue[tail++]=n;
        }
    }
    if(goal<0) {
        for(i=0;i<CC_NODES;i++)path[i]=parent[i]!=255;
        return tail;
    }
    if(parent[goal]==255)return 0;
    n=goal;
    do {count++;if(n==start)break;n=parent[n];}while(count<=CC_NODES);
    n=goal;
    for(i=count-1;i>=0;i--) {path[i]=n;if(n!=start)n=parent[n];}
    return count;
}
static bool8 has_cave(int node) {
    int i;for(i=0;i<gCreamWorld.degree[node];i++)if(gCreamWorld.edges[node][i].kind==CC_CAVE)return TRUE;
    return FALSE;
}
static bool8 add_long_drop(u32* state) {
    u8 path[CC_NODES],side[CC_NODES];int length=path_between(gCreamWorld.entry_node,gCreamWorld.goal_node,path,-1,-1);
    int start=pick(state,MAX(1,length-1)),k;
    for(k=0;k<length-1;k++) {
        int at=(start+k)%(length-1),src=-1,dst=-1,count=0,r,c,span;
        if(at<2 || at>length-4)continue;
        path_between(gCreamWorld.entry_node,-1,side,path[at],path[at+1]);
        for(c=0;c<CC_WIDTH;c++)for(r=0;r<CC_HEIGHT-2;r++)for(span=2;span<=4-r;span++) {
            int a=cream_node(r*CC_WIDTH+c,CC_UPPER);
            int b=cream_node((r+span)*CC_WIDTH+c,CC_LOWER);
            if(side[a] && !side[b] && pick(state,++count)==0) {src=a;dst=b;}
        }
        if(src<0)continue;
        remove_edge(path[at],path[at+1]);remove_edge(path[at+1],path[at]);
        if(!add_edge(src,dst,CC_DROP,0,CC_LONG_DROP))return FALSE;
        /* After all three capabilities, this paired cave makes the otherwise
           irreversible descent revisitable without bypassing its first use. */
        if(!add_edge(src,dst,CC_CAVE,CC_TOKEN_ALL,CC_LATE_SHORTCUT) ||
           !add_edge(dst,src,CC_CAVE,CC_TOKEN_ALL,CC_LATE_SHORTCUT))return FALSE;
        return TRUE;
    }
    return FALSE;
}
static bool8 add_required_cave(u32* state) {
    u8 path[CC_NODES];int length=path_between(gCreamWorld.entry_node,gCreamWorld.goal_node,path,-1,-1);
    int long_at=-1,a,b,source=-1,target=-1,cut=-1,count=0;
    if(length<19)return FALSE;
    for(a=0;a<length-1;a++) {
        const CreamEdge* e=cream_edge(path[a],cream_find_edge(path[a],path[a+1]));
        if(e->flags&CC_LONG_DROP)long_at=a;
    }
    if(long_at<0)return FALSE;
    /* Graft a nonlocal cave onto two points of the actual directed route.
       Cutting the intervening surface connection makes the cave meaningful;
       the displaced surface segments become content-bearing side branches.
       Its span never bypasses the deliberately required long descent. */
    for(a=2;a<length-4;a++)for(b=a+2;b<length-1 && b<=a+8;b++) {
        int shortened=length-(b-a-1);
        int moved_long=long_at-(long_at>=b ? b-a-1 : 0),third,third_ok=0;
        if(long_at>=a && long_at<b)continue;
        if(shortened<17 || moved_long<2 || moved_long>shortened-5 || a>shortened-4 || ABS(moved_long-a)<3)continue;
        if(has_cave(path[a]) || has_cave(path[b]))continue;
        if(ABS(row_of(path[a])-row_of(path[b]))+ABS(col_of(path[a])-col_of(path[b]))<2)continue;
        for(third=moved_long+3;third<=shortened-4;third++)if(ABS(third-a)>=3)third_ok=1;
        if(!third_ok)continue;
        if(pick(state,++count)==0) {source=a;target=b;}
    }
    if(source<0)return FALSE;
    cut=source+pick(state,target-source);
    remove_edge(path[cut],path[cut+1]);remove_edge(path[cut+1],path[cut]);
    return add_edge(path[source],path[target],CC_CAVE,0,0) &&
           add_edge(path[target],path[source],CC_CAVE,0,0);
}

static bool8 cut_pair(int a,int b,const u8* path,const u8* cuts) {
    int i;for(i=0;i<3;i++)if((a==path[cuts[i]] && b==path[cuts[i]+1]) ||
        (b==path[cuts[i]] && a==path[cuts[i]+1]))return TRUE;
    return FALSE;
}
static bool8 missions(u32* state) {
    u8 path[CC_NODES],cuts[3],queue[CC_NODES],branch[CC_NODES];
    int length=path_between(gCreamWorld.entry_node,gCreamWorld.goal_node,path,-1,-1);
    int i,j,long_at=-1,cave_at=-1,third=-1,count=0;
    if(length<17)return FALSE;
    for(i=0;i<length-1;i++) {
        const CreamEdge* e=cream_edge(path[i],cream_find_edge(path[i],path[i+1]));
        if(e->flags&CC_LONG_DROP)long_at=i;
        if(e->kind==CC_CAVE && !(e->flags&CC_LATE_SHORTCUT))cave_at=i;
    }
    if(long_at<2 || cave_at<2 || long_at>length-5 || cave_at>length-4 || ABS(long_at-cave_at)<3)return FALSE;
    /* Keep the long descent before the final capability: its late cave
       cannot be used to skip the first required jump. */
    for(i=long_at+3;i<=length-4;i++)if(ABS(i-cave_at)>=3 && pick(state,++count)==0)third=i;
    if(third<0)return FALSE;
    cuts[0]=long_at;cuts[1]=cave_at;cuts[2]=third;
    for(i=0;i<3;i++)for(j=i+1;j<3;j++)if(cuts[j]<cuts[i]) {u8 t=cuts[i];cuts[i]=cuts[j];cuts[j]=t;}
    for(i=0;i<CC_NODES;i++)gCreamWorld.stage[i]=255;
    for(i=0;i<4;i++) {
        int head=0,tail=0,start=i?path[cuts[i-1]+1]:gCreamWorld.entry_node;
        queue[tail++]=start;gCreamWorld.stage[start]=i;
        while(head<tail) {
            int cur=queue[head++];
            for(j=0;j<gCreamWorld.degree[cur];j++) {
                const CreamEdge* e=&gCreamWorld.edges[cur][j];int to=e->target;
                if(e->flags&CC_LATE_SHORTCUT || cut_pair(cur,to,path,cuts))continue;
                if(gCreamWorld.stage[to]!=255)continue;
                gCreamWorld.stage[to]=i;queue[tail++]=to;
            }
        }
    }
    for(i=0;i<CC_NODES;i++) {
        if(gCreamWorld.stage[i]>3)return FALSE;
        for(j=0;j<gCreamWorld.degree[i];j++) {
            CreamEdge* e=&gCreamWorld.edges[i][j];
            if(e->flags&CC_LATE_SHORTCUT)e->require=CC_TOKEN_ALL;
            else if(gCreamWorld.stage[e->target]>gCreamWorld.stage[i]) {
                e->require=prefix(gCreamWorld.stage[e->target]);e->flags|=CC_MISSION_GATE;
            } else if(gCreamWorld.stage[e->target]<gCreamWorld.stage[i])e->flags|=CC_MISSION_GATE;
        }
    }
    /* Prefer a branch end over an on-route handout. A reward remains on its
       own stage's component, before the capability lock it is intended for. */
    for(i=0;i<3;i++) {
        int best=-1,score=-1000,head=0,tail=0;
        for(j=0;j<CC_NODES;j++)branch[j]=255;
        for(j=0;j<length;j++)if(gCreamWorld.stage[path[j]]==i) {
            branch[path[j]]=0;queue[tail++]=path[j];
        }
        while(head<tail) {
            int cur=queue[head++],k;
            for(k=0;k<gCreamWorld.degree[cur];k++) {
                const CreamEdge* e=&gCreamWorld.edges[cur][k];int to=e->target;
                if((e->flags&CC_LATE_SHORTCUT) || gCreamWorld.stage[to]!=i || branch[to]!=255)continue;
                branch[to]=branch[cur]+1;queue[tail++]=to;
            }
        }
        for(j=0;j<CC_NODES;j++)if(gCreamWorld.stage[j]==i && j!=gCreamWorld.entry_node && !has_cave(j)) {
            int s=(int)(random_next(state)&7);
            if(branch[j])s+=16-MIN(20,branch[j]*2);
            if(gCreamWorld.degree[j]==1)s+=6;
            if(s>score) {score=s;best=j;}
        }
        if(best<0)return FALSE;
        gCreamWorld.reward_node[i]=best;
    }
    for(i=0;i<CC_NODES;i++) {
        u32 h=mix(gCreamWorld.seed^(u32)(i*0x9e3779b9u));
        gCreamWorld.content[i]=CC_CONTENT_ENEMIES;
        if((h&7)==0)gCreamWorld.content[i]|=CC_CONTENT_NPC;
        else if((h&7)==1)gCreamWorld.content[i]|=CC_CONTENT_HEAL;
        else if((h&7)<4)gCreamWorld.content[i]|=CC_CONTENT_CHEST;
        /* A full-capability dead end must hold a purpose beyond a fight. */
        if(gCreamWorld.degree[i]<=1 && !(gCreamWorld.content[i]&CC_CONTENT_CHEST))
            gCreamWorld.content[i]|=(h&1)?CC_CONTENT_CHEST:CC_CONTENT_CACHE;
    }
    for(i=0;i<3;i++)gCreamWorld.content[gCreamWorld.reward_node[i]]|=CC_CONTENT_MISSION;
    gCreamWorld.content[gCreamWorld.entry_node]=CC_CONTENT_ENTRY|CC_CONTENT_HEAL;
    gCreamWorld.content[gCreamWorld.goal_node]=CC_CONTENT_BOSS;
    for(i=0;i<CC_ROOMS;i++)gCreamWorld.corruption[i]=MIN(2,(MAX(gCreamWorld.stage[i*2],gCreamWorld.stage[i*2+1])*2+4-i/5)/4);
    gCreamWorld.corruption[cream_cell(gCreamWorld.entry_node)]=0;
    gCreamWorld.corruption[cream_cell(gCreamWorld.goal_node)]=2;
    return TRUE;
}

static int state_id(int node,int tokens) {return tokens*CC_NODES+node;}
static bool8 bit_get(const u8* bits,int id) {return (bits[id>>3]>>(id&7))&1;}
static void bit_set(u8* bits,int id) {bits[id>>3]|=1<<(id&7);}

/* The graph has only400 node/capability states. Incoming source IDs avoid a
   large reverse-edge copy while keeping the reverse win flood bounded. */
static bool8 verify_states(void) {
    u8 reachable[50]={0},winning[50]={0};
    u8 incoming[CC_NODES][CC_EDGE_MAX],incount[CC_NODES]={0};
    u16 queue[CC_NODES*8];int head=0,tail=0,n,i,t;
    for(n=0;n<CC_NODES;n++)for(i=0;i<gCreamWorld.degree[n];i++) {
        int to=gCreamWorld.edges[n][i].target,j,found=0;
        for(j=0;j<incount[to];j++)if(incoming[to][j]==n)found=1;
        if(found)continue;
        if(incount[to]>=CC_EDGE_MAX)return FALSE;
        incoming[to][incount[to]++]=n;
    }
    /* Check every possible inherited inventory, not just a tool-free start. */
    for(t=0;t<8;t++) {
        int id=state_id(gCreamWorld.entry_node,cream_collect_tokens(gCreamWorld.entry_node,t));
        if(!bit_get(reachable,id)) {bit_set(reachable,id);queue[tail++]=id;}
    }
    while(head<tail) {
        int id=queue[head++],cur=id%CC_NODES,mask=id/CC_NODES;
        for(i=0;i<gCreamWorld.degree[cur];i++) {
            const CreamEdge* e=&gCreamWorld.edges[cur][i];int to,next;
            if(!cream_edge_open(e,mask))continue;
            to=cream_collect_tokens(e->target,mask);next=state_id(e->target,to);
            if(!bit_get(reachable,next)) {bit_set(reachable,next);queue[tail++]=next;}
        }
    }
    head=tail=0;n=state_id(gCreamWorld.goal_node,CC_TOKEN_ALL);bit_set(winning,n);queue[tail++]=n;
    while(head<tail) {
        int id=queue[head++],cur=id%CC_NODES,mask=id/CC_NODES;
        int reward=cream_reward_bit(cur),masks[2]={mask,mask^reward},count=reward?2:1;
        for(i=0;i<incount[cur];i++) {
            int from=incoming[cur][i],k,m;
            for(m=0;m<count;m++) {
                int previous=masks[m],pid=state_id(from,previous);
                if(cream_collect_tokens(cur,previous)!=mask || cream_collect_tokens(from,previous)!=previous)continue;
                if(bit_get(winning,pid))continue;
                for(k=0;k<gCreamWorld.degree[from];k++) {
                    const CreamEdge* e=&gCreamWorld.edges[from][k];
                    if(e->target==cur && cream_edge_open(e,previous))break;
                }
                if(k<gCreamWorld.degree[from]) {bit_set(winning,pid);queue[tail++]=pid;}
            }
        }
    }
    for(n=0;n<CC_NODES*8;n++)if(bit_get(reachable,n) && !bit_get(winning,n))return FALSE;
    for(n=0;n<CC_NODES;n++)if(!bit_get(reachable,state_id(n,CC_TOKEN_ALL)))return FALSE;
    return TRUE;
}

bool8 cream_world_validate(void) {
    int n,i,long_count=0,cave_count=0;
    if(gCreamWorld.entry_node>=CC_NODES || gCreamWorld.goal_node>=CC_NODES ||
       row_of(gCreamWorld.entry_node)!=4 || cream_terrace(gCreamWorld.entry_node)!=CC_LOWER ||
       row_of(gCreamWorld.goal_node)!=0 || cream_terrace(gCreamWorld.goal_node)!=CC_UPPER)return FALSE;
    if(gCreamWorld.corruption[cream_cell(gCreamWorld.entry_node)]!=0 ||
       gCreamWorld.corruption[cream_cell(gCreamWorld.goal_node)]!=2)return FALSE;
    for(n=0;n<CC_ROOMS;n++)if(gCreamWorld.corruption[n]>2)return FALSE;
    for(n=0;n<CC_NODES;n++) {
        if(!gCreamWorld.degree[n] || gCreamWorld.degree[n]>CC_EDGE_MAX || gCreamWorld.stage[n]>3)return FALSE;
        if((gCreamWorld.content[n]&(CC_CONTENT_CHEST|CC_CONTENT_CACHE))==(CC_CONTENT_CHEST|CC_CONTENT_CACHE))return FALSE;
        if(gCreamWorld.degree[n]<=1 && !(gCreamWorld.content[n]&~CC_CONTENT_ENEMIES))return FALSE;
        for(i=0;i<gCreamWorld.degree[n];i++) {
            const CreamEdge* e=&gCreamWorld.edges[n][i];int to=e->target,dx,dy;
            if(to>=CC_NODES || e->require>CC_TOKEN_ALL)return FALSE;
            dx=col_of(to)-col_of(n);dy=row_of(to)-row_of(n);
            if(e->kind==CC_WALK) {
                if(ABS(dx)!=1 || dy || cream_terrace(to)!=cream_terrace(n))return FALSE;
            } else if(e->kind==CC_CLIMB) {
                if(dx || !((to==n+1 && cream_terrace(n)==CC_LOWER) ||
                    (dy==-1 && cream_terrace(n)==CC_UPPER && cream_terrace(to)==CC_LOWER)))return FALSE;
            } else if(e->kind==CC_DROP) {
                if(e->flags&CC_LONG_DROP) {
                    if(dx || dy<2 || dy>4 || cream_terrace(n)!=CC_UPPER || cream_terrace(to)!=CC_LOWER)return FALSE;
                    long_count++;
                } else if(dx || !((to==n-1 && cream_terrace(n)==CC_UPPER) ||
                    (dy==1 && cream_terrace(n)==CC_LOWER && cream_terrace(to)==CC_UPPER)))return FALSE;
            } else if(e->kind==CC_CAVE) {
                int j,paired=0;
                for(j=0;j<gCreamWorld.degree[to];j++)if(gCreamWorld.edges[to][j].target==n && gCreamWorld.edges[to][j].kind==CC_CAVE)paired=1;
                if(!paired || cream_cell(to)==cream_cell(n))return FALSE;
                cave_count++;
            } else return FALSE;
        }
    }
    if(!long_count || cave_count<4)return FALSE;
    for(i=0;i<3;i++)if(gCreamWorld.reward_node[i]>=CC_NODES ||
        gCreamWorld.stage[gCreamWorld.reward_node[i]]!=i ||
        !(gCreamWorld.content[gCreamWorld.reward_node[i]]&CC_CONTENT_MISSION))return FALSE;
    return verify_states();
}

int cream_solution(u8 start_tokens,u8* out,int capacity) {
    u16 parent[CC_NODES*8],queue[CC_NODES*8];
    int head=0,tail=0,i,start,end=-1,length=0,id;
    for(i=0;i<CC_NODES*8;i++)parent[i]=0xffff;
    start=state_id(gCreamWorld.entry_node,cream_collect_tokens(gCreamWorld.entry_node,start_tokens));
    queue[tail++]=start;parent[start]=start;
    while(head<tail) {
        int cur=queue[head++],node=cur%CC_NODES,mask=cur/CC_NODES;
        if(node==gCreamWorld.goal_node && mask==CC_TOKEN_ALL) {end=cur;break;}
        for(i=0;i<gCreamWorld.degree[node];i++) {
            const CreamEdge* e=&gCreamWorld.edges[node][i];int next;
            if(!cream_edge_open(e,mask))continue;
            next=state_id(e->target,cream_collect_tokens(e->target,mask));
            if(parent[next]!=0xffff)continue;
            parent[next]=cur;queue[tail++]=next;
        }
    }
    if(end<0)return 0;
    id=end;
    do {length++;if(id==start)break;id=parent[id];}while(length<CC_NODES*8);
    if(out && capacity>=length) {
        id=end;for(i=length-1;i>=0;i--) {out[i]=id%CC_NODES;if(id!=start)id=parent[id];}
    }
    return length;
}

static bool8 candidate(u32 seed,u32 shape_seed) {
    u32 state=shape_seed?shape_seed:1;u8 path[CC_NODES*4];
    int length,i;u32 rooms=0;
    clear_world(seed);
    gCreamWorld.entry_node=cream_node(20+pick(&state,5),CC_LOWER);
    tree(&state);
    gCreamWorld.goal_node=cream_node(pick(&state,CC_WIDTH),CC_UPPER);
    if(!add_long_drop(&state) || !add_required_cave(&state) || !missions(&state) || !cream_world_validate())return FALSE;
    length=cream_solution(0,path,sizeof(path));
    if(length<19 || length>(int)sizeof(path))return FALSE;
    for(i=0;i<length;i++)rooms|=1u<<cream_cell(path[i]);
    gCreamWorld.required_rooms=0;
    for(i=0;i<CC_ROOMS;i++)gCreamWorld.required_rooms+=(rooms>>i)&1;
    if(gCreamWorld.required_rooms>22)return FALSE;
    gCreamWorld.required_steps=length-1;
    return TRUE;
}

#include "cream_world_fallback.inc"

bool8 cream_generate(u32 seed) {
    int attempt;
    for(attempt=0;attempt<24;attempt++)if(candidate(seed,mix(seed^0x43555244u^(u32)(attempt*0x9e3779b9u)))) {
        gCreamWorld.attempts=attempt+1;return TRUE;
    }
    /* This is a solved ROM certificate, not an unbounded retry loop and not
       an unchecked emergency random layout. Its structure is independent of
       the run seed; the native room painter still receives that run seed. */
    return cream_generate_certified(seed);
}

bool8 cream_generate_certified(u32 seed) {
    gCreamWorld=sCreamCertificate;
    gCreamWorld.seed=seed;
    return cream_world_validate();
}
