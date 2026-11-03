"""A fresh delivery starts empty and a restart never replaces existing data."""
import os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BundledExamplesTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);shutil.copy(ROOT/'server.py',self.root/'server.py')
  for directory in ('backend','frontend'):shutil.copytree(ROOT/directory,self.root/directory,ignore=shutil.ignore_patterns('__pycache__'))
 def tearDown(self):self.temp.cleanup()
 def run_code(self,code,custom=False):
  env={k:v for k,v in os.environ.items() if k!='PULSE_DB_PATH'}
  if custom:env['PULSE_DB_PATH']=str(self.root/'operational_pulse.db')
  r=subprocess.run([sys.executable,'-c',code],cwd=self.root,env=env,text=True,capture_output=True);self.assertEqual(r.returncode,0,r.stderr);return r.stdout
 def test_fresh_bundle_has_only_initial_administrators(self):
  self.run_code('''import server
from fastapi.testclient import TestClient
c=TestClient(server.app)
for emp,pw in [('admin1','admin12026'),('admin2','admin22026')]:assert c.post('/api/login',json={'identity':emp,'password':pw}).status_code==200
with server.connection() as db:
 assert db.execute('SELECT count(*) FROM users').fetchone()[0]==2
 assert db.execute("SELECT count(*) FROM users WHERE role!='ADMIN'").fetchone()[0]==0
 for table in ['accounts','groups','overtime','guards','timers','rules','delegations']:assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
''')
 def test_restart_keeps_changed_password_and_manual_data(self):
  self.run_code('''import server
with server.connection(True) as c:
 c.execute("UPDATE users SET password_hash=? WHERE username='admin1'",(server.password_hash('MiPassword2026!'),))
 c.execute("INSERT INTO accounts(id,code,name) VALUES('manual','MANUAL','Cuenta manual')")
''')
  self.run_code('''import server
from fastapi.testclient import TestClient
c=TestClient(server.app)
assert c.post('/api/login',json={'identity':'admin1','password':'MiPassword2026!'}).status_code==200
assert c.post('/api/login',json={'identity':'admin1','password':'admin12026'}).status_code==401
with server.connection() as db:assert db.execute("SELECT name FROM accounts WHERE id='manual'").fetchone()[0]=='Cuenta manual'
''')
 def test_existing_clean_database_is_not_replaced(self):
  self.run_code('import server',custom=True);self.run_code('''import server
with server.connection() as c:
 assert c.execute('SELECT count(*) FROM users').fetchone()[0]==2
 assert c.execute('SELECT count(*) FROM accounts').fetchone()[0]==0
''')
