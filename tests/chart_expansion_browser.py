"""v1.0.7 interactive dashboard and bulk weekly rule editor."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_analytics_workspace
root=Path(__file__).resolve().parents[1];fixture=test_analytics_workspace.AnalyticsWorkspaceTests();fixture.setUp();proc=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=root,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy')
  page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  page.locator('[data-action=analytics-months]').click();page.locator('[name=compare_month]').fill('2026-02');page.locator('[data-action=comparison-add]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  assert page.locator('.chart-card').evaluate_all('xs=>Math.abs(xs[0].getBoundingClientRect().height-xs[1].getBoundingClientRect().height)<2')
  for identity,view in [('M001','analytics'),('T001','myAnalytics')]:
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':'Password2026!'}).ok
   page.goto(base);page.locator('.sidebar [data-page='+view+']').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
   for kind in ['distribution','comparison','hourly','daily']:
    for width,height in [(1440,780),(390,844)]:
     page.set_viewport_size({'width':width,'height':height})
     if kind=='daily':page.locator('.analytics-days summary').click()
     page.locator('[data-action=chart-expand][data-id='+kind+']').click();expect(page.locator('#modal.expanded-chart-dialog')).to_be_visible()
     assert page.locator('#modal').evaluate('el=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.bottom<=innerHeight+1}')
     expect(page.locator('#modal')).to_contain_text('enero de 2026')
     if kind=='hourly':expect(page.locator('#modal .hourly-slot')).to_have_count(24)
     if width==1440 and kind=='hourly':
      assert page.locator('#modal').evaluate('el=>el.getBoundingClientRect().width>1000')
      assert page.locator('#modal .hourly-grid').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
      page.wait_for_timeout(250);page.screenshot(path='/tmp/pulse-expanded-hours.png')
     page.locator('#modal .dialog-footer [data-action=close]').click()
     if kind=='daily':page.locator('.analytics-days summary').click()
  # A delegated Lead sees the same tools, using the existing team permission checks.
  lead,lc,_=fixture.f.person('USER','LEADTEST',group=fixture.g,lead=True)
  fixture.f.post('/api/delegations',{'lead_id':lead['id']},fixture.mc)
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'LEADTEST','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  page.locator('[data-action=chart-expand][data-id=distribution]').click();expect(page.locator('#modal')).to_contain_text('Alcance del equipo autorizado');page.locator('#modal .dialog-footer [data-action=close]').click()
  assert not errors,errors
  b.close();print('PASS: equal chart cards; four expandable charts for Manager and Technician, delegated Lead expansion, correct period, mobile modal containment and zero JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
