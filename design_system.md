# design_system.md — J.A.R.V.I.S. Design System (Revision 2: built on "Dashboard – M.O.N.K.Y")

Base template: Vercel v0 community template **Dashboard – M.O.N.K.Y** by JOYCO — https://v0.app/templates/b7GDYVxuoGC
Described by its page as: integrated chat, custom design system, multi-view layout, collapsible sidebar and top bar, dark mode by default. Stack: Next.js, Tailwind CSS, shadcn/ui.

---

## 0. How to use this file

**Template-first rule.** The M.O.N.K.Y code is the visual source of truth. This file does not replace its look. It does four things:

1. Tells you how to **audit and reuse** the template's own tokens (§2).
2. Adds a small **semantic status layer** for incident states the template does not have (§3).
3. **Maps** the template's shell and components onto J.A.R.V.I.S. screens (§6).
4. Defines the **custom components** the template lacks: root-cause panel, causal graph, timeline, confidence meter (§7).

**Important:** the exact hex values, fonts and radii of the template were not inspected when this file was written. Do not invent them. Read them from the code in the token audit (§2) and record them in `docs/tokens-audit.md`. Where this file gives hex values, they are **defaults for the semantic layer only**, to be tuned after the audit.

If the template cannot be imported for any reason, use the fallback in §11 and tell the human.

---

## 1. Design direction

Keep the template's identity: dark-first, studio-crafted, punchy but structured. J.A.R.V.I.S. adds one idea on top: **the root cause is the only loud thing on screen.** Everything else stays quiet so the cause reads instantly.

**Principles**
1. **One loud element per screen.** Red is reserved for root cause and critical severity.
2. **Structure carries meaning.** Borders, rails, lanes and dashes encode role (cause / affected / at risk). No decoration for its own sake.
3. **Explain, don't just score.** Every number sits next to its reason (confidence + evidence).
4. **Never color alone.** Every status has an icon and a text label.
5. **Plain language.** "Why we think this", not "Evidence vector".

**Do not**
- Restyle the template's shell, spacing rhythm, radii, fonts or animation language.
- Add a new typeface, a second accent color or extra glow/gradient effects.
- Hard-code hex values in components. Use tokens/Tailwind classes only.
- Leave template demo content (sample pages, fake data, placeholder branding) in the product.

---

## 2. Token audit (do this first — Phase 0b)

Read these files in the forked template and write the results to `docs/tokens-audit.md`:

- `app/globals.css` (CSS variables for light/dark)
- `tailwind.config.*` (extended colors, radius, fonts, animation)
- `components.json` (shadcn config)
- `components/ui/*` (which primitives exist: button, card, badge, table, tabs, tooltip, dialog, sheet, scroll-area, input, select, sidebar…)
- Shell/layout files (`app/layout.tsx`, sidebar, top bar, chat component)

Record:

| Item | What to capture |
|---|---|
| Surfaces | page background, panel/card, raised/popover (names and values) |
| Text | primary, muted, disabled |
| Lines | border/divider color and width |
| Accent | primary/accent color and where the template uses it |
| Radius | scale and which components use which |
| Type | font families, size scale, weights, any uppercase/tracking conventions |
| Spacing | page gutter, card padding, grid gaps, sidebar width, top bar height |
| Elevation/glow | shadows, rings, blur |
| Motion | durations, easing, any ambient animation |
| Inventory | which shadcn components and which template-specific components exist |

Rule: **if the template defines a token, use it; do not duplicate it.** Only add what the audit shows is missing.

---

## 3. Semantic status layer (additions)

Add to `app/globals.css`, scoped under the same selectors the template uses for its dark theme (and light theme if it has one). Defaults below are tuned for dark surfaces; adjust hue/saturation to sit with the template's palette after the audit, but **keep the semantic meaning** (red = cause, amber = affected, green = healthy, blue = selection/propagation).

| Token | Default (dark) | Use |
|---|---|---|
| `--cause` | `#FF5A47` | Root cause, P1, critical errors (the one loud color) |
| `--cause-wash` | `rgba(255,90,71,.14)` | Tint behind cause elements |
| `--cause-ink` | `#FF8A7A` | Red text on dark surfaces |
| `--affected` | `#F5A524` | Affected / degraded services, P2/P3 |
| `--affected-wash` | `rgba(245,165,36,.14)` | Tint for affected rows |
| `--affected-ink` | `#FFC766` | Amber text |
| `--steady` | `#3DD68C` | Healthy |
| `--steady-wash` | `rgba(61,214,140,.12)` | Healthy tint |
| `--trace` | `#5B8DEF` | Selection, causal edges, focus ring |
| `--trace-wash` | `rgba(91,141,239,.16)` | Selection tint |
| `--unmapped` | `#8B93A1` | Unknown services, resolved items |

Expose them in Tailwind (`cause`, `affected`, `steady`, `trace`, `unmapped` with `DEFAULT`, `wash`, `ink`).

**Conflict rule:** if the template's own accent is red/orange (or close to `--cause`), demote the template accent to neutral in navigation and selection states so that **red appears only on cause elements**. Selection uses `--trace`.

**Severity mapping:** P1 filled `--cause` · P2 filled `--affected` · P3 outlined `--affected` · P4 outlined `--unmapped`. Always pair with icon and word (Critical / High / Medium / Low).

**Contrast:** verify after tuning: text ≥ 4.5:1 on its surface, graphical objects ≥ 3:1.

---

## 4. Typography

Use the template's font families and scale. Additions:
- Monospace only for literal machine output (log messages, trace IDs, curl snippets). Use the template's mono if it has one.
- `font-variant-numeric: tabular-nums` on every number that updates live.
- KPI and confidence figures use the template's largest numeric style.
- Our own copy is sentence case with no tracked-out uppercase labels. Template chrome that is already uppercase can stay as is.
- Prose (report, evidence) max line length ~70 characters.

---

## 5. Shape, spacing, elevation

- Reuse the template's radius scale, spacing rhythm and card style for all new components.
- Hierarchy by treatment, not by new shapes: the **root-cause panel** is the one component with extra emphasis (a 4px `--cause` left rail and the template's strongest elevation/ring). Everything else uses the standard card.
- Graph nodes use the template's smallest radius (services are boxes, not bubbles).
- No new shadows or glows beyond what the template already uses.

---

## 6. Shell and layout mapping

| Template piece | J.A.R.V.I.S. use |
|---|---|
| Collapsible sidebar | Nav: Overview, Incidents, Sources, Topology. Collapsed state shows icons with tooltips. Remove all template demo links. |
| Top bar | Page title/breadcrumb, **live connection indicator** ("Live" / "Reconnecting…"), simulator quick control (scenario chip + play/stop), theme toggle if present |
| Multi-view layout | `/` Overview · `/incidents/[id]` Incident detail · `/sources` Data sources · `/topology` Topology |
| Integrated chat | **Copilot** ("Ask J.A.R.V.I.S."): docked panel on the incident page, grounded in that incident's data (specsheet §12.3) |
| Cards, tables, charts | KpiStrip, EventTable, sparklines, ImpactCard |
| Custom design system | Source of all tokens (§2) |

### Overview
```
┌──────┬────────────────────────────────────────────────────────┐
│ side │ Overview                    ● Live   [db_pool ▸ Start] │
│ bar  ├────────────────────────────────────────────────────────┤
│      │  3 open │ 5 services affected │ 412 events/min │ 38s    │
│      ├───────────────────────────────┬────────────────────────┤
│      │ Incidents                     │ Live events            │
│      │ ┃P1 Payment DB exhausted      │ 10:15:47 gateway 504   │
│      │ ┃   5 services · 62 users     │ 10:15:46 auth login_f. │
│      │ ┃P4 Slow image delivery (cdn) │ ...                    │
│      ├───────────────────────────────┴────────────────────────┤
│      │ Service health map (mini graph)                        │
└──────┴────────────────────────────────────────────────────────┘
```

### Incident detail (hero screen)
```
┌──────┬──────────────────────────────────────────┬─────────────┐
│ side │ P1 · Payment platform degraded by DB     │ Impact      │
│ bar  │ Open · started 10:15:02 · 4m 12s         │ 5 services  │
│      ├──────────────────────────────────────────┤ 62 users    │
│      │ ┃ Most likely cause                      │ 41 payments │
│      │ ┃ postgres-primary  ████████░░ 91%       │             │
│      │ ┃ Why we think this                      │ Fixes       │
│      │ ┃  • First anomaly, 23s before the rest  │ 1 Raise pool│
│      │ ├──────────────────────────────────────  │ 2 Kill idle │
│      │ │ CAUSAL GRAPH  [pg]━▶[pay]━▶[gw]        │ 3 Find leak │
│      │ ├──────────────────────────────────────  │             │
│      │ │ TIMELINE  ▶ ─●──●───●────●─────        │ [Ask J.A.R.V│
│      │ └ Tabs: Events · Report                  │  .I.S. ▸]   │
└──────┴──────────────────────────────────────────┴─────────────┘
```
Alignment: left-aligned content; numbers right-aligned in tables; KPI figures left-aligned with label beneath.
Responsive: sidebar collapses to icons on tablet, to a sheet on mobile; right column stacks under the main column.

---

## 7. New components (built from template primitives)

Build each from the template's shadcn primitives (Card, Badge, Table, Tabs, Tooltip, Sheet, ScrollArea…). Props typed; states listed.

**IncidentRow** — severity pill, title, one-line summary ("5 services · 62 users · 12m"), root-cause service chip. 4px left rail in severity color. Hover/selected use template hover and `--trace-wash`. Resolved: muted.

**SeverityPill** — `P1…P4` + icon (▲ P1/P2, ● P3, ○ P4) + `aria-label="Severity P1, critical"`.

**RootCausePanel** — the hero. Service name, label, `ConfidenceMeter`, "Why we think this" (max 5 one-sentence bullets), collapsed "Other candidates". 4px `--cause` left rail, `--cause-wash` header strip. Uncertain (<50%): rail becomes `--affected`, title "Root cause uncertain", show top three candidates.

**ConfidenceMeter** — 10 segments + large numeric value ("91%"). Filled `--cause`, empty = template border color. Fills once on first view (300ms); respects reduced motion.

**ServiceNode / CausalGraph (React Flow)** — node 160×56, icon by kind, name, status line.
- Root cause: 3px `--cause` border, `--cause-wash` fill, one slow pulse ring (2.4s loop) — **the only ambient animation we add**.
- Affected: 2px `--affected` border + wash. At risk: 2px dashed `--affected`. Healthy: 1px template border + `--steady` dot. Unmapped: dotted `--unmapped`. Selected: 2px `--trace` outline.
- Edges: 1.5px template border color by default; propagation path 2.5px `--trace` with arrowhead from cause to dependents and a lag label ("+11s").
- Layered layout by `tier`. Provide "View as list" toggle for accessibility.

**Timeline** — one lane per service ordered by first anomaly. Markers: ● warning, ◆ error/critical, ▪ deploy/info. Playhead 2px `--trace`; scrubbing updates graph state. Controls: play/pause, 1×/5×/10×, jump to start. Keys: arrows step, space toggles.

**ImpactCard** — three big figures (services, users, failed transactions) + "Critical path affected" row with icon and text.

**RecommendationItem** — ordered index (a real sequence), title, one-line detail, risk tag (low/medium/high text), copy button, expandable rationale, source label ("Rulebook" / "AI-assisted").

**EventTable / LogLine** — template table; mono message; severity icon; relative time (absolute on hover); service chip. Anomalous rows `--affected-wash`; rows matching the selected node `--trace-wash`. Virtualize beyond 200 rows.

**KpiStrip** — four figures; open-incidents figure uses `--cause-ink` only if a P1 is open.

**SourceCard** — File (dropzone + parse result "1,240 accepted · 6 skipped"), API (copyable curl), Simulator (scenario select, speed segmented control, Start/Stop/Reset).

**ReportView** — rendered Markdown, ~70ch, "Regenerate" and "Download report" actions, badge "Written by AI" or "Generated from template".

**CopilotPanel** — uses the template's chat component. Header "Ask J.A.R.V.I.S." plus the incident title; 3 suggestion chips ("Why postgres-primary?", "Who is affected?", "What should I do first?"); answers show a small "Based on this incident's data" note. Fallback answers work with no API key.

**Empty / error / loading**
- Empty overview: "No incidents yet. Start the simulator or upload a log file." + two buttons.
- Upload error: "3 lines couldn't be read. Lines must start with a timestamp, level and service name. See example."
- Loading: skeletons matching the final layout (template skeleton if present).
- Stream lost: banner "Live updates paused. Reconnecting…" using `--affected-wash`.

---

## 8. Motion

- Follow the template's motion language everywhere.
- Our only ambient addition: the root-cause pulse ring.
- Response motion (user-triggered): timeline replay edge drawing (400ms, in sequence), panel expand/collapse, confidence fill on first view.
- `prefers-reduced-motion: reduce`: disable the pulse, make edge drawing instant.
- No staggered entrances, no hover lift on cards.

---

## 9. Copy

- Sentence case, active voice, plain verbs. "Most likely cause", not "RCA result".
- Buttons say exactly what happens: "Start simulator", "Regenerate report", "Download report". Confirmations reuse the verb: "Report regenerated".
- Errors say what happened and how to fix it. No apologies.
- Numbers always have units and nouns: "62 users", "41 failed payments", "p95 latency 2.3 s".
- Wordmark `J.A.R.V.I.S.` in the sidebar header only.

---

## 10. Accessibility

- Keep the template's focus ring; if absent, add 2px `--trace` with 2px offset.
- Status = icon + text + color. Graph nodes: `aria-label="payment-service, affected, first seen 10:15:13"`.
- Graph has a list-view alternative. New P1 incidents announced via `aria-live="polite"`.
- Hit targets ≥ 40px on touch; works down to 360px wide.
- Never rely on glow or blur to convey state (contrast on dark surfaces must hold without it).

---

## 11. Template cleanup and fallback

**Cleanup checklist (Phase 0b)**
- [ ] Remove template demo routes, sample data, placeholder images and unused components
- [ ] Replace branding with the J.A.R.V.I.S. wordmark; update page title, metadata and favicon
- [ ] Remove unused dependencies; keep `package.json` clean
- [ ] Keep the shell (sidebar, top bar, layout), tokens, UI primitives and chat component
- [ ] App still builds (`npm run build`) after cleanup

**Fallback if the template cannot be imported:** scaffold Next.js (App Router) + Tailwind + shadcn/ui in dark mode with this minimal token set and tell the human:
`--background #0E1116 · --card #151A21 · --raised #1C222B · --border #2A323D · --foreground #E8ECF1 · --muted-foreground #9AA4B2 · --accent #5B8DEF`, plus the semantic layer from §3. Font: Geist (Next.js default) for UI and Geist Mono for logs.

---

## 12. Quality checklist (run before demo)

- [ ] Looks like the template: spacing, radii, fonts, and motion unchanged
- [ ] Only one red element dominates each screen
- [ ] No status is conveyed by color alone
- [ ] Every number has a unit and a plain-language label
- [ ] Empty, loading, error and disconnected states exist for each page
- [ ] Keyboard: open an incident, play the timeline, copy a recommendation without a mouse
- [ ] Works at 1280px (projector) and 390px (phone)
- [ ] Reduced-motion setting respected
- [ ] No template demo content left
