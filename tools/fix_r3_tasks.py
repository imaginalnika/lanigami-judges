# post-process instruct candidates: continuation = text after the first echo of the prompt's last line "In the beginning," (drops model-added title + echoed opener); then same 300-token budget + sentence trim as base. Raw kept.
import os,sys,json,re; os.environ['TINKER_TELEMETRY']='0'
sys.path.insert(0,'./tools')
from lib import *
import tinker as tk
sys.argv=['x']
exec(open('tools/gen_r3_tasks.py').read().split("sc=tinker_client")[0].split("from concurrent")[0].split("import tinker as tk")[0]) if False else None
def trim_sentence(t):
    m=list(re.finditer(r'[.!?…]["”’\')\]]*(?=\s|$)',t)); return t[:m[-1].end()].rstrip() if m else t.rstrip()
tok=tk.ServiceClient().create_sampling_client(base_model='Qwen/Qwen3.5-35B-A3B-Base').get_tokenizer()
D=json.load(open('data/r3/tasks_josh_myths.json')); WRAP=D['wrapper']; tasks=D['tasks']
M=['opus46','opus55','sol61','gpt4o']
for t in tasks:
    for j,m in enumerate(M):
        c=t['candidates'][2+j]
        if not c['raw'].strip() and m=='opus55':
            r=openrouter(m,[{'role':'user','content':WRAP+t['source']}],2500,temperature=1.0)
            c['raw']=r['text']; c['finish']=r['finish']; c['regenerated_note']='first call (max_tokens 900) returned empty text (finish=length, hidden reasoning used the budget); regenerated once with max_tokens 2500, same prompt/temperature'
        raw=c['raw']; key='In the beginning,'; i=raw.find(key)
        if 0<=i<600 and raw[:i].strip(): 
            c['pre_removed']=raw[:i+len(key)]; txt=raw[i+len(key):]
        elif raw.strip().startswith(key): c['pre_removed']=key; txt=raw.strip()[len(key):]
        else: c['pre_removed']=None; txt=raw
        t2=txt.strip(); ids=tok.encode(t2); cutn=False
        if len(ids)>300: t2=trim_sentence(tok.decode(ids[:300])); cutn=True
        c['text']=t2; c['cut_to_300_tokens']=cutn; c['tokens_before_cut']=len(ids); c.pop('prefix_removed',None)
D['tasks']=tasks
json.dump(D,open('data/r3/tasks_josh_myths.json','w'),ensure_ascii=False,indent=1); json.dump(tasks,open('data/r3/tasks.json','w'),ensure_ascii=False)
for t in tasks:
    print(t['id'],[(len(c['text'].split()),bool(c.get('pre_removed')),c.get('cut_to_300_tokens')) for c in t['candidates'][2:]],[c['text'][:50] for c in t['candidates'][2:]])
print(spend())
