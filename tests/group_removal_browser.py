"""Admin account workspace, metrics, filters, actions and direct Lead recovery."""
import os, shutil, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
temp=tempfile.TemporaryDirectory();db=Path(temp.name)/'demo.db';shutil.copy(ROOT/'fixtures/banorte_pruebas.sqlite3',db);process=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':780});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert context.request.post(base+'/api/login',data={'identity':'MGR0001','password':'manager12026'}).ok
  state=context.request.get(base+'/api/state').json()
  user=next(p for p in state['people'] if p['employee_id']=='951357');source=user['group_id'];dest=next(g['id'] for g in state['groups'] if g['id']!=source)
  page.goto(base);page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-team-destination="'+source+'"] [data-action=group-edit]').click()
  page.locator('#modal [data-action=group-delete]').click()
  expect(page.locator('#dialog-title')).to_have_text('Eliminar Grupo')
  expect(page.locator('#modal')).to_contain_text('Samuel Alejandro Díaz Chávez')
  for width,height in [(1440,780),(390,844)]:
   page.set_viewport_size({'width':width,'height':height})
   box=page.locator('#modal').bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
  page.set_viewport_size({'width':1440,'height':780})
  page.locator('#modal [name=destination_group_id]').select_option(dest)
  page.locator('#modal [name=reason]').fill('Consolidación de grupos')
  page.locator('#modal [name=confirm]').check()
  page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('#modal')).not_to_be_visible()
  expect(page.locator('[data-team-destination="'+source+'"]')).to_have_count(0)
  expect(page.locator('[data-team-destination="'+dest+'"]')).to_contain_text('Samuel Alejandro Díaz Chávez')
  assert not errors,errors
  browser.close();print('PASS: Group removal review, member destination, responsive dialog and resulting board; no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
