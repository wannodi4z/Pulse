"""Native-zoom viewport checks against a real server and disposable populated SQLite."""
import json,os,socket,subprocess,sys,tempfile,time,urllib.request
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
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
                    print(json.dumps({'result':'PASS','viewports':len(checked),'javascript_errors':errors},indent=2));browser.close()
            finally:
                process.terminate();process.wait(timeout=10)
if __name__=='__main__':run()
