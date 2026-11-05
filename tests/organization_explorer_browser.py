"""Fifty DPE: bounded lists, deep search, actions and compact optional tree."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_api
R=Path(__file__).resolve().parents[1];f=test_api.PulseTests();f.setUp();proc=None
try:
 a,g,m,mc,u,tc=f.organization();lead,lc,_=f.person('USER','LEAD',group=g,lead=True)
 with f.server.connection(True) as c:
  dpe=dict(c.execute('SELECT * FROM users WHERE id=?',(m['parent_id'],)).fetchone());dp=dict(c.execute('SELECT * FROM users WHERE id=?',(dpe['parent_id'],)).fetchone())
  for i in range(49):
   c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,parent_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(f.server.uid(),'DPE','SCALE-DPE-'+str(i),'SCALE-DPE-'+str(i),'DPE de prueba',str(i).zfill(2),'',a,dp['id'],'PENDING_ACTIVATION',f.server.now()))
  for i in range(20):
   c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,parent_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(f.server.uid(),'MANAGER','SCALE-MGR-'+str(i),'SCALE-MGR-'+str(i),'Manager de prueba',str(i).zfill(2),'',a,dpe['id'],'PENDING_ACTIVATION',f.server.now()))
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
  page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>!busy');page.evaluate('(id)=>perform("organization-open",id)',a);expect(page.locator('.organization-explorer')).to_be_visible()
  expect(page.locator('.org-directory-person')).to_have_count(8);expect(page.locator('.org-directory-title>span')).to_have_text('50');assert page.locator('.hierarchy-dpe').count()==0
  page.locator('[data-action=org-explorer-page][data-id="directory:1"]').click();expect(page.locator('.org-directory-person')).to_have_count(8);expect(page.locator('.org-explorer-directory .org-explorer-pagination>span')).to_contain_text('9–16 de 50')
  search=page.locator('[data-org-explorer-search]');search.fill(dpe['employee_id']);expect(page.locator('.org-directory-person')).to_have_count(1);page.locator('.org-directory-person').click();expect(page.locator('.org-manager-row')).to_have_count(6);expect(page.locator('.org-explorer-detail>header p')).to_contain_text('21 Managers')
  page.locator('[data-action=org-explorer-page][data-id="managers:1"]').click();expect(page.locator('.org-manager-row')).to_have_count(6)
  search.fill('T001');expect(page.locator('.org-directory-person')).to_have_count(1);page.locator('.org-directory-person').click();expect(page.locator('#modal h2')).to_contain_text(m['last']);expect(page.locator('#modal [data-action=person-edit][data-id="'+lead['id']+'"]')).to_be_visible();page.locator('#modal .dialog-header [data-action=close]').click()
  # Tree starts compact, opens one branch, and pages DPE children instead of rendering fifty.
  page.locator('[data-action=org-explorer-mode][data-id=tree]').click();page.locator('[data-org-explorer-search]').fill('');expect(page.locator('.org-tree-row')).to_have_count(1)
  page.locator('[data-action=org-explorer-tree-toggle][data-id="'+dp['id']+'"]').click();expect(page.locator('.org-tree-row')).to_have_count(9);expect(page.locator('.org-tree-page>span')).to_have_text('1–8 de 50')
  page.locator('[data-action=org-explorer-tree-page][data-id="'+dp['id']+':1"]').click();expect(page.locator('.org-tree-page>span')).to_have_text('9–16 de 50')
  page.locator('[data-org-explorer-search]').fill('M001');page.locator('[data-action=org-explorer-tree-toggle][data-id="'+m['id']+'"]').click();expect(page.locator('.org-tree-content')).to_contain_text('Lead · LEAD');expect(page.locator('.org-tree-content')).to_contain_text('Grupo ·')
  page.locator('[data-action=org-explorer-tree-toggle][data-id="group-'+g+'"]').click();expect(page.locator('.org-tree-content')).to_contain_text('Técnico · T001')
  page.locator('[data-org-explorer-search]').fill('');page.screenshot(path='/tmp/pulse112-tree.png',full_page=True)
  page.locator('[data-action=org-explorer-mode][data-id=explorer]').click();page.screenshot(path='/tmp/pulse112-explorer.png',full_page=True)
  # Existing edit actions remain reachable without loading every Manager card.
  page.locator('[data-org-explorer-search]').fill('T001');page.locator('.org-directory-person').click();page.locator('#modal [data-action=person-edit][data-id="'+m['id']+'"]').click();expect(page.locator('#modal [name=employee_id]')).to_have_value('M001');page.locator('#modal .dialog-header [data-action=close]').click()
  for width in (1024,390):
   page.set_viewport_size({'width':width,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.locator('[data-action=org-explorer-mode][data-id=tree]').click();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.locator('[data-action=org-explorer-mode][data-id=explorer]').click()
  assert not errors,errors;browser.close();print('PASS: 50 DPE in pages of 8, 21 Managers in pages of 6; cross-level Employee ID search; optional tree with paged branches, Lead and Group/Technician nodes; existing edit actions; mobile; no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 f.tearDown()
