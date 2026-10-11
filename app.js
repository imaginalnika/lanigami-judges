const $=s=>document.querySelector(s);let IDX=null;const cache={};
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const pct=x=>x==null?'–':Math.round(x*100)+'%';const f2=x=>x==null?'–':x.toFixed(2);
const JN={'qwen35b-base':'Qwen 3.5 35B-A3B Base','opus46':'Opus 4.6','opus55':'Opus 5.5','sol61':'GPT-6.1 Sol','gpt4o':'GPT-4o'};
async function J(u){if(cache[u])return cache[u];const r=await fetch(u);return cache[u]=await r.json()}
function bar(p,w=70){return `<span class="bar" style="width:${Math.round((p||0)*w)}px"></span> ${pct(p)}`}
async function route(){
  if(!IDX)IDX=await J('site-data/index.json');
  const h=(location.hash||'#overview').slice(1).split('/');
  document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.id==='n-'+h[0]));
  if(h[0]==='overview')overview();else if(h[0]==='tasks')await tasks(h[1]);else if(h[0]==='prompts')prompts();
}
window.addEventListener('hashchange',route);route();
function prompts(){
  let o=`<h2>Base-judge prefills (Qwen 3.5 35B-A3B Base, plain-text completion)</h2><p class="mut">One file per prefill in <code>prompts/base/</code>. Each file has a <code>@@translation</code> and a <code>@@myth</code> section. Placeholders: {SOURCE}, {CONTEXT}, {CANDS} (lettered candidates). The base model sees the rendered text only, no chat template. Raw files, exactly as used:</p>`;
  for(const p of IDX.base_prefills)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">(${p.mode}) ${esc(p.title)}</span></summary><pre>${esc(p.raw)}</pre></details>`;
  o+=`<h2>Instruct-judge prompts (Opus 4.6, Opus 5.5, GPT-6.1 Sol, GPT-4o)</h2><p class="mut">Sent as one plain user message (no system prompt).</p>`;
  for(const p of IDX.instruct_prefills)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">${esc(p.title)}</span></summary><pre>${esc(p.raw)}</pre></details>`;
  o+=`<h2>Myth generation prompt (instruct models)</h2><pre>${esc(IDX.myth_gen_prompt)}</pre><p class="mut">Qwen base got only the opener sentence as plain text.</p>`;
  $('#app').innerHTML=o;
}
function overview(){
  const S=IDX.summary;let o='';
  o+=`<div class="warn"><b>No verdict here is marked right or wrong.</b> This page reports what each judge preferred and how that relates to length and a crude ornateness proxy. Judging taste is for you.</div>`;
  o+=`<div id="findings"></div>`;
  const rows=S.rows;
  function tbl(typ){
    let t=`<div class="scroll"><table><tr><th>Judge</th><th>Prompt</th><th>Picks longest<br><span class="mut">(chance)</span></th><th>Ornate rank of pick<br><span class="mut">(0 plain–1 ornate)</span></th><th>Picks base-origin<br><span class="mut">(chance)</span></th><th>Order-consistent</th></tr>`;
    for(const r of rows){const a=r[typ];if(!a)continue;const oc=S.order_consistency[r.judge+'|'+r.prompt];
      t+=`<tr><td>${JN[r.judge]}</td><td>${esc(r.prompt)}</td><td class="num">${pct(a.p_longest)} <span class="mut">(${pct(a.chance_longest)})</span></td><td class="num">${f2(a.mean_ornate_rank_of_pick)}</td><td class="num">${pct(a.p_base_origin)} <span class="mut">(${pct(a.chance_base_origin)})</span></td><td class="num">${pct(oc)}</td></tr>`}
    return t+'</table></div>'}
  o+=`<h2>Preferences vs length / ornateness</h2><p class="mut">Shares are averaged over tasks and over the two candidate orders. Ornate rank = mean within-task rank of word count, long-word ratio (≥9 letters), punctuation density and -ly density. "Order-consistent" = same top pick when the candidate order is reversed.</p>`;
  o+=`<h3>Myths (6 tasks)</h3>`+tbl('myth')+`<h3>Translations (10 tasks)</h3>`+tbl('translation');
  const OS=S.origin_share;
  function otbl(typ){const keys=Object.keys(OS).filter(k=>k.endsWith('|'+typ));const origs=Object.keys(S.origin_feats[typ]);
    let t=`<div class="scroll"><table><tr><th>Judge (instruct: mean of its 3 prompts)</th>`+origs.map(x=>`<th>${x}</th>`).join('')+`</tr>`;
    t+=`<tr><td class="mut">candidate stats: mean words / ornate rank / n</td>`+origs.map(x=>{const f=S.origin_feats[typ][x];return `<td class="mut">${f.words.toFixed(0)} w · ${f.ornate_rank.toFixed(2)} · ${f.n}</td>`}).join('')+'</tr>';
    for(const k of keys){const [j]=k.split('|');t+=`<tr><td>${JN[j]||j}</td>`+origs.map(x=>`<td class="num">${pct(OS[k][x])}</td>`).join('')+'</tr>'}
    return t+'</table></div>'}
  o+=`<h2>Preferences by candidate origin</h2><p class="mut">Mean share of the judge's preference that went to candidates from each origin, over the tasks where that origin appears (instruct judges here pool their 3 prompts; the base-judge row pools all 11 prefills; per-prefill numbers are in the table above). Chance for Qwen base in myths is 50% (it has 2 of 4 candidates); other origins 25%. Opus 4.6, Opus 5.5, Sol and GPT-4o each wrote myths in only 3 tasks.</p><h3>Myths</h3>`+otbl('myth')+`<h3>Translations</h3>`+otbl('translation');
  // agreement: base prefill vs instruct judges
  const keys=[...new Set(rows.map(r=>r.judge+'|'+r.prompt))];
  const inst=['opus46','opus55','sol61','gpt4o'],iprompts=['i1-what-do-you-think','i2-which-do-you-prefer','i3-texture-feel'];
  const bp=IDX.base_prefills.map(p=>p.id);
  o+=`<h2>Agreement of top pick (all 16 tasks)</h2><p class="mut">Share of tasks where the two judge×prompt combinations name the same candidate as top pick (tasks where either side tied between its two order-runs are left out of that cell; chance would be about 20–25%). Rows: base prefills. Columns: instruct judges, averaged over their 3 prompts.</p><div class="scroll"><table><tr><th>Base prefill</th>`+inst.map(j=>`<th>${JN[j]}</th>`).join('')+`<th>Other base prefills (mean)</th></tr>`;
  for(const b of bp){o+=`<tr><td>${b}</td>`;
    for(const j of inst){const v=iprompts.map(p=>S.agree[`qwen35b-base|${b}||${j}|${p}`]?.agree).filter(x=>x!=null);o+=`<td class="num">${pct(v.reduce((a,c)=>a+c,0)/v.length)}</td>`}
    const ov=bp.filter(x=>x!==b).map(x=>S.agree[`qwen35b-base|${b}||qwen35b-base|${x}`]?.agree).filter(x=>x!=null);o+=`<td class="num">${pct(ov.reduce((a,c)=>a+c,0)/ov.length)}</td></tr>`}
  o+=`</table></div><h3>Instruct judges vs each other (mean over prompt pairs)</h3><div class="scroll"><table><tr><th></th>`+inst.map(j=>`<th>${JN[j]}</th>`).join('')+`</tr>`;
  for(const a of inst){o+=`<tr><td>${JN[a]}</td>`;for(const b of inst){if(a===b){o+='<td>–</td>';continue}
    const v=[];for(const p of iprompts)for(const q of iprompts){const x=S.agree[`${a}|${p}||${b}|${q}`]?.agree;if(x!=null)v.push(x)}o+=`<td class="num">${pct(v.reduce((x,y)=>x+y,0)/v.length)}</td>`}o+='</tr>'}
  o+=`</table></div>`;
  // JSD
  o+=`<h2>How far prefills move the base verdict distribution</h2><p class="mut">Mean Jensen–Shannon divergence (bits, 0 = identical, 1 = disjoint) between two prefills' candidate distributions, averaged over tasks.</p><div class="scroll"><table><tr><th></th>`+bp.map(b=>`<th>${b.replace('kex-','k-')}</th>`).join('')+`</tr>`;
  for(const a of bp){o+=`<tr><td>${a}</td>`+bp.map(b=>`<td class="num">${a===b?'–':f2(S.jsd[a+'||'+b])}</td>`).join('')+'</tr>'}
  o+=`</table></div>`;
  // CoT
  o+=`<h2>Base model chain of thought (k-example prompts)</h2><div class="scroll"><table><tr><th>Prefill</th><th>samples</th><th>wrote per-candidate notes</th><th>wrote a Why line</th><th>reached a Keep verdict</th></tr>`;
  for(const [k,v] of Object.entries(S.cot_stats))o+=`<tr><td>${k}</td><td class="num">${v.n}</td><td class="num">${pct(v.has_notes/v.n)}</td><td class="num">${pct(v.has_why/v.n)}</td><td class="num">${pct(v.has_verdict/v.n)}</td></tr>`;
  o+=`</table></div><h3>Most frequent words in the base model's own "Why:" lines</h3>`;
  for(const [k,v] of Object.entries(S.why_words))o+=`<div class="card"><b>${k}</b><br><span class="mut">${v.map(x=>x[0]+' '+x[1]).join(' · ')}</span></div>`;
  if(IDX.spend)o+=`<h2>Spend</h2><pre>${esc(JSON.stringify(IDX.spend,null,1))}</pre>`;
  o+=`<h2>Caveats</h2><ul><li>16 tasks × 2 candidate orders; small numbers. Distributions are descriptive.</li><li>Qwen base verdicts at a "slot" prefill come from next-token log-probabilities of the letters (top-20 logprobs from Tinker), renormalised over the letters; "label mass" is the share of probability that went to letters at all and is shown on each task page. CoT prefills are sampled (8 samples) and the letter after "Keep:" is read from those logprobs.</li><li>The worked examples in the k-example prefills were written by an instruct model (the assistant), so they carry that model's idea of the three tastes; that is why three variants exist.</li><li>Myth candidates by an instruct model were judged partly by that same model family (self-preference is possible, not separated).</li><li>The ornateness proxy is crude (lexical and punctuation only).</li></ul>`;
  $('#app').innerHTML=o;
  fetch('findings.html').then(r=>r.ok?r.text():'').then(t=>{if(t)$('#findings').innerHTML=t});
}
async function tasks(id){
  let o=`<select id="sel">`+IDX.tasks.map(t=>`<option value="${t.id}" ${t.id===id?'selected':''}>${t.id} · ${esc(t.title)}</option>`).join('')+`</select>`;
  if(!id){$('#app').innerHTML=o+'<p class="mut">Pick a task.</p>';$('#sel').onchange=e=>location.hash='#tasks/'+e.target.value;return}
  const D=await J(`site-data/task/${id}.json`);const t=D.task;
  o+=`<h2>${t.type==='translation'?'Translation':'Creation myth'}: ${t.id}</h2>`;
  o+=`<div class="card"><b>${t.type==='translation'?'Korean source':'Opener (given to every writer)'}</b><br>${esc(t.display_source)}${t.context?`<br><span class="mut">Where it appears: ${esc(t.context)}</span>`:''}</div>`;
  o+=`<h3>Candidates (origins revealed; judges saw only letters, in shuffled order)</h3>`;
  t.candidates.forEach((c,i)=>{const k=c.kinds.includes('base')?'base':c.kinds.includes('base-refine')?'base-refine':'instruct';
    o+=`<div class="cand ${k}"><b>C${i+1}</b> ${c.kinds.map(x=>`<span class="tag ${x}">${x}</span>`).join('')}<span class="mut">${esc(c.origins.join(' = '))}<br>${c.feats.words} words · ornate rank ${c.ornate.toFixed(2)}${c.is_longest?' · longest':''}</span><br>${esc(c.text).replace(/\n/g,'<br>')}</div>`});
  if(t.unused_base_samples?.length)o+=`<details><summary class="mut">${t.unused_base_samples.length} other Qwen base samples not used (derailed or too short)</summary>${t.unused_base_samples.map(u=>`<pre>${esc(u.raw)}</pre>`).join('')}</details>`;
  // matrix
  const n=t.candidates.length;const rowsK=[];
  const agg={};
  for(const r of D.base){const k='qwen35b-base|'+r.prefill;agg[k]??={n:0,d:{}};if(!r.dist_norm)continue;agg[k].n++;for(const [l,p] of Object.entries(r.dist_norm)){const c=r.label_to_short[l];agg[k].d[c]=(agg[k].d[c]||0)+(p||0)}}
  for(const r of D.instruct){const k=r.judge+'|'+r.prefill;agg[k]??={n:0,d:{}};if(!r.verdict)continue;agg[k].n++;const c=r.label_to_short[r.verdict];agg[k].d[c]=(agg[k].d[c]||0)+1}
  o+=`<h3>Who preferred what</h3><p class="mut">Share of the judge's preference per candidate (base: probability averaged over 2 orders; instruct: share of its 2 answers, one per order).</p><div class="scroll"><table><tr><th>Judge · prompt</th>`+t.candidates.map((c,i)=>`<th>C${i+1}</th>`).join('')+`</tr>`;
  const order=[...Object.keys(agg)].sort((a,b)=>(a.startsWith('qwen')?1:0)-(b.startsWith('qwen')?1:0)||a.localeCompare(b));
  for(const k of order){const a=agg[k];const tot=Object.values(a.d).reduce((x,y)=>x+y,0)||1;const [j,p]=k.split('|');
    o+=`<tr><td class="cell">${JN[j]}<br><span class="mut">${p}</span></td>`+t.candidates.map((c,i)=>`<td class="cell">${bar((a.d[i+1]||0)/tot,40)}</td>`).join('')+'</tr>'}
  o+=`</table></div><h3>Every judge × prompt: full prompt text and answers</h3>`;
  const groups={};for(const r of D.instruct)(groups[r.judge+'|'+r.prefill]??=[]).push(r);for(const r of D.base)(groups['qwen35b-base|'+r.prefill]??=[]).push(r);
  for(const k of order){const [j,p]=k.split('|');const rs=groups[k].sort((a,b)=>a.order-b.order);
    o+=`<details class="card"><summary><b>${JN[j]}</b> · ${esc(p)}</summary>`;
    for(const r of rs){
      o+=`<h3>Order ${r.order+1} <span class="mut">(letters → ${r.labels.map(l=>l+'=C'+r.label_to_short[l]).join(', ')})</span></h3><details><summary class="mut">exact prompt sent</summary><pre>${esc(r.prompt)}</pre></details>`;
      if(j==='qwen35b-base'){
        o+=`<div>${r.mode==='slot'?'Next-token distribution over letters':'Mean letter distribution at the Keep: slot over samples'}: `+r.labels.map(l=>`${l}(C${r.label_to_short[l]}) ${pct(r.dist_norm?.[l])}`).join(' · ')+` <span class="mut">· label mass ${f2(r.label_mass)} · ${r.n_with_dist}/8 samples with a verdict slot</span></div>`;
        o+=`<details><summary class="mut">${r.samples.length} sampled continuations</summary>`+r.samples.map((s,i)=>`<div class="mut">sample ${i+1} → verdict ${s.verdict?s.verdict+' (C'+r.label_to_short[s.verdict]+')':'none'}</div><pre>${esc(s.text)}</pre>`).join('')+`</details>`;
      }else{
        o+=`<div>Verdict: <b>${r.verdict?r.verdict+' (C'+r.label_to_short[r.verdict]+')':'none'}</b> <span class="mut">${r.provider||''}${r.error?' ERROR '+esc(r.error):''}</span></div><pre>${esc(r.text||'')}</pre>`}
    }
    o+=`</details>`}
  $('#app').innerHTML=o;$('#sel').onchange=e=>location.hash='#tasks/'+e.target.value;
}
