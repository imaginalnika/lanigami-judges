import sys,json,os,re; sys.path.insert(0,'./tools')
from lib import *; from common import *
from concurrent.futures import ThreadPoolExecutor
tasks=json.load(open(S+'data/tasks.json'))+json.load(open(S+'data/r2/tasks_origin_controlled.json'))
fp=[load_template(S+f'prompts/fold/{n}.txt') for n in ('fold-editor-final','fold-revision-session','instruct-fold')]
OUT=S+'data/r2/fold.jsonl'
done=set()
if os.path.exists(OUT):
    for l in open(OUT): r=json.loads(l); done.add((r['task'],r['fold'],r['who']))
def clean(t):
    t=t.split('\n\n')[0] if False else t
    return t.strip()
def job(a):
    t,p,who=a
    if (t['id'],p['id'],who) in done: return
    prompt,cids=render(p,t,t['orders'][0])
    outs=[]
    if who=='qwen-base':
        mt=int(p['max_tokens_translation'] if t['type']=='translation' else p['max_tokens_myth'])
        for k in range(4):
            c=tinker(prompt,mt,temperature=0.7,top_p=0.95,seed=900000+k*13+len(t['id']))
            x=c['text']
            if t['type']=='translation': x=x.split('\n\n')[0].split('\nKorean')[0]
            else: x=x.split('\n\n\n')[0]
            outs.append({'text':x.strip(),'finish':c['finish_reason']})
    else:
        r=openrouter(who,[{'role':'user','content':prompt}],2000 if who=='sol61' else 700,temperature=None if who=='sol61' else 1.0,reasoning={'effort':'low','exclude':True} if who=='sol61' else None)
        outs.append({'text':r['text'].strip(),'finish':r['finish']})
    rec={'task':t['id'],'fold':p['id'],'who':who,'prompt':prompt,'label_to_cid':dict(zip('ABCDE',cids)),'outputs':outs}
    with open(OUT,'a') as f: f.write(json.dumps(rec,ensure_ascii=False)+'\n')
jobs=[]
for t in tasks:
    for p in fp[:2]: jobs.append((t,p,'qwen-base'))
    for w in ('opus55','sol61'): jobs.append((t,fp[2],w))
with ThreadPoolExecutor(6) as ex: list(ex.map(job,jobs))
print('done',spend())
