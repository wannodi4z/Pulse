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
    for index,ref in enumerate(['CHG-FIRST','CHG-SECOND','CHG-THIRD']):
        f.ot(uc,start=f'2026-01-05T{20+index}:00:00-06:00',end='2026-01-06T00:00:00-06:00',reference=ref)
    _,other,_=f.person('USER','PRIVATE-CALENDAR',group=gid)
    f.ot(other,start='2026-01-05T20:00:00-06:00',end='2026-01-05T21:00:00-06:00',reference='CHG-PRIVATE')
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
        expect(page.locator('.monthly-calendar')).to_be_visible();expect(page.locator('.personal-timeline')).to_have_count(0)
        def calendar_month(value):
            page.locator('#month').fill(value);page.locator('#month').dispatch_event('change');page.locator('h1').click();page.wait_for_function('()=>!busy')
            page.locator('.monthly-calendar').evaluate('(el)=>PulseLayout.reveal(el)')
        def save_ot(ref):
            for name,value in [('reference',ref),('description','Registro desde calendario'),('justification','Cambio'),('impact','Operación'),('in_lieu','Cobertura')]:
                field=page.locator('#modal [name='+name+']');field.evaluate('(el)=>PulseLayout.reveal(el)');field.fill(value)
            for _ in range(15):
                nxt=page.locator('#modal [data-step-next]:visible:not(:disabled)')
                if not nxt.count():break
                nxt.click()
            page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible()
        calendar_month('2026-01')
        day=page.locator('[data-calendar-date="2026-01-05"]')
        expect(day.locator('.calendar-more')).to_contain_text('+3 más')
        day.locator('.calendar-more').click();expect(page.locator('.calendar-agenda-event')).to_have_count(4)
        expect(page.locator('#modal')).not_to_contain_text('CHG-PRIVATE')
        page.locator('#modal [data-action=record-detail]').first.click();expect(page.locator('#dialog-title')).to_have_text('Detalle del registro');page.locator('#modal [data-action=close]').first.click()
        expect(page.locator('[data-calendar-date="2026-01-06"] .calendar-event')).to_have_count(1)
        assert page.locator('.monthly-calendar [data-id="guard:'+guard+'"]').count()==7
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.set_viewport_size({'width':1440,'height':780});page.screenshot(path='/tmp/pulse-calendar-month.png')
        page.locator('[data-calendar-date="2026-01-06"] .calendar-date-button').click()
        expect(page.locator('#modal [name=scheduled_start]')).to_have_value('2026-01-06T09:00')
        expect(page.locator('#ot-type-preview')).to_contain_text('OT histórica')
        save_ot('CHG-CALENDAR-PAST')
        calendar_month('2030-01');page.locator('[data-calendar-date="2030-01-10"] .calendar-date-button').click()
        expect(page.locator('#ot-type-preview')).to_contain_text('OT programada');save_ot('CHG-CALENDAR-FUTURE')
        fresh=uc.get('/api/state').json()
        assert next(o for o in fresh['overtime'] if o['reference']=='CHG-CALENDAR-PAST')['capture_type']=='HISTORICAL'
        assert next(o for o in fresh['overtime'] if o['reference']=='CHG-CALENDAR-FUTURE')['capture_type']=='PLANNED'
        calendar_month('2026-01')
        start=page.locator('[data-calendar-date="2026-01-12"] .calendar-date-button');end=page.locator('[data-calendar-date="2026-01-18"] .calendar-date-button')
        start.scroll_into_view_if_needed();end.scroll_into_view_if_needed();a=start.bounding_box();b=end.bounding_box()
        page.mouse.move(a['x']+10,a['y']+10);page.mouse.down();page.mouse.move(b['x']+10,b['y']+10,steps=15)
        expect(page.locator('.calendar-selected')).to_have_count(7);page.mouse.up()
        expect(page.locator('#modal [data-form=guard]')).to_be_visible()
        expect(page.locator('#modal [name=start_date]')).to_have_value('2026-01-12');expect(page.locator('#modal [name=end_date]')).to_have_value('2026-01-18')
        page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible()
        assert any(g['start_date']=='2026-01-12' and g['end_date']=='2026-01-18' for g in uc.get('/api/state').json()['guards'])
        page.locator('[data-action=calendar-range]').click();page.locator('[data-calendar-date="2026-01-20"] .calendar-date-button').click();page.locator('[data-calendar-date="2026-01-21"] .calendar-date-button').click()
        expect(page.locator('#modal [name=start_date]')).to_have_value('2026-01-20');expect(page.locator('#modal [name=end_date]')).to_have_value('2026-01-21');page.locator('#modal [data-action=close]').first.click()
        page.locator('.monthly-calendar').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-action=calendar-today]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('.calendar-today')).to_have_count(1)
        from datetime import datetime,timedelta,timezone
        now=datetime.now(timezone.utc)
        planned=f.ot(uc,start=(now+timedelta(seconds=4)).isoformat(),end=(now+timedelta(minutes=3)).isoformat(),reference='CHG-DASHBOARD-PLAY')
        page.locator('.sidebar [data-page=dashboard]').click();page.wait_for_function('()=>!busy')
        play=page.locator('.upcoming-activity [data-action=timer-planned][data-id="'+planned+'"]')
        expect(play).to_be_visible();expect(play).to_be_disabled()
        page.wait_for_timeout(4500);expect(play).to_be_disabled()
        f.approve(mc,'ot',planned);page.evaluate('()=>refresh()');expect(play).to_be_enabled()
        play.click();page.wait_for_function('()=>!busy')
        assert any(t['overtime_id']==planned for t in uc.get('/api/state').json()['timers'])
        page.wait_for_timeout(250);page.screenshot(path='/tmp/pulse105-timer-active.png')
        expect(page.locator('#modal [data-action=extension-new]')).to_be_visible()
        expect(page.locator('#modal [data-action=timer-stop]')).to_be_visible()
        with f.server.connection(True) as c:c.execute('UPDATE overtime SET scheduled_end=? WHERE id=?',((datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat(),planned))
        page.locator('#modal [data-action=close]').first.click();page.evaluate('()=>refresh()')
        page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy');page.locator('.monthly-calendar').evaluate('(el)=>PulseLayout.reveal(el)')
        page.locator('.calendar-event[data-id="ot:'+planned+'"]').first.click();page.locator('#modal [data-action=own-timer-open]').click()
        expect(page.locator('#modal [data-paused-timer]')).to_be_visible()
        page.wait_for_timeout(250);page.screenshot(path='/tmp/pulse105-timer-paused.png')
        page.locator('#modal [data-action=extension-new]').click()
        page.locator('#modal [name=requested_end]').fill((datetime.now(timezone.utc)+timedelta(minutes=5)).astimezone(f.server.TZ).strftime('%Y-%m-%dT%H:%M'))
        page.locator('#modal [name=reason]').fill('Ampliar desde el Timer del calendario')
        page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
        extension=next(e for e in uc.get('/api/state').json()['extensions'] if e['overtime_id']==planned)
        f.post('/api/extensions/'+extension['id']+'/decision',{'decision':'APPROVED'},mc)
        page.evaluate('()=>refresh()');page.locator('.monthly-calendar').evaluate('(el)=>PulseLayout.reveal(el)')
        page.locator('.calendar-event[data-id="ot:'+planned+'"]').first.click();page.locator('#modal [data-action=own-timer-open]').click()
        expect(page.locator('#modal [data-action=timer-planned]')).to_be_enabled();page.locator('#modal [data-action=timer-planned]').click();page.wait_for_function('()=>!busy')
        page.locator('#modal [data-action=timer-stop]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('#modal')).not_to_be_visible()
        assert not errors,errors
        print('PASS: monthly own OT/Guard calendar, multi-day coverage, midnight boundary, private records excluded, overflow agenda and details, past/future prefilled forms and persisted classification, Today, drag and keyboard ranges with persisted Guard request, responsive containment, dashboard Timer disabled until approved/time window then starts; no JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
