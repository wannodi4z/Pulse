"""Native-zoom viewport checks against a real server and disposable populated SQLite."""
import json,os,socket,subprocess,sys,tempfile,time,urllib.request
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]

def run():
    with tempfile.TemporaryDirectory() as tmp:
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        with open(Path(tmp)/'server.log','w+') as log:
            process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(Path(tmp)/'layout.db')},stdout=log,stderr=log)
            base=f'http://127.0.0.1:{port}'
            try:
                for _ in range(100):
                    try:urllib.request.urlopen(base+'/api/health',timeout=1);break
                    except Exception:time.sleep(.1)
                with sync_playwright() as p:
                    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE'),args=['--no-sandbox','--disable-dev-shm-usage'])
                    context=browser.new_context(viewport={'width':1440,'height':780});page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                    def post(path,data):
                        result=context.request.post(base+path,data=data);assert result.ok,(path,result.text());return result.json()
                    def login(emp,password='Password2026!'):post('/api/login',{'identity':emp,'password':password})
                    def person(role,emp,**extra):
                        result=post('/api/people',{'role':role,'employee_id':emp,'first':'Nombre de prueba','last':emp,'email':emp+'@example.test',**extra})
                        # Activation doesn't change the administrator's session.
                        post('/api/activate',{'identity':emp,'code':result['activation_code'],'password':'Password2026!'})
                        return result['id']
                    login('admin1','admin12026');account=post('/api/accounts',{'code':'AC','name':'Cuenta de pruebas de pantalla'})['id']
                    groups=[post('/api/groups',{'account_id':account,'code':'G'+str(i),'name':'Grupo '+str(i)})['id'] for i in range(3)]
                    manager=person('MANAGER','M001',account_id=account,group_ids=groups)
                    for i in range(12):person('USER','T'+str(i),group_id=groups[i%3],is_lead=i==0)
                    # Populate real approved time so reports, histories and exports are not tested empty.
                    login('T1');month=datetime.now().strftime('%Y-%m');overtime=[]
                    for day in range(1,9):
                        overtime.append(post('/api/overtime',{'capture_type':'HISTORICAL','scheduled_start':f'{month}-{day:02}T20:00:00-06:00','scheduled_end':f'{month}-{day:02}T21:00:00-06:00','reference':'CHG123456','description':'Trabajo de prueba','justification':'Servicio','impact':'Operación','in_lieu':'Cobertura'})['id'])
                    login('M001')
                    for identity in overtime:post('/api/approvals/ot/'+identity,{'decision':'APPROVED'})
                    # Actual HTML drag-and-drop: preview/cancel, confirm and keyboard fallback.
                    login('admin1','admin12026');page.goto(base);page.locator('.sidebar [data-page=organization]').click()
                    page.wait_for_function('()=>page==="organization" && document.querySelector(".account-block")')
                    state=context.request.get(base+'/api/state').json();tech=next(n for n in state['people'] if n['employee_id']=='T1')
                    card=page.locator('[data-person="'+tech['id']+'"]');target=page.locator('[data-group="'+groups[0]+'"] > header')
                    card.evaluate('(el)=>PulseLayout.reveal(el)')
                    card.locator('.technician-open').focus();page.keyboard.press('Enter')
                    expect(page.locator('#modal [data-form=person]')).to_be_visible();page.locator('#modal [data-action=close]').first.click()
                    if os.environ.get('PULSE_SCREENSHOT_DIR'):
                        preview=Path(os.environ['PULSE_SCREENSHOT_DIR']);preview.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(preview/'organization-board.png'))
                    card.locator('.drag-handle').drag_to(target)
                    expect(page.locator('#modal [data-form=transfer]')).to_be_visible()
                    expect(page.locator('#modal [name=group_id]')).to_have_value(groups[0])
                    if os.environ.get('PULSE_SCREENSHOT_DIR'):
                        destination=Path(os.environ['PULSE_SCREENSHOT_DIR']);destination.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(destination/'transfer-after-drag.png'))
                    for modal_width,modal_height in [(1440,760),(1366,700),(1280,650)]:
                        page.set_viewport_size({'width':modal_width,'height':modal_height})
                        page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                        assert page.locator('#modal').evaluate('(el)=>{const r=el.getBoundingClientRect();return r.height<=innerHeight&&r.width<=innerWidth}'),'Transfer modal exceeds viewport'
                        assert page.locator('#modal').evaluate('(el)=>[...el.querySelectorAll("input,select,button")].filter(n=>n.getClientRects().length).every(n=>n.getBoundingClientRect().bottom<=el.getBoundingClientRect().bottom+1)'),'Transfer control is clipped'
                    page.set_viewport_size({'width':1440,'height':780})
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    assert next(n for n in context.request.get(base+'/api/state').json()['people'] if n['id']==tech['id'])['group_id']==groups[1]
                    page.keyboard.press('Escape');expect(page.locator('#modal')).not_to_be_visible()
                    assert next(n for n in context.request.get(base+'/api/state').json()['people'] if n['id']==tech['id'])['group_id']==groups[1]
                    card.locator('.drag-handle').drag_to(target)
                    page.locator('[data-action=transfer-reason]').first.click()
                    page.locator('#modal button[type=submit]').click();expect(page.locator('#modal')).not_to_be_visible()
                    moved=next(n for n in context.request.get(base+'/api/state').json()['people'] if n['id']==tech['id'])
                    assert moved['group_id']==groups[0] and moved['status']=='ACTIVE'
                    card=page.locator('[data-person="'+tech['id']+'"]');card.evaluate('(el)=>PulseLayout.reveal(el)')
                    card.locator('[data-action=person-transfer]').focus();page.keyboard.press('Enter')
                    page.locator('#modal [name=group_id]').select_option(groups[1]);page.locator('[data-action=transfer-reason]').first.click()
                    page.locator('#modal button[type=submit]').click();expect(page.locator('#modal')).not_to_be_visible()
                    assert next(n for n in context.request.get(base+'/api/state').json()['people'] if n['id']==tech['id'])['group_id']==groups[1]
                    timer_context=browser.new_context();timer_api=timer_context.request
                    assert timer_api.post(base+'/api/login',data={'identity':'T2','password':'Password2026!'}).ok
                    running=timer_api.post(base+'/api/timers/start',data={}).json()
                    page.reload();page.locator('.sidebar [data-page=organization]').click()
                    timer_user=next(n for n in context.request.get(base+'/api/state').json()['people'] if n['employee_id']=='T2')
                    timer_card=page.locator('[data-person="'+timer_user['id']+'"]');timer_card.evaluate('(el)=>PulseLayout.reveal(el)')
                    expect(timer_card).to_have_attribute('draggable','false')
                    timer_card.locator('[data-action=person-transfer]').click()
                    expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('#toast')).to_contain_text('Detén el Timer')
                    assert timer_api.post(base+'/api/timers/'+running['id']+'/stop',data={}).ok
                    timer_context.close()
                    checked=[]
                    def bounds(label):
                        issues=page.evaluate('''()=>{
                          const stage=document.querySelector('.viewport-stage');if(!stage)return [];
                          const b=stage.getBoundingClientRect(),issues=[];
                          for(const el of stage.querySelectorAll('button,input,select,textarea,h2,h3,td,.identity')){
                            if(!el.getClientRects().length)continue;const r=el.getBoundingClientRect();
                            if(r.bottom>b.bottom+2||r.right>b.right+2||r.left<b.left-2)issues.push([el.tagName,el.textContent.trim().slice(0,45),Math.round(r.bottom-b.bottom),Math.round(r.right-b.right)]);
                          }
                          return issues;
                        }''')
                        assert not issues,(label,issues[:8])
                        assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth'),label
                    for role,identity,password,routes in [('ADMIN','admin1','admin12026',['dashboard','organization','admins','recoveries','profile']),('MANAGER','M001','Password2026!',['dashboard','team','teamTime','analytics','timeRules','recoveries','profile']),('USER','T1','Password2026!',['dashboard','time','myAnalytics','claim','adp','profile'])]:
                        login(identity,password)
                        for width,height in [(1440,780),(1366,700),(1280,650)]:
                            page.set_viewport_size({'width':width,'height':height});page.goto(base);page.locator('.sidebar').wait_for()
                            for route in routes:
                                target=page.locator('[data-page='+route+']').first;target.evaluate('(el)=>el.closest("details")?.setAttribute("open", "")');target.click()
                                page.wait_for_function('(route)=>document.querySelector(".breadcrumb strong")?.textContent===pageNames[route]',arg=route)
                                if route=='organization':
                                    assert page.locator('.organization-summary').is_visible()
                                    assert page.locator('.account-block').is_visible()
                                    assert not page.locator('[aria-label="Vista de la página"]').is_visible(),'One Account must not require a separate summary screen'
                                if route in ['teamTime','analytics']:
                                    assert page.locator('.workspace-context.filters,.workspace-context.analytics-filters').is_visible()
                                selector=page.locator('[aria-label="Vista de la página"]');count=selector.locator('option').count() if selector.is_visible() else 1
                                for index in range(count):
                                    if selector.is_visible():selector.select_option(str(index))
                                    bounds(f'{role} {route} {width}x{height} section {index}')
                                    # Traverse each visible list's pages, checking that controls never leave the frame.
                                    controls=page.locator('.viewport-pagination:visible select').all()
                                    for control in controls:
                                        for value in range(control.locator('option').count()):
                                            control.select_option(str(value));bounds(f'{role} {route} {width}x{height} list {value}')
                                checked.append(f'{role}:{route}:{width}x{height}')
                    # Complete a long OT form through the actual step controls at native 100%.
                    target=page.locator('[data-page=time]').first;target.click();page.wait_for_function('()=>page==="time" && document.querySelector(".breadcrumb strong")?.textContent==="Mi tiempo"')
                    page.locator('[data-action=ot-new]').evaluate('(el)=>PulseLayout.reveal(el)')
                    page.locator('[data-action=ot-new]').click()
                    values={'scheduled_start':'2026-01-15T20:00','scheduled_end':'2026-01-15T21:00','reference':'INC123456','description':'Descripción completa','justification':'Servicio requerido','impact':'Continuidad','in_lieu':'Sin cobertura'}
                    for _ in range(30):
                        for field in page.locator('#modal input:visible,#modal textarea:visible').all():
                            name=field.get_attribute('name')
                            if name in values:field.fill(values[name])
                        capture=page.locator('#modal [name=capture_type]:visible')
                        if capture.count():capture.select_option('HISTORICAL')
                        geometry=page.locator('#modal').evaluate('(el)=>{const b=el.getBoundingClientRect();return [...el.querySelectorAll("input,select,textarea,button")].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.top>=b.top&&r.bottom<=b.bottom+1&&r.right<=b.right+1})}')
                        assert geometry,'A modal step clips an interactive control'
                        nxt=page.locator('[data-step-next]:visible:not(:disabled)')
                        if not nxt.count():break
                        nxt.click()
                    page.locator('#modal button[type=submit]').click();page.locator('#modal').wait_for(state='hidden')
                    saved=context.request.get(base+'/api/state').json()['overtime']
                    assert any(r['reference']=='INC123456' and r['description']=='Descripción completa' and r['impact']=='Continuidad' for r in saved),'Wizard lost documentation'
                    page.locator('[data-action=ot-new]').click()
                    assert page.locator('.wizard-navigation').inner_text().find('Paso 1 de')>=0,'A new form must start on its first step'
                    page.locator('#modal [data-action=close]').first.click()
                    assert not errors,errors
                    print(json.dumps({'result':'PASS','viewports':len(checked),'javascript_errors':errors,'native_drag_and_drop':'PASS','cancel_and_keyboard_fallback':'PASS','running_timer_drag_block':'PASS'},indent=2));browser.close()
            finally:
                process.terminate();process.wait(timeout=10)
if __name__=='__main__':run()
