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
  page.goto(base);page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-action=team-details]').first.click()
  expect(page.locator('#modal [data-action=person-edit]')).to_be_visible()
  page.locator('#modal [data-action=person-edit]').click()
  page.locator('#modal [name=email]').fill('updated-tech@example.test')
  page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('#modal')).not_to_be_visible()
  page.locator('[data-action=team-details]').first.click()
  expect(page.locator('#modal')).to_contain_text('updated-tech@example.test')
  for width,height in [(1440,780),(390,844)]:
   page.set_viewport_size({'width':width,'height':height})
   for action in ['person-edit','team-move','person-offboard','close']:
    button=page.locator('#modal [data-action='+action+']').last
    expect(button).to_be_visible()
    box=button.bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
   sizes=page.locator('.technician-sheet-options button').evaluate_all('(buttons)=>buttons.slice(0,2).map(b=>b.getBoundingClientRect().height)')
   assert abs(sizes[0]-sizes[1])<1,sizes
  page.set_viewport_size({'width':1440,'height':780})
  page.locator('#modal [data-action=person-offboard]').click()
  expect(page.locator('#modal [name=reason]')).to_be_visible()
  page.locator('#modal [name=reason]').fill('Fin de asignación de prueba')
  page.locator('#modal [name=confirm]').check()
  page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('#modal')).not_to_be_visible()
  page.evaluate('lastInteraction=Date.now()-300001')
  expect(page.locator('.sidebar')).not_to_be_visible(timeout=5000)
  expect(page.locator('#toast')).to_contain_text('inactividad')
  assert context.request.get(base+'/api/state').status==401
  assert not errors,errors
  browser.close();print('PASS: Manager Technician offboarding UI and five-minute idle logout; no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
