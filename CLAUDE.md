# Atlas Framework — Project Configuration

## Quick Reference

```bash
# Key files
projects.md              # Active projects and tasks
tools/manifest.md        # All available tools (check before writing new ones)
memory/MEMORY.md         # Persistent facts (auto-loaded, <200 lines)

# Knowledge Base (sqlite-vec, 7,600+ vectors)
PYTHON=/Users/nl/projects/chief_of_staff/.venv/bin/python
$PYTHON tools/kb/kb_search.py "query"          # Hybrid search across everything
$PYTHON tools/kb/kb_ingest.py all              # Re-ingest all sources

# Dev servers always on port 8001 (port 8000 is reserved)
```

---

## GOTCHA Framework

6-layer architecture for agentic systems:

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Goals** | `goals/` | Process definitions — what to achieve |
| **Orchestration** | (you) | AI manager — coordinates execution |
| **Tools** | `tools/` | Deterministic scripts — do the actual work |
| **Context** | `context/` | Domain knowledge and reference material |
| **Hard prompts** | `hardprompts/` | Reusable instruction templates |
| **Args** | `args/` | Behavior settings (YAML/JSON) |

**Principle:** Push reliability into deterministic code (tools). Push reasoning into the LLM (you). Each layer has one responsibility.

---

## Operating Rules

1. **Check `goals/manifest.md` first** — if a goal exists for this task, follow it.
2. **Check `tools/manifest.md` before writing code** — if a tool exists, use it. If you create one, add it to the manifest.
3. **When tools fail** — read the error, fix the tool, update the goal with what you learned.
4. **Goals are living docs** — update when better approaches emerge. Never modify without permission.
5. **When stuck** — explain what's missing and what you need. Don't guess capabilities.

---

## Guardrails

- Always check `tools/manifest.md` before writing a new script
- Verify tool output format before chaining into another tool
- Don't assume APIs support batch operations — check first
- Preserve intermediate outputs before retrying failed workflows
- Read the full goal before starting — don't skim
- **NEVER DELETE YOUTUBE VIDEOS** — irreversible. Direct user to YouTube Studio instead.
- **Use port 8001 for dev servers** — port 8000 is reserved for another Claude instance.
- **New tool/API = update CLAUDE.md + manifest.** When adding any tool, integration, or API — updating docs is part of "done", not a follow-up.

*(Add new guardrails as mistakes happen. Keep under 15 items.)*

---

## Tools Overview

| Directory | Tools | Purpose |
|-----------|-------|---------|
| `tools/kb/` | kb_search, kb_ingest, kb_schema | Vector knowledge base (sqlite-vec + FTS5) |
| `tools/discord/` | export_channel, daily_pull | Discord channel exports (Hans's server) |
| `tools/llm/` | orchestrator | Grok for social sentiment (only external LLM still active) |
| `tools/data/` | market_data, technical_indicators | Market data and TA calculations |
| `tools/memory/` | conversation_logger | Hook-based session logging, Slack poll triggers |
| `tools/esphome/` | office-ble-proxy.yaml | ESPHome BLE presence detection configs |

See `tools/manifest.md` for full details and usage examples.

---

## File Structure

```
goals/          — Process definitions
tools/          — Scripts organized by workflow
args/           — Behavior settings (YAML/JSON)
context/        — Domain knowledge and reference material
hardprompts/    — Instruction templates
memory/         — Session transcripts and MEMORY.md
reports/        — Generated analysis reports
.tmp/           — Disposable scratch work
.env            — API keys (XAI_API_KEY for Grok)
```

---

## Autonomous Work Protocol

- **Explore before acting** — understand the codebase before suggesting changes
- **Plan before implementing** — use `EnterPlanMode` for non-trivial tasks
- **Track state** — update `projects.md` after milestones
- **Test before done** — "it should work" is not verification
- **Don't leave work uncommitted** at session end

---

*Last updated: February 15, 2026*
