"""Personal chronology inserts late historical capture by worked date and preserves authorization."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright,expect
import test_api
ROOT=Path(__file__).resolve().parents[1]
f=test_api.PulseTests();f.setUp();process=None
try:
    account,gid,manager,mc,user,uc=f.organization()
    earlier=f.ot(uc,start='2026-01-05T20:00:00-06:00',end='2026-01-05T21:00:00-06:00',reference='CHG-EARLY')
    later=f.ot(uc,start='2026-01-10T20:00:00-06:00',end='2026-01-10T21:00:00-06:00',reference='CHG-LATER')
    future=f.ot(uc,start='2030-01-10T20:00:00-06:00',end='2030-01-10T21:00:00-06:00',reference='CHG-FUTURE')
    f.approve(mc,'ot',future)
    other,oc,_=f.person('USER','T-OTHER',group=gid)
    f.ot(oc,reference='CHG-PRIVATE')
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1280,'height':650});assert context.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
        def set_month(value):
            page.locator('#month').fill(value);page.locator('#month').dispatch_event('change');page.locator('h1').click();page.wait_for_function('()=>!busy')
            page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)')
        set_month('2026-01')
        assert page.locator('[data-timeline-id]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.timelineId)')==[earlier,later]
        backlog=f.ot(uc,start='2026-01-07T20:00:00-06:00',end='2026-01-07T21:00:00-06:00',reference='CHG-BACKLOG')
        expect(page.locator('[data-timeline-id="'+backlog+'"]')).to_have_count(1,timeout=12000)
        assert page.locator('[data-timeline-id]').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.timelineId)')==[earlier,backlog,later]
        expect(page.locator('.personal-timeline')).not_to_contain_text('CHG-PRIVATE')
        expect(page.locator('[data-timeline-id="'+backlog+'"]')).to_contain_text('Captura histórica')
        expect(page.locator('[data-timeline-id="'+backlog+'"]')).to_contain_text('Pendiente')
        assert context.request.get(base+'/api/accounting?month=2026-01').json()['ot_minutes']==0
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight')
            issues=page.locator('.personal-timeline').evaluate('(el)=>{const b=document.querySelector(".viewport-stage").getBoundingClientRect();return [...el.querySelectorAll("button,.timeline-date")].filter(n=>n.getClientRects().length).map(n=>{const r=n.getBoundingClientRect();return {label:n.textContent.slice(0,40),bottom:r.bottom-b.bottom,right:r.right-b.right,left:r.left-b.left}}).filter(r=>r.bottom>2||r.right>1||r.left< -1)}');assert not issues,(width,height,issues)
        page.set_viewport_size({'width':1280,'height':650});set_month('2030-01')
        expect(page.locator('.personal-timeline')).to_contain_text('Planificada');expect(page.locator('.ot-availability')).to_contain_text('2030')
        expect(page.locator('.personal-timeline [data-action=timer-planned]')).to_have_count(0)
        detail=page.locator('.personal-timeline [data-action=record-detail]').first;detail.click();expect(page.locator('#modal')).to_contain_text('CHG-FUTURE')
        assert not errors,errors
        print('PASS: personal timeline sorts by worked date; historical backlog inserted by polling without reload; pending excluded from approved totals; no other technician records; future availability without early Timer; detail; 1440/1280/390 no page scroll; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
