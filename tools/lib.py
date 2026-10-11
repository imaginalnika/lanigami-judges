import os,json,time,threading,urllib.request,urllib.error
LEDGER='./data/ledger.jsonl'
_lock=threading.Lock()
TURL="https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1/completions"
ORURL="https://openrouter.ai/api/v1/chat/completions"
OR_MODELS={'opus46':'anthropic/claude-opus-4.6','opus55':'anthropic/claude-opus-5.5','sol61':'openai/gpt-6.1-sol','gpt4o':'openai/gpt-4o'}
OR_LABEL={'opus46':'Opus 4.6','opus55':'Opus 5.5','sol61':'GPT-6.1 Sol','gpt4o':'GPT-4o'}
def ledger(rec):
    with _lock:
        open(LEDGER,'a').write(json.dumps(rec)+'\n')
def spend():
    t={'tinker':0.0,'openrouter':0.0,'tinker_in':0,'tinker_out':0,'or_calls':0,'tinker_calls':0}
    if not os.path.exists(LEDGER): return t
    for l in open(LEDGER):
        r=json.loads(l)
        if r['svc']=='tinker':
            t['tinker']+=r['cost'];t['tinker_in']+=r['in'];t['tinker_out']+=r['out'];t['tinker_calls']+=1
        else:
            t['openrouter']+=r['cost'];t['or_calls']+=1
    return t
def tinker(prompt,max_tokens,temperature=1.0,top_p=1.0,logprobs=None,seed=None,retries=4):
    body={'model':'Qwen/Qwen3.5-35B-A3B-Base','prompt':prompt,'n':1,'max_tokens':max_tokens,'temperature':temperature,'top_p':top_p,'stream':False}
    if logprobs: body['logprobs']=logprobs
    if seed is not None: body['seed']=seed
    for a in range(retries):
        r=urllib.request.Request(TURL,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['TINKER_API_KEY'],'Content-Type':'application/json','User-Agent':'curl/8.5.0','Accept':'*/*'})
        try:
            with urllib.request.urlopen(r,timeout=120) as f: d=json.load(f)
            u=d.get('usage',{}); i=u.get('prompt_tokens',0); o=u.get('completion_tokens',0)
            ledger({'svc':'tinker','in':i,'out':o,'cost':(i*0.54+o*1.335)/1e6})
            return d['choices'][0]
        except urllib.error.HTTPError as e:
            msg=e.read().decode()[:300]
            if e.code in (429,500,502,503,504) and a<retries-1: time.sleep(2+3*a); continue
            raise RuntimeError(f'tinker HTTP {e.code}: {msg}')
        except Exception as e:
            if a<retries-1: time.sleep(2+3*a); continue
            raise RuntimeError('tinker error '+type(e).__name__)
def openrouter(model_key,messages,max_tokens,temperature=None,reasoning=None,retries=3):
    body={'model':OR_MODELS[model_key],'messages':messages,'max_tokens':max_tokens,'usage':{'include':True}}
    if temperature is not None: body['temperature']=temperature
    if reasoning: body['reasoning']=reasoning
    for a in range(retries):
        r=urllib.request.Request(ORURL,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY'],'Content-Type':'application/json','X-Title':'Lanigami judge test'})
        try:
            with urllib.request.urlopen(r,timeout=240) as f: d=json.load(f)
            u=d.get('usage',{})
            ledger({'svc':'openrouter','model':model_key,'in':u.get('prompt_tokens',0),'out':u.get('completion_tokens',0),'cost':u.get('cost',0) or 0})
            ch=d['choices'][0]
            return {'text':ch['message'].get('content') or '','finish':ch.get('finish_reason'),'provider':d.get('provider'),'model':d.get('model'),'usage':u}
        except urllib.error.HTTPError as e:
            msg=e.read().decode()[:400]
            if e.code in (429,500,502,503,504) and a<retries-1: time.sleep(3+4*a); continue
            raise RuntimeError(f'openrouter HTTP {e.code}: {msg}')
        except Exception as e:
            if a<retries-1: time.sleep(3+4*a); continue
            raise RuntimeError('openrouter error '+type(e).__name__)
