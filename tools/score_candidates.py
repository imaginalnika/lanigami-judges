# run with python (with tinker installed) ; needs TINKER_API_KEY in env
import os,sys,json,glob; os.environ['TINKER_TELEMETRY']='0'; os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1'
sys.path.insert(0,'./tools')
import tinker
from common import load_template
from concurrent.futures import ThreadPoolExecutor
S='./'
tasks=json.load(open(S+'data/tasks.json'))+json.load(open(S+'data/r2/tasks_origin_controlled.json'))
pre=[load_template(p) for p in sorted(glob.glob(S+'prompts/score/*.txt'))]
c=tinker.ServiceClient().create_sampling_client(base_model='Qwen/Qwen3.5-35B-A3B-Base'); tok=c.get_tokenizer()
def one(args):
    t,cand,p=args
    sec=p['sections'][t['type']]
    prefix=sec.replace('{SOURCE}',t['display_source']).replace('{CONTEXT}',t.get('context','')).rstrip('\n')
    # translation templates end with "English:" -> candidate follows after a space; myth ends with opener -> space
    sep=' '
    full=prefix+sep+cand['text']
    enc=tok(full,return_offsets_mapping=True,add_special_tokens=False)
    ids=enc['input_ids']; offs=enc['offset_mapping']
    start=len(prefix)
    ci=[i for i,(a,b) in enumerate(offs) if b>start]
    lps=c.compute_logprobs(tinker.types.ModelInput.from_ints(ids)).result()
    sel=[lps[i] for i in ci if lps[i] is not None]
    return {'task':t['id'],'cid':cand['cid'],'prefix_id':p['id'],'group':p['group'],'n_tokens':len(sel),'sum':sum(sel),'mean':sum(sel)/max(len(sel),1),'prefix_text':prefix}
jobs=[(t,cd,p) for t in tasks for cd in t['candidates'] for p in pre]
print(len(jobs),'jobs')
with ThreadPoolExecutor(8) as ex: res=list(ex.map(one,jobs))
json.dump(res,open(S+'data/r2/scores.json','w'),ensure_ascii=False)
print('done')
