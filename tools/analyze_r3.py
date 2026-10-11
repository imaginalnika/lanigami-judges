import json,re,math,glob,collections,statistics as st,sys
sys.path.insert(0,'./tools')
from common import *
R=S+'data/r3/'
def jl(p): return [json.loads(l) for l in open(p)] if glob.glob(p) else []
tasks=json.load(open(R+'tasks.json')); ids=[t['id'] for t in tasks]
def feats(text):
    w=re.findall(r"[A-Za-z']+",text); n=max(len(w),1)
    return {'words':len(text.split()),'long_word_ratio':sum(len(x)>=9 for x in w)/n,'punct_per100':100*len(re.findall(r'[,;:—–-]',text))/n,'ly_per100':100*sum(x.lower().endswith('ly') for x in w)/n}
for t in tasks:
    keys=['words','long_word_ratio','punct_per100','ly_per100']; n=len(t['candidates'])
    for c in t['candidates']: c['feats']=feats(c['text']); c['ornate']=0
    for k in keys:
        vals=[c['feats'][k] for c in t['candidates']]
        for c in t['candidates']:
            lt=sum(v<c['feats'][k] for v in vals); eq=sum(v==c['feats'][k] for v in vals); c['ornate']+=((lt+(eq-1)/2)/(n-1))/len(keys)
    L=max(c['feats']['words'] for c in t['candidates'])
    for c in t['candidates']: c['is_longest']=c['feats']['words']==L; c['is_base']='base' in c['kinds']
    for c in t['candidates']:
        o=c['origins'][0]; c['src']='qwen' if c['is_base'] else {'Opus 4.6':'opus46','Opus 5.5':'opus55','GPT-6.1':'sol61','GPT-4o':'gpt4o'}[next(k for k in ['Opus 4.6','Opus 5.5','GPT-6.1','GPT-4o'] if o.startswith(k))]
T={t['id']:t for t in tasks}; CM={t['id']:{c['cid']:c for c in t['candidates']} for t in tasks}
base=jl(R+'base_results.jsonl'); inst=jl(R+'instruct_results.jsonl'); scores=json.load(open(R+'scores.json')) if glob.glob(R+'scores.json') else []; priors_raw=jl(R+'calibration_priors.jsonl')
INST=['opus46','opus55','sol61','gpt4o']; SRCS=['qwen']+INST
R2P=['preface','prize-citation','reading-group','critic-persona','two-critics-senior','kex-neutral-cot']
pri=collections.defaultdict(list)
for r in priors_raw: pri[r['prefill']].append(r['dist'])
PRIOR={k:{l:max(st.mean(d[l] for d in v),1e-4) for l in v[0]} for k,v in pri.items()}
def top(d):
    if not d: return None
    m=max(d.values()); w=[c for c,p in d.items() if abs(p-m)<1e-9]; return w[0] if len(w)==1 else None
def cdist(rec,cal=False):
    d=rec['dist_norm']
    if not d: return None
    d={l:(p or 0) for l,p in d.items()}
    if cal:
        pr=PRIOR.get(rec['prefill'])
        if not pr: return None
        d={l:p/pr[l] for l,p in d.items()}
    s=sum(d.values())
    return {rec['label_to_cid'][l]:p/s for l,p in d.items()} if s>0 else None
def avg(ds):
    ds=[d for d in ds if d]
    if not ds: return None
    o=collections.defaultdict(float)
    for d in ds:
        for c,p in d.items(): o[c]+=p/len(ds)
    return dict(o)
U=collections.defaultdict(dict); OC=collections.defaultdict(dict)
g=collections.defaultdict(lambda:collections.defaultdict(list))
for r in base:
    g[('B:'+r['prefill'],r['task'])][r['order']].append(cdist(r))
    if r['mode']=='slot': g[('BC:'+r['prefill'],r['task'])][r['order']].append(cdist(r,True))
for (u,t),od in g.items():
    U[u][t]=avg([x for o in od for x in od[o]]); OC[u][t]=tuple(top(od[o][0]) if od.get(o) else None for o in (0,1))
gi=collections.defaultdict(lambda:collections.defaultdict(list)); gp=collections.defaultdict(lambda:collections.defaultdict(list))
for r in inst:
    if not r.get('verdict'): continue
    c=r['label_to_cid'][r['verdict']]; gi[('J:'+r['judge'],r['task'])][r['order']].append(c); gp[('JP:'+r['judge']+'|'+r['prefill'],r['task'])][r['order']].append(c)
for src in (gi,gp):
    for (u,t),od in src.items():
        v=[c for o in od for c in od[o]]; U[u][t]={c:v.count(c)/len(v) for c in set(v)}; OC[u][t]=tuple(od[o][0] if od.get(o) else None for o in (0,1))
# scoring
sc_by=collections.defaultdict(dict)
for r in scores: sc_by[(r['task'],r['cid'])][r['prefix_id']]=r
scoring_rows={}
for tid,t in T.items():
    rows=[]
    if not scores: break
    for c in t['candidates']:
        d=sc_by[(tid,c['cid'])]; goods=[k for k in d if d[k]['group']=='good']; bads=[k for k in d if d[k]['group']=='bad']
        neu=d['neutral']['mean']; gd=st.mean(d[k]['mean'] for k in goods); bd=st.mean(d[k]['mean'] for k in bads)
        rows.append({'cid':c['cid'],'n_tokens':d['neutral']['n_tokens'],'neutral_mean':neu,'per_prefix_mean':{k:d[k]['mean'] for k in d},'good_mean':gd,'bad_mean':bd,'pmi_good_minus_neutral':gd-neu,'good_minus_bad':gd-bd,'pmi_each_good':{k:d[k]['mean']-neu for k in goods},'neutral_minus_bad':neu-bd})
    scoring_rows[tid]=rows
    for name,key in (('SC:raw-neutral','neutral_mean'),('SC:pmi-good-vs-neutral','pmi_good_minus_neutral'),('SC:good-minus-bad','good_minus_bad')):
        b=max(rows,key=lambda r:r[key]); U[name][tid]={b['cid']:1.0}
def agree(a,b):
    s=n=0
    for t in ids:
        x=top(U[a].get(t)); y=top(U[b].get(t))
        if x and y: n+=1; s+=x==y
    return (s/n if n else None),n
def oc_rate(u):
    s=n=0
    for t in ids:
        a=OC[u].get(t)
        if a and a[0] and a[1]: n+=1; s+=a[0]==a[1]
    return (s/n if n else None),n
mean=lambda v:(st.mean(v) if v else None)
def metrics(u):
    pl=[];po=[];sh=collections.defaultdict(list)
    for t in ids:
        d=U[u].get(t)
        if not d: continue
        tot=sum(d.values()); cs=CM[t]
        pl.append(sum(p for c,p in d.items() if cs[c]['is_longest'])/tot); po.append(sum(p*cs[c]['ornate'] for c,p in d.items())/tot)
        for s in SRCS: sh[s].append(sum(p for c,p in d.items() if cs[c]['src']==s)/tot)
    return {'p_longest':mean(pl),'ornate_rank_pick':mean(po),'share':{s:mean(sh[s]) for s in SRCS},'n':len(pl)}
OUT={}
ju=['J:'+j for j in INST]
bu=sorted(u for u in U if u.startswith('B:')); bc=sorted(u for u in U if u.startswith('BC:')); sc=sorted(u for u in U if u.startswith('SC:'))
OUT['chance']={'longest':mean([sum(c['is_longest'] for c in t['candidates'])/len(t['candidates']) for t in tasks]),'qwen':2/6,'each_instruct':1/6,'ornate_rank':0.5}
OUT['instruct_metrics']={u[2:]:metrics(u) for u in ju}
OUT['instruct_prompt_metrics']={u[3:]:metrics(u) for u in U if u.startswith('JP:')}
OUT['instruct_prompt_oc']={u[3:]:oc_rate(u)[0] for u in U if u.startswith('JP:')}
OUT['instruct_oc_mean']=mean([v for v in OUT['instruct_prompt_oc'].values() if v is not None])
OUT['instruct_picks']={u[2:]:{t:top(U[u].get(t)) for t in ids} for u in ju}
OUT['instruct_unparsed']=sum(1 for r in inst if not r.get('verdict')); OUT['instruct_calls']=len(inst)
def bsrow(p):
    u='B:'+p; r={'prefill':p,'round':2 if p in R2P else 1,'metrics':metrics(u),'oc':oc_rate(u)[0],'label_mass':mean([x['label_mass'] for x in base if x['prefill']==p and x['label_mass'] is not None]),
      'agree_instruct':{j:agree(u,'J:'+j)[0] for j in INST},'picks':{t:top(U[u].get(t)) for t in ids},'dist':{t:U[u].get(t) for t in ids}}
    r['agree_instruct_mean']=mean([v for v in r['agree_instruct'].values() if v is not None]); return r
OUT['base']=[bsrow(u[2:]) for u in bu]
cal=[]
for u in bc:
    p=u[3:]; recs=[r for r in base if r['prefill']==p and r['dist_norm']]
    A=lambda c_:mean([(cdist(r,c_) or {}).get(r['label_to_cid']['A'],0) for r in recs])
    def single(c_):
        by=collections.defaultdict(dict)
        for r in recs: by[r['task']][r['order']]=top(cdist(r,c_))
        v=[float(a[0]==a[1]) for a in by.values() if 0 in a and 1 in a and a[0] and a[1]]; return mean(v)
    cal.append({'prefill':p,'posA_raw':A(False),'posA_cal':A(True),'oc_single_raw':single(False),'oc_single_cal':single(True),'oc_raw':oc_rate('B:'+p)[0],'oc_cal':oc_rate(u)[0],
      'agree_inst_raw':mean([agree('B:'+p,j)[0] for j in ju if agree('B:'+p,j)[0] is not None]),'agree_inst_cal':mean([agree(u,j)[0] for j in ju if agree(u,j)[0] is not None]),
      'metrics_cal':metrics(u),'prior':PRIOR.get(p)})
OUT['calibration']=cal
def pairs(A,B,same=False):
    v=[]
    for a in A:
        for b in B:
            if same and a>=b: continue
            x,_=agree(a,b)
            if x is not None: v.append(x)
    return mean(v)
OUT['agreement']={'instruct_vs_instruct':pairs(ju,ju,True),'base_prefill_vs_instruct':pairs(bu,ju),'base_calibrated_vs_instruct':pairs(bc,ju),'base_vs_base':pairs(bu,bu,True),'scoring_vs_instruct':pairs(sc,ju),'scoring_vs_base':pairs(sc,bu),
  'instruct_pair_matrix':{f'{a[2:]}|{b[2:]}':agree(a,b)[0] for a in ju for b in ju if a<b},'per_scoring':{u:mean([agree(u,j)[0] for j in ju if agree(u,j)[0] is not None]) for u in sc},
  'per_base_prefill':{u[2:]:mean([agree(u,j)[0] for j in ju if agree(u,j)[0] is not None]) for u in bu},'per_calibrated_prefill':{u[3:]:mean([agree(u,j)[0] for j in ju if agree(u,j)[0] is not None]) for u in bc}}
un=nn=0
for t in ids:
    ps=[top(U[j].get(t)) for j in ju]
    if all(ps): nn+=1; un+=len(set(ps))==1
OUT['agreement']['instruct_unanimous']=(un,nn)
# base prefill group shares
OUT['base_group']={'qwen_share_mean':mean([r['metrics']['share']['qwen'] for r in OUT['base']]),'p_longest_mean':mean([r['metrics']['p_longest'] for r in OUT['base']]),'ornate_mean':mean([r['metrics']['ornate_rank_pick'] for r in OUT['base']]),
  'share_mean':{s:mean([r['metrics']['share'][s] for r in OUT['base']]) for s in SRCS},'oc_mean':mean([r['oc'] for r in OUT['base'] if r['oc'] is not None])}
OUT['instruct_group']={'share_mean':{s:mean([OUT['instruct_metrics'][j]['share'][s] for j in INST]) for s in SRCS}}
# self-preference: per judge share of own candidate
OUT['self_pref']={j:OUT['instruct_metrics'][j]['share'][j] for j in INST}
# scoring
OUT['scoring']={'rows':scoring_rows,'winners':{name:{t:top(U[name].get(t)) for t in ids} for name in sc}}
def sc_metrics(name): return metrics(name)
OUT['scoring_metrics']={n:metrics(n) for n in sc}
if scores:
    sh=collections.defaultdict(lambda:collections.defaultdict(list)); 
    for tid,rows in scoring_rows.items():
        for r in rows:
            s=CM[tid][r['cid']]['src']
            for k in ('neutral_mean','pmi_good_minus_neutral','good_minus_bad'): sh[s][k].append(r[k])
    OUT['scoring_by_src']={s:{k:mean(v) for k,v in d.items()} for s,d in sh.items()}
# per task view data
pt={}
for t in tasks:
    tid=t['id']; e={'instruct':{},'base':{},'cal':{},'sc':{}}
    for j in INST:
        e['instruct'][j]={'picks':[(r['order'],r['prefill'],r['verdict'] and r['label_to_cid'][r['verdict']]) for r in inst if r['task']==tid and r['judge']==j]}
    e['base']={r['prefill']:{c:round(p,3) for c,p in (U['B:'+r['prefill']].get(tid) or {}).items()} for r in OUT['base']}
    pt[tid]=e
OUT['per_task']=pt
OUT['tasks_meta']=[{'id':t['id'],'set':t['set'],'prompt_id':t['prompt_id'],'cands':[{'cid':c['cid'],'src':c['src'],'words':c['feats']['words'],'ornate':round(c['ornate'],3),'longest':c['is_longest']} for c in t['candidates']]} for t in tasks]
json.dump(OUT,open(R+'summary_r3.json','w'),ensure_ascii=False,indent=1)
print('ok')
