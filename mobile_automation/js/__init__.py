from __future__ import annotations

from functools import cache, lru_cache
from pathlib import Path

_JS_DIR = Path(__file__).resolve().parent


@cache
def load(name: str) -> str:
    """Read a JS snippet shipped with the package and cache the result."""
    if not name.endswith(".js"):
        name = f"{name}.js"
    return (_JS_DIR / name).read_text(encoding="utf-8")
