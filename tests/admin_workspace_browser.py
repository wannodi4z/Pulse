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
  expect(page.locator('.sidebar .nav-item')).to_have_count(4)
  expect(page.locator('.sidebar .nav-settings')).to_have_count(0)
  expect(page.locator('.admin-dashboard .kpi')).to_have_count(4)
  assert page.locator('.admin-dashboard .kpi strong').all_text_contents()==['2','4','4','0']
  expect(page.locator('.admin-bar-row')).to_have_count(2)
  assert page.locator('meter').evaluate_all('(els)=>els.every(el=>el.value===2&&el.max===2)')
  page.locator('#admin-search').fill('Banorte');expect(page.locator('.admin-bar-row')).to_have_count(1);expect(page.locator('#admin-distribution tbody tr')).to_have_count(1)
  assert page.locator('#admin-search').evaluate('(el)=>el===document.activeElement')
  page.locator('#admin-search').fill('');page.locator('#admin-country').select_option('MX');expect(page.locator('.admin-bar-row')).to_have_count(2)
  for width,height in [(1440,780),(1366,700),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight'),width
   assert page.locator('.admin-dashboard').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),width
   if width>=1280:
    page.screenshot(path=f'/tmp/pulse120-dashboard-{width}.png',full_page=True)
    assert page.locator('.admin-dashboard').evaluate('(el)=>el.scrollHeight<=el.clientHeight+1'), (width,page.locator('.admin-dashboard').evaluate('(el)=>[el.scrollHeight,el.clientHeight]'))
  page.set_viewport_size({'width':1440,'height':780});go('organization');expect(page.locator('.admin-account-tile')).to_have_count(2)
  page.locator('[data-action=organization-open][data-id="'+aid+'"]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('.admin-manager-card')).to_have_count(2);expect(page.locator('.admin-lead-slot')).to_have_count(2);expect(page.locator('.group-card,.technician')).to_have_count(0)
  assert page.locator('.admin-manager-card').all_text_contents()[0].find('SL0001')>=0
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight'),width
   assert page.locator('.admin-account-detail').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),width
  page.set_viewport_size({'width':1440,'height':780})
  # Identity edits must preserve the Manager's groups, absent from the new form.
  manager=next(u for u in state['people'] if u['employee_id']=='MGR0001');before=[g['id'] for g in state['groups'] if g['manager_id']==manager['id']]
  page.locator('[data-manager="'+manager['id']+'"] [data-action=person-edit]').first.click();expect(page.locator('#modal [name=group_ids]')).to_have_count(0);fill('first','Yao');save();expect(page.locator('#modal')).not_to_be_visible()
  after=context.request.get(base+'/api/state').json();assert before==[g['id'] for g in after['groups'] if g['manager_id']==manager['id']]
  # Create unrestricted additional Manager and direct Lead through real forms.
  page.locator('.heading-actions [data-action=manager-new]').click()
  for name,value in [('first','Nuevo'),('last','Manager'),('employee_id','MGR-UI'),('email','mgr-ui@example.test')]:fill(name,value)
  save();expect(page.locator('.secret-code')).to_be_visible();code=page.locator('.secret-code').inner_text();assert context.request.post(base+'/api/activate',data={'identity':'MGR-UI','code':code,'password':'ManagerUI2026!'}).ok;page.locator('#modal [data-action=close]').first.click()
  state=context.request.get(base+'/api/state').json();mid=next(u['id'] for u in state['people'] if u['employee_id']=='MGR-UI');card=page.locator('[data-manager="'+mid+'"]');expect(card).to_contain_text('Sin Grupos asignados');card.locator('[data-action=lead-new]').click()
  expect(page.locator('#modal [name=manager_id]')).to_have_value(mid)
  for name,value in [('first','Nueva'),('last','Lead'),('employee_id','LEAD-UI'),('email','lead-ui@example.test')]:fill(name,value)
  save();expect(page.locator('.secret-code')).to_be_visible();code=page.locator('.secret-code').inner_text();assert context.request.post(base+'/api/activate',data={'identity':'LEAD-UI','code':code,'password':'LeadUI2026!'}).ok;page.locator('#modal [data-action=close]').first.click();expect(card).to_contain_text('LEAD-UI');expect(card.locator('[data-action=lead-new]')).to_have_count(0)
  # Lead recovery arrives only to Admin. Verify code issue/view/regenerate in UI.
  assert context.request.post(base+'/api/recoveries',data={'identity':'LEAD-UI'}).ok;go('recoveries');expect(page.locator('tbody')).to_contain_text('LEAD-UI');page.locator('[data-action=recovery-issue]').click();expect(page.locator('.secret-code')).to_be_visible();first=page.locator('.secret-code').inner_text();page.locator('#modal [data-action=close]').first.click();page.locator('[data-action=recovery-view]').click();expect(page.locator('.secret-code')).to_have_text(first);page.locator('#modal [data-action=close]').first.click();page.locator('[data-action=recovery-issue]').click();assert page.locator('.secret-code').inner_text()!=first;page.locator('#modal [data-action=close]').first.click()
  # CRUD empty Account, create and edit another Administrator.
  go('organization');page.locator('[data-action=account-new]').click();fill('code','UITEST');fill('name','Cuenta de interfaz');save();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('.admin-account-tile')).to_have_count(3)
  go('admins');page.locator('[data-action=admin-new]').click()
  for name,value in [('first','Admin'),('last','Interfaz'),('username','admin-ui'),('email','admin-ui@example.test')]:fill(name,value)
  save();expect(page.locator('.secret-code')).to_be_visible();page.locator('#modal [data-action=close]').first.click();expect(page.locator('#main')).to_contain_text('admin-ui')
  page.screenshot(path='/tmp/pulse120-admins.png',full_page=True)
  go('dashboard');page.screenshot(path='/tmp/pulse120-dashboard.png',full_page=True)
  go('organization');page.locator('[data-action=organization-open][data-id="'+aid+'"]').click();page.wait_for_function('()=>!busy');page.screenshot(path='/tmp/pulse120-account.png',full_page=True)
  assert not errors,errors
  print('PASS: Admin navigation, metrics, country/search, charts/table, responsive bounds at 4 viewports, two Managers with direct Leads per Account, group preservation on Manager edit, third Manager plus Lead created, empty groups message, recovery issue/view/regenerate, Account and Admin creation; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
