"""Activity desktop files, authenticated continuation and explicit personal Timer start."""
import os,socket,subprocess,sys,time,urllib.request,plistlib
from datetime import datetime,timedelta,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_api
R=Path(__file__).resolve().parents[1];fixture=test_api.PulseTests();fixture.setUp();proc=None
try:
 a,g,m,mc,u,tc=fixture.organization()
 start=datetime.now(timezone.utc)+timedelta(seconds=8)
 record=fixture.ot(tc,start.isoformat(),(start+timedelta(hours=1)).isoformat(),capture_type='PLANNED');fixture.approve(mc,'ot',record)
 own=next(o for o in tc.get('/api/state').json()['overtime'] if o['id']==record);activity=own['window_id'] or record
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';url=base+'/?activity='+activity
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url);page.locator('[data-form=login] [name=identity]').fill('T001');page.locator('[data-form=login] [name=password]').fill('Password2026!');page.locator('[data-form=login] [type=submit]').click();expect(page.locator('#modal h2')).to_contain_text('CHG123456')
  assert ctx.request.get(base+'/api/state').json()['timers']==[]
  page.locator('#modal .dialog-header [data-action=close]').click()
  assert page.locator('[data-action=timer-shortcut]').count()==0
  for fmt,suffix in [('mac','.webloc'),('windows','.url')]:
   page.evaluate('(id)=>timerShortcutModal(id)',activity);page.locator('#modal [name=format]').select_option(fmt)
   with page.expect_download() as download:page.locator('#modal [type=submit]').click()
   file=download.value;assert file.suggested_filename.endswith(suffix);content=Path(file.path()).read_text();assert url in content and 'password' not in content.lower()
   if fmt=='mac':assert plistlib.loads(Path(file.path()).read_bytes())['URL']==url
   else:assert b'\r\n' in Path(file.path()).read_bytes()
  while datetime.now(timezone.utc)<start:page.wait_for_timeout(200)
  page.goto(url);expect(page.locator('#modal [data-action=activity-timer-start]')).to_be_enabled();page.locator('#modal [data-action=activity-timer-start]').click();expect(page.locator('#modal.own-timer-dialog')).to_be_visible()
  assert len(ctx.request.get(base+'/api/state').json()['timers'])==1
  page.goto(url);expect(page.locator('#modal.own-timer-dialog')).to_be_visible();assert len(ctx.request.get(base+'/api/state').json()['timers'])==1
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok;page.goto(url);expect(page.locator('#modal')).not_to_be_visible()
  assert not errors,errors;browser.close();print('PASS: contextual macOS/Windows activity files, login continuation, explicit start, active Timer reuse, no generic button/no automatic capture and Manager exclusion')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
