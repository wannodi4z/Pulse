"""Capture discipline is scoped and distinguishes backup recovery from manual backlog."""
import unittest
import test_analytics_workspace

class CaptureTimelinessTests(unittest.TestCase):
 def setUp(self):self.x=test_analytics_workspace.AnalyticsWorkspaceTests();self.x.setUp()
 def tearDown(self):self.x.tearDown()
 def test_delay_and_recovery_exclusion_preserve_approved_hours(self):
  x=self.x;s=x.f.server
  with s.connection() as c:
   source=c.execute("SELECT id FROM overtime WHERE reference='CHG-ALPHA' AND start_at LIKE '2026-01%' ").fetchone()[0]
   recovered=c.execute("SELECT id,user_id FROM overtime WHERE reference='INC-BETA'").fetchone()
   c.execute('UPDATE overtime SET created_at=? WHERE id=?',('2026-01-07T12:00:00-06:00',source))
   c.execute('INSERT INTO time_recovery_items VALUES(?,?,?,?,?)',(recovered['user_id'],'test-source',recovered['id'],'test-batch','{"kind":"OT","origin":"PULSE-TIME-1","source_id":"example"}'))
  report=x.mc.get('/api/analytics?month=2026-01').json();t=report['timeliness']
  self.assertEqual(t,{'manual_ot_records':1,'historical_records':1,'historical_share':100.0,'average_delay_hours':48.0,'recovered_ot_records':1})
  self.assertEqual(report['summary']['ot_minutes'],360)
  self.assertTrue(next(r for r in report['records'] if r['id']==recovered['id'])['recovered'])
  self.assertIsNone(next(r for r in report['records'] if r['id']==recovered['id'])['capture_delay_hours'])
  personal=x.tc.get('/api/my-analytics?month=2026-01').json();self.assertEqual(personal['timeliness']['recovered_ot_records'],0)
  self.assertNotIn(recovered['id'],{r['id'] for r in personal['records']})
 def test_no_base_and_query_scope(self):
  r=self.x.mc.get('/api/analytics?month=2026-01&q=not-found').json()
  self.assertEqual(r['timeliness']['manual_ot_records'],0);self.assertIsNone(r['timeliness']['historical_share']);self.assertIsNone(r['timeliness']['average_delay_hours'])
