"""Cross-role interface alignment, saved dashboard views, compact sidebar and Admin settings."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_analytics_workspace
R=Path(__file__).resolve().parents[1];fixture=test_analytics_workspace.AnalyticsWorkspaceTests();fixture.setUp();proc=None
try:
 empty_manager,_,_=fixture.f.person('MANAGER','EMPTY-UI',account=fixture.a)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(identity,password='Password2026!'):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>state&&!busy')
  def go(view):
   page.locator('.sidebar [data-page='+view+']').click();expect(page.locator('.sidebar [data-page='+view+']')).to_have_attribute('aria-current','page');page.wait_for_function('()=>!busy')
  def left_actions():assert page.locator('.page-heading').evaluate("e=>{const title=e.querySelector('h1').getBoundingClientRect(),actions=e.querySelector('.heading-actions').getBoundingClientRect();return !e.querySelector('.heading-actions').children.length||Math.abs(title.left-actions.left)<2}")
  def centered_empty(selector):assert page.locator(selector).evaluate("e=>{const b=e.getBoundingClientRect(),icon=e.querySelector('.empty-icon').getBoundingClientRect(),parent=e.parentElement.getBoundingClientRect();return Math.abs((icon.x+icon.width/2)-(b.x+b.width/2))<2&&Math.abs((b.x+b.width/2)-(parent.x+parent.width/2))<2}")
  login('admin1','admin12026');go('organization');page.locator('#admin-search').fill('NO-MATCH');centered_empty('.admin-account-grid>.empty');left_actions();page.screenshot(path='/tmp/pulse122-empty.png')
  expect(page.locator('.sidebar .nav-group')).to_have_count(4);page.locator('[data-action=sidebar-toggle]').click();expect(page.locator('.shell')).to_have_class('shell is-sidebar-collapsed');assert page.locator('.sidebar').bounding_box()['width']==76
  page.reload();page.locator('.sidebar').wait_for();expect(page.locator('.shell')).to_have_class('shell is-sidebar-collapsed');go('settings');left_actions();page.locator('[data-action=sidebar-toggle]').click()
  for name,value in [('host','smtp.example.test'),('username','pulse-service'),('from_address','pulse@example.test'),('password','saved-smtp-secret')]:page.locator('[data-form=smtp-settings] [name='+name+']').fill(value)
  page.locator('[data-form=smtp-settings] [type=submit]').click();expect(page.locator('.settings-secret-note')).to_be_visible();expect(page.locator('[data-form=smtp-settings] [name=password]')).to_have_value('');expect(page.locator('#toast')).to_contain_text('No se enviaron mensajes')
  page.locator('[data-action=organization-backup]').click();page.locator('#modal [name=password]').fill('Demo-backup-password-2026!');page.locator('#modal [name=confirm]').fill('Demo-backup-password-2026!')
  with page.expect_download() as download:page.locator('#modal [type=submit]').click()
  file=download.value;assert file.suggested_filename.endswith('.pulseorg');assert Path(file.path()).stat().st_size>1000
  expect(page.locator('#modal')).not_to_be_visible();page.screenshot(path='/tmp/pulse122-settings.png')
  page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');expect(page.locator('[data-action=sidebar-toggle]')).not_to_be_visible();page.set_viewport_size({'width':1440,'height':1000})
  login('EMPTY-UI');go('team');centered_empty('.team-kanban>.empty');left_actions();expect(page.locator('.team-board-hint')).not_to_be_visible()
  for identity,view,count in [('M001','analytics',9),('T001','myAnalytics',6)]:
   login(identity);go(view);page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy');expect(page.locator('.chart-tile')).to_have_count(count)
   original=page.evaluate('JSON.stringify({summary:analyticsReport.summary,filters,comparisonMonths})');page.locator('[data-action=chart-layout-edit]').click()
   page.locator('[data-chart-width=trend]').select_option('8');page.locator('[data-action=chart-layout-save-profile]').click();page.locator('#modal [name=name]').fill('Mi revisión mensual');page.locator('#modal [type=submit]').click();expect(page.locator('.chart-saved-view')).to_have_count(1)
   page.locator('[data-action=chart-layout-preset][data-id=comparison]').click();expect(page.locator('.chart-tile')).to_have_count(4);page.locator('[data-action=chart-layout-load-profile]').click();expect(page.locator('.chart-tile')).to_have_count(count);expect(page.locator('[data-chart-kind=trend]')).to_have_attribute('data-width','8')
   assert page.evaluate('JSON.stringify({summary:analyticsReport.summary,filters,comparisonMonths})')==original
   page.reload();page.locator('.sidebar').wait_for();go(view);page.wait_for_function('()=>analyticsReport!==null');page.locator('[data-action=chart-layout-edit]').click();expect(page.locator('.chart-saved-view')).to_have_count(1)
   page.locator('[data-action=chart-layout-save-profile]').click();page.locator('#modal [name=name]').fill('Mi revisión mensual');page.locator('#modal [type=submit]').click();expect(page.locator('#modal .form-error')).to_contain_text('Ya existe');page.locator('#modal .dialog-header [data-action=close]').click()
   page.locator('.personalized-charts').scroll_into_view_if_needed();page.screenshot(path='/tmp/pulse122-'+view+'-views.png');page.locator('[data-action=chart-layout-delete-profile]').click();expect(page.locator('.chart-saved-view')).to_have_count(0)
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.set_viewport_size({'width':1440,'height':1000})
  assert not errors,errors;browser.close();print('PASS: centered empty states and left actions; grouped/collapsible persistent navigation; SMTP masked secrets and backup download; Manager and Technician preset/saved view persistence and duplicate validation; unchanged metrics; mobile and zero JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
