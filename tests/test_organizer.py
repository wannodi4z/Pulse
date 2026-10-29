"""Legacy Admin batch moves are rejected without affecting records or sessions."""
import unittest
import test_api
class OrganizerTests(unittest.TestCase):
 def setUp(self):
  self.f=test_api.PulseTests();self.f.setUp();self.a,self.g,self.m,self.mc,self.u,self.uc=self.f.organization()
  a2=self.f.account('OTHER');self.g2=self.f.group(a2,'DEST');self.m2,self.mc2,_=self.f.person('MANAGER','M002',account=a2,groups=[self.g2]);self.other,self.oc,_=self.f.person('USER','T002',group=self.g)
 def tearDown(self):self.f.tearDown()
 def payload(self,**extra):return {'reason':'Reorganización de especialidades','moves':[{'user_id':self.u['id'],'from_group_id':self.g,'to_group_id':self.g2},{'user_id':self.other['id'],'from_group_id':self.g,'to_group_id':self.g2}],**extra}
 def test_cross_account_batch_preserves_records_and_updates_authority(self):
  oid=self.f.ot(self.uc)
  rule=self.f.post('/api/rules',{'name':'Noche','effective_from':'2026-01-01','segments':[{'day':0,'start':'20:00','end':'00:00'}]},self.mc)['id']
  guard=self.f.post('/api/guards',{'rule_id':rule,'start_date':'2026-01-05','end_date':'2026-01-05'},self.uc)['id']
  with self.f.server.connection() as c:before={t:dict(self.f.server.get(c,t,rid)) for t,rid in [('overtime',oid),('guards',guard)]}
  r=self.f.client.post('/api/admin/organization/transfers',json=self.payload());self.assertEqual(r.status_code,403)
  for client in (self.uc,self.oc):self.assertEqual(client.get('/api/state').status_code,200)
  with self.f.server.connection() as c:
   self.assertEqual(before['overtime'],dict(self.f.server.get(c,'overtime',oid)));self.assertEqual(before['guards'],dict(self.f.server.get(c,'guards',guard)))
   self.assertEqual(self.f.server.get(c,'users',self.u['id'])['group_id'],self.g)
 def test_timer_failure_rolls_back_all_moves_and_sessions(self):
  self.f.post('/api/timers/start',{},self.oc)
  r=self.f.client.post('/api/admin/organization/transfers',json=self.payload());self.assertEqual(r.status_code,403)
  self.assertEqual(self.uc.get('/api/state').status_code,200)
  self.assertEqual(next(u for u in self.f.client.get('/api/state').json()['people'] if u['id']==self.u['id'])['group_id'],self.g)
 def test_role_stale_source_duplicates_and_lead_rejected(self):
  for client in (self.mc,self.uc):self.assertEqual(client.post('/api/admin/organization/transfers',json=self.payload()).status_code,403)
  data=self.payload();data['moves'][1]['from_group_id']=self.g2
  self.assertEqual(self.f.client.post('/api/admin/organization/transfers',json=data).status_code,403)
  data=self.payload();data['moves'][1]=data['moves'][0]
  self.assertEqual(self.f.client.post('/api/admin/organization/transfers',json=data).status_code,403)
  lead,_,_=self.f.person('USER','L001',group=self.g,lead=True)
  data=self.payload(moves=[{'user_id':lead['id'],'from_group_id':self.g,'to_group_id':self.g2}])
  self.assertEqual(self.f.client.post('/api/admin/organization/transfers',json=data).status_code,403)
  self.assertEqual(self.f.client.post('/api/admin/organization/transfers',json=self.payload(reason='')).status_code,403)
  self.assertEqual(self.uc.get('/api/state').status_code,200)
