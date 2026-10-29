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
  page.goto(base);page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy');state=context.request.get(base+'/api/state').json();source=state['groups'][0]['id'];target=state['groups'][1]['id'];receiver=next(m for m in state['manager_directory'] if m['employee_id']=='MGR0003')
  page.locator('.heading-actions [data-action=manager-group-new]').click();fill('service_key','LABORATORIO-UI');fill('name','Grupo creado por el Manager');save();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('.team-kanban')).to_contain_text('Grupo creado por el Manager')
  page.locator('.heading-actions [data-action=tech-new]').click()
  for name,value in [('first','Técnico'),('last','Nuevo de interfaz'),('employee_id','UI-TECH'),('email','ui-tech@example.test')]:fill(name,value)
  page.locator('#modal [name=group_id]').select_option(source);save();expect(page.locator('.secret-code')).to_be_visible();oldcode=page.locator('.secret-code').inner_text();page.locator('#modal [data-action=close]').first.click();state=context.request.get(base+'/api/state').json();user=next(p for p in state['people'] if p['employee_id']=='UI-TECH');card=page.locator('[data-team-person="'+user['id']+'"]');expect(card).to_be_visible();card.locator('[data-action=team-details]').last.click();page.locator('#modal [data-action=activation-code]').click();expect(page.locator('[data-form=confirmation]')).to_be_visible();save();expect(page.locator('.secret-code')).to_be_visible();code=page.locator('.secret-code').inner_text();assert code!=oldcode;page.locator('#modal [data-action=close]').first.click()
  public=browser.new_context();assert public.request.post(base+'/api/activate',data={'identity':'UI-TECH','code':code,'password':'TechUI2026!'}).ok
  page.reload();page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy');card.locator('[data-action=team-details]').last.click();page.locator('#modal [data-action=person-edit]').click();fill('first','Técnico editado');save();expect(card).to_contain_text('Técnico editado')
  # Native drag moves only after explicit confirmation, directly by the owner.
  card.drag_to(page.locator('[data-team-destination="'+target+'"]'));expect(page.locator('#dialog-title')).to_have_text('Mover Técnico');expect(page.locator('#modal [name=group_id]')).to_have_value(target);page.locator('#modal [data-action=close]').first.click();assert next(p for p in context.request.get(base+'/api/state').json()['people'] if p['id']==user['id'])['group_id']==source
  card.locator('[data-action=team-details]').last.click();page.locator('#modal [data-action=team-move]').click();node=page.locator('#modal [name=group_id]');node.evaluate('(el)=>PulseLayout.reveal(el)');node.select_option(target);fill('transfer_reason','Cambio interno de cobertura');save();expect(page.locator('#modal')).not_to_be_visible();assert next(p for p in context.request.get(base+'/api/state').json()['people'] if p['id']==user['id'])['group_id']==target
  # Inter-Manager transfer stays pending until the receiving Manager chooses its Group.
  card.locator('[data-action=team-details]').last.click();page.locator('#modal [data-action=manager-transfer-new]').click();page.locator('#modal [name=target_manager_id]').select_option(receiver['id']);fill('reason','Nueva especialidad con el Manager receptor')
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(120);box=page.locator('#modal').bounding_box();assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1;assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight')
  page.set_viewport_size({'width':1280,'height':650});page.wait_for_timeout(100);save();state=context.request.get(base+'/api/state').json();assert state['manager_transfers'][0]['status']=='SUBMITTED';assert next(p for p in state['people'] if p['id']==user['id'])['group_id']==target
  assert context.request.post(base+'/api/login',data={'identity':'MGR0003','password':'manager32026'}).ok;page.goto(base);page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy');page.locator('[data-action=manager-transfers]').click();expect(page.locator('#modal')).to_contain_text('UI-TECH');page.locator('[data-action=manager-transfer-accept]').click();recipient=context.request.get(base+'/api/state').json();rg=recipient['groups'][0]['id'];page.locator('#modal [name=group_id]').select_option(rg);fill('reason','Aceptado para ampliar cobertura');save();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('[data-team-person="'+user['id']+'"]')).to_contain_text('Técnico editado');result=context.request.get(base+'/api/state').json();assert result['manager_transfers'][0]['status']=='APPROVED'
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight');assert page.locator('.team-kanban-workspace').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
  assert not errors,errors
  print('PASS: Manager creates Technician, regenerates activation and activates, edits identity, native drag cancel without writes, direct internal move, cross-Manager pending request and receiving Manager acceptance into own Group, responsive bounds at 1440/1280/390; zero JS errors')
  public.close();browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
