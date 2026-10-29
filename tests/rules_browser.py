"""Regression: multiple guard intervals survive create, edit, deletion, pagination and reload."""
import sys,os,socket,subprocess,time,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_api import PulseTests
from playwright.sync_api import sync_playwright
x=PulseTests();x.setUp();x.organization()
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
base=f'http://127.0.0.1:{port}'
proc=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=Path(__file__).resolve().parents[1],env={**os.environ,'PULSE_DB_PATH':str(x.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(100):
  try:urllib.request.urlopen(base+'/api/health');break
  except:time.sleep(.1)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox']);page=b.new_page(viewport={'width':1280,'height':650});page.goto(base)
  page.locator('[name=identity]').fill('M001');page.locator('[name=password]').fill('Password2026!');page.locator('[type=submit]').click();page.locator('.sidebar').wait_for()
  page.evaluate("navigate('timeRules')");page.locator('[data-action=rule-new]').click()
  page.locator('[name=name]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[name=name]').fill('Multiple')
  page.locator('[data-rule-day="0"] [name=days]').evaluate('(el)=>PulseLayout.reveal(el)');page.locator('[data-rule-day="0"] [name=days]').check()
  day=page.locator('[data-rule-day="0"]');day.locator('[data-start]').fill('02:00');day.locator('[data-end]').fill('04:00')
  for i in range(4):
   day.locator('[data-action=rule-add]').click();day.locator('[data-start]').last.fill(f'{i+5:02}:00');day.locator('[data-end]').last.fill(f'{i+6:02}:00')
  # Screenshots are optional; no real user data is used.
  def save():
   while page.locator('.wizard-navigation [data-step-next]:not([disabled])').count():
    page.locator('.wizard-navigation [data-step-next]').click()
   with page.expect_response(lambda r:'/api/rules' in r.url and r.request.method in ('POST','PUT')) as response:
    page.locator('#modal [type=submit]').click()
   assert response.value.ok,response.value.text()
   page.locator('#modal').wait_for(state='hidden')
  save()
  expected=[{'day':0,'start':'02:00','end':'04:00'}]+[{'day':0,'start':f'{i+5:02}:00','end':f'{i+6:02}:00'} for i in range(4)]
  assert page.request.get(base+'/api/state').json()['rules'][0]['segments']==expected
  page.reload();page.locator('.sidebar').wait_for();page.evaluate("navigate('timeRules')");page.locator('[data-action=rule-edit]').click()
  day=page.locator('[data-rule-day="0"]')
  for i,segment in enumerate(expected):
   row=day.locator('[data-rule-segment]').nth(i)
   row.evaluate('(el)=>PulseLayout.reveal(el)')
   assert row.locator('[data-start]').input_value()==segment['start']
   assert row.locator('[data-end]').input_value()==segment['end']
  row=day.locator('[data-rule-segment]').nth(2);row.evaluate('(el)=>PulseLayout.reveal(el)');row.locator('[data-start]').fill('06:15');expected[2]['start']='06:15'
  day.locator('[data-action=rule-add]').evaluate('(el)=>PulseLayout.reveal(el)');day.locator('[data-action=rule-add]').click()
  day.locator('[data-start]').last.fill('20:00');day.locator('[data-end]').last.fill('00:00');expected.append({'day':0,'start':'20:00','end':'00:00'})
  row=day.locator('[data-rule-segment]').nth(1);row.evaluate('(el)=>PulseLayout.reveal(el)');row.locator('[data-action=rule-remove]').click();expected.pop(1)
  save()
  page.reload();page.locator('.sidebar').wait_for();page.evaluate("navigate('timeRules')");page.locator('[data-action=rule-edit]').click()
  assert page.request.get(base+'/api/state').json()['rules'][0]['segments']==expected
  day=page.locator('[data-rule-day="0"]')
  for i,segment in enumerate(expected):
   row=day.locator('[data-rule-segment]').nth(i);row.evaluate('(el)=>PulseLayout.reveal(el)')
   assert row.locator('[data-start]').input_value()==segment['start']
   assert row.locator('[data-end]').input_value()==segment['end']
  assert page.locator('#modal .dialog-footer').evaluate('(el)=>el.getBoundingClientRect().bottom<=innerHeight')
  print('PASS: 5 intervals saved; reload/edit/add/remove/resave/reopen preserve exact values at 1280x650')
  b.close()
finally:proc.terminate();proc.wait();x.tearDown()
