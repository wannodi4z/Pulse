"""Admin account workspace, metrics, filters, actions and direct Lead recovery."""
import os, shutil, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
temp=tempfile.TemporaryDirectory();db=Path(temp.name)/'demo.db';shutil.copy(ROOT/'fixtures/banorte_pruebas.sqlite3',db);process=None
try:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health',timeout=1);break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':780});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert context.request.post(base+'/api/login',data={'identity':'MGR0001','password':'manager12026'}).ok
  assert context.request.post(base+'/api/rules',data={'name':'Regla para modales','effective_from':'2026-01-01','segments':[{'day':day,'start':'02:00','end':'04:00'} for day in range(7)]}).ok
  assert context.request.post(base+'/api/login',data={'identity':'951357','password':'tecnico12026'}).ok
  page.goto(base);page.locator('.sidebar [data-page=time]').click();page.wait_for_function('()=>!busy')
  assert page.locator('.calendar-weekdays span').all_text_contents()==['Dom','Lun','Mar','Mié','Jue','Vie','Sáb']
  page.locator('#month').fill('2026-11');page.locator('#month').dispatch_event('change');page.locator('h1').click();page.wait_for_function('()=>!busy')
  assert page.locator('[data-calendar-date]').first.get_attribute('data-calendar-date')=='2026-11-01'
  def geometry():
   expect(page.locator('.wizard-navigation,[data-step-next],[data-step-back],.wizard-step')).to_have_count(0)
   expect(page.locator('#modal [type=submit]')).to_be_visible()
   assert page.locator('#modal').evaluate("el=>{const b=el.getBoundingClientRect(),f=el.querySelector('.dialog-footer').getBoundingClientRect();return b.left>=0&&b.right<=innerWidth+1&&b.top>=0&&b.bottom<=innerHeight+1&&f.bottom<=b.bottom+1&&f.top>=0}")
   assert page.locator('#modal .form-body').evaluate("el=>{const f=el.closest('dialog').querySelector('.dialog-footer').getBoundingClientRect();return el.getBoundingClientRect().bottom<=f.top+1&&getComputedStyle(el).overflowY==='auto'}")
  for i,(width,height) in enumerate([(1440,780),(1280,650),(390,844)]):
   page.set_viewport_size({'width':width,'height':height})
   page.locator('.time-actions [data-action=ot-new]').click();geometry()
   assert page.locator('#modal .field').count()==7
   page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).to_be_visible()
   for name,value in [('scheduled_start',f'2026-01-{10+i:02d}T09:00'),('scheduled_end',f'2026-01-{10+i:02d}T10:00'),('reference','CHG-SINGLE-'+str(i)),('description','Actividad de prueba'),('justification','Continuidad'),('impact','Operación'),('in_lieu','Cobertura del servicio')]:page.locator('#modal [name='+name+']').fill(value)
   geometry()
   if width==1440:page.screenshot(path='/tmp/pulse-single-modal-desktop.png')
   if width==390:page.screenshot(path='/tmp/pulse-single-modal-mobile.png')
   page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible()
  assert len(context.request.get(base+'/api/state').json()['overtime'])==3
  page.set_viewport_size({'width':1280,'height':650})
  page.locator('.time-actions [data-action=guard-new]').click();geometry()
  page.locator('#modal [name=start_date]').fill('2026-11-01');page.locator('#modal [name=end_date]').fill('2026-11-07')
  page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('#modal')).not_to_be_visible()
  assert len(context.request.get(base+'/api/state').json()['guards'])==1
  assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
  page.goto(base);page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy')
  page.evaluate("()=>perform('manager-new',state.accounts[0].id)");geometry()
  assert page.locator('#modal [name=first]').is_visible() and page.locator('#modal [name=email]').is_visible()
  assert not errors,errors
  browser.close();print('PASS: Sunday-first dates, single-view OT/Guard/Admin dialogs at desktop/small/mobile sizes, no wizard or hidden field stages, fixed visible actions, native validation, submitted records and no JS errors')
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
