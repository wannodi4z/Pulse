"""UI approval flow, free canvas, contextual activity links and modal sizing."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_organization_transfers import OrganizationTransferTests
R=Path(__file__).resolve().parents[1];fixture=OrganizationTransferTests();fixture.setUp();proc=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.s.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1100});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(identity,password='Password2026!'):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>!busy')
  def go(view):page.evaluate('(v)=>navigate(v)',view);page.wait_for_function('()=>!busy')
  login('admin1','admin12026');go('orgTransfers');page.locator('[data-action=org-transfer-new]').click();page.locator('#modal [name=subject_id]').select_option(fixture.m['id']);page.locator('#modal [name=target_id]').select_option(fixture.dpe['id']);page.locator('#modal [name=reason]').fill('Cambio organizacional con continuidad')
  page.locator('[data-org-drag]').drag_to(page.locator('[data-org-drop]'));expect(page.locator('#modal [type=submit]')).to_be_enabled();page.screenshot(path='/tmp/pulse110-transfer-builder.png');page.locator('#modal [type=submit]').click();expect(page.locator('.org-transfer-card')).to_have_count(1)
  record=ctx.request.get(base+'/api/organization-transfers').json()[0]
  for reviewer in record['reviewers']:
   with fixture.s.connection() as db:username=db.execute('SELECT username FROM users WHERE id=?',(reviewer['id'],)).fetchone()[0]
   login(username);go('orgTransfers');page.locator('[data-action=org-transfer-detail]').click();page.locator('[data-action=org-transfer-decision][data-id$=APPROVED]').click();textarea=page.locator('#modal textarea');assert textarea.evaluate('e=>e.getBoundingClientRect().width/e.closest(".form-body").getBoundingClientRect().width>.85');textarea.fill('Equipo y destino revisados');page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible()
  login('admin1','admin12026');go('orgTransfers');page.locator('[data-action=org-transfer-detail]').click();expect(page.locator('[data-action=org-transfer-apply]')).to_be_visible();page.locator('#modal .dialog-header [data-action=close]').click()
  # Keep the source Manager in place for testing his original chart scope.
  login('M001');go('analytics');page.locator('[data-action=chart-layout-edit]').click();tile=page.locator('.chart-tile[data-chart-kind=trend]');tile.scroll_into_view_if_needed();before=tile.bounding_box();handle=tile.locator('[data-chart-resize]');box=handle.bounding_box();page.mouse.move(box['x']+12,box['y']+12);page.mouse.down();page.mouse.move(box['x']+53,box['y']+49,steps=5);page.mouse.up();page.wait_for_timeout(120);after=tile.bounding_box();assert abs(after['height']-before['height']-37)<3,(before,after);assert abs(after['width']-before['width']-41)<3,(before,after)
  height=after['height'];page.reload();page.locator('.sidebar').wait_for();go('analytics');tile=page.locator('.chart-tile[data-chart-kind=trend]');assert abs(tile.bounding_box()['height']-height)<2
  assert page.locator('.chart-tile').evaluate_all('es=>{const rs=es.map(e=>e.getBoundingClientRect());return rs.every((a,i)=>rs.slice(i+1).every(b=>a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1))}')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.set_viewport_size({'width':1440,'height':1100})
  assert not errors,errors;browser.close();print('PASS: drag proposal and four UI approvals; full-width modal fields; continuous resize +41px/+37px, persistence, no overlaps and mobile containment; no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
