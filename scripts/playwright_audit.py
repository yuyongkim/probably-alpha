"""Playwright frontend audit: visit every page, collect console errors,
network failures, and rendering problems. Output bug_report.json."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

BASE = "http://127.0.0.1:8080"
PAGES = [
    ("/index.html", "Dashboard"),
    ("/market-wizards-korea.html", "Market Wizards Korea"),
    ("/market-wizards.html", "Market Wizards"),
    ("/market-wizards-people.html", "Market Wizards People"),
    ("/wizard-screener.html", "Wizard Screener"),
    ("/glossary.html", "Glossary"),
]
WAIT_MS = 5000  # wait for async renders


def audit_page(page, url: str, label: str) -> dict:
    console_errors: list[dict] = []
    network_errors: list[dict] = []
    render_issues: list[dict] = []

    def on_console(msg):
        if msg.type in ("error", "warning"):
            console_errors.append({
                "type": msg.type,
                "text": msg.text,
                "url": msg.location.get("url", "") if hasattr(msg, "location") and msg.location else "",
                "line": msg.location.get("lineNumber", 0) if hasattr(msg, "location") and msg.location else 0,
            })

    def on_response(resp):
        if resp.status >= 400:
            network_errors.append({
                "url": resp.url,
                "status": resp.status,
                "statusText": resp.status_text,
            })

    def on_request_failed(req):
        network_errors.append({
            "url": req.url,
            "status": 0,
            "statusText": req.failure or "request failed",
        })

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)

    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
    except PwTimeout:
        render_issues.append({"issue": "page load timeout", "selector": "", "detail": f"networkidle not reached within 30s"})

    # Extra wait for JS renders
    page.wait_for_timeout(WAIT_MS)

    # Check for empty-state elements
    for el in page.query_selector_all(".empty-state"):
        text = (el.inner_text() or "").strip()[:200]
        if text:
            render_issues.append({"issue": "empty state block", "selector": ".empty-state", "detail": text})

    # Check for error messages (p.bad or div.bad, not span.bad which is used for low scores)
    for el in page.query_selector_all("p.bad, div.bad"):
        text = (el.inner_text() or "").strip()[:200]
        if text:
            render_issues.append({"issue": "error message element", "selector": "p.bad/div.bad", "detail": text})

    # Check key containers are not empty
    key_containers = {
        "/index.html": [
            ("#sectorRows", "confirmed sector rows"),
            ("#watchSectorRows", "watchlist sector rows"),
            ("#confirmedStockRows", "confirmed stock rows"),
            ("#sectorGroupedView", "sector leaders at a glance"),
            ("#briefingBox", "daily briefing"),
        ],
        "/market-wizards-korea.html": [
            ("#presetSectorRows", "preset sector rows"),
            ("#presetStockRows", "preset stock rows"),
        ],
    }
    path = url.replace(BASE, "")
    for sel, desc in key_containers.get(path, []):
        el = page.query_selector(sel)
        if el:
            inner = (el.inner_text() or "").strip()
            children = el.query_selector_all("tr, article, div")
            if not inner and not children:
                render_issues.append({"issue": "empty container", "selector": sel, "detail": f"{desc} has no content"})

    # Check for broken images / SVGs
    broken_imgs = page.evaluate("""() => {
        const issues = [];
        document.querySelectorAll('img').forEach(img => {
            if (!img.complete || img.naturalWidth === 0)
                issues.push({src: img.src, alt: img.alt});
        });
        return issues;
    }""")
    for img in broken_imgs:
        render_issues.append({"issue": "broken image", "selector": "img", "detail": f"src={img['src']}"})

    # Check for JS errors in page context
    js_errors = page.evaluate("""() => {
        return window.__playwright_errors || [];
    }""")

    page.remove_listener("console", on_console)
    page.remove_listener("response", on_response)
    page.remove_listener("requestfailed", on_request_failed)

    return {
        "page": label,
        "url": url,
        "console_errors": console_errors,
        "network_errors": network_errors,
        "render_issues": render_issues,
    }


def main():
    out_path = Path("bug_report.json")
    results = []
    summary = {"total_pages": len(PAGES), "pages_with_errors": 0, "total_console_errors": 0, "total_network_errors": 0, "total_render_issues": 0}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})

        # Inject error collector before any page loads
        context.add_init_script("""
            window.__playwright_errors = [];
            window.addEventListener('error', e => {
                window.__playwright_errors.push({message: e.message, filename: e.filename, lineno: e.lineno});
            });
        """)

        page = context.new_page()

        for path, label in PAGES:
            url = f"{BASE}{path}"
            print(f"[AUDIT] {label} ({url})...")
            result = audit_page(page, url, label)
            results.append(result)

            errs = len(result["console_errors"]) + len(result["network_errors"]) + len(result["render_issues"])
            if errs:
                summary["pages_with_errors"] += 1
            summary["total_console_errors"] += len(result["console_errors"])
            summary["total_network_errors"] += len(result["network_errors"])
            summary["total_render_issues"] += len(result["render_issues"])

            status = f"console={len(result['console_errors'])} network={len(result['network_errors'])} render={len(result['render_issues'])}"
            print(f"  -> {status}")

        # Also test Market Wizards Korea with different presets
        preset_hashes = ["#ed-seykota", "#stan-druckenmiller", "#paul-tudor-jones", "#william-oneil", "#nicolas-darvas", "#jesse-livermore"]
        for h in preset_hashes:
            url = f"{BASE}/market-wizards-korea.html{h}"
            label = f"MW Korea {h}"
            print(f"[AUDIT] {label}...")
            result = audit_page(page, url, label)
            results.append(result)
            errs = len(result["console_errors"]) + len(result["network_errors"]) + len(result["render_issues"])
            if errs:
                summary["pages_with_errors"] += 1
            summary["total_console_errors"] += len(result["console_errors"])
            summary["total_network_errors"] += len(result["network_errors"])
            summary["total_render_issues"] += len(result["render_issues"])
            status = f"console={len(result['console_errors'])} network={len(result['network_errors'])} render={len(result['render_issues'])}"
            print(f"  -> {status}")

        summary["total_pages"] += len(preset_hashes)
        browser.close()

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "results": results,
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] {out_path} written")
    print(f"  Pages: {summary['total_pages']} | With errors: {summary['pages_with_errors']}")
    print(f"  Console errors: {summary['total_console_errors']}")
    print(f"  Network errors: {summary['total_network_errors']}")
    print(f"  Render issues: {summary['total_render_issues']}")


if __name__ == "__main__":
    main()
