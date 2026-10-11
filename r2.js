// Round 2 views. Loaded after app.js; app.js route() hands #r2... here.
let R2=null;
const f2r=x=>x==null?'–':(typeof x==='number'?x.toFixed(2):x);const pr=x=>x==null?'–':Math.round(x*100)+'%';
const fs=x=>x==null?'–':(x>=0?'+':'')+x.toFixed(3);
const JN2={'opus46':'Opus 4.6','opus55':'Opus 5.5','sol61':'GPT-6.1 Sol','gpt4o':'GPT-4o'};
const R2SEC=[['home','Round 2'],['scoring','1 Likelihood scoring'],['prestige','2 Prestige prefills'],['calibration','3 Calibration'],['origin','4 Origin-controlled'],['fold','5 Folding'],['prompts','R2 prompts'],['task','Per task']];
function r2nav(sec){return `<div style="margin:6px 0 12px">`+R2SEC.map(([k,n])=>`<a href="#r2/${k}" style="margin-right:10px;font-size:14px;${k===sec?'font-weight:700;border-bottom:2px solid var(--ref)':''}">${n}</a>`).join('')+`</div>`}
async function r2route(parts){
  if(!R2)R2=await J('site-data/r2/index.json');
  const sec=parts[1]||'home';let o=`<h2 style="margin-top:4px">Round 2: other prefills and new directions</h2>`+r2nav(sec);o+=`<div class="warn" style="border-color:#d98a8a;background:#fdecec"><b>Myth results in Round 2 are superseded</b> (invented openers, incl. the origin-controlled mythB-*/mythI-* sets). They were redone with Josh's openers: <a href="#r3">Myths (Josh's prompts)</a>. Translation results are unaffected.</div>`;
  const S=R2.summary;
  if(sec==='home')o+=await r2home();
  else if(sec==='scoring')o+=r2scoring(S);
  else if(sec==='prestige')o+=r2prestige(S);
  else if(sec==='calibration')o+=r2cal(S);
  else if(sec==='origin')o+=r2origin(S);
  else if(sec==='fold')o+=r2fold(S);
  else if(sec==='prompts')o+=r2prompts();
  else if(sec==='task'){$('#app').innerHTML=o+'<div id="r2t"></div>';await r2task(parts[2]);return}
  $('#app').innerHTML=o;
}
async function r2home(){
  let o='';try{const r=await fetch('findings_r2.html');if(r.ok)o+=await r.text()}catch(e){}
  if(R2.spend)o+=`<h3>Round 2 spend</h3><pre>${esc(JSON.stringify(R2.spend,null,1))}</pre>`;
  return o}
function r2prompts(){
  let o=`<p class="mut">Exact text sent to the model, one box per task type, with {SOURCE} {CONTEXT} {CANDS} filled in at run time. Metadata (mode, notes) is shown above each box and is not part of the prompt.</p><h3>Base-judge prefills (round 2)</h3>`;
  for(const p of R2.prefills_r2)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">(${p.mode}) ${esc(p.title)}</span></summary>${pbox(p)}</details>`;
  o+=`<h3>Likelihood-scoring prefixes</h3><p class="mut">Scored text = prefix + " " + candidate. Only the candidate tokens are scored (mean per-token logprob). Translation sections end at "English:"; myth sections end at the opener, and the candidate is the continuation.</p>`;
  for(const p of R2.prefills_score)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">(${p.mode}) ${esc(p.title)}</span></summary>${pbox(p)}</details>`;
  o+=`<h3>Folding prompts</h3>`;
  for(const p of R2.prefills_fold)o+=`<details class="card"><summary><b>${esc(p.id)}</b> <span class="mut">${esc(p.title)}</span></summary>${pbox(p)}</details>`;
  o+=`<p class="mut">Round-1 prefills are on the main <a href="#prompts">Prompts tab</a>.</p>`;
  return o}
function r2scoring(S){
  const a=S.sec1.agg;const names={'SC:raw-neutral':'raw: mean logprob under neutral prefix','SC:pmi-good-vs-neutral':'PMI: good prefixes minus neutral','SC:good-minus-bad':'contrast: good prefixes minus bad prefixes'};
  let o=`<p class="mut"><b>Method.</b> Tinker's OpenAI-style /completions endpoint ignores <code>echo</code> and <code>prompt_logprobs</code> (returns no prompt logprobs), so scoring uses the Tinker SDK's native <code>compute_logprobs</code> (prompt-token logprobs) on the full text prefix + " " + candidate; only candidate tokens count. Score = mean per-token logprob. Each candidate is scored under 1 neutral prefix, 4 "good" prefixes (anthology, prize-winning entry, editor-approved final copy, the published version) and 2 "bad" prefixes (first draft rejected by the editor, unreviewed rough draft). PMI-style contrast = mean(good) − neutral; good-minus-bad = mean(good) − mean(bad). Per task the "winner" under a rule is the highest-scoring candidate. Descriptive only.</p>`;
  o+=`<h3>What each rule picks</h3><div class="scroll"><table><tr><th>Rule</th><th>Set</th><th>Picks longest</th><th>Ornate rank of pick</th><th>Picks base-origin (chance)</th></tr>`;
  for(const [k,v] of Object.entries(a))for(const [s,l] of [['main16','16 tasks (mixed origin)'],['myth16','6 mixed-origin myths'],['originB','all-Qwen-base myths'],['originI','all-Opus-5.5 myths']]){const m=v.metrics[s];o+=`<tr><td>${names[k]}</td><td>${l}</td><td class="num">${pr(m.p_longest)}</td><td class="num">${f2r(m.ornate_rank_pick)}</td><td class="num">${s.startsWith('origin')?'–':pr(m.p_base_origin)+' ('+pr(m.chance_base)+')'}</td></tr>`}
  o+=`</table></div><h3>Agreement of the rule's winner with each instruct judge's top pick</h3><div class="scroll"><table><tr><th>Rule</th><th>Set</th>`+Object.values(JN2).map(x=>`<th>${x}</th>`).join('')+`</tr>`;
  for(const [k,v] of Object.entries(a))for(const [s,l] of [['main16','16 tasks'],['originB','all-Qwen-base'],['originI','all-Opus-5.5']])o+=`<tr><td>${names[k]}</td><td>${l}</td>`+Object.keys(JN2).map(j=>`<td class="num">${pr(v.agree_instruct[j][s])}</td>`).join('')+'</tr>';
  o+=`</table></div><p class="mut">Judges' top pick pools all their prompts and both candidate orders; ties are skipped, so n is smaller than the number of tasks. Chance is roughly 20–25%.</p>`;
  o+=`<h3>How much does each prefix move the score?</h3><p class="mut">Mean (and sd across all 156 candidates) of per-token logprob under the prefix minus under the neutral prefix.</p><div class="scroll"><table><tr><th>Prefix</th><th>mean shift</th><th>sd</th></tr>`;
  for(const [k,v] of Object.entries(S.sec1.per_prefix_mean_shift_vs_neutral))o+=`<tr><td>${k}</td><td class="num">${fs(v.mean)}</td><td class="num">${v.sd.toFixed(3)}</td></tr>`;
  o+=`</table></div><h3>Mean score by origin</h3><div class="scroll"><table><tr><th>Set</th><th>Origin</th><th>n</th><th>neutral mean logprob</th><th>good − neutral</th><th>good − bad</th></tr>`;
  for(const [k,d] of Object.entries(S.sec1.origin_means))for(const [org,v] of Object.entries(d))o+=`<tr><td>${k}</td><td>${org}</td><td class="num">${v.n}</td><td class="num">${f2r(v.neutral_mean)}</td><td class="num">${fs(v.pmi_good_minus_neutral)}</td><td class="num">${fs(v.good_minus_bad)}</td></tr>`;
  o+=`</table></div><h3>Rank correlation of score with candidate length (Spearman, mean over tasks)</h3><pre>${esc(Object.entries(S.sec1.spearman_with_words).map(([k,v])=>k.padEnd(42)+v.toFixed(2)).join('\n'))}</pre>`;
  o+=`<p class="mut">Per-task candidate tables, with the exact scored prefix text, are on the <a href="#r2/task">Per task</a> page.</p>`;return o}
function r2prestige(S){
  let o=`<p class="mut">Five new pick-task prefills (anthology preface, prize citation, reading-group notes, named-style critic persona, two critics then senior editor) plus <b>kex-neutral-cot</b>, a k-example variant whose worked examples use only descriptive notes (no ornate-is-heavy language) and are won by one plain and one rich candidate. All worked examples and notes were written by the assistant (an instruct model); the neutral variant is the attempt to reduce that steering. Exact text on the <a href="#r2/prompts">R2 prompts</a> page.</p>`;
  o+=`<div class="scroll"><table><tr><th>Prefill</th><th>Round</th><th>Order-consistent</th><th>Label mass</th><th>Agrees with instruct judges (mean)</th><th>Picks longest</th><th>Ornate rank of pick</th><th>Myths: share to base-origin</th></tr>`;
  for(const r of S.sec2.slice().sort((a,b)=>a.round-b.round||a.prefill.localeCompare(b.prefill)))o+=`<tr><td>${r.prefill}</td><td>${r.round}</td><td class="num">${pr(r.order_consistency)}</td><td class="num">${f2r(r.label_mass)}</td><td class="num">${pr(r.agree_instruct_mean)}</td><td class="num">${pr(r.all.p_longest)}</td><td class="num">${f2r(r.all.ornate_rank_pick)}</td><td class="num">${pr(r.myth.p_base_origin)}</td></tr>`;
  o+=`</table></div><p class="mut">16 tasks, both candidate orders. Chance for "picks longest" is about 24%; myths have 2 of 4 candidates from Qwen base (50%).</p><h3>Do the worked examples steer ornateness?</h3><div class="scroll"><table><tr><th>k-example variant</th><th>Ornate rank of pick</th><th>Picks longest</th><th>Myths: share to instruct</th></tr>`;
  for(const [k,v] of Object.entries(S.kex_variants))o+=`<tr><td>${k}</td><td class="num">${f2r(v.ornate_rank_pick)}</td><td class="num">${pr(v.p_longest)}</td><td class="num">${pr(v.myth_instruct_share)}</td></tr>`;
  return o+`</table></div>`}
function r2cal(S){
  let o=`<p class="mut"><b>Contextual calibration.</b> For each slot prefill, task and label count, the prompt is rendered with every candidate replaced by "N/A" (source kept) and the next-token letter distribution is read (1 Tinker call). Priors are pooled over tasks with the same prefill, task type and number of candidates. A raw distribution p is calibrated as q ∝ p / prior. Applied post hoc to all slot prefills of round 1 and 2 on the original 16 tasks and on both origin-controlled sets. Calibration was not applied to the note-writing (sampled) prefills. "Order-consistent" = same top pick when the candidate order is reversed; "agrees" = mean top-pick agreement with the 4 instruct judges (order-averaged distribution).</p>`;
  const sets=[['main16','16 original tasks'],['originB','all-Qwen-base set'],['originI','all-Opus-5.5 set']];
  for(const [sk,sl] of sets){o+=`<h3>${sl}</h3><div class="scroll"><table><tr><th>Prefill</th><th>P(letter A) raw → cal</th><th>Order-consistent raw → cal</th><th>Agrees w/ instruct raw → cal</th><th>Label mass</th></tr>`;
    for(const r of S.calibration){const d=r[sk];if(!d)continue;o+=`<tr><td>${r.prefill}</td><td class="num">${pr(d.posA_raw)} → ${pr(d.posA_cal)}</td><td class="num">${pr(d.oc_single_raw)} → ${pr(d.oc_single_cal)}</td><td class="num">${pr(d.agree_inst_raw)} → ${pr(d.agree_inst_cal)}</td><td class="num">${f2r(d.label_mass)}</td></tr>`}
    o+=`</table></div>`}
  o+=`<p class="mut">Where the label mass is low, the letter distribution is a small slice of the model's probability, and dividing by the prior can over-correct (e.g. kex-middle-label pushes P(A) to about 0–5%).</p>`;
  const pk=Object.entries(S.priors).filter(([k])=>k.endsWith('|myth|4')||k.endsWith('|translation|5'));
  o+=`<h3>Estimated letter priors (content-free candidates)</h3><div class="scroll"><table><tr><th>prefill | type | n labels</th><th>A</th><th>B</th><th>C</th><th>D</th><th>E</th></tr>`;
  for(const [k,v] of pk)o+=`<tr><td>${k}</td>`+['A','B','C','D','E'].map(l=>`<td class="num">${v[l]!=null?pr(v[l]):'–'}</td>`).join('')+'</tr>';
  return o+`</table></div>`}
function r2origin(S){
  const s4=S.sec4;let o=`<p class="mut"><b>Origin removed.</b> Two new myth sets over the same 6 openers: <b>all-Qwen-base</b> (4 Qwen base continuations at temperatures 0.6, 0.8, 1.0, 1.2, mechanically filtered as in round 1) and <b>all-Opus-5.5</b> (4 samples at temperature 1.0). Judges cannot use origin. Judges: all 17 base prefills (11 from round 1 and 6 from round 2), the same prefills calibrated, Opus 4.6, Opus 5.5, GPT-6.1 Sol and GPT-4o (3 plain prompts × 2 orders each, pooled), and the three likelihood rules. Agreement = share of tasks where two judges name the same unique top pick (ties skipped); chance is about 25%. Only 6 tasks per set: treat all numbers as indicative.</p>`;
  const rows=[['instruct_vs_instruct','instruct vs instruct'],['base_prefill_vs_instruct','base prefills vs instruct'],['base_calibrated_vs_instruct','calibrated base prefills vs instruct'],['base_vs_base','base prefill vs base prefill'],['scoring_vs_instruct','likelihood rules vs instruct'],['scoring_vs_base','likelihood rules vs base prefills']];
  o+=`<div class="scroll"><table><tr><th>Mean pairwise agreement</th><th>6 mixed-origin myths (round 1 set)</th><th>all-Qwen-base</th><th>all-Opus-5.5</th></tr>`;
  for(const [k,l] of rows)o+=`<tr><td>${l}</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s][k])}</td>`).join('')+'</tr>';
  o+=`<tr><td>4 instruct judges unanimous (tasks where all have a unique pick)</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s].instruct_unanimous[0])} (n=${s4[s].instruct_unanimous[1]})</td>`).join('')+`</tr><tr><td>order-consistency, instruct judge×prompt</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s].order_consistency.instruct_judge_prompt)}</td>`).join('')+`</tr><tr><td>order-consistency, base prefills</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s].order_consistency.base_prefills)}</td>`).join('')+`</tr><tr><td>order-consistency, calibrated base</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s].order_consistency.base_calibrated)}</td>`).join('')+`</tr></table></div>`;
  o+=`<h3>Agreement with the instruct judges, per base prefill</h3><div class="scroll"><table><tr><th>Prefill</th><th>mixed-origin</th><th>all-Qwen-base</th><th>all-Opus-5.5</th></tr>`;
  for(const p of Object.keys(s4.all_Qwen_base.per_base_prefill))o+=`<tr><td>${p}</td>`+['mixed_myths_16','all_Qwen_base','all_Opus55'].map(s=>`<td class="num">${pr(s4[s].per_base_prefill[p])}</td>`).join('')+'</tr>';
  o+=`</table></div><h3>Which temperature does each judge group favor? (all-Qwen-base set)</h3><div class="scroll"><table><tr><th>Group</th><th>0.6</th><th>0.8</th><th>1.0</th><th>1.2</th></tr>`;
  for(const [g,d] of Object.entries(s4.setB_mass_by_temperature))o+=`<tr><td>${g}</td>`+['0.6','0.8','1.0','1.2'].map(t=>`<td class="num">${pr(d[t]||0)}</td>`).join('')+'</tr>';
  o+=`</table></div><p class="mut">Share of the group's preference mass per candidate temperature (each task has exactly one candidate per temperature; 25% would be even).</p><h3>Instruct judges on the origin-controlled sets</h3><div class="scroll"><table><tr><th>Set</th><th>Judge</th><th>Picks longest</th><th>Ornate rank of pick</th></tr>`;
  for(const [sk,sl] of [['all_Qwen_base','all-Qwen-base'],['all_Opus55','all-Opus-5.5']])for(const j of ['opus46','opus55','sol61','gpt4o']){const m=s4.metrics_units[sk]['J:'+j];o+=`<tr><td>${sl}</td><td>${JN2[j]}</td><td class="num">${pr(m.p_longest)}</td><td class="num">${f2r(m.ornate_rank_pick)}</td></tr>`}
  o+=`</table></div><h3>Base prefills on the origin-controlled sets (mean over the 17 prefills)</h3><div class="scroll"><table><tr><th>Set</th><th>Picks longest</th><th>Ornate rank of pick</th></tr>`;
  for(const [sk,sl] of [['mixed_myths_16','6 mixed-origin myths'],['all_Qwen_base','all-Qwen-base'],['all_Opus55','all-Opus-5.5']]){const m=s4.base_prefill_metrics[sk];o+=`<tr><td>${sl}</td><td class="num">${pr(m.p_longest)}</td><td class="num">${f2r(m.ornate_rank_pick)}</td></tr>`}
  return o+`</table></div><p class="mut">Candidates, every judge's prompt and answers per task are on the <a href="#r2/task">Per task</a> page (tasks mythB-1…6 and mythI-1…6).</p>`}
function r2fold(S){
  const s=S.sec5;let o=`<p class="mut"><b>Folding.</b> Instead of picking, the model writes a combined version. Qwen base got two zero-shot prefills (editor's final version; revision-session merged version), 4 samples each at temperature 0.7; Opus 5.5 and GPT-6.1 Sol got a plain request to combine (1 output each). No correctness judgement: outputs are on the <a href="#r2/task">Per task</a> page. Below is only descriptive: mean length and which candidate's wording each output overlaps with most (word overlap, 1-grams for translations, 3-grams for myths).</p><div class="scroll"><table><tr><th>Type · fold prompt · model</th><th>mean words</th><th>nearest candidate origin (share of outputs)</th></tr>`;
  for(const [k,d] of Object.entries(s.nearest_origin))o+=`<tr><td>${k.replace(/\|/g,' · ')}</td><td class="num">${f2r(s.mean_words[k])}</td><td>${Object.entries(d).sort((a,b)=>b[1]-a[1]).map(([x,y])=>x+' '+pr(y)).join(', ')}</td></tr>`;
  return o+`</table></div><p class="mut">Mean candidate length for reference: translations ${f2r(s.mean_candidate_words.translation)} words, myths ${f2r(s.mean_candidate_words.myth)} words.</p>`}
async function r2task(id){
  let o=`<select id="r2sel">`+R2.tasks.map(t=>`<option value="${t.id}" ${t.id===id?'selected':''}>${t.type!=='translation'?'[SUPERSEDED: invalid opener] ':''}${t.id} · ${t.set} · ${esc(t.title)}</option>`).join('')+`</select>`;
  if(!id){$('#r2t').innerHTML=o+'<p class="mut">Pick a task.</p>';$('#r2sel').onchange=e=>location.hash='#r2/task/'+e.target.value;return}
  const D=await J(`site-data/r2/task/${id}.json`);const t=D.task;
  o+=`<h3>${t.id} <span class="mut">(${t.set||'mixed-origin'})</span></h3><div class="card"><b>${t.type==='translation'?'Korean source':'Opener'}</b><br>${esc(t.display_source)}${t.context?`<br><span class="mut">Where it appears: ${esc(t.context)}</span>`:''}</div>`;
  t.candidates.forEach((c,i)=>{const k=c.kinds.includes('base')?'base':c.kinds.includes('base-refine')?'base-refine':'instruct';
    o+=`<div class="cand ${k}"><b>C${i+1}</b> ${c.kinds.map(x=>`<span class="tag ${x}">${x}</span>`).join('')}<span class="mut">${esc(c.origins.join(' = '))} · ${c.feats.words} words · ornate rank ${c.ornate.toFixed(2)}</span><br>${esc(c.text).replace(/\n/g,'<br>')}</div>`});
  // scoring
  o+=`<h3>1 · Likelihood scoring</h3><p class="mut">Mean per-token logprob of the candidate under each prefix. Winners per rule are in bold.</p>`;
  const sc=D.scoring;const pf=Object.keys(sc[0].per_prefix_mean);
  const win=k=>sc.reduce((a,b)=>b[k]>a[k]?b:a).cid;const w1=win('neutral_mean'),w2=win('pmi_good_minus_neutral'),w3=win('good_minus_bad');
  o+=`<div class="scroll"><table><tr><th>Cand</th><th>tokens</th>`+pf.map(p=>`<th>${p}</th>`).join('')+`<th>good−neutral</th><th>good−bad</th></tr>`;
  sc.forEach(r=>{const i=t.candidates.findIndex(c=>c.cid===r.cid)+1;o+=`<tr><td>C${i}</td><td class="num">${r.n_tokens}</td>`+pf.map(p=>`<td class="num">${p==='neutral'&&r.cid===w1?'<b>'+r.per_prefix_mean[p].toFixed(3)+'</b>':r.per_prefix_mean[p].toFixed(3)}</td>`).join('')+`<td class="num">${r.cid===w2?'<b>':''}${fs(r.pmi_good_minus_neutral)}${r.cid===w2?'</b>':''}</td><td class="num">${r.cid===w3?'<b>':''}${fs(r.good_minus_bad)}${r.cid===w3?'</b>':''}</td></tr>`});
  o+=`</table></div>`;
  const ex=R2.prefix_examples[id];if(ex)o+=`<details><summary class="mut">exact scored prefixes for this task</summary>`+Object.entries(ex).map(([k,v])=>`<div class="mut">${k}</div><pre>${esc(v)}</pre>`).join('')+`</details>`;
  // judges grid
  o+=`<h3>2–4 · Letter judges</h3>`;
  if(D.base.length){
    o+=`<p class="mut">Base prefills (order-averaged probability per candidate; "cal" = after contextual calibration) and, on origin-controlled tasks, instruct judges (share of their 6 answers: 3 prompts × 2 orders).</p><div class="scroll"><table><tr><th>Judge</th>`+t.candidates.map((c,i)=>`<th>C${i+1}</th>`).join('')+`</tr>`;
    const by={};for(const r of D.base){const k=r.prefill;(by[k]??=[]).push(r)}
    for(const [k,rs] of Object.entries(by)){const d={},dc={};let nc=0;for(const r of rs){if(!r.dist_norm)continue;for(const [l,p] of Object.entries(r.dist_norm)){const c=r.label_to_short[l];d[c]=(d[c]||0)+(p||0)/2}
        if(r.cal_dist){nc++;for(const [l,p] of Object.entries(r.cal_dist)){const c=r.label_to_short[l];dc[c]=(dc[c]||0)+p/2}}}
      o+=`<tr><td class="cell">${k}</td>`+t.candidates.map((c,i)=>`<td class="cell">${bar(d[i+1]||0,36)}</td>`).join('')+'</tr>';
      if(nc)o+=`<tr><td class="cell mut">${k} (cal)</td>`+t.candidates.map((c,i)=>`<td class="cell">${bar(dc[i+1]||0,36)}</td>`).join('')+'</tr>'}
    const ij={};for(const r of D.instruct){if(!r.verdict)continue;(ij[r.judge]??={})[r.label_to_short[r.verdict]]=((ij[r.judge]??={})[r.label_to_short[r.verdict]]||0)+1}
    for(const [j,d] of Object.entries(ij)){const n=Object.values(d).reduce((a,b)=>a+b,0);o+=`<tr><td class="cell">${JN2[j]}</td>`+t.candidates.map((c,i)=>`<td class="cell">${bar((d[i+1]||0)/n,36)}</td>`).join('')+'</tr>'}
    o+=`</table></div>`;
    o+=`<h3>Full prompts and answers</h3>`;
    const groups={};for(const r of D.base)(groups['Qwen base · '+r.prefill]??=[]).push(r);for(const r of D.instruct)(groups[JN2[r.judge]+' · '+r.prefill]??=[]).push(r);
    for(const [k,rs] of Object.entries(groups)){rs.sort((a,b)=>a.order-b.order);o+=`<details class="card"><summary><b>${esc(k)}</b></summary>`;
      for(const r of rs){o+=`<h3>Order ${r.order+1} <span class="mut">(${r.labels.map(l=>l+'=C'+r.label_to_short[l]).join(', ')})</span></h3><details><summary class="mut">exact prompt sent</summary><pre>${esc(r.prompt)}</pre></details>`;
        if(r.samples){o+=`<div>${r.mode==='slot'?'Letter distribution':'Mean letter distribution at the verdict slot'}: `+r.labels.map(l=>`${l}(C${r.label_to_short[l]}) ${pr(r.dist_norm?.[l])}`).join(' · ')+(r.cal_dist?`<br>calibrated: `+r.labels.map(l=>`${l}(C${r.label_to_short[l]}) ${pr(r.cal_dist[l])}`).join(' · '):'')+` <span class="mut">· label mass ${f2r(r.label_mass)}</span></div><details><summary class="mut">${r.samples.length} sampled continuations</summary>`+r.samples.map((s,i)=>`<div class="mut">sample ${i+1} → verdict ${s.verdict?s.verdict+' (C'+r.label_to_short[s.verdict]+')':'none'}</div><pre>${esc(s.text)}</pre>`).join('')+`</details>`}
        else o+=`<div>Verdict: <b>${r.verdict?r.verdict+' (C'+r.label_to_short[r.verdict]+')':'none'}</b></div><pre>${esc(r.text||'')}</pre>`}
      o+=`</details>`}
  }
  // fold
  o+=`<h3>5 · Folded versions (outputs only)</h3>`;
  for(const r of D.fold){o+=`<details class="card"><summary><b>${esc(r.fold)}</b> · ${r.who==='qwen-base'?'Qwen base':JN2[r.who]}</summary><details><summary class="mut">exact prompt</summary><pre>${esc(r.prompt)}</pre></details>`+r.outputs.map((x,i)=>`<div class="mut">output ${i+1} · nearest candidate C${t.candidates.findIndex(c=>c.cid===x.nearest_cid)+1} (overlap ${x.nearest_sim.toFixed(2)})</div><pre>${esc(x.text)}</pre>`).join('')+`</details>`}
  $('#r2t').innerHTML=o;$('#r2sel').onchange=e=>location.hash='#r2/task/'+e.target.value;
}
