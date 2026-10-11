import json,glob,os,re
S='./'
def load_template(path):
    txt=open(path).read(); head,body=txt.split('\n=====\n',1)
    meta={}
    for l in head.splitlines():
        if ': ' in l: k,v=l.split(': ',1); meta[k.strip()]=v.strip()
    secs={}
    for m in re.split(r'^@@',body,flags=re.M)[1:]:
        name,rest=m.split('\n',1); secs[name.strip()]=rest
    meta['sections']=secs
    return meta
def render(meta,task,order):
    cs=[task['candidates'][i] for i in order]
    L='ABCDEFG'
    cands='\n\n'.join(f'{L[k]}. {c["text"]}' for k,c in enumerate(cs))
    sec=meta['sections'][task['type']]
    return sec.replace('{SOURCE}',task['display_source']).replace('{CONTEXT}',task.get('context','')).replace('{CANDS}',cands), [c['cid'] for c in cs]
