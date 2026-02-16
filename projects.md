# Active Projects

> Persistent project tracking across sessions. Each project groups related tasks.

---

## Network Security & Pi-hole

**Status:** In Progress
**Started:** 2026-02-04
**Goal:** Harden home network with geo-blocking, ad blocking, and private DNS

**Hardware:**
- UXG Max (gateway) - Pi-hole plugged directly into this
- U6 LR switch
- U7 Pro Wall AP
- U6 LR AP
- Raspberry Pi (Pi-hole)

**Tasks:**
- [x] #14 - Upgrade UniFi to Zone-Based Firewall (completed 2026-02-05)
- [x] #15 - Configure geo-blocking — 30 countries, inbound + outbound (completed 2026-02-05)
- [x] #10 - Flash DietPi to SD card (completed 2026-02-05)
- [x] #11 - Boot Pi, verify SSH from Mac (completed 2026-02-05)
- [x] #16 - Set static IP for Pi (192.168.1.115) (completed 2026-02-05)
- [x] #12 - Install AdGuard Home (replaced Pi-hole) (completed 2026-02-05)
- [x] #13 - Install Unbound (recursive DNS) (completed 2026-02-05)
- [x] #8 - Configure blocklists — OISD, URLhaus, Phishing Army, DandelionSprout (completed 2026-02-05)
- [x] #9 - Point UniFi DHCP to AdGuard (completed 2026-02-05)
- [x] #18 - Enable IPS with active prevention (completed 2026-02-05)
- [x] #19 - Enable Honeypot (completed 2026-02-05)
- [ ] #17 - DNS redirect rule for hardcoded devices
- [x] #20 - Review AdGuard Home advanced config (completed 2026-02-06)
  - Enabled DNSSEC
  - Min TTL override: 300 (5 min floor)
  - Max TTL override: 86400 (24 hr ceiling)
  - Enabled optimistic caching
  - Rate limit left at 20/sec (intentional safety net)
  - Reverse client IP resolving already enabled
  - Fallback/bootstrap DNS left empty (Unbound is local, no need)
- [ ] #21 - Uninstall Honey extension from Emily's PC (she thought she removed it, still making DNS calls to joinhoney.com)
- [ ] #22 - DNS log audit: export AdGuard query log, run agent team (scanner/researcher/reporter) to triage domains — flag tracking, bloatware, suspicious calls, per-device cleanup recommendations
- [x] #23 - Move MacBook from UXG Max to switch (completed 2026-02-06)

**References:**
- AdGuard config docs: https://github.com/AdguardTeam/AdGuardHome/wiki/Configuration#upstreams

**Notes:**
- AdGuard settings fully reviewed 2026-02-06: encryption not needed (LAN only), DHCP stays on UXG Max, client settings available for per-device rules (future), filter update interval set to 12h
- Switched from Pi-hole to AdGuard Home (more modern, better UI)
- Using DietPi as the OS (lightweight)
- Unbound for recursive DNS (no third-party DNS providers)
- AdGuard web UI at http://192.168.1.115:8083 or http://adguard.lan:8083
- Pi hardware: Raspberry Pi 3 Model B+ on 192.168.1.115

**Security Stack:**
- Zone-based firewall
- Geo-blocking: 30 countries (inbound + outbound)
- IPS: Active prevention (gaming rules disabled for daughters)
- Honeypot: Enabled
- DNS filtering: AdGuard + 5 blocklists (~590K rules)
- Recursive DNS: Unbound (no Google/Cloudflare)

**Blocklists:**
- AdGuard DNS filter (145K)
- OISD Big (267K)
- Phishing Army (156K)
- DandelionSprout Anti-Malware (15K)
- URLhaus (8K)

---

## Claude Atlas Framework

**Status:** Active (ongoing)
**Started:** 2026-02-04
**Goal:** AI-powered investment research and automation

**Architecture (Simplified 2026-02-05):**
- Claude Opus 4.6 = orchestrator + synthesizer + reasoner
- Grok (xAI) = optional X/social sentiment (only external LLM)
- Alpaca MCP = live market data
- Deterministic tools = technical indicators, data aggregation
- Claude Code subagents = specialized Opus 4.6 instances

**Retired (Opus 4.6 makes these redundant):**
- ~~Codex (GPT-4o)~~ — Claude does code natively
- ~~Gemini (Google)~~ — Claude handles synthesis with full context
- ~~Qwen (local MLX)~~ — unnecessary laptop overhead

**Completed:**
- [x] Multi-agent LLM system setup
- [x] Pipeline orchestrator with handoffs
- [x] Market data integration (Alpaca)
- [x] Technical indicators tool
- [x] Memory system with RAG
- [x] Simplify to Claude-centric architecture (2026-02-05)
- [x] Create market-researcher subagent (2026-02-05)

---

## Dark Web Credential Cleanup

**Status:** In Progress
**Started:** 2026-02-05
**Goal:** Review and remediate all breach alerts from NordVPN and LastPass, complete password manager migration

**Context:**
- NordVPN Dark Web Monitor: 12 alerts
- LastPass Security Dashboard: additional alerts (TBD)
- Currently using two password managers — migrating from LastPass to 1Password
- None appear recent, but need review and cleanup
- Opportunity to strengthen overall credential hygiene

**Tasks:**
- [ ] #6 - Review all 12 NordVPN Dark Web Monitor alerts
- [ ] #11 - Review LastPass Security Dashboard alerts
- [ ] #7 - Prioritize accounts by risk level
- [ ] #8 - Change passwords for affected accounts
- [ ] #9 - Enable 2FA on all critical accounts
- [ ] #10 - Check for unauthorized account activity
- [ ] #12 - Complete migration from LastPass to 1Password

**Notes:**
- Critical accounts (financial, email) get priority
- All new/changed passwords go into 1Password (not LastPass)
- Prefer authenticator app over SMS for 2FA
- Good time to delete old/unused accounts during cleanup

---

## Automatic Conversation Logging

**Status:** In Progress
**Started:** 2026-02-05
**Goal:** Automatically capture every user message and assistant response to persistent transcript files using Claude Code hooks — no manual intervention required

**Problem Solved:**
- Conversation context lost on restart/new session
- Relying on Claude to remember to log is unreliable
- Summaries lose important detail

**Architecture:**
- Claude Code hooks fire on `UserPromptSubmit` (user message) and `Stop` (assistant done)
- Python script reads hook input, extracts messages, appends to transcript
- Transcripts stored at `memory/transcripts/YYYY-MM-DD.md`

**Tasks:**
- [ ] #1 - Research Claude Code hooks input format
- [ ] #2 - Build conversation_logger.py script
- [ ] #3 - Configure hooks in settings.json
- [ ] #4 - Test conversation logging end-to-end
- [ ] #5 - Document conversation logging system

**Files:**
- `tools/memory/conversation_logger.py` — main script (to be created)
- `.claude/settings.json` — hook configuration
- `memory/transcripts/` — output directory

---

## DET Projects Board

**Status:** Active
**Started:** 2026-02-06
**Live URL:** https://det-projects-wwvu5.ondigitalocean.app

**Known Bugs:**
- [ ] #24 - Modal click-through bug: after editing a task and closing the modal, clicking other tasks no longer opens the edit modal. Requires page refresh. Likely React state issue — modal overlay not unmounting, or selectedTask/isModalOpen state not resetting on close. Julie and Norm both reproduced it.

**Tasks:**
- [ ] #25 - SMS notification when a task is assigned/reassigned to someone (replaces SendGrid email idea — less friction than email)

**Notes:**
- John gave the go-ahead for the Kanban board

---

## Electrical Work Photo Inspection (AI Vision)

**Status:** Research / Concept
**Started:** 2026-02-06
**Requested by:** John Dixon
**Goal:** Train an AI agent to review job site photos and identify electrical code compliance issues before inspector visits

**Use Case:**
- Foremen take daily progress photos (ceiling cavities, walls, conduit runs)
- AI agent reviews photos and flags potential code violations
- Pre-inspection QA tool — catch issues before the inspector does

**What the agent should detect:**
- [ ] Conduit properly strapped (correct intervals per NEC)
- [ ] Lighting whips strapped
- [ ] All wires terminated correctly
- [ ] Junction boxes have covers
- [ ] Proper grounding visible
- [ ] General workmanship / obvious violations

**Approach:**
- Multimodal vision model (Claude Opus, GPT-4V, or Gemini)
- Context layer with NEC code requirements for relevant sections
- Reference library: 20-30 annotated photos (good vs bad) from John
- Checklist output per photo: pass, flagged, needs closer look
- NOT a replacement for licensed inspection — pre-inspection QA only

**Tasks:**
- [ ] #26 - Research: test Claude vision with sample electrical work photos to gauge baseline accuracy
- [ ] #27 - Build NEC code reference context file (strapping, termination, box covers, grounding)
- [ ] #28 - Get annotated reference photos from John (good and bad examples)
- [ ] #29 - Build photo inspection goal + hard prompt
- [ ] #30 - Prototype: upload photo → get compliance checklist

**Notes:**
- Image quality is critical — dark ceiling shots may need flash or better lighting
- Local code amendments may differ from NEC baseline — need to confirm jurisdiction
- John would initially walk the agent through photos to build its understanding

---

## Foundation Invoice Routing & AP Automation

**Status:** Planning
**Started:** 2026-02-09
**Source:** Julie interview + Norm notes
**Goal:** Route Foundation invoices to the correct project manager (not all to John), then progressively automate the AP pipeline

### Current Workflow (Manual)
1. Vendor (e.g., Capital Electric) emails invoice PDFs to **ap@dtech.org**
2. **Leanna** opens AP email, downloads PDFs — a single email often contains invoices for multiple jobs
3. Leanna separates PDFs by job
4. Separated invoices go into a **Dropbox (Business/Teams) invoices folder**
5. Project coordinators (**Jennifer** and **Caitlin**) are each assigned different jobs — they pick up invoices from Dropbox
6. Jennifer/Caitlin enter invoices into **Foundation** (construction accounting software)
7. Foundation routes the invoice to **John** for approval (this is the problem — should go to the PM assigned to that job)
8. After approval, goes to **Leanna or Julie** for payment

### Desired State
- Invoices route to the **correct PM** based on Foundation's job-to-PM assignment
- Foundation has a field/table mapping PMs to jobs — need to find it
- Eventually: automate the entire AP pipeline (email parsing, PDF separation, Dropbox filing, AI-assisted review)

### Technical Assets
- **Foundation back-end:** SQL Server (hosted, not on-prem)
- **Foundation access:** Via customer portal at https://www.foundationsoft.com/clients/ — Julie signs in through there now (used to be glitchy, now stable)
- **Foundation customer portal:** Norm has access — routing docs should be in here
- **Foundation demo database:** Available for testing — Julie will enter sample data
- **Foundation modules:** Most modules active (no warehouse/inventory mgmt)
- **Routing config:** Done through Foundation UI (not SQL) — Norm set up original routing but doesn't remember the steps
- **Dropbox Business API:** Previously had an app for folder permission audits — API access is feasible
- **AP email:** ap@dtech.org — potential for email parsing automation later
- **Norm had read-only SQL Server access** previously — needs to recover credentials

### Job Numbers
- Every job in Foundation has a job number (Foundation is source of truth)
- Job number format likely based on year + GC
- Dropbox folder naming mirrors this: GC-[job number or year]
- Jennifer/Caitlin enter the job number when entering invoices — this is the key field linking to PM assignment

### People
- **John Dixon** — Owner, currently receives ALL invoice approvals (bottleneck). Smartest and hardest-working person at the company. This project exists to take load off him.
- **Leanna** — AP inbox, separates PDFs, handles payment after approval
- **Julie** — Handles payment after approval, provided project info, will set up demo data
- **Jennifer** — Project coordinator, enters invoices for her assigned jobs
- **Caitlin** — Project coordinator, enters invoices for her assigned jobs
- **PMs (6 total):** John Dixon, Devin, Johnny, Newly, Alfredo, John Stiltner
- PMs sometimes collaborate on jobs (e.g., John assists Devin), but in Foundation it's always **one PM per job** — no shared assignments

### Phases

**Phase 1 — Quick Win: Fix Routing in Foundation**
- [x] #31 - Open Controls > Routing Rules in Foundation — DONE 2026-02-10
- [x] #32 - Review existing Rule 1 — DONE: single catch-all rule routes ALL invoices to John Dixon regardless of PM/job
  - Rule: When Added + Entered by Katlin/Julia/Leanna/Jennifer → Route to John Dixon
  - No PM filter, no job filter — everything goes to John
- [x] #33 - Check PM user accounts — BLOCKER FOUND: only 3 of 6 PMs have Foundation user accounts
  - **Have accounts:** John Dixon (JDixon), John Stiltner (JStiltner), Johnny (JNguyen)
  - **No accounts:** Devin, Newly, Alfredo Rojas (AROJAS exists as PM value but not as user)
  - Norm has admin access to create users but will not create them — Julie's call
- [ ] #34 - Talk to Julie: confirm plan to test routing for Stiltner + Johnny first, decide what to do for PMs without accounts
- [x] #35 - Create routing rule for John Stiltner — DONE 2026-02-10
- [x] #36 - Create routing rule for Johnny Wynn — DONE 2026-02-10
  - Both rules live in production. Waiting for new invoices to be entered to verify routing works.
- [ ] #37 - Keep original Rule 1 as catch-all (everything else still goes to John Dixon)
- [ ] #38 - Test in Foundation demo database (Julie to enter sample invoices)
- [ ] #39 - Decide notification method: per-invoice email or daily digest
- [ ] #40 - Deploy routing rules to production Foundation
- [ ] #41 - Train PMs on Daily Document Manager workflow (approve/revise/reject)

**Routing Rules Discovery (2026-02-10):**
- Record Type: A/P Invoice
- "Related to Record Type" dropdown options: Geographic Area, Job, Project Class, **Project Manager**, Vendor
- Selecting "Project Manager" lets you filter by PM in "Related to Record Value"
- Available Foundation users for routing: JDoby, JDixon, JStiltner, JNguyen, Julia Greene, Katlin Greene-U, Leanna Dixon, NormV, processor1, Processor2, roger
- Entered By users (coordinators): Katlin Greene-U, Julia Greene, Leanna Dixon, Jennifer Doby

**Phase 2 — Dropbox + Data Access Integration**
- [ ] #41 - Set up Dropbox Business API access (OAuth app)
- [ ] #42 - Map Dropbox invoices folder structure (GC-[job#/year] naming convention)
- [ ] #43 - Recover Norm's read-only SQL Server access to Foundation database
- [ ] #44 - Connect to Foundation SQL Server from Claude/scripts
- [ ] #45 - Build tool to cross-reference Dropbox invoices with Foundation job/PM data
- [ ] #46 - Set up Foundation batch folders linked to Dropbox (auto-populate batch window in Document Imaging)

**Phase 3 — Full AP Pipeline Automation (Two Paths)**

*Path A — PDF Email Pipeline (most vendors):*
- [ ] #47 - Email parsing: connect to ap@dtech.org via Microsoft Graph API (MS 365)
- [ ] #48 - PDF separation: AI splits multi-job invoice PDFs by job number
- [ ] #49 - Auto-file separated invoices to correct Dropbox folder via API
- [ ] #50 - AI-assisted invoice review: flag discrepancies, suggest approvals, highlight items for PM attention

*Path B — EDI/XML Pipeline (high-volume vendors like Graybar):*
- [ ] #51 - Contact Graybar eChannel team about EDI/XML invoice integration
- [ ] #52 - Evaluate which other major vendors offer EDI/XML
- [ ] #53 - Build EDI/XML parser to extract structured invoice data (job#, amounts, PO refs)
- [ ] #54 - Route structured invoices directly into Foundation or Dropbox folders

**Technical Assets:**
- DET email: Microsoft 365 (ap@dtech.org)
- Dropbox: Business/Teams — Norm is admin, has API experience
- Graybar offers: EDI, XML, FTP/SFTP/email/VAN transmission (docs/GraybaR/)
- Foundation back-end: SQL Server (hosted)

### Future: Job Financials Dashboard (after routing is complete)
- **John's long-term wish:** Public dashboard on a monitor in the work area
- Shows all active jobs with financial summaries — profitability, on track vs over budget, margins
- Visible to everyone (read-only, no login required)
- Depends on Foundation SQL Server access (read-only) — same access we need for Phase 2
- Once we understand Foundation's job cost tables, this becomes a straightforward data viz project
- Tech options: simple web app pulling from SQL Server on a refresh interval, displayed on a wall-mounted monitor
- **Blocked by:** Foundation routing project completion + SQL Server access

### Notes
- Foundation Software is a construction-specific accounting platform (common in electrical/mechanical contractors)
- SQL Server back-end means we can query job data, PM assignments, invoice status directly
- Demo database is critical — all experimentation happens there before touching production
- Dropbox Business (Teams) — not personal Dropbox. API access requires admin-level OAuth app

---

*Last updated: 2026-02-14*

---

## DET Contractor Foreman Integration

**Status:** Scoping
**Started:** 2026-02-14
**Goal:** Automate data flows between Contractor Foreman, Dropbox, Foundation, and Procore to eliminate manual re-entry

**Scope doc:** `context/contractor_foreman/integration_scope.md`

**Data Flows (5):**
1. Drawings: Dropbox → Contractor Foreman (auto-upload new plans to CF)
2. Time Cards: CF → Foundation (extract time entries, import to payroll/job costing)
3. Material/Inventory: Warehouse stock → CF material database (John's request — field ordering via dropdowns)
4. Budgets: Foundation → CF (sync budget data to field)
5. Weekly Reports: CF → John ("what was updated this week by job?")

**Tech:** Playwright (browser automation) + Dropbox API + Foundation SQL

**People:** Andrew (field supervisor, primary CF user), Julie (PM), John (owner, requested material DB)

**Tasks:**
- [ ] Get CF login working with Playwright (prove browser automation works)
- [ ] Map CF UI — understand where drawings, time cards, materials, budgets live
- [ ] Crawl CF knowledge base for reference
- [ ] Identify Foundation time card + budget table structures
- [ ] Determine warehouse inventory source (spreadsheet? Foundation?)
- [ ] Build first automation: Dropbox → CF drawing upload

**Separate project:** Andrew's Power Track reward system (details TBD)

**Two Parallel Tracks:**
- **Track 1 (DET):** Integration work — connect CF, Dropbox, Foundation, Procore via browser automation + APIs. DET keeps existing tools. Norm is the IT guy.
- **Track 2 (Product):** Build AI-native CF competitor independently. Norm's own company. Not for DET — find separate pilot contractor when ready.
- Track 1 feeds Track 2: domain knowledge, pain points, workflow understanding
- John will NOT use a Norm-built product ("I want somebody's neck to ring") — don't pitch it to DET
- See also: `context/contractor_foreman/integration_scope.md`

**Notes:**
- Zapier integration evaluated — too limited, not useful
- Procore sync is future/stretch goal (GC-side PM tool)
- CF may or may not have an API — browser automation is the safe path
- CF feature sections to replicate: Project Management, Financials, People, Documents, Settings
- Start with Projects module, get to 80%, then expand
