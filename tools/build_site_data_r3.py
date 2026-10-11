import json,glob,os,sys,statistics as st
sys.path.insert(0,'./tools')
from common import *
R=S+'data/r3/'; os.makedirs(S+'site-data/r3/task',exist_ok=True)
sm=json.load(open(R+'summary_r3.json')); D=json.load(open(R+'tasks_josh_myths.json')); tasks=D['tasks']
import re
exec(open(S+'tools/analyze_r3.py').read().split("T={t['id']")[0].split("tasks=json.load")[0]) if False else None
def jl(p): return [json.loads(l) for l in open(p)]
base=jl(R+'base_results.jsonl'); inst=jl(R+'instruct_results.jsonl'); scores=json.load(open(R+'scores.json')); pri=jl(R+'calibration_priors.jsonl')
import collections
P=collections.defaultdict(list)
for r in pri: P[r['prefill']].append(r['dist'])
PRIOR={k:{l:max(st.mean(d[l] for d in v),1e-4) for l in v[0]} for k,v in P.items()}
meta={m['id']:m for m in sm['tasks_meta']}
ptex={}
for t in tasks:
    tid=t['id']; short={c['cid']:i+1 for i,c in enumerate(t['candidates'])}
    for c,mc in zip(t['candidates'],meta[tid]['cands']): c['ornate']=mc['ornate']; c['is_longest']=mc['longest']; c['words']=mc['words']; c['src']=mc['src']
    b=[r for r in base if r['task']==tid]
    for r in b:
        r['label_to_short']={l:short[c] for l,c in r['label_to_cid'].items()}
        if r['mode']=='slot' and r['dist_norm']:
            pr=PRIOR[r['prefill']]; q={l:(r['dist_norm'][l] or 0)/pr[l] for l in r['labels']}; z=sum(q.values()); r['cal_dist']={l:q[l]/z for l in q}
    i=[r for r in inst if r['task']==tid]
    for r in i: r['label_to_short']={l:short[c] for l,c in r['label_to_cid'].items()}
    sc=sm['scoring']['rows'][tid]
    json.dump({'task':t,'base':b,'instruct':i,'scoring':sc},open(S+f'site-data/r3/task/{tid}.json','w'),ensure_ascii=False)
for r in scores:
    if r['task']=='jm-P09': ptex[r['prefix_id']]=r['prefix_text']
def files(d):
    out=[]
    for p in sorted(glob.glob(S+f'prompts/{d}/*.txt')):
        m=load_template(p); out.append({'id':m['id'],'title':m['title'],'mode':m.get('mode',m.get('group','')),'raw':open(p).read()})
    return out
spend=json.load(open(S+'data/spend_r3.json')) if os.path.exists(S+'data/spend_r3.json') else None
idx={'tasks':[{'id':t['id'],'set':t['set'],'prompt_id':t['prompt_id'],'title':t['source'].split('\n')[0][:60]} for t in tasks],'wrapper':D['wrapper'],'template':D['template'],'summary':sm,'prefills':files('base-r3'),'score_prefixes':files('score'),'instruct_prefills':files('instruct'),'prefix_example':ptex,'spend':spend}
json.dump(idx,open(S+'site-data/r3/index.json','w'),ensure_ascii=False); print('ok')
