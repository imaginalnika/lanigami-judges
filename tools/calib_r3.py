import sys,json,math,glob,os; sys.path.insert(0,'./tools')
from lib import *; from common import *
from concurrent.futures import ThreadPoolExecutor
tasks=json.load(open(S+'data/r3/tasks.json'))
pre=[load_template(p) for p in sorted(glob.glob(S+'prompts/base-r3/*.txt'))]
pre=[p for p in pre if p['mode']=='slot']
OUT=S+'data/r3/calibration_priors.jsonl'
done=set()
if os.path.exists(OUT):
    for l in open(OUT): r=json.loads(l); done.add((r['task'],r['prefill']))
def job(a):
    t,p=a
    if (t['id'],p['id']) in done: return
    stub=dict(t,candidates=[dict(c,text='N/A') for c in t['candidates']])
    prompt,_=render(p,stub,list(range(len(t['candidates']))))
    labels=list('ABCDEFG'[:len(t['candidates'])])
    c=tinker(prompt,1,temperature=1.0,logprobs=20)
    top=c['logprobs']['top_logprobs'][0]; d={l:0.0 for l in labels}
    for k,lp in top.items():
        if k.strip() in d: d[k.strip()]+=math.exp(lp)
    m=sum(d.values())
    with open(OUT,'a') as f: f.write(json.dumps({'task':t['id'],'prefill':p['id'],'type':t['type'],'n':len(labels),'prompt':prompt,'label_mass':m,'dist':{l:(v/m if m>0 else None) for l,v in d.items()}})+'\n')
with ThreadPoolExecutor(6) as ex: list(ex.map(job,[(t,p) for t in tasks for p in pre]))
print('done')
