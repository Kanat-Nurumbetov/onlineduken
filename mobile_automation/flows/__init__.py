"""Public surface of the flows package.

Re-exports every name that used to live in the monolithic `flows.py` so
existing imports like `from mobile_automation.flows import enter_onlineduken`
keep working unchanged.

Internal modules:
- `_helpers`: low-level utilities (bounds parser, wait_for/wait_for_any)
- `debug`: artifact capture for failed runs
- `auth`: Halyk login flow (phone, sms, pin)
- `main_home`: contract picker, OnlineDuken entry tile, native store popup
- `webview`: WEBVIEW context switching and webview-bound store popup
- `onlineduken`: deeplink + WebView orchestration (enter, recover)
"""

from __future__ import annotations

from mobile_automation.flows._helpers import wait_for, wait_for_any
from mobile_automation.flows.auth import (
    AUTH_RETRY_DIALOG_MARKERS,
    dismiss_auth_retry_dialog_if_present,
    dismiss_post_login_prompts,
    fill_pin_with_virtual_keyboard,
    fill_text_input,
    get_pin_value,
    is_auth_flow_visible,
    is_passcode_screen,
    is_sms_confirmation_screen,
    try_complete_login,
    unlock_if_needed,
    wait_until_auth_flow_finishes,
)
from mobile_automation.flows.debug import (
    ARTIFACTS_DIR,
    capture_native_debug_state,
    capture_web_debug_state,
)
from mobile_automation.flows.main_home import (
    choose_first_store_if_present,
    click_first_clickable_ancestor_for_text,
    ensure_expected_contract_selected,
    open_onlineduken_from_main,
    swipe_up_within_element,
    wait_for_main_home,
)
from mobile_automation.flows.onlineduken import (
    apply_b2b_auth_url_in_webview,
    enter_onlineduken,
    open_b2b_auth_url,
    open_b2b_deeplink,
    open_onlineduken_home,
    open_onlineduken_route,
    recover_onlineduken_home,
    wait_for_post_deeplink_ready_state,
)
from mobile_automation.flows.webview import (
    KNOWN_STORE_MARKERS,
    choose_first_store_in_webview_if_present,
    click_web_element,
    ensure_webview_context,
    has_target_b2b_webview,
    switch_to_native,
    switch_to_webview,
    wait_for_web_element,
    wait_for_web_overlay_to_clear,
)

# Backward-compat shim: flows.py used to re-export this name as well.
from mobile_automation.web_flows import wait_for_customer_frontend as wait_for_web_customer_frontend  # noqa: F401

__all__ = [
    "ARTIFACTS_DIR",
    "AUTH_RETRY_DIALOG_MARKERS",
    "KNOWN_STORE_MARKERS",
    "apply_b2b_auth_url_in_webview",
    "capture_native_debug_state",
    "capture_web_debug_state",
    "choose_first_store_if_present",
    "choose_first_store_in_webview_if_present",
    "click_first_clickable_ancestor_for_text",
    "click_web_element",
    "dismiss_auth_retry_dialog_if_present",
    "dismiss_post_login_prompts",
    "ensure_expected_contract_selected",
    "ensure_webview_context",
    "enter_onlineduken",
    "fill_pin_with_virtual_keyboard",
    "fill_text_input",
    "get_pin_value",
    "has_target_b2b_webview",
    "is_auth_flow_visible",
    "is_passcode_screen",
    "is_sms_confirmation_screen",
    "open_b2b_auth_url",
    "open_b2b_deeplink",
    "open_onlineduken_from_main",
    "open_onlineduken_home",
    "open_onlineduken_route",
    "recover_onlineduken_home",
    "swipe_up_within_element",
    "switch_to_native",
    "switch_to_webview",
    "try_complete_login",
    "unlock_if_needed",
    "wait_for",
    "wait_for_any",
    "wait_for_main_home",
    "wait_for_post_deeplink_ready_state",
    "wait_for_web_customer_frontend",
    "wait_for_web_element",
    "wait_for_web_overlay_to_clear",
    "wait_until_auth_flow_finishes",
]
