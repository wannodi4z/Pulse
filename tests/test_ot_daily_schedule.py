"""Approved recurring windows count executed tranches, never the multi-day envelope."""
import unittest
from contextlib import contextmanager
from datetime import datetime,timezone
from unittest.mock import patch
import test_api
class DailyScheduleTests(unittest.TestCase):
 def setUp(self):
  self.f=test_api.PulseTests();self.f.setUp();self.s=self.f.server;self.a,self.g,self.m,self.mc,self.u,self.tc=self.f.organization()
 def tearDown(self):self.f.tearDown()
 @contextmanager
 def clock(self,iso):
  stamp=datetime.fromisoformat(iso)
  class Clock(datetime):
   @classmethod
   def now(cls,tz=None):return stamp.astimezone(tz) if tz else stamp.replace(tzinfo=None)
  with patch.object(self.s,'datetime',Clock),patch.object(self.s,'now',return_value=stamp.astimezone(timezone.utc).isoformat()):
   with self.s.connection(True) as c:
    c.execute("UPDATE sessions SET expires_at='2050-01-01T00:00:00+00:00'");c.execute('UPDATE session_activity SET last_activity=?',(self.s.now(),))
   yield
 def planned(self):return self.f.ot(self.tc,'2030-11-02T21:00:00-06:00','2030-11-05T08:00:00-06:00',capture_type='PLANNED',daily_window=True)
 def test_night_boundaries_resume_and_real_accounting(self):
  with self.clock('2030-11-01T12:00:00-06:00'):
   record=self.planned();self.f.approve(self.mc,'ot',record)
   rule=self.f.post('/api/rules',{'name':'Cobertura completa','effective_from':'2030-11-01','segments':[{'day':d,'start':'00:00','end':'00:00'} for d in range(7)]},self.mc)['id']
   guard=self.f.post('/api/guards',{'rule_id':rule,'start_date':'2030-11-02','end_date':'2030-11-04'},self.tc)['id'];self.f.approve(self.mc,'guard',guard)
  with self.clock('2030-11-02T20:59:00-06:00'):self.assertEqual(self.tc.post('/api/timers/start',json={'overtime_id':record}).status_code,422)
  with self.clock('2030-11-02T21:00:00-06:00'):self.f.post('/api/timers/start',{'overtime_id':record},self.tc)
  with self.clock('2030-11-03T08:00:00-06:00'):
   o=next(o for o in self.tc.get('/api/state').json()['overtime'] if o['id']==record);self.assertEqual(o['execution'],'PAUSED');self.assertEqual(o['worked_seconds'],11*3600)
   self.assertEqual(self.tc.post('/api/timers/start',json={'overtime_id':record}).status_code,422)
  with self.clock('2030-11-03T21:00:00-06:00'):self.f.post('/api/timers/start',{'overtime_id':record},self.tc)
  with self.clock('2030-11-03T22:00:00-06:00'):self.f.post('/api/overtime/'+record+'/pause',{},self.tc)
  with self.clock('2030-11-04T21:00:00-06:00'):timer=self.f.post('/api/timers/start',{'overtime_id':record},self.tc)['id']
  with self.clock('2030-11-04T23:00:00-06:00'):
   self.f.post('/api/timers/'+timer+'/stop',{},self.tc);self.f.approve(self.mc,'ot',record)
   report=self.tc.get('/api/accounting?month=2030-11').json();self.assertEqual(report['ot_minutes'],14*60);self.assertEqual(report['guard_minutes'],58*60)
   for view in ('claim',None):
    report=self.tc.get('/api/accounting',params={'month':'2030-11',**({'view':view} if view else {})});self.assertEqual(report.status_code,200,report.text);self.assertEqual(report.json()['ot_minutes'],14*60)
 def test_reconciliation_after_downtime_stops_at_first_daily_close(self):
  with self.clock('2030-11-01T12:00:00-06:00'):
   record=self.planned();self.f.approve(self.mc,'ot',record)
  with self.clock('2030-11-02T21:00:00-06:00'):self.f.post('/api/timers/start',{'overtime_id':record},self.tc)
  with self.clock('2030-11-04T22:00:00-06:00'):
   o=next(x for x in self.tc.get('/api/state').json()['overtime'] if x['id']==record)
   self.assertEqual(o['execution'],'PAUSED');self.assertEqual(o['worked_seconds'],11*3600);self.assertFalse(self.tc.get('/api/state').json()['timers'])
 def test_manager_policy_snapshot_shared_activity_and_authorization(self):
  peer,pc,_=self.f.person('USER','PEER',group=self.g)
  with self.clock('2030-11-01T12:00:00-06:00'):
   self.assertEqual(self.tc.put('/api/ot-policy',json={'enabled':True,'start_time':'21:00','end_time':'08:00'}).status_code,403)
   self.assertEqual(self.mc.put('/api/ot-policy',json={'enabled':True,'start_time':'21:00','end_time':'08:00'}).status_code,200)
   record=self.planned();self.f.approve(self.mc,'ot',record)
   self.assertEqual(self.mc.put('/api/ot-policy',json={'enabled':True,'start_time':'22:00','end_time':'06:00'}).status_code,200)
   o=next(o for o in self.tc.get('/api/state').json()['overtime'] if o['id']==record);self.assertEqual(o['schedule']['start_time'],'21:00')
   joined=self.f.post('/api/windows/'+o['window_id']+'/join',{},pc)['id'];po=next(x for x in pc.get('/api/state').json()['overtime'] if x['id']==joined);self.assertEqual(po['schedule'],o['schedule'])
   second=self.f.ot(self.tc,'2030-11-06T21:00:00-06:00','2030-11-07T08:00:00-06:00',daily_window=False)
   self.assertEqual(next(x for x in self.tc.get('/api/state').json()['overtime'] if x['id']==second)['schedule']['start_time'],'22:00')
  with self.clock('2030-11-02T12:00:00-06:00'):
   result=self.tc.get('/api/activities/'+o['window_id']);self.assertFalse(result.json()['can_start'])
  with self.clock('2030-11-02T21:00:00-06:00'):self.assertEqual(pc.post('/api/timers/start',json={'overtime_id':joined}).status_code,200)
 def test_historical_original_window_and_actual_tranches_are_distinct(self):
  data={'scheduled_start':'2026-01-05T21:00:00-06:00','scheduled_end':'2026-01-07T08:00:00-06:00','actual_start':'2026-01-05T22:00:00-06:00','actual_end':'2026-01-06T23:30:00-06:00','actual_segments':[{'start_at':'2026-01-05T22:00:00-06:00','end_at':'2026-01-05T23:00:00-06:00'},{'start_at':'2026-01-06T22:00:00-06:00','end_at':'2026-01-06T23:30:00-06:00'}],'reference':'CHG-HISTORY','description':'Cambio nocturno','justification':'Captura posterior justificada'}
  record=self.f.post('/api/overtime',data,self.tc)['id'];self.f.approve(self.mc,'ot',record)
  o=next(o for o in self.tc.get('/api/state').json()['overtime'] if o['id']==record)
  self.assertEqual(datetime.fromisoformat(o['scheduled_start']),datetime.fromisoformat(data['scheduled_start']));self.assertEqual(o['worked_seconds'],9000);self.assertFalse(o['time_corrected']);self.assertEqual(len(o['actual_segments']),2)
  self.assertEqual(self.tc.get('/api/accounting?month=2026-01').json()['ot_minutes'],150)
  import io,json
  from openpyxl import load_workbook
  wb=load_workbook(io.BytesIO(self.tc.get('/api/time-backup.pulse?month=2026-01').content));payload=json.loads(wb['Respaldo Pulse'].cell(2,2).value)
  self.assertEqual(datetime.fromisoformat(payload['original_window']['start_at']),datetime.fromisoformat(data['scheduled_start']));self.assertEqual(len(payload['segments']),2)
  bad={**data,'reference':'INC-BAD','actual_segments':[data['actual_segments'][1],data['actual_segments'][0]]}
  self.assertEqual(self.tc.post('/api/overtime',json=bad).status_code,422)
if __name__=='__main__':unittest.main()
