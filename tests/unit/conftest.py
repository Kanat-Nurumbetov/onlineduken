"""Standalone conftest for unit tests.

The root tests/conftest.py wires in Appium/Selenium fixtures that need a real
mobile environment. Unit tests must be runnable on any CI box, so we override
that and only provide the minimum needed here.
"""
