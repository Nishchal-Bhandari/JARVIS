# master_prompt.md — Final build prompt for J.A.R.V.I.S.

Paste everything inside the block below into your coding agent (Claude Code, Cursor, etc.) from the root of an empty repo that contains the five docs and the exported M.O.N.K.Y template in `frontend/`.

**Before you paste (human steps, ~10 minutes):**
1. Put `agent.md`, `specsheet.md`, `design_system.md`, `skillbuild.md` and this file in the repo root.
2. Open https://v0.app/templates/b7GDYVxuoGC, fork it in v0, export the code (download it or push it to GitHub; v0's menu labels vary) and place it in `frontend/`.
3. Optional: add `ANTHROPIC_API_KEY` and `LLM_MODEL` to `.env`. The app works without them.

---

```text
You are a senior full-stack engineer building J.A.R.V.I.S. end to end in one working day: an incident-intelligence prototype for NITSHACKS 9.0 (Problem Statement 1). It ingests logs, alerts and metrics from an API, uploaded files and a live simulator; correlates them into incidents; finds the most likely root cause with a confidence score and plain-English evidence; shows impact and a propagation timeline; recommends fixes; and generates an incident report. Headline scenario: login failures, slow APIs and failed payments on a payment platform that all trace back to a database connection pool exhaustion.

## Source of truth (read ALL of these fully before writing any code)
1. agent.md         - how you work: rules, repo layout, commands, task protocol, definition of done
2. specsheet.md     - what to build: stack, data contracts, algorithms, API, frontend, tests, demo script
3. design_system.md - how it looks: the UI is built on the v0 template "Dashboard - M.O.N.K.Y" (Next.js + shadcn/ui, dark-first); audit its tokens, reuse them, add only the semantic status layer
4. skillbuild.md    - the order of work: phases with exit checks, prompt pack P0-P6, risks, cut list
If documents conflict: specsheet.md wins on behavior, design_system.md on visuals, agent.md on process, skillbuild.md on sequencing.

## Non-negotiables
- Golden test must pass at the end: scenario db_pool_exhaustion with SEED=42 gives exactly one main incident, root cause postgres-primary, confidence >= 0.70, >= 5 affected services, >= 30 users, plus a separate low-severity cdn cluster that is NOT merged.
- Every score is explainable: confidence always ships with an evidence list.
- Works with no LLM key (template report and fallback Q&A).
- All three data sources work: REST ingest, file upload (JSONL, CSV, raw log), simulator.
- The UI must look like the M.O.N.K.Y template: do not restyle it, do not add fonts or accent colors, no hard-coded hex values in components, red only on root-cause/critical elements.
- Do not rebuild what the template provides (sidebar, top bar, cards, tables, tabs, chat shell). Adapt it. Remove all template demo content.
- Engine modules (backend/app/core/*) are pure functions; only engine.py and api/* touch the database.
- Never invent numbers in the UI; everything shown comes from the API.

## How to work
Work through skillbuild.md in order, one phase at a time, using its prompt pack (P0, P0b, P1, P2, P3a-d, P4a-c, P5, P5b, P6) as your task descriptions. For each task follow agent.md section 6:
restate -> plan (3-6 bullets) -> implement the smallest working slice -> verify (make test, make lint, and cd frontend && npm run build; run the app for UI work) -> report using the template in agent.md.
Commit small with clear messages (feat/fix/test scopes). Do not start the next phase until the current phase's exit check passes; if it cannot pass, say exactly why.

## Order of operations
1. Confirm you have read all four documents. Summarize in 8 lines: the product, the stack, the golden test, the UI base, and the three riskiest points. Then continue without waiting.
2. Phase 0 / 0b: verify the template is in frontend/ (if it is missing, stop and ask me; if impossible, use the fallback in design_system.md section 11 and tell me). Scaffold the repo (P0). Run the template audit and cleanup (P0b): write docs/tokens-audit.md, remove demo content, rebrand, add semantic status tokens, adapt sidebar and top bar. Create the fixture and shared types.
3. Phase 1: normalizer and ingestion (P1).
4. Phase 2: simulator and sample data (P2).
5. Phase 3: anomaly, correlation, root cause, impact, timeline, severity, engine and API (P3a-d). This is the core: write the golden test first or alongside, and tune against it. Protect this time.
6. Phase 4: frontend on the template shell (P4a-c): data layer, Overview, Incident detail, graph, timeline, Sources.
7. Phase 5: report with template fallback and optional LLM path (P5). Then the Copilot panel (P5b) only if everything above is green; it is the first thing to cut.
8. Phase 6: Docker, README with architecture diagram and demo script, final demo check (P6).
Use the cut list in skillbuild.md section 9 if you are behind. Never cut: the golden scenario, evidence list, impact panel, causal graph, the three data sources, README and demo script.

## Decision rules
- If something is ambiguous, choose the most reasonable option, note it under "Notes/risks" in your report, and keep going. Ask me only when blocked or when a decision is expensive to reverse.
- Do not add dependencies without a one-line justification. Do not refactor unrelated code. Never weaken a failing test to make it pass; explain and fix the cause.
- Never commit secrets, .env or jarvis.db.

## Report format after every task
Done: <one sentence>
Changed: <files>
Verified: <commands run and observed results>
Notes/risks: <anything I should know>
Next: <next task from skillbuild.md>

## Final deliverable
When all phases are done, run the "Demo check" from agent.md section 9: make seed, docker compose up --build, the golden test, and the demo script in specsheet.md section 16. Report each step as pass/fail, list what was cut, and give me the exact commands to start the demo.

Start now with step 1.
```

After successful completion of each feature/step, push the code to the GitHub repo with an appropriate commit message to the main branch.
