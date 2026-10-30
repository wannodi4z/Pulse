"""The delivered test bundle works without running a configurator and never replaces user data."""
import json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BundledExamplesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        shutil.copy(ROOT/'server.py',self.root/'server.py')
        for directory in ('backend','frontend','fixtures'):
            shutil.copytree(ROOT/directory,self.root/directory,ignore=shutil.ignore_patterns('__pycache__'))
    def tearDown(self):self.temp.cleanup()
    def run_code(self,code,custom=False):
        env={k:v for k,v in os.environ.items() if k!='PULSE_DB_PATH'}
        if custom:env['PULSE_DB_PATH']=str(self.root/'operational_pulse.db')
        r=subprocess.run([sys.executable,'-c',code],cwd=self.root,env=env,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr);return r.stdout
    def test_new_bundle_has_all_three_active_logins_without_setup(self):
        self.run_code('''import server
from fastapi.testclient import TestClient
c=TestClient(server.app)
for emp,pw in [('MGR0001','manager12026'),('SL0001','lead120261'),('951357','tecnico12026'),('MGR0002','manager22026'),('SL0002','lead220261'),('TEC0012','tecnico12026'),('MGR0003','manager32026'),('MGR0004','manager42026'),('SL0003','lead320261'),('SL0004','lead420261')]:
 r=c.post('/api/login',json={'identity':emp,'password':pw});assert r.status_code==200,r.text
 assert r.json()['user']['status']=='ACTIVE'
 if emp=='SL0001':assert r.json()['user']['group_id'] is None and r.json()['user']['is_lead']
with server.connection() as db:
 assert db.execute('SELECT count(*) FROM groups').fetchone()[0]==15
 assert tuple(db.execute("SELECT first,last FROM users WHERE employee_id='951357'").fetchone())==('Samuel Alejandro','Díaz Chávez')
 assert db.execute('SELECT count(*) FROM accounts').fetchone()[0]==2
 for aid, in db.execute('SELECT id FROM accounts'):
  assert db.execute("SELECT count(*) FROM users WHERE role='MANAGER' AND account_id=?",(aid,)).fetchone()[0]==2
 assert db.execute("SELECT count(*) FROM users WHERE is_lead=1 AND group_id IS NULL").fetchone()[0]==4
 assert db.execute('SELECT count(*) FROM overtime').fetchone()[0]>0
 assert db.execute('SELECT count(*) FROM guards').fetchone()[0]>0
 assert db.execute('SELECT count(*) FROM timers WHERE end_at IS NULL').fetchone()[0]==0
 assert db.execute("SELECT count(*) FROM overtime o JOIN users u ON u.id=o.user_id WHERE u.employee_id='951357' AND coalesce(o.start_at,o.scheduled_start)<'2026-11-01' AND coalesce(o.end_at,o.scheduled_end)>'2026-10-01'").fetchone()[0]==0
 for t in ['recoveries','delegations']:assert db.execute('SELECT count(*) FROM '+t).fetchone()[0]==0
''')
    def test_restart_keeps_changed_password_and_manual_data(self):
        self.run_code('''import server
with server.connection(True) as c:
 c.execute("UPDATE users SET password_hash=? WHERE employee_id='951357'",(server.password_hash('MiPassword2026!'),))
 c.execute("INSERT INTO accounts(id,code,name) VALUES('manual','MANUAL','Cuenta manual')")
''')
        self.run_code('''import server
from fastapi.testclient import TestClient
c=TestClient(server.app)
assert c.post('/api/login',json={'identity':'951357','password':'MiPassword2026!'}).status_code==200
assert c.post('/api/login',json={'identity':'951357','password':'tecnico12026'}).status_code==401
with server.connection() as db:assert db.execute("SELECT name FROM accounts WHERE id='manual'").fetchone()[0]=='Cuenta manual'
''')
    def test_existing_clean_database_is_not_replaced(self):
        self.run_code('import server',custom=True)
        self.run_code('''import server
with server.connection() as c:
 assert c.execute('SELECT count(*) FROM users').fetchone()[0]==2
 assert c.execute('SELECT count(*) FROM accounts').fetchone()[0]==0
''')
