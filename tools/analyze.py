import json,re,math,glob,collections,statistics as st,sys
sys.path.insert(0,'./tools')
from common import *
tasks=json.load(open(S+'data/tasks.json'))
base=[json.loads(l) for l in open(S+'data/base_results.jsonl')]
inst=[json.loads(l) for l in open(S+'data/instruct_results.jsonl')]
T={t['id']:t for t in tasks}
def feats(text):
    w=re.findall(r"[A-Za-z']+",text); n=max(len(w),1)
    sents=max(len(re.findall(r'[.!?…]+(?:\s|$)',text)),1)
    return {'words':len(text.split()),'chars':len(text),
      'long_word_ratio':sum(len(x)>=9 for x in w)/n,
      'punct_per100':100*len(re.findall(r'[,;:—–-]',text))/n,
      'ly_per100':100*sum(x.lower().endswith('ly') for x in w)/n,
      'words_per_sentence':n/sents}
for t in tasks:
    for c in t['candidates']: c['feats']=feats(c['text'])
    # ornateness proxy: mean within-task normalized rank over 4 measures (0=plainest, 1=most ornate)
    keys=['words','long_word_ratio','punct_per100','ly_per100']
    n=len(t['candidates'])
    for c in t['candidates']: c['ornate']=0
    for k in keys:
        vals=[c['feats'][k] for c in t['candidates']]
        for c in t['candidates']:
            lt=sum(v<c['feats'][k] for v in vals); eq=sum(v==c['feats'][k] for v in vals)
            c['ornate']+=((lt+(eq-1)/2)/(n-1))/len(keys)
    L=[c['feats']['words'] for c in t['candidates']]
    for c in t['candidates']: c['is_longest']=c['feats']['words']==max(L); c['is_base']='base' in c['kinds']
    t['kind_of']={c['cid']:c for c in t['candidates']}
def cdist(rec):
    """distribution over cids for a base record"""
    if not rec['dist_norm']: return None
    return {rec['label_to_cid'][l]:p for l,p in rec['dist_norm'].items() if p is not None}
# per (task, judgeprompt) -> aggregated dist over orders
agg=collections.defaultdict(lambda: collections.defaultdict(dict))  # key (judge,prompt)-> task -> {cid:p}
meta={}
for r in base:
    d=cdist(r)
    if d is None: continue
    key=('qwen35b-base',r['prefill']); a=agg[key][r['task']]
    for c,p in d.items(): a[c]=a.get(c,0)+p/2
    meta[key]={'type':'base','mode':r['mode']}
errs=collections.Counter()
for r in inst:
    if r.get('error'): errs[r['judge']]+=1; continue
    if not r['verdict']: errs[r['judge']+':unparsed']+=1; continue
    key=(r['judge'],r['prefill']); a=agg[key][r['task']]
    c=r['label_to_cid'][r['verdict']]; a[c]=a.get(c,0)+0.5
    meta[key]={'type':'instruct'}
def top(d):
    m=max(d.values()); w=[c for c,p in d.items() if abs(p-m)<1e-9]
    return w[0] if len(w)==1 else None
rows=[]
for key,tk in sorted(agg.items()):
    out={'judge':key[0],'prompt':key[1],**meta[key]}
    for typ in ('translation','myth','all'):
        ts=[t for t in tk if typ=='all' or T[t]['type']==typ]
        if not ts: continue
        ex_long=[];ex_orn=[];ex_base=[];chance_base=[];chance_long=[];ex_rank=[]
        for t in ts:
            d=tk[t]; tot=sum(d.values()); d={c:p/tot for c,p in d.items()}
            cs=T[t]['kind_of']
            ex_long.append(sum(p for c,p in d.items() if cs[c]['is_longest']))
            ex_orn.append(sum(p*cs[c]['ornate'] for c,p in d.items()))
            ex_base.append(sum(p for c,p in d.items() if cs[c]['is_base']))
            chance_base.append(sum(c['is_base'] for c in T[t]['candidates'])/len(cs))
            chance_long.append(sum(c['is_longest'] for c in T[t]['candidates'])/len(cs))
        out[typ]={'n_tasks':len(ts),'p_longest':st.mean(ex_long),'chance_longest':st.mean(chance_long),'mean_ornate_rank_of_pick':st.mean(ex_orn),'p_base_origin':st.mean(ex_base),'chance_base_origin':st.mean(chance_base)}
    rows.append(out)
# agreement: top pick agreement across keys
keys=sorted(agg)
def toppick(key,t): 
    d=agg[key].get(t); return top(d) if d else None
agree={}
for a in keys:
    for b in keys:
        s=n=0
        for t in T:
            x=toppick(a,t); y=toppick(b,t)
            if x and y: n+=1; s+= x==y
        agree[f'{a[0]}|{a[1]}||{b[0]}|{b[1]}']={'agree':s/n if n else None,'n':n}
# JS divergence between base prefills (mean over tasks)
def js(p,q):
    cs=set(p)|set(q); m={c:(p.get(c,0)+q.get(c,0))/2 for c in cs}
    kl=lambda a:sum(a.get(c,0)*math.log2(a.get(c,0)/m[c]) for c in cs if a.get(c,0)>0)
    return (kl(p)+kl(q))/2
def norm(d): t=sum(d.values()); return {c:p/t for c,p in d.items()}
bk=[k for k in keys if k[0]=='qwen35b-base']
jsd={}
for a in bk:
    for b in bk:
        v=[js(norm(agg[a][t]),norm(agg[b][t])) for t in T if t in agg[a] and t in agg[b]]
        jsd[f'{a[1]}||{b[1]}']=st.mean(v)
# order consistency & position bias
orderc=collections.defaultdict(lambda:[0,0]); posA=collections.defaultdict(lambda:[0,0])
by=collections.defaultdict(dict)
for r in base:
    if r['dist_norm']: 
        d=cdist(r); by[('qwen35b-base',r['prefill'],r['task'])][r['order']]=top(d)
        posA[('qwen35b-base',r['prefill'])][0]+=r['dist_norm']['A'] or 0; posA[('qwen35b-base',r['prefill'])][1]+=1
for r in inst:
    if r.get('verdict'):
        by[(r['judge'],r['prefill'],r['task'])][r['order']]=r['label_to_cid'][r['verdict']]
        a=posA[(r['judge'],r['prefill'])]; a[0]+= r['verdict']=='A'; a[1]+=1
for (j,p,t),d in by.items():
    if 0 in d and 1 in d and d[0] and d[1]:
        orderc[(j,p)][1]+=1; orderc[(j,p)][0]+= d[0]==d[1]
# base CoT: criteria text
cot=[]; stats=collections.defaultdict(lambda:collections.Counter())
for r in base:
    if r['mode']!='sample': continue
    for s in r['samples']:
        tx=s['text']; stats[r['prefill']]['n']+=1
        stats[r['prefill']]['has_notes']+= bool(re.search(r'^A:',tx,re.M))
        stats[r['prefill']]['has_why']+= 'Why:' in tx
        stats[r['prefill']]['has_verdict']+= s['verdict'] is not None
        for m in re.finditer(r'^Why: (.*)$',tx,re.M): cot.append((r['prefill'],r['task'],m.group(1)))
stop=set('the a an of to and is in it that as its but for are with on be this one more than not or by at has have was from their which them they he she his her only just into so too very'.split())
words={}
for pf in ['kex-plain-cot','kex-middle-cot','kex-ornate-cot']:
    c=collections.Counter()
    for p,t,w in cot:
        if p==pf: c.update(x for x in re.findall(r"[a-z']+",w.lower()) if x not in stop and len(x)>2)
    words[pf]=c.most_common(25)

def olabel(o):
    if o.startswith('Qwen 3.5 35B-A3B Base (plain'): return 'Qwen base'
    if o.startswith('Qwen 3.5 35B-A3B Base (direct)'): return 'Qwen base'
    if 'draft -> Qwen' in o: return 'Opus 5.5 -> Qwen base refine'
    return o.split(' (')[0]
osh=collections.defaultdict(lambda: collections.defaultdict(lambda:[0.0,0]))
for key,tk in agg.items():
    for t,d in tk.items():
        tot=sum(d.values()); cs=T[t]['kind_of']
        for typ in (T[t]['type'],):
            share=collections.defaultdict(float)
            for c,p in d.items():
                os_=[olabel(o) for o in cs[c]['origins']]
                for o in os_: share[o]+=p/tot/len(os_)
            # include zero entries for present origins
            for c in cs.values():
                for o in c['origins']: share[olabel(o)]+=0
            for o,v in share.items():
                a=osh[(key[0],typ)][o]; a[0]+=v; a[1]+=1
origin_share={f'{k[0]}|{k[1]}':{o:v[0]/v[1] for o,v in d.items()} for k,d in osh.items()}
ofeat=collections.defaultdict(lambda:collections.defaultdict(list))
for t in tasks:
    for c in t['candidates']:
        for o in c['origins']:
            L=olabel(o); ofeat[t['type']][L].append((c['feats']['words'],c['ornate'],c['feats']['long_word_ratio'],c['feats']['punct_per100']))
origin_feats={typ:{o:{'n':len(v),'words':st.mean(x[0] for x in v),'ornate_rank':st.mean(x[1] for x in v),'long_word_ratio':st.mean(x[2] for x in v),'punct_per100':st.mean(x[3] for x in v)} for o,v in d.items()} for typ,d in ofeat.items()}
summ={'origin_share':origin_share,'origin_feats':origin_feats,'rows':rows,'agree':agree,'jsd':jsd,'order_consistency':{f'{k[0]}|{k[1]}':v[0]/v[1] for k,v in orderc.items() if v[1]},
 'pos_A':{f'{k[0]}|{k[1]}':v[0]/v[1] for k,v in posA.items() if v[1]},'cot_stats':{k:dict(v) for k,v in stats.items()},'why_words':words,'errors':dict(errs),
 'n_tasks':len(T)}
json.dump(summ,open(S+'data/summary.json','w'),indent=1)
json.dump([ {**{k:v for k,v in t.items() if k not in('kind_of',)}} for t in tasks],open(S+'data/tasks_feats.json','w'),ensure_ascii=False,indent=1)
print('rows',len(rows),'errors',dict(errs))
for r in rows:
    a=r['all']; print(f"{r['judge'][:10]:10} {r['prompt']:24} long {a['p_longest']:.2f}/{a['chance_longest']:.2f} orn {a['mean_ornate_rank_of_pick']:.2f} base {a['p_base_origin']:.2f}/{a['chance_base_origin']:.2f}", end='')
    if 'myth' in r: m=r['myth']; print(f"  | myth long {m['p_longest']:.2f}/{m['chance_longest']:.2f} orn {m['mean_ornate_rank_of_pick']:.2f} base {m['p_base_origin']:.2f}/{m['chance_base_origin']:.2f}",end='')
    print()
