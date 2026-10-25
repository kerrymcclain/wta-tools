import threading, functools, http.server, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
# Usage: python test_x.py SITE_DIR OUT_DIR   (run_all.py passes both)
site=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
d=str(out)+"/"
H=functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site)); H.log_message=lambda *a:None
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
u=f"http://127.0.0.1:{srv.server_address[1]}/tax-calendar/"
ok=True
def check(l,c,x=""):
    global ok; ok&=bool(c); print(("PASS " if c else "FAIL ")+l+(f"  [{x}]" if x else ""))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":900}, accept_downloads=True); errs=[]
    pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(u+"?year=2026"); pg.wait_for_timeout(600)
    n=pg.locator(".item").count(); check("2026 list renders", n>80, n)
    # Feb 1 2026 is a Sunday -> Feb 2
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('Last year’s taxes become delinquent')).map(e=>e.querySelector('.d').textContent+' | '+(e.querySelector('.roll')?.textContent||''))[0]""")
    check("Feb 1 2026 (Sun) rolls to Feb 2", t.startswith("Feb 2") and "Sunday" in t, t)
    # May 15 2027 is Saturday -> May 17
    pg.select_option("#yearSel","2027"); pg.wait_for_timeout(300)
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('Protest deadline for most property')).map(e=>e.querySelector('.d').textContent+' | '+e.querySelector('.roll')?.textContent)[0]""")
    check("May 15 2027 (Sat) protest rolls to Mon May 17", t.startswith("May 17"), t)
    # Holiday: Jun 19 2026 (Fri, Juneteenth) - nothing due; test Dec 31 2027 Friday: none. Test Jul 4 2027 Sunday -> no deadline; use Sep 14 2025? Year range limited. Check Jan 1 2027 status items not rolled.
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('Tax lien attaches')).map(e=>e.querySelector('.d').textContent+'|'+!!e.querySelector('.roll'))[0]""")
    check("status date Jan 1 not rolled", t=="Jan 1|false", t)
    # Thanksgiving: Nov 30 2025? Year 2028: Nov 30 2028 Thursday. Check Dec 24-26: Dec 31 2028 Sunday -> Jan 1 2029 holiday -> Jan 2 2029
    pg.select_option("#yearSel","2028"); pg.wait_for_timeout(300)
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('goods-in-transit')).map(e=>e.querySelector('.d').textContent+' | '+e.querySelector('.roll')?.textContent)[0]""")
    check("Dec 31 2028 (Sun) rolls past New Year's to Jan 2", t.startswith("Jan 2") and "New Year" in t, t)
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('cooperative housing')).map(e=>e.querySelector('.when').textContent)[0]""")
    check("Feb last day 2028 is Feb 29 (Tue)", "Feb 29" in t, t.strip())
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('directors begin two-year')).length""")
    check("even-year item shows in 2028", t==1)
    pg.select_option("#yearSel","2027"); pg.wait_for_timeout(300)
    t=pg.evaluate("""[...document.querySelectorAll('.item')].filter(e=>e.textContent.includes('directors begin two-year')).length""")
    check("even-year item hidden in 2027", t==0)
    # filters
    pg.click('.chip[data-aud="ARB"]'); pg.wait_for_timeout(200)
    tags=pg.evaluate("[...document.querySelectorAll('.item')].every(e=>e.querySelector('.tag.ARB'))")
    check("ARB filter", tags and pg.locator(".item").count()>=5, pg.locator(".item").count())
    pg.click('.chip[data-aud="all"]'); pg.check("#keyOnly"); pg.wait_for_timeout(200)
    kc=pg.locator(".item").count(); check("key dates only", 10<kc<30, kc)
    pg.uncheck("#keyOnly"); pg.fill("#q","41.44"); pg.wait_for_timeout(300)
    check("search by section", pg.locator(".item").count()==1)
    href=pg.get_attribute(".item .secs a","href"); check("section link to Tax Code Search", href=="/tax-code/#q=Sec.%2041.44", href)
    pg.fill("#q",""); pg.wait_for_timeout(200)
    items=pg.locator(".item").count()
    with pg.expect_download() as dl: pg.click("#icsBtn")
    path=dl.value.path(); txt=open(path,encoding="utf-8",newline="").read()
    check("ics export", txt.startswith("BEGIN:VCALENDAR") and txt.count("BEGIN:VEVENT")==items and "\r\n" in txt, f"{txt.count(chr(66)+'EGIN:VEVENT')} events vs {items} items, file {dl.value.suggested_filename}")
    long=[l for l in txt.split("\r\n") if len(l.encode())>75]; check("ics lines folded", not long, long[:1])
    # current-year next-up
    pg.goto(u); pg.wait_for_timeout(500)
    check("next-up shown for current year", pg.is_visible("#next"), pg.inner_text("#next"))
    pg.screenshot(path=d+"cal-d.png")
    m=b.new_page(viewport={"width":390,"height":844}); m.goto(u); m.wait_for_timeout(800)
    check("phone no overflow", m.evaluate("document.documentElement.scrollWidth<=390")); m.screenshot(path=d+"cal-m.png")
    check("no page errors", not errs, errs)
    b.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
