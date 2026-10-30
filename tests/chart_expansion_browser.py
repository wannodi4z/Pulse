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
  for identity,view in [('M001','analytics'),('T001','myAnalytics')]:
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':'Password2026!'}).ok
   page.goto(base);page.locator('.sidebar [data-page='+view+']').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
   page.locator('[data-action=analytics-months]').first.click();page.locator('[data-action=comparison-toggle][data-id="2026-02"]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
   expect(page.locator('.decision-card')).to_have_count(4)
   for kind in ['trend','groups','mix','waterfall']:
    for width,height in [(1440,780),(390,844)]:
     page.set_viewport_size({'width':width,'height':height})
     page.locator('[data-action=decision-detail][data-id='+kind+']').click();expect(page.locator('#modal.expanded-chart-dialog')).to_be_visible()
     assert page.locator('#modal').evaluate('el=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.bottom<=innerHeight+1}')
     expect(page.locator('#modal')).to_contain_text('enero de 2026')
     expect(page.locator('#modal')).to_contain_text('Lectura del periodo')
     assert page.locator('#modal tbody tr').count()>0
     page.locator('#modal .dialog-footer [data-action=close]').click()
  # A delegated Lead sees the same tools, using the existing team permission checks.
  lead,lc,_=fixture.f.person('USER','LEADTEST',group=fixture.g,lead=True)
  fixture.f.post('/api/delegations',{'lead_id':lead['id']},fixture.mc)
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'LEADTEST','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  page.locator('[data-action=decision-detail][data-id=groups]').click();expect(page.locator('#modal')).to_contain_text('Lectura del periodo');page.locator('#modal .dialog-footer [data-action=close]').click()
  assert not errors,errors
  b.close();print('PASS: four visual chart types and data tables for Manager and Technician, delegated Lead expansion, correct period, mobile modal containment and zero JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
