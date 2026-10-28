"""Real browser workflow: future availability, offline server pause, extension approval and resume."""
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
f=PulseTests();f.setUp();process=None
try:
    account,g1,manager,mc,tech,tc=f.organization()
    g2=f.group(account,'G2',manager['id'])
    second,second_client,_=f.person('USER','SECOND',group=g2)
    second_timer=f.post('/api/timers/start',{},second_client)['id']
    current=datetime.now(timezone.utc)
    ot=f.ot(tc,(current+timedelta(hours=1)).isoformat(),(current+timedelta(hours=2)).isoformat())
    f.approve(mc,'ot',ot)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        tech_context=browser.new_context(viewport={'width':1280,'height':650})
        manager_context=browser.new_context(viewport={'width':1280,'height':650})
        assert tech_context.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
        assert manager_context.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok
        errors=[]
        def page_for(context,route):
            page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
            page.locator('.sidebar [data-page='+route+']').click();page.wait_for_function('()=>!busy');return page
        page=page_for(tech_context,'time')
        expect(page.locator('.ot-availability')).to_contain_text('Timer disponible el')
        expect(page.locator('[data-action=timer-planned]')).to_have_count(0)
        response=tech_context.request.post(base+'/api/timers/start',data={'overtime_id':ot})
        assert response.status==422 and 'disponible desde' in response.json()['detail']
        deadline=datetime.now(timezone.utc)+timedelta(seconds=12)
        with f.server.connection(True) as c:
            c.execute('UPDATE overtime SET scheduled_start=?,scheduled_end=? WHERE id=?',((datetime.now(timezone.utc)+timedelta(seconds=3)).isoformat(),deadline.isoformat(),ot))
        page.close();page=page_for(tech_context,'time')
        expect(page.locator('[data-action=timer-planned]')).to_have_count(1,timeout=8000)
        page.locator('[data-action=timer-planned]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-action=timer-planned]').click()
        expect(page.locator('.timer-card')).to_have_count(1)
        mgr=page_for(manager_context,'teamTime')
        assert mgr.locator('.timer-card').count()==2
        expect(mgr.locator('.timer-list')).to_contain_text('T001');expect(mgr.locator('.timer-list')).to_contain_text('SECOND')
        expect(mgr.locator('.timer-list')).to_contain_text('Grupo G1');expect(mgr.locator('.timer-list')).to_contain_text('Grupo G2')
        # No open pages or API polling: the server clock must still close the exact boundary.
        page.close();mgr.close()
        while datetime.now(timezone.utc)<deadline+timedelta(seconds=1.5):time.sleep(.1)
        with f.server.connection() as c:
            row=dict(c.execute('SELECT * FROM overtime WHERE id=?',(ot,)).fetchone())
            segments=[dict(r) for r in c.execute('SELECT * FROM timers WHERE overtime_id=?',(ot,))]
        assert row['execution']=='PAUSED' and segments[0]['end_at']==deadline.isoformat(),(row,segments)
        page=page_for(tech_context,'time')
        expect(page.locator('.record-card')).to_contain_text('Timer pausado')
        page.locator('[data-action=extension-new]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-action=extension-new]').click()
        field=page.locator('#modal [name=requested_end]');field.evaluate('(el)=>PulseLayout.reveal(el)')
        field.fill((datetime.now(timezone.utc)+timedelta(hours=1)).astimezone(ZoneInfo('America/Mexico_City')).strftime('%Y-%m-%dT%H:%M'))
        page.locator('#modal [name=reason]').fill('El cambio requiere una validación adicional')
        page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        expect(page.locator('[data-action=timer-planned]')).to_have_count(0)
        mgr=page_for(manager_context,'teamTime')
        review=mgr.locator('.extension-review');review.evaluate('(el)=>PulseLayout.reveal(el)')
        expect(review).to_contain_text('T001');expect(review).to_contain_text('Grupo G1');expect(review).to_contain_text('validación adicional')
        review.locator('[data-action=extension-approve]').click();mgr.wait_for_function('()=>!busy')
        page.reload();page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('.timer-card')).to_have_count(0)
        resume=page.locator('[data-action=timer-planned]');resume.evaluate('(el)=>PulseLayout.reveal(el)');expect(resume).to_have_text('▶ Reanudar');resume.click()
        expect(page.locator('.timer-card')).to_have_count(1)
        # A pause received while an extension form is open must appear on cancel.
        page.locator('[data-action=extension-new]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-action=extension-new]').click()
        cutoff=datetime.now(timezone.utc)+timedelta(seconds=1)
        with f.server.connection(True) as c:c.execute('UPDATE overtime SET scheduled_end=? WHERE id=?',(cutoff.isoformat(),ot))
        while datetime.now(timezone.utc)<cutoff+timedelta(seconds=.3):time.sleep(.1)
        page.evaluate('refresh(true)');expect(page.locator('#modal')).to_be_visible()
        page.locator('#modal [data-action=close]').first.click()
        expect(page.locator('.timer-card')).to_have_count(0)
        finish=page.locator('[data-action=paused-finish]');finish.evaluate('(el)=>PulseLayout.reveal(el)');finish.click()
        page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        result=tech_context.request.get(base+'/api/state').json()
        saved=next(o for o in result['overtime'] if o['id']==ot);assert saved['status']=='SUBMITTED'
        assert len([t for t in result['timer_segments'] if t['overtime_id']==ot])==2
        assert saved['worked_seconds']<(datetime.fromisoformat(saved['end_at'])-datetime.fromisoformat(saved['start_at'])).total_seconds()
        assert not errors,errors
        print('PASS: future availability; two simultaneous technicians/Groups visible to Manager; exact server pause with all pages closed; request/approve/resume/finalize through UI, including deferred pause after cancelling an open modal; two segments with waiting excluded; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
