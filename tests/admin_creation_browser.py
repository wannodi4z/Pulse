"""Discoverable Admin actions: two Managers per Account, unrestricted additional Managers and direct Lead creation."""
import os,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
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
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1280,'height':650});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
  state=context.request.get(base+'/api/state').json();accounts=state['accounts'];a=next(a for a in accounts if a['base_code']=='BNTE')
  for account in accounts:
   managers=[u for u in state['people'] if u['role']=='MANAGER' and u['account_id']==account['id']];assert len(managers)==2
   for m in managers:assert len([u for u in state['people'] if u['is_lead'] and u['manager_id']==m['id'] and u['group_id'] is None])==1
  page.goto(base);page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy')
  block=page.locator('[data-account="'+a['id']+'"]');block.evaluate('(el)=>PulseLayout.reveal(el)')
  expect(block.locator('.account-main-actions [data-action=manager-new]')).to_be_visible()
  for width,height in [(1440,780),(1366,700),(1280,650)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
   issues=block.evaluate('''el=>{const b=document.querySelector('.viewport-stage').getBoundingClientRect();const buttons=[...el.querySelectorAll('button,select')].filter(n=>n.getClientRects().length);return buttons.map(n=>{const r=n.getBoundingClientRect();return {text:n.textContent.slice(0,30),bottom:r.bottom-b.bottom,right:r.right-b.right,left:r.left-b.left}}).filter(r=>r.bottom>2||r.right>1||r.left< -1)}''');assert not issues,(width,issues)
   lead=block.locator('.direct-lead-person:visible .backup-identity strong');assert lead.evaluate('(el)=>getComputedStyle(el).whiteSpace!=="nowrap"&&el.scrollHeight<=el.clientHeight+1')
   buttons=block.locator('.manager-main-actions:visible button').all()
   boxes=[b.bounding_box() for b in buttons]
   assert all(b['height']>=30 for b in boxes)
   assert all(boxes[i]['x']+boxes[i]['width']<=boxes[i+1]['x']+1 for i in range(len(boxes)-1))
  def fill(name,value):
   node=page.locator('#modal [name='+name+']');node.evaluate('(el)=>PulseLayout.reveal(el)');node.fill(value)
  def save():
   for _ in range(20):
    nxt=page.locator('[data-step-next]:visible:not(:disabled)')
    if not nxt.count():break
    nxt.click()
   page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  block.locator('.account-main-actions [data-action=manager-new]').click()
  for name,value in [('first','Manager'),('last','Adicional de Banorte'),('employee_id','EXTRA-MGR'),('email','extra-mgr@example.test')]:fill(name,value)
  expect(page.locator('#modal [name=account_id]')).to_have_value(a['id']);save();expect(page.locator('.secret-code')).to_be_visible();code=page.locator('.secret-code').inner_text()
  assert context.request.post(base+'/api/activate',data={'identity':'EXTRA-MGR','code':code,'password':'ExtraManager2026!'}).ok
  page.locator('#modal [data-action=close]').first.click();state=context.request.get(base+'/api/state').json();extra=next(u for u in state['people'] if u['employee_id']=='EXTRA-MGR')
  expect(block.locator('[data-manager-jump]')).to_have_value(extra['id'])
  manager=block.locator('[data-manager="'+extra['id']+'"]');expect(manager.locator('[data-action=lead-new]')).to_be_visible();manager.locator('[data-action=lead-new]').click()
  expect(page.locator('#modal [name=manager_id]')).to_have_value(extra['id']);expect(page.locator('#modal [name=is_lead]')).to_be_checked()
  expect(page.locator('#modal [name=group_id]')).not_to_be_visible()
  for name,value in [('first','Lead'),('last','Del Manager Adicional'),('employee_id','EXTRA-LEAD'),('email','extra-lead@example.test')]:fill(name,value)
  save();expect(page.locator('.secret-code')).to_be_visible();code=page.locator('.secret-code').inner_text()
  assert context.request.post(base+'/api/activate',data={'identity':'EXTRA-LEAD','code':code,'password':'ExtraLead2026!'}).ok
  page.locator('#modal [data-action=close]').first.click()
  expect(manager.locator('[data-action=lead-new]')).to_have_count(0);expect(manager.locator('.direct-lead-person')).to_contain_text('EXTRA-LEAD');expect(manager.locator('button').filter(has_text='Editar Lead')).to_be_visible()
  manager.locator('[data-action=manager-group-new]').click();expect(page.locator('#modal [name=manager_id]')).to_have_value(extra['id']);expect(page.locator('#modal [name=account_id]')).to_have_value(a['id'])
  fill('service_key','Laboratorio');fill('name','Laboratorio del Manager adicional');save();expect(page.locator('#modal')).not_to_be_visible()
  state=context.request.get(base+'/api/state').json();assert len([u for u in state['people'] if u['role']=='MANAGER' and u['account_id']==a['id']])==3
  lead=next(u for u in state['people'] if u['employee_id']=='EXTRA-LEAD');assert lead['manager_id']==extra['id'] and lead['group_id'] is None
  assert any(g['name']=='Laboratorio del Manager adicional' and g['manager_id']==extra['id'] for g in state['groups'])
  assert not errors,errors
  print('PASS: two Managers per Account and four direct Leads; visible aligned Account/Manager/Lead actions and full Lead names at 1440/1366/1280; Manager selector; third Manager created without cap; new Manager focused automatically; direct Add Lead with correct parent; Edit Lead after assignment; contextual Add Group saves correct owner; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
