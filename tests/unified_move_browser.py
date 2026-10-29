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
  page.goto(base);go('team');state=context.request.get(base+'/api/state').json();tech=next(p for p in state['people'] if p['employee_id']=='951357');foreign=next(m for m in state['manager_directory'] if m['employee_id']=='MGR0002');same=next(m for m in state['manager_directory'] if m['employee_id']=='MGR0003')
  page.locator('[data-team-person="'+tech['id']+'"] [data-action=team-details]').last.click();expect(page.locator('#modal [data-action=team-move]')).to_have_count(1);expect(page.locator('#modal [data-action=manager-transfer-new]')).to_have_count(0);page.locator('#modal [data-action=team-move]').click();expect(page.locator('#dialog-title')).to_have_text('Mover Técnico');fill('reason','Motivo conservado entre filtros y tipos de movimiento')
  page.locator('[data-action=move-mode][data-id=external]').click();expect(page.locator('#modal [name=reason]')).to_have_value('Motivo conservado entre filtros y tipos de movimiento');page.locator('#modal [name=move_account]').select_option(foreign['account_id']);page.locator('#move-manager-search').fill('Mariana');select=page.locator('#modal [name=target_manager_id]');expect(select.locator('option')).to_have_count(2);select.select_option(foreign['id']);expect(page.locator('#move-route-summary')).to_contain_text(foreign['account_code']);expect(page.locator('#move-route-summary')).to_contain_text(foreign['account_name'])
  # Changing filters must clear a now-hidden destination, without clearing the reason or stealing focus.
  page.locator('#modal [name=move_account]').select_option(same['account_id']);expect(select).to_have_value('');expect(page.locator('#move-manager-results')).to_contain_text('Sin coincidencias');assert not select.evaluate('(el)=>el.checkValidity()')
  page.locator('#move-manager-search').fill('MGR0003');assert page.locator('#move-manager-search').evaluate('(el)=>el===document.activeElement');expect(select.locator('option')).to_have_count(2);select.select_option(same['id']);page.locator('[data-action=move-mode][data-id=group]').click();expect(page.locator('#modal [name=reason]')).to_have_value('Motivo conservado entre filtros y tipos de movimiento');assert page.locator('#modal [name=target_manager_id]').is_disabled();assert not page.locator('#modal [name=group_id]').is_disabled()
  page.locator('[data-action=move-mode][data-id=external]').click();expect(select).to_have_value(same['id']);page.locator('#modal [name=move_account]').select_option(foreign['account_id']);page.locator('#move-manager-search').fill('MGR0002');select.select_option(foreign['id'])
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(220);box=page.locator('#modal').bounding_box();assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1
   page.screenshot(path='/tmp/pulse102-move-current.png',full_page=True)
   assert page.locator('#modal .form-body').evaluate('(el)=>el.scrollHeight<=el.clientHeight+1&&el.scrollWidth<=el.clientWidth+1'),(width,page.locator('#modal .form-body').evaluate('(el)=>[el.scrollHeight,el.clientHeight]'))
   expect(page.locator('#modal .dialog-footer')).to_be_visible()
   if width==1280:page.screenshot(path='/tmp/pulse102-move.png',full_page=True)
  page.set_viewport_size({'width':1280,'height':650});page.wait_for_timeout(180);save();expect(page.locator('#modal')).not_to_be_visible();state=context.request.get(base+'/api/state').json();request=state['manager_transfers'][0];assert request['target_manager_id']==foreign['id'];assert next(p for p in state['people'] if p['id']==tech['id'])['group_id']==tech['group_id']
  # A Manager in the other Account accepts into its own Group.
  assert context.request.post(base+'/api/login',data={'identity':'MGR0002','password':'manager22026'}).ok;page.goto(base);go('team');expect(page.locator('[data-action=manager-transfers]')).to_contain_text('Traslados de Técnicos');page.locator('[data-action=manager-transfers]').click();page.locator('[data-action=manager-transfer-accept]').click();state=context.request.get(base+'/api/state').json();page.locator('#modal [name=group_id]').select_option(state['groups'][0]['id']);fill('reason','Recibido en la Cuenta de destino');save();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('[data-team-person="'+tech['id']+'"]')).to_be_visible()
  assert not errors,errors
  print('PASS: one Move action, Account filter, Manager name/Employee ID search, stale selection cleared, reason and valid selection retained across modes, no focus loss, destination Account summary, modal bounds at 1440/1280/390, cross-Account request then receiving Manager acceptance, precise inbox label; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
