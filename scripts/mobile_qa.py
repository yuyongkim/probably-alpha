"""Mobile QA — render gazua.yule.pics at iPhone SE / 13 viewports
and report layout problems (horizontal scroll, overflow, broken text)."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://gazua.yule.pics/"
DEVICES = [
    ("iphone_se",  375, 667),   # smallest reasonable target
    ("iphone_13",  390, 844),   # mainstream iOS
    ("pixel_7",    412, 915),   # mainstream Android
    ("desktop",   1440, 900),   # baseline reference
]
OUT_DIR = Path(__file__).parent.parent / "runtime_logs" / "mobile_qa"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, w, h in DEVICES:
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=2,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                ),
            )
            page = ctx.new_page()
            try:
                page.goto(URL, wait_until="networkidle", timeout=30_000)
            except Exception as exc:
                print(f"[{name}] goto FAILED: {exc}")
                ctx.close()
                continue
            # Wait for hero to render
            try:
                page.wait_for_selector("h1", timeout=10_000)
            except Exception:
                pass

            # Layout metrics
            metrics = page.evaluate(
                """() => {
                  const doc = document.documentElement;
                  const body = document.body;
                  const overflowEls = [];
                  // Find any direct or nested element wider than the viewport
                  const all = document.querySelectorAll('*');
                  for (const el of all) {
                    const r = el.getBoundingClientRect();
                    if (r.right > window.innerWidth + 1) {
                      overflowEls.push({
                        tag: el.tagName,
                        cls: (el.className && el.className.toString && el.className.toString().slice(0,80)) || '',
                        right: Math.round(r.right),
                        width: Math.round(r.width),
                      });
                      if (overflowEls.length >= 5) break;
                    }
                  }
                  return {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    docScrollWidth: doc.scrollWidth,
                    docClientWidth: doc.clientWidth,
                    bodyScrollWidth: body.scrollWidth,
                    overflowSample: overflowEls,
                    h1Text: document.querySelector('h1')?.textContent?.trim() || null,
                    accentText: document.querySelector('h1+div')?.textContent?.trim() || null,
                  };
                }"""
            )
            shot_path = OUT_DIR / f"{name}_top.png"
            page.screenshot(path=str(shot_path), full_page=False)
            full_path = OUT_DIR / f"{name}_full.png"
            page.screenshot(path=str(full_path), full_page=True)
            print(f"\n=== {name} {w}x{h} ===")
            print(f"  innerWidth={metrics['innerWidth']}  docScrollWidth={metrics['docScrollWidth']}")
            scroll_diff = metrics["docScrollWidth"] - metrics["innerWidth"]
            print(f"  H-scroll: {scroll_diff}px {'[FAIL OVERFLOW]' if scroll_diff > 1 else '[OK CLEAN]'}")
            if metrics["overflowSample"]:
                print(f"  Overflow elements:")
                for el in metrics["overflowSample"]:
                    print(f"    {el['tag']}.{el['cls'][:40]} right={el['right']} w={el['width']}")
            print(f"  h1: {metrics['h1Text']}")
            print(f"  accent: {metrics['accentText']}")
            print(f"  shot: {shot_path}")
            ctx.close()
        browser.close()
    print(f"\nScreenshots in: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
