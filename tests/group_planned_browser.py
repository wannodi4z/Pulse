"""A normal planned OT appears to peers, each of whom starts only their own Timer."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from datetime import datetime,timedelta,timezone
from playwright.sync_api import sync_playwright,expect
from test_group_planned_ot import GroupPlannedOTTests
ROOT=Path(__file__).resolve().parents[1]
fixture=GroupPlannedOTTests();fixture.setUp();f=fixture.f;process=None
try:
 start=datetime.now(timezone.utc)+timedelta(seconds=5);end=start+timedelta(minutes=3)
 with f.server.connection(True) as c:
  c.execute('UPDATE overtime SET scheduled_start=?,scheduled_end=? WHERE id=?',(start.isoformat(),end.isoformat(),fixture.ot));f.server.sync_group_ot(c,f.server.get(c,'overtime',fixture.ot))
 wid=fixture.activity()['id']
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':780});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'PEER-GROUP','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
  page.locator('.calendar-event[data-id="group:'+wid+'"]').first.click()
  expect(page.locator('#modal')).to_contain_text('CHG-GROUP-NORMAL')
  play=page.locator('#modal [data-action=group-timer-start]');expect(play).to_be_disabled()
  f.approve(fixture.mc,'ot',fixture.ot);page.evaluate('()=>refresh()');expect(play).to_be_enabled(timeout=9000)
  play.click();page.wait_for_function('()=>!busy');expect(page.locator('#modal .timer-dialog-clock')).to_be_visible()
  own=ctx.request.get(base+'/api/state').json();assert len(own['overtime'])==1;participant=own['overtime'][0]['id'];assert participant!=fixture.ot
  assert len(own['timers'])==1 and own['timers'][0]['user_id']==own['user']['id']
  assert fixture.uc.get('/api/state').json()['overtime'][0]['execution']=='SCHEDULED'
  assert fixture.uc.post('/api/timers/start',json={'overtime_id':fixture.ot}).status_code==200
  assert len(fixture.mc.get('/api/state').json()['timers'])==2
  page.locator('#modal [data-action=timer-stop]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('#modal')).not_to_be_visible()
  assert ctx.request.get(base+'/api/state').json()['overtime'][0]['status']=='SUBMITTED'
  assert len(fixture.uc.get('/api/state').json()['timers'])==1
  assert not errors,errors
  browser.close();print('PASS: automatic planned-OT group visibility, approval/time gating, independent peer Timer from calendar, no duplicate personal activity, own stop and individual hours; no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 fixture.tearDown()
