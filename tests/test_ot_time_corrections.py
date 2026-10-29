"""Time corrections preserve original timers and drive approved OT, Guard, Claim and ADP."""
import io,json,unittest
from unittest.mock import patch
from openpyxl import load_workbook
import test_claim_capture
class OTTimeCorrectionsTests(unittest.TestCase):
 def setUp(self):
  self.fixture=test_claim_capture.ClaimCaptureTests();self.fixture.setUp();self.f=self.fixture.f;self.uc=self.fixture.uc;self.mc=self.fixture.mc
  self.o=next(o for o in self.uc.get('/api/state').json()['overtime'] if o['reference']=='CHG-90MIN')
 def tearDown(self):self.fixture.tearDown()
 def payload(self,o=None,**extra):
  o=o or self.o
  return {**{key:o[key] for key in ['reference','description','justification','impact','in_lieu']},'expected_revision':o['revision'],'actual_start':o['start_at'],'actual_end':o['end_at'],'time_change_reason':'Corregir horario registrado',**extra}
 def test_correction_reopens_approval_then_recalculates_claim_adp_and_guard(self):
  result=self.uc.put('/api/overtime/'+self.o['id'],json=self.payload(actual_end='2026-01-03T05:00:00-06:00'));self.assertEqual(result.status_code,200,result.text)
  pending=self.uc.get('/api/accounting?month=2026-01').json();self.assertEqual(pending['ot_minutes'],30);self.assertEqual(pending['guard_minutes'],3360)
  self.f.approve(self.mc,'ot',self.o['id'])
  actual=self.uc.get('/api/accounting?month=2026-01').json();self.assertEqual((actual['ot_minutes'],actual['guard_minutes']),(150,3240))
  book=load_workbook(io.BytesIO(self.uc.get('/api/export.xlsx?month=2026-01&view=claim').content))
  rows=list(book['Claim semanal'].values);standby=next(r for r in rows if r[0]=='2026-01-03' and r[1]=='Stand By');ot=next(r for r in rows if r[0]=='2026-01-03' and r[1]=='OT')
  self.assertEqual((standby[3],ot[3]),(6,2))
  overtime=next(r for r in actual['rows'] if r['id']==self.o['id']);self.assertEqual(overtime['hours'],2);self.assertEqual(overtime['end'],'05:00')
  with self.f.server.connection() as c:self.assertIsNotNone(c.execute("SELECT 1 FROM audit WHERE action='CORRECT_OT_TIME' AND entity_id=?",(self.o['id'],)).fetchone())
 def test_change_day_cross_midnight_and_reject_future_invalid_or_stale(self):
  p=self.payload(actual_start='2026-01-10T23:30:00-06:00',actual_end='2026-01-11T01:00:00-06:00')
  self.assertEqual(self.uc.put('/api/overtime/'+self.o['id'],json={**p,'expected_revision':999}).status_code,409)
  self.assertEqual(self.uc.put('/api/overtime/'+self.o['id'],json={**p,'time_change_reason':''}).status_code,422)
  self.assertEqual(self.uc.put('/api/overtime/'+self.o['id'],json={**p,'actual_end':'2035-01-11T01:00:00-06:00'}).status_code,422)
  self.assertEqual(self.mc.put('/api/overtime/'+self.o['id'],json=p).status_code,403)
  self.assertEqual(self.uc.put('/api/overtime/'+self.o['id'],json=p).status_code,200)
  self.assertEqual(self.uc.put('/api/overtime/'+self.o['id'],json=p).status_code,409)
  self.f.approve(self.mc,'ot',self.o['id']);rows=[r for r in self.uc.get('/api/accounting?month=2026-01').json()['rows'] if r['id']==self.o['id']]
  self.assertEqual([(r['date'],r['minutes']) for r in rows],[('2026-01-10',30),('2026-01-11',60)])
 def test_emergency_correction_preserves_original_timer_and_unchanged_documentation(self):
  with patch.object(self.f.server,'now',return_value='2026-01-17T02:00:12-06:00'):timer=self.f.post('/api/timers/start',{},self.uc)['id']
  with patch.object(self.f.server,'now',return_value='2026-01-17T02:05:42-06:00'):self.f.post('/api/timers/'+timer+'/stop',{},self.uc)
  o=next(o for o in self.uc.get('/api/state').json()['overtime'] if o['capture_type']=='EMERGENCY');p=self.payload(o,reference='INC-TIME-FIX',description='Corrección',justification='Registro',impact='Servicio',in_lieu='Cobertura')
  metadata={k:v for k,v in p.items() if not k.startswith('actual_')};self.assertEqual(self.uc.put('/api/overtime/'+o['id'],json=metadata).status_code,200)
  with self.f.server.connection() as c:
   original=dict(self.f.server.get(c,'timers',timer));self.assertEqual(c.execute('SELECT count(*) FROM ot_time_corrections WHERE overtime_id=?',(o['id'],)).fetchone()[0],0)
  updated=next(r for r in self.uc.get('/api/state').json()['overtime'] if r['id']==o['id']);p=self.payload(updated,actual_start='2026-01-17T02:00:00-06:00',actual_end='2026-01-17T03:00:00-06:00')
  self.assertEqual(self.uc.put('/api/overtime/'+o['id'],json=p).status_code,200)
  with self.f.server.connection() as c:self.assertEqual(original,dict(self.f.server.get(c,'timers',timer)))
  self.f.approve(self.mc,'ot',o['id']);actual=self.uc.get('/api/accounting?month=2026-01').json();self.assertEqual(next(r for r in actual['rows'] if r['id']==o['id'])['minutes'],60)
 def test_multiple_work_segments_preserve_unpaid_gap(self):
  oid=self.f.ot(self.uc,start='2026-01-17T00:00:00-06:00',end='2026-01-17T04:00:00-06:00',reference='CHG-MULTI');self.f.approve(self.mc,'ot',oid)
  with self.f.server.connection(True) as c:
   c.execute("UPDATE overtime SET capture_type='PLANNED' WHERE id=?",(oid,))
   for a,b in [('00:00','01:00'),('03:00','04:00')]:c.execute('INSERT INTO timers VALUES(?,?,?,?,?)',(self.f.server.uid(),self.fixture.u['id'],oid,'2026-01-17T'+a+':00-06:00','2026-01-17T'+b+':00-06:00'))
   originals=[dict(r) for r in c.execute('SELECT * FROM timers WHERE overtime_id=?',(oid,))]
  o=next(r for r in self.uc.get('/api/state').json()['overtime'] if r['id']==oid)
  p=self.payload(o,actual_end='2026-01-17T05:00:00-06:00',actual_segments=[{'start_at':'2026-01-17T00:00:00-06:00','end_at':'2026-01-17T01:00:00-06:00'},{'start_at':'2026-01-17T03:00:00-06:00','end_at':'2026-01-17T05:00:00-06:00'}])
  self.assertEqual(self.uc.put('/api/overtime/'+oid,json=p).status_code,200)
  self.f.approve(self.mc,'ot',oid)
  actual=self.uc.get('/api/accounting?month=2026-01').json();self.assertEqual(sum(r['minutes'] for r in actual['rows'] if r['id']==oid),180)
  state=next(r for r in self.uc.get('/api/state').json()['overtime'] if r['id']==oid);self.assertEqual(state['worked_seconds'],10800);self.assertTrue(state['time_corrected'])
  with self.f.server.connection() as c:self.assertEqual(originals,[dict(r) for r in c.execute('SELECT * FROM timers WHERE overtime_id=?',(oid,))])
