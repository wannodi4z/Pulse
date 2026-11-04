"""Admin disaster recovery and SMTP configuration: no network or real messages."""
import json
from pathlib import Path
import sqlite3
import unittest
from fastapi.testclient import TestClient
import test_api
from backend.system_admin import open_backup,MAGIC
from scripts.restore_organization import restore_backup

class SystemAdminTests(unittest.TestCase):
 def setUp(self):self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.tc=self.f.organization();self.password='Respaldo-Seguro-2026!'
 def tearDown(self):self.f.tearDown()
 def save(self,**extra):
  data={'host':'smtp.example.test','port':587,'security':'STARTTLS','username':'pulse','from_address':'pulse@example.test','from_name':'Pulse','password':'smtp-secret-not-public',**extra}
  return self.f.client.put('/api/admin/settings/smtp',json=data)
 def export(self):
  r=self.f.client.post('/api/admin/organization-backup',json={'password':self.password});self.assertEqual(r.status_code,200,r.text[:100] if r.status_code!=200 else '');return r.content
 def test_smtp_secrets_are_encrypted_and_no_delivery(self):
  self.assertEqual(self.save().status_code,200)
  public=self.f.client.get('/api/admin/settings').json();self.assertTrue(public['smtp']['password_configured']);self.assertFalse(public['mail_delivery_enabled']);self.assertNotIn('smtp-secret',json.dumps(public));self.assertNotIn('password_encrypted',json.dumps(public))
  with self.f.server.connection() as db:
   stored=db.execute("SELECT value FROM system_settings WHERE key='smtp'").fetchone()[0];self.assertNotIn('smtp-secret',stored);secret=json.loads(stored)['password_encrypted'];self.assertEqual(self.f.server.recovery_cipher().decrypt(secret.encode()).decode(),'smtp-secret-not-public');self.assertNotIn('smtp-secret',str(list(db.execute('SELECT detail FROM audit'))))
  self.assertEqual(self.save(password='',host='relay.example.test').status_code,200)
  self.assertTrue(self.f.client.get('/api/admin/settings').json()['smtp']['password_configured'])
  self.assertEqual(self.save(password='',clear_password=True).status_code,200)
  self.assertFalse(self.f.client.get('/api/admin/settings').json()['smtp']['password_configured'])
  for bad in [{'host':'https://bad/path'},{'port':70000},{'from_name':'bad\r\nheader'},{'security':'INVALID'},{'from_address':'invalid'}]:self.assertEqual(self.save(**bad).status_code,422)
 def test_roles_cannot_read_or_change_settings_or_export_backup(self):
  with self.f.server.connection() as db:dp=dict(db.execute("SELECT * FROM users WHERE role='DP'").fetchone())
  dc=TestClient(self.f.server.app);self.f.login(dc,dp['username'])
  for c in [self.mc,self.tc,dc]:
   self.assertEqual(c.get('/api/admin/settings').status_code,403)
   self.assertEqual(c.put('/api/admin/settings/smtp',json={}).status_code,403)
   self.assertEqual(c.post('/api/admin/organization-backup',json={'password':self.password}).status_code,403)
 def test_backup_and_offline_restore_preserve_data_and_secrets(self):
  self.assertEqual(self.save().status_code,200)
  ot=self.f.ot(self.tc);self.f.approve(self.mc,'ot',ot)
  rule=self.f.post('/api/rules',{'name':'Guardia de prueba','effective_from':'2026-01-01','segments':[{'day':0,'start':'08:00','end':'16:00'}]},self.mc)['id']
  guard=self.f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},self.tc)['id'];self.f.approve(self.mc,'guard',guard)
  payload=self.export();self.assertTrue(payload.startswith(MAGIC));self.assertNotIn(b'SQLite format',payload)
  with self.assertRaises(ValueError):open_backup(payload,'incorrect-password')
  with self.assertRaises(ValueError):open_backup(payload[:-1]+bytes([payload[-1]^1]),self.password)
  source=Path(self.f.temp.name)/'test.pulseorg';source.write_bytes(payload);destination=Path(self.f.temp.name)/'restored';manifest=restore_backup(source,destination,self.password)
  self.assertEqual(manifest['format'],'PULSE-ORG-1');self.assertTrue((destination/'operational_pulse.key').exists())
  with sqlite3.connect(destination/'operational_pulse.db') as db:
   self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0],0);self.assertEqual(db.execute('SELECT count(*) FROM session_activity').fetchone()[0],0)
   self.assertEqual(db.execute('SELECT status FROM overtime WHERE id=?',(ot,)).fetchone()[0],'APPROVED');self.assertEqual(db.execute("SELECT count(*) FROM users WHERE role IN ('DP','DPE')").fetchone()[0],2)
   self.assertEqual(db.execute('SELECT status FROM guards WHERE id=?',(guard,)).fetchone()[0],'APPROVED');self.assertIsNotNone(db.execute('SELECT id FROM rules WHERE id=?',(rule,)).fetchone())
   encrypted=json.loads(db.execute("SELECT value FROM system_settings WHERE key='smtp'").fetchone()[0])['password_encrypted']
  from cryptography.fernet import Fernet
  self.assertEqual(Fernet((destination/'operational_pulse.key').read_bytes()).decrypt(encrypted.encode()).decode(),'smtp-secret-not-public')
  with self.assertRaises(ValueError):restore_backup(source,destination,self.password)
 def test_active_timer_only_closed_in_recovery_copy(self):
  active=self.f.post('/api/timers/start',{'capture_type':'EMERGENCY'},self.tc)
  payload=self.export();database,_,manifest=open_backup(payload,self.password);self.assertEqual(manifest['closed_timers_in_copy'],1)
  with self.f.server.connection() as db:self.assertIsNone(db.execute('SELECT end_at FROM timers WHERE id=?',(active['id'],)).fetchone()[0])
  path=Path(self.f.temp.name)/'snapshot.db';path.write_bytes(database)
  with sqlite3.connect(path) as db:
   timer=db.execute('SELECT overtime_id,end_at FROM timers WHERE id=?',(active['id'],)).fetchone();self.assertEqual(timer[1],manifest['created_at']);self.assertEqual(db.execute('SELECT status,execution FROM overtime WHERE id=?',(timer[0],)).fetchone(),('DOCUMENTATION','COMPLETED'))
 def test_short_password_rejected(self):self.assertEqual(self.f.client.post('/api/admin/organization-backup',json={'password':'short'}).status_code,422)

if __name__=='__main__':unittest.main()
