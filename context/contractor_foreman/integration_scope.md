# DET Contractor Foreman Integration Project

## Overview
Automate data flows between Contractor Foreman (CF), Dropbox, Foundation (accounting), and Procore to eliminate manual re-entry and friction for field crews and PMs.

## Key People
- **John** — Owner/decision maker. Hates IT framing — pitch as time-saving/efficiency.
- **Andrew** — Field supervisor. Primary CF user. Also needs Dropbox access (field folders only).
- **Julie** — PM. Works in Dropbox, Foundation, Procore.
- **PMs** — Work primarily in Dropbox (office folder) and Procore. Set up jobs, manage budgets.
- **Field guys** — In Contractor Foreman daily. Enter time, view drawings, request materials.

## Systems
| System | Role | Access |
|--------|------|--------|
| Contractor Foreman | Field ops — time, drawings, materials, daily logs | Web app, browser automation (Playwright) |
| Dropbox | Document storage — job folders (field + office) | Business/Teams, Norm is admin, API available |
| Foundation | Accounting — budgets, payroll, job costing | SQL Server (hosted), direct DB access |
| Procore | GC-side project management | Used by GCs + PMs. API may be available. |
| Spreadsheets | Job bidding | Manual, pre-Foundation |

## Data Flows (Priority Order)

### 1. Drawings: Dropbox → Contractor Foreman
- **Current:** PM gets plans via email → saves to Dropbox job folder → manually uploads to CF
- **Automation:** Watch Dropbox field folders for new files → auto-upload to matching CF project
- **Tech:** Dropbox API (webhooks or polling) + Playwright CF upload
- **Impact:** High — eliminates double-handling of every drawing set

### 2. Time Cards: Contractor Foreman → Foundation
- **Current:** Field guys enter time in CF → someone manually enters into Foundation
- **Automation:** Extract time card data from CF → format → import to Foundation SQL
- **Tech:** Playwright CF extraction + Foundation SQL INSERT
- **Impact:** High — payroll/job costing accuracy, eliminates manual data entry
- **Note:** Need to understand Foundation's time card table structure

### 3. Material/Inventory: Warehouse → CF Material Database
- **Current:** Field guys request materials manually, no visibility into warehouse stock
- **Automation:** Load DET warehouse inventory into CF's material database so field can order from dropdowns
- **Tech:** Get inventory list (source TBD — spreadsheet? Foundation?) → Playwright CF material database entry
- **Impact:** High — John specifically requested this. Reduces material request friction.
- **John's words:** "Can we get our stuff into the database so guys could order material from Contractor Foreman within drop-downs?"

### 4. Budgets: Foundation → Contractor Foreman
- **Current:** Job bid on spreadsheet → won job → budget entered in Foundation (source of truth) → needs to be in CF
- **Automation:** Pull budget from Foundation SQL → push to CF project
- **Tech:** Foundation SQL SELECT + Playwright CF budget entry
- **Impact:** Medium — keeps field informed on budget status

### 5. Weekly Reports: CF → John
- **Current:** John wants to know "what was updated this week by job?"
- **Automation:** Pull weekly activity from CF, generate summary report
- **Tech:** Playwright CF data extraction → formatted report (email, PDF, or dashboard)
- **Impact:** Medium — visibility for John without logging into CF

### Future: Procore ↔ CF/Dropbox Sync
- GCs use Procore with similar info (drawings, RFIs, submittals)
- PMs work in Procore, field guys in CF
- Some drawings exist in both Procore and Dropbox
- TBD if field has moved away from Dropbox in favor of CF for drawings
- May need Procore API integration eventually

### Separate Project: Andrew's Power Track Reward System
- Details TBD — Norm will provide more info later

## Technical Approach
- **Playwright** (Python) for CF browser automation — login, navigate, upload, extract
- **Dropbox API** for folder watching — Norm is admin with API experience
- **Foundation SQL Server** for budget reads and time card writes
- Scripts in `tools/contractor_foreman/` per GOTCHA framework
- Start with CF login automation + one data flow, prove the pattern, then expand

## Dropbox Structure
```
Job Folder/
├── Field/     ← Andrew + field guys access this
└── Office/    ← PMs work here
```

## Open Questions
- [ ] What does CF's material database look like? Fields, import capability?
- [ ] Foundation time card table structure — what fields are required?
- [ ] Foundation budget table structure — what to pull?
- [ ] Inventory source — where is the warehouse stock list maintained today?
- [ ] Does CF have any API, or is browser automation the only path?
- [ ] Procore API access — do we have credentials?
- [ ] Which Dropbox job folders map to which CF projects? Naming convention?

---

*Created: 2026-02-14*
*Status: Scoping — not yet started*
