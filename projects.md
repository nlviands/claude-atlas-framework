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

**Notes:**
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
**Goal:** Multi-agent LLM system for investment research and automation

**Components:**
- Codex (OpenAI) - code generation/review
- Gemini (Google) - reasoning/synthesis
- Grok (xAI) - social sentiment
- Qwen (local MLX) - drafts/formatting
- Claude - orchestrator

**Completed:**
- [x] Multi-agent LLM system setup
- [x] Pipeline orchestrator with handoffs
- [x] Market data integration (Alpaca)
- [x] Technical indicators tool
- [x] Memory system with RAG

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

*Last updated: 2026-02-05 ~11pm*
