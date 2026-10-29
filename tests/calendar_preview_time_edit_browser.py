"""Expanded calendar fits the viewport; actual OT time edits recalculate Claim and ADP."""
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
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':780});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
  page.locator('[data-action=calendar-preview]').click();expect(page.locator('#modal.calendar-preview-dialog')).to_be_visible()
  page.locator('#modal [data-preview-month]').fill('2026-05');page.locator('#modal [data-preview-month]').dispatch_event('change');page.wait_for_function('()=>!busy')
  expect(page.locator('#modal [data-calendar-date]')).to_have_count(42)
  for width,height in [(1440,780),(1024,600),(720,480),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.locator('#modal').evaluate("el=>{const b=el.getBoundingClientRect(),f=el.querySelector('.dialog-footer').getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.top>=0&&b.bottom<=innerHeight+1&&f.bottom<=innerHeight+1}")
   assert page.locator('#modal .calendar-grid').evaluate("el=>{const grid=el.getBoundingClientRect();const f=el.closest('dialog').querySelector('.dialog-footer').getBoundingClientRect();return grid.bottom<=f.top+1&&[...el.querySelectorAll('.calendar-date-button')].every(x=>{const r=x.getBoundingClientRect();return r.top>=grid.top-1&&r.bottom<=grid.bottom+1})}")
   expect(page.locator('#modal [data-calendar-date="2026-05-31"]')).to_be_visible()
  page.set_viewport_size({'width':1440,'height':780});page.wait_for_timeout(150);page.screenshot(path='/tmp/pulse106-calendar-preview.png')
  page.locator('#modal [data-action=calendar-preview-next]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal [data-preview-month]')).to_have_value('2026-06')
  page.locator('#modal [data-preview-month]').fill('2026-01');page.locator('#modal [data-preview-month]').dispatch_event('change');page.wait_for_function('()=>!busy')
  page.locator('#modal [data-calendar-date="2026-01-03"] .calendar-preview-count').click()
  original=next(o for o in fixture.uc.get('/api/state').json()['overtime'] if o['reference']=='CHG-90MIN')
  page.locator('#modal [data-id="ot:'+original['id']+'"]').click();page.locator('#modal [data-action=ot-edit]').click()
  expect(page.locator('#modal [name=actual_start]')).to_have_value('2026-01-03T03:00')
  expect(page.locator('#modal [name=actual_end]')).to_have_value('2026-01-03T04:30')
  expect(page.locator('#modal [name=time_change_reason]')).not_to_be_visible()
  page.locator('#modal [name=actual_end]').fill('2026-01-03T05:00');expect(page.locator('#modal [name=time_change_reason]')).to_be_visible();page.locator('#modal [name=time_change_reason]').fill('Corregir fin de la actividad')
  page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible()
  pending=fixture.uc.get('/api/state').json();assert next(o for o in pending['overtime'] if o['id']==original['id'])['status']=='SUBMITTED'
  f.approve(fixture.mc,'ot',original['id'])
  page.locator('.sidebar [data-page=claim]').click();page.wait_for_function('()=>!busy');week=page.locator('[data-claim-week="2026-01-03"]');week.evaluate('(el)=>PulseLayout.reveal(el)')
  expect(week.locator('[data-claim-kind=OT] [data-claim-date="2026-01-03"]')).to_have_text('2')
  expect(week.locator('[data-claim-kind=GUARD] [data-claim-date="2026-01-03"]')).to_have_text('6')
  page.locator('.sidebar [data-page=adp]').click();page.wait_for_function('()=>!busy')
  expect(page.locator('tbody tr').filter(has_text='CHG-90MIN').locator('td').last).to_have_text('02:00')
  assert not errors,errors
  browser.close();print('PASS: expanded six-week Sunday calendar in desktop/small/zoom-like/mobile viewports, all dates visible, preview month navigation, edited actual OT hours, required correction reason, reapproval and matching Claim/ADP/Guard totals; no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 fixture.tearDown()
