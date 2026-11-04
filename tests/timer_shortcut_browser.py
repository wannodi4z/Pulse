"""Desktop links download without credentials and never silently create time records."""
import os,socket,subprocess,sys,time,urllib.request,plistlib
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_analytics_workspace
R=Path(__file__).resolve().parents[1];fixture=test_analytics_workspace.AnalyticsWorkspaceTests();fixture.setUp();proc=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
  page.goto(base+'/?view=timer');expect(page.locator('#modal h2')).to_have_text('Control rápido del Timer');assert ctx.request.get(base+'/api/state').json()['timers']==[]
  page.locator('#modal .dialog-header [data-action=close]').click();page.locator('[data-action=timer-shortcut]').click()
  for fmt,suffix in [('mac','.webloc'),('windows','.url')]:
   page.locator('#modal [name=format]').select_option(fmt)
   with page.expect_download() as download:page.locator('#modal [type=submit]').click()
   file=download.value;assert file.suggested_filename.endswith(suffix);content=Path(file.path()).read_text();assert base+'/?view=timer' in content and 'password' not in content.lower()
   if fmt=='mac':assert plistlib.loads(Path(file.path()).read_bytes())['URL']==base+'/?view=timer'
   else:assert b'\r\n' in Path(file.path()).read_bytes()
   page.locator('[data-action=timer-shortcut]').click()
  page.locator('#modal .dialog-header [data-action=close]').click();page.goto(base+'/?view=timer');expect(page.locator('#modal h2')).to_have_text('Control rápido del Timer');page.locator('#modal [data-action=timer-start]').click();page.locator('#modal [data-form=confirmation] [type=submit]').click();expect(page.locator('#modal.own-timer-dialog')).to_be_visible()
  assert len(ctx.request.get(base+'/api/state').json()['timers'])==1
  page.goto(base+'/?view=timer');expect(page.locator('#modal.own-timer-dialog')).to_be_visible();assert len(ctx.request.get(base+'/api/state').json()['timers'])==1
  ctx.clear_cookies();page.goto(base+'/?view=timer');page.locator('[data-form=login] [name=identity]').fill('T001');page.locator('[data-form=login] [name=password]').fill('Password2026!');page.locator('[data-form=login] [type=submit]').click();expect(page.locator('#modal.own-timer-dialog')).to_be_visible()
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok;page.goto(base+'/?view=timer');expect(page.locator('#toast')).to_contain_text('corresponde a Técnicos');expect(page.locator('#modal')).not_to_be_visible()
  assert not errors,errors;browser.close();print('PASS: macOS/Windows shortcut files, login continuation, active timer reuse, no automatic capture and Manager exclusion')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
