"""Requested BNTE access is provisioned in-place without replacing existing records."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
import test_api

ROOT=Path(__file__).resolve().parents[1]


class BanorteSetupTests(unittest.TestCase):
    def setUp(self):
        self.f=test_api.PulseTests();self.f.setUp()

    def tearDown(self):
        self.f.tearDown()

    def run_setup(self):
        return subprocess.run([sys.executable,'scripts/prepare_banorte_users.py'],cwd=ROOT,env={**os.environ,'PULSE_DB_PATH':str(self.f.server.DB)},capture_output=True,text=True)

    def test_fresh_banorte_users_are_active_and_setup_is_idempotent(self):
        result=self.run_setup();self.assertEqual(result.returncode,0,result.stderr)
        for employee,password,role,lead in [('MGR0001','manager12026','MANAGER',False),('SL0001','lead120261','USER',True),('951357','tecnico12026','USER',False)]:
            user=self.f.login(self.f.client,employee,password)
            self.assertEqual(user['status'],'ACTIVE');self.assertEqual(user['role'],role);self.assertEqual(bool(user['is_lead']),lead)
            self.assertEqual(self.f.client.get('/api/state').json()['can_approve'],role=='MANAGER')
        with self.f.server.connection() as c:
            account=dict(c.execute("SELECT * FROM accounts WHERE code='BNTE'").fetchone());self.assertEqual(account['name'],'Banorte');self.assertEqual(account['country_code'],'MX')
            before=[dict(r) for r in c.execute('SELECT * FROM users ORDER BY id')]
            groups=[dict(r) for r in c.execute('SELECT * FROM groups')];self.assertEqual(len(groups),6)
            manager=next(u for u in before if u['employee_id']=='MGR0001')
            self.assertTrue(all(g['account_id']==account['id'] and g['manager_id']==manager['id'] for g in groups))
            for table in ['overtime','guards','timers','rules','delegations','ot_extensions']:
                self.assertEqual(c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
        self.assertEqual(self.run_setup().returncode,0)
        with self.f.server.connection() as c:
            self.assertEqual(before,[dict(r) for r in c.execute('SELECT * FROM users ORDER BY id')])
            self.assertEqual(c.execute('SELECT count(*) FROM groups').fetchone()[0],6)

    def test_existing_banorte_memberships_names_and_history_are_preserved(self):
        account=self.f.account('BNTE');group=self.f.group(account,'MANUAL')
        manager,_,_=self.f.person('MANAGER','MGR0001',account=account,groups=[group])
        lead,_,_=self.f.person('USER','SL0001',group=group,lead=True)
        tech,tc,_=self.f.person('USER','951357',group=group)
        ot=self.f.ot(tc)
        other_account=self.f.account('OTHER');other_group=self.f.group(other_account,'OTHER')
        other,_,_=self.f.person('USER','UNRELATED',group=other_group)
        with self.f.server.connection() as c:
            unrelated=dict(c.execute('SELECT * FROM users WHERE id=?',(other['id'],)).fetchone())
        result=self.run_setup();self.assertEqual(result.returncode,0,result.stderr)
        with self.f.server.connection() as c:
            self.assertEqual(unrelated,dict(c.execute('SELECT * FROM users WHERE id=?',(other['id'],)).fetchone()))
            self.assertIsNotNone(c.execute('SELECT id FROM overtime WHERE id=?',(ot,)).fetchone())
            for original in (lead,tech):
                saved=dict(c.execute('SELECT * FROM users WHERE id=?',(original['id'],)).fetchone())
                self.assertEqual(saved['group_id'],group);self.assertEqual(saved['first'],original['first']);self.assertEqual(saved['last'],original['last'])
            self.assertEqual(c.execute('SELECT count(*) FROM groups WHERE manager_id=?',(manager['id'],)).fetchone()[0],7)
        self.f.login(tc,'951357','tecnico12026')

    def test_foreign_account_conflict_rolls_back_everything(self):
        other=self.f.account('OTHER')
        self.f.person('MANAGER','MGR0001',account=other)
        result=self.run_setup();self.assertNotEqual(result.returncode,0)
        with self.f.server.connection() as c:
            self.assertIsNone(c.execute("SELECT id FROM accounts WHERE code='BNTE'").fetchone())
            self.assertIsNone(c.execute("SELECT id FROM users WHERE employee_id='SL0001'").fetchone())
            self.assertEqual(c.execute('SELECT count(*) FROM groups').fetchone()[0],0)
