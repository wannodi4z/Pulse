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
  state=context.request.get(base+'/api/state').json();manager=next(u for u in state['people'] if u['employee_id']=='MGR0001');lead=next(u for u in state['people'] if u['employee_id']=='SL0001')
  cases=[('new-manager',"personModal('','MANAGER',"+repr(aid)+")"),('edit-manager',"personModal("+repr(manager['id'])+")"),('edit-lead',"personModal("+repr(lead['id'])+")"),('offboard-manager',"lifecycleModal("+repr(manager['id'])+")"),('offboard-lead',"lifecycleModal("+repr(lead['id'])+")"),('account',"accountModal()"),('activation-code',"credentials('ACT-ABCDEF1234','MGR0001')")]
  checks=0
  for name,opener in cases:
   page.set_viewport_size({'width':1440,'height':780});page.evaluate(opener);expect(page.locator('#modal')).to_be_visible();page.wait_for_timeout(120)
   for width,height in [(1440,780),(1280,650),(390,844)]:
    page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
    modal=page.locator('#modal');box=modal.bounding_box();assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1,(name,width,box)
    for _ in range(15):
     problems=modal.evaluate("""el=>{const fields=[...el.querySelectorAll('.field')].filter(n=>n.getClientRects().length).map(n=>({text:n.textContent.trim().slice(0,45),r:n.getBoundingClientRect()}));const pairs=[];for(let i=0;i<fields.length;i++)for(let j=i+1;j<fields.length;j++){const a=fields[i],b=fields[j];if(a.r.left<b.r.right-1&&a.r.right>b.r.left+1&&a.r.top<b.r.bottom-1&&a.r.bottom>b.r.top+1)pairs.push([a.text,b.text]);}return pairs;}""");assert not problems,(name,width,problems)
     footer=modal.locator('.dialog-footer').bounding_box();assert footer and footer['y']+footer['height']<=height+1,(name,width,footer)
     assert modal.evaluate('(el)=>el.scrollWidth<=el.clientWidth+1'),(name,width,'horizontal overflow')
     page.screenshot(path='/tmp/pulse121-dialog-current.png',full_page=True)
     body=modal.locator('.form-body');assert not body.count() or body.evaluate('(el)=>el.scrollHeight<=el.clientHeight+1||["auto","scroll"].includes(getComputedStyle(el).overflowY)'),(name,width,'inaccessible body')
     if body.count():
      body.evaluate('el=>{el.scrollTop=el.scrollHeight}')
      assert modal.locator('.dialog-footer').evaluate('el=>el.getBoundingClientRect().bottom<=innerHeight+1'),(name,width,'footer lost while scrolling')
      body.evaluate('el=>el.scrollTop=0')
     checks+=1
     if width==1280 and _==0:page.screenshot(path='/tmp/pulse121-'+name+'.png',full_page=True)
     nxt=modal.locator('[data-step-next]:visible:not(:disabled)')
     if not nxt.count():break
     for field in modal.locator('input:visible:not([readonly]),select:visible').all():
      tag=field.evaluate('(el)=>el.tagName');kind=field.get_attribute('type')
      if tag=='SELECT':
       values=field.locator('option').evaluate_all('(els)=>els.map(el=>el.value).filter(Boolean)')
       if values:field.select_option(values[0])
      elif kind=='checkbox':field.check()
      elif kind=='email':field.fill('modal@example.test')
      else:field.fill('Prueba de distribución')
     nxt.click();page.wait_for_timeout(80)
   page.locator('#modal [data-action=close]').first.click()
  # Exercise the redesigned offboarding form through a real atomic reassignment.
  response=context.request.post(base+'/api/people',data={'role':'MANAGER','account_id':aid,'employee_id':'MODAL-MGR','first':'Destino','last':'Validación','email':'modal-manager@example.test'});assert response.ok,response.text();created=response.json();target=created['id']
  assert context.request.post(base+'/api/activate',data={'identity':'MODAL-MGR','code':created['activation_code'],'password':'ModalManager2026!'}).ok
  page.set_viewport_size({'width':1280,'height':650});page.evaluate('()=>refresh()');page.evaluate('id=>lifecycleModal(id)',manager['id']);expect(page.locator('#modal')).to_be_visible()
  bulk=page.locator('#modal [name=bulk_destination]');bulk.evaluate('(el)=>PulseLayout.reveal(el)');bulk.select_option(target)
  assert page.locator('#modal [name^="transfer:"]').evaluate_all('(els)=>els.every(el=>el.value===document.querySelector("[name=bulk_destination]").value)')
  destination=page.locator('#modal [name=lead_manager_id]');destination.evaluate('(el)=>PulseLayout.reveal(el)');destination.select_option(target)
  reason=page.locator('#modal [name=reason]');reason.evaluate('(el)=>PulseLayout.reveal(el)');reason.fill('Reasignación completa por baja del Manager')
  confirmation=page.locator('#modal [name=confirm]');confirmation.evaluate('(el)=>PulseLayout.reveal(el)');confirmation.check();save();expect(page.locator('#modal')).not_to_be_visible()
  result=context.request.get(base+'/api/state').json();assert next(u for u in result['people'] if u['id']==manager['id'])['status']=='DISABLED';assert all(g['manager_id']==target for g in result['groups'] if g['id'] in [x['id'] for x in state['groups'] if x['manager_id']==manager['id']]);assert next(u for u in result['people'] if u['id']==lead['id'])['manager_id']==target
  page.evaluate('id=>lifecycleModal(id)',lead['id']);expect(page.locator('#modal')).to_be_visible();reason=page.locator('#modal [name=reason]');reason.evaluate('(el)=>PulseLayout.reveal(el)');reason.fill('Baja de Lead de validación');confirmation=page.locator('#modal [name=confirm]');confirmation.evaluate('(el)=>PulseLayout.reveal(el)');confirmation.check();save();expect(page.locator('#modal')).not_to_be_visible()
  result=context.request.get(base+'/api/state').json();assert next(u for u in result['people'] if u['id']==lead['id'])['status']=='DISABLED'
  assert not errors,errors
  print(f'PASS: {checks} dialog/page checks across 7 administrative dialogs at 1440/1280/390, nonoverlapping fields, bounded dialogs and footers, no horizontal overflow, scrollable single-view bodies with fixed footers and reachable fields; actual Manager offboarding transfers all Groups and direct Lead, actual Lead offboarding; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
