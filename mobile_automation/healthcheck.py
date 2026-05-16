from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

import requests

from mobile_automation.config import Settings


@dataclass(frozen=True)
class HealthcheckTarget:
    url: str
    expected_statuses: set[int] | None = None


def _parse_expected_statuses(raw_value: str) -> set[int]:
    statuses: set[int] = set()
    for raw_status in raw_value.split(","):
        raw_status = raw_status.strip()
        if not raw_status:
            continue
        try:
            statuses.add(int(raw_status))
        except ValueError as exc:
            raise ValueError(f"Invalid healthcheck status code: {raw_status}") from exc
    return statuses


def parse_healthcheck_target(raw_target: str) -> HealthcheckTarget:
    target = raw_target.strip()
    if "|" not in target:
        return HealthcheckTarget(url=target)

    url, raw_statuses = (part.strip() for part in target.split("|", 1))
    if not url:
        raise ValueError("Healthcheck URL cannot be empty.")
    return HealthcheckTarget(url=url, expected_statuses=_parse_expected_statuses(raw_statuses))


def _is_expected_status(response_status: int, expected_statuses: set[int] | None) -> bool:
    if expected_statuses is not None:
        return response_status in expected_statuses
    return 200 <= response_status < 400


def check_urls(urls: list[str], timeout_sec: int = 10) -> tuple[bool, list[str]]:
    messages: list[str] = []
    if not urls:
        messages.append("No healthcheck URLs configured; treating environment as available.")
        return True, messages

    ok = True
    for raw_url in urls:
        try:
            target = parse_healthcheck_target(raw_url)
            response = requests.get(target.url, timeout=timeout_sec)
            expected = (
                ",".join(str(status) for status in sorted(target.expected_statuses))
                if target.expected_statuses is not None
                else "2xx/3xx"
            )
            messages.append(f"{target.url} -> {response.status_code} (expected {expected})")
            if not _is_expected_status(response.status_code, target.expected_statuses):
                ok = False
        except (requests.RequestException, ValueError) as exc:
            messages.append(f"{raw_url} -> ERROR: {exc}")
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
