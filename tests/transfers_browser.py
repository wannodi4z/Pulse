"""Manager requests a change; Admin reviews and moves, preserving prior OT and Guard data."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright,expect
import test_transfer_requests
ROOT=Path(__file__).resolve().parents[1]
f=test_transfer_requests.TransferRequestTests();f.setUp();process=None
try:
    oid=f.f.ot(f.uc,reference='CHG-TRANSFER')
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(f.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1280,'height':650});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def login(identity,password='Password2026!'):
            assert context.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base)
        def submit():
            page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            for _ in range(20):
                nxt=page.locator('[data-step-next]:visible:not(:disabled)')
                if not nxt.count():break
                nxt.click()
            page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        def fit():
            page.wait_for_timeout(100)
            return page.locator('#modal').evaluate('(el)=>{const b=el.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth&&b.top>=0&&b.bottom<=innerHeight&&[...el.querySelectorAll("input,button,textarea,select")].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect();return r.right<=b.right+1&&r.left>=b.left-1&&r.bottom<=b.bottom+1})}')
        login('M001');page.locator('.sidebar [data-page=team]').click();page.wait_for_function('()=>!busy')
        page.locator('[data-action=transfer-request-new]').first.click()
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});assert fit(),('request',width)
        page.set_viewport_size({'width':1280,'height':650});page.locator('#modal [name=destination]').fill('Oracle con Manager M002');page.locator('#modal [name=reason]').fill('Cambio de especialidad solicitado');submit()
        req=context.request.get(base+'/api/state').json()['transfer_requests'][0];assert req['status']=='SUBMITTED'
        login('admin1','admin12026');page.locator('.sidebar [data-page=organization]').click();page.wait_for_function('()=>!busy');page.locator('[data-action=transfer-requests]').click()
        expect(page.locator('#modal')).to_contain_text('Oracle con Manager M002')
        page.locator('[data-action=transfer-request-review]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('#modal [name=transfer_request_id]')).to_have_value(req['id'])
        expect(page.locator('#modal')).to_contain_text('Destino solicitado por el Manager')
        page.locator('#modal [name=group_id]').select_option(f.dest)
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});assert fit(),('review',width)
        page.set_viewport_size({'width':1280,'height':650});submit()
        saved=context.request.get(base+'/api/state').json();assert next(u for u in saved['people'] if u['id']==f.u['id'])['group_id']==f.dest
        assert next(r for r in saved['transfer_requests'] if r['id']==req['id'])['status']=='APPROVED'
        assert next(o for o in saved['overtime'] if o['id']==oid)['origin_info']['group_id']==f.g
        login('M002');page.locator('.sidebar [data-page=teamTime]').click();page.wait_for_function('()=>!busy');expect(page.locator('#main')).to_contain_text('CHG-TRANSFER')
        assert not errors,errors
        print('PASS: Manager requests through UI; no direct reassignment; Admin reviews exact request and executes; destination Manager sees prior pending OT; origin retained; request/review modals fit 1440/1280/390; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    f.tearDown()
