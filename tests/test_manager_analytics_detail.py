"""Manager analytics distinguishes enrollment, executed Timers and approved hours."""
import unittest
from datetime import timedelta
from unittest.mock import patch
import test_group_planned_ot
import test_analytics_workspace
class ManagerActivityTests(unittest.TestCase):
 def setUp(self):
  self.x=test_group_planned_ot.GroupPlannedOTTests();self.x.setUp();self.f=self.x.f
 def tearDown(self):self.x.tearDown()
 def url(self,identity=None):return '/api/analytics/overtime/'+(identity or self.x.ot)+'/participants'
 def test_only_linked_activity_not_same_reference_and_distinct_timer_execution(self):
  x=self.x;self.f.approve(x.mc,'ot',x.ot);window=x.activity()
  peer=self.f.post('/api/windows/'+window['id']+'/join',{},x.pc)['id']
  idle,ic,_=self.f.person('USER','IDLE',group=x.g);self.f.post('/api/windows/'+window['id']+'/join',{},ic)
  other=self.f.ot(x.pc,'2026-01-02T10:00:00-06:00','2026-01-02T11:00:00-06:00',reference='CHG-GROUP-NORMAL')
  s=self.f.server
  with patch.object(s,'now',return_value=(x.start+timedelta(minutes=1)).isoformat()):t1=self.f.post('/api/timers/start',{'overtime_id':x.ot},x.uc)['id']
  with patch.object(s,'now',return_value=(x.start+timedelta(minutes=3)).isoformat()):t2=self.f.post('/api/timers/start',{'overtime_id':peer},x.pc)['id']
  with patch.object(s,'now',return_value=(x.start+timedelta(minutes=11)).isoformat()):self.f.post('/api/timers/'+t1+'/stop',{},x.uc)
  with patch.object(s,'now',return_value=(x.start+timedelta(minutes=23)).isoformat()):self.f.post('/api/timers/'+t2+'/stop',{},x.pc)
  self.f.approve(x.mc,'ot',x.ot);self.f.approve(x.mc,'ot',peer)
  r=x.mc.get(self.url()).json();self.assertTrue(r['shared_activity']);self.assertEqual(r['participant_count'],3);self.assertEqual(r['executed_count'],2)
  self.assertNotIn(other,{p['record_id'] for p in r['participants']});self.assertEqual(sum(p['approved_minutes'] for p in r['participants']),30)
  self.assertEqual(sum(p['closed_seconds'] for p in r['participants']),1800);self.assertEqual(sum(p['is_source'] for p in r['participants']),1)
  self.assertFalse(next(p for p in r['participants'] if p['user_id']==idle['id'])['executed_timer'])
  self.assertEqual(x.mc.get(self.url(peer)).json()['participants'],r['participants'])
 def test_personal_denied_other_manager_hidden_and_delegation_revoked(self):
  x=self.x;self.assertEqual(x.uc.get(self.url()).status_code,403)
  a=self.f.account('PRIVATE');g=self.f.group(a,'P');manager,mc,_=self.f.person('MANAGER','PRIV-M',account=a,groups=[g])
  self.assertEqual(mc.get(self.url()).status_code,404)
  lead,lc,_=self.f.person('USER','LEAD-A',group=x.g,lead=True)
  self.assertEqual(lc.get(self.url()).status_code,403)
  d=self.f.post('/api/delegations',{'lead_id':lead['id']},x.mc)['id'];self.assertEqual(lc.get(self.url()).status_code,200)
  self.assertEqual(x.mc.delete('/api/delegations/'+d).status_code,200);self.assertEqual(lc.get(self.url()).status_code,403)
 def test_historical_reference_is_not_shared_activity(self):
  other=self.f.ot(self.x.uc,reference='CHG-GROUP-NORMAL');r=self.x.mc.get(self.url(other)).json()
  self.assertFalse(r['shared_activity']);self.assertEqual(r['participant_count'],1);self.assertEqual(r['executed_count'],0)
class ManagerBreakdownTests(unittest.TestCase):
 def setUp(self):self.x=test_analytics_workspace.AnalyticsWorkspaceTests();self.x.setUp()
 def tearDown(self):self.x.tearDown()
 def test_counts_zero_hours_and_search_share_same_scope(self):
  x=self.x;zero,zc,_=x.f.person('USER','ZERO',group=x.g)
  r=x.mc.get('/api/analytics?month=2026-01').json();group=next(g for g in r['groups'] if g['id']==x.g)
  self.assertEqual(group['approved_counts']['HISTORICAL'],1);self.assertEqual(group['approved_counts']['GUARD'],2)
  self.assertEqual(next(u for u in r['users'] if u['id']==zero['id'])['minutes']['total_minutes'],0)
  q=x.mc.get('/api/analytics',params={'month':'2026-01','q':'Persona T001'}).json();self.assertEqual(q['summary']['ot_minutes'],120)
  q=x.mc.get('/api/analytics',params={'month':'2026-01','q':'INC-BETA'}).json();self.assertEqual(q['summary']['ot_minutes'],240);self.assertEqual(q['groups'][0]['id'],x.g2)
  q=x.mc.get('/api/analytics',params={'month':'2026-01','q':'G2'}).json();self.assertEqual(q['users'][0]['id'],x.other['id'])
