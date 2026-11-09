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

Then open http://localhost:3000, go to Sources, and start the simulator
(`db_pool_exhaustion`, 5× or 10×). A P1 incident appears with root cause
`postgres-primary`.

## Demo script (3 minutes)

1. **Problem (20s):** a wall of raw alerts — login failures, slow APIs, failed payments.
2. **Ingest (30s):** upload `sample_data/payment_outage.log`, `curl` one event to
   `POST /api/v1/events`, click "Start simulator".
3. **Correlation (40s):** Overview shows one P1 incident replacing dozens of
   alerts; the unrelated CDN alert stays a separate P4 incident.
4. **Root cause (50s):** open the incident — the graph lights up red at
   `postgres-primary`; read the confidence and evidence lines.
5. **Timeline (20s):** replay the spread DB → payment → auth → gateway.
6. **Impact and fix (20s):** affected users and failed payments, then the
   prioritized recommendations.
7. **Report (20s):** generated incident report, download it.

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
  template / intent matching. Set `ANTHROPIC_API_KEY` + `LLM_MODEL` for the
  LLM paths (structured incident JSON only, never raw logs).
- **Docker was not verified in this environment** (no Docker daemon here);
  `docker compose up --build` is the intended one-command start — verify it
  on the demo machine before the pitch.

## Out of scope (roadmap)

Real agent-based collection, auth/multi-tenancy, automatic remediation
execution, ML model training. Roadmap: OpenTelemetry/Prometheus/Loki
connectors, learned topology from traces, a feedback loop to tune weights,
Slack/PagerDuty integration, runbook automation.
