"""Real Chromium smoke test. Creates an isolated database and local server automatically.
Install requirements-dev.txt and run `python -m playwright install chromium` first.
Optional PULSE_CHROMIUM_EXECUTABLE selects an already installed Chromium binary.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def run():
    with tempfile.TemporaryDirectory() as tmp:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        env = {**os.environ, 'PULSE_DB_PATH': str(Path(tmp)/'browser-test.db')}
        log = open(Path(tmp)/'server.log', 'w+')
        process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=log)
        base = f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(base+'/api/health', timeout=1); break
                except Exception:
                    time.sleep(.1)
            else:
                raise RuntimeError('El servidor de pruebas no inició.')
            with sync_playwright() as p:
                launch = {'headless': True}
                if os.environ.get('PULSE_CHROMIUM_EXECUTABLE'):
                    launch.update(executable_path=os.environ['PULSE_CHROMIUM_EXECUTABLE'], args=['--no-sandbox','--disable-dev-shm-usage'])
                browser = p.chromium.launch(**launch)
                context = browser.new_context(viewport={'width':1440,'height':1000}, accept_downloads=True)
                page = context.new_page(); errors=[];page.on('pageerror',lambda error: errors.append(str(error)))
                page.on('dialog',lambda dialog: dialog.accept())
                page.goto(base)
                def fill(name,value):
                    page.locator('dialog[open] [name='+name+']').fill(value)
                def save():
                    page.locator('dialog[open] button[type=submit]').click()
                def action(name,within=None):
                    selector=f'[data-action="{name}"]'
                    target=within if within is not None else page.locator('dialog[open]') if page.locator('dialog[open] '+selector).count() else page
                    target.locator(selector).first.click()
                def login(username,password='Password2026!'):
                    page.locator('[data-form=login] [name=identity]').fill(username)
                    page.locator('[data-form=login] [name=password]').fill(password)
                    page.locator('[data-form=login] button').click()
                    page.locator('.sidebar').wait_for()
                def activate(username,code):
                    action('activate');fill('identity',username);fill('code',code);fill('password','Password2026!');fill('confirm','Password2026!');save();expect(page.locator('.access-result-body')).to_be_visible();action('access-login');expect(page.locator('#modal')).not_to_be_visible()
                # Access dialogs: layout, feedback, visibility and a real recovery cycle.
                page.locator('[data-form=login]').wait_for()
                action('activate')
                expect(page.locator('#modal [name=identity]')).to_be_focused()
                fill('password','Password2026!');fill('confirm','Different2026!')
                expect(page.locator('[data-password-check=length]')).to_have_class('satisfied')
                expect(page.locator('[data-password-check=match]')).not_to_have_class('satisfied')
                page.locator('[data-action=password-visibility]').first.click()
                expect(page.locator('#access-password')).to_have_attribute('type','text')
                expect(page.locator('[data-action=password-visibility]').first).to_have_attribute('aria-pressed','true')
                page.locator('[data-action=password-visibility]').first.click()
                expect(page.locator('#access-password')).to_have_attribute('type','password')
                for width,height in [(1440,1000),(390,844)]:
                    page.set_viewport_size({'width':width,'height':height})
                    assert page.locator('#modal').evaluate('(el)=>el.scrollWidth<=el.clientWidth'),'Access dialog horizontal overflow'
                    assert page.locator('#modal').evaluate('(el)=>el.getBoundingClientRect().height<=innerHeight'),'Access dialog vertical overflow'
                page.set_viewport_size({'width':1440,'height':1000})
                if os.environ.get('PULSE_SCREENSHOT_DIR'):
                    dest=Path(os.environ['PULSE_SCREENSHOT_DIR']);dest.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest/'activate-v1.1.0.png'))
                page.keyboard.press('Escape');expect(page.locator('#modal')).not_to_be_visible()
                action('recovery-request');fill('identity','admin2')
                if os.environ.get('PULSE_SCREENSHOT_DIR'):page.screenshot(path=str(Path(os.environ['PULSE_SCREENSHOT_DIR'])/'recovery-v1.1.0.png'))
                save();expect(page.locator('.access-result-body')).to_contain_text('Si tu cuenta está activa')
                expect(page.locator('#modal h2')).to_have_text('Solicitud recibida')
                action('recovery-complete');expect(page.locator('#modal [name=identity]')).to_have_value('admin2')
                action('recovery-request');expect(page.locator('#modal [name=identity]')).to_have_value('admin2')
                action('close')
                # Branding and credits work before and after authentication.
                action('about');expect(page.locator('.about-project')).to_contain_text('Francisco Cervantes Marquez')
                expect(page.locator('.about-project')).to_contain_text('Versión 1.1.0')
                expect(page.locator('.author-list')).to_contain_text('Samuel Alejandro Díaz Chávez')
                expect(page.locator('.author-list article')).to_have_count(2)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Credit dialog overflow on mobile'
                assert page.locator('#modal').evaluate('(el)=>el.getBoundingClientRect().right<=innerWidth')
                page.set_viewport_size({'width':1440,'height':1000})
                assert page.locator('.about-project img.kyndryl-logo').evaluate('(img)=>img.complete&&img.naturalWidth>0')
                action('close')
                login('admin1','admin12026')
                expect(page.locator('.workspace-tag')).to_contain_text('v1.1.0')
                action('about');expect(page.locator('.author-list')).to_contain_text('Francisco Cervantes Marquez');action('close')
                page.locator('.sidebar [data-page=recoveries]').click();action('recovery-issue')
                expect(page.locator('.secret-code')).to_be_visible();recovery_code=page.locator('.secret-code').inner_text();action('close');action('logout')
                action('recovery-request');fill('identity','admin2');action('recovery-complete')
                fill('code','REC-INVALID');fill('password','Recovered2026!');fill('confirm','Mismatch2026!');save()
                expect(page.locator('#access-error')).to_contain_text('Las contraseñas no coinciden')
                expect(page.locator('#access-error')).to_be_focused()
                fill('confirm','Recovered2026!');save();expect(page.locator('#access-error')).to_contain_text('Código inválido o vencido')
                expect(page.locator('#modal [name=identity]')).to_have_value('admin2')
                fill('code',recovery_code);save();expect(page.locator('#modal h2')).to_have_text('Contraseña actualizada')
                action('access-login');expect(page.locator('[data-form=login] [name=identity]')).to_have_value('admin2')
                login('admin2','Recovered2026!');action('logout');login('admin1','admin12026')
                page.locator('.sidebar [data-page=organization]').click()
                expect(page.locator('h1')).to_have_text('Organización')
                action('account-new');fill('code','MX');fill('name','Operación México');save();expect(page.locator('.account-block')).to_have_count(1)
                account_id=page.locator('.account-block').get_attribute('data-account')
                for code in ['G1','G2','G3']:
                    action('group-new');fill('code',code);fill('name','Grupo '+code);save();expect(page.locator('.group-card')).to_have_count(int(code[-1]))
                gids=page.locator('.group-card').evaluate_all('(nodes)=>nodes.map(n=>n.dataset.group)')
                action('manager-new')
                for name,value in [('first','María'),('last','Responsable'),('employee_id','M001'),('email','manager@example.test')]:fill(name,value)
                page.locator('[name=group_ids]').nth(0).check();page.locator('[name=group_ids]').nth(1).check();save();expect(page.locator('.secret-code')).to_be_visible();manager_code=page.locator('.secret-code').inner_text();action('close')
                expect(page.locator('.manager-block')).to_have_count(1)
                expect(page.locator('.manager-block .group-card')).to_have_count(2)
                expect(page.locator('.manager-meta')).to_contain_text('Multigrupo · 2 grupos')
                expect(page.locator('.unassigned .group-card')).to_have_count(1)
                action('manager-new')
                for name,value in [('first','José'),('last','Segundo'),('employee_id','M002'),('email','manager2@example.test')]:fill(name,value)
                expect(page.locator('[name=group_ids]')).to_have_count(1);page.locator('[name=group_ids]').check();save();expect(page.locator('.secret-code')).to_be_visible();action('close')
                expect(page.locator('.manager-block')).to_have_count(2)
                codes={}
                for emp,lead,gid in [('T001',False,gids[0]),('L001',True,gids[0]),('T002',False,gids[0]),('L002',True,gids[1])]:
                    action('tech-new',page.locator('[data-group="'+gid+'"]'))
                    for name,value in [('first','Persona'),('last',emp),('employee_id',emp),('email',emp+'@example.test')]:fill(name,value)
                    if lead:page.locator('[name=is_lead]').check()
                    if emp=='T002':
                        expect(page.locator('#lead-option')).not_to_be_visible();expect(page.locator('#lead-note')).to_contain_text('L001')
                    save();expect(page.locator('.secret-code')).to_be_visible();codes[emp]=page.locator('.secret-code').inner_text();action('close')
                expect(page.locator('[data-group="'+gids[0]+'"] .technician')).to_have_count(3)
                leadrow=page.locator('.technician').filter(has_text='L001');action('person-edit',leadrow)
                expect(page.locator('[name=is_lead]')).to_be_checked();action('close')
                # Navigation stays on the selected page after sync and can return to Organization.
                for target,title in [('dashboard','Todo empieza con tu equipo.'),('admins','Administradores'),('recoveries','Recuperación de acceso'),('profile','Mi perfil')]:
                    page.locator('.sidebar [data-page='+target+']').click();expect(page.locator('h1')).to_have_text(title)
                    page.wait_for_timeout(150)
                    expect(page.locator('.account-block')).to_have_count(0)
                    page.locator('.sidebar [data-page=organization]').click();expect(page.locator('h1')).to_have_text('Organización')
                page.wait_for_timeout(5200);expect(page.locator('h1')).to_have_text('Organización');assert not page.url.endswith('#organization')
                # Account with groups cannot be removed.
                action('account-delete');expect(page.locator('#toast')).to_contain_text('contiene Grupos');expect(page.locator('.account-block')).to_have_count(1)
                # Desktop and mobile layout must not overflow the viewport.
                for width,height in [(1440,1000),(390,844)]:
                    page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'Horizontal overflow at {width}'
                page.set_viewport_size({'width':1440,'height':1000})
                screenshot=os.environ.get('PULSE_SCREENSHOT_DIR')
                if screenshot:
                    Path(screenshot).mkdir(parents=True,exist_ok=True);page.screenshot(path=str(Path(screenshot)/'organization.png'),full_page=True)
                action('logout');activate('L001',codes['L001']);activate('L002',codes['L002']);activate('T001',codes['T001']);activate('M001',manager_code);login('M001')
                page.locator('.sidebar [data-page=team]').click();expect(page.locator('h1')).to_have_text('Mi equipo')
                search=page.locator('#team-search');search.fill('T001');expect(page.locator('tbody tr:visible')).to_have_count(1);assert search.evaluate('(el)=>el===document.activeElement');search.fill('')
                # Delegate inline from a person's row; replacing/revoking preserves Lead capability.
                for employee in ['L001','L002']:
                    row=page.locator('tbody tr').filter(has_text=employee)
                    action('delegation-inline',row);expect(page.locator('#modal')).not_to_be_visible()
                    expect(page.locator('#delegation-editor')).to_contain_text(employee)
                    if employee=='L002':expect(page.locator('#delegation-editor')).to_contain_text('sustituirá')
                    if screenshot and employee=='L001':page.screenshot(path=str(Path(screenshot)/'inline-delegation-v1.1.0.png'),full_page=True)
                    page.locator('#delegation-editor button[type=submit]').click()
                    expect(page.locator('#delegation-editor')).to_have_count(0)
                    expect(page.locator('.delegation-summary')).to_contain_text(employee)
                delegated=page.request.get(base+'/api/state').json()
                assert len([d for d in delegated['delegations'] if not d['revoked_at']])==1
                assert all(p['is_lead'] for p in delegated['people'] if p['employee_id'] in ['L001','L002'])
                action('delegation-revoke');expect(page.locator('.delegation-summary')).to_contain_text('Sin delegación asignada')
                # Capture the requested 13-interval week, including overnight and full Sunday.
                page.locator('.sidebar [data-page=timeRules]').click();action('rule-new');fill('name','Guardia semanal');fill('effective_from','2026-01-01')
                for day in range(6):
                    section=page.locator('[data-rule-day="'+str(day)+'"]')
                    section.locator('[name=days]').check()
                    section.locator('[data-start]').first.fill('02:00' if day<5 else '00:00')
                    section.locator('[data-end]').first.fill('04:00' if day<5 else '08:00')
                    action('rule-add',section)
                    section.locator('[data-start]').nth(1).fill('20:00' if day<5 else '15:00')
                    section.locator('[data-end]').nth(1).fill('00:00')
                monday=page.locator('[data-rule-day="0"]');action('rule-add',monday)
                expect(monday.locator('[data-rule-segment]')).to_have_count(3)
                monday.locator('[data-action=rule-remove]').last.click();expect(monday.locator('[data-rule-segment]')).to_have_count(2)
                sunday=page.locator('[data-rule-day="6"]');sunday.locator('[name=days]').check();sunday.locator('[data-full-day]').check()
                expect(sunday.locator('.rule-full-note')).to_be_visible()
                page.set_viewport_size({'width':390,'height':844});assert page.locator('#modal').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
                page.set_viewport_size({'width':1440,'height':1000})
                if screenshot:page.locator('#modal').evaluate('(el)=>el.scrollTop=0');page.screenshot(path=str(Path(screenshot)/'weekly-intervals-v1.1.0.png'))
                save();expect(page.locator('.rules-grid')).to_contain_text('24 horas')
                assert len(page.request.get(base+'/api/state').json()['rules'][0]['segments'])==13
                # Independent technician session provides a real active event for Manager drilldowns.
                tech_context=browser.new_context();tc=tech_context.request
                assert tc.post(base+'/api/login',data={'identity':'T001','password':'Password2026!'}).status==200
                timer=tc.post(base+'/api/timers/start',data={}).json()['id']
                pending=tc.post(base+'/api/overtime',data={'capture_type':'HISTORICAL','scheduled_start':'2025-12-01T02:00:00-06:00','scheduled_end':'2025-12-01T04:00:00-06:00','reference':'INC-CARD','description':'Actividad desde tarjeta','justification':'Servicio','impact':'Cobertura','in_lieu':'No aplica'})
                assert pending.status==200
                page.reload();page.locator('[data-action=dashboard-drill][data-id=running]').wait_for()
                page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change')
                page.locator('[data-action=dashboard-drill][data-id=running]').click()
                expect(page.locator('[name=filter-status]')).to_have_value('RUNNING')
                expect(page.locator('[name=filter-period]')).to_have_value('ALL')
                expect(page.locator('tbody tr')).to_have_count(1);expect(page.locator('.timer-card')).to_have_count(1)
                action('timer-open');expect(page.locator('#modal')).to_contain_text('T001');expect(page.locator('#modal .badge')).to_contain_text('En curso');action('close')
                page.locator('.sidebar [data-page=dashboard]').click()
                expect(page.locator('.priority-list')).to_contain_text('INC-CARD')
                page.locator('[data-action=dashboard-drill][data-id=pending]').click()
                expect(page.locator('[name=filter-period]')).to_have_value('ALL');expect(page.locator('tbody tr')).to_have_count(1)
                action('record-detail');action('approve');expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('tbody tr')).to_have_count(0)
                assert tc.post(base+'/api/timers/'+timer+'/stop',data={}).status==200
                tech_context.close()
                action('logout');login('T001')
                page.locator('.sidebar [data-page=time]').click();expect(page.locator('h1')).to_have_text('Mi tiempo')
                action('ot-new');page.locator('[name=capture_type]').select_option('HISTORICAL')
                for name,value in [('scheduled_start','2026-01-05T23:00'),('scheduled_end','2026-01-06T01:00'),('reference','CHG12345'),('description','Cambio de prueba'),('justification','Mantenimiento'),('impact','Disponibilidad'),('in_lieu','Ventana de servicio')]:fill(name,value)
                save();expect(page.locator('#modal')).not_to_be_visible()
                page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');expect(page.locator('.record-list').first).to_contain_text('CHG12345')
                action('guard-new');fill('start_date','2026-01-05');fill('end_date','2026-01-05');save();expect(page.locator('#modal')).not_to_be_visible()
                action('timer-start');expect(page.locator('.timer-card')).to_have_count(1);page.wait_for_timeout(1100);action('timer-stop');expect(page.locator('.timer-card')).to_have_count(0)
                action('logout');login('M001');page.locator('.sidebar [data-page=teamTime]').click()
                page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change');expect(page.locator('tbody tr')).to_have_count(2)
                action('approve');expect(page.locator('[data-action=approve]')).to_have_count(1);action('approve');expect(page.locator('[data-action=approve]')).to_have_count(0)
                with page.expect_download() as download_info:page.locator('a[download]').click()
                download=download_info.value;path=Path(tmp)/'export.xlsx';download.save_as(path);assert path.stat().st_size>1000
                action('logout');login('T001')
                for target in ['claim','adp']:
                    page.locator('.sidebar [data-page='+target+']').click();expect(page.locator('h1')).to_have_text(target.upper() if target=='adp' else 'Claim');expect(page.locator('tbody tr')).to_have_count(4)
                action('logout');login('L001')
                expect(page.locator('.sidebar [data-page=time]')).to_have_count(1);expect(page.locator('.sidebar [data-page=teamTime]')).to_have_count(0)
                page.locator('.sidebar [data-page=time]').click();expect(page.locator('h1')).to_have_text('Mi tiempo')
                assert errors==[],errors
                print(json.dumps({'result':'PASS','browser':'Chromium','checks':['Kyndryl brand and credits before/after login','version 1.1.0','access dialogs: mobile/focus/visibility/validation/success','real password recovery through UI','initial login','account/groups/two managers','physical nesting','multigroup label','technicians and Lead selector','activation Manager/Technician/Lead','sidebar exit and polling','responsive desktop/mobile','search focus','13 weekly intervals and full Sunday','inline single backup replacement/revocation','dashboard running/pending drilldowns and detail approvals','rule and guard request','historical OT','emergency timer start/stop','manager approvals','download Excel','Claim/ADP rows','Lead has no implicit approval authority'],'javascript_errors':errors},ensure_ascii=False,indent=2))
                browser.close()
        except Exception:
            log.flush();log.seek(0);print(log.read()[-7000:]);raise
        finally:
            process.terminate()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            log.close()


if __name__=='__main__':run()
