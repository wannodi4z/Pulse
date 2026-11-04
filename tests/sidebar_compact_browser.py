"""Regression: compact rail has centered icons, no clipped labels or visible scrollbars."""
import os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from test_executive_hierarchy import ExecutiveTests
R=Path(__file__).resolve().parents[1];fixture=ExecutiveTests();fixture.setUp();proc=None
try:
 lead,_,_=fixture.f.person('USER','SIDEBAR-LEAD',group=fixture.g,lead=True);fixture.f.post('/api/delegations',{'lead_id':lead['id']},fixture.mc)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=R,env={**os.environ,'PULSE_DB_PATH':str(fixture.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except Exception:time.sleep(.1)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));checks=0
  for identity,password in [('admin1','admin12026'),('M001','Password2026!'),('T001','Password2026!'),(fixture.dp['username'],'Password2026!'),(fixture.dpe['username'],'Password2026!'),('SIDEBAR-LEAD','Password2026!')]:
   ctx.clear_cookies();assert ctx.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base);page.locator('.sidebar').wait_for();page.wait_for_function('()=>!busy')
   if page.locator('[data-action=sidebar-toggle]').get_attribute('aria-expanded')=='true':page.locator('[data-action=sidebar-toggle]').click()
   for width,height,zoom in [(1440,1000,1),(1440,900,.9),(1024,600,1),(800,420,1)]:
    page.set_viewport_size({'width':width,'height':height});page.evaluate('(z)=>document.body.style.zoom=z',str(zoom));page.locator('.sidebar .nav-item').first.hover()
    expect(page.locator('.sidebar .nav-text').first).not_to_be_visible()
    assert page.locator('.sidebar').evaluate("e=>{const s=getComputedStyle(e.querySelector('nav'));return s.scrollbarWidth==='none'&&getComputedStyle(e.querySelector('nav'),'::-webkit-scrollbar').display==='none'}")
    assert page.locator('.sidebar nav').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
    assert page.locator('.sidebar').evaluate("e=>{const r=e.getBoundingClientRect(),logo=e.querySelector('.brand img').getBoundingClientRect(),toggle=e.querySelector('.sidebar-toggle').getBoundingClientRect();return Math.abs((r.x+r.width/2)-(logo.x+logo.width/2))<2&&Math.abs((r.x+r.width/2)-(toggle.x+toggle.width/2))<2}")
    assert page.locator('.sidebar .nav-item').evaluate_all("es=>es.every(e=>{const a=e.getBoundingClientRect(),b=e.querySelector('.nav-icon').getBoundingClientRect(),s=e.closest('.sidebar').getBoundingClientRect();return Math.abs((a.left+a.width/2)-(b.left+b.width/2))<2&&Math.abs((s.left+s.width/2)-(b.left+b.width/2))<2&&a.left>=s.left&&a.right<=s.right})")
    last=page.locator('.sidebar .nav-item').last;page.locator('.sidebar .nav-item').first.focus();last.focus();expect(last).to_be_in_viewport();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');checks+=1
   page.set_viewport_size({'width':1440,'height':900});page.evaluate("document.body.style.zoom='0.9'");page.locator('.sidebar nav').evaluate('e=>e.scrollTop=0')
   if identity=='admin1':page.evaluate("document.body.style.zoom='1'");page.screenshot(path='/tmp/pulse122-sidebar-fixed.png')
   page.evaluate("document.body.style.zoom='1'");page.reload();page.locator('.sidebar').wait_for();expect(page.locator('[data-action=sidebar-toggle]')).to_have_attribute('aria-expanded','false')
   page.set_viewport_size({'width':390,'height':844});expect(page.locator('.sidebar .nav-text').first).to_be_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   page.set_viewport_size({'width':1440,'height':900});page.locator('[data-action=sidebar-toggle]').focus();page.keyboard.press('Enter');expect(page.locator('[data-action=sidebar-toggle]')).to_have_attribute('aria-expanded','true');expect(page.locator('.sidebar .nav-text').first).to_be_visible()
  assert not errors,errors;browser.close();print(f'PASS: {checks} compact role/viewport/zoom checks; centered icons, hidden labels and scrollbars, keyboard reachability, persistence, mobile labels and expansion; zero JS errors')
finally:
 if proc:proc.terminate();proc.wait(timeout=10)
 fixture.tearDown()
