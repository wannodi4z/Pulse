"""Normal planned OT is automatically visible to its Group; time remains individual."""
import unittest
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
import test_api
class GroupPlannedOTTests(unittest.TestCase):
 def setUp(self):
  self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.uc=self.f.organization()
  self.peer,self.pc,_=self.f.person('USER','PEER-GROUP',group=self.g)
  othergroup=self.f.group(self.a,'OTHER-GROUP',self.m['id']);self.outside,self.oc,_=self.f.person('USER','OUTSIDE-GROUP',group=othergroup)
  self.start=datetime.now(timezone.utc)+timedelta(hours=1);self.end=self.start+timedelta(hours=1)
  self.ot=self.f.ot(self.uc,start=self.start.isoformat(),end=self.end.isoformat(),reference='CHG-GROUP-NORMAL')
 def tearDown(self):self.f.tearDown()
 def activity(self):return self.pc.get('/api/state').json()['group_activities'][0]
 def test_automatic_group_visibility_pending_and_historical_privacy(self):
  pending=self.activity();self.assertEqual(pending['status'],'SUBMITTED');self.assertEqual(pending['reference'],'CHG-GROUP-NORMAL')
  self.assertEqual(self.pc.get('/api/state').json()['overtime'],[])
  self.assertEqual(self.oc.get('/api/state').json()['group_activities'],[])
  self.f.ot(self.uc,start='2026-01-03T10:00:00-06:00',end='2026-01-03T11:30:00-06:00',reference='CHG-HISTORY-PRIVATE')
  self.assertEqual(len(self.pc.get('/api/state').json()['group_activities']),1)
  self.assertEqual(self.pc.post('/api/windows/'+pending['id']+'/join',json={}).status_code,422)
 def test_independent_timers_authorization_and_accounting(self):
  self.f.approve(self.mc,'ot',self.ot);window=self.activity();self.assertEqual(window['status'],'APPROVED')
  join=self.pc.post('/api/windows/'+window['id']+'/join',json={});self.assertEqual(join.status_code,200,join.text);participant=join.json()['id'];self.assertNotEqual(participant,self.ot)
  self.assertEqual(self.pc.post('/api/windows/'+window['id']+'/join',json={}).json()['id'],participant)
  self.assertEqual(self.oc.post('/api/windows/'+window['id']+'/join',json={}).status_code,422)
  self.assertEqual(self.pc.post('/api/timers/start',json={'overtime_id':participant}).status_code,422)
  with patch.object(self.f.server,'now',return_value=(self.start+timedelta(minutes=1)).isoformat()):timer1=self.f.post('/api/timers/start',{'overtime_id':self.ot},self.uc)['id']
  with patch.object(self.f.server,'now',return_value=(self.start+timedelta(minutes=3)).isoformat()):timer2=self.f.post('/api/timers/start',{'overtime_id':participant},self.pc)['id']
  self.assertNotEqual(timer1,timer2)
  self.assertEqual(len(self.mc.get('/api/state').json()['timers']),2)
  self.assertEqual(len(self.uc.get('/api/state').json()['timers']),1)
  with patch.object(self.f.server,'now',return_value=(self.start+timedelta(minutes=11)).isoformat()):self.f.post('/api/timers/'+timer1+'/stop',{},self.uc)
  self.assertEqual(self.activity()['status'],'APPROVED')
  with patch.object(self.f.server,'now',return_value=(self.start+timedelta(minutes=23)).isoformat()):self.f.post('/api/timers/'+timer2+'/stop',{},self.pc)
  self.f.approve(self.mc,'ot',self.ot);self.f.approve(self.mc,'ot',participant)
  month=self.start.astimezone(self.f.server.TZ).strftime('%Y-%m')
  self.assertEqual(self.uc.get('/api/accounting?month='+month).json()['ot_minutes'],10)
  self.assertEqual(self.pc.get('/api/accounting?month='+month).json()['ot_minutes'],20)
  self.assertEqual(self.pc.get('/api/state').json()['overtime'][0]['justification'],'Cambio requerido')
 def test_source_revision_requires_approval_and_freezes_after_participants_join(self):
  self.f.approve(self.mc,'ot',self.ot);wid=self.activity()['id']
  data={'scheduled_start':self.start.isoformat(),'scheduled_end':self.end.isoformat(),'reference':'CHG-GROUP-UPDATED','description':'Nueva descripción','justification':'Operación','impact':'Servicio','in_lieu':'Cobertura'}
  self.assertEqual(self.uc.put('/api/overtime/'+self.ot,json=data).status_code,200)
  self.assertEqual(self.activity()['status'],'SUBMITTED');self.assertEqual(self.pc.post('/api/windows/'+wid+'/join',json={}).status_code,422)
  self.f.approve(self.mc,'ot',self.ot);self.assertEqual(self.pc.post('/api/windows/'+wid+'/join',json={}).status_code,200)
  self.assertEqual(self.uc.put('/api/overtime/'+self.ot,json=data).status_code,409)
