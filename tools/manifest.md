# Tools Manifest

> Master list of all available tools. Check here before writing new scripts.

## Architecture (Simplified)

Claude Opus 4.6 is the orchestrator, synthesizer, and reasoner. External tools provide
data and deterministic calculations. Grok is the only external LLM (optional, for X sentiment).

---

## LLM Tools (`tools/llm/`)

| Tool | Description |
|------|-------------|
| `orchestrator.py` | Queries Grok for social sentiment when needed |
| `base.py` | Base classes and interfaces for LLM clients |
| `clients/grok_client.py` | xAI Grok client — X/social sentiment (only external LLM still active) |

### Usage

```bash
# Check if Grok is available
cd tools/llm && uv run python orchestrator.py health

# Query Grok for sentiment
uv run python orchestrator.py query grok "Social sentiment on TSLA"
```

### Retired Clients (kept for reference, not actively used)
- `clients/codex_client.py` — OpenAI/GPT-4o (replaced by Claude Opus 4.6)
- `clients/gemini_client.py` — Google Gemini (replaced by Claude Opus 4.6)
- `clients/qwen_local.py` — Local Qwen via MLX (replaced by Claude Opus 4.6)

---

## Data Tools (`tools/data/`)

| Tool | Description |
|------|-------------|
| `market_data.py` | Market data aggregator — bundles price, news, options for analysis |
| `technical_indicators.py` | Calculates RSI, MACD, Bollinger Bands, MAs from price data |

---

## Memory Tools (`tools/memory/`)

| Tool | Description |
|------|-------------|
| `memory_db.py` | Core database operations for memory storage and retrieval |
| `memory_read.py` | Read memory entries with formatting options |
| `memory_write.py` | Write new entries to memory or update MEMORY.md |
| `embed_memory.py` | Generate embeddings for memory entries |
| `semantic_search.py` | Search memory using semantic similarity |
| `hybrid_search.py` | Combined keyword + semantic search (recommended) |
| `conversation_logger.py` | Auto-logs user prompts and assistant responses via Claude Code hooks |

---

## Claude Code Subagents (`.claude/agents/`)

| Agent | Description |
|-------|-------------|
| `market-researcher` | Stock research — pulls data, runs TA, delivers concise reports |

---

## Knowledge Base (`tools/kb/`)

| Tool | Description |
|------|-------------|
| `kb_schema.py` | Creates/migrates the vector knowledge base schema (sqlite-vec + FTS5) |
| `kb_ingest.py` | Ingests all data sources into KB — memories, trades, Discord, transcripts, etc. |
| `kb_search.py` | Hybrid search (vector + keyword) across all ingested knowledge |
| `kb_utils.py` | Shared utilities — embedding, chunking, DB connections |

### Usage

```bash
PYTHON=/Users/nl/projects/chief_of_staff/.venv/bin/python

# Create/update schema
$PYTHON tools/kb/kb_schema.py

# Ingest all sources
$PYTHON tools/kb/kb_ingest.py all

# Ingest specific source
$PYTHON tools/kb/kb_ingest.py discord path/to/export.json

# Search
$PYTHON tools/kb/kb_search.py "TROW earnings"
$PYTHON tools/kb/kb_search.py "Hans LITE" --source discord
$PYTHON tools/kb/kb_search.py "options strategy" --ticker TROW --limit 20
$PYTHON tools/kb/kb_search.py "coolant leak" --mode keyword
```

**Database:** `/Users/nl/projects/chief_of_staff/knowledge.db` (19MB, 7,254 vectors)

---

## Discord Tools (`tools/discord/`)

| Tool | Description |
|------|-------------|
| `export_channel.py` | Export messages from a Discord channel using user token |
| `daily_pull.py` | Automated daily pull of Hans's key channels (scheduled by Chief at 8:45 AM) |

---

## Voice Tools (`tools/voice/`)

| Tool | Description |
|------|-------------|
| `call.py` | Outbound call trigger — starts server, ngrok tunnel, initiates Twilio call |
| `server.py` | FastAPI WebSocket server — bridges Twilio ConversationRelay ↔ Claude streaming |

### Usage

```bash
PYTHON=/Users/nl/projects/chief_of_staff/.venv/bin/python

# Call a contact by name (from args/contacts.yaml)
$PYTHON tools/voice/call.py norm "Hey Norm, this is Atlas testing voice."

# Call with custom greeting
$PYTHON tools/voice/call.py austin "Hey Austin, this is Atlas, Norm's AI assistant."

# Call a raw number
$PYTHON tools/voice/call.py --to "+19105551234" --greeting "Hello!"
```

### Prerequisites
- Twilio account with SID, Auth Token, and phone number in `.env`
- `ngrok` installed (`brew install ngrok/ngrok/ngrok` + authtoken configured)
- Recipient must be verified on Twilio trial account (or upgrade to paid)

### Config
- `args/voice_config.yaml` — TTS voice, STT provider, Claude model, max duration
- `args/contacts.yaml` — Phone contacts with context for the AI

---

*Update this manifest when adding new tools or subagents.*
