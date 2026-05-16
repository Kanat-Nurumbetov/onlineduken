from __future__ import annotations

"""Resource-id helpers for the Halyk stage Android app.

All Android `resource-id` strings in this project follow the pattern
`<APP_PACKAGE>:id/<short_id>`. Centralising the package name and exposing a
small `app_id()` builder removes repetition and makes it trivial to retarget
a different app build (e.g. production vs. stage) by changing one constant.
"""

APP_PACKAGE = "kz.halyk.onlinebank.stage"


def app_id(short_id: str, package: str = APP_PACKAGE) -> str:
    return f"{package}:id/{short_id}"


# Frequently referenced ids — keep here so call-sites stay readable.
PIN_EDIT_TEXT = app_id("pinEditText")
PASSCODE_KEYBOARD = app_id("passcode_fragment_keyboard")
FULL_PROGRESS = app_id("full_progress")
TOUCH_OUTSIDE = app_id("touch_outside")
