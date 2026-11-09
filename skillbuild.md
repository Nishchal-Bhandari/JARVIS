# skillbuild.md — Skills, build order and execution playbook for J.A.R.V.I.S.

Goal: ship a working, demo-ready prototype **in one day** (assume ~12 working hours, 2–4 people, with an AI coding agent following `agent.md`).

Companion files: `specsheet.md` (what), `design_system.md` (look), `agent.md` (process), `master_prompt.md` (the single prompt that drives the agent through this plan).

**Revision 2:** the UI is built on the v0 template **Dashboard – M.O.N.K.Y** (https://v0.app/templates/b7GDYVxuoGC) using Next.js + shadcn/ui. Template adoption is now part of Phase 0.

---

## 1. Skills needed

| Skill | Used for | Depth needed |
|---|---|---|
| Python and FastAPI | API, WebSocket, background tasks | Intermediate |
| Data modeling (SQLAlchemy/SQLite) | Events, incidents, relations | Basic |
| Graph reasoning (NetworkX) | Dependency closure, hops, blast radius | Basic–intermediate |
| Applied statistics | Robust z-score (median/MAD), softmax confidence | Basic |
| Text similarity (TF-IDF) | Message similarity in correlation | Basic (use scikit-learn) |
| Next.js (App Router) + TypeScript + shadcn/ui | Dashboard, routing, state, adapting the M.O.N.K.Y template | Intermediate |
| Data visualization (React Flow, Recharts) | Causal graph, timeline | Intermediate |
| UI/UX with design tokens | Following `design_system.md` | Basic–intermediate |
| Reading and reskinning an existing codebase | Token audit, removing demo content, mapping template components | Intermediate |
| Prompt engineering | LLM-written incident report with fact-grounding | Basic |
| Testing (pytest, Vitest) | Golden scenario tests | Basic |
| Docker/Compose | One-command demo | Basic |
| Storytelling and demo craft | 3-minute pitch | Important |

### Team split (pick the row matching your headcount)
| Team size | Split |
|---|---|
| 2 | **A:** backend engine (normalizer → correlation → root cause → API). **B:** frontend (all screens) + simulator + demo. |
| 3 | **A:** engine and API. **B:** frontend and graph/timeline. **C:** simulator, sample data, rulebook, tests, report/LLM, README, pitch. |
| 4 | Above plus **D:** design-system implementation, polish, accessibility, demo video. |

**Interface contract first (first 30 minutes, everyone):** agree on the canonical event schema and the `/incidents/{id}` response JSON from `specsheet.md` §5, §7, §11. Frontend builds against a hand-written fixture until the engine is ready.

---

## 2. Phase plan (12-hour schedule)

Each phase has an exit check. Do not start the next phase until the check passes. If you fall behind, jump to §9 (cut list).

### Phase 0: Setup, contracts and template import (0:00–1:00)
- [ ] **Human step:** open https://v0.app/templates/b7GDYVxuoGC, fork it in v0, export the code (download it or push it to GitHub; v0's menu labels vary) and place it in `frontend/`. An agent cannot do this step.
- [ ] Repo layout per `agent.md` §2; `make setup`, `make dev`, `make test` run (even if empty)
- [ ] FastAPI `/health`, CORS for `http://localhost:3000`
- [ ] **Phase 0b: template audit and cleanup** (design_system §2, §11): write `docs/tokens-audit.md`, remove demo pages and sample data, rebrand to J.A.R.V.I.S., add the semantic status tokens, adapt sidebar and top bar; `npm run build` passes
- [ ] `schemas.py` and `types.ts` for Event, Incident, RootCause, Impact, TimelineStage
- [ ] Write `fixtures/incident_s1.json` (hand-made full incident detail) for the frontend
- **Exit check:** both servers start; the Next.js app shows the J.A.R.V.I.S. shell (sidebar + top bar) and the Overview page renders a fixture incident; `docs/tokens-audit.md` exists.

### Phase 1: Ingestion and storage (1:00–2:15)
- [ ] `models.py`, `db.py`; `topology.json` loaded into DB on startup
- [ ] `normalizer.py`: JSONL, CSV, raw-log regex; severity inference; unknown service handling
- [ ] `POST /events`, `POST /ingest/upload`, `GET /events` with filters
- [ ] Tests: each format plus bad lines
- **Exit check:** upload `sample_data/payment_outage.log` → events visible via `GET /events`; response shows accepted/rejected counts.

### Phase 2: Simulator (2:15–3:15)
- [ ] `scenarios.py` with S1 fully scripted (specsheet §13) plus background noise and the CDN distractor
- [ ] `runner.py` async playback with speed control, `SEED`, start/stop/reset/status endpoints
- [ ] `make seed` writes the same S1 events to `.jsonl`, `.log`, `.csv` in `sample_data/`
- **Exit check:** start simulator → events stream into DB at expected offsets; reset clears everything.

### Phase 3: Detection, correlation, root cause (3:15–6:00) — **the core; protect this time**
- [ ] `anomaly.py`: signature tagging via `rules.yaml`, robust z-score for metrics
- [ ] `correlation.py`: pairwise weight, threshold, union-find, min size rule, merge into existing incidents
- [ ] `rootcause.py`: four factors, softmax confidence, evidence strings, alternatives
- [ ] `impact.py`, `timeline.py`, `severity.py`, `recommend.py`
- [ ] `engine.py` tick: detect → correlate → analyse → persist → publish
- [ ] `GET /incidents`, `GET /incidents/{id}`; WebSocket broadcast
- [ ] **Golden test** (agent.md §8) passing for S1; tests for S2 and S3 once scenarios exist
- **Exit check:** run S1 via simulator; `GET /incidents` returns one P1 incident with root cause `postgres-primary` ≥ 0.70 and a separate low-severity CDN cluster.

### Phase 4: Frontend on the M.O.N.K.Y shell (6:00–9:00; can start during Phase 1 using fixtures)
- [ ] API client, TanStack Query provider, WebSocket hook in a client component + zustand store, "Live updates paused" banner
- [ ] Overview page: KpiStrip, incident list, live ticker (template cards/table reused)
- [ ] Incident detail: `RootCausePanel`, `ConfidenceMeter`, `ImpactCard`, `RecommendationItem`
- [ ] `ServiceNode` and causal graph (React Flow via `dynamic`, `ssr: false`; layered layout by `tier`; animated propagation edges)
- [ ] `Timeline` with lanes, playhead, replay 1×/5×/10×
- [ ] Sources page: upload dropzone, curl snippet, simulator controls (also reachable from the top bar)
- **Exit check:** full S1 flow visible live in the browser without touching the console, and the pages still look like the template (spacing, radii, fonts unchanged).

### Phase 5: Report, LLM and polish (9:00–10:30)
- [ ] `report.py`: template renderer first; LLM path second with 15s timeout and fact-only prompt
- [ ] Report tab with regenerate and download
- [ ] Empty/loading/error/disconnected states (design_system §7)
- [ ] Copilot panel using the template's chat component (stretch; first thing to cut)
- [ ] Accessibility pass: focus rings, aria labels, list-view toggle for the graph
- [ ] Add S2/S3 scenarios if time allows
- **Exit check:** works with `ANTHROPIC_API_KEY` unset; keyboard-only path works.

### Phase 6: Packaging and rehearsal (10:30–12:00)
- [ ] `Dockerfile` ×2, `docker-compose.yml`; test on a clean clone
- [ ] README: pitch, architecture diagram, run steps, scenario descriptions, roadmap
- [ ] Record a 2–3 minute backup demo video
- [ ] Rehearse the demo script (specsheet §16) twice with a timer
- **Exit check:** cold `docker compose up` → demo runs end to end.

---

## 3. Prompt pack (paste into your AI coding agent, one at a time)

Start every session with: *"Read agent.md, specsheet.md, design_system.md and skillbuild.md. Confirm you understand the golden test. Then do the following task."*

**P0: Scaffold and import template**
> The human has exported the M.O.N.K.Y template into `frontend/`. If it is not there, stop and ask for it; if that is impossible, use the fallback in design_system §11 and say so. Create the rest of the repo exactly as in agent.md §2: FastAPI app with `/health`, CORS from `CORS_ORIGINS`, config via pydantic-settings, SQLAlchemy models from specsheet §5.4, startup that loads `data/topology.json`. Add Makefile targets from agent.md §3 and the `.env` examples. Show me how to run both servers.

**P0b: Template audit and cleanup**
> Follow design_system §2 and §11. Read the template's code and write `docs/tokens-audit.md`. Remove demo routes, sample data and placeholder branding; rename to J.A.R.V.I.S.; adapt the sidebar to Overview / Incidents / Sources / Topology and the top bar to a live indicator plus a simulator quick control. Add the semantic status tokens (design_system §3) to `globals.css` and Tailwind, resolving any accent conflict as described there. Do not restyle the template. `npm run build` must pass. Report a short summary of tokens found and components reusable.

**P1: Normalizer and ingest**
> Implement `core/normalizer.py` and the endpoints `POST /events`, `POST /ingest/upload`, `GET /events` per specsheet §5.1–5.2 and §11. Support JSONL, CSV, and raw log lines (regex in §5.2). Infer severity from level words. Unknown services must be auto-added as unmapped. Return `{accepted, rejected, errors[:10]}`. Write pytest tests for each format and for bad lines.

**P2: Simulator**
> Implement `simulator/scenarios.py` and `runner.py` for scenario `db_pool_exhaustion` exactly as specsheet §13, seeded by `SEED`, with background noise and the CDN distractor. Add `/simulator/start|stop|reset|status`. Add `make seed` to write `sample_data/payment_outage.{jsonl,log,csv}`. Include user_ids on login_failed and payment_failed events (at least 60 distinct users overall).

**P3a: Anomaly and rules**
> Implement `core/anomaly.py` and `data/rules.yaml` (≥6 rules from specsheet §10). Add signature tagging and the median/MAD robust z-score for metrics with absolute thresholds. Pure functions only. Tests: spike flagged, steady noise ignored, each signature tagged.

**P3b: Correlation**
> Implement `core/correlation.py` per specsheet §6: pairwise weight, threshold, union-find, ≥3 events across ≥2 services, merging into existing incidents by ≥50% service overlap. Keep it pure and fast (±5 minute neighbor window). Test with S1: exactly one main incident and a separate CDN cluster.

**P3c: Root cause, impact, timeline, severity**
> Implement `core/rootcause.py`, `impact.py`, `timeline.py`, `severity.py` per specsheet §7–9, using NetworkX on the dependency graph (edge A→B means A depends on B). Evidence strings must be plain English with real numbers from the data. Add the golden test from agent.md §8.

**P3d: Engine and API**
> Implement `core/engine.py` (tick every `TICK_SECONDS`: detect → correlate → analyse → persist → broadcast) and endpoints `GET /incidents`, `GET /incidents/{id}`, `PATCH /incidents/{id}`, `GET /stats/overview`, WebSocket `/ws/stream` with the message types in specsheet §11. Make sure incident IDs are stable across ticks.

**P4a: Frontend data layer**
> In `frontend/`, create `lib/types.ts` mirroring `schemas.py`, `lib/api.ts` using `NEXT_PUBLIC_API_URL`, a TanStack Query provider, and a WebSocket hook (client component, `NEXT_PUBLIC_WS_URL`, auto-reconnect) that updates a zustand store and invalidates queries. Show the "Live updates paused. Reconnecting…" banner from design_system §7. Use `fixtures/incident_s1.json` when `NEXT_PUBLIC_USE_FIXTURES=1`.

**P4b: Overview and incident detail**
> Build the Overview and Incident detail pages following design_system §6–7, reusing the template's cards, tables, tabs, badges and layout. Components: KpiStrip, IncidentRow, SeverityPill (icon + text), RootCausePanel (cause rail), ConfidenceMeter, ImpactCard, RecommendationItem, EventTable. Use token classes only. Include loading, empty and error states. The pages must look like they belong to the template.

**P4c: Graph and timeline**
> Build `ServiceNode` and the causal graph with React Flow, loaded via `next/dynamic` with `ssr: false`: layered layout by `tier`, node states (root cause with a single pulse ring, affected, at risk dashed, healthy, unmapped), animated propagation edges with lag labels. Build `Timeline` with per-service lanes, markers, playhead, play/pause, 1×/5×/10×, arrow-key stepping; scrubbing updates graph node states. Add a "View as list" alternative. Respect reduced motion.

**P5: Report**
> Implement `core/report.py`: a deterministic Markdown template from the incident JSON, plus an LLM path using the Anthropic SDK that receives only the structured incident summary and must use only supplied facts. 15s timeout, fallback to template, cache per incident. Add the Report tab with regenerate, download, and a "Written by AI / Generated from template" badge.

**P5b: Copilot (stretch)**
> Backend: add `core/copilot.py` and `POST /incidents/{id}/ask` per specsheet §12.3. Answer only from the incident's structured JSON. With an LLM key use the model with a fact-only prompt (15s timeout); without one, fall back to intent matching (why / who is affected / what first / timeline / confidence). Frontend: build `CopilotPanel` on the template's chat component with three suggestion chips and a "Based on this incident's data" note. Add tests for the fallback intents.

**P6: Packaging**
> Add Dockerfiles and docker-compose, `.env.example`, a README with architecture diagram (ASCII or mermaid), run steps, scenarios, demo script and roadmap. Verify on a clean clone that `docker compose up --build` gives a working app.

**Review prompt (use after any phase)**
> Review the work against specsheet.md and design_system.md. List any deviations, missing tests, hard-coded colors, accessibility gaps, and anything that would break the golden test. Fix them.

---

## 4. Sample data to prepare (Phase 2)

`sample_data/payment_outage.log` (excerpt of the format the parser must handle):
```
2026-11-09T10:15:00Z WARN  postgres-primary connections 90/100 host=pg-1
2026-11-09T10:15:02Z ERROR postgres-primary too many connections host=pg-1
2026-11-09T10:15:13Z ERROR payment-service timeout acquiring connection from pool trace=tr_9ac1 user=u_4821 latency=2300ms
2026-11-09T10:15:36Z ERROR auth-service login failed: upstream timeout user=u_1177 trace=tr_77b2
2026-11-09T10:15:49Z ERROR api-gateway 504 gateway timeout status=504 latency=3100ms
2026-11-09T10:15:57Z ERROR payment-service payment failed: could not persist transaction user=u_2031 status=500
2026-11-09T10:15:22Z WARN  cdn image latency above baseline p95=950ms
```
Include a 5-minute run of healthy background traffic **before** the incident so the baselines are meaningful.

---

## 5. Verification matrix (run at the end of each phase)

| Check | Command or action | Expected |
|---|---|---|
| Unit tests | `make test` | All green |
| Lint and types | `make lint` | Clean |
| Golden scenario | `pytest -k golden` | 1 main incident, root cause `postgres-primary` ≥ 0.70 |
| File ingest | Upload `payment_outage.log` | Accepted count matches the file |
| API ingest | `curl -X POST :8000/api/v1/events -d '[...]'` | 200 with accepted count |
| Live flow | Start simulator at 5× | Incident appears within ~15s, updates live |
| No-LLM mode | Unset `ANTHROPIC_API_KEY` | Report from template; no errors |
| Keyboard | Tab through incident detail | Focus visible; timeline controllable |
| Cold start | `docker compose up --build` on clean clone | Demo works |

---

## 6. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Correlation merges everything or nothing | High | Tune against S1 early; print pairwise weights; keep CDN distractor in the golden test |
| Edge direction reversed, wrong root cause | High | Unit test on a 3-node chain; document "A → B = A depends on B" in code |
| Graph layout looks messy | Medium | Use layered layout by `tier`; fixed node size; no force layout |
| LLM slow or unavailable at demo | Medium | Template fallback, cached report, pre-generate before the demo |
| Live demo breaks | Medium | `SEED` determinism, backup video, one-click reset |
| Scope creep (extra scenarios, topology editor) | High | Follow the cut list; only S1 is mandatory |
| Time zone bugs on uploads | Medium | Treat naive timestamps as UTC; test it |
| Template code is unfamiliar or messy | Medium | Do the token audit first; reuse components instead of rewriting; keep changes small |
| React Flow breaks under Next.js SSR | Medium | `dynamic(..., { ssr: false })` and an explicit container height |
| Our red/amber clashes with the template's accent | Medium | Apply the conflict rule in design_system §3; red only on cause elements |
| Template export unavailable or incompatible | Low | Fallback scaffold in design_system §11 |

---

## 7. What makes this win (judging lens)

1. **Clear problem, clear payoff:** many alerts become one cause, in under a minute.
2. **Explainability:** confidence plus evidence on screen, not a black box.
3. **Demo moment:** the graph lighting up red at the database, then the replay showing the spread.
4. **Honest correlation:** the unrelated CDN alert stays separate, which shows it is not "merge all".
5. **Completeness:** all seven required features visibly present; three data sources working.
6. **Polish:** consistent design system, empty/error states, accessibility.
7. **Credible roadmap:** OpenTelemetry/Prometheus connectors, learned topology, feedback loop, runbook automation.

---

## 8. Judge Q&A cheat sheet

- **"Is this real ML?"** The correlation and root-cause scoring are transparent, weighted heuristics over time, topology and text similarity, with robust statistics for anomaly detection. We chose explainability over a black box; the feedback loop in the roadmap would let us learn the weights.
- **"How does it scale?"** The engine is stateless and windowed; swap SQLite for Postgres, ingest through Kafka/OpenTelemetry, shard by service group.
- **"What if the topology is unknown?"** Unknown services are added as unmapped nodes; correlation falls back to time, trace/user context and text similarity. Roadmap: infer topology from traces.
- **"Why not just use PagerDuty or Datadog?"** They alert, we explain. J.A.R.V.I.S. focuses on cause, impact and fix in one view and shows the evidence.
- **"What about false positives?"** The confidence score drops when evidence is ambiguous, and the UI says "root cause uncertain" with the top three candidates.

---

## 9. Cut list (apply in order if you run behind)

1. Copilot chat panel (hide the template chat shell)
2. Topology page (keep the graph inside the incident view)
3. Scenarios S2 and S3 (keep S1 plus the CDN distractor)
4. LLM report path (keep the template report)
5. Timeline scrubbing (keep static timeline with stage list)
6. Theme toggle polish, list-view toggle polish, Playwright test
7. CSV upload (keep JSONL and raw log)

**Never cut:** S1 golden scenario, evidence list, impact panel, causal graph, one working data source of each kind (API, file, simulator), README and demo script.

---

## 10. Final pre-demo checklist

- [ ] Fresh clone runs with one command
- [ ] Simulator reset → start produces the same result every time
- [ ] Browser zoom set for the projector; fonts loaded offline (fallbacks verified)
- [ ] Report pre-generated; backup video ready; laptop on charger
- [ ] Each teammate knows their part of the 3-minute script
- [ ] Judge Q&A sheet reviewed
