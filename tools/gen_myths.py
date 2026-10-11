import sys,json,re,random; sys.path.insert(0,'./tools')
from lib import *
from concurrent.futures import ThreadPoolExecutor
OPENERS=[
 "In the world of Hollowmere, where the rivers run uphill at night, strange tales are told of how the first light was made.",
 "In the world of the Salt Teeth, a chain of islands no map agrees on, strange tales are told of the first fisherman.",
 "In the world of Ankh-Ember, where every house keeps a small fire that must never be named, strange tales are told of how fire came to be shared.",
 "In the world of the Tin Meadows, where the wind has a postal address, strange tales are told of the first word ever spoken.",
 "In the world of Orrery Deep, the sea at the bottom of the sky, strange tales are told of why the stars keep their distance.",
 "In the world of the Grey Orchard, strange tales are told of the first death, and of the tree that apologised.",
]
PAIRS=[('opus46','opus55'),('sol61','gpt4o'),('opus46','sol61'),('opus55','gpt4o'),('opus46','gpt4o'),('opus55','sol61')]
GEN_PROMPT="Complete this creation myth. Continue directly from where the opening leaves off, in one or two paragraphs, about 150 words. Output only the continuation, nothing else.\n\nOpening: {o}"
def trim(t):
    t=t.rstrip()
    m=list(re.finditer(r'[.!?…]["”’\')\]]*(?=\s|$)',t))
    return t[:m[-1].end()].rstrip() if m else t
def one(i,job):
    o=OPENERS[i]
    if job[0]=='base':
        c=tinker(o,230,temperature=0.8,top_p=0.95,seed=1000*i+job[1])
        raw=c['text']; txt=raw.split('\n\n\n')[0]
        m=re.search(r'[\u3000-\u9fff\uac00-\ud7af]|###|\*\*|\n(?:Here are|Question|Q:)',txt)
        cut=txt[:m.start()] if m else txt
        return i,{'kind':'base','origin':f'Qwen 3.5 35B-A3B Base (plain continuation, sample {job[1]+1})','continuation':trim(cut),'raw':raw,'raw_finish':c['finish_reason'],'sampling':'temp 0.8, top_p 0.95, max_tokens 230, prompt = opener only','derailed':bool(m)}
    m=job[1]
    r=openrouter(m,[{'role':'user','content':GEN_PROMPT.format(o=o)}],1500 if m=='sol61' else 600,temperature=None if m=='sol61' else 1.0,reasoning={'effort':'low','exclude':True} if m=='sol61' else None)
    return i,{'kind':'instruct','origin':OR_LABEL[m]+' (asked to complete)','continuation':r['text'].strip(),'raw_finish':r['finish'],'sampling':'default/temp 1.0'}
jobs=[]
for i in range(6):
    jobs+= [(i,('base',k)) for k in range(6)]+[(i,('or',PAIRS[i][0])),(i,('or',PAIRS[i][1]))]
with ThreadPoolExecutor(6) as ex: res=list(ex.map(lambda j: one(*j),jobs))
tasks=[]
for i,o in enumerate(OPENERS):
    allc=[r for k,r in res if k==i]
    for c in allc: c['text']=o+' '+c['continuation']
    ok=lambda c: c['kind']!='base' or (not c['derailed'] and len(c['continuation'].split())>=90)
    base_ok=[c for c in allc if c['kind']=='base' and ok(c)][:2]
    unused=[c for c in allc if c['kind']=='base' and c not in base_ok]
    cs=base_ok+[c for c in allc if c['kind']=='instruct']
    tasks.append({'id':f'myth-{i+1}','type':'myth','source':o,'unused_base_samples':[{'text':c['text'],'raw':c['raw'],'derailed':c['derailed'],'origin':c['origin']} for c in unused],'candidates':[{'text':c['text'],'origins':[c['origin']],'kinds':[c['kind']],'finish':c['raw_finish'],'sampling':c['sampling']} for c in cs]})
json.dump({'openers':OPENERS,'gen_prompt':GEN_PROMPT,'tasks':tasks},open('./data/myth_tasks_raw.json','w'),ensure_ascii=False,indent=1)
print(spend())
for t in tasks[:2]:
    for c in t['candidates']: print(c['origins'],len(c['text'].split()),c['finish'],'\n',c['text'],'\n')
