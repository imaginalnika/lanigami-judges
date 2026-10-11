import json,re,math,glob,collections,itertools,statistics as st,sys
sys.path.insert(0,'./tools')
from common import *
R=S+'data/r2/'
def jl(p): return [json.loads(l) for l in open(p)] if glob.glob(p) else []
tasks16=json.load(open(S+'data/tasks_feats.json'))
tasksOC=json.load(open(R+'tasks_origin_controlled.json'))
def feats(text):
    w=re.findall(r"[A-Za-z']+",text); n=max(len(w),1)
    return {'words':len(text.split()),'long_word_ratio':sum(len(x)>=9 for x in w)/n,'punct_per100':100*len(re.findall(r'[,;:—–-]',text))/n,'ly_per100':100*sum(x.lower().endswith('ly') for x in w)/n}
def add_feats(t):
    keys=['words','long_word_ratio','punct_per100','ly_per100']; n=len(t['candidates'])
    for c in t['candidates']: c['feats']=feats(c['text']); c['ornate']=0
    for k in keys:
        vals=[c['feats'][k] for c in t['candidates']]
        for c in t['candidates']:
            lt=sum(v<c['feats'][k] for v in vals); eq=sum(v==c['feats'][k] for v in vals); c['ornate']+=((lt+(eq-1)/2)/(n-1))/len(keys)
    L=max(c['feats']['words'] for c in t['candidates'])
    for c in t['candidates']: c['is_longest']=c['feats']['words']==L; c['is_base']='base' in c['kinds']
for t in tasksOC: add_feats(t)
T={t['id']:t for t in tasks16+tasksOC}
CM={t['id']:{c['cid']:c for c in t['candidates']} for t in T.values()}
base_main=jl(S+'data/base_results.jsonl')+jl(R+'base_r2_main.jsonl')
base_oc=jl(R+'base_origin_controlled_r1prefills.jsonl')+jl(R+'base_origin_controlled_r2prefills.jsonl')
inst_main=jl(S+'data/instruct_results.jsonl'); inst_oc=jl(R+'instruct_origin_controlled.jsonl')
scores=json.load(open(R+'scores.json')); priors_raw=jl(R+'calibration_priors.jsonl')
INST=['opus46','opus55','sol61','gpt4o']
R2_PREFILLS=['preface','prize-citation','reading-group','critic-persona','two-critics-senior','kex-neutral-cot']
# prior
pri=collections.defaultdict(list)
for r in priors_raw: pri[(r['prefill'],r['type'],r['n'])].append(r['dist'])
PRIOR={k:{l:max(st.mean(d[l] for d in v),1e-4) for l in v[0]} for k,v in pri.items()}
def top(d):
    if not d: return None
    m=max(d.values()); w=[c for c,p in d.items() if abs(p-m)<1e-9]; return w[0] if len(w)==1 else None
def cdist(rec,calibrated=False):
    d=rec['dist_norm']
    if not d: return None
    d={l:(p or 0) for l,p in d.items()}
    if calibrated:
        t=T[rec['task']]; pr=PRIOR.get((rec['prefill'],t['type'],len(rec['labels'])))
        if not pr: return None
        d={l:p/pr[l] for l,p in d.items()}
    s=sum(d.values())
    if s<=0: return None
    return {rec['label_to_cid'][l]:p/s for l,p in d.items()}
def avg(ds):
    ds=[d for d in ds if d]
    if not ds: return None
    out=collections.defaultdict(float)
    for d in ds:
        for c,p in d.items(): out[c]+=p/len(ds)
    return dict(out)
# ---- unit pick tables: units[set][unit][task]=dist over cids
def build_units(base,inst,prefill_ids=None):
    U=collections.defaultdict(dict); OC=collections.defaultdict(dict)  # OC: order-consistency (unit->task->(top0,top1))
    g=collections.defaultdict(lambda:collections.defaultdict(list))
    for r in base:
        g[('B:'+r['prefill'],r['task'])][r['order']].append(cdist(r))
        if r['mode']=='slot': g[('BC:'+r['prefill'],r['task'])][r['order']].append(cdist(r,True))
    for (u,t),od in g.items():
        U[u][t]=avg([x for o in od for x in od[o]])
        OC[u][t]=tuple(top(od[o][0]) if od.get(o) else None for o in (0,1))
    gi=collections.defaultdict(lambda:collections.defaultdict(list)); gp=collections.defaultdict(lambda:collections.defaultdict(list))
    for r in inst:
        if not r.get('verdict'): continue
        c=r['label_to_cid'][r['verdict']]
        gi[('J:'+r['judge'],r['task'])][r['order']].append(c)
        gp[('JP:'+r['judge']+'|'+r['prefill'],r['task'])][r['order']].append(c)
    for src,tag in ((gi,'J'),(gp,'JP')):
        for (u,t),od in src.items():
            votes=[c for o in od for c in od[o]]
            U[u][t]={c:votes.count(c)/len(votes) for c in set(votes)}
            OC[u][t]=tuple(od[o][0] if od.get(o) else None for o in (0,1))
    return U,OC
# scoring units
sc_by=collections.defaultdict(dict)
for r in scores: sc_by[(r['task'],r['cid'])][r['prefix_id']]=r
SCU=collections.defaultdict(dict); scoring_rows={}
for tid,t in T.items():
    rows=[]
    for c in t['candidates']:
        d=sc_by[(tid,c['cid'])]
        goods=[k for k in d if d[k]['group']=='good']; bads=[k for k in d if d[k]['group']=='bad']
        neu=d['neutral']['mean']; g=st.mean(d[k]['mean'] for k in goods); b=st.mean(d[k]['mean'] for k in bads)
        rows.append({'cid':c['cid'],'n_tokens':d['neutral']['n_tokens'],'neutral_mean':neu,'neutral_sum':d['neutral']['sum'],'per_prefix_mean':{k:d[k]['mean'] for k in d},'good_mean':g,'bad_mean':b,'pmi_good_minus_neutral':g-neu,'good_minus_bad':g-b,
                     'pmi_each_good':{k:d[k]['mean']-neu for k in goods},'neutral_minus_bad':neu-b})
    scoring_rows[tid]=rows
    for name,key in (('SC:raw-neutral','neutral_mean'),('SC:pmi-good-vs-neutral','pmi_good_minus_neutral'),('SC:good-minus-bad','good_minus_bad')):
        best=max(rows,key=lambda r:r[key]); SCU[name][tid]={best['cid']:1.0}
def agree(U,a,b,tasks):
    s=n=0
    for t in tasks:
        x=top(U[a].get(t)); y=top(U[b].get(t))
        if x and y: n+=1; s+=x==y
    return (s/n if n else None),n
def oc_rate(OC,u,tasks):
    s=n=0
    for t in tasks:
        a=OC[u].get(t)
        if a and a[0] and a[1]: n+=1; s+= a[0]==a[1]
    return (s/n if n else None),n
mean=lambda v:(st.mean(v) if v else None)
def metrics(U,u,tasks):
    pl=[];po=[];pb=[];ch=[]
    for t in tasks:
        d=U[u].get(t)
        if not d: continue
        tot=sum(d.values()); cs=CM[t]
        pl.append(sum(p for c,p in d.items() if cs[c]['is_longest'])/tot); po.append(sum(p*cs[c]['ornate'] for c,p in d.items())/tot)
        pb.append(sum(p for c,p in d.items() if cs[c]['is_base'])/tot); ch.append(sum(c['is_base'] for c in T[t]['candidates'])/len(cs))
    return {'p_longest':mean(pl),'ornate_rank_pick':mean(po),'p_base_origin':mean(pb),'chance_base':mean(ch),'n':len(pl)}
OUT={}
ids16=[t['id'] for t in tasks16]; myth16=[t for t in ids16 if t.startswith('myth')]; idsB=[t['id'] for t in tasksOC if t['id'].startswith('mythB')]; idsI=[t['id'] for t in tasksOC if t['id'].startswith('mythI')]
U16,OC16=build_units(base_main,inst_main); UOC,OCOC=build_units(base_oc,inst_oc)
# ================= Section 2: round-2 prefills on 16 tasks
sec2=[]
allp=[p for p in sorted({r['prefill'] for r in base_main})]
for p in allp:
    u='B:'+p; row={'prefill':p,'round':2 if p in R2_PREFILLS else 1}
    row['all']=metrics(U16,u,ids16); row['myth']=metrics(U16,u,myth16)
    row['order_consistency']=oc_rate(OC16,u,ids16)[0]
    ms=[r['label_mass'] for r in base_main if r['prefill']==p and r['label_mass'] is not None]; row['label_mass']=mean(ms)
    row['agree_instruct']={j:agree(U16,u,'J:'+j,ids16)[0] for j in INST}
    row['agree_instruct_mean']=mean([v for v in row['agree_instruct'].values() if v is not None])
    sec2.append(row)
OUT['sec2']=sec2
# kex steering table
OUT['kex_variants']={p:{'ornate_rank_pick':metrics(U16,'B:'+p,ids16)['ornate_rank_pick'],'p_longest':metrics(U16,'B:'+p,ids16)['p_longest'],'myth_instruct_share':1-metrics(U16,'B:'+p,myth16)['p_base_origin']} for p in ['kex-plain-cot','kex-middle-cot','kex-ornate-cot','kex-neutral-cot','kex-middle-label']}
# ================= Section 3: calibration
slot_ps=sorted({r['prefill'] for r in base_main+base_oc if r['mode']=='slot'})
cal=[]
for p in slot_ps:
    row={'prefill':p}
    for setname,U,OC,tasks,base in (('main16',U16,OC16,ids16,base_main),('originB',UOC,OCOC,idsB,base_oc),('originI',UOC,OCOC,idsI,base_oc)):
        tk=set(tasks)
        recs=[r for r in base if r['prefill']==p and r['task'] in tk and r['dist_norm']]
        if not recs: continue
        A=lambda cal_:mean([ (cdist(r,cal_) or {}).get(r['label_to_cid']['A'],0) for r in recs])
        ao=lambda u:[agree(U,u,('J:'+j),tasks)[0] for j in INST]
        d={'posA_raw':A(False),'posA_cal':A(True),'oc_raw_single_order':None,
           'oc_raw':oc_rate(OC,'B:'+p,tasks)[0],'oc_cal':oc_rate(OC,'BC:'+p,tasks)[0],
           'agree_inst_raw':mean([x for x in ao('B:'+p) if x is not None]),'agree_inst_cal':mean([x for x in ao('BC:'+p) if x is not None]),
           'label_mass':mean([r['label_mass'] for r in recs])}
        row[setname]=d
    cal.append(row)
OUT['calibration']=cal
# single-order order consistency (not order averaged): top pick per single order raw vs calibrated
def single_oc(base,p,tasks,cal_):
    by=collections.defaultdict(dict)
    for r in base:
        if r['prefill']==p and r['task'] in tasks and r['dist_norm']: by[r['task']][r['order']]=top(cdist(r,cal_))
    v=[a[0]==a[1] for a in by.values() if 0 in a and 1 in a and a[0] and a[1]]
    return mean([float(x) for x in v]),len(v)
for row in cal:
    for setname,tasks,base in (('main16',ids16,base_main),('originB',idsB,base_oc),('originI',idsI,base_oc)):
        if setname in row:
            row[setname]['oc_single_raw']=single_oc(base,row['prefill'],set(tasks),False)[0]; row[setname]['oc_single_cal']=single_oc(base,row['prefill'],set(tasks),True)[0]
OUT['priors']={f'{k[0]}|{k[1]}|{k[2]}':v for k,v in PRIOR.items()}
# ================= Section 4: origin-controlled agreement
def group_stats(U,OC,tasks):
    bunits=sorted(u for u in U if u.startswith('B:') ); bc=sorted(u for u in U if u.startswith('BC:'))
    ju=['J:'+j for j in INST]; sc=sorted(u for u in U if u.startswith('SC:'))
    res={}
    def pairs(A,B,same=False):
        vals=[]
        for a in A:
            for b in B:
                if same and a>=b: continue
                x,n=agree(U,a,b,tasks)
                if x is not None: vals.append(x)
        return mean(vals)
    res['instruct_vs_instruct']=pairs(ju,ju,True)
    res['base_prefill_vs_instruct']=pairs(bunits,ju)
    res['base_calibrated_vs_instruct']=pairs(bc,ju)
    res['base_vs_base']=pairs(bunits,bunits,True)
    res['scoring_vs_instruct']=pairs(sc,ju)
    res['scoring_vs_base']=pairs(sc,bunits)
    res['per_base_prefill']={u[2:]:mean([agree(U,u,j,tasks)[0] for j in ju if agree(U,u,j,tasks)[0] is not None]) for u in bunits}
    res['per_calibrated_prefill']={u[3:]:mean([agree(U,u,j,tasks)[0] for j in ju if agree(U,u,j,tasks)[0] is not None]) for u in bc}
    res['per_scoring']={u:mean([agree(U,u,j,tasks)[0] for j in ju if agree(U,u,j,tasks)[0] is not None]) for u in sc}
    res['instruct_pair_matrix']={f'{a[2:]}|{b[2:]}':agree(U,a,b,tasks)[0] for a in ju for b in ju if a<b}
    # unanimity
    un=0;nn=0
    for t in tasks:
        ps=[top(U[j].get(t)) for j in ju]
        if all(ps): nn+=1; un+= len(set(ps))==1
    res['instruct_unanimous']=(un/nn if nn else None,nn)
    res['order_consistency']={'instruct_judge_prompt':mean([oc_rate(OC,u,tasks)[0] for u in U if u.startswith('JP:') and oc_rate(OC,u,tasks)[0] is not None]),
        'base_prefills':mean([oc_rate(OC,u,tasks)[0] for u in bunits if oc_rate(OC,u,tasks)[0] is not None]),
        'base_calibrated':mean([oc_rate(OC,u,tasks)[0] for u in bc if oc_rate(OC,u,tasks)[0] is not None])}
    res['metrics']={u:metrics(U,u,tasks) for u in ju}
    return res
# mix U16 (restricted to myth16) as reference
sec4={'mixed_myths_16':group_stats(U16|{},OC16,myth16),'all_Qwen_base':group_stats(UOC,OCOC,idsB),'all_Opus55':group_stats(UOC,OCOC,idsI)}
# scoring units for main16 need merge: SCU added to both
for k in list(sec4): pass
U16.update(SCU); UOC.update(SCU)
sec4={'mixed_myths_16':group_stats(U16,OC16,myth16),'all_Qwen_base':group_stats(UOC,OCOC,idsB),'all_Opus55':group_stats(UOC,OCOC,idsI)}
# top picks per task per unit for display & temp analysis (set B)
temps=lambda c: float(re.search(r'temp ([0-9.]+)',c['origins'][0]).group(1))
tb={}
for who in ('instruct','base','scoring'):
    units={'instruct':[u for u in UOC if u.startswith('J:')],'base':[u for u in UOC if u.startswith('B:')],'scoring':[u for u in UOC if u.startswith('SC:')]}[who]
    share=collections.defaultdict(list)
    for u in units:
        for t in idsB:
            d=UOC[u].get(t)
            if not d: continue
            tot=sum(d.values())
            for c,p in d.items(): share[temps(CM[t][c])].append(p/tot*1.0)
    # mean mass per temp: sum over tasks / tasks
    mass=collections.defaultdict(float); cnt=0
    for u in units:
        for t in idsB:
            d=UOC[u].get(t)
            if not d: continue
            cnt+=1; tot=sum(d.values())
            for c,p in d.items(): mass[temps(CM[t][c])]+=p/tot
    tb[who]={str(k):v/cnt for k,v in sorted(mass.items())}
sec4['setB_mass_by_temperature']=tb
sec4['metrics_units']={ s:{u:metrics(UOC,u,ids) for u in ['J:'+j for j in INST]+['SC:raw-neutral','SC:pmi-good-vs-neutral','SC:good-minus-bad']} for s,ids in (('all_Qwen_base',idsB),('all_Opus55',idsI))}
sec4['base_prefill_metrics']={}
for sk,ids in (('all_Qwen_base',idsB),('all_Opus55',idsI),('mixed_myths_16',myth16)):
    U_=UOC if sk!='mixed_myths_16' else U16
    ms=[metrics(U_,u,ids) for u in U_ if u.startswith('B:')]
    sec4['base_prefill_metrics'][sk]={'p_longest':mean([m['p_longest'] for m in ms if m['p_longest'] is not None]),'ornate_rank_pick':mean([m['ornate_rank_pick'] for m in ms if m['ornate_rank_pick'] is not None]),'by_prefill':{u[2:]:metrics(U_,u,ids) for u in U_ if u.startswith('B:')}}
OUT['sec4']=sec4
# ================= Section 1: scoring aggregates
sec1={'rows':scoring_rows,'prefix_texts':{}}
allt=list(T)
agg={}
for name in ['SC:raw-neutral','SC:pmi-good-vs-neutral','SC:good-minus-bad']:
    d={'agree_instruct':{j:{'main16':agree(U16,name,'J:'+j,ids16)[0],'originB':agree(UOC,name,'J:'+j,idsB)[0],'originI':agree(UOC,name,'J:'+j,idsI)[0]} for j in INST},
       'agree_base_prefills_mean':{ 'main16':mean([agree(U16,name,'B:'+p,ids16)[0] for p in allp if agree(U16,name,'B:'+p,ids16)[0] is not None])}}
    d['metrics']={'main16':metrics(U16,name,ids16),'myth16':metrics(U16,name,myth16),'originB':metrics(UOC,name,idsB),'originI':metrics(UOC,name,idsI)}
    agg[name]=d
sec1['agg']=agg
# correlation of neutral mean with length, by type
def spearman(x,y):
    rk=lambda v:[sorted(v).index(a)+(v.count(a)-1)/2 for a in v]
    rx,ry=rk(x),rk(y); mx,my=st.mean(rx),st.mean(ry)
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry)); den=math.sqrt(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))
    return num/den if den else 0
cor=collections.defaultdict(list)
for tid,rows in scoring_rows.items():
    t=T[tid]; w=[CM[tid][r['cid']]['feats']['words'] for r in rows]
    for k in ('neutral_mean','pmi_good_minus_neutral','good_minus_bad'):
        cor[(t['type']+('-originB' if tid.startswith('mythB') else '-originI' if tid.startswith('mythI') else ''),k)].append(spearman([r[k] for r in rows],w))
sec1['spearman_with_words']={f'{a}|{b}':mean(v) for (a,b),v in cor.items()}
# origin means of contrasts (myth16 + translation16)
om=collections.defaultdict(lambda:collections.defaultdict(list))
def olab(o):
    if o.startswith('Qwen 3.5 35B-A3B Base'):
        return 'Opus 5.5 -> Qwen refine' if 'draft' in o else 'Qwen base'
    return o.split(' (')[0].split(',')[0]
for tid,rows in scoring_rows.items():
    for r in rows:
        for o in CM[tid][r['cid']]['origins']:
            om[(T[tid]['type'],'OC' if tid in idsB+idsI else 'main')][olab(o)].append((r['neutral_mean'],r['pmi_good_minus_neutral'],r['good_minus_bad']))
sec1['origin_means']={f'{k[0]}|{k[1]}':{o:{'n':len(v),'neutral_mean':mean([x[0] for x in v]),'pmi_good_minus_neutral':mean([x[1] for x in v]),'good_minus_bad':mean([x[2] for x in v])} for o,v in d.items()} for k,d in om.items()}
# per-prefix good-neutral overall by group
pp=collections.defaultdict(list)
for tid,rows in scoring_rows.items():
    for r in rows:
        for k,v in r['pmi_each_good'].items(): pp[('good',k)].append(v)
        for k in r['per_prefix_mean']:
            if k.startswith('bad'): pp[('bad',k)].append(r['per_prefix_mean'][k]-r['neutral_mean'])
sec1['per_prefix_mean_shift_vs_neutral']={f'{k[1]}':{'mean':mean(v),'sd':st.pstdev(v)} for k,v in pp.items()}
for p in glob.glob(S+'prompts/score/*.txt'):
    m=load_template(p); sec1['prefix_texts'][m['id']]=open(p).read()
OUT['sec1']=sec1
# ================= Section 5: fold
fold=jl(R+'fold.jsonl')
def grams(s,n): 
    w=re.findall(r"[a-z']+",s.lower()); return {tuple(w[i:i+n]) for i in range(max(len(w)-n+1,0))}
def sim(a,b,typ):
    n=1 if typ=='translation' else 3
    ga,gb=grams(a,n),grams(b,n)
    return len(ga&gb)/len(ga|gb) if ga|gb else 0
near=collections.defaultdict(collections.Counter); nfold=collections.Counter(); lens=collections.defaultdict(list); candlen=[]
for r in fold:
    t=T[r['task']]; cs={l:CM[r['task']][c] for l,c in r['label_to_cid'].items()}
    key=r['fold']+'|'+r['who']
    for o in r['outputs']:
        best=max(cs.values(),key=lambda c:sim(o['text'],c['text'],t['type']))
        sims={c['cid']:sim(o['text'],c['text'],t['type']) for c in cs.values()}
        o['nearest_cid']=best['cid']; o['nearest_sim']=sims[best['cid']]; o['sims']=sims
        for og in best['origins']: near[(t['type'],key)][olab(og)]+=1/len(best['origins'])
        nfold[(t['type'],key)]+=1; lens[(t['type'],key)].append(len(o['text'].split()))
    # also candidate mean len
meanlen=lambda t,typ: mean([c['feats']['words'] for c in t['candidates']])
cl=collections.defaultdict(list)
for t in T.values(): cl[t['type']].append(mean([c['feats']['words'] for c in t['candidates']]))
sec5={'nearest_origin':{f'{k[0]}|{k[1]}':{o:v/nfold[k] for o,v in c.items()} for k,c in near.items()},'mean_words':{f'{k[0]}|{k[1]}':mean(v) for k,v in lens.items()},'mean_candidate_words':{k:mean(v) for k,v in cl.items()}}
OUT['sec5']=sec5
json.dump(OUT,open(R+'summary_r2.json','w'),indent=1,default=str)
# write per-task fold with sims back
json.dump(fold,open(R+'fold_annotated.json','w'),ensure_ascii=False)
json.dump(tasksOC,open(R+'tasks_oc_feats.json','w'),ensure_ascii=False)
print('ok')
