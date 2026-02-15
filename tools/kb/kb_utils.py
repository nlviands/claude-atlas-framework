#!/Users/nl/projects/chief_of_staff/.venv/bin/python
"""
Knowledge Base Utilities

Shared helpers for schema, ingestion, and search.
Run with Chief's venv: /Users/nl/projects/chief_of_staff/.venv/bin/python
"""

import json
import re
import sqlite3
from pathlib import Path

import sqlite_vec

# Paths
KB_DB_PATH = Path("/Users/nl/projects/chief_of_staff/knowledge.db")
CHIEF_DB_PATH = Path("/Users/nl/projects/chief_of_staff/claude_memory.db")
DISCORD_DIR = Path("/Users/nl/projects/claude_atlas_framework/tools/discord")
TRANSCRIPT_DIR = Path("/Users/nl/projects/claude_atlas_framework/memory/transcripts")

# Embedding model (lazy-loaded)
_model = None


def get_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of 384-dim float vectors."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=len(texts) > 100)
    return [e.tolist() for e in embeddings]


def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    return embed_texts([text])[0]


def get_kb_conn() -> sqlite3.Connection:
    """Get a connection to the knowledge base with sqlite-vec loaded."""
    conn = sqlite3.connect(str(KB_DB_PATH))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_chief_conn(readonly=True) -> sqlite3.Connection:
    """Get a connection to Chief's memory database."""
    uri = f"file:{CHIEF_DB_PATH}"
    if readonly:
        uri += "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def chunk_transcript(filepath: Path) -> list[dict]:
    """Parse a transcript markdown file into chunks.

    Splits on ## User / ## Claude headers.
    Returns list of dicts with 'content', 'role', 'timestamp'.
    """
    text = filepath.read_text()
    chunks = []

    # Split on section headers like "## User (14:30)" or "## Claude (14:31)"
    pattern = r'## (User|Claude) \((\d{2}:\d{2})\)\n\n'
    parts = re.split(pattern, text)

    # parts[0] is the header before first section
    # Then groups of 3: role, timestamp, content
    i = 1
    while i + 2 < len(parts):
        role = parts[i]
        timestamp = parts[i + 1]
        content = parts[i + 2].strip().rstrip('---').strip()
        if content and len(content) > 20:  # Skip trivially short chunks
            chunks.append({
                'role': role,
                'timestamp': timestamp,
                'content': content[:2000],  # Cap at 2000 chars for embedding quality
            })
        i += 3

    return chunks


def parse_discord_messages(filepath: Path) -> list[dict]:
    """Parse a Discord export JSON file into individual messages.

    Handles two formats:
    - Individual export: [message, message, ...]
    - Daily pull: {channel_name: [message, ...], ...}

    Returns list of dicts with 'id', 'author', 'content', 'timestamp', 'channel'.
    """
    data = json.loads(filepath.read_text())
    messages = []

    # Detect format
    if isinstance(data, dict):
        # Daily pull format: {channel_name: [messages]}
        for channel_name, channel_msgs in data.items():
            for msg in channel_msgs:
                parsed = _parse_single_message(msg, channel_name.replace("-", "_"))
                if parsed:
                    messages.append(parsed)
    elif isinstance(data, list):
        # Individual export format: [messages]
        channel = filepath.stem.replace("_export", "").replace("-", "_")
        for msg in data:
            parsed = _parse_single_message(msg, channel)
            if parsed:
                messages.append(parsed)

    return messages


def _parse_single_message(msg: dict, channel: str) -> dict | None:
    """Parse a single Discord message dict."""
    content = msg.get("content", "").strip()
    if not content:
        return None

    author = msg.get("author", {})
    author_name = author.get("global_name") or author.get("username", "unknown")

    return {
        'id': msg.get("id", ""),
        'author': author_name,
        'content': content[:2000],
        'timestamp': msg.get("timestamp", ""),
        'channel': channel,
    }


def serialize_vec(vec: list[float]) -> bytes:
    """Serialize a float vector to bytes for sqlite-vec."""
    import struct
    return struct.pack(f'{len(vec)}f', *vec)
