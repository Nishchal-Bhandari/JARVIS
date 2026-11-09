# J.A.R.V.I.S. — Justified Analysis, Reasoning & Visualization of Incident Systems

**NITSHACKS 9.0 · Problem Statement 1 · "Ten alerts, one cause."**

J.A.R.V.I.S. ingests logs, alerts and metrics from an API, uploaded files and a
live simulator, correlates them into incidents, names the most likely root cause
with a confidence score and plain-English evidence, shows impact and a
propagation timeline, recommends fixes, and generates an incident report.

Headline scenario: login failures, slow APIs and failed payments on a payment
platform — all tracing back to a database connection pool exhaustion
(`postgres-primary`).

## Architecture

```
 REST ingest ─┐   File upload ─┐   Live simulator ─┐
              └───────┬────────┴───────────────────┘
                      ▼
              Normalizer (JSONL / CSV / raw log)
                      ▼
              Event store (SQLite)
                      ▼
              Anomaly detector (robust z-score + signatures)
                      ▼
              Correlation (weighted pairs + union-find)
                      ▼
              Root cause · Impact · Timeline · Recommendations · Report
                      ▼
              REST + WebSocket → Next.js dashboard
```

Correlation weight: `w = .40·e^(-|Δt|/120) + .35·1/(1+hops) + .15·shared_ctx + .10·tfidf_cos`,
link if `w ≥ 0.45`. Root-cause score: `.35·earliness + .35·upstreamness +
.20·signature + .10·severity`, confidence = softmax(score / 0.15), with a
mandatory evidence list.

## Run it

```bash
cp .env.example .env
make setup        # venv + pip install + npm ci
make dev          # api on :8000, web on :3000 (two terminals: make api / make web)
# or one command:
docker compose up --build
```

On Windows, `make` is not required. Run the PowerShell setup script from the
repository root:

```powershell
.\setup.ps1
Copy-Item .env.example .env
Copy-Item frontend\.env.local.example frontend\.env.local
```

If PowerShell blocks local scripts, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Start the services in two PowerShell terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000 --app-dir backend
Push-Location frontend; npm run dev; Pop-Location
```

Then open http://localhost:3000, go to Sources, and start the simulator
(`db_pool_exhaustion`, 5× or 10×). A P1 incident appears with root cause
`postgres-primary`.

## Host it for free (Vercel + Render)

The cheapest reliable free split: **frontend on Vercel (Hobby, free)** and
**backend on Render (free tier)**. Do not put both on Render — two free
services would use ~1,440 instance-hours/month against Render's 750-hour
free allowance, and both would be suspended.

1. **Backend on Render** — sign in at render.com with GitHub, New → Web
   Service, pick this repo. Render reads `render.yaml` from the repo root:
   Python 3.11, build `pip install -e backend`, start
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`,
   health check `/health`. Note your API URL, e.g.
   `https://jarvis-api.onrender.com`.
   - Free tier limits: the service spins down after 15 minutes without
     traffic and takes about a minute to wake up on the next request, and
     the SQLite file is ephemeral — data is lost on restart. For this demo
     that is fine: re-run the simulator and the incident is rebuilt.
   - Open the API URL once after deploy to wake it up before the demo.
2. **Frontend on Vercel** — sign in at vercel.com with GitHub, Add New →
   Project, import this repo, set **Root Directory to `frontend`**. Add
   environment variables:
   - `NEXT_PUBLIC_API_URL` = your Render API URL (step 1)
   - `NEXT_PUBLIC_WS_URL` = `wss://<your-render-host>/ws/stream`
   Deploy. Vercel Hobby is free for personal, non-commercial projects
   (100 GB transfer, 1M function invocations/month).
3. **Point the API at the frontend** — in Render, set the API service's
   `CORS_ORIGINS` to your Vercel URL (e.g. `https://jarvis-xyz.vercel.app`)
   and redeploy the API. Without this, the browser blocks API calls.
4. Open your Vercel URL, go to Sources, start the simulator — the demo
   works exactly as it does locally.

Alternative if you want one host: Fly.io (free credit for new accounts) can
run the `docker-compose.yml` stack on one small VM, but its free allowance
is a trial credit, not a permanent free tier — Vercel + Render above is
the permanent-free option.

### Backend on Railway (works, but not free forever)

Yes, the backend runs on Railway — `backend/railway.json` and
`backend/Procfile` are in the repo. In Railway: New Project → Deploy from
GitHub repo → pick JARVIS, set the service's **Root Directory to `backend`**,
add variables `CORS_ORIGINS` (your Vercel URL), `SEED=42`, and optionally
`OPENROUTER_API_KEY` / `LLM_MODEL` (free model by default). Railway gives you a public URL and sets
`$PORT` itself. Then set Vercel's `NEXT_PUBLIC_API_URL` /
`NEXT_PUBLIC_WS_URL` to that Railway URL, as in step 2 above.

Cost warning: Railway has no permanent free tier for a running service.
New accounts get a one-time $5 trial credit (30 days); after that the
cheapest real option is Hobby at $5/month, and a small always-on service
typically costs a few dollars above the included credit. Use Railway for
the hackathon demo if you like it, but for a $0 long-term home, Render
(step 1) is the better pick.

## Demo script (3 minutes)

1. **Problem (20s):** a wall of raw alerts — login failures, slow APIs, failed payments.
2. **Ingest (30s):** upload `sample_data/payment_outage.log`, `curl` one event to
   `POST /api/v1/events`, click "Start simulator".
3. **Correlation (40s):** Overview shows the headline — "87 alerts → 2 incidents,
   97.7% noise reduced"; the unrelated CDN alert stays a separate P4 incident.
4. **Root cause (50s):** open the incident — the graph lights up red at
   `postgres-primary`; read the confidence and evidence lines, then "Why not
   the others?": payment-service lost because its first anomaly was 11s later
   and only 2 of 5 affected services depend on it.
5. **Timeline (20s):** replay the spread DB → payment → auth → gateway.
6. **Impact and fix (20s):** affected users, failed payments, and the estimated
   revenue impact (≈ ₹20,000 — an estimate, 40 failed payments × ₹500 assumed
   average order value), then the prioritized recommendations.
7. **Report (20s):** generated incident report, download it.
8. **Chaos (60s, the closer):** on Sources, "Break something" — let a judge pick
   a service and a fault, and watch J.A.R.V.I.S. find it live. Then show the
   Benchmark page: 225/225, 100%, 5.6s average detection.

## Golden test

```bash
.venv/bin/python -m pytest backend/tests -q   # 7 passed, incl. test_golden_db_pool_exhaustion
```

Scenario `db_pool_exhaustion` with `SEED=42` gives exactly one main incident,
root cause `postgres-primary`, confidence ≥ 0.70 (observed 0.78 live),
≥ 5 affected services, ≥ 30 users (observed 62), ≥ 30 failed transactions
(observed 40), plus a separate low-severity CDN cluster that is not merged.

## Scenarios

- `db_pool_exhaustion` (primary): pool exhaustion cascades to payment, auth, gateway, order, web-app.
- `bad_deploy`: auth-service deploy → login errors → gateway 5xx. Root cause `auth-service`.
- `cache_failure`: redis-cache down → auth latency → login failures. Root cause `redis-cache`.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| POST | `/api/v1/events` | Ingest one event or a list |
| POST | `/api/v1/ingest/upload` | File upload → `{accepted, rejected, errors}` |
| GET | `/api/v1/events` | Query events |
| GET | `/api/v1/incidents` · `/api/v1/incidents/{id}` | List / detail |
| GET | `/api/v1/incidents/{id}/report` | Markdown report (`?format=md\|json`) |
| POST | `/api/v1/incidents/{id}/ask` | Copilot Q&A grounded in the incident |
| PATCH | `/api/v1/incidents/{id}` | Update status |
| GET/PUT | `/api/v1/topology` | Service graph |
| POST | `/api/v1/simulator/start\|stop\|reset` | Simulator control |
| GET | `/api/v1/stats/overview` | KPIs |
| WS | `/ws/stream` | Live `event.ingested`, `incident.updated`, `simulator.progress` |

## Notes / known deviations

- **Template fallback:** the v0 "Dashboard – M.O.N.K.Y" template was not supplied
  (its fork/export is a human step), so the frontend uses the documented
  fallback scaffold in `design_system.md` §11 (Next.js + Tailwind + shadcn-style
  primitives, dark-first, semantic status tokens). See `docs/tokens-audit.md`.
  If the template export arrives later, re-run the token audit and swap the
  tokens in — the screens and components map 1:1.
- **CDN distractor timing:** the CDN events are at +120s in the scenario (not
  +20s as in specsheet §13). With the spec's 0.45 threshold, a +20s CDN event
  links to the web-app/payment events via the 1-hop `cdn → web-app` edge and
  merges. At +120s it stays a separate P4 cluster at every playback speed.
- **Simulator timestamps:** event timestamps are scenario start + scripted
  offset (not wall-clock at ingest), so correlation and the timeline are
  speed-independent.
- **No LLM key needed:** reports and Copilot fall back to a deterministic
  template / intent matching. Set `OPENROUTER_API_KEY` + `LLM_MODEL` for the
  LLM paths (structured incident JSON only, never raw logs). The default
  model is the free `meta-llama/llama-3.3-70b-instruct:free` on OpenRouter,
  so limited credits are safe; other free options include
  `deepseek/deepseek-r1:free` and `qwen/qwen-2.5-7b-instruct:free`.
- **Docker was not verified in this environment** (no Docker daemon here);
  `docker compose up --build` is the intended one-command start — verify it
  on the demo machine before the pitch.

## Standout features (added for the pitch)

- **Noise-reduction headline:** the Overview banner turns the alert stream into
  one line — "87 alerts → 2 incidents, 97.7% noise reduced" (`GET /stats/overview`
  returns `total_events`, `total_incidents`, `noise_reduction_pct`).
- **"Why not the others?":** every runner-up root cause ships with its score,
  its four factor values, and 1–2 plain-English reasons it lost, computed from
  the same scoring (first-seen delay, dependent count, missing signature, peak
  severity) — never invented. See `root_cause.alternatives[].why_not`.
- **Business impact:** the Impact card shows estimated revenue impact alongside
  users and failed payments. It is labelled an estimate everywhere: failed
  transactions × `avg_order_value_inr` (₹500, returned with the number).

## Chaos, benchmark, what-if, suspect changes

- **Fault injector / "Break something" (Sources page):** `POST /api/v1/simulator/inject`
  with `{service, fault_type, seed, speed}` makes the chosen service emit errors,
  then spreads symptoms to its dependents along the topology graph, one hop every
  ~8–20s, plus healthy noise. Fault types: pool_exhaustion, cache_failure,
  deploy_failure, oom, latency. Nothing is scripted per service — the engine has
  to find the injected service. Live check: injecting `cache_failure` into
  `redis-cache` produced 1 P1 incident, root cause redis-cache, confidence 0.84.
- **Benchmark (Benchmark page):** `POST /api/v1/benchmark/run` runs the injector
  across every service × every fault type, 5 seeds each (225 runs), and reports
  top-1 root-cause accuracy and average time to detect (scenario time, from the
  first anomalous event until the engine first names the injected service).
  Measured 2026-11-09: **225/225 correct, 100.0% accuracy, 5.6s average time
  to detect, 0 misses** — the full run table is on the page, misses included.
  A robustness probe with the shared trace id stripped also scored 225/225.
  Honest scope: this measures the engine on injected cascades built from the
  topology graph, not on wild production logs.
- **What-if replay:** `GET /api/v1/incidents/{id}/whatif?fix_at=30` re-counts the
  incident's own events after the fix time — no new data. The incident page has
  a slider ("fix applied at +N seconds"). S1 example: fixing at +30s would have
  avoided about 60 of 62 users and all failed payments (≈ ₹20,000). Labelled
  everywhere: "Simulation: assumes the fix works immediately."
- **Suspect-change marker:** deploy and config-change events (POST /events, or
  the "Record a change" card on Sources) are checked against each incident: a
  change within 10 minutes before the first error, on the root-cause service or
  a neighbour, adds a timeline marker and an evidence line, e.g. "Suspect:
  auth-service deploy v2.4.1 started, 5s before the first error." The score
  boost is a deliberately small +0.05, so the golden test stays at 0.78.

## Out of scope (roadmap)

Real agent-based collection, auth/multi-tenancy, automatic remediation
execution, ML model training. Roadmap: OpenTelemetry/Prometheus/Loki
connectors, learned topology from traces, a feedback loop to tune weights,
Slack/PagerDuty integration, runbook automation.
