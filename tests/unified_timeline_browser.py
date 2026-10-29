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
    rule=f.post('/api/rules',{'name':'Cobertura de prueba','effective_from':'2026-01-01','segments':[{'day':0,'start':'02:00','end':'04:00'},{'day':0,'start':'20:00','end':'00:00'},{'day':5,'start':'22:00','end':'02:00'}]},mc)['id']
    pending_guard=f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},uc)['id']
    overnight=f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-31','end_date':'2026-01-31'},uc)['id'];f.approve(mc,'guard',overnight)
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
        expect(page.locator('[data-timeline-kind=guard]')).to_have_count(2);expect(page.locator('[data-timeline-kind=ot]')).to_have_count(2)
        first=page.locator('[data-timeline-id="'+pending_guard+'"]');expect(first.locator('.guard-request-total')).to_contain_text('6 h');expect(first.locator('.guard-coverage')).to_have_count(0);expect(first.locator('.record-title .badge')).to_contain_text('Pendiente')
        assert page.locator('[data-timeline-at]').evaluate_all('(els)=>els.every((el,i)=>!i||Date.parse(el.dataset.timelineAt)>=Date.parse(els[i-1].dataset.timelineAt))')
        first.locator('[data-action=record-detail]').click();expect(page.locator('#modal')).to_contain_text('Cobertura de prueba');page.locator('#modal [data-action=close]').first.click()
        set_month('2026-02');expect(page.locator('[data-timeline-kind=ot]')).to_have_count(0);expect(page.locator('[data-timeline-kind=guard]')).to_have_count(1);expect(page.locator('.personal-timeline')).not_to_contain_text('Sin OT');expect(page.locator('.guard-request-total')).to_contain_text('4 h')
        assert context.request.get(base+'/api/accounting?month=2026-02').json()['guard_minutes']==120
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight')
            assert page.locator('.personal-timeline').evaluate('(el)=>{const s=document.querySelector(".viewport-stage").getBoundingClientRect(),r=el.getBoundingClientRect();return r.right<=s.right+1&&r.bottom<=s.bottom+1}')
        page.set_viewport_size({'width':1280,'height':650});set_month('2026-01');page.screenshot(path='/tmp/pulse103-timeline.png',full_page=True)
        # A future plan shows a real disabled button and enables only after approval and the clock boundary.
        from datetime import datetime,timedelta,timezone
        now=datetime.now(timezone.utc);start=now+timedelta(seconds=5);end=now+timedelta(minutes=2)
        plan=f.ot(uc,start=start.isoformat(),end=end.isoformat(),reference='CHG-CLOCK-ENABLE');set_month(now.astimezone(f.server.TZ).strftime('%Y-%m'));page.evaluate('()=>refresh()');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)')
        record=page.locator('[data-timeline-id="'+plan+'"]');timer=record.locator('[data-action=timer-planned]');expect(timer).to_be_disabled();expect(record.locator('[data-action=extension-new]')).to_have_count(0)
        f.approve(mc,'ot',plan);page.evaluate('()=>refresh()');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('h1').click();expect(timer).to_be_enabled(timeout=9000);expect(record.locator('[data-action=extension-new]')).to_have_count(0)
        timer.click();page.wait_for_function('()=>!busy');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)');record.locator('[data-action=own-timer-open]').click();expect(page.locator('#modal [data-action=extension-new]')).to_be_visible();expect(page.locator('#modal [data-action=timer-stop]')).to_be_visible()
        page.locator('#modal [data-action=extension-new]').click();newend=datetime.now(timezone.utc)+timedelta(minutes=4);page.locator('#modal [name=requested_end]').fill(newend.astimezone(f.server.TZ).strftime('%Y-%m-%dT%H:%M'));page.locator('#modal [name=reason]').fill('Continuar desde el Timer activo');page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible();ext=next(e for e in uc.get('/api/state').json()['extensions'] if e['overtime_id']==plan);f.post('/api/extensions/'+ext['id']+'/decision',{'decision':'APPROVED'},mc)
        with f.server.connection(True) as db:db.execute('UPDATE overtime SET scheduled_end=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(milliseconds=100)).isoformat(),plan))
        page.evaluate('()=>refresh()');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)');record.locator('[data-action=own-timer-open]').click();expect(page.locator('#modal')).to_contain_text('TU TIMER PAUSADO');expect(page.locator('#modal [data-action=extension-new]')).to_be_visible();expect(page.locator('#modal [data-action=timer-planned]')).to_be_disabled();expect(page.locator('#modal [data-action=paused-finish]')).to_be_visible();page.locator('#modal [data-action=close]').first.click()
        # Keep the Timer dialog open across a real deadline: it must show pause without a refresh loop.
        state_requests=[];page.on('request',lambda r:state_requests.append(r.url) if r.url.endswith('/api/state') else None)
        now=datetime.now(timezone.utc);quick=f.ot(uc,start=(now+timedelta(seconds=2)).isoformat(),end=(now+timedelta(seconds=8)).isoformat(),reference='CHG-LIVE-PAUSE');f.approve(mc,'ot',quick);page.evaluate('()=>refresh()');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('h1').click();quickcard=page.locator('[data-timeline-id="'+quick+'"]');expect(quickcard.locator('[data-action=timer-planned]')).to_be_enabled(timeout=5000);quickcard.locator('[data-action=timer-planned]').click();page.wait_for_function('()=>!busy');page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)');quickcard.locator('[data-action=own-timer-open]').click();expect(page.locator('#modal [data-paused-timer="'+quick+'"]')).to_be_visible(timeout=10000);assert len(state_requests)<15,state_requests;page.locator('#modal [data-action=close]').first.click()
        # Readable daily analysis uses exact dates, totals and named categories.
        f.approve(mc,'guard',pending_guard);f.approve(mc,'ot',earlier)
        assert context.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok;page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.locator('h1').click();page.wait_for_function('()=>!busy');page.locator('[data-action=analytics-visuals]').click();expect(page.locator('.daily-hours-row')).to_have_count(2);expect(page.locator('.daily-hours-row').first).to_contain_text('5 ene 2026');expect(page.locator('.daily-hours-row').first).to_contain_text('Guardia neta');assert page.locator('.daily-hours-row meter').evaluate_all('(els)=>els.map(el=>el.value)')==[360,120]
        page.screenshot(path='/tmp/pulse103-daily.png',full_page=True)
        assert not errors,errors
        print('PASS: mixed OT/Guard chronology, multiple intervals, overnight month carry, Guard-only month, pending not billed, detail, responsive bounds, future disabled Timer enabling at clock boundary after approval, extensions only in active/paused Timer, paused controls and live deadline transition without refresh loops, daily dates/exact totals/type breakdown; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
