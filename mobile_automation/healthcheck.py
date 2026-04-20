from __future__ import annotations

import argparse
import os
import sys

import requests

from mobile_automation.config import Settings


def check_urls(urls: list[str], timeout_sec: int = 10) -> tuple[bool, list[str]]:
    messages: list[str] = []
    if not urls:
        messages.append("No healthcheck URLs configured; treating environment as available.")
        return True, messages

    ok = True
    for url in urls:
        try:
            response = requests.get(url, timeout=timeout_sec)
            messages.append(f"{url} -> {response.status_code}")
            if response.status_code >= 500:
                ok = False
        except requests.RequestException as exc:
            messages.append(f"{url} -> ERROR: {exc}")
            ok = False
    return ok, messages


def main() -> int:
    parser = argparse.ArgumentParser(description="Check test environment availability before smoke runs.")
    parser.add_argument("--github-output", action="store_true", help="Write result to GITHUB_OUTPUT.")
    args = parser.parse_args()

    settings = Settings()
    available, messages = check_urls(settings.healthcheck_urls)

    for msg in messages:
        print(msg)

    if args.github_output and os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"available={'true' if available else 'false'}\n")

    return 0 if available else 1


if __name__ == "__main__":
    sys.exit(main())

