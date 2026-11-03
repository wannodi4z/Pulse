"""Executive scope and hierarchy migration run only against disposable databases."""
import io
import shutil
import sqlite3
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from openpyxl import load_workbook
import test_api
from backend.hierarchy import migrate_executive_roles

class ExecutiveTests(unittest.TestCase):
 def setUp(self):
  self.f=test_api.PulseTests();self.f.setUp();self.server=self.f.server
  self.a,self.g,self.m,self.mc,self.u,self.tc=self.f.organization()
  self.a2=self.f.account('OTHER');self.g2=self.f.group(self.a2,'G2');self.m2,self.mc2,_=self.f.person('MANAGER','M002',account=self.a2,groups=[self.g2]);self.u2,self.tc2,_=self.f.person('USER','T002',group=self.g2)
  with self.server.connection() as db:
   self.dp=dict(db.execute("SELECT * FROM users WHERE role='DP' AND account_id=?",(self.a,)).fetchone());self.dpe=dict(db.execute("SELECT * FROM users WHERE role='DPE' AND account_id=?",(self.a,)).fetchone())
  self.dc=TestClient(self.server.app);self.f.login(self.dc,self.dp['username'])
  self.ec=TestClient(self.server.app);self.f.login(self.ec,self.dpe['username'])
  self.record=self.f.ot(self.tc,'2026-01-05T10:00:00-06:00','2026-01-05T12:00:00-06:00');self.f.approve(self.mc,'ot',self.record)
 def tearDown(self):self.f.tearDown()
 def test_scopes_and_read_only(self):
  for client in [self.dc,self.ec]:
   state=client.get('/api/state').json();self.assertFalse(state['can_approve']);self.assertIn(self.u['id'],{p['id'] for p in state['people']});self.assertNotIn(self.u2['id'],{p['id'] for p in state['people']})
   r=client.get('/api/analytics?month=2026-01');self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['summary']['ot_minutes'],120);self.assertEqual(r.json()['managers'][0]['minutes']['ot_minutes'],120)
   for suffix in ['&manager_id='+self.m2['id'],'&user_id='+self.u2['id'],'&group_id='+self.g2]:self.assertEqual(client.get('/api/analytics?month=2026-01'+suffix).status_code,403)
   self.assertEqual(client.get('/api/my-analytics?month=2026-01').status_code,403)
   for method,path,payload in [('post','/api/approvals/ot/'+self.record,{'decision':'REJECTED'}),('post','/api/timers/start',{}),('post','/api/overtime',{}),('post','/api/guards',{}),('post','/api/people',{}),('put','/api/overtime/'+self.record,{}),('post','/api/rules',{}),('post','/api/delegations',{})]:self.assertEqual(getattr(client,method)(path,json=payload).status_code,403,path)
   x=client.get('/api/analytics.xlsx?month=2026-01');self.assertEqual(x.status_code,200);self.assertIn('Detalle',load_workbook(io.BytesIO(x.content)).sheetnames)
   self.assertEqual(client.get('/api/analytics/overtime/'+self.record+'/participants').status_code,200)
  # Reassignment is effective immediately, including existing sessions.
  dpe2,_,_=self.f.person('DP','NEW-DP',account=self.a)
  data={**self.m,'parent_id':None};self.assertEqual(self.f.client.put('/api/people/'+self.m['id'],json=data).status_code,422)
  with self.server.connection(True) as db:db.execute('UPDATE users SET parent_id=NULL WHERE id=?',(self.m['id'],))
  self.assertEqual(self.ec.get('/api/analytics?month=2026-01').json()['record_count'],0)
  self.assertEqual(self.ec.get('/api/analytics/overtime/'+self.record+'/participants').status_code,404)
  self.assertEqual(self.dc.get('/api/analytics?month=2026-01').json()['summary']['ot_minutes'],120)
 def test_dp_spans_dpes_but_dpe_does_not(self):
  created=self.f.post('/api/people',{'role':'DPE','employee_id':'DPE-SIBLING','first':'Otro','last':'DPE','email':'dpe@example.test','account_id':self.a,'parent_id':self.dp['id']})
  self.f.post('/api/activate',{'identity':'DPE-SIBLING','code':created['activation_code'],'password':'Password2026!'})
  group=self.f.group(self.a,'SIBLING-GROUP');manager,mc,data=self.f.person('MANAGER','SIBLING-MGR',account=self.a,groups=[group])
  self.f.post('/api/session/activity',{},self.f.client)
  self.assertEqual(self.f.client.put('/api/people/'+manager['id'],json={**data,'parent_id':created['id']}).status_code,200)
  user,uc,_=self.f.person('USER','SIBLING-TECH',group=group)
  record=self.f.ot(uc,'2026-01-06T10:00:00-06:00','2026-01-06T13:00:00-06:00');self.f.approve(mc,'ot',record)
  dp=self.dc.get('/api/analytics?month=2026-01').json();dpe=self.ec.get('/api/analytics?month=2026-01').json()
  self.assertEqual(dp['summary']['ot_minutes'],300);self.assertEqual(dpe['summary']['ot_minutes'],120)
  self.assertEqual(sum(m['minutes']['ot_minutes'] for m in dp['managers']),300)
  self.assertEqual(self.dc.get('/api/analytics',params={'month':'2026-01','dpe_id':created['id']}).json()['summary']['ot_minutes'],180)
  self.assertEqual(self.ec.get('/api/analytics',params={'month':'2026-01','manager_id':manager['id']}).status_code,403)
  self.assertEqual(self.ec.get('/api/analytics/overtime/'+record+'/participants').status_code,404)
  self.assertNotIn(user['id'],{p['id'] for p in self.ec.get('/api/state').json()['people']})
  self.assertIn(user['id'],{p['id'] for p in self.dc.get('/api/state').json()['people']})
  self.assertEqual(self.f.client.put('/api/people/'+manager['id'],json={**data,'parent_id':self.dpe['id']}).status_code,200)
  self.assertEqual(self.ec.get('/api/analytics?month=2026-01').json()['summary']['ot_minutes'],300)

 def test_parent_validation(self):
  self.assertEqual(self.f.client.put('/api/people/'+self.m['id'],json={**self.m,'parent_id':self.dp['id']}).status_code,422)
  self.assertEqual(self.f.client.put('/api/people/'+self.dpe['id'],json={**self.dpe,'parent_id':self.m['id']}).status_code,422)
  self.assertEqual(self.mc.post('/api/people',json={'role':'DP'}).status_code,403)
  r=self.f.client.get('/api/admin/people/'+self.dp['id']+'/impact');self.assertEqual(r.status_code,422)
 @unittest.skipUnless((test_api.ROOT/'fixtures/banorte_pruebas.sqlite3').is_file(), 'La fixture histórica sólo está en el repositorio de desarrollo.')
 def test_legacy_migration(self):
  # Baseline role CHECK migration preserves every original user and all FK references.
  path=Path(self.f.temp.name)/'migration.sqlite3';shutil.copy2(test_api.ROOT/'fixtures/banorte_pruebas.sqlite3',path)
  with sqlite3.connect(path) as db:before=db.execute('SELECT * FROM users ORDER BY id').fetchall()
  migrate_executive_roles(path);migrate_executive_roles(path)
  with sqlite3.connect(path) as db:
   self.assertEqual(before,db.execute('SELECT * FROM users ORDER BY id').fetchall());self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall());self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertIn("'DP'",db.execute("SELECT sql FROM sqlite_master WHERE name='users'").fetchone()[0])
  self.assertTrue(list((path.parent/'backups').glob('antes_v121_*.sqlite3')))

if __name__=='__main__':unittest.main()
