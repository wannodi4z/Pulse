"""Search, records and metrics remain one workspace; comparisons use identical filters."""
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright, expect
import test_analytics_workspace

ROOT=Path(__file__).resolve().parents[1]
fixture=test_analytics_workspace.AnalyticsWorkspaceTests();fixture.setUp();process=None
try:
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    process=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--port',str(port)],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(fixture.f.server.DB)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:urllib.request.urlopen(base+'/api/health',timeout=1);break
        except Exception:time.sleep(.1)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('PULSE_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1280,'height':650},accept_downloads=True)
        assert context.request.post(base+'/api/login',data={'identity':'M001','password':'Password2026!'}).ok
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base);page.locator('.sidebar [data-page=analytics]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('.team-view-tabs')).to_have_count(0)
        search=page.locator('#analytics-search');search.fill('CHG-ALPHA')
        expect(page.locator('#analytics-records tbody tr')).to_have_count(3)
        expect(page.locator('.metric-all strong')).to_contain_text('5')
        expect(page.locator('[name=filter-period]')).to_have_value('ALL')
        assert search.evaluate('(el)=>el===document.activeElement')
        expect(search).to_have_value('CHG-ALPHA')
        page.locator('[name=filter-status]').select_option('SUBMITTED');page.wait_for_function('()=>!busy')
        expect(page.locator('#analytics-records tbody tr')).to_have_count(1)
        expect(page.locator('.metric-all strong')).to_have_text('0 h')
        page.locator('[name=filter-status]').select_option('');page.wait_for_function('()=>!busy')
        page.locator('#month').fill('2026-01');page.locator('#month').dispatch_event('change')
        expect(page.locator('#analytics-records tbody tr')).to_have_count(1)
        expect(page.locator('.metric-all strong')).to_have_text('2 h')
        page.locator('[data-action=analytics-months]').click()
        for month in ['2026-02','2026-03']:
            page.locator('#modal [name=compare_month]').fill(month);page.locator('#modal [data-action=comparison-add]').click();page.wait_for_function('()=>!busy')
        page.locator('#modal [type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();page.wait_for_function('()=>!busy')
        expect(page.locator('#analytics-records tbody tr')).to_have_count(3);expect(page.locator('.metric-all strong')).to_have_text('5 h')
        if os.environ.get('PULSE_SCREENSHOT_DIR'):
            dest=Path(os.environ['PULSE_SCREENSHOT_DIR']);dest.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest/'unified-analytics-v1.1.0.png'))
        for width,height in [(1440,780),(1280,650),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight')
            expect(page.locator('.analytics-dashboard')).to_contain_text('Comparativa por mes')
            expect(page.locator('.hourly-slot')).to_have_count(24)
            assert page.locator('.analytics-dashboard').evaluate('(el)=>el.getBoundingClientRect().right<=innerWidth+1')
        page.set_viewport_size({'width':1280,'height':650})
        with page.expect_download() as download:page.locator('a[download]').click()
        target=Path(fixture.f.temp.name)/'analytics.xlsx';download.value.save_as(target)
        wb=load_workbook(target)
        assert len(list(wb['Registros'].values))-1==3
        assert [r[-1] for r in list(wb['Comparativa'].values)[1:]]==[2,3,0]
        # Read-only consultation and a direct route to the pending decision.
        pending=page.locator('#analytics-records tbody tr').filter(has_text='Pendiente')
        pending.evaluate('(el)=>PulseLayout.reveal(el)');pending.locator('[data-action=record-detail]').click()
        expect(page.locator('#modal [data-action=approve]')).to_have_count(0)
        page.locator('#modal [data-action=close]').first.click()
        page.locator('.sidebar [data-page=teamTime]').click();page.wait_for_function('()=>!busy')
        expect(page.locator('tbody tr')).to_have_count(1)
        expect(page.locator('[name=filter-status],[name=filter-period],a[download],.timer-card')).to_have_count(0)
        expect(page.locator('tbody tr .badge')).to_have_text('Pendiente')
        assert not errors,errors
        print('PASS: one workspace; global reference search updates records/totals without losing focus; pending hours excluded; 3-month comparison and matching Excel; read-only analysis; pending-only approvals; 1440/1280/390 viewports; zero JS errors')
        browser.close()
finally:
    if process:process.terminate();process.wait(timeout=10)
    fixture.tearDown()
