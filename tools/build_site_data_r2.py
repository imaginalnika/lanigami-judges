import json,glob,os,collections,sys,math
sys.path.insert(0,'./tools')
from common import *
R=S+'data/r2/'
os.makedirs(S+'site-data/r2/task',exist_ok=True)
sm=json.load(open(R+'summary_r2.json'))
tasks=json.load(open(S+'data/tasks_feats.json'))+json.load(open(R+'tasks_oc_feats.json'))
def jl(p): return [json.loads(l) for l in open(p)] if glob.glob(p) else []
base=jl(S+'data/r2/base_r2_main.jsonl')+jl(R+'base_origin_controlled_r1prefills.jsonl')+jl(R+'base_origin_controlled_r2prefills.jsonl')
inst=jl(R+'instruct_origin_controlled.jsonl'); fold=json.load(open(R+'fold_annotated.json'))
priors=sm['priors']; T={t['id']:t for t in tasks}
for t in tasks:
    tid=t['id']; cid_idx={c['cid']:i+1 for i,c in enumerate(t['candidates'])}
    b=[r for r in base if r['task']==tid]
    for r in b:
        r['label_to_short']={l:cid_idx[c] for l,c in r['label_to_cid'].items()}
        if r['mode']=='slot' and r['dist_norm']:
            pr=priors.get(f"{r['prefill']}|{t['type']}|{len(r['labels'])}")
            if pr:
                q={l:(r['dist_norm'][l] or 0)/pr[l] for l in r['labels']}; z=sum(q.values()); r['cal_dist']={l:q[l]/z for l in q}; r['prior']=pr
    i=[r for r in inst if r['task']==tid]
    for r in i: r['label_to_short']={l:cid_idx[c] for l,c in r['label_to_cid'].items()}
    f=[r for r in fold if r['task']==tid]
    for r in f: r['label_to_short']={l:cid_idx[c] for l,c in r['label_to_cid'].items()}
    sc=sm['sec1']['rows'][tid]
    ptxt=json.load(open(R+'scores.json')) if False else None
    json.dump({'task':t,'base':b,'instruct':i,'fold':f,'scoring':sc},open(S+f'site-data/r2/task/{tid}.json','w'),ensure_ascii=False)
def files(d):
    out=[]
    for p in sorted(glob.glob(S+f'prompts/{d}/*.txt')):
        m=load_template(p); out.append({'id':m['id'],'title':m['title'],'mode':m.get('mode',m.get('group','')),'raw':open(p).read()})
    return out
scores=json.load(open(R+'scores.json')); ptexts={}
for r in scores:
    if r['task'] in ('tr-DH-0351','myth-3') : ptexts.setdefault(r['task'],{})[r['prefix_id']]=r['prefix_text']
idx={'tasks':[{'id':t['id'],'type':t['type'],'set':t.get('set','mixed-origin'),'title':t['source'][:50]} for t in tasks],
 'prefills_r2':files('base-r2'),'prefills_score':files('score'),'prefills_fold':files('fold'),'summary':sm,'prefix_examples':ptexts,
 'spend':json.load(open(S+'data/spend_r2.json')) if os.path.exists(S+'data/spend_r2.json') else None}
json.dump(idx,open(S+'site-data/r2/index.json','w'),ensure_ascii=False)
print('ok')
