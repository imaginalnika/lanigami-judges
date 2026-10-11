import json,random
tr=json.load(open('data/translation_tasks_raw.json')); my=json.load(open('data/myth_tasks_raw.json'))
tasks=[]
for t in tr:
    tasks.append(dict(t,display_source=t['source'],context=t['context']))
for t in my['tasks']:
    o=t['source']; cs=[]
    for c in t['candidates']:
        c=dict(c); c['full_text']=c['text']; c['text']=c['text'][len(o):].strip(); cs.append(c)
    tasks.append(dict(t,candidates=cs,context='',display_source=o))
for i,t in enumerate(tasks):
    for j,c in enumerate(t['candidates']): c['cid']=f"{t['id']}-c{j}"
    idx=list(range(len(t['candidates']))); random.Random(777+i).shuffle(idx)
    t['orders']=[idx,idx[::-1]]
json.dump(tasks,open('data/tasks.json','w'),ensure_ascii=False,indent=1)
print(len(tasks),[ (t['id'],len(t['candidates'])) for t in tasks])
