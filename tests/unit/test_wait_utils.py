from __future__ import annotations

import pytest
from selenium.common.exceptions import TimeoutException

from mobile_automation.wait_utils import poll_until, wait_until


class TestWaitUntil:
    def test_returns_truthy_immediately(self):
        assert wait_until(lambda: "value", timeout=1.0, poll=0.01) == "value"

    def test_returns_after_a_few_polls(self):
        counter = {"n": 0}

        def predicate():
            counter["n"] += 1
            return counter["n"] >= 3

        assert wait_until(predicate, timeout=1.0, poll=0.01) is True
        assert counter["n"] >= 3

    def test_raises_on_timeout(self):
        with pytest.raises(TimeoutException, match="timed out"):
            wait_until(lambda: False, timeout=0.1, poll=0.05)

    def test_custom_message(self):
        with pytest.raises(TimeoutException, match="never visible"):
            wait_until(lambda: False, timeout=0.1, poll=0.05, message="never visible")


class TestPollUntil:
    def test_returns_true_on_success(self):
        assert poll_until(lambda: True, timeout=0.5, poll=0.05) is True

    def test_returns_false_on_timeout(self):
        assert poll_until(lambda: False, timeout=0.1, poll=0.05) is False
