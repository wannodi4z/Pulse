"""Synthetic data must be append-only, scoped, repeatable and preserve Samuel's October."""
import importlib.util
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient
from scripts.populate_demo_records import populate,protected_october,TZ,key
ROOT=Path(__file__).resolve().parents[1]

class DemoRecordsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'demo.sqlite3';shutil.copy(ROOT/'fixtures/banorte_pruebas.sqlite3',self.db)
  with patch.dict(os.environ,{'PULSE_DB_PATH':str(self.db)}):
   spec=importlib.util.spec_from_file_location('demo_test_server',ROOT/'server.py');self.s=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.s)
  self.client=TestClient(self.s.app);self.clock=datetime(2026,10,30,12,tzinfo=TZ)
 def tearDown(self):self.client.close();self.temp.cleanup()
 def connection(self):
  c=sqlite3.connect(self.db);c.row_factory=sqlite3.Row;return c
 def test_all_teams_samuel_protection_closed_timers_and_idempotency(self):
  with self.connection() as c:
   sam=c.execute("SELECT id FROM users WHERE employee_id='951357'").fetchone()[0]
   c.execute("INSERT INTO overtime(id,user_id,capture_type,start_at,end_at,reference,status,execution,created_at,updated_at) VALUES(?,?,'HISTORICAL',?,?,'CHG-SAM-ORIGINAL','SUBMITTED','COMPLETED',?,?)",('sam-original',sam,'2026-10-05T20:00:00-06:00','2026-10-05T22:00:00-06:00','2026-10-06T08:00:00-06:00','2026-10-06T08:00:00-06:00'))
   before=protected_october(c);original=[tuple(r) for r in c.execute('SELECT * FROM users ORDER BY id')]
  result=populate(self.db,clock=self.clock);self.assertEqual(result['people'],16);self.assertEqual(result['managers'],4);self.assertTrue(Path(result['backup']).is_file());self.assertTrue(result['protected_october_unchanged'])
  with self.connection() as c:
   self.assertEqual(before,protected_october(c));self.assertEqual(original,[tuple(r) for r in c.execute('SELECT * FROM users ORDER BY id')])
   self.assertFalse(list(c.execute('PRAGMA foreign_key_check')));self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   self.assertEqual(c.execute('SELECT count(*) FROM timers WHERE end_at IS NULL').fetchone()[0],0)
   self.assertEqual(c.execute('SELECT count(*) FROM guards g JOIN users u ON u.id=g.user_id WHERE u.is_lead=1').fetchone()[0],0)
   self.assertGreater(c.execute('SELECT count(*) FROM ot_group_activities').fetchone()[0],0)
   self.assertEqual(c.execute('SELECT count(*) FROM windows w LEFT JOIN ot_group_activities a ON a.window_id=w.id WHERE a.source_id IS NULL').fetchone()[0],0)
   counts={t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('overtime','guards','timers','windows','rules','audit')}
  repeat=populate(self.db,clock=self.clock);self.assertEqual(repeat['overtime'],0);self.assertEqual(repeat['guards'],0)
  with self.connection() as c:
   self.assertEqual(counts,{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in counts})
  for identity,password in [('MGR0001','manager12026'),('MGR0002','manager22026'),('MGR0003','manager32026'),('MGR0004','manager42026')]:
   self.assertEqual(self.client.post('/api/login',json={'identity':identity,'password':password}).status_code,200)
   r=self.client.get('/api/analytics?month=2026-09&months=2026-08,2026-10');self.assertEqual(r.status_code,200,r.text)
   data=r.json();self.assertGreater(data['summary']['ot_minutes'],0);self.assertGreater(data['summary']['GUARD'],0)
   self.assertLess(data['timeliness']['historical_share'],30)
   self.assertEqual(self.client.get('/api/state').status_code,200)
   self.assertEqual(self.client.get('/api/analytics.xlsx?month=2026-09').status_code,200)
  self.client.post('/api/login',json={'identity':'951357','password':'tecnico12026'})
  self.assertEqual(self.client.get('/api/my-analytics?month=2026-10').json()['record_count'],1)
  self.assertEqual(self.client.get('/api/my-analytics?month=2026-09').status_code,200)
 def test_seeded_ready_activity_starts_stops_and_returns_to_review(self):
  populate(self.db,clock=self.clock,backup=False)
  self.assertEqual(self.client.post('/api/login',json={'identity':'TEC0002','password':'tecnico12026'}).status_code,200)
  with self.connection() as c:user=c.execute("SELECT id FROM users WHERE employee_id='TEC0002'").fetchone()[0]
  identity=key('OT',user,'2026-10-30','ready-today')
  with patch.object(self.s,'now',return_value=self.clock.isoformat()):
   r=self.client.post('/api/timers/start',json={'overtime_id':identity});self.assertEqual(r.status_code,200,r.text);timer=r.json()['id']
  with patch.object(self.s,'now',return_value=self.clock.replace(minute=10).isoformat()):
   r=self.client.post('/api/timers/'+timer+'/stop',json={});self.assertEqual(r.status_code,200,r.text)
  with self.connection() as c:
   record=c.execute('SELECT * FROM overtime WHERE id=?',(identity,)).fetchone()
   self.assertEqual(record['execution'],'COMPLETED');self.assertEqual(record['status'],'SUBMITTED')
   row=c.execute('SELECT * FROM timers WHERE id=?',(timer,)).fetchone();self.assertEqual((datetime.fromisoformat(row['end_at'])-datetime.fromisoformat(row['start_at'])).total_seconds(),600)
 def test_active_timer_aborts_without_adding_records(self):
  with self.connection() as c:
   sam=c.execute("SELECT id FROM users WHERE employee_id='951357'").fetchone()[0]
   c.execute("INSERT INTO overtime(id,user_id,capture_type,start_at,reference,status,execution,created_at,updated_at) VALUES('active',?,'EMERGENCY',?,'','DOCUMENTATION','RUNNING',?,?)",(sam,self.clock.isoformat(),self.clock.isoformat(),self.clock.isoformat()))
   c.execute("INSERT INTO timers VALUES('active-timer',?,'active',?,NULL)",(sam,self.clock.isoformat()))
  with self.assertRaisesRegex(ValueError,'Timers activos'):populate(self.db,clock=self.clock)
  with self.connection() as c:self.assertEqual(c.execute('SELECT count(*) FROM overtime').fetchone()[0],1)
