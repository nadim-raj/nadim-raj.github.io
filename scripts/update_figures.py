#!/usr/bin/env python3
"""Refresh the FundedNext figures on the portfolio from their public homepage.

The figures are animated counters, so the page ships both the real value and a
zeroed placeholder next to it: "$ 316.1 $ 0.0 M +". A naive scraper reads the
placeholder and publishes "$0.0M+", which is why every value here is validated
before it is allowed anywhere near the page.

The rules are deliberately conservative:

* A value that fails validation is discarded and the previous one kept. The
  card showing a slightly stale number is a non-event; the card showing zero,
  or a number that cannot be sourced, is not.
* Cumulative figures may not go down. Rewards distributed and accounts opened
  only ever increase, so a decrease means the parse is wrong, not the business.
* Nothing is written unless a value actually changed.

Usage:
    python3 scripts/update_figures.py --dry-run
    python3 scripts/update_figures.py
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

SOURCE = "https://fundednext.com/"
STATE = Path("data/fundednext.json")
PAGE = Path("index.html")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0 Safari/537.36"

# figure key -> (regex over visible text, plausible range, cumulative?)
FIGURES = {
    "rewards_musd": (r"\$\s*([\d,]+\.?\d*)\s*\$\s*0\.0\s*M\s*\+?[^.]{0,60}?[Rr]eward", (50.0, 100_000.0), True),
    "accounts_k": (r"([\d,]+\.?\d*)\s*0\.0\s*K\s*\+?\s*FundedNext\s+Accounts", (1.0, 100_000.0), True),
    "countries": (r"([\d,]+)\s*\+?\s*countries", (1.0, 250.0), False),
}


def visible_text(raw: str) -> str:
    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", stripped)))


def fetch(url: str = SOURCE) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse(text: str) -> dict[str, float]:
    """Take the largest plausible candidate for each figure.

    The page repeats figures across sections, and not every copy is current.
    For cumulative totals the largest match is the live one; a stale duplicate
    is always smaller. Taking the first match instead reads whichever section
    happens to appear earliest in the markup, which is not a property anyone
    controls.
    """
    found: dict[str, float] = {}
    for key, (pattern, bounds, _) in FIGURES.items():
        candidates: list[float] = []
        for match in re.finditer(pattern, text, re.I):
            try:
                value = float(match.group(1).replace(",", ""))
            except ValueError:
                continue
            if bounds[0] <= value <= bounds[1]:
                candidates.append(value)
        if candidates:
            found[key] = max(candidates)
    return found


def validate(found: dict[str, float], previous: dict) -> tuple[dict[str, float], list[str]]:
    """Keep only values that are plausible and, where cumulative, not going backwards."""
    accepted: dict[str, float] = {}
    rejected: list[str] = []
    for key, value in found.items():
        low, high, cumulative = FIGURES[key][1][0], FIGURES[key][1][1], FIGURES[key][2]
        prior = previous.get(key)
        if not low <= value <= high:
            rejected.append(f"{key}={value} outside plausible range {low}-{high}")
        elif cumulative and prior is not None and value < prior:
            rejected.append(f"{key}={value} below previous {prior}; cumulative figures do not fall")
        else:
            accepted[key] = value
    for key in FIGURES:
        if key not in found:
            rejected.append(f"{key} not found on the page")
    return accepted, rejected


def render(key: str, value: float) -> str:
    if key == "rewards_musd":
        return f"${value:,.0f}M+"
    if key == "accounts_k":
        return f"{value:,.0f}K+"
    return f"{value:,.0f}+"


def apply_to_page(values: dict[str, float], page: Path = PAGE) -> list[str]:
    """Rewrite only the elements tagged with a matching data-figure attribute."""
    markup = page.read_text()
    changes: list[str] = []
    for key, value in values.items():
        rendered = render(key, value)
        pattern = re.compile(rf'(<dd data-figure="{key}">)([^<]*)(</dd>)')
        match = pattern.search(markup)
        if not match:
            changes.append(f"! no slot for {key} in {page}")
            continue
        if match.group(2) == rendered:
            continue
        markup = pattern.sub(rf"\g<1>{rendered}\g<3>", markup, count=1)
        changes.append(f"{key}: {match.group(2)} -> {rendered}")
    if changes:
        page.write_text(markup)
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = parser.parse_args(argv)

    previous = json.loads(STATE.read_text()) if STATE.exists() else {}
    try:
        text = visible_text(fetch())
    except Exception as error:  # noqa: BLE001 - a fetch failure must never break the page
        print(f"source unreachable ({error}); leaving the page untouched")
        return 0

    found = parse(text)
    accepted, rejected = validate(found, previous)
    for note in rejected:
        print(f"rejected: {note}")
    if not accepted:
        print("nothing usable parsed; leaving the page untouched")
        return 0

    print("accepted:", {k: render(k, v) for k, v in accepted.items()})
    if args.dry_run:
        current = {k: v for k, v in previous.items() if k in FIGURES}
        print("current state:", {k: render(k, v) for k, v in current.items()} or "none recorded")
        return 0

    changes = apply_to_page(accepted)
    state = dict(previous)
    state.update(accepted)
    state["checked_at"] = date.today().isoformat()
    state["source"] = SOURCE
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")

    for change in changes:
        print(change)
    print("page updated" if changes else "figures unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
