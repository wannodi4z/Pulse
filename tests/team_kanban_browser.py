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
  assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
  state=context.request.get(base+'/api/state').json();account=next(a for a in state['accounts'] if a['base_code']=='BNTE');aid=account['id']
  page.goto(base)
  def go(name):page.locator('.sidebar [data-page='+name+']').click();page.wait_for_function('()=>!busy')
  def fill(name,value):
   node=page.locator('#modal [name='+name+']');node.evaluate('(el)=>PulseLayout.reveal(el)');node.fill(value)
  def save():
   for _ in range(20):
    nxt=page.locator('[data-step-next]:visible:not(:disabled)')
    if not nxt.count():break
    nxt.click()
   page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  assert context.request.post(base+'/api/login',data={'identity':'MGR0001','password':'manager12026'}).ok
  page.goto(base);page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy')
  state=context.request.get(base+'/api/state').json();u=next(p for p in state['people'] if p['employee_id']=='951357');source=u['group_id'];target=next(g for g in state['groups'] if g['id']!=source)
  expect(page.locator('.team-lane')).to_have_count(6);expect(page.locator('.team-board-lead')).to_contain_text('SL0001');expect(page.locator('.team-tech-card')).to_have_count(3)
  page.locator('[data-action=delegation-inline]').click();page.locator('[data-form=delegation] [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('.team-delegation-active')).to_be_visible();page.locator('[data-action=delegation-revoke]').click();page.wait_for_function('()=>!busy');expect(page.locator('.team-delegation-active')).to_have_count(0)
  page.locator('#team-board-search').fill('951357');expect(page.locator('.team-tech-card:visible')).to_have_count(1);page.locator('#team-board-search').fill('')
  card=page.locator('[data-team-person="'+u['id']+'"]');lane=page.locator('[data-team-destination="'+target['id']+'"]');card.drag_to(lane);expect(page.locator('#modal')).to_be_visible();expect(page.locator('#modal [name=request_group]')).to_have_value(target['id']);expect(page.locator('#request-route-target')).to_have_text(target['name'])
  assert context.request.get(base+'/api/state').json()['transfer_requests']==[]
  page.locator('#modal [data-action=close]').first.click();assert next(p for p in context.request.get(base+'/api/state').json()['people'] if p['id']==u['id'])['group_id']==source
  # Keyboard-accessible alternative opens the same pre-submission flow.
  card.locator('[data-action=transfer-request-new]').focus();page.keyboard.press('Enter');expect(page.locator('#modal')).to_be_visible();page.locator('#modal [name=request_group]').select_option(target['id']);reason=page.locator('#modal [name=reason]');reason.evaluate('(el)=>PulseLayout.reveal(el)');reason.fill('Redistribución de cobertura de especialidades')
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150);box=page.locator('#modal').bounding_box();assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight')
   assert page.locator('#modal .form-body').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1&&el.scrollHeight<=el.clientHeight+1')
  page.set_viewport_size({'width':1280,'height':650});page.wait_for_timeout(150);save();expect(page.locator('#modal')).not_to_be_visible();state=context.request.get(base+'/api/state').json();request=state['transfer_requests'][0];assert request['status']=='SUBMITTED' and target['name'] in request['destination'];assert next(p for p in state['people'] if p['id']==u['id'])['group_id']==source
  expect(page.locator('[data-team-person="'+u['id']+'"]')).to_contain_text('1 cambio solicitado')
  page.locator('.heading-actions [data-action=transfer-requests]').click();expect(page.locator('#dialog-title')).to_have_text('Cambios solicitados');expect(page.locator('#modal')).to_contain_text('Redistribución de cobertura');page.locator('#modal [data-action=close]').first.click()
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight');assert page.locator('.team-kanban-workspace').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
  page.set_viewport_size({'width':1440,'height':780});page.screenshot(path='/tmp/pulse130-kanban.png',full_page=True)
  # Admin inbox remains discoverable and applies the request using the existing transfer flow.
  assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok;page.goto(base);page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy');page.locator('.heading-actions [data-action=transfer-requests]').click();page.locator('[data-action=transfer-request-review]').click();node=page.locator('#modal [name=group_id]');node.evaluate('(el)=>PulseLayout.reveal(el)');node.select_option(target['id']);save();expect(page.locator('#modal')).not_to_be_visible()
  state=context.request.get(base+'/api/state').json();assert next(p for p in state['people'] if p['id']==u['id'])['group_id']==target['id'];assert next(r for r in state['transfer_requests'] if r['id']==request['id'])['status']=='APPROVED'
  assert not errors,errors
  print('PASS: real native drag, cancel without writes, keyboard alternative, search, prefilled destination, Manager request without transfer, pending badge, request history, Admin inbox and confirmed transfer; responsive bounds at 1440/1280/390; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
