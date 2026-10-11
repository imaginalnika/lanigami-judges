import json,glob,os,collections,sys
sys.path.insert(0,'./tools')
from common import *
tasks=json.load(open(S+'data/tasks_feats.json'))
base=[json.loads(l) for l in open(S+'data/base_results.jsonl')]
inst=[json.loads(l) for l in open(S+'data/instruct_results.jsonl')]
os.makedirs(S+'site-data/task',exist_ok=True)
for t in tasks:
    cid_idx={c['cid']:i+1 for i,c in enumerate(t['candidates'])}
    b=[r for r in base if r['task']==t['id']]; i=[r for r in inst if r['task']==t['id']]
    for r in b+i: r['label_to_short']={l:cid_idx[c] for l,c in r['label_to_cid'].items()}
    json.dump({'task':t,'base':b,'instruct':i},open(S+f'site-data/task/{t["id"]}.json','w'),ensure_ascii=False)
def files(d):
    out=[]
    for p in sorted(glob.glob(S+f'prompts/{d}/*.txt')):
        m=load_template(p); out.append({'id':m['id'],'title':m['title'],'mode':m.get('mode','plain'),'notes':m.get('notes',''),'raw':open(p).read()})
    return out
idx={'tasks':[{'id':t['id'],'type':t['type'],'title':(t['source'][:60]),'n':len(t['candidates'])} for t in tasks],
     'base_prefills':files('base'),'instruct_prefills':files('instruct'),'summary':json.load(open(S+'data/summary.json')),
     'spend':json.load(open(S+'data/spend.json')) if os.path.exists(S+'data/spend.json') else None,
     'myth_gen_prompt':json.load(open(S+'data/myth_tasks_raw.json'))['gen_prompt']}
json.dump(idx,open(S+'site-data/index.json','w'),ensure_ascii=False)
print('ok',len(tasks))
