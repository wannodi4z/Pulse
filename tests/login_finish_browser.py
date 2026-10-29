"""Login visual finish preserves activation/recovery, keyboard, errors and real sign-in."""
import os,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as d:
 db=Path(d)/'login.db';shutil.copy(root/'fixtures/banorte_pruebas.sqlite3',db)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=root,env={**os.environ,'PULSE_DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:urllib.request.urlopen(base+'/api/health',timeout=1);break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
   for width,height in [(1440,900),(1024,600),(800,540),(390,844),(320,568)]:
    page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
    expect(page.locator('[data-form=login]')).to_be_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    for selector in ['[data-form=login] [type=submit]','[data-action=activate]','[data-action=recovery-request]','[data-action=about]']:
     node=page.locator(selector);node.scroll_into_view_if_needed();expect(node).to_be_in_viewport()
    page.locator('[name=identity]').scroll_into_view_if_needed()
    if width in (1440,390):page.screenshot(path=f'/tmp/pulse-login-refined-{width}.png',full_page=True)
   page.set_viewport_size({'width':1440,'height':900});page.locator('[name=identity]').fill('951357');page.locator('#login-password').fill('not-the-password')
   page.locator('[data-action=password-visibility]').click();expect(page.locator('#login-password')).to_have_attribute('type','text');page.locator('[data-action=password-visibility]').click();expect(page.locator('#login-password')).to_have_attribute('type','password')
   page.locator('[data-form=login] [type=submit]').click();page.wait_for_function('()=>!busy');expect(page.locator('[data-form=login] .form-error')).not_to_be_empty();expect(page.locator('[data-form=login] .form-error')).to_be_focused()
   for action in ['activate','recovery-request']:
    page.locator('[data-action='+action+']').click();expect(page.locator('#modal')).to_be_visible();page.locator('#modal [data-action=close]').first.click()
   page.locator('#login-password').fill('tecnico12026');page.locator('[data-form=login] [type=submit]').click();expect(page.locator('.sidebar')).to_be_visible();assert not errors,errors
   b.close();print('PASS: refined login in five viewport sizes, no horizontal overflow, all actions reachable, password visibility, focused authentication error, activation and recovery dialogs, successful demo Technician login; no JS errors')
 finally:proc.terminate();proc.wait(timeout=10)
