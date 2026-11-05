"""One modal: recurring availability and original-vs-worked historical hours."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
import test_api
R=Path(__file__).resolve().parents[1];f=test_api.PulseTests();f.setUp();proc=None
try:
 a,g,m,mc,u,tc=f.organization()
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1100});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  def login(emp):
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':emp,'password':'Password2026!'}).ok;page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>!busy')
  def go(view):page.evaluate('(v)=>navigate(v)',view);page.wait_for_function('()=>!busy')
  login('M001');go('timeRules');page.locator('[data-action=ot-policy]').click();expect(page.locator('#modal [name=start_time]')).to_have_value('21:00');expect(page.locator('#modal [name=end_time]')).to_have_value('08:00');page.locator('#modal [name=enabled]').check();page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible()
  login('T001');go('time');page.locator('[data-action=ot-new]').click();page.locator('#modal [name=scheduled_start]').fill('2030-11-02T21:00');page.locator('#modal [name=scheduled_end]').fill('2030-11-05T08:00');expect(page.locator('#ot-daily-preview')).to_contain_text('3 franjas');expect(page.locator('#modal [data-historical-work]')).not_to_be_visible()
  # Changing only the dates to the past reveals actual work IN THE SAME DIALOG.
  page.locator('#modal [name=scheduled_start]').fill('2026-01-05T21:00');page.locator('#modal [name=scheduled_end]').fill('2026-01-07T08:00');expect(page.locator('#modal [data-historical-work]')).to_be_visible();assert page.locator('[data-historical-work]').evaluate('e=>e.getBoundingClientRect().width/e.closest(".form-body").getBoundingClientRect().width>.85');expect(page.locator('#modal .ot-daily-schedule')).not_to_be_visible();expect(page.locator('#modal')).to_have_count(1)
  page.locator('[data-historical-start]').fill('2026-01-05T22:00');page.locator('[data-historical-end]').fill('2026-01-05T23:00');page.locator('[data-action=historical-add-tranche]').click();page.locator('[data-historical-start]').nth(1).fill('2026-01-06T22:00');page.locator('[data-historical-end]').nth(1).fill('2026-01-06T23:30');expect(page.locator('[data-historical-duration]')).to_contain_text('2.5 h')
  for name,value in [('reference','CHG-ORIGINAL'),('description','Dos noches de mantenimiento'),('justification','Registro posterior de dos tramos reales'),('impact','Servicio'),('in_lieu','Cobertura requerida')]:page.locator('#modal [name='+name+']').fill(value)
  page.screenshot(path='/tmp/pulse112-historical-modal.png');page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible()
  overtime=ctx.request.get(base+'/api/state').json()['overtime'][0];assert overtime['worked_seconds']==9000 and overtime['capture_type']=='HISTORICAL' and len(overtime['actual_segments'])==2
  page.evaluate('(id)=>detailModal("ot:"+id)',overtime['id']);expect(page.locator('#modal')).to_contain_text('Ventana originalmente programada');expect(page.locator('#modal')).to_contain_text('2.5 h')
  page.locator('#modal .dialog-header [data-action=close]').click();go('time');page.locator('[data-action=ot-new]').click();page.locator('#modal [name=scheduled_start]').fill('2030-11-02T21:00');page.locator('#modal [name=scheduled_end]').fill('2030-11-05T08:00')
  for name,value in [('reference','CHG-NIGHT'),('description','Tres noches'),('justification','Mantenimiento'),('impact','Servicio'),('in_lieu','Cobertura')]:page.locator('#modal [name='+name+']').fill(value)
  page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();o=next(x for x in ctx.request.get(base+'/api/state').json()['overtime'] if x['reference']=='CHG-NIGHT');assert o['schedule']['start_time']=='21:00' and o['schedule']['end_time']=='08:00'
  for width in (1024,390):
   page.set_viewport_size({'width':width,'height':844});page.evaluate('(id)=>otModal(id)',overtime['id']);expect(page.locator('#modal')).to_be_visible();assert page.locator('#modal').evaluate('e=>e.scrollWidth<=e.clientWidth+1');page.locator('#modal .dialog-header [data-action=close]').click()
  assert not errors,errors;browser.close();print('PASS: Manager policy 21–08, recurring 3-night preview, past-date detection reveals original schedule and two actual tranches in ONE modal, 2.5-hour payload, future plan snapshot, detail and mobile; no JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 f.tearDown()
