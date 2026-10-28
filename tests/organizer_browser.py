"""Native staged drag workspace, cancellation/review and four-Group overview with two example teams."""
import os,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
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
  page.goto(base);page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy')
  state=context.request.get(base+'/api/state').json();assert len(state['accounts'])==2
  manager=next(u for u in state['people'] if u['employee_id']=='MGR0001');lead=next(u for u in state['people'] if u['employee_id']=='SL0001');samuel=next(u for u in state['people'] if u['employee_id']=='951357')
  assert samuel['first']+' '+samuel['last']=='Samuel Alejandro Díaz Chávez'
  block=page.locator('[data-manager="'+manager['id']+'"]');block.evaluate('(el)=>PulseLayout.reveal(el)')
  expect(block.locator('.manager-header .direct-lead-person')).to_contain_text('SL0001');expect(block.locator('.group-grid .direct-lead-person')).to_have_count(0)
  expect(block.locator('[data-action=person-edit]').filter(has_text='Editar Lead')).to_be_visible()
  for width,height in [(1440,780),(1280,650)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100);block.evaluate('(el)=>PulseLayout.reveal(el)')
   count=block.locator('.group-card:visible').count();print('Groups visible',width,height,count,flush=True);assert count==4,(width,height,count)
   assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
   issues=block.evaluate('(el)=>{const b=document.querySelector(".viewport-stage").getBoundingClientRect();return [...el.querySelectorAll("button,select")].filter(n=>n.getClientRects().length).map(n=>{const r=n.getBoundingClientRect();return {text:n.textContent.slice(0,30),bottom:r.bottom-b.bottom,right:r.right-b.right,left:r.left-b.left}}).filter(r=>r.bottom>2||r.right>1||r.left< -1)}')
   if issues:
    page.screenshot(path='/workspace/org113-debug.png')
    print(page.locator('#main').evaluate('(el)=>[...el.children].map(n=>({tag:n.tagName,cl:n.className,h:n.getBoundingClientRect().height,y:n.getBoundingClientRect().y}))'),flush=True)
   assert not issues,(width,height,issues)
  # No Lead: the Manager header exposes a direct Add Lead action.
  created=context.request.post(base+'/api/people',data={'role':'MANAGER','employee_id':'EMPTY-MGR','first':'Manager','last':'Sin backup','email':'empty@example.test','account_id':state['accounts'][0]['id'],'group_ids':[]});assert created.ok
  page.reload();page.locator('.sidebar [data-page=organization]').click();empty=page.locator('[data-manager="'+created.json()['id']+'"]');empty.evaluate('(el)=>PulseLayout.reveal(el)');expect(empty.locator('[data-action=lead-new]')).to_be_visible()
  empty.locator('[data-action=lead-new]').click();expect(page.locator('#modal [name=is_lead]')).to_be_checked();expect(page.locator('#modal [name=manager_id]')).to_have_value(created.json()['id']);page.locator('#modal [data-action=close]').first.click()
  # The organizer shows both Account contexts and does not write while staging.
  page.locator('[data-action=organizer-open]:visible').first.click();expect(page.locator('#modal')).to_have_class('wide organizer-dialog')
  source=samuel['group_id'];target=next(g['id'] for g in state['groups'] if g['account_id']!=next(g for g in state['groups'] if g['id']==source)['account_id'])
  page.locator('[name=board-source]').select_option(source);page.locator('[name=board-destination]').select_option(target)
  card=page.locator('[data-board-person="'+samuel['id']+'"]');expect(card).to_be_visible();card.drag_to(page.locator('[data-board-lane=destination]'))
  expect(page.locator('.organizer-bottom')).to_contain_text('1 cambios pendientes')
  assert next(u for u in context.request.get(base+'/api/state').json()['people'] if u['id']==samuel['id'])['group_id']==source
  page.locator('#modal [data-action=close]').first.click()
  assert next(u for u in context.request.get(base+'/api/state').json()['people'] if u['id']==samuel['id'])['group_id']==source
  page.locator('[data-action=organizer-open]:visible').first.click();page.locator('[name=board-source]').select_option(source);page.locator('[name=board-destination]').select_option(target)
  # Accessible click alternative to dragging.
  page.locator('[data-board-person="'+samuel['id']+'"] [data-action=organizer-move]').click()
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.locator('#modal').evaluate('(el)=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight&&[...el.querySelectorAll("button,input,select")].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.left>=b.left-1&&r.right<=b.right+1&&r.bottom<=b.bottom+1})}'),('board',width)
  page.locator('[data-action=organizer-review]').click();expect(page.locator('.organizer-review-list')).to_contain_text('Samuel Alejandro Díaz Chávez')
  for width,height in [(1440,780),(1280,650),(390,844)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
   assert page.locator('#modal').evaluate('(el)=>{const b=el.getBoundingClientRect();return [...el.querySelectorAll("button,input,select")].filter(n=>n.getClientRects().length).every(n=>n.getBoundingClientRect().bottom<=b.bottom+1)}'),('review',width)
  page.locator('[data-action=organizer-save]').click();expect(page.locator('.organizer-error')).to_contain_text('motivo')
  page.locator('#organizer-reason').fill('Cambio de especialidad probado por Admin');page.locator('[data-action=organizer-save]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
  assert next(u for u in context.request.get(base+'/api/state').json()['people'] if u['id']==samuel['id'])['group_id']==target
  assert not errors,errors
  print('PASS: two Accounts/four Managers/four Leads and named Samuel; four visible Groups at 1440/1280; Lead header/edit/add; native drag preview and cancel without writes; keyboard/click fallback; cross-account review/confirm; board/review fit 1440/1280/390; zero JS errors')
  browser.close()
finally:
 if process:process.terminate();process.wait(timeout=10)
 temp.cleanup()
