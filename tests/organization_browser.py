"""Browser regression for direct Group lookup and compact structure dialogs.
All fixtures live in a disposable SQLite file, never the local working database.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect
from test_api import PulseTests

ROOT = Path(__file__).resolve().parents[1]
fixture = PulseTests()
fixture.setUp()
process = None
try:
    account, first_group, manager, _, _, _ = fixture.organization()
    for i in range(2, 21):
        fixture.group(account, f'GROUP-{i:02}', manager['id'])
    other_account = fixture.post('/api/accounts',{'code':'OTHER','name':'Otra cuenta','country_code':'MX'})['id']
    other_groups = [fixture.group(other_account, f'OTHER-{i}') for i in range(5)]
    other_manager, _, _ = fixture.person('MANAGER', 'M002', account=other_account, groups=other_groups)
    accent = fixture.post('/api/groups', {'account_id':other_account, 'manager_id':other_manager['id'], 'code':'ANALISIS', 'name':'Infraestructura de Análisis'})['id']
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'server:app', '--port', str(port)], cwd=ROOT, env={**os.environ, 'PULSE_DB_PATH':str(fixture.server.DB)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(base+'/api/health', timeout=1)
            break
        except Exception:
            time.sleep(.1)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE', '/usr/bin/chromium'), args=['--no-sandbox'])
        context = browser.new_context()
        assert context.request.post(base+'/api/login', data={'identity':'admin1', 'password':'admin12026'}).ok
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        def screenshot(name):
            if os.environ.get('PULSE_SCREENSHOT_DIR'):
                folder=Path(os.environ['PULSE_SCREENSHOT_DIR']);folder.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(folder/name))
        def modal_bounds():
            assert page.locator('#modal').evaluate('''el=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight&&[...el.querySelectorAll('input,select,button')].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.left>=b.left&&r.right<=b.right+1&&r.bottom<=b.bottom+1})}''')
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height})
            page.goto(base);page.locator('.sidebar [data-page=organization]').click()
            search=page.locator('#organization-search')
            search.fill('GROUP-20')
            expect(page.locator('#group-search-results [role=option]')).to_have_count(1)
            assert search.evaluate('(el)=>el===document.activeElement')
            search.press('ArrowDown');search.press('Enter')
            last=page.locator('[data-group]').filter(has_text='GROUP-20').first
            expect(last).to_be_visible();assert last.evaluate('(el)=>el.closest("[data-manager]").dataset.manager')==manager['id']
            search.fill('analisis')
            expect(page.locator('#group-search-results [role=option]')).to_have_count(1)
            popup=page.locator('#group-search-results')
            assert popup.evaluate('(el)=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.bottom<=innerHeight}')
            if width==1440:screenshot('group-search-v1.0.4.png')
            popup.locator('[role=option]').click()
            expect(page.locator('[data-group="'+accent+'"]')).to_be_visible()
            assert page.locator('[data-account="'+other_account+'"]:visible').count()==1
            search.fill('not-a-real-group')
            expect(popup).to_contain_text('No hay Grupos')
            search.press('Escape');expect(popup).to_have_count(0)
            search.fill('M001')
            assert 1<=popup.locator('[role=option]').count()<=5
            expect(popup).to_contain_text('Precisa la búsqueda')
            search.press('Escape');search.fill('')
            page.locator('[data-action=account-new]').click()
            expect(page.locator('#modal')).to_have_class('entity-dialog account-dialog')
            assert page.locator('#modal').evaluate('(el)=>el.getBoundingClientRect().width<=620')
            modal_bounds()
            if width==1440:screenshot('account-dialog-v1.0.4.png')
            page.locator('#modal [data-action=close]').first.click()
            page.locator('[data-account="'+other_account+'"] [data-action=group-new]').click()
            expect(page.locator('#modal [name=account_id]')).to_have_value(other_account)
            modal_bounds()
            if width==1440:screenshot('group-dialog-v1.0.4.png')
            page.locator('#modal [data-action=close]').first.click()
        # The direct locator also finds a Group created from the redesigned dialog.
        page.set_viewport_size({'width':1280,'height':650})
        page.locator('[data-account="'+other_account+'"] [data-action=group-new]').click()
        page.locator('#modal [name=service_key]').fill('CREATED-UI')
        page.locator('#modal [name=name]').fill('Grupo creado en interfaz')
        page.locator('#modal [name=manager_id]').select_option(other_manager['id'])
        page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        page.locator('#organization-search').fill('CREATED-UI');page.locator('#organization-search').press('Enter')
        expect(page.locator('.group-located')).to_contain_text('Grupo creado en interfaz')
        assert not errors,errors
        print('PASS: 26 seeded Groups; lookup by code, accent-insensitive name and Manager; keyboard/mouse navigation across Accounts; no-results/Escape; compact dialogs and creation at 1440/1280/390; zero JS errors')
        browser.close()
finally:
    if process:
        process.terminate();process.wait(timeout=10)
    fixture.tearDown()
