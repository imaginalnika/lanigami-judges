# Lanigami judge test (static site)
Open index.html through any static server (`python3 -m http.server`), or publish the folder.
- prompts/base/*.txt  one file per base-judge prefill (header, then `=====`, then `@@translation` / `@@myth` sections with {SOURCE} {CONTEXT} {CANDS}). Add a file there and rerun tools/run_base.py (resumes, only runs new prefills), tools/analyze.py, tools/build_site_data.py.
- prompts/instruct/*.txt  instruct-judge prompts.
- data/  tasks, raw results (base_results.jsonl, instruct_results.jsonl), ledger.jsonl (every API call's token/cost), summary.json.
- site-data/  what the page loads.
Keys are read from environment variables (TINKER_API_KEY, OPENROUTER_API_KEY) and are never stored here.
