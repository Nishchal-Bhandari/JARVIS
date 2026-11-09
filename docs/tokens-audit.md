# Tokens audit (design_system §2)

## Status
The v0 template "Dashboard – M.O.N.K.Y" (https://v0.app/templates/b7GDYVxuoGC)
was **not supplied** with this repo — no `frontend/` export was provided, and
the human step in skillbuild Phase 0 (fork/export in v0) was not done.
Per design_system §11, the fallback scaffold was used instead.

## Fallback tokens (in `frontend/app/globals.css`)
| Item | Value |
|---|---|
| Surfaces | `--background #0E1116` · `--card #151A21` · `--raised #1C222B` · `--border #2A323D` |
| Text | `--foreground #E8ECF1` · `--muted-foreground #9AA4B2` |
| Accent | `--accent #5B8DEF` (selection/propagation, `--trace`) |
| Radius | `--radius 0.625rem` |
| Type | Geist (UI) / Geist Mono (logs) — Next.js defaults, no new typeface added |
| Spacing | Sidebar 224px, page gutter 24px, card padding 16px |

## Semantic status layer (design_system §3, in `globals.css` + Tailwind)
`--cause #FF5A47` / wash / ink, `--affected #F5A524`, `--steady #3DD68C`,
`--trace #5B8DEF`, `--unmapped #8B93A1`. Red is used only on root-cause /
critical elements.

## Reusable components (hand-built to the fallback shell)
shadcn-style primitives in `frontend/components/ui/`: Card, Button, GhostButton,
Badge. J.A.R.V.I.S. components in `frontend/components/jarvis/`: IncidentRow
(in Overview), SeverityPill, RootCausePanel, ConfidenceMeter, ServiceNode /
CausalGraph (React Flow), Timeline, ImpactCard, RecommendationItem, EventTable,
KpiStrip (in Overview), SourceCard (in Sources), ReportView (in incident tabs),
CopilotPanel.

## If the real template arrives later
Re-run the audit against its `app/globals.css`, `tailwind.config.*`,
`components.json` and `components/ui/*`, replace the fallback tokens with the
template's own tokens, and keep the semantic layer above.
