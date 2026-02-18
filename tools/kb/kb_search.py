#!/Users/nl/projects/chief_of_staff/.venv/bin/python
"""
Knowledge Base Search

Hybrid search across all ingested knowledge: vector similarity + FTS5 keyword.

Usage:
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "TROW earnings"
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "Hans LITE" --source discord
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "coolant leak" --mode keyword
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "options strategy" --ticker TROW --limit 20
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "trades" --since 2026-02-15
    /Users/nl/projects/chief_of_staff/.venv/bin/python tools/kb/kb_search.py "BKNG" --since 2026-02-17 --until 2026-02-18
"""

import argparse
import json
import sys

from kb_utils import get_kb_conn, embed_single, serialize_vec


def vector_search(conn, query: str, limit: int = 10, source: str = None, ticker: str = None, since: str = None, until: str = None):
    """Search by vector similarity."""
    query_vec = serialize_vec(embed_single(query))

    sql = """
        SELECT
            v.chunk_id,
            v.distance,
            c.content,
            d.source,
            d.title,
            d.metadata,
            d.created_at
        FROM kb_vec v
        JOIN kb_chunks c ON c.id = v.chunk_id
        JOIN kb_documents d ON d.id = c.document_id
        WHERE v.embedding MATCH ?
        AND k = ?
    """
    # Fetch more than needed so we can filter
    fetch_limit = limit * 3 if (source or ticker) else limit
    params = [query_vec, fetch_limit]

    rows = conn.execute(sql, params).fetchall()

    # Post-filter
    results = []
    for row in rows:
        chunk_id, distance, content, src, title, metadata_str, created_at = row
        if source and src != source:
            continue
        if since and (not created_at or created_at < since):
            continue
        if until and (not created_at or created_at > until):
            continue
        if ticker:
            meta = json.loads(metadata_str) if metadata_str else {}
            if ticker.upper() not in (content.upper() + " " + json.dumps(meta).upper()):
                continue
        results.append({
            'chunk_id': chunk_id,
            'score': 1 - distance,  # Convert distance to similarity
            'content': content,
            'source': src,
            'title': title,
            'metadata': json.loads(metadata_str) if metadata_str else {},
            'created_at': created_at,
            'match_type': 'vector',
        })
        if len(results) >= limit:
            break

    return results


def keyword_search(conn, query: str, limit: int = 10, source: str = None, ticker: str = None, since: str = None, until: str = None):
    """Search by FTS5 keyword matching."""
    sql = """
        SELECT
            c.id,
            rank,
            c.content,
            d.source,
            d.title,
            d.metadata,
            d.created_at
        FROM kb_fts f
        JOIN kb_chunks c ON c.id = f.rowid
        JOIN kb_documents d ON d.id = c.document_id
        WHERE kb_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    fetch_limit = limit * 3 if (source or ticker) else limit
    params = [query, fetch_limit]

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception:
        # FTS5 can fail on special characters, fall back to simple match
        return []

    results = []
    for row in rows:
        chunk_id, rank, content, src, title, metadata_str, created_at = row
        if source and src != source:
            continue
        if since and (not created_at or created_at < since):
            continue
        if until and (not created_at or created_at > until):
            continue
        if ticker:
            meta = json.loads(metadata_str) if metadata_str else {}
            if ticker.upper() not in (content.upper() + " " + json.dumps(meta).upper()):
                continue
        results.append({
            'chunk_id': chunk_id,
            'score': -rank,  # FTS5 rank is negative (lower = better)
            'content': content,
            'source': src,
            'title': title,
            'metadata': json.loads(metadata_str) if metadata_str else {},
            'created_at': created_at,
            'match_type': 'keyword',
        })
        if len(results) >= limit:
            break

    return results


def hybrid_search(conn, query: str, limit: int = 10, source: str = None, ticker: str = None, since: str = None, until: str = None):
    """Combined vector + keyword search with reciprocal rank fusion."""
    vec_results = vector_search(conn, query, limit=limit * 2, source=source, ticker=ticker, since=since, until=until)
    kw_results = keyword_search(conn, query, limit=limit * 2, source=source, ticker=ticker, since=since, until=until)

    # Reciprocal rank fusion
    k = 60  # RRF constant
    scores = {}
    result_map = {}

    for rank, r in enumerate(vec_results):
        cid = r['chunk_id']
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        result_map[cid] = r

    for rank, r in enumerate(kw_results):
        cid = r['chunk_id']
        scores[cid] = scores.get(cid, 0) + 1 / (k + rank + 1)
        if cid not in result_map:
            result_map[cid] = r

    # Sort by combined score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

    results = []
    for cid, score in ranked:
        r = result_map[cid]
        r['score'] = score
        r['match_type'] = 'hybrid'
        results.append(r)

    return results


def format_results(results: list[dict], verbose: bool = False):
    """Format search results for display."""
    if not results:
        print("No results found.")
        return

    for i, r in enumerate(results, 1):
        src_label = f"[{r['source']}]"
        date = r.get('created_at', '')[:10] if r.get('created_at') else ''
        score = f"{r['score']:.4f}"

        # Truncate content for display
        content = r['content'].replace('\n', ' ')
        if not verbose:
            content = content[:150] + "..." if len(content) > 150 else content

        print(f"\n{i}. {src_label} {r['title']} ({date}) score={score}")
        if verbose:
            meta = r.get('metadata', {})
            if meta:
                print(f"   meta: {json.dumps(meta)}")
        print(f"   {content}")

    print(f"\n--- {len(results)} results ---")


def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--mode", choices=["hybrid", "vector", "keyword"], default="hybrid")
    parser.add_argument("--source", help="Filter by source (memory, discord, trade, etc.)")
    parser.add_argument("--ticker", help="Filter by ticker symbol")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--since", help="Only results after this date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Only results before this date (YYYY-MM-DD)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show metadata")
    args = parser.parse_args()

    conn = get_kb_conn()

    if args.mode == "hybrid":
        results = hybrid_search(conn, args.query, args.limit, args.source, args.ticker, args.since, args.until)
    elif args.mode == "vector":
        results = vector_search(conn, args.query, args.limit, args.source, args.ticker, args.since, args.until)
    elif args.mode == "keyword":
        results = keyword_search(conn, args.query, args.limit, args.source, args.ticker, args.since, args.until)

    format_results(results, args.verbose)
    conn.close()


if __name__ == "__main__":
    main()
