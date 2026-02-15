"""Tests for Knowledge Base tools."""

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add kb tools to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "kb"))

from kb_utils import (
    chunk_transcript, parse_discord_messages, serialize_vec,
    KB_DB_PATH,
)


def test_serialize_vec():
    """Test vector serialization produces correct byte length."""
    vec = [0.1] * 384
    result = serialize_vec(vec)
    assert isinstance(result, bytes)
    assert len(result) == 384 * 4  # 4 bytes per float32


def test_chunk_transcript():
    """Test transcript parsing splits on section headers."""
    content = """# Transcript: 2026-02-14

---

## User (09:00)

Hello, how are you doing today?

---

## Claude (09:01)

I'm doing great, thanks for asking! Here's what I found in the data.

---

## User (09:05)

Tell me about TROW and what happened with earnings last week.

---

"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        chunks = chunk_transcript(Path(f.name))

    assert len(chunks) == 3
    assert chunks[0]['role'] == 'User'
    assert chunks[0]['timestamp'] == '09:00'
    assert 'Hello' in chunks[0]['content']
    assert chunks[1]['role'] == 'Claude'
    assert chunks[2]['role'] == 'User'
    assert 'TROW' in chunks[2]['content']


def test_parse_discord_individual_export():
    """Test parsing individual Discord export format."""
    data = [
        {
            "id": "123456",
            "author": {"username": "testuser", "global_name": "Test User"},
            "content": "This is a test message about MSFT",
            "timestamp": "2026-02-14T10:00:00.000000+00:00",
        },
        {
            "id": "123457",
            "author": {"username": "hans", "global_name": None},
            "content": "",  # Empty — should be skipped
            "timestamp": "2026-02-14T10:01:00.000000+00:00",
        },
        {
            "id": "123458",
            "author": {"username": "hans"},
            "content": "Buy LITE calls",
            "timestamp": "2026-02-14T10:02:00.000000+00:00",
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='_export.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        messages = parse_discord_messages(Path(f.name))

    assert len(messages) == 2  # Empty message skipped
    assert messages[0]['author'] == 'Test User'
    assert messages[0]['id'] == '123456'
    assert messages[1]['author'] == 'hans'
    assert 'LITE' in messages[1]['content']


def test_parse_discord_daily_pull():
    """Test parsing daily pull format (dict of channel -> messages)."""
    data = {
        "leaps-alerts": [
            {
                "id": "111",
                "author": {"username": "hans", "global_name": "Hans"},
                "content": "New LEAPS alert: BUY GOOG",
                "timestamp": "2026-02-14T09:00:00.000000+00:00",
            }
        ],
        "general-chat": [
            {
                "id": "222",
                "author": {"username": "member1", "global_name": "Member One"},
                "content": "Good morning everyone",
                "timestamp": "2026-02-14T08:00:00.000000+00:00",
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        messages = parse_discord_messages(Path(f.name))

    assert len(messages) == 2
    assert messages[0]['channel'] == 'leaps_alerts'
    assert messages[0]['author'] == 'Hans'
    assert messages[1]['channel'] == 'general_chat'


def test_kb_database_exists():
    """Verify the KB database was created and has data."""
    assert KB_DB_PATH.exists(), f"KB database not found at {KB_DB_PATH}"

    conn = sqlite3.connect(str(KB_DB_PATH))
    doc_count = conn.execute("SELECT COUNT(*) FROM kb_documents").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM kb_chunks").fetchone()[0]
    conn.close()

    assert doc_count > 0, "No documents in KB"
    assert chunk_count > 0, "No chunks in KB"
    assert doc_count == chunk_count, "Document and chunk counts should match (1:1 chunking)"


def test_kb_has_all_sources():
    """Verify all expected sources were ingested."""
    conn = sqlite3.connect(str(KB_DB_PATH))
    sources = conn.execute(
        "SELECT DISTINCT source FROM kb_documents ORDER BY source"
    ).fetchall()
    conn.close()

    source_names = [s[0] for s in sources]
    expected = ['conversation', 'discord', 'lesson', 'memory', 'research', 'trade', 'transcript']
    for exp in expected:
        assert exp in source_names, f"Missing source: {exp}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
