import io
import unittest
from openpyxl import load_workbook
import test_api

class ActivityExportTests(unittest.TestCase):
 def setUp(self):self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.tc=self.f.organization()
 def tearDown(self):self.f.tearDown()
 def test_activity_permissions_window_and_no_get_capture(self):
  from datetime import datetime,timedelta,timezone
  start=datetime.now(timezone.utc)+timedelta(hours=1);end=start+timedelta(hours=2)
  record=self.f.ot(self.tc,start.isoformat(),end.isoformat(),capture_type='PLANNED')
  self.f.approve(self.mc,'ot',record)
  state=self.tc.get('/api/state').json();o=next(r for r in state['overtime'] if r['id']==record);key=o['window_id'] or record
  result=self.tc.get('/api/activities/'+key);self.assertEqual(result.status_code,200,result.text);self.assertFalse(result.json()['can_start']);self.assertTrue(result.json()['approved']);self.assertEqual(len(self.tc.get('/api/state').json()['timers']),0)
  self.assertEqual(self.mc.get('/api/activities/'+key).status_code,403)
  other_account=self.f.account('OTHER');group=self.f.group(other_account,'OTHERGROUP');other,oc,_=self.f.person('USER','OTHER',group=group)
  self.assertEqual(oc.get('/api/activities/'+key).status_code,404)
 def test_records_export_is_not_analytics_and_keeps_filters(self):
  record=self.f.ot(self.tc);self.f.approve(self.mc,'ot',record);self.f.ot(self.tc,'2026-01-08T10:00:00-06:00','2026-01-08T12:00:00-06:00',reference='INC1234567')
  records=self.mc.get('/api/records.xlsx?month=2026-01&status=SUBMITTED');analytics=self.mc.get('/api/analytics.xlsx?month=2026-01')
  self.assertEqual(records.status_code,200);self.assertEqual(analytics.status_code,200)
  a=load_workbook(io.BytesIO(analytics.content));r=load_workbook(io.BytesIO(records.content))
  self.assertEqual(r.sheetnames,['Registros','Filtros']);self.assertNotIn('Registros',a.sheetnames);self.assertIn('Por grupo',a.sheetnames);self.assertEqual(r['Registros'].max_row,2)
  self.assertEqual(self.tc.get('/api/records.xlsx?month=2026-01').status_code,403);self.assertEqual(self.tc.get('/api/my-records.xlsx?month=2026-01').status_code,200)

if __name__=='__main__':unittest.main()
