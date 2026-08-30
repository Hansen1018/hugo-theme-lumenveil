#!/usr/bin/env python3
"""Verify theme renders correctly in dark mode.

Override BASE_URL to test fork/staging (default: production blog).
Default port + output dir can be overridden via env vars.
"""
import argparse
import os
import sys
import logging
from contextlib import contextmanager
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("dark-check")

DEFAULT_BASE = os.environ.get("BASE_URL", "http://localhost:1313")
DEFAULT_OUT = os.environ.get("OUT_DIR", "./artifacts")


@contextmanager
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        try:
            yield b
        finally:
            b.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--theme", choices=["light", "dark"], default="dark")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    target = f"{args.base_url.rstrip('/')}/archives/2020/12/2020-retro/"

    with browser() as b:
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(args.base_url + "/", wait_until="networkidle", timeout=30000)
        page.evaluate(
            f"localStorage.setItem('lumenveil-theme', '{args.theme}')"
        )
        page.goto(target, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)
        page.evaluate(
            "document.querySelector('.article-share').scrollIntoView({block:'center'})"
        )
        page.wait_for_timeout(600)
        diag = page.evaluate(
            """() => {
                const s = document.querySelector('.article-share');
                const cs = getComputedStyle(s);
                const r = s.getBoundingClientRect();
                return {
                    color: cs.color, bg: cs.backgroundColor, border: cs.border,
                    zIndex: cs.zIndex, position: cs.position,
                    rect: {top: r.top, w: r.width, h: r.height},
                    dataTheme: document.documentElement.getAttribute('data-theme')
                };
            }"""
        )
        log.info("DARK DIAG: %s", diag)
        out_path = os.path.join(args.out_dir, f"share-{args.theme}.png")
        page.screenshot(path=out_path, full_page=False)
        log.info("saved %s", out_path)

        expected = args.theme
        if diag["dataTheme"] != expected:
            log.error("expected data-theme=%s, got %s", expected, diag["dataTheme"])
            return 1
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log.exception("dark-check failed: %s", e)
        sys.exit(2)
