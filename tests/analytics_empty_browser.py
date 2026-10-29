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
  page.locator('[name=filter-person]').select_option(fixture.other['id']);page.wait_for_function('()=>!busy')
  page.locator('#month').fill('2026-02');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  expect(page.locator('.analytics-empty')).to_contain_text('Persona SECOND no tiene registros con estos filtros')
  expect(page.locator('.metric-all strong')).to_have_text('0 h')
  expect(page.locator('#main')).not_to_contain_text('Consultando registros')
  page.locator('[data-action=analytics-reset]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('.analytics-empty')).not_to_be_visible()
  # A failed request must never leave a permanent loading message.
  page.route('**/api/analytics?**',lambda route:route.fulfill(status=500,json={'detail':'Prueba de error'}))
  page.locator('[name=filter-person]').select_option(fixture.other['id']);page.wait_for_function('()=>!busy')
  expect(page.locator('#main')).to_contain_text('No se pudieron consultar los registros')
  expect(page.locator('#main')).not_to_contain_text('Consultando registros')
  assert not errors,errors
  print('PASS: employee without records shows named empty state and zero hours; reset restores data; network failure shows explicit error, never indefinite loading')
  b.close()
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
