"""
gmaps-list-export
=================
Export a Google Maps shared/saved place list to CSV, Markdown or JSON.

Google Maps lets you share a saved list, but gives you no way to get the places
out of it. The list is lazy-loaded into a virtualised sidebar, so there is no
page you can copy from and no public API. This drives a real browser, scrolls
the sidebar until nothing new appears, and writes the result to a file.

Usage:
    pip install -r requirements.txt
    playwright install chromium
    python gmaps_list_export.py --url "https://maps.app.goo.gl/..." -o tokyo.csv
"""

import argparse
import asyncio
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright

# Google Maps place URLs embed coordinates as !3d<lat>!4d<lng>
_COORD_RE = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")

# The sidebar container has changed class names over the years; try in order.
_SIDEBAR_SELECTORS = (
    'div[role="feed"]',
    "div.m6QErb",
    'div[data-value="Saved places"]',
    ".section-scrollbox",
)

# Stop after this many consecutive scrolls that surface no new places.
_STABLE_ROUNDS = 5


def _parse_coords(url: str):
    """Best-effort lat/lng extraction from a Maps place URL."""
    m = _COORD_RE.search(url or "")
    return (m.group(1), m.group(2)) if m else ("", "")


async def scrape_list(
    url: str,
    headless: bool = False,
    scroll_pause: float = 1.5,
    locale: str = "zh-TW",
) -> List[Dict[str, str]]:
    places: Dict[str, Dict[str, str]] = {}

    async with async_playwright() as p:
        # headless=True often fails to render the lazy-loaded sidebar at all,
        # so interactive is the default. Override at your own risk.
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900}, locale=locale
        )
        page = await context.new_page()

        print(f"[INFO] opening {url}")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)

        sidebar = None
        for sel in _SIDEBAR_SELECTORS:
            sidebar = await page.query_selector(sel)
            if sidebar:
                print(f"[INFO] sidebar found: {sel}")
                break
        if not sidebar:
            print("[WARN] sidebar not found — falling back to whole-page scroll")

        stable = 0
        prev = 0
        print("[INFO] scrolling...")

        while stable < _STABLE_ROUNDS:
            for item in await page.query_selector_all("a[aria-label]"):
                href = await item.get_attribute("href") or ""
                if "/maps/place/" not in href:
                    continue
                name = await item.get_attribute("aria-label")
                if not name or name in places:
                    continue
                lat, lng = _parse_coords(href)
                places[name] = {"name": name, "url": href, "lat": lat, "lng": lng}

            count = len(places)
            print(f"\r[INFO] {count} places", end="", flush=True)

            stable = stable + 1 if count == prev else 0
            prev = count

            target = sidebar or page
            await target.evaluate(
                "el => el.scrollBy(0, 800)" if sidebar else "() => window.scrollBy(0, 800)"
            )
            await asyncio.sleep(scroll_pause)

        await browser.close()

    print(f"\n[DONE] {len(places)} places")
    return [dict(p, index=i + 1) for i, p in enumerate(places.values())]


def write_csv(rows: List[Dict[str, str]], path: Path) -> None:
    # utf-8-sig so Excel on Windows opens CJK names correctly
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["index", "name", "lat", "lng", "url"])
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in w.fieldnames} for r in rows)


def write_markdown(rows: List[Dict[str, str]], path: Path, title: str) -> None:
    out = [
        f"# {title}",
        f"\n> {len(rows)} places · exported {time.strftime('%Y-%m-%d %H:%M')}\n",
        "| # | Place | Coordinates | Link |",
        "|---|-------|-------------|------|",
    ]
    for r in rows:
        name = r["name"].replace("|", "｜")
        coords = f"{r['lat']}, {r['lng']}" if r["lat"] else ""
        out.append(f"| {r['index']} | {name} | {coords} | [open]({r['url']}) |")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_json(rows: List[Dict[str, str]], path: Path) -> None:
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Export a Google Maps shared list to CSV / Markdown / JSON."
    )
    ap.add_argument("--url", required=True, help="Google Maps shared list URL")
    ap.add_argument(
        "-o", "--output", default="places.csv",
        help="output path; extension picks the format unless --format is given "
             "(default: places.csv)",
    )
    ap.add_argument(
        "-f", "--format", choices=["csv", "md", "json", "all"],
        help="output format; 'all' writes every format alongside --output",
    )
    ap.add_argument("--title", default="Google Maps list", help="title for Markdown output")
    ap.add_argument("--headless", action="store_true",
                    help="run without a visible browser (often fails to load the list)")
    ap.add_argument("--locale", default="zh-TW", help="browser locale (default: zh-TW)")
    ap.add_argument("--scroll-pause", type=float, default=1.5,
                    help="seconds to wait between scrolls (default: 1.5)")
    args = ap.parse_args()

    out = Path(args.output)
    fmt = args.format or {".csv": "csv", ".md": "md", ".json": "json"}.get(
        out.suffix.lower(), "csv"
    )

    rows = asyncio.run(
        scrape_list(args.url, headless=args.headless,
                    scroll_pause=args.scroll_pause, locale=args.locale)
    )
    if not rows:
        print("[ERROR] no places found — is the list public and the URL correct?",
              file=sys.stderr)
        return 1

    writers = {
        "csv": lambda p: write_csv(rows, p),
        "md": lambda p: write_markdown(rows, p, args.title),
        "json": lambda p: write_json(rows, p),
    }
    for f in (["csv", "md", "json"] if fmt == "all" else [fmt]):
        p = out.with_suffix("." + f)
        writers[f](p)
        print(f"[SAVED] {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
