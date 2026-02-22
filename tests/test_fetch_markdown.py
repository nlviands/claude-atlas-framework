"""Tests for tools/web/fetch_markdown.py"""

import subprocess
import sys


def test_cf_markdown_on_cloudflare_blog():
    """Cloudflare's own blog should return CF markdown."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/web/fetch_markdown.py",
            "https://blog.cloudflare.com/markdown-for-agents/",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/Users/nl/projects/claude_atlas_framework",
    )
    assert result.returncode == 0
    assert "Source: cloudflare" in result.stdout
    assert "markdown" in result.stdout.lower()


def test_firecrawl_fallback():
    """Non-CF site should fall back to firecrawl."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/web/fetch_markdown.py",
            "https://www.monergism.com/thethreshold/sdg/perkins_prophesying.html",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="/Users/nl/projects/claude_atlas_framework",
    )
    assert result.returncode == 0
    assert "Source: firecrawl" in result.stdout


def test_force_firecrawl():
    """--force-firecrawl should skip CF even on CF site."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/web/fetch_markdown.py",
            "--force-firecrawl",
            "https://blog.cloudflare.com/markdown-for-agents/",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        cwd="/Users/nl/projects/claude_atlas_framework",
    )
    assert result.returncode == 0
    assert "Source: firecrawl" in result.stdout


def test_output_file(tmp_path):
    """--output should write to file."""
    outfile = tmp_path / "test.md"
    result = subprocess.run(
        [
            sys.executable,
            "tools/web/fetch_markdown.py",
            "https://blog.cloudflare.com/markdown-for-agents/",
            "--output",
            str(outfile),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/Users/nl/projects/claude_atlas_framework",
    )
    assert result.returncode == 0
    assert outfile.exists()
    content = outfile.read_text()
    assert "Source: cloudflare" in content
