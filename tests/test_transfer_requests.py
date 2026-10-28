"""Manager requests, Admin execution, and attached records preserved atomically."""
import unittest
import test_api

class TransferRequestTests(unittest.TestCase):
    def setUp(self):
        self.f=test_api.PulseTests();self.f.setUp()
        self.a,self.g,self.m,self.mc,self.u,self.uc=self.f.organization()
        self.dest=self.f.group(self.a,'ORACLE');self.m2,self.mc2,_=self.f.person('MANAGER','M002',account=self.a,groups=[self.dest])
    def tearDown(self):self.f.tearDown()
    def request(self):return self.f.post('/api/transfer-requests',{'user_id':self.u['id'],'destination':'Oracle con M002','reason':'Cambio de especialidad'},self.mc)['id']
    def move(self,r):return self.f.client.post('/api/admin/people/'+self.u['id']+'/transfer',json={'group_id':self.dest,'expected_group_id':self.g,'transfer_reason':'Solicitud revisada','transfer_request_id':r})
    def test_records_and_snapshots_follow_technician_after_admin_executes(self):
        oid=self.f.ot(self.uc)
        rid=self.f.post('/api/rules',{'name':'Cobertura','effective_from':'2026-01-01','segments':[{'day':0,'start':'00:00','end':'00:00'}]},self.mc)['id']
        guard=self.f.post('/api/guards',{'rule_id':rid,'start_date':'2026-01-05','end_date':'2026-01-05'},self.uc)['id']
        with self.f.server.connection() as c:
            oldot=dict(self.f.server.get(c,'overtime',oid));oldguard=dict(self.f.server.get(c,'guards',guard))
        r=self.request()
        before=self.mc.get('/api/state').json();self.assertEqual(next(p for p in before['people'] if p['id']==self.u['id'])['group_id'],self.g)
        self.assertEqual(len(before['transfer_requests']),1)
        self.assertEqual(self.move(r).status_code,200)
        with self.f.server.connection() as c:
            self.assertEqual(oldot,dict(self.f.server.get(c,'overtime',oid)));self.assertEqual(oldguard,dict(self.f.server.get(c,'guards',guard)))
            resolved=self.f.server.get(c,'transfer_requests',r);self.assertEqual(resolved['status'],'APPROVED');self.assertEqual(resolved['destination_group_id'],self.dest)
        previous=self.mc.get('/api/state').json()
        self.assertFalse(any(o['id']==oid for o in previous['overtime']))
        request=next(rq for rq in previous['transfer_requests'] if rq['id']==r)
        self.assertIn('T001',request['user_name']);self.assertEqual(request['employee_id'],'T001')
        new=self.mc2.get('/api/state').json();self.assertTrue(any(o['id']==oid for o in new['overtime']));self.assertTrue(any(g['id']==guard for g in new['guards']))
        self.f.login(self.uc,'T001')
        own=self.uc.get('/api/state').json();record=next(o for o in own['overtime'] if o['id']==oid)
        self.assertEqual(record['origin_info']['group_id'],self.g);self.assertFalse(record['origin_info']['inferred'])
        self.f.approve(self.mc2,'ot',oid)
        self.assertEqual(self.move(r).status_code,409)
    def test_roles_duplicates_reject_and_stale_request(self):
        data={'user_id':self.u['id'],'destination':'Oracle','reason':'Solicitud'}
        self.assertEqual(self.uc.post('/api/transfer-requests',json=data).status_code,403)
        self.assertEqual(self.mc2.post('/api/transfer-requests',json=data).status_code,403)
        r=self.request();self.assertEqual(self.mc.post('/api/transfer-requests',json=data).status_code,409)
        self.assertEqual(self.mc.post('/api/admin/people/'+self.u['id']+'/transfer',json={'group_id':self.dest}).status_code,403)
        self.assertEqual(self.mc2.get('/api/state').json()['transfer_requests'],[])
        rejected=self.f.client.post('/api/admin/transfer-requests/'+r+'/reject',json={'reason':'Pendiente cobertura'});self.assertEqual(rejected.status_code,200)
        self.assertEqual(self.move(r).status_code,409)
        r2=self.request();self.assertEqual(self.move(r2).status_code,200)
    def test_running_timer_blocks_execution_and_leaves_request_pending(self):
        r=self.request();timer=self.f.post('/api/timers/start',{},self.uc)
        self.assertEqual(self.move(r).status_code,422)
        with self.f.server.connection() as c:
            self.assertEqual(self.f.server.get(c,'transfer_requests',r)['status'],'SUBMITTED')
            self.assertEqual(self.f.server.get(c,'users',self.u['id'])['group_id'],self.g)
        self.f.post('/api/timers/'+timer['id']+'/stop',{},self.uc)
        self.assertEqual(self.move(r).status_code,200)
