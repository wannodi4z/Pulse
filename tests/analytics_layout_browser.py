"""Personalized chart layout: pointer/keyboard sizing, local isolation, persistence and existing details."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_analytics_workspace
R=Path(__file__).resolve().parents[1];fixture=test_analytics_workspace.AnalyticsWorkspaceTests();fixture.setUp();proc=None
try:
 other_group=fixture.f.group(fixture.a,'LAYOUT-ISOLATION');other,_,_=fixture.f.person('MANAGER','M-LAYOUT',account=fixture.a,groups=[other_group])
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(identity):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':'Password2026!'}).ok
   page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy')
  def month_january():
   page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
   page.locator('[data-action=analytics-months]').first.click();page.locator('#modal [data-action=comparison-toggle][data-id="2026-02"]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  def tile(kind):return page.locator('.chart-tile[data-chart-kind='+kind+']')
  def edit():page.locator('[data-action=chart-layout-edit]').click()
  login('M001');month_january();expect(page.locator('.chart-tile')).to_have_count(9)
  expect(tile('trend').locator('h3')).to_have_text('Tendencia mensual')
  original=page.evaluate('JSON.stringify({summary:analyticsReport.summary,filters,comparisonMonths})')
  # A tall two-thirds chart and a short third leave room for another third below it.
  edit();page.locator('[data-chart-width=trend]').select_option('8');page.locator('[data-chart-height=trend]').select_option('600');page.locator('[data-chart-height=monthlybars]').select_option('300')
  page.wait_for_timeout(80)
  tall=tile('trend').bounding_box();short=tile('monthlybars').bounding_box();packed=tile('groups').bounding_box()
  assert abs(short['x']-packed['x'])<2 and abs(packed['y']-(short['y']+short['height']+12))<2,(tall,short,packed)
  assert packed['y']<tall['y']+tall['height']
  def no_overlaps():return page.locator('.chart-tile').evaluate_all("es=>{const boxes=es.map(e=>e.getBoundingClientRect());return boxes.every((a,i)=>boxes.slice(i+1).every(b=>a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1))}")
  assert no_overlaps()
  page.reload();page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');month_january();assert tile('groups').bounding_box()['y']<tile('trend').bounding_box()['y']+600
  edit();page.locator('[data-action=chart-layout-reset]').click();edit()

  edit()
  def order():return page.locator('.chart-tile').evaluate_all("es=>es.map(e=>e.dataset.chartKind)")
  before=order();source=tile('trend').locator('[data-chart-move]');target=tile('groups')
  source.scroll_into_view_if_needed();a=source.bounding_box();b=target.bounding_box();page.mouse.move(a['x']+12,a['y']+12);page.mouse.down();page.mouse.move(b['x']+b['width']/2,b['y']+100,steps=8);page.evaluate('()=>refresh(true)');assert page.evaluate('chartResizeActive()');page.mouse.up()
  assert order()[:3]==['monthlybars','groups','trend'],order()
  tile('trend').locator('[data-chart-move]').focus();page.keyboard.press('ArrowLeft');assert order()[:3]==['monthlybars','trend','groups']
  page.reload();page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');month_january();assert order()[:3]==['monthlybars','trend','groups']
  edit();source=tile('trend').locator('[data-chart-move]');source.scroll_into_view_if_needed();a=source.bounding_box();b=tile('groups').bounding_box();page.mouse.move(a['x']+12,a['y']+12);page.mouse.down();page.mouse.move(b['x']+20,b['y']+100);page.keyboard.press('Escape');page.mouse.up();assert order()[:3]==['monthlybars','trend','groups']
  page.locator('[data-action=chart-layout-reset]').click();assert order()==before
  page.locator('[data-action=chart-layout-hide][data-id=heatmap]').click();expect(page.locator('.chart-tile')).to_have_count(8)
  page.locator('[data-chart-width=trend]').select_option('8');page.locator('[data-chart-height=trend]').select_option('480')
  expect(tile('trend')).to_have_attribute('data-width','8');expect(tile('trend')).to_have_attribute('data-height','480')
  assert tile('trend').evaluate('e=>Math.abs(e.getBoundingClientRect().height-480)<2')
  page.locator('.personalized-charts').evaluate("e=>e.scrollIntoView({block:'start'})");page.screenshot(path='/tmp/pulse119-layout.png')
  edit();page.reload();page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');month_january()
  expect(page.locator('.chart-tile')).to_have_count(8);expect(tile('trend')).to_have_attribute('data-width','8');expect(tile('trend')).to_have_attribute('data-height','480')
  edit();tile('trend').evaluate("e=>e.scrollIntoView({block:'start'})")
  canvas_before=tile('trend').locator('svg.decision-svg').bounding_box()
  handle=tile('trend').locator('[data-chart-resize]');box=handle.bounding_box();page.mouse.move(box['x']+15,box['y']+12);page.mouse.down();page.mouse.move(box['x']+340,box['y']+110,steps=8);page.evaluate('()=>refresh(true)');assert page.evaluate('chartResizeActive()')
  page.wait_for_timeout(100);canvas_live=tile('trend').locator('svg.decision-svg').bounding_box();assert canvas_live['width']>canvas_before['width'] and canvas_live['height']>canvas_before['height']
  assert tile('trend').locator('svg.decision-svg').evaluate('e=>Math.abs(e.viewBox.baseVal.width-e.getBoundingClientRect().width)<2')
  assert tile('trend').locator('svg.decision-svg text').first.evaluate('e=>{const m=e.getScreenCTM();return Math.abs(m.a-m.d)<.01}')
  page.mouse.up()
  expect(tile('trend')).to_have_attribute('data-width','12');expect(tile('trend')).to_have_attribute('data-height','600')
  handle.focus();page.keyboard.press('ArrowLeft');page.keyboard.press('ArrowUp')
  expect(tile('trend')).to_have_attribute('data-width','8');expect(tile('trend')).to_have_attribute('data-height','480')
  tile('trend').evaluate("e=>e.scrollIntoView({block:'start'})");box=handle.bounding_box();page.mouse.move(box['x']+15,box['y']+12);page.mouse.down();page.mouse.move(box['x']-180,box['y']-100,steps=5);page.keyboard.press('Escape');page.mouse.up()
  expect(tile('trend')).to_have_attribute('data-width','8');expect(tile('trend')).to_have_attribute('data-height','480')
  for width,height in [(1440,1000),(1024,700),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   expect(tile('trend')).to_have_attribute('data-width','8');assert no_overlaps()
  tile('trend').locator('[data-chart-move]').focus();page.keyboard.press('ArrowRight');assert order()[1]=='trend'
  tile('trend').locator('[data-chart-move]').focus();page.keyboard.press('ArrowLeft');assert order()[0]=='trend'
  # Details and local legend remain available on a resized chart.
  tile('area').locator('[data-action=decision-detail]').click();page.locator('#modal [data-action=chart-series][data-id="area:HISTORICAL"]').click()
  expect(page.locator('#modal [data-area-series]')).to_have_count(1);expect(page.locator('#modal .chart-series-status')).to_contain_text('Mostrando sólo OT histórica')
  page.locator('#modal .dialog-footer [data-action=close]').click()
  page.set_viewport_size({'width':1440,'height':1000})
  for kind,selector in [('groups','.decision-group-bars'),('pareto','.decision-people-ranking'),('mix','svg.decision-svg')]:
   canvas=tile(kind).locator(selector);small=canvas.bounding_box()['height'];page.locator('[data-chart-height='+kind+']').select_option('600');page.wait_for_timeout(80);assert canvas.bounding_box()['height']>small
  page.locator('.chart-visibility-panel [data-id=heatmap]').click();cells=tile('heatmap').locator('.decision-heatmap>span');small=cells.first.bounding_box()['height'];page.locator('[data-chart-height=heatmap]').select_option('600');page.wait_for_timeout(80);assert cells.first.bounding_box()['height']>small
  assert page.evaluate('JSON.stringify({summary:analyticsReport.summary,filters,comparisonMonths})')==original
  for kind in page.evaluate('chartLayoutKinds'):
   choice=page.locator('.chart-visibility-panel [data-id='+kind+']')
   if choice.get_attribute('aria-pressed')=='true':choice.click()
  expect(page.locator('.chart-tile')).to_have_count(0);expect(page.locator('.chart-layout-empty')).to_contain_text('No hay gráficas visibles')
  page.locator('.chart-visibility-panel [data-id=trend]').click();expect(page.locator('.chart-tile')).to_have_count(1)
  login('M-LAYOUT');expect(page.locator('.chart-tile')).to_have_count(9);expect(tile('trend')).to_have_attribute('data-width','4')
  login('M001');expect(page.locator('.chart-tile')).to_have_count(1);expect(tile('trend')).to_have_attribute('data-width','8')
  page.locator('[data-action=chart-layout-reset]').click();expect(page.locator('.chart-tile')).to_have_count(9);expect(tile('trend')).to_have_attribute('data-width','4')
  # Malformed browser preferences safely fall back to defaults.
  page.evaluate("localStorage.setItem(chartLayoutKey(),'{bad json')");page.reload();page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');expect(page.locator('.chart-tile')).to_have_count(9)
  # Storage-denied contexts remain usable and retain session changes.
  edit();page.evaluate("()=>{window.savedStorageSet=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new Error('Storage disabled')}}")
  page.locator('[data-chart-width=trend]').select_option('12');expect(tile('trend')).to_have_attribute('data-width','12');expect(page.locator('#toast')).to_contain_text('este navegador no permite guardarlo')
  page.evaluate('()=>{Storage.prototype.setItem=window.savedStorageSet}');page.locator('[data-action=chart-layout-reset]').click()
  assert not errors,errors;browser.close();print('PASS: per-user layout persistence, pointer/keyboard resize and cancel, hide/show/all hidden/reset, responsive sizing, storage errors, modal expansion and interactive legend, unchanged analytics')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
