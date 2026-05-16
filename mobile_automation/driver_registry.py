from __future__ import annotations

"""Driver -> session-manager registry.

Some flow helpers receive a raw driver handle but need to ask "who owns this
session, and can it be restarted?". Instead of monkey-patching attributes onto
the driver object, sessions register themselves here keyed by `session_id`.

Entries are stored in a WeakValueDictionary so that a manager which goes out
of scope (test session ended) is cleaned up automatically — we never leak
references to torn-down sessions.
"""

import weakref
from typing import Any, Protocol

_REGISTRY: "weakref.WeakValueDictionary[str, Any]" = weakref.WeakValueDictionary()


class _Restartable(Protocol):
    def restart(self) -> Any: ...


def register(session_id: str, manager: _Restartable) -> None:
    if session_id:
        _REGISTRY[session_id] = manager


def unregister(session_id: str) -> None:
    if session_id:
        _REGISTRY.pop(session_id, None)


def get_session_manager_for(driver) -> _Restartable | None:
    session_id = getattr(driver, "session_id", "")
    return _REGISTRY.get(session_id) if session_id else None
