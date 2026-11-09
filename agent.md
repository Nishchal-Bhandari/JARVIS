# agent.md — Instructions for AI coding agents working on J.A.R.V.I.S.

Read this file first, every session. Then read `specsheet.md` (what to build), `design_system.md` (how it looks) and `skillbuild.md` (build order and prompts). If they conflict: **specsheet.md wins on behavior, design_system.md wins on visuals, this file wins on process.**

---

## 1. Project in one paragraph

J.A.R.V.I.S. is a hackathon prototype (NITSHACKS 9.0, PS1) that ingests logs, alerts and metrics from an API, uploaded files and a live simulator, correlates them into incidents, identifies the most likely root cause with an evidence-based confidence score, shows impact and a propagation timeline, recommends fixes and generates an incident report. The headline scenario is a payment platform where login failures, slow APIs and failed payments all trace back to a database connection pool exhaustion. **The UI is built on the v0 community template "Dashboard – M.O.N.K.Y" (Next.js + shadcn/ui, dark-first): adapt it, do not rebuild it.** `master_prompt.md` is the entry prompt that sequences all work.

**Timebox: one working day.** Favor a complete, polished vertical slice over breadth. The demo scenario must work every single time.

---

## 2. Repository layout

```
jarvis/
  agent.md  specsheet.md  design_system.md  skillbuild.md  master_prompt.md  README.md
  docker-compose.yml  Makefile  .env.example
  docs/
    tokens-audit.md           # written in Phase 0b from the template's code
  backend/
    pyproject.toml  app/ (see specsheet §4)  tests/
  frontend/                   # exported from v0 template "Dashboard – M.O.N.K.Y"
    package.json  next.config.mjs  tailwind.config.ts  components.json  .env.local
    app/
      layout.tsx              # template shell (sidebar + top bar): keep, adapt
      globals.css             # template tokens + semantic status layer (design_system §3)
      page.tsx                # Overview
      incidents/[id]/page.tsx # Incident detail
      sources/page.tsx
      topology/page.tsx
    components/
      ui/                     # shadcn primitives from the template: reuse
      shell/                  # template sidebar / top bar, adapted
      jarvis/                 # IncidentRow, SeverityPill, RootCausePanel, ConfidenceMeter,
                              # ServiceNode, CausalGraph, Timeline, ImpactCard,
                              # RecommendationItem, EventTable, KpiStrip, SourceCard,
                              # ReportView, CopilotPanel
    lib/                      # api.ts (typed client), ws.ts, format.ts, types.ts
    store/                    # stream.ts (zustand live stream store)
  sample_data/
    payment_outage.jsonl  payment_outage.log  payment_outage.csv
```

---

## 3. Commands

```bash
# Setup
make setup            # create venv, pip install -e backend, npm ci in frontend
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local

# Develop
make dev              # api on :8000 (reload) + web on :3000
make api              # backend only:  uvicorn app.main:app --reload --port 8000
make web              # frontend only: cd frontend && npm run dev

# Quality gates (run before every commit)
make test             # pytest -q  &&  (cd frontend && npm run test -- --run)
make lint             # ruff check backend && ruff format --check backend && (cd frontend && npm run lint && npm run typecheck)
(cd frontend && npm run build)    # must pass after any template cleanup or dependency change

# Demo
make seed             # generate sample_data/ files from simulator scenarios
docker compose up --build
```

`.env.example` (backend)
```
DATABASE_URL=sqlite:///./jarvis.db
CORRELATION_THRESHOLD=0.45
WINDOW_MINUTES=10
TICK_SECONDS=2
SEED=42
CORS_ORIGINS=http://localhost:3000
ANTHROPIC_API_KEY=          # optional; app must work without it
LLM_MODEL=                  # set to a current Anthropic model ID
```

`frontend/.env.local.example`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/stream
```

---

## 4. Operating rules

### Always
1. **Work in vertical slices.** Each task ends with something runnable and a passing test, not half-finished layers.
2. **Write the test for core logic first or alongside it** (normalizer, anomaly, correlation, root cause, impact, severity). UI components need at least a render test for the hero components.
3. **Keep the engine pure.** `core/*.py` modules take data in and return data out: no database, no network, no global state. Only `engine.py` and `api/*` touch the DB. This makes everything unit-testable.
4. **Every score must be explainable.** Anything that outputs a number (confidence, severity) must also output the reasons in plain English.
5. **Degrade gracefully.** No LLM key → template report. Unknown service → add as "unmapped" node. Bad log line → count and skip. Never crash ingestion.
6. **Type everything.** Pydantic models on the backend; TypeScript types in `frontend/src/lib/types.ts` mirroring `schemas.py`. When you change one, change the other in the same commit.
7. **Template first, then `design_system.md`.** Reuse the M.O.N.K.Y shell, tokens, shadcn primitives and chat component. Audit its tokens before styling (design_system §2). No hard-coded hex values in components; use Tailwind token classes. Match the template's look; do not restyle it.
8. **Deterministic demos.** Use `SEED` for the simulator; never use `random` without the seeded generator.
9. **Commit small, with clear messages**: `feat(correlation): union-find clustering`, `fix(ui): graph edge arrow direction`, `test(rootcause): S1 scenario`.
10. **After each task, report**: what changed, how to run or verify it, what's next.

### Never
- Never invent data in the UI. Numbers shown come from the API.
- Never send raw logs to the LLM; send the structured incident summary only, and instruct it to use only supplied facts.
- Never commit secrets, `.env`, or `jarvis.db`.
- Never add a dependency without a one-line justification in the PR/commit message. Prefer what is already in the stack.
- Never skip the failing test by weakening it. If a test is wrong, explain why and fix it.
- Never refactor unrelated code during a feature task.
- Never use localStorage-only state for anything the backend should own.
- Never rebuild something the template already provides (sidebar, top bar, cards, table, tabs, chat shell). Adapt it.
- Never leave template demo pages, sample data or placeholder branding in the final build.
- Don't gold-plate: no auth, no multi-tenancy, no ML training (see specsheet §17).

---

## 5. Coding conventions

### Python (backend)
- Python 3.11, type hints everywhere, `ruff` for lint and format (line length 100).
- Dataclasses or Pydantic models for domain objects; functions under ~40 lines; docstrings stating inputs/outputs and the *why* for scoring formulas.
- Weights and thresholds live in `config.py` (or a `WEIGHTS` constant) with names matching the spec: `W_TIME`, `W_TOPO`, `W_CTX`, `W_TEXT`, `W_EARLY`, `W_UPSTREAM`, `W_SIG`, `W_SEV`.
- Async only where needed (FastAPI handlers, simulator runner, WebSocket). Engine tick is sync and CPU-bound; run it via `run_in_executor` or a background task.
- Timestamps: timezone-aware UTC `datetime` internally; ISO-8601 with `Z` at API boundaries.
- Errors: raise `HTTPException` with the `{error:{code,message}}` envelope via a shared handler.

### TypeScript (frontend)
- Next.js App Router, TypeScript strict mode. Functional components, hooks, no classes.
- Add `"use client"` only where needed (live data, interactivity). Load React Flow and the timeline via `next/dynamic` with `ssr: false`.
- API and WebSocket URLs come from `NEXT_PUBLIC_*` env vars; never hard-code `localhost` in components.
- Data fetching via TanStack Query; live updates via a single WebSocket hook that writes to the zustand store and invalidates relevant queries.
- One component per file, named export, props typed with an interface. Co-locate tests (`Component.test.tsx`).
- Styling with Tailwind token classes only; no inline hex; respect `prefers-reduced-motion`.
- Accessibility is part of "done": focus ring, aria labels, text alongside color.

### Naming
- Services: kebab-case (`payment-service`). Signatures: snake_case (`db_pool_exhausted`). Endpoints: plural nouns. React components: PascalCase.

---

## 6. Task protocol (how to take a task)

1. **Restate** the task and the spec sections it touches (e.g. "Implement correlation — specsheet §6").
2. **Plan** in 3–6 bullets: files to create/change, tests to add.
3. **Implement** the smallest working slice.
4. **Verify**: run `make test` and `make lint`; run the app and check the behavior by hand for UI work.
5. **Report** using this template:

```
Done: <one sentence>
Changed: <files>
Verified: <commands run + observed result>
Notes/risks: <anything the human should know>
Next: <proposed next task from skillbuild.md>
```

If the spec is ambiguous, make the most reasonable choice, note it under "Notes/risks", and keep going. Ask the human only when blocked or when a decision would be expensive to reverse.

---

## 7. Definition of done (per task)

- [ ] Behavior matches `specsheet.md` (cite section)
- [ ] Unit tests written and passing; no previously passing tests broken
- [ ] Lint and typecheck clean
- [ ] Types synchronized between backend and frontend
- [ ] UI follows `design_system.md` (tokens, states: loading/empty/error)
- [ ] Works with no LLM key and with the seeded simulator
- [ ] README or docs updated if a command or endpoint changed

---

## 8. Key algorithms: quick reference (full detail in specsheet)

```
correlation weight:  w = .40·e^(-|Δt|/120) + .35·1/(1+hops) + .15·shared_ctx + .10·tfidf_cos
link if w ≥ 0.45  →  union-find  →  incident if ≥3 events across ≥2 services

root cause score:    .35·earliness + .35·upstreamness + .20·signature + .10·severity
confidence:          softmax(score / 0.15);  evidence[] is mandatory

severity:            P1 if critical-path hit and (≥4 services or ≥50 users); P2 if critical-path hit;
                     P3 if ≥2 services; else P4

dependency edge:     A → B means A depends on B; failures propagate B → A
```

Golden test (must always pass): scenario `db_pool_exhaustion` with `SEED=42` produces exactly one main incident with root cause `postgres-primary`, confidence ≥ 0.70, ≥ 5 affected services, ≥ 30 users, and a separate low-severity `cdn` cluster.

---

## 8b. Debugging checklist

- Incident not forming? Print pairwise weights for the first 20 events; check topology hops and timestamp parsing (timezone!).
- Everything merging into one incident? Raise `CORRELATION_THRESHOLD` or confirm the CDN events are 2+ hops from the DB cluster.
- Wrong root cause? Print the four factor scores per service; most often the dependency edge direction is reversed.
- WebSocket silent? Check CORS (`CORS_ORIGINS` includes `http://localhost:3000`), that the hook runs in a client component, and that `engine.tick()` publishes to the broadcast hub after persisting.
- React Flow hydration/SSR error? Load the graph with `dynamic(() => import(...), { ssr: false })` and give its container an explicit height.
- Template styles look wrong after edits? Re-check `docs/tokens-audit.md`; you probably overrode a template token instead of reusing it.
- Graph layout messy? Use layered layout by `tier` from topology (x = tier, y = index) instead of force layout.

---

## 9. Prompts you may be given

When the human says one of these, do the following:
- **"Next task"** → take the next unchecked item in `skillbuild.md` and follow §6.
- **"Status"** → list completed phases, current phase, failing tests, and the riskiest open item.
- **"Demo check"** → run `make seed`, start the stack, run the golden test, walk the demo script (specsheet §16), and report any step that fails.
- **"Audit template"** → read the template code per design_system §2 and write/refresh `docs/tokens-audit.md`, listing reusable components and anything to remove.
- **"Cut scope"** → apply the cut list in `skillbuild.md` §9 in order and summarize what was removed.
