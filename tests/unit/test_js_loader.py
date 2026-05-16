from __future__ import annotations

import pytest

from mobile_automation import js as js_snippets


def test_load_returns_non_empty_string():
    body = js_snippets.load("overlay_visible")
    assert body.strip().startswith("const overlay")


def test_load_appends_js_extension():
    direct = js_snippets.load("overlay_visible")
    with_ext = js_snippets.load("overlay_visible.js")
    assert direct == with_ext


def test_load_caches_reads(tmp_path, monkeypatch):
    # Just ensure two consecutive loads return the same string object reference
    # via lru_cache (cheap signal that the cache is wired up).
    first = js_snippets.load("main_content_text")
    second = js_snippets.load("main_content_text")
    assert first is second


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        js_snippets.load("definitely_not_a_real_snippet_xyz")
