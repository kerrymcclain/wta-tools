import sys, threading, functools, http.server
from pathlib import Path
from playwright.sync_api import sync_playwright
site=Path(sys.argv[1]).resolve(); pdf=Path(sys.argv[2]).resolve()
H=functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site)); H.log_message=lambda *a: None
srv=http.server.ThreadingHTTPServer(("127.0.0.1",0),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":1440,"height":900}); errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/tax-code/")
    pg.set_input_files("#fileInput", str(pdf)); pg.wait_for_function("document.getElementById('docMeta').textContent.includes('Edition')", timeout=120000)
    pg.fill("#q","appraisal review board"); pg.press("#q","Enter"); pg.wait_for_timeout(2500)
    y1=pg.evaluate("document.getElementById('viewer').scrollTop"); pn1=pg.inner_text("#pageNo")
    pg.click("#clearBtn"); pg.wait_for_timeout(800)
    y2=pg.evaluate("document.getElementById('viewer').scrollTop"); pn2=pg.inner_text("#pageNo")
    print("after search:", y1, pn1, "| after clear button:", y2, pn2)
    pg.fill("#q","rendition"); pg.press("#q","Enter"); pg.wait_for_timeout(2500)
    y3=pg.evaluate("document.getElementById('viewer').scrollTop")
    pg.fill("#q",""); pg.wait_for_timeout(800)
    y4=pg.evaluate("document.getElementById('viewer').scrollTop"); pn4=pg.inner_text("#pageNo")
    print("after 2nd search:", y3, "| after deleting text:", y4, pn4)
    pg.mouse.move(900,500); pg.mouse.wheel(0,3000); pg.wait_for_timeout(300); pg.fill("#q","x"); pg.wait_for_timeout(500)
    y5=pg.evaluate("document.getElementById('viewer').scrollTop"); print("typing 1 char while browsing keeps position:", y5>0)
    ok = y1>0 and y2==0 and "Page 1 " in pn2 and y3>0 and y4==0 and y5>0 and not errs
    print("errors:", errs or "none"); print("ALL PASS" if ok else "FAIL")
    b.close()
srv.shutdown()
sys.exit(0 if ok else 1)
