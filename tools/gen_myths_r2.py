import sys,json,re,random; sys.path.insert(0,'./tools')
from lib import *
from concurrent.futures import ThreadPoolExecutor
src=open('./tools/gen_myths.py').read()
ns={}; exec(src.split('def trim')[0].replace('from lib import *','').replace('from concurrent.futures import ThreadPoolExecutor',''),ns)
OPENERS=ns['OPENERS']; GEN_PROMPT=ns['GEN_PROMPT']
def trim(t):
    t=t.rstrip(); m=list(re.finditer(r'[.!?…]["”’\')\]]*(?=\s|$)',t)); return t[:m[-1].end()].rstrip() if m else t
TEMPS=[0.6,0.8,1.0,1.2]
def base_one(i,k):
    o=OPENERS[i]
    for attempt in range(6):
        c=tinker(o,230,temperature=TEMPS[k],top_p=0.95,seed=50000+1000*i+10*k+attempt)
        raw=c['text'].split('\n\n\n')[0]
        m=re.search(r'[\u3000-\u9fff\uac00-\ud7af]|###|\*\*|\n(?:Here are|Question|Q:)',raw)
        cut=trim(raw[:m.start()] if m else raw)
        if not m and len(cut.split())>=90: return cut,attempt+1,c['finish_reason']
    return cut,6,'rejected-all'
def inst_one(i,k):
    r=openrouter('opus55',[{'role':'user','content':GEN_PROMPT.format(o=OPENERS[i])}],700,temperature=1.0)
    return r['text'].strip(),1,r['finish']
jobs=[(i,k,'B') for i in range(6) for k in range(4)]+[(i,k,'I') for i in range(6) for k in range(4)]
def go(j):
    i,k,w=j; return j,(base_one(i,k) if w=='B' else inst_one(i,k))
with ThreadPoolExecutor(6) as ex: res=dict(ex.map(go,jobs))
tasks=[]
for w,name in (('B','all-Qwen-base'),('I','all-Opus-5.5')):
    for i,o in enumerate(OPENERS):
        cs=[]
        for k in range(4):
            txt,att,fin=res[(i,k,w)]
            cs.append({'text':txt,'full_text':o+' '+txt,'origins':[f'Qwen 3.5 35B-A3B Base, temp {TEMPS[k]} (try {att})' if w=='B' else f'Opus 5.5, sample {k+1}, temp 1.0'],'kinds':['base' if w=='B' else 'instruct'],'finish':fin,'cid':f'myth{w}-{i+1}-c{k}'})
        idx=list(range(4)); random.Random(4242+i+(0 if w=='B' else 100)).shuffle(idx)
        tasks.append({'id':f'myth{w}-{i+1}','type':'myth','set':name,'source':o,'display_source':o,'context':'','candidates':cs,'orders':[idx,idx[::-1]]})
json.dump(tasks,open('./data/r2/tasks_origin_controlled.json','w'),ensure_ascii=False,indent=1)
print(spend()); print([ (t['id'],[len(c['text'].split()) for c in t['candidates']]) for t in tasks])
