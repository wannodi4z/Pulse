"""Only the six requested test users; never overwrite an existing organization."""
import unittest
from fastapi.testclient import TestClient
from backend.demo_banorte import seed_banorte_demo,DEMO_PEOPLE
import test_api
class BanorteBranchTests(unittest.TestCase):
 def setUp(self):self.f=test_api.PulseTests();self.f.setUp();self.s=self.f.server
 def tearDown(self):self.f.tearDown()
 def test_credentials_chain_and_no_hours_or_delegation(self):
  self.assertTrue(seed_banorte_demo(vars(self.s)))
  people={}
  for role,employee,first,last,password in DEMO_PEOPLE:
   client=TestClient(self.s.app);r=client.post('/api/login',json={'identity':employee,'password':password});self.assertEqual(r.status_code,200,r.text);people[employee]=r.json()['user']
   if role in ('DP','DPE','MANAGER'):self.assertEqual(client.post('/api/timers/start',json={}).status_code,403)
  with self.s.connection() as c:
   account=dict(c.execute('SELECT * FROM accounts').fetchone());self.assertEqual((account['name'],account['country_code']),('Banorte','MX'))
   users={r['employee_id']:dict(r) for r in c.execute("SELECT * FROM users WHERE role!='ADMIN'")};self.assertEqual(len(users),6)
   self.assertEqual(users['DPE0001']['parent_id'],users['DP00001']['id']);self.assertEqual(users['MGR0001']['parent_id'],users['DPE0001']['id'])
   self.assertTrue(users['SL0001']['is_lead']);self.assertIsNone(users['SL0001']['group_id']);self.assertEqual(users['SL0001']['manager_id'],users['MGR0001']['id'])
   self.assertEqual(users['951357']['group_id'],users['951358']['group_id'])
   for table in ('overtime','guards','timers','delegations'):self.assertEqual(c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
   self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
 def test_restart_never_resets_password_or_adds_duplicate_people(self):
  self.assertTrue(seed_banorte_demo(vars(self.s)))
  with self.s.connection(True) as c:c.execute("UPDATE users SET password_hash=? WHERE employee_id='951357'",(self.s.password_hash('changed-password-2026'),))
  self.assertFalse(seed_banorte_demo(vars(self.s)))
  client=TestClient(self.s.app);self.assertEqual(client.post('/api/login',json={'identity':'951357','password':'changed-password-2026'}).status_code,200)
 def test_other_organization_is_not_touched(self):
  self.f.organization();self.assertFalse(seed_banorte_demo(vars(self.s)))
  with self.s.connection() as c:self.assertIsNone(c.execute("SELECT 1 FROM users WHERE employee_id='DP00001'").fetchone())
if __name__=='__main__':unittest.main()
