import sys,json,math,re,os,glob; sys.path.insert(0,'./tools')
from lib import *; from common import *
from concurrent.futures import ThreadPoolExecutor
NS=8
tasks=json.load(open(S+'data/tasks.json'))
pre=[load_template(p)|{'file':p} for p in sorted(glob.glob(S+'prompts/base/*.txt'))]
OUT=S+'data/base_results.jsonl'
done=set()
if os.path.exists(OUT):
    for l in open(OUT): r=json.loads(l); done.add((r['task'],r['prefill'],r['order']))
def label_dist(top,labels):
    d={l:0.0 for l in labels}
    for k,lp in top.items():
        s=k.strip()
        if s in d: d[s]+=math.exp(lp)
    return d
def run_sample(prompt,mode,marker,labels,seed):
    c=tinker(prompt,330 if mode=='sample' else 40,temperature=0.8 if mode=='sample' else 1.0,top_p=1.0,logprobs=20,seed=seed)
    text=c['text']; lp=c.get('logprobs') or {}
    toks=lp.get('tokens',[]); offs=lp.get('text_offset',[]); tops=lp.get('top_logprobs',[])
    if mode=='slot':
        dist=label_dist(tops[0],labels) if tops else None
        m=re.match(r'\s*([A-E])\b',text)
        return {'text':text,'verdict':m.group(1) if m and m.group(1) in labels else None,'dist':dist}
    m=re.search(re.escape(marker),text)
    if not m: return {'text':text,'verdict':None,'dist':None}
    end=m.end(); idx=next((i for i,o in enumerate(offs) if o>=end),None)
    dist=label_dist(tops[idx],labels) if idx is not None and idx<len(tops) else None
    v=re.match(r'\s*([A-E])\b',text[end:])
    cut=end+(v.end() if v else 0)
    return {'text':text[:cut],'verdict':v.group(1) if v and v.group(1) in labels else None,'dist':dist}
def job(args):
    ti,p,oi=args
    t=tasks[ti]
    key=(t['id'],p['id'],oi)
    if key in done: return
    prompt,cids=render(p,t,t['orders'][oi]); labels=list('ABCDE'[:len(cids)])
    seeds=[hash((t['id'],p['id'],oi,k))%2**31 for k in range(NS)]
    seeds=[abs(1000003*(ti+1)+10007*(pi_of[p['id']]+1)+101*oi+k) for k in range(NS)]
    samples=[run_sample(prompt,p['mode'],p.get('marker'),labels,s) for s in seeds]
    # exact distribution: first sample for slot prompts (same prompt -> same next-token dist); mean over samples for sample mode
    ds=[s['dist'] for s in samples if s['dist']]
    if p['mode']=='slot': mass=ds[0] if ds else None
    else: mass={l:sum(d[l] for d in ds)/len(ds) for l in labels} if ds else None
    norm=None; lm=None
    if mass:
        lm=sum(mass.values()); norm={l:(mass[l]/lm if lm>0 else None) for l in labels}
    rec={'task':t['id'],'prefill':p['id'],'order':oi,'prompt':prompt,'labels':labels,'label_to_cid':dict(zip(labels,cids)),'mode':p['mode'],
         'dist_norm':norm,'label_mass':lm,'n_with_dist':len(ds),'samples':samples}
    with open(OUT,'a') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
pi_of={p['id']:i for i,p in enumerate(pre)}
only=sys.argv[1:] 
jobs=[(ti,p,oi) for ti,t in enumerate(tasks) for p in pre for oi in (0,1) if (not only or t['id'] in only)]
with ThreadPoolExecutor(6) as ex: list(ex.map(job,jobs))
print(spend())
