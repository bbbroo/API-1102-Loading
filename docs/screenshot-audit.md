# Screenshot Audit Matrix

Current README screenshots live in `docs/screenshots/` and are captured from the latest running FastAPI/Vite app with `scripts/capture-screenshots.mjs`. The `App Screenshots/` directory remains historical UI-reference and audit material; do not treat its `ezgif-frame-*` images as current application screenshots unless they are explicitly recaptured from the running app.

The reduced source set contains 68 screenshots in `App Screenshots/`. All images are `1274 x 1000`.

## UI Families

| Family | Screenshots | Matching requirements |
| --- | --- | --- |
| Dashboard | `ezgif-frame-001.jpg`, `ezgif-frame-004.jpg`, `ezgif-frame-010.jpg`, `ezgif-frame-016.jpg`, `ezgif-frame-020.jpg` equivalent states retained as `001/004/010/016` | Dark HDR header, two-row nav, title/action row, large tip panel, four metric cards, dense filter/action/table panel, recent projects below. |
| Projects | `ezgif-frame-025.jpg`, `031`, `037`, `043`, `044` | Same shell, project/calculation list panels, compact actions, bordered cards, documentation-status style badges. |
| Standards Tables | `048`, `052`, `054`, `055`, `056`, `057`, `060` | Read-only notice, stacked white standard sections, gray section headers, grouped grade/SMYS chips, weld seam chips, dense lookup table presentation. |
| References/About | `061`, `067`, `076`, `081`, `084`, `089`, `093`, `096`, `097`, `102`, `103`, `108`, `109` | Source standard list rows, document-like white panels, open/action links, HDR logo/about card. |
| Metadata/Scenarios | `115`, `117`, `118` | Scenario button row, scenario name field, metadata and documentation fields, no role/finalization workflow. |
| Highway Inputs | `121`, `122`, `125`, `126`, `129`, `130`, `131`, `133`, `134`, `135`, `138`, `139` | Two-tab loading strip, compact engineering forms, `A. Pipeline Geometry`, auto fields muted, info icons, schematic under inputs. |
| Railroad Inputs | `142`, `145`, `146`, `147`, `149`, `150`, `163`, `164`, `169`, `172`, `175`, `176` | Same input layout with railroad-specific fields, track count and surface pressure, railroad schematic. |
| Results/Advanced | `179`, `183`, `184`, `186`, `187`, `188` | Results summary table, controlling badge, utilization bars, advanced show panel, two-column intermediate calculation cards. |
| Report Preview | `195`, `200`, `201`, `205`, `208`, `212` | Toolbar, centered paper, HDR/title header, two-column report blocks, inputs/intermediate blocks, schematic, results, disclaimer. |

## Explicit Exclusions

- Do not include the screenshot role chip.
- Do not include finalization, approval, acknowledgment, or workflow-gating language.
- Status remains a documentation dropdown only.

## Current UI Deviations Addressed By This Pass

- Replace single-file generic prototype layout with screenshot-matched reusable components.
- Replace raw JSON standards display with grouped read-only standards cards.
- Rebuild dashboard, workspace, results, advanced calculation, and report preview composition.
- Align colors, borders, spacing, button sizing, panels, tables, tabs, badges, and form density with the screenshots.
