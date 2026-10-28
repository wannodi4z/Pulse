"""Requested BNTE users, direct Lead UI and account-specific specialty catalogue."""
import os
from pathlib import Path
import socket,subprocess,sys,time,urllib.request
from playwright.sync_api import sync_playwright,expect
import test_api
ROOT=Path(__file__).resolve().parents[1]
f=test_api.PulseTests();f.setUp();process=None
try:
    subprocess.run([sys.executable,'scripts/prepare_banorte_users.py'],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},check=True,stdout=subprocess.DEVNULL)
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1280,'height':650});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def login(identity,password):
            result=context.request.post(base+'/api/login',data={'identity':identity,'password':password});assert result.ok,result.text();page.goto(base)
        def save():
            for _ in range(20):
                n=page.locator('[data-step-next]:visible:not(:disabled)')
                if not n.count():break
                n.click()
            page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        login('SL0001','lead120261');state=context.request.get(base+'/api/state').json();assert state['user']['is_lead'] and state['user']['group_id'] is None
        page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy');expect(page.locator('[data-action=guard-new]')).to_have_count(0)
        assert context.request.post(base+'/api/guards',data={}).status==403
        ot=context.request.post(base+'/api/overtime',data={'scheduled_start':'2026-01-05T20:00:00-06:00','scheduled_end':'2026-01-05T22:00:00-06:00','reference':'CHG-LEAD-OT','description':'Trabajo del Lead','justification':'Cambio requerido','impact':'Servicio','in_lieu':'Cobertura'});assert ot.ok,ot.text();oid=ot.json()['id']
        login('MGR0001','manager12026');page.locator('.sidebar [data-page=teamTime]').click();expect(page.locator('#main')).to_contain_text('CHG-LEAD-OT')
        page.locator('[data-action=approve]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('#main')).not_to_contain_text('CHG-LEAD-OT')
        page.locator('.sidebar [data-page=team]').click();expect(page.locator('#main')).to_contain_text('SL0001');page.locator('[data-action=delegation-inline]').click()
        page.locator('[data-form=delegation] [type=submit]').click();page.wait_for_function('()=>!busy')
        login('SL0001','lead120261');assert context.request.get(base+'/api/state').json()['can_approve'];assert context.request.post(base+'/api/approvals/ot/'+oid,data={'decision':'APPROVED'}).status==403
        login('951357','tecnico12026');page.locator('.sidebar [data-page=time]').click();expect(page.locator('[data-action=guard-new]')).to_have_count(1)
        login('admin1','admin12026');page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('.direct-lead-person')).to_contain_text('SL0001');expect(page.locator('.group-card .technician')).not_to_contain_text('SL0001')
        page.locator('[data-action=transfer-requests]').click();expect(page.locator('#modal')).to_have_class('compact-dialog')
        assert page.locator('#modal').evaluate('(el)=>el.getBoundingClientRect().width<=570&&el.getBoundingClientRect().height<=430')
        page.locator('#modal [data-action=close]').first.click()
        page.locator('[data-action=group-new]:visible').first.click()
        expect(page.locator('#modal select[name=platform_code]')).to_have_count(0)
        page.locator('#modal [name=service_key]').fill('Linux y Oracle');page.locator('#modal [name=name]').fill('Distribuidos · Producción')
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
            assert page.locator('#modal').evaluate('(el)=>{const b=el.getBoundingClientRect();return b.width<=680&&b.height<=innerHeight&&b.left>=0&&b.right<=innerWidth&&[...el.querySelectorAll("input,button,select")].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.left>=b.left-1&&r.right<=b.right+1&&r.bottom<=b.bottom+1})}')
        page.set_viewport_size({'width':1280,'height':650});page.wait_for_timeout(100);save();state=context.request.get(base+'/api/state').json()
        assert any(g['display_code']=='MX-BNTE-LINUX-Y-ORACLE' for g in state['groups'])
        assert any(s['name']=='Linux y Oracle' for s in state['specialties'])
        page.locator('[data-action=group-new]:visible').first.click();expect(page.locator('#service-catalog option[value="Linux y Oracle"]')).to_have_count(1)
        assert not errors,errors
        print('PASS: three requested active logins; direct Lead outside Groups; own OT approved by Manager; no Lead Guards; delegation grants team authority without self-approval; normal Technician Guards; compact empty requests; custom account catalogue and generated code; 1440/1280/390 modal bounds; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
