"""Quiet dashboard, scoped catalog, structured resize, filter drafts and search-only history."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_analytics_workspace import AnalyticsWorkspaceTests
R=Path(__file__).resolve().parents[1];fixture=AnalyticsWorkspaceTests();fixture.setUp();proc=None
try:
 with fixture.f.server.connection() as c:
  dpe=dict(c.execute('SELECT * FROM users WHERE id=?',(fixture.m['parent_id'],)).fetchone());dp=dict(c.execute('SELECT * FROM users WHERE id=?',(dpe['parent_id'],)).fetchone())
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(identity):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':'Password2026!'}).ok;page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>!busy')
  def go(view):page.evaluate('(v)=>navigate(v)',view);page.wait_for_function('()=>!busy')
  def january():page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  def close():page.locator('#modal .dialog-header [data-action=close]').click()
  def no_overlap():return page.locator('.chart-tile').evaluate_all('es=>{const rs=es.map(e=>e.getBoundingClientRect());return rs.every((a,i)=>rs.slice(i+1).every(b=>a.right<=b.left+1||b.right<=a.left+1||a.bottom<=b.top+1||b.bottom<=a.top+1))}')
  login('M001');go('analytics');january();expect(page.locator('.chart-tile')).to_have_count(4);assert page.locator('#main [name^=filter-]').count()==0
  assert page.locator('.sidebar [data-page=orgTransfers]').evaluate("e=>e.closest('.nav-group').getAttribute('aria-label')")=='Administración'
  # Filters are a draft: cancel has no effect; apply changes all plots, and clears dependent fields.
  original=page.evaluate('JSON.stringify(filters)');page.locator('[data-action=analytics-filters]').click();page.locator('#modal [name=person]').select_option(fixture.u['id']);close();assert page.evaluate('JSON.stringify(filters)')==original
  page.locator('[data-action=analytics-filters]').click();page.locator('#modal [name=person]').select_option(fixture.u['id']);page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');assert page.evaluate('filters.person')==fixture.u['id'];assert page.evaluate('analyticsReport.users.length')==1
  page.locator('[data-action=analytics-filters]').click();page.locator('[data-action=analytics-filter-clear]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-action=analytics-months]').click();page.locator('[data-action=comparison-toggle][data-id="2026-02"]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-action=chart-catalog]').click();expect(page.locator('#modal [name=chart]')).to_have_count(18);assert page.locator('#modal [value=accounts]').count()==0
  page.locator('#modal [data-catalog-search]').fill('técnico');assert page.locator('.catalog-choice:visible').count()>=3;page.locator('#modal [data-catalog-search]').fill('')
  for k in page.locator('#modal [name=chart]').all():k.check()
  page.locator('#modal [type=submit]').click();expect(page.locator('.chart-tile')).to_have_count(18)
  # Every catalog entry has a real plot, summary and table; no fallback to an unrelated chart.
  for kind in page.evaluate('availableChartKinds()'):
   page.evaluate('(k)=>decisionDetailModal(k)',kind);expect(page.locator('#modal h2')).not_to_have_text('undefined');assert page.locator('#modal tbody tr').count()>0,kind
   if page.locator('#modal [data-action=chart-series]').count()>1:
    page.locator('#modal [data-action=chart-series]').nth(1).click();expect(page.locator('#modal .chart-series-status')).to_contain_text('Mostrando sólo')
   close()
  # Select a quiet view and resize only along the prescribed grid sizes.
  page.locator('[data-action=chart-catalog]').click()
  for k in page.locator('#modal [name=chart]').all():k.set_checked(k.get_attribute('value') in ['trend','monthlybars','groups','mix'])
  page.locator('#modal [type=submit]').click();page.locator('[data-action=chart-layout-edit]').click();page.locator('[data-chart-width=trend]').select_option('8');page.locator('[data-chart-height=trend]').select_option('600');page.wait_for_timeout(120)
  assert no_overlap();tile=page.locator('[data-chart-kind=trend]');tile.scroll_into_view_if_needed();handle=tile.locator('[data-chart-resize]');b=handle.bounding_box();page.mouse.move(b['x']+12,b['y']+12);page.mouse.down();page.mouse.move(b['x']-250,b['y']-120,steps=5);page.mouse.up();assert tile.get_attribute('data-width') in ['4','6','8','12'];assert tile.get_attribute('data-height') in ['300','380','480','600'];assert no_overlap()
  assert tile.locator('svg.decision-svg').evaluate('e=>Math.abs(e.viewBox.baseVal.width-e.getBoundingClientRect().width)<2')
  # Movement and named views remain independent from data filters.
  before_order=page.locator('.chart-tile').evaluate_all('es=>es.map(e=>e.dataset.chartKind)');tile.locator('[data-chart-move]').focus();page.keyboard.press('ArrowRight');assert page.locator('.chart-tile').evaluate_all('es=>es.map(e=>e.dataset.chartKind)')!=before_order
  page.locator('[data-action=chart-layout-save-profile]').click();page.locator('#modal [name=name]').fill('Revisión de prueba');page.locator('#modal [type=submit]').click()
  expect(page.locator('.chart-saved-view')).to_have_count(1)
  saved=page.evaluate('Object.fromEntries(Object.entries(readChartLayout()).map(([k,v])=>[k,[v.visible,v.width,v.height,v.order]]))');page.reload();page.locator('.sidebar').wait_for();go('analytics');january();assert page.evaluate('Object.fromEntries(Object.entries(readChartLayout()).map(([k,v])=>[k,[v.visible,v.width,v.height,v.order]]))')==saved;expect(page.locator('.chart-tile')).to_have_count(4)
  page.screenshot(path='/tmp/pulse111-dashboard.png',full_page=True)
  # History remains a search; no compare controls, same filter modal and month/all-history options.
  go('records');january();expect(page.locator('#analytics-search')).to_be_visible();assert page.locator('[data-action=analytics-months]').count()==0
  page.locator('[data-action=analytics-filters]').click();page.locator('#modal [name=period]').select_option('ALL');page.locator('#modal [name=status]').select_option('SUBMITTED');page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');assert page.evaluate('filters.period')=='ALL';assert page.evaluate('analyticsReport.record_count')==1;assert page.evaluate('comparisonMonths.length')==0
  # Role-aware catalog: all twenty for DP, only personal analyses for Technician.
  login(dp['username']);go('analytics');january();page.locator('[data-action=chart-catalog]').click();expect(page.locator('#modal [name=chart]')).to_have_count(20);page.locator('#modal [value=accounts]').check();page.locator('#modal [value=managers]').check();page.locator('#modal [type=submit]').click()
  for kind in ['accounts','managers']:
   page.evaluate('(k)=>decisionDetailModal(k)',kind);assert page.locator('#modal tbody tr').count()>0;close()
  page.locator('[data-action=analytics-tree]').click();expect(page.locator('.executive-scope-tree')).to_be_visible();close()
  login('T001');go('myAnalytics');january();expect(page.locator('.chart-tile')).to_have_count(4);page.locator('[data-action=chart-catalog]').click();expect(page.locator('#modal [name=chart]')).to_have_count(11);assert page.locator('#modal [value=groups]').count()==0;close()
  for width in [1024,390]:
   page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert no_overlap()
  assert not errors,errors;browser.close();print('PASS: 4 defaults; scoped catalog 20/18/11; every chart summary/table/series; filter draft/cancel/apply; structured resize and persistence; search-only history; executive tree; Administration navigation; mobile containment; no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
