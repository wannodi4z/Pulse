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
  expect(page.locator('.hourly-slot')).to_have_count(24);expect(page.locator('.metric-all strong')).to_have_text('12 h')
  page.locator('[data-action=analytics-months]').click();page.locator('[name=compare_month]').fill('2026-02');page.locator('[data-action=comparison-add]').click();page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('.metric-all strong')).to_have_text('15 h')
  expect(page.locator('.analytics-dashboard')).to_contain_text('Comparativa por mes')
  page.screenshot(path='/tmp/pulse107-dashboard.png',full_page=True)
  page.locator('[data-action=analytics-group][data-id="'+fixture.g+'"]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('#analytics-users tbody tr')).to_have_count(1)
  page.locator('[data-action=analytics-user]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-person]')).not_to_have_value('')
  page.locator('#analytics-search').fill('CHG-ALPHA');expect(page.locator('#analytics-records tbody tr')).to_have_count(2);expect(page.locator('.metric-all strong')).to_have_text('5 h')
  for width,height in [(1024,600),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(200)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), 'horizontal page overflow'
  page.set_viewport_size({'width':1440,'height':900});page.evaluate("navigate('timeRules')");page.wait_for_function('()=>!busy');page.locator('[data-action=rule-new]').click()
  page.locator('[name=name]').fill('Semana visual');page.locator('[name=effective_from]').fill('2026-01-01')
  monday=page.locator('[data-rule-day="0"]');monday.locator('[name=days]').check();monday.locator('[data-start]').fill('02:00');monday.locator('[data-end]').fill('04:00');monday.locator('[data-action=rule-add]').click();monday.locator('[data-start]').last.fill('20:00');monday.locator('[data-end]').last.fill('00:00')
  page.locator('[data-action=rule-copy]').click();expect(page.locator('.rule-week-total')).to_contain_text('30 h')
  page.locator('[data-action=rule-day-open][data-id="5"]').click();sat=page.locator('[data-rule-day="5"]');sat.locator('[name=days]').check();sat.locator('[data-start]').fill('00:00');sat.locator('[data-end]').fill('08:00');sat.locator('[data-action=rule-add]').click();sat.locator('[data-start]').last.fill('15:00');sat.locator('[data-end]').last.fill('00:00')
  page.locator('[data-action=rule-day-open][data-id="6"]').click();sun=page.locator('[data-rule-day="6"]');sun.locator('[name=days]').check();sun.locator('[data-full-day]').check();expect(page.locator('.rule-week-total')).to_contain_text('71 h')
  assert page.locator('.rule-day-tabs').evaluate('el=>el.getBoundingClientRect().bottom<=document.querySelector(".rule-editor-layout").getBoundingClientRect().top+1')
  assert page.locator('.rule-coverage-track rect').first.evaluate('el=>el.getBoundingClientRect().width>0')
  page.screenshot(path='/tmp/pulse107-rule.png')
  for width,height in [(1024,600),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.locator('#modal .dialog-footer').evaluate('el=>el.getBoundingClientRect().bottom<=innerHeight')
  page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
  r=ctx.request.get(base+'/api/state').json();rule=next(x for x in r['rules'] if x['name']=='Semana visual');assert len(rule['segments'])==13
  # Personal scope has the same history/comparison tools but no people selectors.
  ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=myAnalytics]').click();page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-person]')).to_have_count(0)
  page.locator('#analytics-search').fill('INC-BETA');expect(page.locator('#analytics-records tbody tr')).to_have_count(0);expect(page.locator('.metric-all strong')).to_have_text('0 h')
  assert not errors,errors
  b.close();print('PASS: dashboard totals and hours, month comparison, group/person drilldown, shared search, mobile containment; 71-hour visual rule with weekday copy, Saturday exceptions and full Sunday; personal privacy; no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
