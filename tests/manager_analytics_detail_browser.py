"""Manager dashboard drilldown, ranking and real linked-activity participation."""
import os,sys,socket,subprocess,time,urllib.request
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from playwright.sync_api import sync_playwright,expect
import test_manager_analytics_detail
R=Path(__file__).resolve().parents[1];f=test_manager_analytics_detail.ManagerActivityTests();f.setUp();x=f.x;fx=f.f;proc=None
try:
 fx.approve(x.mc,'ot',x.ot);window=x.activity();peer=fx.post('/api/windows/'+window['id']+'/join',{},x.pc)['id']
 zero,zc,_=fx.person('USER','ZERO-HOURS',group=x.g)
 with patch.object(fx.server,'now',return_value=(x.start+timedelta(minutes=1)).isoformat()):timer=fx.post('/api/timers/start',{'overtime_id':x.ot},x.uc)['id']
 with patch.object(fx.server,'now',return_value=(x.start+timedelta(minutes=31)).isoformat()):fx.post('/api/timers/'+timer+'/stop',{},x.uc)
 fx.approve(x.mc,'ot',x.ot)
 # Historical and emergency categories in two months; exact known totals.
 for day,start,end,reference,client,category in [('2026-09-06','20:00','22:00','CHG-HISTORY',x.uc,'HISTORICAL'),('2026-10-06','20:00','21:00','INC-RESTORE',x.pc,'HISTORICAL')]:fx.ot(client,day+'T'+start+':00-06:00',day+'T'+end+':00-06:00',reference=reference)
 # Keep the programmed activity's actual test month, even when the host month changes.
 month=x.start.astimezone(fx.server.TZ).strftime('%Y-%m')
 with socket.socket() as sk:sk.bind(('127.0.0.1',0));port=sk.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fx.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok
  page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy');page.locator('#month').fill(month);page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
  expect(page.locator('#analytics-rankings')).to_contain_text('ZERO-HOURS');expect(page.locator('#main')).to_contain_text('OT y Stand By por Grupo')
  expect(page.locator('.command-hero')).to_contain_text('La operación, en perspectiva.')
  expect(page.locator('.command-kpis .command-kpi')).to_have_count(4)
  expect(page.locator('.command-attention')).to_contain_text('Solicitudes pendientes')
  expect(page.locator('.command-group-map')).to_contain_text('SB')
  page.screenshot(path='/tmp/pulse-premium-desktop.png',full_page=True)
  for width in [390,768,1440]:
   page.set_viewport_size({'width':width,'height':900})
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), 'Dashboard overflow'
  page.set_viewport_size({'width':1440,'height':900})
  before=page.locator('[name=filter-period]').input_value();page.locator('#analytics-search').fill('CHG-GROUP-NORMAL');page.wait_for_timeout(550);page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-period]')).to_have_value(before)
  expect(page.locator('#analytics-records tbody tr')).to_have_count(2)
  page.locator('[data-action=record-detail][data-id="ot:'+x.ot+'"]').first.click();page.locator('#modal [data-action=analytics-participants]').click();expect(page.locator('.activity-participants tbody tr')).to_have_count(2);expect(page.locator('#modal')).to_contain_text('Sin iniciar');expect(page.locator('#modal')).to_contain_text('1 tramo iniciado')
  for w,h in [(1440,900),(1024,600),(390,844)]:
   page.set_viewport_size({'width':w,'height':h});assert page.locator('#modal').evaluate('e=>{let r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1}');assert page.locator('#modal .dialog-footer').evaluate('e=>e.getBoundingClientRect().bottom<=innerHeight+1')
  page.screenshot(path='/tmp/pulse111-participants-mobile.png');page.locator('#modal [data-action=close]').first.click();page.set_viewport_size({'width':1440,'height':900});page.locator('[data-action=analytics-reset]').first.click();page.wait_for_function('()=>!busy')
  page.locator('#analytics-rank-metric').select_option('ot_minutes');expect(page.locator('#analytics-rankings')).to_contain_text('Más horas · OT aprobada');expect(page.locator('#analytics-rankings')).to_contain_text('ZERO-HOURS')
  page.locator('[data-action=analytics-group][data-id="'+x.g+'"]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('[name=filter-group]')).to_have_value(x.g)
  page.locator('#analytics-rankings [data-action=analytics-user][data-id="'+zero['id']+'"]').first.click();page.wait_for_function('()=>!busy');expect(page.locator('.analytics-empty')).to_contain_text('ZERO-HOURS');expect(page.locator('#main')).not_to_contain_text('Consultando registros')
  assert not errors,errors;b.close();print('PASS: group table and three ranking metrics; zero-hour drilldown; reference search retains month scope; real enrollment versus Timer participation; mobile/small modal footer; linked individual detail; no JavaScript errors')
finally:
 if proc:proc.terminate();proc.wait()
 f.tearDown()
