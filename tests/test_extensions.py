"""Functional extension workflow, exact pause boundaries and gap-free accounting."""
import io
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from openpyxl import load_workbook
import test_api


class ExtensionTests(unittest.TestCase):
    def setUp(self):
        self.fx=test_api.PulseTests();self.fx.setUp();self.server=self.fx.server
        self.account,self.group,self.manager,self.mc,self.user,self.tc=self.fx.organization()

    def tearDown(self):
        self.fx.tearDown()

    def paused(self):
        current=datetime.now(timezone.utc)
        ot=self.fx.ot(self.tc,(current+timedelta(days=1)).isoformat(),(current+timedelta(days=1,hours=1)).isoformat())
        self.fx.approve(self.mc,'ot',ot)
        timer=self.server.uid()
        with self.server.connection(True) as c:
            c.execute("UPDATE overtime SET scheduled_start='2026-01-06T05:00:00+00:00',scheduled_end='2026-01-06T06:00:00+00:00',start_at='2026-01-06T05:00:00+00:00',execution='RUNNING' WHERE id=?",(ot,))
            c.execute('INSERT INTO timers VALUES(?,?,?,?,NULL)',(timer,self.user['id'],ot,'2026-01-06T05:00:00+00:00'))
        return ot,timer

    def test_pause_extend_resume_excludes_waiting_and_preserves_guard_excel(self):
        ot,timer=self.paused()
        with patch.object(self.server,'now',return_value='2026-01-06T06:30:00+00:00'):
            state=self.tc.get('/api/state').json()
            self.assertFalse(state['timers']);self.assertEqual(state['overtime'][0]['execution'],'PAUSED')
            self.assertEqual(state['timer_segments'][0]['end_at'],'2026-01-06T06:00:00+00:00')
            self.assertEqual(state['overtime'][0]['worked_seconds'],3600)
            self.assertEqual(self.tc.post('/api/timers/start',json={'overtime_id':ot}).status_code,422)
            ext=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T08:00:00+00:00','reason':'Cambio requiere trabajo adicional'},self.tc)['id']
            self.assertEqual(self.tc.post(f'/api/overtime/{ot}/extensions',json={'requested_end':'2026-01-06T09:00:00+00:00','reason':'Duplicada'}).status_code,409)
            self.assertEqual(self.tc.post(f'/api/extensions/{ext}/decision',json={'decision':'APPROVED'}).status_code,403)
        with patch.object(self.server,'now',return_value='2026-01-06T06:45:00+00:00'):
            self.fx.post(f'/api/extensions/{ext}/decision',{'decision':'APPROVED'},self.mc)
            state=self.tc.get('/api/state').json();self.assertFalse(state['timers']);self.assertEqual(state['overtime'][0]['execution'],'PAUSED')
        with patch.object(self.server,'now',return_value='2026-01-06T07:00:00+00:00'):
            resumed=self.fx.post('/api/timers/start',{'overtime_id':ot},self.tc)['id']
            manager_state=self.mc.get('/api/state').json()
            self.assertEqual(manager_state['timers'][0]['user_id'],self.user['id'])
            self.assertEqual(manager_state['timers'][0]['start_at'],'2026-01-06T07:00:00+00:00')
        with patch.object(self.server,'now',return_value='2026-01-06T07:15:00+00:00'):
            pending=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T09:00:00+00:00','reason':'Segunda extensión'},self.tc)['id']
        with patch.object(self.server,'now',return_value='2026-01-06T07:30:00+00:00'):
            self.fx.post(f'/api/timers/{resumed}/stop',{},self.tc)
            self.assertEqual(self.mc.post(f'/api/extensions/{pending}/decision',json={'decision':'APPROVED'}).status_code,409)
        state=self.tc.get('/api/state').json();self.assertEqual(len(state['timer_segments']),2)
        self.assertEqual(state['overtime'][0]['status'],'SUBMITTED');self.assertEqual(state['overtime'][0]['worked_seconds'],5400)
        self.assertEqual(state['extensions'][1]['status'],'CANCELLED')
        self.assertEqual(self.tc.get('/api/accounting?month=2026-01').json()['ot_minutes'],0)
        self.fx.approve(self.mc,'ot',ot)
        rule=self.fx.post('/api/rules',{'name':'Noche','effective_from':'2026-01-01','segments':[{'day':0,'start':'22:00','end':'04:00'}]},self.mc)['id']
        guard=self.fx.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},self.tc)['id'];self.fx.approve(self.mc,'guard',guard)
        report=self.tc.get('/api/accounting?month=2026-01').json()
        self.assertEqual(report['ot_minutes'],90);self.assertEqual(report['guard_minutes'],270)
        wb=load_workbook(io.BytesIO(self.tc.get('/api/export.xlsx?month=2026-01').content))
        self.assertEqual(sum(r[8] for r in list(wb['Tiempo aprobado'].values)[1:]),6)
        for route in ['/api/my-analytics?month=2026-01','/api/analytics?month=2026-01']:
            client=self.tc if 'my-' in route else self.mc
            analytics=client.get(route).json();self.assertEqual(analytics['summary']['PLANNED'],90);self.assertEqual(analytics['summary']['GUARD'],270)
        events={a['action'] for a in self.tc.get('/api/state').json()['audit']}
        self.assertTrue({'PAUSE_PLANNED_WINDOW','REQUEST_OT_EXTENSION','DECIDE_OT_EXTENSION','CANCEL_OT_EXTENSION'}.issubset(events))

    def test_delegated_backup_can_decide_other_users_but_not_self_or_after_revocation(self):
        backup_group=self.fx.group(self.account,'BACKUP-GROUP',self.manager['id'])
        lead,lc,_=self.fx.person('USER','BACKUP',group=backup_group,lead=True)
        current=datetime.now(timezone.utc)
        own=self.fx.ot(lc,(current+timedelta(days=1)).isoformat(),(current+timedelta(days=1,hours=1)).isoformat())
        self.fx.approve(self.mc,'ot',own)
        ot,_=self.paused()
        with patch.object(self.server,'now',return_value='2026-01-06T06:30:00+00:00'):
            delegation=self.fx.post('/api/delegations',{'lead_id':lead['id']},self.mc)['id']
            own_ext=self.fx.post(f'/api/overtime/{own}/extensions',{'requested_end':(current+timedelta(days=1,hours=2)).isoformat(),'reason':'Más trabajo'},lc)['id']
            self.assertEqual(lc.post(f'/api/extensions/{own_ext}/decision',json={'decision':'APPROVED'}).status_code,403)
            ext=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T08:00:00+00:00','reason':'Más trabajo'},self.tc)['id']
            self.fx.post(f'/api/extensions/{ext}/decision',{'decision':'APPROVED'},lc)
            next_ext=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T09:00:00+00:00','reason':'Nueva extensión'},self.tc)['id']
            self.assertEqual(self.mc.delete('/api/delegations/'+delegation).status_code,200)
            self.assertEqual(lc.post(f'/api/extensions/{next_ext}/decision',json={'decision':'APPROVED'}).status_code,403)
            self.fx.post(f'/api/extensions/{next_ext}/decision',{'decision':'APPROVED'},self.mc)

    def test_approved_extension_before_deadline_keeps_same_timer_running(self):
        ot,timer=self.paused()
        with patch.object(self.server,'now',return_value='2026-01-06T05:30:00+00:00'):
            ext=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T08:00:00+00:00','reason':'Continuar el cambio'},self.tc)['id']
            self.fx.post(f'/api/extensions/{ext}/decision',{'decision':'APPROVED'},self.mc)
        with patch.object(self.server,'now',return_value='2026-01-06T06:30:00+00:00'):
            state=self.tc.get('/api/state').json();self.assertEqual(state['timers'][0]['id'],timer)
        with patch.object(self.server,'now',return_value='2026-01-06T08:30:00+00:00'):
            state=self.tc.get('/api/state').json();self.assertFalse(state['timers'])
            self.assertEqual(state['timer_segments'][0]['end_at'],'2026-01-06T08:00:00+00:00')
            self.assertEqual(self.tc.put('/api/overtime/'+ot,json={}).status_code,422)
            self.fx.post('/api/overtime/'+ot+'/finish',{},self.tc)
        self.fx.approve(self.mc,'ot',ot)
        self.assertEqual(self.tc.get('/api/accounting?month=2026-01').json()['ot_minutes'],180)

    def test_offboarding_cancels_pending_extension_for_unstarted_plan(self):
        current=datetime.now(timezone.utc)
        ot=self.fx.ot(self.tc,(current+timedelta(days=1)).isoformat(),(current+timedelta(days=1,hours=1)).isoformat())
        self.fx.approve(self.mc,'ot',ot)
        ext=self.fx.post('/api/overtime/'+ot+'/extensions',{'requested_end':(current+timedelta(days=1,hours=2)).isoformat(),'reason':'Trabajo adicional'},self.tc)['id']
        impact=self.fx.client.get('/api/admin/people/'+self.user['id']+'/impact').json()
        self.fx.post('/api/admin/people/'+self.user['id']+'/offboard',{'reason':'Baja de pruebas','confirm':True,'expected':impact['expected'],'transfers':{}})
        state=self.mc.get('/api/state').json()
        self.assertEqual(next(e for e in state['extensions'] if e['id']==ext)['status'],'CANCELLED')
        self.assertEqual(next(o for o in state['overtime'] if o['id']==ot)['status'],'CANCELLED')

    def test_rejection_permissions_and_manual_finish(self):
        ot,timer=self.paused()
        other_account=self.fx.account('OTHER');other_group=self.fx.group(other_account,'FOREIGN')
        _,foreign,_=self.fx.person('MANAGER','FOREIGN',account=other_account,groups=[other_group])
        with patch.object(self.server,'now',return_value='2026-01-06T06:30:00+00:00'):
            ext=self.fx.post(f'/api/overtime/{ot}/extensions',{'requested_end':'2026-01-06T08:00:00+00:00','reason':'Más trabajo'},self.tc)['id']
            self.assertEqual(foreign.post(f'/api/extensions/{ext}/decision',json={'decision':'APPROVED'}).status_code,403)
            self.assertEqual(self.fx.client.post(f'/api/extensions/{ext}/decision',json={'decision':'APPROVED'}).status_code,403)
            self.assertEqual(self.mc.post(f'/api/extensions/{ext}/decision',json={'decision':'REJECTED'}).status_code,422)
            self.fx.post(f'/api/extensions/{ext}/decision',{'decision':'REJECTED','reason':'No autorizado'},self.mc)
            self.assertEqual(self.tc.post('/api/timers/start',json={'overtime_id':ot}).status_code,422)
            self.assertEqual(self.mc.post(f'/api/overtime/{ot}/finish',json={}).status_code,403)
            self.fx.post(f'/api/overtime/{ot}/finish',{},self.tc)
        self.fx.approve(self.mc,'ot',ot)
        self.assertEqual(self.tc.get('/api/accounting?month=2026-01').json()['ot_minutes'],60)
        self.assertEqual(self.tc.get('/api/state').json()['extensions'][0]['status'],'REJECTED')


if __name__=='__main__':
    unittest.main()
