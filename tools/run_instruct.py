import sys,json,re,os,glob; sys.path.insert(0,'./tools')
from lib import *; from common import *
from concurrent.futures import ThreadPoolExecutor
tasks=json.load(open(S+'data/tasks.json'))
pre=[load_template(p)|{'file':p} for p in sorted(glob.glob(S+'prompts/instruct/*.txt'))]
OUT=S+'data/instruct_results.jsonl'
JUDGES=['opus46','opus55','sol61','gpt4o']
done=set()
if os.path.exists(OUT):
    for l in open(OUT): r=json.loads(l); done.add((r['task'],r['prefill'],r['order'],r['judge']))
def parse(text,labels):
    m=re.findall(r'Preferred:\s*\**\(?([A-E])\b',text)
    if m: return m[-1]
    m=re.match(r'\s*\**\(?([A-E])\b',text)
    return m.group(1) if m and m.group(1) in labels else None
def job(a):
    ti,p,oi,j=a; t=tasks[ti]
    if (t['id'],p['id'],oi,j) in done: return
    prompt,cids=render(p,t,t['orders'][oi]); labels=list('ABCDE'[:len(cids)])
    try:
        r=openrouter(j,[{'role':'user','content':prompt}],2500 if j=='sol61' else (1500 if j=='opus55' else 500),reasoning={'effort':'low','exclude':True} if j=='sol61' else None)
        rec={'task':t['id'],'prefill':p['id'],'order':oi,'judge':j,'prompt':prompt,'labels':labels,'label_to_cid':dict(zip(labels,cids)),'text':r['text'],'verdict':parse(r['text'],labels),'finish':r['finish'],'provider':r['provider'],'model':r['model'],'usage':r['usage'],'cost':r['usage'].get('cost')}
    except Exception as e:
        rec={'task':t['id'],'prefill':p['id'],'order':oi,'judge':j,'prompt':prompt,'labels':labels,'label_to_cid':dict(zip(labels,cids)),'error':str(e)[:300],'verdict':None}
    with open(OUT,'a') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
only=sys.argv[1:]
jobs=[(ti,p,oi,j) for ti,t in enumerate(tasks) for p in pre for oi in (0,1) for j in JUDGES if (not only or t['id'] in only)]
with ThreadPoolExecutor(6) as ex: list(ex.map(job,jobs))
print(spend())
