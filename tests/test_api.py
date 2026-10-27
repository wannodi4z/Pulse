"""Functional tests run against a disposable SQLite database, never the user's local data."""
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


class PulseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        with patch.dict(os.environ, {'PULSE_DB_PATH': str(Path(self.temp.name) / 'test.db')}):
            spec = importlib.util.spec_from_file_location('pulse_test_server', ROOT / 'server.py')
            self.server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.server)
        self.client = TestClient(self.server.app)
        self.login(self.client, 'admin1', 'admin12026')

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def login(self, client, username, password='Password2026!'):
        result = client.post('/api/login', json={'identity': username, 'password': password})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['user']

    def post(self, path, data, client=None):
        result = (client or self.client).post(path, json=data)
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def account(self, code='AC'):
        return self.post('/api/accounts', {'code': code, 'name': 'Cuenta ' + code})['id']

    def group(self, account, code='G1', manager=None):
        return self.post('/api/groups', {'code': code, 'name': 'Grupo ' + code, 'account_id': account, 'manager_id': manager})['id']

    def person(self, role, emp, account=None, group=None, groups=None, lead=False):
        data = {'role': role, 'employee_id': emp, 'username': emp, 'first': 'Persona', 'last': emp, 'email': emp+'@example.test', 'account_id': account, 'group_id': group, 'group_ids': groups or [], 'is_lead': lead}
        r = self.post('/api/people', data)
        c = TestClient(self.server.app)
        self.post('/api/activate', {'identity': emp, 'code': r['activation_code'], 'password': 'Password2026!'}, c)
        user = self.login(c, emp)
        return user, c, data

    def organization(self):
        a = self.account()
        g = self.group(a)
        m, mc, md = self.person('MANAGER', 'M001', account=a, groups=[g])
        u, uc, ud = self.person('USER', 'T001', group=g)
        return a, g, m, mc, u, uc

    def ot(self, client, start='2026-01-05T23:00:00-06:00', end='2026-01-06T01:00:00-06:00', **extra):
        return self.post('/api/overtime', {'capture_type': 'HISTORICAL', 'scheduled_start': start, 'scheduled_end': end, 'reference': 'CHG123456', 'description': 'Trabajo aprobado', 'justification': 'Cambio requerido', 'impact': 'Servicio', 'in_lieu': 'Cobertura', **extra}, client)['id']

    def approve(self, manager, kind, identity):
        return self.post(f'/api/approvals/{kind}/{identity}', {'decision': 'APPROVED'}, manager)

    def test_clean_bootstrap_and_reinitialization(self):
        with self.server.connection() as c:
            users = self.server.rows(c, 'users')
            self.assertEqual({u['username'] for u in users}, {'admin1', 'admin2'})
            for table in ['accounts', 'groups', 'overtime', 'guards', 'timers', 'rules', 'windows', 'delegations', 'recoveries']:
                self.assertEqual(c.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 0, table)
        a = self.account()
        self.server.init_db()
        self.assertEqual(self.client.get('/api/state').json()['accounts'][0]['id'], a)
        text = self.client.get('/api/state').text
        self.assertNotIn('password_hash', text)
        self.assertNotIn('activation_hash', text)
        self.assertEqual(TestClient(self.server.app).get('/api/state').status_code, 401)

    def test_hierarchy_ownership_cross_account_and_delete(self):
        a, b = self.account(), self.account('OTHER')
        g1, g2, g3 = self.group(a), self.group(a, 'G2'), self.group(b, 'G3')
        m, mc, data = self.person('MANAGER', 'M001', account=a, groups=[g1, g2])
        m2, _, d2 = self.person('MANAGER', 'M002', account=a)
        r = self.client.put('/api/people/'+m2['id'], json={**d2,'group_ids':[g1]})
        self.assertEqual(r.status_code, 422)
        r = self.client.put('/api/people/'+m['id'], json={**data,'group_ids':[g1,g3]})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.client.delete('/api/accounts/'+a).status_code, 422)
        empty = self.account('EMPTY')
        self.assertEqual(self.client.delete('/api/accounts/'+empty).status_code, 200)
        state = self.client.get('/api/state').json()
        self.assertEqual(len([p for p in state['people'] if p['role']=='MANAGER' and p['account_id']==a]),2)
        self.assertEqual(len([g for g in state['groups'] if g['manager_id']==m['id']]),2)
        self.assertEqual(mc.post('/api/accounts',json={'name':'Bad','code':'BAD'}).status_code,403)

    def test_one_lead_moves_and_independent_delegation(self):
        a=self.account();g1=self.group(a);g2=self.group(a,'G2')
        m,mc,_=self.person('MANAGER','M001',account=a,groups=[g1,g2])
        lead,lc,d1=self.person('USER','L001',group=g1,lead=True)
        other,oc,d2=self.person('USER','L002',group=g2,lead=True)
        tech,tc,d3=self.person('USER','T003',group=g1)
        self.assertEqual(self.client.put('/api/people/'+tech['id'],json={**d3,'is_lead':True}).status_code,422)
        self.assertEqual(self.client.put('/api/people/'+lead['id'],json={**d1,'group_id':g2}).status_code,422)
        self.assertFalse(lc.get('/api/state').json()['can_approve'])
        future=(self.server.datetime.now(self.server.timezone.utc)+self.server.timedelta(hours=3)).isoformat()
        start=(self.server.datetime.now(self.server.timezone.utc)-self.server.timedelta(minutes=1)).isoformat()
        d=self.post('/api/delegations',{'lead_id':lead['id'],'group_ids':[g1],'start_at':start,'end_at':future},mc)
        self.assertTrue(lc.get('/api/state').json()['can_approve'])
        own=self.ot(lc)
        self.assertEqual(lc.post('/api/approvals/ot/'+own,json={'decision':'APPROVED'}).status_code,403)
        target=self.ot(tc)
        self.approve(lc,'ot',target)
        denied=self.ot(oc)
        self.assertEqual(lc.post('/api/approvals/ot/'+denied,json={'decision':'APPROVED'}).status_code,403)
        self.assertEqual(mc.delete('/api/delegations/'+d['id']).status_code,200)
        s=lc.get('/api/state').json();self.assertFalse(s['can_approve']);self.assertTrue(s['user']['is_lead'])
        self.assertEqual(self.client.put('/api/people/'+lead['id'],json={**d1,'is_lead':False}).status_code,200)
        self.assertEqual(self.client.put('/api/people/'+tech['id'],json={**d3,'is_lead':True}).status_code,200)

    def test_multiple_weekday_intervals_full_sunday_and_net_guard(self):
        _, _, _, mc, u, uc = self.organization()
        segments = [{'day': day, 'start': start, 'end': end} for day in range(5) for start, end in [('02:00', '04:00'), ('20:00', '00:00')]]
        segments += [{'day': 5, 'start': '00:00', 'end': '08:00'}, {'day': 5, 'start': '15:00', 'end': '00:00'}, {'day': 6, 'start': '00:00', 'end': '00:00'}]
        rule = self.post('/api/rules', {'name': 'Cobertura por intervalos', 'effective_from': '2026-01-01', 'segments': segments}, mc)['id']
        saved = next(r for r in mc.get('/api/state').json()['rules'] if r['id'] == rule)
        self.assertEqual(saved['segments'], segments)
        self.assertEqual(len(saved['segments']), 13)
        guard = self.post('/api/guards', {'rule_id': rule, 'start_date': '2026-01-05', 'end_date': '2026-01-11'}, uc)['id']
        self.approve(mc, 'guard', guard)
        result = uc.get('/api/accounting?month=2026-01').json()
        self.assertEqual(result['guard_minutes'], 71*60)
        self.assertEqual(sum(r['minutes'] for r in result['rows'] if r['date']=='2026-01-11'), 24*60)
        overtime = self.ot(uc, '2026-01-05T20:30:00-06:00', '2026-01-05T22:30:00-06:00')
        self.approve(mc, 'ot', overtime)
        result = uc.get('/api/accounting?month=2026-01').json()
        self.assertEqual(result['ot_minutes'], 120)
        self.assertEqual(result['guard_minutes'], 69*60)
        self.assertEqual(mc.post('/api/rules', json={'name':'Invalid', 'effective_from':'2026-01-01', 'segments':[{'day':0,'start':'30:00','end':'04:00'}]}).status_code,422)
        self.assertEqual(mc.post('/api/rules', json={'name':'Invalid', 'effective_from':'2026-01-01', 'segments':'bad'}).status_code,422)

    def test_single_backup_atomic_replacement_and_history(self):
        a = self.account(); g1 = self.group(a); g2 = self.group(a, 'G2')
        manager, mc, _ = self.person('MANAGER', 'M001', account=a, groups=[g1,g2])
        first, c1, _ = self.person('USER', 'L001', group=g1, lead=True)
        second, c2, _ = self.person('USER', 'L002', group=g2, lead=True)
        start=(self.server.datetime.now(self.server.timezone.utc)-self.server.timedelta(minutes=1)).isoformat()
        end=(self.server.datetime.now(self.server.timezone.utc)+self.server.timedelta(hours=2)).isoformat()
        data={'lead_id':first['id'],'group_ids':[g1,g2],'start_at':start,'end_at':end}
        old=self.post('/api/delegations',data,mc)['id']
        self.assertTrue(c1.get('/api/state').json()['can_approve'])
        self.assertEqual(mc.post('/api/delegations',json={**data,'lead_id':second['id']}).status_code,409)
        # Invalid replacements roll back without revoking the current backup.
        self.assertEqual(mc.post('/api/delegations',json={**data,'lead_id':'missing','replace_current':True}).status_code,404)
        self.assertTrue(c1.get('/api/state').json()['can_approve'])
        latest=self.post('/api/delegations',{**data,'lead_id':second['id'],'replace_current':True},mc)['id']
        self.assertFalse(c1.get('/api/state').json()['can_approve'])
        self.assertTrue(c2.get('/api/state').json()['can_approve'])
        records=mc.get('/api/state').json()['delegations']
        self.assertEqual(len(records),2)
        self.assertTrue(next(d for d in records if d['id']==old)['revoked_at'])
        self.assertEqual(len([d for d in records if not d['revoked_at']]),1)
        self.assertEqual(c1.post('/api/delegations',json=data).status_code,403)
        self.assertEqual(mc.delete('/api/delegations/'+latest).status_code,200)
        self.assertFalse(c2.get('/api/state').json()['can_approve'])
        self.assertTrue(c1.get('/api/state').json()['user']['is_lead'])
        self.assertTrue(c2.get('/api/state').json()['user']['is_lead'])

    def test_legacy_multiple_backups_never_grant_simultaneous_authority(self):
        a=self.account();g1=self.group(a);g2=self.group(a,'G2')
        manager,mc,_=self.person('MANAGER','M001',account=a,groups=[g1,g2])
        first,c1,_=self.person('USER','L001',group=g1,lead=True)
        second,c2,_=self.person('USER','L002',group=g2,lead=True)
        start=(self.server.datetime.now(self.server.timezone.utc)-self.server.timedelta(minutes=1)).isoformat()
        end=(self.server.datetime.now(self.server.timezone.utc)+self.server.timedelta(hours=2)).isoformat()
        import json
        with self.server.connection(True) as c:
            for identity,lead in [('old',first),('latest',second)]:
                c.execute('INSERT INTO delegations VALUES(?,?,?,?,?,?,NULL)',(identity,manager['id'],lead['id'],json.dumps([g1,g2]),start,end))
        self.server.init_db()
        self.assertEqual(len(mc.get('/api/state').json()['delegations']),2)
        self.assertFalse(c1.get('/api/state').json()['can_approve'])
        self.assertTrue(c2.get('/api/state').json()['can_approve'])
        self.assertEqual(mc.delete('/api/delegations/latest').status_code,200)
        self.assertFalse(c1.get('/api/state').json()['can_approve'])
        self.assertFalse(c2.get('/api/state').json()['can_approve'])
        self.assertEqual(len(mc.get('/api/state').json()['delegations']),2)

    def test_accounting_midnight_guard_net_unique_ot_and_excel(self):
        _,_,_,mc,u,uc=self.organization()
        rule=self.post('/api/rules',{'name':'Noche','effective_from':'2026-01-01','segments':[{'day':0,'start':'22:00','end':'06:00'}]},mc)['id']
        guard=self.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},uc)['id']
        guard2=self.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},uc)['id']
        self.assertNotEqual(guard,guard2)
        self.approve(mc,'guard',guard);self.approve(mc,'guard',guard2)
        ot=self.ot(uc);self.approve(mc,'ot',ot)
        duplicate=uc.post('/api/overtime',json={'capture_type':'HISTORICAL','scheduled_start':'2026-01-05T23:00:00-06:00','scheduled_end':'2026-01-06T01:00:00-06:00','reference':'INC123','description':'Duplicada'})
        self.assertEqual(duplicate.status_code,409)
        r=uc.get('/api/accounting?month=2026-01').json()
        self.assertEqual(r['ot_minutes'],120);self.assertEqual(r['guard_minutes'],360)
        self.assertEqual(len([x for x in r['rows'] if x['kind']=='OT']),2)
        self.assertEqual({x['date'] for x in r['rows']},{'2026-01-05','2026-01-06'})
        ot2=self.ot(uc,'2026-01-06T00:30:00-06:00','2026-01-06T02:00:00-06:00');self.approve(mc,'ot',ot2)
        r=uc.get('/api/accounting?month=2026-01').json();self.assertEqual(r['ot_minutes'],180);self.assertEqual(r['guard_minutes'],300)
        response=uc.get('/api/export.xlsx?month=2026-01');self.assertEqual(response.status_code,200)
        wb=load_workbook(io.BytesIO(response.content));self.assertEqual(wb.sheetnames,['Tiempo aprobado','Resumen'])
        values=list(wb['Tiempo aprobado'].values)[1:];self.assertAlmostEqual(sum(row[8] for row in values),8)
        filtered=uc.get('/api/export.xlsx?month=2026-01&kind=OT')
        wb2=load_workbook(io.BytesIO(filtered.content));self.assertTrue(all(row[4]=='Onsite Overtime' for row in list(wb2.active.values)[1:]))

    def test_timer_emergency_documentation_reapproval_and_history(self):
        _,_,_,mc,u,uc=self.organization()
        with patch.object(self.server,'now',return_value='2026-01-06T05:00:00+00:00'):
            timer=self.post('/api/timers/start',{},uc)['id']
        self.assertEqual(uc.post('/api/timers/start',json={}).status_code,422)
        self.assertEqual(mc.post(f'/api/timers/{timer}/stop',json={}).status_code,403)
        with patch.object(self.server,'now',return_value='2026-01-06T07:00:00+00:00'):
            self.post(f'/api/timers/{timer}/stop',{},uc)
        state=uc.get('/api/state').json();o=state['overtime'][0];self.assertEqual(o['status'],'DOCUMENTATION');self.assertFalse(state['timers'])
        self.assertEqual(mc.post('/api/approvals/ot/'+o['id'],json={'decision':'APPROVED'}).status_code,422)
        data={'reference':'INC1000','description':'Emergencia','justification':'Servicio','impact':'Interrupción','in_lieu':'No aplica'}
        self.assertEqual(uc.put('/api/overtime/'+o['id'],json=data).status_code,200)
        self.approve(mc,'ot',o['id'])
        self.assertEqual(uc.get('/api/accounting?month=2026-01').json()['ot_minutes'],120)
        self.assertEqual(uc.put('/api/overtime/'+o['id'],json={**data,'description':'Actualizada'}).status_code,200)
        self.assertEqual(uc.get('/api/accounting?month=2026-01').json()['ot_minutes'],0)
        self.approve(mc,'ot',o['id'])
        self.assertTrue(any(a['action']=='EDIT_OT_REOPEN_APPROVAL' for a in uc.get('/api/state').json()['audit']))
        self.assertTrue(any(a['action']=='APPROVED' for a in uc.get('/api/state').json()['audit']))

    def test_shared_planned_individual_participations(self):
        _,gid,_,mc,u,uc=self.organization()
        u2,c2,_=self.person('USER','T002',group=gid)
        current=self.server.datetime.now(self.server.timezone.utc)
        a=(current-self.server.timedelta(minutes=5)).isoformat();b=(current+self.server.timedelta(hours=1)).isoformat()
        w=self.post('/api/windows',{'group_id':gid,'scheduled_start':a,'scheduled_end':b,'reference':'CHG9000','description':'Cambio compartido'},mc)['id']
        one=self.post(f'/api/windows/{w}/join',{},uc)['id'];two=self.post(f'/api/windows/{w}/join',{},c2)['id'];self.assertNotEqual(one,two)
        self.assertEqual(uc.post(f'/api/windows/{w}/join',json={}).status_code,409)
        t1=self.post('/api/timers/start',{'overtime_id':one},uc)['id'];t2=self.post('/api/timers/start',{'overtime_id':two},c2)['id']
        self.assertEqual(len(mc.get('/api/state').json()['timers']),2)
        self.post(f'/api/timers/{t1}/stop',{},uc);self.post(f'/api/timers/{t2}/stop',{},c2)
        self.assertTrue(all(o['status']=='SUBMITTED' for o in mc.get('/api/state').json()['overtime']))

    def test_activation_recovery_password_and_session_invalidation(self):
        _,_,_,mc,u,uc=self.organization()
        self.post('/api/recoveries',{'identity':'T001'},TestClient(self.server.app))
        r=mc.get('/api/state').json()['recoveries'][0]
        code=self.post('/api/recoveries/'+r['id']+'/issue',{},mc)['code']
        public=TestClient(self.server.app)
        self.post('/api/recoveries/complete',{'identity':'T001','code':code,'password':'NewPassword2026!'},public)
        self.assertEqual(uc.get('/api/state').status_code,401)
        self.assertEqual(public.post('/api/recoveries/complete',json={'identity':'T001','code':code,'password':'Different2026!'}).status_code,422)
        self.login(uc,'T001','NewPassword2026!')
        self.assertEqual(uc.put('/api/password',json={'current':'wrong','password':'FinalPassword2026!'}).status_code,422)
        self.assertEqual(uc.put('/api/password',json={'current':'NewPassword2026!','password':'FinalPassword2026!'}).status_code,200)
        self.assertEqual(uc.get('/api/state').status_code,401)
        self.login(uc,'T001','FinalPassword2026!')

    def test_authorization_no_state_overwrite_and_external_origin(self):
        a,g,m,mc,u,uc=self.organization()
        a2=self.account('SECRET');g2=self.group(a2,'SECRET-G')
        outsider,oc,_=self.person('USER','PRIVATE',group=g2)
        self.assertNotIn(outsider['id'],{p['id'] for p in uc.get('/api/state').json()['people']})
        self.assertEqual(uc.get('/api/accounting?month=2026-01&user_id='+outsider['id']).status_code,403)
        self.assertEqual(uc.put('/api/state',json={}).status_code,405)
        self.assertEqual(self.client.post('/api/accounts',json={'code':'BAD','name':'Bad'},headers={'origin':'https://evil.test'}).status_code,403)
        self.assertEqual(self.client.get('/').headers['x-frame-options'],'DENY')
        for p in ['server.py','operational_pulse.db','requirements.txt']:
            self.assertEqual(self.client.get('/'+p).status_code,404)


if __name__=='__main__':
    unittest.main(verbosity=2)
