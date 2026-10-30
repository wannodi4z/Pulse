"""Four-role interface review: responsive content, calendar reachability and keyboard access."""
import os,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as d:
 db=Path(d)/'review.db';shutil.copy(root/'fixtures/banorte_pruebas.sqlite3',db)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}';proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=root,env={**os.environ,'PULSE_DB_PATH':str(db)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   try:urllib.request.urlopen(base+'/api/health',timeout=1);break
   except Exception:time.sleep(.1)
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);checks=0;errors=[]
   roles=[('admin1','admin12026',['dashboard','organization','admins','recoveries']),('MGR0001','manager12026',['dashboard','team','teamTime','analytics','records','timeRules','recoveries']),('SL0001','lead120261',['dashboard','time','myAnalytics','myRecords','claim','adp']),('951357','tecnico12026',['dashboard','time','myAnalytics','myRecords','claim','adp'])]
   for identity,password,pages in roles:
    context=browser.new_context();page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));assert context.request.post(base+'/api/login',data={'identity':identity,'password':password}).ok;page.goto(base);page.locator('.sidebar').wait_for()
    for width,height in [(1440,900),(1024,600),(800,540),(390,844)]:
     page.set_viewport_size({'width':width,'height':height})
     for view in pages:
      page.evaluate('(v)=>navigate(v)',view);page.wait_for_function('()=>!busy');page.wait_for_timeout(40)
      assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(identity,view,width)
      expect(page.locator('h1')).to_be_visible();expect(page.locator('.sidebar [aria-current=page]')).to_have_count(1)
      if width==390:
       assert page.locator('.sidebar [aria-current=page]').evaluate('el=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1}'),(identity,view,'active tab hidden')
      checks+=1
    # Calendar stays seven columns wide and every date can be reached by normal scrolling.
    if identity in ('SL0001','951357'):
     page.set_viewport_size({'width':390,'height':844});page.evaluate("navigate('time')");page.wait_for_function('()=>!busy');page.locator('#month').fill('2026-05');page.locator('#month').dispatch_event('change');page.wait_for_function('()=>!busy')
     expect(page.locator('#main [data-calendar-date]')).to_have_count(42)
     assert page.locator('#main .calendar-date-button').evaluate_all('els=>els.every(el=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1})')
     last=page.locator('#main [data-calendar-date="2026-05-31"] .calendar-date-button');last.scroll_into_view_if_needed();expect(last).to_be_in_viewport()
     expect(page.locator('#main>.workspace-totals')).to_be_visible()
     assert page.locator('#main').evaluate('el=>el.scrollHeight>el.clientHeight')
     page.screenshot(path='/tmp/pulse109-mobile-calendar.png')
    page.set_viewport_size({'width':1440,'height':900});page.locator('.skip-link').focus();page.keyboard.press('Enter');expect(page.locator('#main')).to_be_focused()
    context.close()
   assert not errors,errors
   browser.close();print(f'PASS: {checks} role/page/viewport checks; no horizontal page overflow; active mobile navigation visible; six-week calendars fit seven columns with final dates reachable; totals retained; keyboard skip link; no JS errors')
 finally:proc.terminate();proc.wait(timeout=10)
