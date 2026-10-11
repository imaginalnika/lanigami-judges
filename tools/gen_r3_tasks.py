# run with python (with tinker installed). Josh's exact myth prompts + 3 added world names in his exact template.
import os,sys,json,re,random; os.environ['TINKER_TELEMETRY']='0'; os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
sys.path.insert(0,'./tools')
from lib import *
import tinker as tk
from concurrent.futures import ThreadPoolExecutor
P=json.load(open('../ds4-research/compare/prompts.json')); PD={p['id']:p for p in P}
TEMPLATE='The world of {W} is one of strange tales and histories.\n\nIn the beginning,'
PROMPTS=[('jm-P07','P07',PD['P07']['prompt'],'Josh'),('jm-P09','P09',PD['P09']['prompt'],'Josh'),('jm-P10','P10',PD['P10']['prompt'],'Josh')]
for i,w in enumerate(['Marvethine','Oluskar','Tessimire']):
    PROMPTS.append((f'jm-X{i+1}',f'X{i+1}',TEMPLATE.format(W=w),'added by assistant'))
assert PD['P07']['prompt']==TEMPLATE.format(W='Furiotre') and PD['P09']['prompt']==TEMPLATE.format(W='Lanigami') and PD['P10']['prompt']==TEMPLATE.format(W='Deniasent')
for p in P:
    if p['id'] in('P07','P09','P10'): assert p['temperature']==1 and p['top_p']==0.95 and p['max_tokens']==300 and p['stop']==''
WRAP='Complete this creation myth.\n\n'
sc=tinker_client=tk.ServiceClient().create_sampling_client(base_model='Qwen/Qwen3.5-35B-A3B-Base'); tok=sc.get_tokenizer()
NB=6; BUDGET=300
CJK=re.compile(r'[\u3000-\u9fff\uac00-\ud7af]')
def junk(t):
    w=t.split()
    if CJK.search(t): return 'CJK/Hangul characters (language drift)'
    if len(w)<30: return 'fewer than 30 words'
    from collections import Counter
    g=Counter(tuple(w[i:i+6]) for i in range(len(w)-5))
    if g and max(g.values())>=3: return 'repetition loop (a 6-word sequence repeated 3+ times)'
    return None
def trim_sentence(t):
    m=list(re.finditer(r'[.!?…]["”’\')\]]*(?=\s|$)',t)); return t[:m[-1].end()].rstrip() if m else t.rstrip()
def base_one(args):
    tid,pid,prompt,k=args
    c=tinker(prompt,300,temperature=1.0,top_p=0.95,seed=7700+31*int(re.sub(r'\D','',pid))+k)
    return {'raw':c['text'],'finish':c['finish_reason']}
MODELS=['opus46','opus55','sol61','gpt4o']
def inst_one(args):
    tid,pid,prompt,m=args
    r=openrouter(m,[{'role':'user','content':WRAP+prompt}],1500 if m=='sol61' else 900,temperature=None if m=='sol61' else 1.0,reasoning={'effort':'low','exclude':True} if m=='sol61' else None)
    return {'raw':r['text'],'finish':r['finish']}
with ThreadPoolExecutor(6) as ex:
    bres={(a[0],a[3]):x for a,x in zip([(t,p,pr,k) for t,p,pr,_ in PROMPTS for k in range(NB)],ex.map(base_one,[(t,p,pr,k) for t,p,pr,_ in PROMPTS for k in range(NB)]))}
    ires={(a[0],a[3]):x for a,x in zip([(t,p,pr,m) for t,p,pr,_ in PROMPTS for m in MODELS],ex.map(inst_one,[(t,p,pr,m) for t,p,pr,_ in PROMPTS for m in MODELS]))}
tasks=[]; log=[]
for ti,(tid,pid,prompt,who) in enumerate(PROMPTS):
    kept=[];unused=[];dropped=[]
    for k in range(NB):
        r=bres[(tid,k)]; txt=r['raw'].lstrip()
        cut=trim_sentence(txt) if r['finish']=='length' else txt.rstrip()
        j=junk(cut)
        rec={'sample':k+1,'raw':r['raw'],'finish':r['finish'],'text':cut,'trimmed_to_sentence':r['finish']=='length' and cut!=txt.rstrip()}
        if j: rec['dropped_reason']=j; dropped.append(rec)
        elif len(kept)<2: kept.append(rec)
        else: unused.append(rec)
    cands=[]
    for rec in kept:
        cands.append({'text':rec['text'],'raw':rec['raw'],'origins':[f"Qwen 3.5 35B-A3B Base, sample {rec['sample']} (temp 1, top_p 0.95, max 300 tokens, no stop)"],'kinds':['base'],'finish':rec['finish'],'trimmed':rec['trimmed_to_sentence']})
    notes=[]
    for m in MODELS:
        r=ires[(tid,m)]; raw=r['raw']; t=raw.strip(); prefix_removed=None
        if t.startswith(prompt.strip()): t=t[len(prompt.strip()):].lstrip(); prefix_removed='full prompt'
        elif t.startswith('In the beginning,'): t=t[len('In the beginning,'):].lstrip(); prefix_removed='"In the beginning,"'
        ids=tok.encode(t); cutn=False
        if len(ids)>BUDGET: t=tok.decode(ids[:BUDGET]); t=trim_sentence(t); cutn=True
        cands.append({'text':t,'raw':raw,'origins':[f'{OR_LABEL[m]} (wrapper: "Complete this creation myth.")'],'kinds':['instruct'],'finish':r['finish'],'prefix_removed':prefix_removed,'cut_to_300_tokens':cutn,'tokens_before_cut':len(ids)})
    for i,c in enumerate(cands): c['cid']=f'{tid}-c{i}'
    idx=list(range(len(cands))); random.Random(31337+ti).shuffle(idx)
    tasks.append({'id':tid,'type':'myth','set':'Josh prompts' if who=='Josh' else 'Josh template, world added by assistant','prompt_id':pid,'source':prompt,'display_source':prompt,'context':'','candidates':cands,'orders':[idx,idx[::-1]],'base_samples_dropped':dropped,'base_samples_unused':unused})
json.dump({'wrapper':WRAP,'template':TEMPLATE,'tasks':tasks},open('./data/r3/tasks_josh_myths.json','w'),ensure_ascii=False,indent=1)
json.dump(tasks,open('./data/r3/tasks.json','w'),ensure_ascii=False)
for t in tasks:
    print(t['id'],[ (c['kinds'][0][:2],len(c['text'].split()),c.get('prefix_removed'),c.get('cut_to_300_tokens'),c.get('trimmed')) for c in t['candidates']],'dropped',[d['dropped_reason'] for d in t['base_samples_dropped']],'unused',len(t['base_samples_unused']))
print(spend())
