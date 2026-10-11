import json
B='../dh-loc/translation/experiments/'
fr=json.load(open(B+'frontier-pilot-2026-10-10/workbook-data.json'))[0]['rows']
g=json.load(open(B+'gpt4o-pilot-2026-10-10/workbook-data.json'))[0]['rows']
h=fr[0]; gh=g[0]; gm={r[0]:r for r in g[1:]}
ROWS=['DH-0009','DH-0043','DH-0074','DH-0159','DH-0174','DH-0349','DH-0351','DH-0474','DH-0671','DH-1453']
tasks=[]
for r in fr[1:]:
    if r[0] not in ROWS: continue
    d=dict(zip(h,r)); gd=dict(zip(gh,gm[r[0]]))
    src=[('Qwen 3.5 35B-A3B Base (direct)','base',d['qwen 35b + skill']),
         ('Opus 4.6 (direct)','instruct',d['Opus 4.6 + skill']),
         ('Opus 5.5 (direct)','instruct',d['Opus 5.5 + skill']),
         ('GPT-4o (direct)','instruct',gd['GPT-4o + skill']),
         ('Opus 5.5 draft -> Qwen base refine','base-refine',d['Opus 5.5->base'])]
    cands={}
    for name,kind,t in src:
        cands.setdefault(t,[]).append((name,kind))
    tasks.append({'id':'tr-'+r[0],'type':'translation','source':d['ko'],'context':d['출력 용도'],
      'candidates':[{'text':t,'origins':[o[0] for o in os],'kinds':sorted({o[1] for o in os})} for t,os in cands.items()]})
json.dump(tasks,open('./data/translation_tasks_raw.json','w'),ensure_ascii=False,indent=1)
for t in tasks:
    print(t['id'],t['source'][:70],'|',t['context'])
    for c in t['candidates']: print('   ',c['kinds'],c['origins'],'::',c['text'][:200].replace('\n','\\n'))
