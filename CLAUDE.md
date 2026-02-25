# Atlas Framework — MERGED INTO CHIEF OF STAFF

**This repo has been merged into `/Users/nl/projects/chief_of_staff` as of February 24, 2026.**

All tools, context, args, and config have been migrated. Use chief_of_staff as your working directory.

```bash
cd /Users/nl/projects/chief_of_staff
```

## What moved where

| From (atlas_framework) | To (chief_of_staff) |
|------------------------|---------------------|
| `tools/kb/` | `tools/kb/` |
| `tools/discord/` | `tools/discord/` |
| `tools/data/` | `tools/data/` |
| `tools/memory/` | `tools/memory/` |
| `tools/llm/` | `tools/llm/` |
| `args/` | `args/` |
| `context/` | `context/` |
| `memory/transcripts/` | `memory/transcripts/` |
| `.claude/agents/market-researcher.md` | `.claude/agents/market-researcher.md` |

## What was dropped

- `goals/` — Goals layer never proved useful; Claude handles orchestration directly
- `hardprompts/` — Templates unused; inline prompts work better
- `reports/` — Already lived in chief_of_staff
- Old delegate scripts (gpt, gemini, grok) — Dead code, deleted

---

*Merged: February 24, 2026*
