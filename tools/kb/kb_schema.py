#!/Users/nl/projects/chief_of_staff/.venv/bin/python
"""
Knowledge Base Schema

Creates the knowledge base database with tables and virtual tables.
Idempotent — safe to re-run.

Usage:
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_schema.py
"""

from kb_utils import get_kb_conn, KB_DB_PATH


def create_schema():
    conn = get_kb_conn()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS kb_documents (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            source_id TEXT,
            title TEXT,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT,
            ingested_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source, source_id)
        );

        CREATE TABLE IF NOT EXISTS kb_chunks (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER DEFAULT 0,
            content TEXT NOT NULL,
            token_count INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_docs_source ON kb_documents(source);
        CREATE INDEX IF NOT EXISTS idx_docs_source_id ON kb_documents(source, source_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_doc ON kb_chunks(document_id);
    """)

    # sqlite-vec virtual table — must check if exists manually
    existing = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='kb_vec'"
    ).fetchone()
    if not existing:
        conn.execute("""
            CREATE VIRTUAL TABLE kb_vec USING vec0(
                chunk_id INTEGER PRIMARY KEY,
                embedding float[384]
            )
        """)

    # FTS5 for keyword search
    existing_fts = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='kb_fts'"
    ).fetchone()
    if not existing_fts:
        conn.execute("""
            CREATE VIRTUAL TABLE kb_fts USING fts5(
                content,
                content='kb_chunks',
                content_rowid='id'
            )
        """)

        # Triggers to keep FTS in sync with chunks
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS kb_fts_insert AFTER INSERT ON kb_chunks BEGIN
                INSERT INTO kb_fts(rowid, content) VALUES (new.id, new.content);
            END;

            CREATE TRIGGER IF NOT EXISTS kb_fts_delete AFTER DELETE ON kb_chunks BEGIN
                INSERT INTO kb_fts(kb_fts, rowid, content) VALUES('delete', old.id, old.content);
            END;

            CREATE TRIGGER IF NOT EXISTS kb_fts_update AFTER UPDATE ON kb_chunks BEGIN
                INSERT INTO kb_fts(kb_fts, rowid, content) VALUES('delete', old.id, old.content);
                INSERT INTO kb_fts(rowid, content) VALUES (new.id, new.content);
            END;
        """)

    conn.commit()
    conn.close()
    print(f"Schema created: {KB_DB_PATH}")
    print(f"  Size: {KB_DB_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    create_schema()
