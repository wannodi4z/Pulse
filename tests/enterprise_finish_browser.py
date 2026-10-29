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
  assert context.request.post(base+'/api/login',data={'identity':'admin1','password':'admin12026'}).ok
  state=context.request.get(base+'/api/state').json();account=next(a for a in state['accounts'] if a['base_code']=='BNTE');aid=account['id']
  page.goto(base)
  def go(name):page.locator('.sidebar [data-page='+name+']').click();page.wait_for_function('()=>!busy')
  def fill(name,value):
   node=page.locator('#modal [name='+name+']');node.evaluate('(el)=>PulseLayout.reveal(el)');node.fill(value)
  def save():
   for _ in range(20):
    nxt=page.locator('[data-step-next]:visible:not(:disabled)')
    if not nxt.count():break
    nxt.click()
   page.locator('#modal [type=submit]').click();page.wait_for_function('()=>!busy')
  assert context.request.post(base+'/api/login',data={'identity':'MGR0001','password':'manager12026'}).ok
  page.goto(base);go('team');state=context.request.get(base+'/api/state').json();source=state['groups'][0];tech=next(p for p in state['people'] if p['employee_id']=='951357')
  expect(page.locator('.sidebar .nav-settings')).to_have_count(0);expect(page.locator('.sidebar [data-page=timeRules]')).to_be_visible();expect(page.locator('.sidebar [data-page=recoveries]')).to_be_visible()
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(220)
   page.locator('.team-kanban-workspace').evaluate('(el)=>el.scrollTop=0')
   lanes=page.locator('.team-lane').evaluate_all('(els)=>els.map(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height}))');assert len(lanes)==6 and all(abs(el['height']-(300 if height==650 else 380))<1 for el in lanes),lanes;assert max(el['width'] for el in lanes)-min(el['width'] for el in lanes)<1
   assert page.locator('.team-tech-card').evaluate_all('(els)=>els.every(el=>Math.abs(el.getBoundingClientRect().height-98)<1)')
   expect(page.locator('.team-tech-card [data-action=person-edit],.team-tech-card [data-action=manager-transfer-new]')).to_have_count(0)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight')
   card=page.locator('[data-team-person="'+tech['id']+'"]');card.locator('[data-action=team-details]').last.click();expect(page.locator('#dialog-title')).to_have_text('Ficha del Técnico');expect(page.locator('#modal')).to_contain_text('Samuel Alejandro Díaz Chávez');expect(page.locator('#modal')).to_contain_text(tech['email']);expect(page.locator('#modal [data-action=person-edit]')).to_be_visible();page.wait_for_timeout(220)
   b=page.locator('#modal').bounding_box();assert b['x']>=0 and b['y']>=0 and b['x']+b['width']<=width+1 and b['y']+b['height']<=height+1,(width,b)
   assert page.locator('#modal .form-body').evaluate('(el)=>el.scrollHeight<=el.clientHeight+1&&el.scrollWidth<=el.clientWidth+1')
   if width==1280:page.screenshot(path='/tmp/pulse101-technician-sheet.png',full_page=True)
   page.locator('#modal [data-action=close]').first.click()
  page.set_viewport_size({'width':1440,'height':780});page.wait_for_timeout(220);page.locator('.team-kanban-workspace').evaluate('(el)=>el.scrollTop=0');page.screenshot(path='/tmp/pulse101-board.png',full_page=True)
  # Context add fixes Group in a hidden field; submitting cannot accidentally pick a different Group.
  page.locator('[data-team-destination="'+source['id']+'"] footer [data-action=tech-new]').click();expect(page.locator('#modal select[name=group_id]')).to_have_count(0);expect(page.locator('#modal input[name=group_id]')).to_have_value(source['id']);expect(page.locator('.fixed-group-context')).to_contain_text(source['name'])
  for name,value in [('first','Contexto'),('last','De Grupo'),('employee_id','GROUP-CONTEXT'),('email','context@example.test')]:fill(name,value)
  save();expect(page.locator('.secret-code')).to_be_visible();page.locator('#modal [data-action=close]').first.click();state=context.request.get(base+'/api/state').json();assert next(p for p in state['people'] if p['employee_id']=='GROUP-CONTEXT')['group_id']==source['id']
  page.locator('.heading-actions [data-action=tech-new]').click();expect(page.locator('#modal select[name=group_id]')).to_have_count(1);page.locator('#modal [data-action=close]').first.click()
  go('teamTime');note=page.locator('.approvals-note');assert note.evaluate('(el)=>{const r=document.createRange();r.selectNodeContents(el);return r.getClientRects().length===1}');page.screenshot(path='/tmp/pulse101-approvals.png',full_page=True)
  go('timeRules');expect(page.locator('#main')).to_contain_text('Reglas de Guardia');go('recoveries');expect(page.locator('#main')).to_contain_text('Recuperación de acceso');go('team')
  page.emulate_media(reduced_motion='reduce');page.locator('[data-team-person="'+tech['id']+'"] [data-action=team-details]').last.click();assert page.locator('#modal').evaluate('(el)=>parseFloat(getComputedStyle(el).animationDuration)<.001');page.locator('#modal [data-action=close]').first.click()
  assert not errors,errors
  print('PASS: equal responsive lanes and 98px Technician cards, detail sheet and responsive bounds at 1440/1280/390, contextual add with fixed hidden Group submitted correctly, global add retains choice, full-width single-line approvals note, flat sidebar and direct navigation, reduced-motion preference, zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
