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
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1440,'height':900},has_touch=True);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy')
  page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  for identity,view in [('M001','analytics'),('T001','myAnalytics')]:
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':'Password2026!'}).ok
   page.goto(base);page.locator('.sidebar [data-page='+view+']').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
   page.locator('[data-action=analytics-months]').first.click();page.locator('[data-action=comparison-toggle][data-id="2026-02"]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
   expect(page.locator('.decision-card')).to_have_count(8 if view=='analytics' else 5)
   expect(page.locator('#main table')).to_have_count(0)
   if view=='analytics':
    expect(page.locator('.bi-kpis .bi-kpi')).to_have_count(4)
    assert page.locator('.bi-kpi>strong').first.evaluate("e=>getComputedStyle(e).color==='rgb(40, 118, 200)'")
    assert page.evaluate("()=>{const r=structuredClone(analyticsReport);r.timeliness.average_delay_hours=48;r.comparison=[{month:'2026-01',minutes:{ot_minutes:240,PLANNED:60,GUARD:0,EMERGENCY:0}},{month:'2026-02',minutes:{ot_minutes:240,PLANNED:120,GUARD:0,EMERGENCY:0}}];const html=managerCommandDashboard(r);return html.includes('+25 pp')&&html.includes('48 h')}")
    page.locator('#main').evaluate('e=>e.scrollTop=0');page.screenshot(path='/tmp/pulse115-bi.png')
   for kind in (['trend','groups','mix','waterfall','heatmap','area','pareto','scatter'] if view=='analytics' else ['trend','mix','waterfall','area','heatmap']):
    for width,height in [(1440,780),(390,844)]:
     page.set_viewport_size({'width':width,'height':height})
     page.locator('[data-action=decision-detail][data-id='+kind+']').click();expect(page.locator('#modal.expanded-chart-dialog')).to_be_visible()
     assert page.locator('#modal').evaluate('el=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.bottom<=innerHeight+1}')
     expect(page.locator('#modal')).to_contain_text('enero de 2026')
     expect(page.locator('#modal')).to_contain_text('Lectura del periodo')
     assert page.locator('#modal tbody tr').count()>0
     if kind=='heatmap':
      assert page.locator('#modal [data-heat-value]').evaluate_all("xs=>new Set(xs.map(e=>getComputedStyle(e).backgroundColor)).size>1")
     point=page.locator('#modal [data-chart-tip]').last
     expect(point).to_have_count(1)
     point.hover();expect(page.locator('#pulse-chart-tooltip:popover-open')).to_be_visible()
     expect(page.locator('#pulse-chart-tooltip')).to_have_text(point.get_attribute('data-chart-tip'))
     assert page.locator('#pulse-chart-tooltip').evaluate('e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.top>=0&&r.bottom<=innerHeight+1}')
     if kind=='heatmap' and width==390:
      point.tap();expect(page.locator('#pulse-chart-tooltip:popover-open')).to_be_visible()
     point.focus();expect(page.locator('#pulse-chart-tooltip:popover-open')).to_be_visible()
     page.locator('#modal .dialog-footer [data-action=close]').focus()
     expect(page.locator('#pulse-chart-tooltip:popover-open')).to_have_count(0)
     if view=='myAnalytics':
      expect(page.locator('#modal')).not_to_contain_text('SECOND')
      expect(page.locator('#modal')).not_to_contain_text('INC-BETA')
     page.locator('#modal .dialog-footer [data-action=close]').click()
  page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-action=ot-new]').click();page.locator('#modal [name=scheduled_start]').fill('2026-01-01T10:00');page.locator('#modal [name=scheduled_end]').fill('2026-01-01T11:00')
  expect(page.locator('#ot-type-preview')).to_contain_text('Captura histórica excepcional')
  expect(page.locator('#modal [name=justification]')).to_have_attribute('placeholder','Explica la actividad, por qué se captura después y por qué no se utilizó el Timer.')
  page.locator('#modal .dialog-footer [data-action=close]').click()
  # A delegated Lead sees the same tools, using the existing team permission checks.
  lead,lc,_=fixture.f.person('USER','LEADTEST',group=fixture.g,lead=True)
  fixture.f.post('/api/delegations',{'lead_id':lead['id']},fixture.mc)
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'LEADTEST','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  page.locator('[data-action=decision-detail][data-id=groups]').click();expect(page.locator('#modal')).to_contain_text('Lectura del periodo');page.locator('#modal .dialog-footer [data-action=close]').click()
  assert not errors,errors
  b.close();print('PASS: eight team and five personal visual chart types with separate search for Manager and Technician, delegated Lead expansion, correct period, mobile modal containment and zero JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
