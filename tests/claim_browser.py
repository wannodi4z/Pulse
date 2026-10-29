"""Capture-ready Claim matrix and unchanged ADP layout, using approved accounting."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_claim_capture import ClaimCaptureTests
ROOT=Path(__file__).resolve().parents[1]
fixture=ClaimCaptureTests();fixture.setUp();f=fixture.f;process=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':780},permissions=['clipboard-read','clipboard-write']);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=claim]').click();page.wait_for_function('()=>!busy')
  page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');page.locator('h1').click();page.wait_for_function('()=>!busy')
  week=page.locator('[data-claim-week="2026-01-03"]');week.evaluate('(el)=>PulseLayout.reveal(el)')
  assert week.locator('thead th span').all_text_contents()==['Sáb','Dom','Lun','Mar','Mié','Jue','Vie']
  expect(week.locator('tbody tr')).to_have_count(2)
  expect(week.locator('[data-claim-kind=OT] [data-claim-date="2026-01-03"]')).to_have_text('1.5')
  expect(week.locator('[data-claim-kind=GUARD] [data-claim-date="2026-01-03"]')).to_have_text('6.5')
  expect(week.locator('[data-claim-kind=GUARD] .claim-row-total')).to_have_text('54.5')
  expect(page.locator('[data-action=claim-copy]')).to_have_count(0)
  expect(week.locator('thead th')).to_have_count(9)
  week.locator('[data-action=claim-detail]').click();expect(page.locator('#modal')).to_contain_text('CHG-90MIN')
  expect(page.locator('#modal .claim-detail-table thead th')).to_have_count(5)
  expect(page.locator('#modal .claim-detail-summary')).to_contain_text('Stand By')
  for width,height in [(1440,780),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.locator('#modal .dialog-footer').evaluate('el=>el.getBoundingClientRect().bottom<=innerHeight+1')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.set_viewport_size({'width':1440,'height':780});page.locator('#modal [data-action=close]').first.click()
  page.locator('#toast').evaluate("el=>el.classList.remove('visible')");page.screenshot(path='/tmp/pulse-claim-matrix.png')
  for width,height in [(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});week.evaluate('(el)=>PulseLayout.reveal(el)')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  page.set_viewport_size({'width':1440,'height':780})
  page.locator('.sidebar [data-page=adp]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('h1')).to_have_text('ADP');expect(page.locator('.claim-matrix')).to_have_count(0)
  expect(page.locator('thead th').last).to_have_text('Duración HH:MM')
  expect(page.locator('tbody').first).to_contain_text('01:30')
  assert not errors,errors
  browser.close();print('PASS: Claim Saturday-Friday matrix, decimal OT/Stand By, net subtraction, weekly totals, nine aligned columns without copy action, detailed table, responsive containment and unchanged ADP HH:MM; no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 fixture.tearDown()
