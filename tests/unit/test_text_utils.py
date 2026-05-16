from __future__ import annotations

from mobile_automation.text_utils import maybe_fix_mojibake, normalize_text


class TestMaybeFixMojibake:
    def test_empty_returns_empty(self):
        assert maybe_fix_mojibake("") == ""

    def test_clean_ascii_passes_through(self):
        assert maybe_fix_mojibake("Hello world") == "Hello world"

    def test_decodes_cp1251_seen_as_utf8(self):
        # "Оплатить" → encoded UTF-8 then decoded as CP1251 → mojibake form.
        original = "Оплатить"
        mojibake = original.encode("utf-8").decode("latin-1")
        assert maybe_fix_mojibake(mojibake) == original

    def test_unrecoverable_text_returned_as_is(self):
        # Pure clean Cyrillic does not round-trip latin-1 -> utf-8, returns original.
        assert maybe_fix_mojibake("Привет") == "Привет"


class TestNormalizeText:
    def test_collapses_whitespace(self):
        assert normalize_text("  foo\n\tbar   baz") == "foo bar baz"

    def test_empty(self):
        assert normalize_text("") == ""

    def test_handles_mojibake(self):
        mojibake = "Оплатить  заказ".encode().decode("latin-1")
        assert normalize_text(mojibake) == "Оплатить заказ"
