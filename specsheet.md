# specsheet.md — J.A.R.V.I.S. (Justified Analysis, Reasoning & Visualization of Incident Systems)

NITSHACKS 9.0 · Software Track · Problem Statement 1

This is the source of truth for **what** to build. `design_system.md` covers how it looks, `agent.md` covers how an AI coding agent should work in the repo, and `skillbuild.md` covers the order of work. `master_prompt.md` is the single prompt that drives a coding agent through all of it.

**Revision 2:** the UI is built on the Vercel v0 community template **Dashboard – M.O.N.K.Y** (JOYCO, https://v0.app/templates/b7GDYVxuoGC). Frontend is Next.js (App Router) + Tailwind + shadcn/ui, dark-first. The backend is unchanged.

---

## 1. Product summary

J.A.R.V.I.S. ingests logs, alerts and metrics from several sources, groups the ones that belong to the same underlying problem into a single **incident**, ranks the most likely **root cause** with an explanation, shows the **blast radius**, replays how the failure **spread** across services, and recommends **fixes**.

**One-line pitch:** "Ten alerts, one cause. J.A.R.V.I.S. shows you which one and why."

### Primary scenario (must work flawlessly)
A digital payment platform shows login failures, slow API responses and failed transactions. All three are symptoms of one failure: the primary database exhausting its connection pool. J.A.R.V.I.S. must connect them and name `postgres-primary` as the root cause with a confidence score and evidence.

### Secondary scenarios (nice to have, in priority order)
1. **Unrelated noise** — a separate, minor CDN slowdown that must NOT merge into the main incident (proves correlation is not "merge everything").
2. **Bad deploy** — `auth-service` deploy followed by login errors, then gateway 5xx.
3. **Cache failure** — `redis-cache` down causing a latency cascade.

---

## 2. Requirements traceability (problem statement → implementation)

| # | Problem-statement feature | Implementation | Acceptance test |
|---|---|---|---|
| 1 | Multiple data sources (APIs, uploaded logs, simulated live data) | REST ingest endpoint, file upload (JSONL/CSV/plain log), simulator with WebSocket stream | All three sources produce events visible in the same feed, tagged by `source` |
| 2 | Event correlation (timestamps, common services, activity patterns) | Weighted pairwise correlation + union-find clustering (see §6) | Scenario 1 events collapse into 1 incident; CDN noise stays separate |
| 3 | Root cause detection | Multi-factor scoring with softmax confidence and evidence list (see §7) | Root cause = `postgres-primary`, confidence ≥ 0.70 |
| 4 | Impact analysis | Dependency-graph traversal plus observed-affected users and failed transactions (see §8) | Impact panel lists affected services, user count, failed payments |
| 5 | Incident timeline | Ordered propagation stages with per-service first-seen time (see §9) | Timeline shows DB → payment → auth → gateway order |
| 6 | Smart recommendations | Rulebook by signature plus LLM-written explanation, with offline fallback (see §10) | Recommendations appear with priority and rationale; works with no API key |
| 7 | Interactive dashboard | Next.js app on the M.O.N.K.Y shell: overview, incident detail, sources, topology (see §12) | Click an incident → graph, timeline, root cause, impact, report all render |

---

## 3. Tech stack (fixed — do not substitute without a reason)

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn | Fast to build, typed, native WebSocket |
| Storage | SQLite via SQLAlchemy 2.0 (file `jarvis.db`) | Zero setup; swap to Postgres later |
| Graph / analytics | NetworkX, NumPy, scikit-learn (TF-IDF only) | Dependency graph traversal and text similarity |
| LLM (optional) | Anthropic API via `anthropic` SDK; model from env `LLM_MODEL` | Incident narrative; must degrade gracefully |
| Frontend | Next.js 14+ (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui, forked from the M.O.N.K.Y template | Studio-quality shell (sidebar, top bar, chat, design system) for free |
| Graph viz | React Flow (`@xyflow/react`) | Custom nodes, animated edges |
| Charts | Recharts | Latency/error sparklines |
| State/data | TanStack Query + a small Zustand store for live stream | Simple caching plus live updates |
| Realtime | WebSocket `/ws/stream` | Live feed and incident updates |
| Tests | pytest, httpx, Vitest, Playwright (one smoke test) | Core logic must be tested |
| Packaging | Docker Compose (api, web) plus `make dev` | One-command start |

---

## 4. Architecture

```
 ┌──────────────┐  ┌───────────────┐  ┌────────────────┐
 │ REST ingest  │  │ File upload   │  │ Live simulator │
 │ POST /events │  │ JSONL/CSV/log │  │ scenario runner│
 └──────┬───────┘  └──────┬────────┘  └───────┬────────┘
        └────────────┬────┴───────────────────┘
                     ▼
          ┌─────────────────────┐
          │ Normalizer          │  parsers → canonical Event
          └─────────┬───────────┘
                    ▼
          ┌─────────────────────┐
          │ Event store (SQLite)│◄──────────────┐
          └─────────┬───────────┘               │
                    ▼                           │
          ┌─────────────────────┐               │
          │ Anomaly detector    │ flags events  │
          └─────────┬───────────┘               │
                    ▼                           │
          ┌─────────────────────┐   ┌───────────┴─────────┐
          │ Correlation engine  │──►│ Incident store      │
          └─────────┬───────────┘   └───────────┬─────────┘
                    ▼                           │
   ┌────────────────────────────────┐           │
   │ Root cause · Impact · Timeline │           │
   │ Recommendations · Report (LLM) │───────────┘
   └────────────────┬───────────────┘
                    ▼
        REST + WebSocket → Next.js dashboard
```

### Backend layout
```
backend/
  app/
    main.py                 # FastAPI app, routers, CORS, lifespan
    config.py               # env settings (pydantic-settings)
    db.py                   # engine, session, create_all
    models.py               # SQLAlchemy models
    schemas.py              # Pydantic request/response models
    api/
      events.py  ingest.py  incidents.py  topology.py  simulator.py  stats.py  ws.py
    core/
      normalizer.py         # parse JSONL, CSV, raw log lines
      anomaly.py            # robust z-score + signature tagging
      correlation.py        # pairwise weights, union-find clustering
      rootcause.py          # scoring + confidence + evidence
      impact.py             # blast radius, users, transactions
      timeline.py           # propagation stages
      severity.py           # P1–P4 scoring
      recommend.py          # rulebook lookup
      report.py             # LLM narrative with template fallback
      engine.py             # orchestrates a tick: detect → correlate → analyse → persist
    data/
      topology.json         # default service graph
      rules.yaml            # signatures, root cause labels, fixes
    simulator/
      scenarios.py          # scripted event generators
      runner.py             # async playback with speed control
  tests/
```

---

## 5. Data contracts

### 5.1 Canonical event
```json
{
  "id": "evt_01HXYZ",
  "timestamp": "2026-11-09T10:15:02.123Z",
  "source": "api | file | simulator",
  "service": "payment-service",
  "host": "pay-2",
  "type": "log | alert | metric",
  "severity": "info | warning | error | critical",
  "message": "timeout acquiring connection from pool",
  "metric": { "name": "p95_latency_ms", "value": 2300 },
  "user_id": "u_4821",
  "trace_id": "tr_9ac1",
  "signature": "db_pool_exhausted",
  "is_anomaly": true,
  "attrs": { "endpoint": "/v1/charge", "status": 504 }
}
```
Required: `timestamp`, `service`, `message` or `metric`. Everything else is optional and defaulted by the normalizer (`severity` inferred from level keywords, `type` inferred, `source` set by the ingest path).

### 5.2 Accepted upload formats
- **JSONL**: one canonical-ish event per line. Unknown fields go into `attrs`.
- **CSV**: header row with any of `timestamp,service,severity,message,user_id,trace_id,host,metric_name,metric_value`.
- **Plain log**: regex `^(?P<ts>\S+)\s+(?P<level>[A-Z]+)\s+(?P<service>[\w\-.]+)\s*[:\-]?\s*(?P<msg>.*)$`, with optional `user=`, `trace=`, `status=`, `latency=` tokens extracted from `msg`.
- Bad lines are skipped and counted; the response returns `{accepted, rejected, errors[:10]}`.
- Max upload 20 MB. Timestamps with no timezone are treated as UTC.

### 5.3 Topology
```json
{
  "services": [
    {"id":"web-app","kind":"client","tier":0,"critical":false},
    {"id":"api-gateway","kind":"gateway","tier":1,"critical":true},
    {"id":"auth-service","kind":"service","tier":2,"critical":true},
    {"id":"payment-service","kind":"service","tier":2,"critical":true},
    {"id":"order-service","kind":"service","tier":2,"critical":false},
    {"id":"notification-service","kind":"service","tier":3,"critical":false},
    {"id":"redis-cache","kind":"cache","tier":3,"critical":false},
    {"id":"postgres-primary","kind":"database","tier":4,"critical":true},
    {"id":"cdn","kind":"edge","tier":0,"critical":false}
  ],
  "dependencies": [
    {"from":"web-app","to":"api-gateway"},
    {"from":"api-gateway","to":"auth-service"},
    {"from":"api-gateway","to":"payment-service"},
    {"from":"api-gateway","to":"order-service"},
    {"from":"auth-service","to":"postgres-primary"},
    {"from":"auth-service","to":"redis-cache"},
    {"from":"payment-service","to":"postgres-primary"},
    {"from":"order-service","to":"postgres-primary"},
    {"from":"payment-service","to":"notification-service"},
    {"from":"web-app","to":"cdn"}
  ]
}
```
Edge `A → B` means **A depends on B**. A failure in B propagates to A. Unknown services found in events are auto-added as isolated nodes (and flagged "unmapped") so ingestion never fails.

### 5.4 Database tables
`events`, `incidents`, `incident_events(incident_id, event_id)`, `incident_services(incident_id, service, role[root|affected|at_risk], first_seen, peak_severity, event_count)`, `recommendations(incident_id, priority, title, detail, source[rule|llm])`, `reports(incident_id, markdown, generated_by[llm|template], created_at)`, `services`, `dependencies`.

Incident row: `id, title, status[open|investigating|resolved], severity[P1..P4], started_at, last_event_at, root_cause_service, root_cause_label, confidence, user_impact, failed_txn_count, summary`.

---

## 6. Correlation engine

Runs every **2 seconds** (and once after each upload) over a sliding **10-minute window** of anomalous events.

1. **Select candidates** — events where `is_anomaly` is true (see §6.1).
2. **Pairwise weight** between events *i* and *j*:

```
w = 0.40 * time_prox + 0.35 * topo_prox + 0.15 * shared_ctx + 0.10 * text_sim
time_prox  = exp(-|Δt| / 120s)
topo_prox  = 1 / (1 + hops(service_i, service_j))      # undirected shortest path; 0 if unmapped/disconnected
shared_ctx = 1 if same trace_id, 0.6 if same user_id within 60s, 0.4 if same host, else 0
text_sim   = TF-IDF cosine similarity of normalized messages
```
3. **Link** pairs with `w ≥ 0.45` (tunable: `CORRELATION_THRESHOLD`).
4. **Cluster** with union-find. Each cluster of ≥ 3 events spanning ≥ 2 services becomes an incident. Smaller clusters stay as "uncorrelated alerts".
5. **Merge / update** — if a new cluster overlaps an existing open incident by ≥ 50% of services, update that incident instead of creating a new one (stable IDs, no flicker).
6. **Resolve** — incident is auto-marked `resolved` after 5 quiet minutes (configurable).

For performance, only compare each event to events within ±5 minutes, and cap the window at 5,000 events.

### 6.1 Anomaly detection
- **Logs/alerts**: anomaly if `severity ≥ warning` OR a signature from `rules.yaml` matches.
- **Metrics**: robust z-score per `(service, metric)` over the last 30 samples: `z = 0.6745 * (x - median) / MAD`. Anomaly if `z > 3.5` or an absolute threshold is crossed (`p95_latency_ms > 1000`, `error_rate > 0.05`).
- Signature tagging sets `signature` (e.g. `db_pool_exhausted`, `timeout`, `conn_refused`, `oom`, `deploy`, `http_5xx`, `login_failed`, `payment_failed`, `cache_miss_storm`).

---

## 7. Root cause detection

For each service *s* in the incident, compute four sub-scores in [0, 1]:

| Factor | Weight | Definition |
|---|---|---|
| Earliness | 0.35 | `1 - rank(first_anomaly_time_s) / (n-1)`; earliest service scores 1 |
| Upstream-ness | 0.35 | Fraction of the *other* incident services that transitively depend on *s* (i.e. *s* is in their dependency closure) |
| Signature strength | 0.20 | Best prior from `rules.yaml` for signatures seen on *s* (e.g. `db_pool_exhausted` on a `database` node = 1.0) |
| Severity | 0.10 | Peak severity normalized (info 0, warning 0.33, error 0.66, critical 1) |

`raw_s = Σ weight × factor`. **Confidence** = softmax(`raw_s / 0.15`) so the top candidate typically lands 0.7–0.95 when evidence is aligned and much lower when it is ambiguous.

**Output per incident**
```json
{
  "root_cause": {
    "service": "postgres-primary",
    "label": "Database connection pool exhaustion",
    "confidence": 0.91,
    "evidence": [
      "First anomaly in the incident (10:15:02), 23s before any other service",
      "All 4 other affected services depend on it",
      "Matched signature: 'timeout acquiring connection from pool'",
      "Active connections hit 100/100 at 10:15:04"
    ],
    "alternatives": [
      {"service":"payment-service","confidence":0.06},
      {"service":"auth-service","confidence":0.02}
    ]
  }
}
```
The `evidence` list is **mandatory** — every score must be explainable in plain language. If the top confidence is < 0.5 the UI says "Root cause uncertain" and shows the top three candidates.

---

## 8. Impact analysis

- **Affected services** (observed): services with anomalous events in the incident.
- **At-risk services** (predicted): transitive dependents of the root cause with no anomalies yet.
- **Users affected**: distinct `user_id` on error/critical events (fallback: count of failed login/payment events).
- **Failed transactions**: count of events with signature `payment_failed` or `attrs.status ≥ 500` on payment endpoints.
- **Critical path hit**: true if any `critical` service is affected.
- **Severity** (P1–P4): P1 if critical path hit AND (≥ 4 services OR ≥ 50 users); P2 if critical path hit; P3 if ≥ 2 services; else P4.

---

## 9. Incident timeline

Build **stages**: group services by first-anomaly time in 15-second buckets. Each stage returns `{t, offset_seconds, services[], key_events[]}` plus **propagation edges** `{from, to, lag_seconds}` that follow real dependency edges (cause → dependent). The UI animates this in order. Example for the primary scenario:

```
+0s   postgres-primary    pool exhausted (100/100)
+11s  payment-service     DB acquire timeouts
+19s  auth-service        slow queries
+34s  auth-service        login failures begin
+47s  api-gateway         5xx spike, latency p95 > 3s
+68s  web-app             checkout errors reported
```

---

## 10. Recommendations and report

**Rulebook (`rules.yaml`)** — each rule has `signature`, `applies_to_kind`, `label`, `prior`, and ordered `actions`:
```yaml
- id: db_pool_exhausted
  match: ["connection pool", "too many connections", "timeout acquiring connection"]
  applies_to: [database]
  label: Database connection pool exhaustion
  prior: 1.0
  actions:
    - {priority: 1, title: "Raise pool size / max_connections temporarily", detail: "...", risk: low}
    - {priority: 2, title: "Kill idle-in-transaction sessions", detail: "...", risk: medium}
    - {priority: 3, title: "Find the leaking client (last deploy / slow query)", detail: "...", risk: low}
    - {priority: 4, title: "Add pgbouncer and per-service pool limits", detail: "long-term", risk: low}
```
Ship at least 6 rules: DB pool exhaustion, cache failure, bad deploy, OOM/memory pressure, network partition/timeouts, downstream dependency outage.

**Report generation** — Markdown with sections: Summary · Root cause · Timeline · Impact · Recommended actions · Open questions.
- LLM path: send the structured incident JSON (not raw logs) to the model and ask it to write only from the given facts. Timeout 15s.
- Fallback: deterministic template rendering of the same JSON. The app must work fully with **no API key**.
- Report is cached per incident; "Regenerate" button forces a refresh.
- Never invent numbers: the prompt says "use only the supplied facts; say 'unknown' otherwise".

---

## 11. API specification (`/api/v1`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| POST | `/events` | Ingest one event or a list (`source=api`) |
| POST | `/ingest/upload` | Multipart file upload → `{accepted, rejected, errors}` |
| GET | `/events` | Query: `service, severity, source, from, to, anomaly, limit, cursor` |
| GET | `/incidents` | List with filters `status, severity` |
| GET | `/incidents/{id}` | Full detail: root cause, impact, timeline, recommendations, events, graph |
| GET | `/incidents/{id}/report` | `?format=md|json` |
| POST | `/incidents/{id}/report/regenerate` | Force regenerate |
| POST | `/incidents/{id}/ask` | Copilot Q&A grounded in that incident's data (stretch, see §12.3) |
| PATCH | `/incidents/{id}` | Update `status` |
| GET | `/topology` | Services and dependencies with live health |
| PUT | `/topology` | Replace topology |
| POST | `/simulator/start` | `{scenario, speed: 1|5|10}` |
| POST | `/simulator/stop` · `/simulator/reset` | Stop · clear all data |
| GET | `/simulator/status` | Running, scenario, progress |
| GET | `/stats/overview` | Event rate, open incidents, affected services, MTTD |
| WS | `/ws/stream` | Pushes `event.ingested`, `incident.created`, `incident.updated`, `simulator.progress` |

Errors use `{ "error": { "code": "...", "message": "..." } }` with correct HTTP codes. All timestamps are ISO-8601 UTC.

---

## 12. Frontend specification

### 12.1 Base and conventions
- **Base:** fork/export the M.O.N.K.Y template into `frontend/`. Keep its shell (collapsible sidebar, top bar, multi-view layout), tokens, shadcn primitives and chat component. Visual rules are in `design_system.md`.
- **Next.js:** App Router. Pages that show live data are client components (`"use client"`). React Flow and the timeline are loaded with `next/dynamic` and `ssr: false`.
- **Env (`frontend/.env.local`):** `NEXT_PUBLIC_API_URL=http://localhost:8000` and `NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/stream`. Backend CORS must allow `http://localhost:3000`.
- **Data:** TanStack Query for REST, one WebSocket hook writing to a small Zustand store and invalidating queries.
- **Theme:** dark-first as in the template. Do not build a separate light theme unless the template already has one.

### 12.2 Template mapping

| Template piece | J.A.R.V.I.S. use |
|---|---|
| Sidebar | Overview, Incidents, Sources, Topology (demo links removed) |
| Top bar | Page title, live connection indicator, simulator quick control |
| Multi-view layout | Four routes below |
| Integrated chat | Copilot panel on the incident page |
| Cards / tables / charts | KPI strip, event table, sparklines, impact card |

### 12.3 Routes
1. **`/` Overview**: KPI strip (open incidents, services affected, events per minute, time to detect), incident list sorted by severity then recency, live event ticker, mini topology with health colors.
2. **`/incidents/[id]` Incident detail** (the hero screen)
   - Header: title, severity, status, started time, duration.
   - **Root cause panel**: service, label, confidence meter, evidence list, alternatives.
   - **Causal graph** (React Flow): root node highlighted, affected nodes colored by severity, at-risk nodes dashed, animated edges showing propagation direction.
   - **Timeline**: horizontal lanes per service, markers for key events, scrub/replay control.
   - **Impact**: services, users, failed transactions, critical path flag.
   - **Recommendations**: prioritized list with risk tag and copy button.
   - **Tabs**: Events (filterable table; clicking a row highlights its node) and Report (rendered Markdown, regenerate, download `.md`).
   - **Copilot (stretch)**: docked chat using the template's chat UI. `POST /incidents/{id}/ask` with `{question}` returns `{answer, based_on: ["root_cause","impact",...]}`. The server answers only from the incident's structured JSON. With an LLM key it uses the model; without one it falls back to intent matching (why / who / what first / timeline / confidence) over the same JSON. Three suggestion chips are always shown.
3. **`/sources` Data sources**: upload dropzone with parse results, API snippet (`curl` example), simulator controls (scenario, speed, start/stop/reset).
4. **`/topology`**: read-only graph with live health (JSON edit is a stretch).

### 12.4 States
Every view has a loading skeleton, an empty state with a call to action ("Start the simulator or upload a log file"), an error state with retry, and a stream-lost banner.

### 12.5 Cleanup
No template demo pages, sample data or placeholder branding may remain in the final build.

---

## 13. Simulator scenarios (`scenarios.py`)

Each scenario is a list of `(offset_seconds, event_template)` plus background noise (info logs and healthy metrics at about 5–10 events/sec at 1×).

**S1 — `db_pool_exhaustion` (primary, ~90 seconds at 1×)**
- t+0 `postgres-primary` warning "connections 90/100", then error "too many connections" (t+2).
- t+11 `payment-service` errors "timeout acquiring connection from pool"; p95 latency jumps from 180ms to 2,300ms.
- t+19 `auth-service` slow queries; t+34 `login_failed` events with `user_id`s.
- t+47 `api-gateway` 502/504 and p95 > 3s.
- t+55–80 `payment_failed` events (≈ 40) with user IDs; `order-service` timeouts.
- **Concurrent noise**: t+20 `cdn` image latency warnings (should remain a separate low-severity cluster).

**S2 — `bad_deploy`**: deploy event on `auth-service`, then error rate spike, then gateway 5xx.
**S3 — `cache_failure`**: `redis-cache` conn refused → auth latency → login failures.

Simulator is deterministic when `SEED` is set so demos are repeatable.

---

## 14. Non-functional requirements

- Ingest 1,000 events/sec sustained locally; a correlation tick on a 5,000-event window finishes in under 500 ms.
- Dashboard updates within 1 second of an incident change (WebSocket).
- Cold start to working demo in under 2 minutes using `docker compose up`.
- No secrets in the repo; `.env.example` provided. LLM key optional.
- Accessibility: keyboard navigable, WCAG AA contrast, severity never conveyed by color alone (icon and text label too).
- Logging: structured JSON logs from the backend; no PII beyond synthetic `user_id`.

---

## 15. Testing and acceptance

**Backend (pytest)**
- Normalizer: JSONL, CSV, raw-log parsing, bad-line handling.
- Anomaly: z-score flags a latency spike, ignores steady noise.
- Correlation: S1 produces exactly 1 main incident (≥ 5 services) plus 1 separate CDN cluster.
- Root cause: S1 → `postgres-primary`, confidence ≥ 0.70, ≥ 3 evidence lines. S2 → `auth-service`. S3 → `redis-cache`.
- Impact: S1 reports ≥ 30 affected users and ≥ 30 failed transactions.
- Report: template fallback works with no API key.
- Performance: 5,000-event tick under 500 ms.

**Frontend**: component tests for ConfidenceMeter, RootCausePanel, Timeline; one Playwright smoke test (start simulator → incident appears → detail page shows root cause).

**Definition of done for the prototype**
- [ ] All three data sources work end to end
- [ ] S1 produces the correct single incident and root cause live
- [ ] Graph, timeline, impact, recommendations and report all render for S1
- [ ] Works with no LLM key
- [ ] `docker compose up` brings up the full app
- [ ] README with architecture diagram, run steps and demo script
- [ ] UI is the M.O.N.K.Y shell with J.A.R.V.I.S. screens; no template demo content left
- [ ] `docs/tokens-audit.md` exists and the semantic status tokens are in `globals.css`

---

## 16. Demo script (3 minutes)

1. **(20s) Problem**: show a wall of raw alerts from a payment platform ("login failures, slow APIs, failed payments: three teams, three tickets").
2. **(30s) Ingest**: upload a log file, hit one API call with `curl`, click "Start simulator".
3. **(40s) Correlation**: overview shows one P1 incident replacing dozens of alerts; the unrelated CDN alert correctly stays separate.
4. **(50s) Root cause**: open the incident; the graph lights up red at `postgres-primary`; read the confidence and evidence lines.
5. **(20s) Timeline replay**: scrub through the spread DB → payment → auth → gateway.
6. **(20s) Impact and fix**: affected users and failed payments, then prioritized recommendations.
7. **(20s) Report**: generated incident report, download it. Close with scalability (swap SQLite → Postgres, ingest from Kafka/OpenTelemetry, learn rules from past incidents).

---

## 17. Out of scope (state explicitly to judges)
Real agent-based collection, auth/multi-tenancy, automatic remediation execution, ML model training. Mention them as the roadmap.

## 18. Future scope
OpenTelemetry/Prometheus/Loki connectors, learned topology from traces, feedback loop ("was this root cause right?") to tune weights, Slack/PagerDuty integration, runbook automation.
