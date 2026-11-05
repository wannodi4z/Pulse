"""Executive approval does not grant time approval; structural movements are atomic."""
import unittest
from fastapi.testclient import TestClient
import test_api

class OrganizationTransferTests(unittest.TestCase):
 def setUp(self):
  self.f=test_api.PulseTests();self.f.setUp();self.s=self.f.server
  self.a,self.g,self.m,self.mc,self.u,self.tc=self.f.organization();self.b=self.f.account('OTHER');self.f.client.put('/api/accounts/'+self.b,json={'code':'OTHER','name':'Cuenta OTHER','country_code':'MX'});self.g2=self.f.group(self.b,'G2');self.target,self.target_client,_=self.f.person('MANAGER','TARGET',account=self.b,groups=[self.g2])
  self.clients={}
  with self.s.connection() as c:
   self.dpe=dict(c.execute('SELECT * FROM users WHERE id=?',(self.target['parent_id'],)).fetchone())
   reviewers=[dict(r) for r in c.execute("SELECT * FROM users WHERE role IN ('DP','DPE')")]
  for row in reviewers:
   client=TestClient(self.s.app);self.f.login(client,row['username']);self.clients[row['id']]=client
 def tearDown(self):self.f.tearDown()
 def request(self,**change):
  plan={'subject_id':self.m['id'],'target_id':self.dpe['id'],'groups':{self.g:'FOLLOW'},'lead_target':'FOLLOW',**change}
  preview=self.f.post('/api/organization-transfers/preview',plan);r=self.f.post('/api/organization-transfers',{**plan,'fingerprint':preview['fingerprint'],'reason':'Cambio de responsabilidad'})
  return r['id'],preview
 def authorize(self,identity,preview):
  for reviewer in preview['reviewers']:
   r=self.clients[reviewer['id']].post('/api/organization-transfers/'+identity+'/decision',json={'decision':'APPROVED','reason':'Revisado equipo e impacto'});self.assertEqual(r.status_code,200,r.text)
 def test_four_approvals_then_atomic_move_and_history(self):
  record=self.f.ot(self.tc);self.f.approve(self.mc,'ot',record)
  lead,lc,_=self.f.person('USER','LEAD',group=self.g,lead=True);self.f.post('/api/delegations',{'lead_id':lead['id']},self.mc)
  identity,preview=self.request();self.assertEqual(len(preview['reviewers']),4)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,409)
  self.authorize(identity,preview)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,200)
  with self.s.connection() as c:
   self.assertEqual(self.s.get(c,'users',self.m['id'])['account_id'],self.b);self.assertEqual(self.s.get(c,'groups',self.g)['account_id'],self.b)
   self.assertEqual(self.s.get(c,'users',self.u['id'])['group_id'],self.g);self.assertEqual(self.s.get(c,'overtime',record)['status'],'APPROVED')
   self.assertFalse(self.s.effective_delegations(c));self.assertIsNotNone(c.execute('SELECT snapshot FROM record_origins WHERE record_id=?',(record,)).fetchone());self.assertFalse(c.execute('PRAGMA foreign_key_check').fetchall())
  self.assertEqual(self.mc.get('/api/state').status_code,200);self.assertEqual(self.tc.get('/api/state').status_code,200)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,409)
 def test_lead_move_rejection_and_executive_cannot_approve_time(self):
  lead,lc,_=self.f.person('USER','LEAD',group=self.g,lead=True)
  identity,preview=self.request(subject_id=lead['id'],target_id=self.target['id'],groups={})
  reviewer=preview['reviewers'][0]['id'];client=self.clients[reviewer]
  self.assertEqual(client.post('/api/approvals/ot/fake',json={'decision':'APPROVED'}).status_code,403)
  self.assertEqual(self.mc.post('/api/organization-transfers/'+identity+'/decision',json={'decision':'APPROVED','reason':'No autorizado'}).status_code,403)
  r=client.post('/api/organization-transfers/'+identity+'/decision',json={'decision':'REJECTED','reason':'Pendiente reorganización'});self.assertEqual(r.status_code,200,r.text)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,409)
  with self.s.connection() as c:self.assertEqual(self.s.get(c,'users',lead['id'])['manager_id'],self.m['id'])
 def test_active_timer_blocks_and_structural_change_invalidates(self):
  identity,preview=self.request();self.authorize(identity,preview)
  timer=self.f.post('/api/timers/start',{},self.tc)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,409)
  self.f.post('/api/timers/'+timer['id']+'/stop',{},self.tc)
  self.f.person('USER','NEW-TECH',group=self.g)
  self.assertEqual(self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True}).status_code,409)
  self.assertTrue(next(r for r in self.f.client.get('/api/organization-transfers').json() if r['id']==identity)['stale'])
 def test_groups_and_lead_can_stay_with_origin_manager(self):
  replacement,rc,_=self.f.person('MANAGER','REPLACEMENT',account=self.a)
  lead,lc,_=self.f.person('USER','LEAD-STAY',group=self.g,lead=True)
  identity,preview=self.request(groups={self.g:replacement['id']},lead_target=replacement['id'])
  self.authorize(identity,preview)
  response=self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True});self.assertEqual(response.status_code,200,response.text)
  with self.s.connection() as c:
   group=self.s.get(c,'groups',self.g);self.assertEqual(group['account_id'],self.a);self.assertEqual(group['manager_id'],replacement['id'])
   self.assertEqual(self.s.get(c,'users',lead['id'])['manager_id'],replacement['id']);self.assertEqual(self.s.get(c,'users',self.u['id'])['group_id'],self.g)
   self.assertEqual(self.s.get(c,'users',self.m['id'])['account_id'],self.b)
 def test_shared_executives_decide_once_for_lead_transfer(self):
  replacement,rc,_=self.f.person('MANAGER','SAME-DPE',account=self.a)
  lead,lc,_=self.f.person('USER','LEAD-SAME',group=self.g,lead=True)
  identity,preview=self.request(subject_id=lead['id'],target_id=replacement['id'],groups={})
  self.assertEqual(len(preview['reviewers']),2)
  self.assertTrue(all(p['sides']==['Origen','Destino'] for p in preview['reviewers']))
  self.authorize(identity,preview)
  response=self.f.client.post('/api/organization-transfers/'+identity+'/apply',json={'confirm':True});self.assertEqual(response.status_code,200,response.text)
  with self.s.connection() as c:self.assertEqual(self.s.get(c,'users',lead['id'])['manager_id'],replacement['id'])
  self.assertEqual(lc.get('/api/state').status_code,200)
 def test_direct_changes_are_blocked(self):
  self.assertEqual(self.f.client.put('/api/people/'+self.m['id'],json={**self.m,'account_id':self.b,'parent_id':self.dpe['id']}).status_code,422)
  lead,lc,data=self.f.person('USER','LEAD',group=self.g,lead=True)
  self.assertEqual(self.f.client.put('/api/people/'+lead['id'],json={**data,'manager_id':self.target['id']}).status_code,422)

if __name__=='__main__':unittest.main()
