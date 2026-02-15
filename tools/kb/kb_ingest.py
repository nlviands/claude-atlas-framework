#!/Users/nl/projects/chief_of_staff/.venv/bin/python
"""
Knowledge Base Ingestion

Ingests data from all sources into the KB. Deduplicates by (source, source_id).

Usage:
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py all
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py memories
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py discord [file.json]
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py transcripts
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py trades
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py lessons
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py research
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_ingest.py conversations
"""

import argparse
import json
import sys
from pathlib import Path

from kb_utils import (
    get_kb_conn, get_chief_conn,
    embed_texts, serialize_vec,
    chunk_transcript, parse_discord_messages,
    DISCORD_DIR, TRANSCRIPT_DIR,
)


def _insert_and_embed(conn, documents: list[dict]):
    """Insert documents and their chunks with embeddings.

    Each document dict must have:
        source, source_id, title, content, metadata (dict), created_at
    """
    if not documents:
        return 0

    inserted = 0
    # Batch: collect all texts to embed at once
    to_embed = []
    doc_chunk_map = []  # (doc_index, chunk_index) for each text

    for doc in documents:
        # Check if already exists
        existing = conn.execute(
            "SELECT id FROM kb_documents WHERE source=? AND source_id=?",
            (doc['source'], doc['source_id'])
        ).fetchone()
        if existing:
            continue

        to_embed.append(doc['content'])
        doc_chunk_map.append(len(to_embed) - 1)
        inserted += 1

    if not to_embed:
        return 0

    # Batch embed
    print(f"  Embedding {len(to_embed)} chunks...", end=" ", flush=True)
    embeddings = embed_texts(to_embed)
    print("done.")

    # Insert
    embed_idx = 0
    for doc in documents:
        existing = conn.execute(
            "SELECT id FROM kb_documents WHERE source=? AND source_id=?",
            (doc['source'], doc['source_id'])
        ).fetchone()
        if existing:
            continue

        cursor = conn.execute(
            """INSERT INTO kb_documents (source, source_id, title, content, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (doc['source'], doc['source_id'], doc.get('title'),
             doc['content'], json.dumps(doc.get('metadata', {})),
             doc.get('created_at'))
        )
        doc_id = cursor.lastrowid

        cursor = conn.execute(
            """INSERT INTO kb_chunks (document_id, chunk_index, content, token_count)
               VALUES (?, 0, ?, ?)""",
            (doc_id, doc['content'], len(doc['content'].split()))
        )
        chunk_id = cursor.lastrowid

        # Insert embedding
        vec_bytes = serialize_vec(embeddings[embed_idx])
        conn.execute(
            "INSERT INTO kb_vec (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, vec_bytes)
        )
        embed_idx += 1

    conn.commit()
    return inserted


def ingest_memories(conn):
    """Ingest memories from Chief's database."""
    print("Ingesting memories...")
    chief = get_chief_conn()
    rows = chief.execute("""
        SELECT id, timestamp, category, topic, context, summary, details, outcome
        FROM memory ORDER BY id
    """).fetchall()
    chief.close()

    documents = []
    for row in rows:
        mid, ts, cat, topic, ctx, summary, details, outcome = row
        parts = []
        if topic:
            parts.append(f"Topic: {topic}")
        if summary:
            parts.append(summary)
        if details:
            parts.append(details)
        if outcome:
            parts.append(f"Outcome: {outcome}")
        if ctx:
            parts.append(f"Context: {ctx}")

        content = "\n".join(parts)
        if not content.strip():
            continue

        documents.append({
            'source': 'memory',
            'source_id': str(mid),
            'title': topic or summary[:80] if summary else f"Memory #{mid}",
            'content': content[:2000],
            'metadata': {'category': cat, 'topic': topic},
            'created_at': ts,
        })

    count = _insert_and_embed(conn, documents)
    print(f"  Memories: {count} new / {len(documents)} total")
    return count


def ingest_trades(conn):
    """Ingest trades from Chief's database."""
    print("Ingesting trades...")
    chief = get_chief_conn()
    rows = chief.execute("""
        SELECT id, ticker, asset_type, direction, strategy, entry_date,
               entry_price, quantity, exit_date, exit_price, pnl, notes, outcome,
               entry_reason, exit_reason, source
        FROM trades ORDER BY id
    """).fetchall()
    chief.close()

    documents = []
    for row in rows:
        tid, ticker, atype, direction, strategy, entry_date, entry_price, qty, exit_date, exit_price, pnl, notes, outcome, entry_reason, exit_reason, source = row
        parts = [f"Trade: {direction} {qty}x {ticker} ({atype})"]
        if strategy:
            parts.append(f"Strategy: {strategy}")
        if entry_date:
            parts.append(f"Entry: {entry_date} @ ${entry_price}")
        if entry_reason:
            parts.append(f"Entry reason: {entry_reason}")
        if exit_date:
            parts.append(f"Exit: {exit_date} @ ${exit_price}")
        if exit_reason:
            parts.append(f"Exit reason: {exit_reason}")
        if pnl is not None:
            parts.append(f"P&L: ${pnl}")
        if outcome:
            parts.append(f"Outcome: {outcome}")
        if notes:
            parts.append(notes)

        documents.append({
            'source': 'trade',
            'source_id': str(tid),
            'title': f"{direction} {ticker} {strategy or ''}".strip(),
            'content': "\n".join(parts),
            'metadata': {'ticker': ticker, 'direction': direction, 'outcome': outcome},
            'created_at': entry_date,
        })

    count = _insert_and_embed(conn, documents)
    print(f"  Trades: {count} new / {len(documents)} total")
    return count


def ingest_lessons(conn):
    """Ingest trading lessons from Chief's database."""
    print("Ingesting lessons...")
    chief = get_chief_conn()
    rows = chief.execute("""
        SELECT id, category, pattern, context, takeaway, importance, created_at
        FROM lessons ORDER BY id
    """).fetchall()
    chief.close()

    documents = []
    for row in rows:
        lid, category, pattern, context, takeaway, importance, created_at = row
        parts = []
        if pattern:
            parts.append(f"Pattern: {pattern}")
        if takeaway:
            parts.append(f"Takeaway: {takeaway}")
        if context:
            parts.append(f"Context: {context}")
        if category:
            parts.append(f"Category: {category}")

        content = "\n".join(parts)
        if not content.strip():
            continue

        documents.append({
            'source': 'lesson',
            'source_id': str(lid),
            'title': pattern[:80] if pattern else f"Lesson #{lid}",
            'content': content[:2000],
            'metadata': {'category': category, 'importance': importance},
            'created_at': created_at,
        })

    count = _insert_and_embed(conn, documents)
    print(f"  Lessons: {count} new / {len(documents)} total")
    return count


def ingest_research(conn):
    """Ingest research entries from Chief's database."""
    print("Ingesting research...")
    chief = get_chief_conn()
    rows = chief.execute("""
        SELECT id, file_path, file_name, title, content, tickers, source, file_date
        FROM research ORDER BY id
    """).fetchall()
    chief.close()

    documents = []
    for row in rows:
        rid, fpath, fname, title, content, tickers, source, file_date = row
        text = ""
        if title:
            text += f"{title}\n"
        if content:
            text += content

        if not text.strip():
            continue

        documents.append({
            'source': 'research',
            'source_id': str(rid),
            'title': title or fname or f"Research #{rid}",
            'content': text[:2000],
            'metadata': {'file_path': fpath, 'tickers': tickers, 'research_source': source},
            'created_at': file_date,
        })

    count = _insert_and_embed(conn, documents)
    print(f"  Research: {count} new / {len(documents)} total")
    return count


def ingest_conversations(conn):
    """Ingest conversation log entries from Chief's database."""
    print("Ingesting conversations...")
    chief = get_chief_conn()
    rows = chief.execute("""
        SELECT id, session_id, timestamp, role, content
        FROM conversation_log
        WHERE content IS NOT NULL AND length(content) > 20
        ORDER BY id
    """).fetchall()
    chief.close()

    # Group by session, then create chunks of 3-5 exchanges
    sessions = {}
    for row in rows:
        cid, sid, ts, role, content = row
        if sid not in sessions:
            sessions[sid] = []
        sessions[sid].append({'id': cid, 'timestamp': ts, 'role': role, 'content': content})

    documents = []
    for sid, entries in sessions.items():
        # Chunk into groups of 4 entries
        for i in range(0, len(entries), 4):
            group = entries[i:i+4]
            parts = []
            for e in group:
                parts.append(f"[{e['role']}] {e['content'][:500]}")
            content = "\n\n".join(parts)

            first_id = group[0]['id']
            documents.append({
                'source': 'conversation',
                'source_id': f"{sid}_{first_id}",
                'title': f"Conversation {sid[:8]}",
                'content': content[:2000],
                'metadata': {'session_id': sid},
                'created_at': group[0]['timestamp'],
            })

    count = _insert_and_embed(conn, documents)
    print(f"  Conversations: {count} new / {len(documents)} total")
    return count


def ingest_discord(conn, filepath: Path = None):
    """Ingest Discord export JSON files."""
    print("Ingesting Discord messages...")

    if filepath:
        files = [filepath]
    else:
        # Find all export files and daily pulls
        files = list(DISCORD_DIR.glob("*_export.json"))
        daily_dir = DISCORD_DIR / "daily"
        if daily_dir.exists():
            files.extend(daily_dir.glob("*.json"))

    total = 0
    for f in files:
        messages = parse_discord_messages(f)
        if not messages:
            continue

        documents = []
        for msg in messages:
            documents.append({
                'source': 'discord',
                'source_id': msg['id'],
                'title': f"{msg['author']} in #{msg['channel']}",
                'content': f"[{msg['author']}] {msg['content']}",
                'metadata': {
                    'author': msg['author'],
                    'channel': msg['channel'],
                },
                'created_at': msg['timestamp'],
            })

        count = _insert_and_embed(conn, documents)
        print(f"  {f.name}: {count} new / {len(documents)} total")
        total += count

    return total


def ingest_transcripts(conn):
    """Ingest session transcript markdown files."""
    print("Ingesting transcripts...")

    if not TRANSCRIPT_DIR.exists():
        print("  No transcripts directory found.")
        return 0

    files = sorted(TRANSCRIPT_DIR.glob("*.md"))
    # Skip INDEX.md
    files = [f for f in files if f.name != "INDEX.md"]

    total = 0
    for f in files:
        date = f.stem  # e.g., "2026-02-06"
        chunks = chunk_transcript(f)
        if not chunks:
            continue

        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                'source': 'transcript',
                'source_id': f"{date}_{i}",
                'title': f"Transcript {date} ({chunk['role']} {chunk['timestamp']})",
                'content': chunk['content'],
                'metadata': {
                    'date': date,
                    'role': chunk['role'],
                    'timestamp': chunk['timestamp'],
                },
                'created_at': f"{date}T{chunk['timestamp']}:00",
            })

        count = _insert_and_embed(conn, documents)
        print(f"  {f.name}: {count} new / {len(documents)} total")
        total += count

    return total


def ingest_all(conn):
    """Run all ingestion sources."""
    total = 0
    total += ingest_memories(conn)
    total += ingest_trades(conn)
    total += ingest_lessons(conn)
    total += ingest_research(conn)
    total += ingest_discord(conn)
    total += ingest_transcripts(conn)
    total += ingest_conversations(conn)

    # Report totals
    doc_count = conn.execute("SELECT COUNT(*) FROM kb_documents").fetchone()[0]
    chunk_count = conn.execute("SELECT COUNT(*) FROM kb_chunks").fetchone()[0]
    vec_count = conn.execute("SELECT COUNT(*) FROM kb_vec").fetchone()[0]
    print(f"\nKB totals: {doc_count} documents, {chunk_count} chunks, {vec_count} vectors")
    return total


def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Ingestion")
    parser.add_argument("source", nargs="?", default="all",
                        choices=["all", "memories", "trades", "lessons", "research",
                                 "discord", "transcripts", "conversations"],
                        help="Source to ingest (default: all)")
    parser.add_argument("file", nargs="?", help="Specific file (for discord)")
    args = parser.parse_args()

    conn = get_kb_conn()

    if args.source == "all":
        ingest_all(conn)
    elif args.source == "memories":
        ingest_memories(conn)
    elif args.source == "trades":
        ingest_trades(conn)
    elif args.source == "lessons":
        ingest_lessons(conn)
    elif args.source == "research":
        ingest_research(conn)
    elif args.source == "discord":
        filepath = Path(args.file) if args.file else None
        ingest_discord(conn, filepath)
    elif args.source == "transcripts":
        ingest_transcripts(conn)
    elif args.source == "conversations":
        ingest_conversations(conn)

    conn.close()


if __name__ == "__main__":
    main()
