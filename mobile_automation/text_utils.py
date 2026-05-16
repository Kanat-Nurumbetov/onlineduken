from __future__ import annotations


def maybe_fix_mojibake(text: str) -> str:
    if not text:
        return ""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def normalize_text(text: str) -> str:
    return " ".join(maybe_fix_mojibake(text).split()).strip()
