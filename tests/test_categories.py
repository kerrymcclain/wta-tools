import threading, functools, http.server, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
# Usage: python test_x.py SITE_DIR OUT_DIR   (run_all.py passes both)
site=Path(sys.argv[1]).resolve(); out=Path(sys.argv[2]).resolve()
d=str(out)+"/"
H=functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site)); H.log_message=lambda *a:None
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
u=f"http://127.0.0.1:{srv.server_address[1]}/categories/"
ok=True
def check(l,c,x=""):
    global ok; ok&=bool(c); print(("PASS " if c else "FAIL ")+l+(f"  [{x}]" if x else ""))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":900}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    pg.goto(u); pg.wait_for_timeout(500)
    check("all 21 categories", pg.locator(".cat").count()==21, pg.locator(".cat").count())
    def top(q):
        pg.fill("#q",q); pg.wait_for_timeout(250); return pg.eval_on_selector_all(".cat","e=>e.map(x=>x.id)")
    for q,exp in [("mobile home rented land","M1"),("wind turbine","F2"),("hotel","F1"),("XV","X"),("j3","J"),("C1","C1"),("drilling rig","L2"),("caliche","G3"),("barn","D2"),("never occupied","O"),("colonia","C2"),("homestead duplex","A")]:
        r=top(q); check(f"'{q}' -> {exp}", r[:1]==[exp] or (exp in r[:2]), r[:4])
    r=top("zzzz"); check("no match message", pg.is_visible(".empty"))
    pg.fill("#q",""); pg.wait_for_timeout(200)
    pg.click('.cat#A a.xref[data-go="E"]'); pg.wait_for_timeout(400)
    check("xref jumps to E", pg.evaluate("location.hash")=="#E" and abs(pg.evaluate("document.getElementById('E').getBoundingClientRect().top"))<200)
    pg.click('.chip[data-kind="Exempt"]'); pg.wait_for_timeout(200); check("exempt filter", pg.locator(".cat").count()==1)
    pg.click('.cat#X a.xref[data-go="F1"]'); pg.wait_for_timeout(400)
    check("xref out of filtered view resets filter", pg.locator(".cat").count()==21 and pg.evaluate("location.hash")=="#F1")
    pg.goto(u+"#J3"); pg.wait_for_timeout(600); check("deep link #J3 -> J", pg.evaluate("location.hash")=="#J", pg.evaluate("location.hash"))
    href=pg.get_attribute('.cat#X td.sec a','href'); check("X code links to Tax Code Search", href.startswith("/tax-code/#q=Sec.%2011."), href)
    pg.fill("#q","barn d2"); pg.wait_for_timeout(250); check("search with a code word keeps links intact", pg.locator('a.xref[data-go="D2"]').count()>0 and pg.locator('mark').count()>0)
    pg.fill("#q",""); pg.goto(u); pg.wait_for_timeout(400); pg.screenshot(path=d+"cat-d.png")
    m=b.new_page(viewport={"width":390,"height":844}); m.goto(u+"#M1"); m.wait_for_timeout(800)
    check("phone no overflow", m.evaluate("document.documentElement.scrollWidth<=390")); m.screenshot(path=d+"cat-m.png")
    check("no page errors", not errs, errs); b.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
