"""Drive the Tax Code Search tool in headless Chromium and check the new features."""
import json, os, sys, threading, functools, http.server
from pathlib import Path
from playwright.sync_api import sync_playwright

site, pdf25, pdf24, shots = (Path(a).resolve() for a in sys.argv[1:5])
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
Handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}/tax-code/"
ok = True

def check(label, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + label + (f"  [{extra}]" if extra else ""))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 860})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(base); pg.wait_for_timeout(600)
    check("start card uses edition.json", pg.inner_text("#dlNote") == "2025 edition, about 3 MB", pg.inner_text("#dlNote"))
    check("official link in header", "96-297-25.pdf" in pg.get_attribute("#officialLink", "href"))

    # 2025 test copy: size differs from the Comptroller's file -> "updated copy" notice
    pg.set_input_files("#fileInput", str(pdf25))
    pg.wait_for_function("document.getElementById('docMeta').textContent.includes('Edition')", timeout=20000)
    meta = pg.inner_text("#docMeta")
    check("header shows edition", "2025 Edition" in meta, meta)
    check("no 'posted' date for a non-matching copy", "posted" not in meta)
    check("updated-copy notice shown", pg.is_visible("#notice") and "updated copy" in pg.inner_text("#noticeText"), pg.inner_text("#noticeText"))
    check("official link still visible after load", pg.is_visible("#officialLink"))

    # Search with >99 hits
    pg.fill("#q", "residence homestead"); pg.press("#q", "Enter")
    pg.wait_for_timeout(1500)
    nums = pg.eval_on_selector_all(".hit .num", "els => els.map(e => e.textContent)")
    check("list badges 1..50 on first page", nums[:3] == ["1", "2", "3"] and nums[-1] == "50", f"{len(nums)} badges, last {nums[-1] if nums else None}")
    summ = pg.inner_text("#summary")
    check("more than 99 matches in test", int(summ.split()[0].replace(",", "").rstrip("+")) > 99, summ)
    pg.wait_for_selector(".hl-num.active", timeout=8000)
    act = pg.inner_text(".hl-num.active")
    check("active badge overlaid in PDF", act == "1", act)
    pg.screenshot(path=str(shots / "tcs-results.png"))
    pg.locator(".hl-num.active").screenshot(path=str(shots / "tcs-badge.png"))

    # Page 2 of results: 51..99 numbered, 100 unnumbered
    pg.click("#nextPage"); pg.wait_for_timeout(300)
    nums2 = pg.eval_on_selector_all(".hit .num", "els => els.map(e => e.textContent)")
    hits2 = pg.eval_on_selector_all(".hit", "els => els.length")
    check("badges stop at 99", nums2[0] == "51" and nums2[-1] == "99" and hits2 > len(nums2), f"{nums2[0]}..{nums2[-1]}, {hits2} rows")
    pg.click('.hit[data-i="99"]'); pg.wait_for_timeout(1200)
    check("hit 100 has no PDF badge", pg.locator(".hl-num.active").count() == 0)
    pg.click('.hit[data-i="60"]'); pg.wait_for_timeout(1200)
    check("hit 61 badge in PDF", pg.inner_text(".hl-num.active") == "61")

    # Dismiss sticks across reload (PDF reopens from browser storage)
    pg.click("#noticeClose")
    pg.reload(); pg.wait_for_function("document.getElementById('docMeta').textContent.includes('Edition')", timeout=20000); pg.wait_for_timeout(500)
    check("dismissed notice stays hidden", not pg.is_visible("#notice"))

    # Older edition -> new-edition notice
    pg.set_input_files("#fileInput", str(pdf24))
    pg.wait_for_function("document.getElementById('docMeta').textContent.includes('2024')", timeout=20000); pg.wait_for_timeout(300)
    check("older edition notice", pg.is_visible("#notice") and "2025 edition" in pg.inner_text("#noticeText"), pg.inner_text("#noticeText"))
    pg.screenshot(path=str(shots / "tcs-notice.png"))

    # Matching copy -> no notice, "posted" date shown
    (site / "tax-code" / "edition.json").write_text(json.dumps({"edition": 2025, "file": "96-297-25.pdf",
        "url": "https://comptroller.texas.gov/taxes/property-tax/docs/96-297-25.pdf", "bytes": pdf25.stat().st_size, "posted": "2026-01-07"}))
    pg.set_input_files("#fileInput", str(pdf25)); pg.reload()
    pg.wait_for_function("document.getElementById('docMeta').textContent.includes('posted')", timeout=20000)
    check("matching copy shows posted date, no notice", "posted Jan 7, 2026" in pg.inner_text("#docMeta") and not pg.is_visible("#notice"), pg.inner_text("#docMeta"))

    # Phone layout sanity
    ph = ctx.new_page(); ph.set_viewport_size({"width": 390, "height": 844}); ph.goto(base); ph.wait_for_timeout(1500)
    ph.screenshot(path=str(shots / "tcs-phone.png"))
    check("no horizontal overflow on phone", ph.evaluate("document.documentElement.scrollWidth <= 390"))
    check("no page errors", not errs, "; ".join(errs))
    b.close()
srv.shutdown()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
