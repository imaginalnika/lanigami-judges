// Myths redo with Josh's original openers. Loaded after app.js; #r3... routed here.
let R3=null;
const q3=x=>x==null?'–':(typeof x==='number'?x.toFixed(2):x);const p3=x=>x==null?'–':Math.round(x*100)+'%';
const JN3={'opus46':'Opus 4.6','opus55':'Opus 5.5','sol61':'GPT-6.1 Sol','gpt4o':'GPT-4o','qwen':'Qwen base samples'};
const R3SEC=[['home','Myths: findings'],['judges','Instruct judges'],['base','Base prefills'],['calibration','Calibration'],['scoring','Likelihood scoring'],['task','Per task (candidates, unused samples)'],['prompts','Exact prompt text'],['superseded','Superseded: invalid openers']];
function r3nav(sec){return `<div style="margin:6px 0 12px">`+R3SEC.map(([k,n])=>`<a href="#r3/${k}" style="margin-right:10px;font-size:14px;${k===sec?'font-weight:700;border-bottom:2px solid var(--ref)':''}">${n}</a>`).join('')+`</div>`}
async function r3route(parts){
  if(!R3)R3=await J('site-data/r3/index.json');
  const sec=parts[1]||'home';let o=`<h2 style="margin-top:4px">Creation myths, redone with Josh's original openers</h2>`+r3nav(sec);const S=R3.summary;
  if(sec==='home'){o+=`<div id="r3f"></div>`+`<h3>Spend</h3><pre>${esc(JSON.stringify(R3.spend,null,1))}</pre>`;$('#app').innerHTML=o;fetch('findings_r3.html').then(r=>r.text()).then(t=>$('#r3f').innerHTML=t);return}
  if(sec==='judges')o+=r3judges(S);else if(sec==='base')o+=r3base(S);else if(sec==='calibration')o+=r3cal(S);else if(sec==='scoring')o+=r3scoring(S);
  else if(sec==='prompts')o+=r3prompts();else if(sec==='superseded')o+=r3super();
  else if(sec==='task'){o+=`<div id="r3t"></div>`;$('#app').innerHTML=o;await r3task(parts[2]);return}
  $('#app').innerHTML=o;
}
function srow(m){return ['qwen','opus46','opus55','sol61','gpt4o'].map(s=>`<td class="num">${p3(m.share[s])}</td>`).join('')}
const SH=`<th>Qwen base<br><span class="mut">(chance 33%)</span></th><th>Opus 4.6<br><span class="mut">(17%)</span></th><th>Opus 5.5</th><th>Sol</th><th>GPT-4o</th>`;
function r3judges(S){
  let o=`<p class="mut">Judges saw letters A–F in shuffled order (two orders per task, reversed). Shares = share of the judge's votes going to candidates of each origin, averaged over 6 tasks (3 prompts × 2 orders = 6 votes per task). Longest-pick chance 17%; ornate rank 0 = plainest, 1 = most ornate.</p>`;
  o+=`<h3>Per judge (3 prompts pooled)</h3><div class="scroll"><table><tr><th>Judge</th><th>Picks longest</th><th>Ornate rank of pick</th>${SH}</tr>`;
  for(const [j,m] of Object.entries(S.instruct_metrics))o+=`<tr><td>${JN3[j]}</td><td class="num">${p3(m.p_longest)}</td><td class="num">${q3(m.ornate_rank_pick)}</td>${srow(m)}</tr>`;
  o+=`</table></div><h3>Per judge × prompt</h3><div class="scroll"><table><tr><th>Judge | prompt</th><th>Picks longest</th><th>Ornate rank</th>${SH}<th>Same top pick when order reversed</th></tr>`;
  for(const [k,m] of Object.entries(S.instruct_prompt_metrics))o+=`<tr><td>${esc(k)}</td><td class="num">${p3(m.p_longest)}</td><td class="num">${q3(m.ornate_rank_pick)}</td>${srow(m)}<td class="num">${p3(S.instruct_prompt_oc[k])}</td></tr>`;
  o+=`</table></div><h3>Top pick agreement between instruct judges (share of 6 tasks)</h3><div class="scroll"><table><tr><th>Pair</th><th>Agree</th></tr>`;
  for(const [k,v] of Object.entries(S.agreement.instruct_pair_matrix))o+=`<tr><td>${k.split('|').map(x=>JN3[x]).join(' – ')}</td><td class="num">${p3(v)}</td></tr>`;
  o+=`</table></div><p class="mut">Unparsed verdicts: ${S.instruct_unparsed} of ${S.instruct_calls} calls.</p>`;
  o+=`<h3>Top pick per task</h3><div class="scroll"><table><tr><th>Judge</th>`+S.tasks_meta.map(t=>`<th>${t.id.slice(3)}</th>`).join('')+`</tr>`;
  const src={};S.tasks_meta.forEach(t=>t.cands.forEach(c=>src[c.cid]=c.src));
  for(const [j,p] of Object.entries(S.instruct_picks))o+=`<tr><td>${JN3[j]}</td>`+S.tasks_meta.map(t=>`<td>${p[t.id]?JN3[src[p[t.id]]]:'<span class="mut">tie</span>'}</td>`).join('')+'</tr>';
  return o+`</table></div>`}
function r3base(S){
  let o=`<p class="mut">Qwen 3.5 35B-A3B Base, 17 prefills (R1 = round 1, R2 = round 2 prestige / neutral k-example). Verdict = next-token probability over letters (slot) or letter at the "Keep:" slot averaged over 6 samples (k-example). Averaged over the two orders; 6 tasks. Raw prefill text is under "Exact prompt text".</p><div class="scroll"><table><tr><th>Prefill</th><th>Rd</th><th>Picks longest</th><th>Ornate rank</th>${SH}<th>Agree w/ instruct judges</th><th>Same top pick, reversed order</th><th>Label mass</th></tr>`;
  for(const r of S.base)o+=`<tr><td>${r.prefill}</td><td>${r.round}</td><td class="num">${p3(r.metrics.p_longest)}</td><td class="num">${q3(r.metrics.ornate_rank_pick)}</td>${srow(r.metrics)}<td class="num">${p3(r.agree_instruct_mean)}</td><td class="num">${p3(r.oc)}</td><td class="num">${q3(r.label_mass)}</td></tr>`;
  const g=S.base_group,A=S.agreement;
  o+=`</table></div><p class="mut">Mean over prefills: Qwen-sample share ${p3(g.qwen_share_mean)}, picks longest ${p3(g.p_longest_mean)}. Agreement: base prefill vs instruct judge ${p3(A.base_prefill_vs_instruct)}; instruct vs instruct ${p3(A.instruct_vs_instruct)}; base vs base ${p3(A.base_vs_base)}. "Agree w/ instruct judges" is mean over the four instruct judges (including GPT-4o, which agrees with the others on 25%).</p>`;
  o+=`<h3>Top pick per task (origin of the winning candidate)</h3><div class="scroll"><table><tr><th>Prefill</th>`+S.tasks_meta.map(t=>`<th>${t.id.slice(3)}</th>`).join('')+`</tr>`;
  const src={};S.tasks_meta.forEach(t=>t.cands.forEach(c=>src[c.cid]=c.src));
  for(const r of S.base)o+=`<tr><td>${r.prefill}</td>`+S.tasks_meta.map(t=>`<td>${r.picks[t.id]?JN3[src[r.picks[t.id]]]:'<span class="mut">tie</span>'}</td>`).join('')+'</tr>';
  return o+`</table></div>`}
function r3cal(S){
  let o=`<p class="mut">Contextual calibration: letter prior estimated from the same prompt with every candidate replaced by "N/A" (per prefill, per task), subtracted by division and renormalised. Only slot prefills. "Same top pick" = top pick identical across the two orders when each order is taken alone.</p><div class="scroll"><table><tr><th>Prefill</th><th>P(letter A) raw</th><th>cal</th><th>Same top pick (single order) raw</th><th>cal</th><th>Agree w/ instruct raw</th><th>cal</th><th>Qwen-sample share (cal)</th></tr>`;
  for(const c of S.calibration)o+=`<tr><td>${c.prefill}</td><td class="num">${p3(c.posA_raw)}</td><td class="num">${p3(c.posA_cal)}</td><td class="num">${p3(c.oc_single_raw)}</td><td class="num">${p3(c.oc_single_cal)}</td><td class="num">${p3(c.agree_inst_raw)}</td><td class="num">${p3(c.agree_inst_cal)}</td><td class="num">${p3(c.metrics_cal.share.qwen)}</td></tr>`;
  return o+`</table></div>`}
function r3scoring(S){
  let o=`<p class="mut">Mean per-token logprob of each candidate under Qwen 3.5 35B-A3B Base after each prefix (prefix texts under "Exact prompt text"). Winner per rule = candidate with the highest value. No judgement of correctness.</p><h3>By candidate origin (mean over tasks)</h3><div class="scroll"><table><tr><th>Origin</th><th>neutral mean logprob</th><th>good − neutral</th><th>good − bad</th></tr>`;
  for(const [s,v] of Object.entries(S.scoring_by_src))o+=`<tr><td>${JN3[s]}</td><td class="num">${v.neutral_mean.toFixed(3)}</td><td class="num">${v.pmi_good_minus_neutral.toFixed(3)}</td><td class="num">${v.good_minus_bad.toFixed(3)}</td></tr>`;
  o+=`</table></div><h3>Winners by rule</h3><div class="scroll"><table><tr><th>Rule</th>`+S.tasks_meta.map(t=>`<th>${t.id.slice(3)}</th>`).join('')+`<th>Agree w/ instruct judges</th></tr>`;
  const src={};S.tasks_meta.forEach(t=>t.cands.forEach(c=>src[c.cid]=c.src));
  for(const [n,w] of Object.entries(S.scoring.winners))o+=`<tr><td>${n.slice(3)}</td>`+S.tasks_meta.map(t=>`<td>${w[t.id]?JN3[src[w[t.id]]]:'–'}</td>`).join('')+`<td class="num">${p3(S.agreement.per_scoring[n])}</td></tr>`;
  return o+`</table></div>`}
function r3prompts(){
  let o=`<h3>Wrapper text given to the instruct models (added by the assistant)</h3><p class="mut">User message = wrapper + Josh's exact opener, nothing else (no system prompt). Instruct generation: Opus 4.6, Opus 5.5 and GPT-4o at temperature 1.0; GPT-6.1 Sol default temperature with reasoning effort low (hidden); max_tokens 900 (Opus 4.6/GPT-4o), 900 then 2500 for one empty Opus 5.5 reply, 1500 (Sol). All outputs then cut to 300 Qwen tokens.</p><pre>${esc(R3.wrapper)}&lt;opener&gt;</pre><pre>${esc(R3.wrapper+R3.template.replace('{NAME}','&lt;NAME&gt;'))}</pre>`;
  o+=`<h3>Opener template (Josh's)</h3><pre>${esc(R3.template)}</pre><p class="mut">Josh's three: Furiotre (P07), Lanigami (P09), Deniasent (P10). <b>Added by the assistant, same template: Marvethine, Oluskar, Tessimire.</b></p>`;
  o+=`<h3>Base judge prefills used on these tasks (<code>prompts/base-r3/</code>)</h3><p class="mut">Identical to Round 1/2 files except the myth worked examples inside the k-example files, which were re-expressed in Josh's opener template with continuation-style candidates (assistant-written). The myth text box is the one used here.</p>`;
  for(const p of R3.prefills)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">(${p.mode}) ${esc(p.title)}</span></summary>${pbox(p)}</details>`;
  o+=`<h3>Instruct judge prompts (unchanged from Round 1)</h3>`;for(const p of R3.instruct_prefills)o+=`<details class="card"><summary><b>${esc(p.id)}</b></summary>${pbox(p)}</details>`;
  o+=`<h3>Scoring prefixes</h3><p class="mut">Candidate text is appended after one space. Example (myth task jm-P09):</p>`;
  for(const [k,v] of Object.entries(R3.prefix_example))o+=`<div class="mut">${k}</div><pre>${esc(v)}</pre>`;
  return o}
function r3super(){return `<div class="warn"><b>Superseded: invalid openers.</b> These myth tasks (myth-1…myth-6 in Round 1 and the origin-controlled mythB-*/mythI-* sets in Round 2) used openers the assistant invented, not Josh's prompts. Nothing was deleted; the results are kept for reference only and should not be read as evidence about Josh's setup.</div><p>Round 1 myth tasks are in the <a href="#tasks">Tasks</a> list under the "superseded" group; Round 2 ones are in <a href="#r2/task">Round 2 → Per task</a> under the same group.</p>`}
async function r3task(id){
  let o=`<select id="r3sel">`+R3.tasks.map(t=>`<option value="${t.id}" ${t.id===id?'selected':''}>${t.id} · ${t.set} · ${esc(t.title)}</option>`).join('')+`</select>`;
  if(!id){$('#r3t').innerHTML=o+'<p class="mut">Pick a task.</p>';$('#r3sel').onchange=e=>location.hash='#r3/task/'+e.target.value;return}
  const D=await J(`site-data/r3/task/${id}.json`);const t=D.task;
  o+=`<h3>${t.id} <span class="mut">(${esc(t.set)}; prompt ${t.prompt_id})</span></h3><div class="card"><b>Opener, exact</b><pre>${esc(t.source)}</pre></div>`;
  o+=`<h3>Candidates (what judges saw; origins revealed here)</h3>`;
  t.candidates.forEach((c,i)=>{const k=c.kinds.includes('base')?'base':'instruct';
    o+=`<div class="cand ${k}"><b>C${i+1}</b> <span class="tag ${k}">${k}</span><span class="mut">${esc(c.origins.join(' = '))} · ${c.words} words · ornate rank ${c.ornate.toFixed(2)}${c.is_longest?' · longest':''}${c.trimmed?' · trimmed to last full sentence':''}${c.cut_to_300_tokens?' · cut at 300 tokens, trimmed to last full sentence ('+c.tokens_before_cut+' tokens before cut)':''}${c.pre_removed?' · echoed text removed':''}${c.regenerated_note?' · '+esc(c.regenerated_note):''}</span><br>${esc(c.text).replace(/\n/g,'<br>')}<details><summary class="mut">raw output before any cleanup</summary><pre>${esc(c.raw)}</pre></details></div>`});
  const un=t.base_samples_unused||[],dr=t.base_samples_dropped||[];
  o+=`<h3>Other Qwen base samples</h3><p class="mut">Dropped as degenerate junk: ${dr.length}. Unused (valid, but only the first 2 valid samples were taken): ${un.length}.</p>`;
  dr.forEach(u=>o+=`<details><summary class="mut">DROPPED sample ${u.sample}: ${esc(u.dropped_reason)}</summary><pre>${esc(u.raw)}</pre></details>`);
  un.forEach(u=>o+=`<details><summary class="mut">unused sample ${u.sample} (${u.finish})</summary><pre>${esc(u.raw)}</pre></details>`);
  // who preferred what
  const agg={};
  for(const r of D.base){const k='Qwen base · '+r.prefill;agg[k]??={d:{}};if(!r.dist_norm)continue;for(const [l,p] of Object.entries(r.dist_norm)){const c=r.label_to_short[l];agg[k].d[c]=(agg[k].d[c]||0)+(p||0)/2}
    if(r.cal_dist){const k2=k+' (cal)';agg[k2]??={d:{}};for(const [l,p] of Object.entries(r.cal_dist)){const c=r.label_to_short[l];agg[k2].d[c]=(agg[k2].d[c]||0)+p/2}}}
  for(const r of D.instruct){if(!r.verdict)continue;const k=JN3[r.judge]+' · '+r.prefill;agg[k]??={d:{}};const c=r.label_to_short[r.verdict];agg[k].d[c]=(agg[k].d[c]||0)+1}
  o+=`<h3>Who preferred what</h3><div class="scroll"><table><tr><th>Judge · prompt</th>`+t.candidates.map((c,i)=>`<th>C${i+1}</th>`).join('')+`</tr>`;
  const keys=Object.keys(agg).sort((a,b)=>(a.startsWith('Qwen')?1:0)-(b.startsWith('Qwen')?1:0));
  for(const k of keys){const tot=Object.values(agg[k].d).reduce((x,y)=>x+y,0)||1;o+=`<tr><td class="cell">${esc(k)}</td>`+t.candidates.map((c,i)=>`<td class="cell">${bar((agg[k].d[i+1]||0)/tot,36)}</td>`).join('')+'</tr>'}
  o+=`</table></div>`;
  const sc=D.scoring,pf=Object.keys(sc[0].per_prefix_mean);
  o+=`<h3>Likelihood scoring</h3><div class="scroll"><table><tr><th>Cand</th><th>tokens</th>`+pf.map(p=>`<th>${p}</th>`).join('')+`<th>good−neutral</th><th>good−bad</th></tr>`;
  sc.forEach(r=>{const i=t.candidates.findIndex(c=>c.cid===r.cid)+1;o+=`<tr><td>C${i}</td><td class="num">${r.n_tokens}</td>`+pf.map(p=>`<td class="num">${r.per_prefix_mean[p].toFixed(3)}</td>`).join('')+`<td class="num">${r.pmi_good_minus_neutral.toFixed(3)}</td><td class="num">${r.good_minus_bad.toFixed(3)}</td></tr>`});
  o+=`</table></div><h3>Full prompts and answers</h3>`;
  const groups={};for(const r of D.base)(groups['Qwen base · '+r.prefill]??=[]).push(r);for(const r of D.instruct)(groups[JN3[r.judge]+' · '+r.prefill]??=[]).push(r);
  for(const [k,rs] of Object.entries(groups)){rs.sort((a,b)=>a.order-b.order);o+=`<details class="card"><summary><b>${esc(k)}</b></summary>`;
    for(const r of rs){o+=`<h3>Order ${r.order+1} <span class="mut">(${r.labels.map(l=>l+'=C'+r.label_to_short[l]).join(', ')})</span></h3><details><summary class="mut">exact prompt sent</summary><pre>${esc(r.prompt)}</pre></details>`;
      if(r.samples){o+=`<div>${r.labels.map(l=>`${l}(C${r.label_to_short[l]}) ${p3(r.dist_norm?.[l])}`).join(' · ')} <span class="mut">· label mass ${q3(r.label_mass)}</span></div>`;
        if(r.mode!=='slot')o+=`<details><summary class="mut">${r.samples.length} sampled continuations</summary>`+r.samples.map((s,i)=>`<div class="mut">sample ${i+1} → ${s.verdict?s.verdict+' (C'+r.label_to_short[s.verdict]+')':'none'}</div><pre>${esc(s.text)}</pre>`).join('')+`</details>`}
      else o+=`<div>Verdict: <b>${r.verdict?r.verdict+' (C'+r.label_to_short[r.verdict]+')':'none'}</b></div><pre>${esc(r.text||'')}</pre>`}
    o+=`</details>`}
  $('#r3t').innerHTML=o;$('#r3sel').onchange=e=>location.hash='#r3/task/'+e.target.value;
}
