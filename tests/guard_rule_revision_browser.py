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
    rule=f.post('/api/rules',{'name':'Guardia semanal','effective_from':'2026-01-01','segments':[{'day':day,'start':'02:00','end':'04:00'} for day in range(7)]},mc)['id']
    guard=f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-11'},uc)['id']
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
        expect(page.locator('[data-timeline-kind=guard]')).to_have_count(1)
        expect(page.locator('.guard-request-total')).to_contain_text('14 h')
        assert len([g for g in mc.get('/api/state').json()['guards'] if g['status']=='SUBMITTED'])==1
        assert uc.get('/api/accounting?month=2026-01').json()['guard_minutes']==0
        assert mc.put('/api/rules/'+rule,json={'name':'Guardia actualizada','effective_from':'2026-01-01','segments':[{'day':day,'start':'02:00','end':'05:00'} for day in range(7)]}).status_code==200
        page.evaluate('()=>refresh()')
        expect(page.locator('.guard-rule-notice')).to_be_visible()
        page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)')
        expect(page.locator('[data-timeline-id="'+guard+'"]')).to_contain_text('Regla actualizada')
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            card=page.locator('[data-timeline-id="'+guard+'"] article')
            box=card.bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
            if width>600:assert box['height']<185,box
        page.set_viewport_size({'width':1440,'height':780})
        page.screenshot(path='/tmp/pulse-compact-rule-notice.png')
        page.locator('[data-timeline-id="'+guard+'"] [data-action=guard-edit]').click()
        expect(page.locator('#dialog-title')).to_have_text('Revisar Guardia')
        page.locator('#modal [name=reason]').fill('Actualizar la regla de mi Guardia')
        page.locator('#modal [name=confirm]').check()
        page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('#modal')).not_to_be_visible()
        expect(page.locator('.guard-rule-notice')).to_have_count(0)
        page.locator('.personal-timeline').evaluate('(el)=>PulseLayout.reveal(el)')
        expect(page.locator('.guard-request-total')).to_contain_text('21 h')
        expect(page.locator('[data-timeline-kind=guard]')).to_have_count(1)
        page.locator('[data-timeline-kind=guard] [data-action=record-detail]').click()
        expect(page.locator('#modal')).to_contain_text('Guardia actualizada')
        assert not errors,errors
        print('PASS: compact responsive cards, Details retained, live rule-change notice, review and reapproval of same Guard, updated coverage and cleared notice; no JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
