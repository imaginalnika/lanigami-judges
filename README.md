# Lanigami judge test (static site)
Open index.html through any static server (`python3 -m http.server`), or publish the folder.
- prompts/base/*.txt  one file per base-judge prefill (body only: the exact text sent, with `@@translation` / `@@myth` lines marking the two templates and {SOURCE} {CONTEXT} {CANDS} placeholders; each file's id/title/mode/notes are in prompts/meta.json). Note: in this published copy the header was moved out of the .txt files, so tools/run_base.py expects the unstripped originals. Add a file there and rerun tools/run_base.py (resumes, only runs new prefills), tools/analyze.py, tools/build_site_data.py.
- prompts/instruct/*.txt  instruct-judge prompts.
- data/  tasks, raw results (base_results.jsonl, instruct_results.jsonl), ledger.jsonl (every API call's token/cost), summary.json.
- site-data/  what the page loads.
Keys are read from environment variables (TINKER_API_KEY, OPENROUTER_API_KEY) and are never stored here.

- r3.js / findings_r3.html / data/r3 / prompts/base-r3: myths redone with Josh's original openers (tab `#r3`). Old myth tasks are kept as 'superseded: invalid openers'.
