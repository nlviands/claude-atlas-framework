# Tools Manifest

> Master list of all available tools. Check here before writing new scripts.

## LLM Tools (`tools/llm/`)

| Tool | Description |
|------|-------------|
| `orchestrator.py` | Pipeline orchestrator - routes tasks through agent chains |
| `base.py` | Base classes and interfaces for LLM clients |
| `clients/codex_client.py` | OpenAI/Codex client for code generation and review |
| `clients/gemini_client.py` | Google Gemini client for reasoning and synthesis |
| `clients/grok_client.py` | xAI Grok client for social sentiment and creative tasks |
| `clients/qwen_local.py` | Local Qwen client via MLX for drafts and formatting |

### Orchestrator Commands

```bash
# Check which agents are available
uv run python orchestrator.py health

# List available pipelines
uv run python orchestrator.py list

# Run a pipeline
uv run python orchestrator.py run <pipeline_name> "<task>"

# Query a single agent
uv run python orchestrator.py query <agent> "<prompt>"
```

---

## Data Tools (`tools/data/`)

| Tool | Description |
|------|-------------|
| `market_data.py` | Market data aggregator - bundles price, news, options for pipelines |
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

---

*Update this manifest when adding new tools.*
