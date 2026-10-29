"""Read-only personal Guard chronology uses snapshots, operating timezone and midnight slices."""
import unittest,json
import test_api
class GuardTimelineTests(unittest.TestCase):
 def setUp(self):self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.uc=self.f.organization()
 def tearDown(self):self.f.tearDown()
 def coverage(self,segments,start='2026-01-31',end='2026-02-01'):
  data={'name':'Regla guardada','effective_from':'2026-01-01','segments':segments};rule=self.f.post('/api/rules',data,self.mc)['id'];guard=self.f.post('/api/guards',{'rule_id':rule,'start_date':start,'end_date':end},self.uc)['id'];return rule,guard
 def test_pending_overnight_and_multiple_segments_are_on_actual_days(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'00:00'},{'day':6,'start':'00:00','end':'04:00'},{'day':6,'start':'20:00','end':'00:00'}])
  state=self.uc.get('/api/state').json();g=next(g for g in state['guards'] if g['id']==guard);days=g['timeline_days'];self.assertEqual([d['date'] for d in days],['2026-01-31','2026-02-01']);self.assertEqual(len(days[1]['segments']),2);self.assertTrue(days[0]['end_at'].startswith('2026-02-01T00:00:00'))
  self.assertEqual(g['status'],'SUBMITTED');self.assertEqual(self.uc.get('/api/accounting?month=2026-01').json()['guard_minutes'],0)
  self.assertNotIn('timeline_days',self.mc.get('/api/state').json()['guards'][0])
 def test_overnight_spills_into_next_month_and_snapshot_does_not_follow_rule_edit(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'02:00'}],end='2026-01-31');before=self.uc.get('/api/state').json()['guards'][0]
  self.assertEqual([d['date'] for d in before['timeline_days']],['2026-01-31','2026-02-01'])
  with self.f.server.connection() as c:stored=dict(self.f.server.get(c,'guards',guard))
  self.assertEqual(self.mc.put('/api/rules/'+rule,json={'name':'Regla modificada','effective_from':'2026-01-01','segments':[{'day':5,'start':'15:00','end':'16:00'}]}).status_code,200)
  after=self.uc.get('/api/state').json()['guards'][0];self.assertEqual(before['timeline_days'],after['timeline_days']);self.assertEqual(after['rule_snapshot']['name'],'Regla guardada')
  with self.f.server.connection() as c:self.assertEqual(stored,dict(self.f.server.get(c,'guards',guard)))
  self.f.approve(self.mc,'guard',guard);self.assertEqual(self.uc.get('/api/accounting?month=2026-01').json()['guard_minutes'],120);self.assertEqual(self.uc.get('/api/accounting?month=2026-02').json()['guard_minutes'],120)
 def test_closed_coverage_is_clipped_and_unmatched_rule_is_empty(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'02:00'}],end='2026-01-31')
  with self.f.server.connection(True) as c:
   snapshot=json.loads(self.f.server.get(c,'guards',guard)['rule_snapshot']);snapshot['coverage_end_at']='2026-02-01T01:30:00-06:00';c.execute('UPDATE guards SET rule_snapshot=? WHERE id=?',(json.dumps(snapshot),guard))
  days=self.uc.get('/api/state').json()['guards'][0]['timeline_days'];self.assertEqual(days[-1]['end_at'],'2026-02-01T01:30:00-06:00')
  _,empty=self.coverage([{'day':0,'start':'02:00','end':'04:00'}],start='2026-01-31',end='2026-01-31');self.assertEqual(next(g for g in self.uc.get('/api/state').json()['guards'] if g['id']==empty)['timeline_days'],[])
 def test_full_day_and_privacy(self):
  _,guard=self.coverage([{'day':6,'start':'00:00','end':'00:00'}],start='2026-02-01',end='2026-02-01');days=self.uc.get('/api/state').json()['guards'][0]['timeline_days'];self.assertEqual(len(days),1);self.assertTrue(days[0]['end_at'].startswith('2026-02-02T00:00:00'))
  _,other,_=self.f.person('USER','T-PRIVATE',group=self.g);self.assertEqual(other.get('/api/state').json()['guards'],[])

 def test_rule_change_notice_and_explicit_revision_reapproval(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'02:00'}],end='2026-01-31')
  self.f.approve(self.mc,'guard',guard)
  self.assertFalse(self.uc.get('/api/state').json()['guards'][0]['rule_changed'])
  self.assertEqual(self.mc.put('/api/rules/'+rule,json={'name':'Nueva cobertura','effective_from':'2026-01-01','segments':[{'day':5,'start':'20:00','end':'02:00'}]}).status_code,200)
  current=self.uc.get('/api/state').json()['guards'][0];self.assertTrue(current['rule_changed']);self.assertEqual(current['status'],'APPROVED')
  self.assertEqual(self.uc.get('/api/accounting?month=2026-01').json()['guard_minutes'],120)
  review=self.uc.get('/api/guards/'+guard+'/revision').json()
  payload={'expected':review['expected'],'rule_token':review['rules'][0]['token'],'rule_id':rule,'start_date':'2026-01-31','end_date':'2026-01-31','reason':'Actualizar intervalos','confirm':True}
  self.assertEqual(self.mc.put('/api/guards/'+guard,json=payload).status_code,403)
  self.assertEqual(self.uc.put('/api/guards/'+guard,json={**payload,'confirm':False}).status_code,422)
  self.assertEqual(self.uc.put('/api/guards/'+guard,json=payload).status_code,200)
  current=self.uc.get('/api/state').json()['guards'][0];self.assertEqual(current['id'],guard);self.assertEqual(current['status'],'SUBMITTED');self.assertIsNone(current['approved_by']);self.assertFalse(current['rule_changed'])
  self.assertEqual(self.uc.get('/api/accounting?month=2026-01').json()['guard_minutes'],0)
  self.f.approve(self.mc,'guard',guard)
  self.assertEqual(self.uc.get('/api/accounting?month=2026-01').json()['guard_minutes'],240)
  with self.f.server.connection() as c:self.assertIsNotNone(c.execute("SELECT 1 FROM audit WHERE action='REVISE_GUARD' AND entity_id=?",(guard,)).fetchone())
 def test_revision_rejects_changed_rule_stale_guard_and_foreign_owner(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'02:00'}],end='2026-01-31')
  review=self.uc.get('/api/guards/'+guard+'/revision').json()
  payload={'expected':review['expected'],'rule_token':review['rules'][0]['token'],'rule_id':rule,'start_date':'2026-01-31','end_date':'2026-01-31','reason':'Revisar','confirm':True}
  _,other,_=self.f.person('USER','PRIVATE-REV',group=self.g)
  self.assertEqual(other.get('/api/guards/'+guard+'/revision').status_code,403)
  self.assertEqual(other.put('/api/guards/'+guard,json=payload).status_code,403)
  self.assertEqual(self.uc.put('/api/guards/'+guard,json={**payload,'expected':'stale'}).status_code,409)
  self.mc.put('/api/rules/'+rule,json={'name':'Cambio concurrente','effective_from':'2026-01-01','segments':[{'day':5,'start':'20:00','end':'02:00'}]})
  self.assertEqual(self.uc.put('/api/guards/'+guard,json=payload).status_code,409)
 def test_removed_rule_retains_snapshot_and_notifies_owner(self):
  rule,guard=self.coverage([{'day':5,'start':'22:00','end':'02:00'}],end='2026-01-31')
  before=self.uc.get('/api/state').json()['guards'][0]['timeline_days']
  self.assertEqual(self.mc.delete('/api/rules/'+rule).status_code,200)
  after=self.uc.get('/api/state').json()['guards'][0];self.assertTrue(after['rule_changed']);self.assertEqual(after['timeline_days'],before)
