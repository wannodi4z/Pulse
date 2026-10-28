"""Regression for compact status dialogs and automatic OT classification in another browser timezone."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright, expect
from test_api import PulseTests

ROOT=Path(__file__).resolve().parents[1]
fixture=PulseTests();fixture.setUp();process=None
try:
    env={**os.environ,'PULSE_TEST_DB_PATH':str(fixture.server.DB)}
    subprocess.run([sys.executable,'scripts/prepare_test_users.py'],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    with fixture.server.connection() as c:
        before={u['employee_id']:dict(u) for u in c.execute('SELECT * FROM users WHERE employee_id IS NOT NULL')}
    subprocess.run([sys.executable,'scripts/prepare_test_users.py'],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    with fixture.server.connection() as c:
        after={u['employee_id']:dict(u) for u in c.execute('SELECT * FROM users WHERE employee_id IS NOT NULL')}
        assert before==after,'Initialization changed existing test users'
    for emp,password,role,lead in [('MGR0001','manager12026','MANAGER',False),('SL0001','lead120261','USER',True),('951357','tecnico12026','USER',False)]:
        user=fixture.login(fixture.client,emp,password)
        assert user['role']==role and bool(user['is_lead'])==lead and user['status']=='ACTIVE'
    fixture.login(fixture.client,'admin1','admin12026')
    group=next(u['group_id'] for u in before.values() if u['employee_id']=='951357')
    pending=fixture.post('/api/people',{'role':'USER','employee_id':'PENDING','first':'Usuario','last':'Pendiente','email':'pending@example.test','group_id':group})['id']
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(fixture.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        context=browser.new_context(timezone_id='America/Los_Angeles');page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
        def geometry():
            assert page.locator('#modal').evaluate('''el=>{const b=el.getBoundingClientRect();return el.scrollHeight<=el.clientHeight+1&&b.width<=540&&b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight&&[...el.querySelectorAll('input,select,button')].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.left>=b.left&&r.right<=b.right+1&&r.bottom<=b.bottom+1})}''')
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.goto(base);page.locator('.sidebar').wait_for()
            page.evaluate('(id)=>perform("activation-code",id)',pending)
            expect(page.locator('[data-form=confirmation]')).to_be_visible();geometry()
            page.locator('#modal [type=submit]').click();expect(page.locator('.secret-code')).to_be_visible();geometry()
            page.locator('#modal [data-action=close]').first.click()
            for result in ['activate','complete','request']:
                page.evaluate('(kind)=>accessResult(kind,"PENDING")',result);geometry()
                page.locator('#modal [data-action=close]').first.click()
        assert context.request.post(base+'/api/login',data={'identity':'951357','password':'tecnico12026'}).ok
        page.set_viewport_size({'width':1280,'height':650});page.goto(base);page.locator('.sidebar [data-page=time]').click();page.locator('[data-action=ot-new]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-action=ot-new]').click()
        expect(page.locator('[name=capture_type]')).to_have_count(0)
        current=datetime.now(timezone.utc)
        def period(start,end):
            for name,value in [('scheduled_start',start),('scheduled_end',end)]:
                field=page.locator('#modal [name='+name+']');field.evaluate('(el)=>PulseLayout.reveal(el)');field.fill(value.astimezone(ZoneInfo('America/Mexico_City')).strftime('%Y-%m-%dT%H:%M'))
        period(current+timedelta(hours=3),current+timedelta(hours=4));expect(page.locator('#ot-type-preview')).to_contain_text('OT programada')
        period(current-timedelta(minutes=10),current+timedelta(hours=1));expect(page.locator('#ot-type-preview')).to_contain_text('periodo está en curso');assert not page.locator('#modal [name=scheduled_end]').evaluate('(el)=>el.checkValidity()')
        period(current-timedelta(hours=4),current-timedelta(hours=3));expect(page.locator('#ot-type-preview')).to_contain_text('OT histórica')
        for name in ['reference','description','justification','impact','in_lieu']:
            field=page.locator('#modal [name='+name+']');field.evaluate('(el)=>PulseLayout.reveal(el)');field.fill('CHG12345' if name=='reference' else 'Prueba de clasificación automática')
        while page.locator('.wizard-navigation [data-step-next]:not([disabled])').count():page.locator('.wizard-navigation [data-step-next]').click()
        page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        record=context.request.get(base+'/api/state').json()['overtime'][0];assert record['capture_type']=='HISTORICAL' and record['status']=='SUBMITTED'
        assert not errors,errors
        print('PASS: active test-user login/idempotence; compact confirmations/codes/access results at 3 viewports; automatic past/future/ongoing OT in a different browser timezone and persisted historical OT; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    fixture.tearDown()
