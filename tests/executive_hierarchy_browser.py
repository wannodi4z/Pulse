"""Real browser coverage of Admin hierarchy forms and read-only DP/DPE dashboards."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_executive_hierarchy import ExecutiveTests
R=Path(__file__).resolve().parents[1];fixture=ExecutiveTests();fixture.setUp();proc=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(identity,password='Password2026!'):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base);page.wait_for_function('()=>state&&!busy')
  login('admin1','admin12026');page.locator('.sidebar [data-page=organization]').click();expect(page.locator('.admin-account-grid')).to_be_visible();page.locator('[data-action=organization-open][data-id="'+fixture.a+'"]').click()
  expect(page.locator('.hierarchy-dp')).to_have_count(1);expect(page.locator('.hierarchy-dpe')).to_have_count(1)
  page.locator('[data-action=executive-new][data-id="DP:'+fixture.a+'"]').click()
  for name,value in [('first','Nueva'),('last','Dirección'),('employee_id','BROWSER-DP'),('email','dp@example.test')]:page.locator('#modal [name='+name+']').fill(value)
  expect(page.locator('#modal [name=account_id]')).to_have_value(fixture.a);page.locator('#modal [type=submit]').click();expect(page.locator('#modal .secret-code')).to_be_visible();page.locator('#modal [data-action=close]').first.click();expect(page.locator('.hierarchy-dp')).to_have_count(2)
  page.locator('[data-action=executive-new][data-id="DPE:'+fixture.dp['id']+'"]').click()
  for name,value in [('first','Nueva'),('last','Responsable'),('employee_id','BROWSER-DPE'),('email','new@example.test')]:page.locator('#modal [name='+name+']').fill(value)
  expect(page.locator('#modal [name=parent_id]')).to_have_value(fixture.dp['id']);page.locator('#modal [type=submit]').click();expect(page.locator('#modal .secret-code')).to_be_visible();page.locator('#modal [data-action=close]').first.click();expect(page.locator('.hierarchy-dpe')).to_have_count(2)
  page.locator('[data-action=hierarchy-manager]').first.click();expect(page.locator('#modal [name=parent_id]')).not_to_have_value('');page.locator('#modal [data-action=close]').first.click()
  page.screenshot(path='/tmp/pulse121-admin.png',full_page=True)
  for actor in [fixture.dp,fixture.dpe]:
   login(actor['username']);expect(page.locator('.sidebar [data-page=analytics]')).to_be_visible();expect(page.locator('.sidebar [data-page=teamTime]')).to_have_count(0);expect(page.locator('.sidebar [data-page=time]')).to_have_count(0)
   page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy');expect(page.locator('[data-action=executive-drill]')).to_have_count(1)
   if actor['role']=='DP':
    expect(page.locator('[name=filter-dpe]')).to_be_visible();page.locator('[data-action=executive-dpe][data-id="'+fixture.dpe['id']+'"]').click();expect(page.locator('[name=filter-dpe]')).to_have_value(fixture.dpe['id']);page.wait_for_function('()=>!busy')
   else:expect(page.locator('[name=filter-dpe]')).to_have_count(0)
   # Tree navigation is another search path; ordinary filters remain visible and synchronized.
   disclosure=page.locator('.executive-tree-disclosure')
   if disclosure.get_attribute('open') is None:disclosure.locator(':scope > summary').click()
   if actor['role']=='DP':
    dpe_node=page.locator('.executive-tree-node:has(> summary [data-action=executive-scope][data-id="dpe:'+fixture.dpe['id']+'"])')
    if dpe_node.get_attribute('open') is None:dpe_node.locator(':scope > summary').click()
   manager_node=page.locator('.executive-tree-node:has(> summary [data-action=executive-scope][data-id="manager:'+fixture.m['id']+'"])')
   if manager_node.get_attribute('open') is None:manager_node.locator(':scope > summary').click()
   group_node=page.locator('.executive-tree-node:has(> summary [data-action=executive-scope][data-id="group:'+fixture.g+'"])');group_node.locator(':scope > summary').click()
   page.locator('[data-action=executive-scope][data-id="person:'+fixture.u['id']+'"]').click();page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-person]')).to_have_value(fixture.u['id']);expect(page.locator('[name=filter-manager]')).to_have_value(fixture.m['id']);expect(page.locator('[name=filter-group]')).to_have_value(fixture.g)
   if actor['role']=='DP':page.screenshot(path='/tmp/pulse121-tree.png',full_page=True)
   page.locator('#executive-tree-search').fill('NO-SUCH-PERSON');expect(page.locator('#executive-tree-empty')).to_be_visible();page.locator('#executive-tree-search').fill('')
   page.locator('[data-action=executive-scope][data-id=all]').click();page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-person]')).to_have_value('')
   page.locator('[data-action=executive-drill]').click();expect(page.locator('[name=filter-manager]')).to_have_value(fixture.m['id']);page.wait_for_function('()=>!busy')
   page.locator('[data-action=decision-detail][data-id=mix]').click();expect(page.locator('#modal h2')).to_contain_text('Composición');page.locator('#modal [data-action=chart-series][data-id="mix:HISTORICAL"]').click();expect(page.locator('#modal .chart-series-status')).to_contain_text('Mostrando sólo');page.locator('#modal .dialog-footer [data-action=close]').click()
   page.locator('.sidebar [data-page=records]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy');page.locator('[data-action=record-detail]').first.click();expect(page.locator('#modal [data-action=approve]')).to_have_count(0);expect(page.locator('#modal [data-action=reject]')).to_have_count(0);page.locator('#modal .dialog-footer [data-action=close]').click()
   page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.screenshot(path='/tmp/pulse121-'+actor['role'].lower()+'.png',full_page=True)
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.set_viewport_size({'width':1440,'height':1000})
  assert not errors,errors;browser.close();print('PASS: Admin nested creation, DP/DPE scope filters, drill-down, chart legends, record details read-only, mobile containment and no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
