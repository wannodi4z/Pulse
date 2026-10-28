"""Direct Manager backup: own OT, no new Guards, delegated team approvals and stable data."""
import unittest
import test_api
class DirectLeadTests(unittest.TestCase):
    def setUp(self):
        self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.uc=self.f.organization()
        self.data={'role':'USER','employee_id':'SL0001','first':'Lead','last':'Directo','email':'lead@example.test','is_lead':True,'manager_id':self.m['id']}
        r=self.f.post('/api/people',self.data);self.lid=r['id'];self.lc=type(self.f.client)(self.f.server.app)
        self.f.post('/api/activate',{'identity':'SL0001','code':r['activation_code'],'password':'lead120261'},self.lc);self.f.login(self.lc,'SL0001','lead120261')
    def tearDown(self):self.lc.close();self.f.tearDown()
    def test_direct_assignment_ot_and_guard_authorization(self):
        state=self.lc.get('/api/state').json();self.assertIsNone(state['user']['group_id']);self.assertEqual(state['user']['manager_id'],self.m['id']);self.assertFalse(state['can_approve'])
        duplicate=self.f.client.post('/api/people',json={**self.data,'employee_id':'SL0002'});self.assertEqual(duplicate.status_code,422)
        own=self.f.ot(self.lc);self.assertEqual(self.lc.post('/api/guards',json={}).status_code,403)
        self.assertEqual(self.lc.get('/api/analytics?month=2026-01').status_code,403)
        self.assertEqual(self.lc.post('/api/approvals/ot/'+own,json={'decision':'APPROVED'}).status_code,403)
        self.f.approve(self.mc,'ot',own)
        self.assertEqual(self.lc.get('/api/my-analytics?month=2026-01').json()['summary']['ot_minutes'],120)
        self.assertEqual(self.mc.get('/api/analytics?month=2026-01').json()['summary']['ot_minutes'],120)
        self.assertEqual(self.lc.get('/api/export.xlsx?month=2026-01').status_code,200)
    def test_delegation_covers_other_groups_but_never_own_ot(self):
        g2=self.f.group(self.a,'G2',self.m['id']);other,oc,_=self.f.person('USER','T002',group=g2);oid=self.f.ot(oc)
        own=self.f.ot(self.lc);d=self.f.post('/api/delegations',{'lead_id':self.lid},self.mc)['id']
        self.assertTrue(self.lc.get('/api/state').json()['can_approve']);self.f.approve(self.lc,'ot',oid)
        self.assertEqual(self.lc.post('/api/approvals/ot/'+own,json={'decision':'APPROVED'}).status_code,403)
        rule=self.f.post('/api/rules',{'name':'Noche','effective_from':'2026-01-01','segments':[{'day':0,'start':'20:00','end':'00:00'}]},self.mc)['id']
        guard=self.f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},oc)['id'];self.f.approve(self.lc,'guard',guard)
        self.mc.delete('/api/delegations/'+d);self.assertFalse(self.lc.get('/api/state').json()['can_approve']);self.assertTrue(self.lc.get('/api/state').json()['user']['is_lead'])
    def test_move_to_another_manager_keeps_ot_and_revokes_authority(self):
        m2,mc2,_=self.f.person('MANAGER','M002',account=self.a)
        own=self.f.ot(self.lc);self.f.post('/api/delegations',{'lead_id':self.lid},self.mc)
        result=self.f.client.put('/api/people/'+self.lid,json={**self.data,'manager_id':m2['id'],'transfer_reason':'Nuevo responsable'})
        self.assertEqual(result.status_code,200,result.text);self.assertEqual(self.lc.get('/api/state').status_code,401)
        self.f.login(self.lc,'SL0001','lead120261');state=self.lc.get('/api/state').json();self.assertFalse(state['can_approve']);self.assertIsNone(state['user']['group_id']);self.assertEqual(state['user']['manager_id'],m2['id'])
        self.assertEqual(state['overtime'][0]['origin_info']['manager_id'],self.m['id'])
        self.assertFalse(any(o['id']==own for o in self.mc.get('/api/state').json()['overtime']));self.f.approve(mc2,'ot',own)
    def test_recovery_is_only_for_administrators(self):
        _,other,_=self.f.person('MANAGER','M002',account=self.a)
        self.f.post('/api/recoveries',{'identity':'SL0001'},self.lc)
        self.assertEqual(self.mc.get('/api/state').json()['recoveries'],[])
        self.assertEqual(other.get('/api/state').json()['recoveries'],[])
        self.assertEqual(len(self.f.client.get('/api/state').json()['recoveries']),1)
        rid=self.f.client.get('/api/state').json()['recoveries'][0]['id']
        self.assertEqual(self.mc.post('/api/recoveries/'+rid+'/issue',json={}).status_code,403)
        self.assertEqual(self.f.client.post('/api/recoveries/'+rid+'/issue',json={}).status_code,200)
    def test_catalogue_custom_specialty_without_platform(self):
        a=self.f.post('/api/accounts',{'code':'CUSTOM','name':'Cuenta personalizada','country_code':'MX'})['id']
        d={'account_id':a,'service_key':'Linux y Oracle','specialty_name':'Linux y Oracle','name':'Distribuidos Producción'}
        first=self.f.post('/api/groups',d)['id'];second=self.f.post('/api/groups',d)['id'];state=self.f.client.get('/api/state').json()
        groups={g['id']:g for g in state['groups']};self.assertEqual(groups[first]['display_code'],'MX-CUSTOM-LINUX-Y-ORACLE');self.assertEqual(groups[second]['display_code'],'MX-CUSTOM-LINUX-Y-ORACLE-02')
        self.assertEqual(len([s for s in state['specialties'] if s['account_id']==a]),1)

    def test_upgrade_preserves_previous_group_lead_records(self):
        m2,_,_=self.f.person('MANAGER','M002',account=self.a)
        gid=self.f.group(self.a,'LEGACY',m2['id']);legacy,lc,_=self.f.person('USER','OLDLEAD',group=gid)
        oid=self.f.ot(lc)
        with self.f.server.connection(True) as c:
            before=dict(self.f.server.get(c,'overtime',oid));c.execute('UPDATE users SET is_lead=1 WHERE id=?',(legacy['id'],))
        self.f.server.init_db()
        with self.f.server.connection() as c:
            saved=self.f.server.get(c,'users',legacy['id']);self.assertIsNone(saved['group_id']);self.assertEqual(saved['manager_id'],m2['id'])
            self.assertEqual(before,dict(self.f.server.get(c,'overtime',oid)))
        self.f.server.init_db()
        self.assertEqual(lc.get('/api/state').status_code,200)
