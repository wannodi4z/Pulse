"""Managers own Technician identities, activation and moves; receiving Manager decides transfers."""
import importlib.util,os,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
class ManagerAdministrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();path=Path(self.tmp.name)/'test.db';shutil.copy(ROOT/'fixtures/banorte_pruebas.sqlite3',path)
  with patch.dict(os.environ,{'PULSE_DB_PATH':str(path)}):
   spec=importlib.util.spec_from_file_location('manager_test_server',ROOT/'server.py');self.s=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.s)
  self.m=TestClient(self.s.app);self.other=TestClient(self.s.app);self.admin=TestClient(self.s.app);self.tech=TestClient(self.s.app)
  for c,user,pw in [(self.m,'MGR0001','manager12026'),(self.other,'MGR0003','manager32026'),(self.admin,'admin1','admin12026'),(self.tech,'951357','tecnico12026')]:self.assertEqual(c.post('/api/login',json={'identity':user,'password':pw}).status_code,200)
  self.state=self.m.get('/api/state').json();self.uid=next(p['id'] for p in self.state['people'] if p['employee_id']=='951357');self.gid=next(p['group_id'] for p in self.state['people'] if p['id']==self.uid);self.dest=next(g['id'] for g in self.state['groups'] if g['id']!=self.gid);self.os=self.other.get('/api/state').json();self.og=self.os['groups'][0]['id']
 def tearDown(self):
  for c in (self.m,self.other,self.admin,self.tech):c.close()
  self.tmp.cleanup()
 def data(self,**kw):return {'role':'USER','employee_id':'T-NEW','first':'Técnico','last':'Nuevo','email':'new@example.test','group_id':self.gid,**kw}
 def request(self):
  r=self.m.post('/api/team/transfers',json={'user_id':self.uid,'target_manager_id':self.os['user']['id'],'reason':'Cambio de especialidad'});self.assertEqual(r.status_code,200,r.text);return r.json()['id']
 def test_create_edit_activate_and_regenerate(self):
  r=self.m.post('/api/people',json=self.data());self.assertEqual(r.status_code,200,r.text);uid=r.json()['id'];old=r.json()['activation_code'];new=self.m.post('/api/people/'+uid+'/activation',json={});self.assertEqual(new.status_code,200);self.assertNotEqual(old,new.json()['activation_code']);self.assertEqual(self.tech.post('/api/activate',json={'identity':'T-NEW','code':old,'password':'TechNew2026!'}).status_code,422)
  self.assertEqual(self.tech.post('/api/activate',json={'identity':'T-NEW','code':new.json()['activation_code'],'password':'TechNew2026!'}).status_code,200)
  r=self.m.put('/api/people/'+uid,json=self.data(first='Nombre editado'));self.assertEqual(r.status_code,200,r.text);self.assertEqual(self.m.post('/api/people/'+uid+'/activation',json={}).status_code,422)
 def test_authorization_no_foreign_technicians_or_role_escalation(self):
  for role in ('ADMIN','MANAGER'):
   self.assertEqual(self.m.post('/api/people',json=self.data(role=role)).status_code,403)
  self.assertEqual(self.m.post('/api/people',json=self.data(is_lead=True)).status_code,403)
  self.assertEqual(self.m.post('/api/people',json=self.data(group_id=self.og)).status_code,403)
  self.assertEqual(self.other.put('/api/people/'+self.uid,json=self.data()).status_code,403)
  lead=next(p for p in self.state['people'] if p['is_lead']);self.assertEqual(self.m.put('/api/people/'+lead['id'],json=self.data()).status_code,403)
  self.assertEqual(self.admin.post('/api/people',json=self.data()).status_code,403)
  self.assertEqual(self.tech.post('/api/people',json=self.data()).status_code,403)
 def test_activation_only_own_manager(self):
  r=self.m.post('/api/people',json=self.data()).json()
  for c in (self.other,self.admin,self.tech):self.assertEqual(c.post('/api/people/'+r['id']+'/activation',json={}).status_code,403)
 def test_local_move_preserves_records_origin_and_invalidates_session(self):
  o=self.tech.post('/api/overtime',json={'scheduled_start':'2026-01-05T20:00:00-06:00','scheduled_end':'2026-01-05T22:00:00-06:00','reference':'CHG-MOVE','description':'Trabajo','justification':'Cambio','impact':'Servicio','in_lieu':'Cobertura'});self.assertEqual(o.status_code,200,o.text);oid=o.json()['id']
  with self.s.connection() as c:before=dict(self.s.get(c,'overtime',oid))
  r=self.m.post('/api/team/people/'+self.uid+'/move',json={'group_id':self.dest,'expected_group_id':self.gid,'transfer_reason':'Reorganización'});self.assertEqual(r.status_code,200,r.text)
  with self.s.connection() as c:self.assertEqual(before,dict(self.s.get(c,'overtime',oid)))
  self.assertEqual(self.tech.get('/api/state').status_code,401);self.assertEqual(self.m.get('/api/state').json()['overtime'][0]['origin_info']['group_id'],self.gid)
 def test_admin_cannot_authorize_or_execute_moves(self):
  self.assertEqual(self.admin.post('/api/team/people/'+self.uid+'/move',json={}).status_code,403)
  self.assertEqual(self.admin.post('/api/admin/organization/transfers',json={}).status_code,403)
  self.assertEqual(self.admin.post('/api/admin/people/'+self.uid+'/transfer',json={}).status_code,403)
  malicious=self.data(group_id=self.dest,is_lead=True,_transfer_only=True,expected_group_id=self.gid,transfer_reason='Intento de eludir autorización');self.assertEqual(self.admin.put('/api/people/'+self.uid,json=malicious).status_code,403)
 def test_receiving_manager_accepts_selecting_own_group(self):
  rid=self.request();self.assertEqual(self.m.get('/api/state').json()['people'][0]['id'],self.state['people'][0]['id']);self.assertEqual(len(self.other.get('/api/state').json()['manager_transfers']),1);self.assertEqual(self.admin.get('/api/state').json()['manager_transfers'],[])
  data={'decision':'APPROVED','group_id':self.og,'reason':'Cobertura aceptada'}
  self.assertEqual(self.m.post('/api/team/transfers/'+rid+'/decision',json=data).status_code,403);self.assertEqual(self.admin.post('/api/team/transfers/'+rid+'/decision',json=data).status_code,403)
  self.assertEqual(self.other.post('/api/team/transfers/'+rid+'/decision',json={**data,'group_id':self.gid}).status_code,403)
  r=self.other.post('/api/team/transfers/'+rid+'/decision',json=data);self.assertEqual(r.status_code,200,r.text);self.assertEqual(self.tech.get('/api/state').status_code,401)
  state=self.other.get('/api/state').json();self.assertEqual(next(p for p in state['people'] if p['id']==self.uid)['group_id'],self.og);self.assertEqual(state['manager_transfers'][0]['status'],'APPROVED');self.assertEqual(self.other.post('/api/team/transfers/'+rid+'/decision',json=data).status_code,409)
 def test_reject_cancel_duplicate_and_stale_origin(self):
  rid=self.request();self.assertEqual(self.m.post('/api/team/transfers',json={'user_id':self.uid,'target_manager_id':self.os['user']['id'],'reason':'Duplicado'}).status_code,409)
  self.assertEqual(self.other.post('/api/team/transfers/'+rid+'/decision',json={'decision':'REJECTED','reason':'Sin cobertura'}).status_code,200)
  rid=self.request();self.assertEqual(self.m.post('/api/team/transfers/'+rid+'/decision',json={'decision':'CANCELLED','reason':'Ya no aplica'}).status_code,200)
  rid=self.request();self.assertEqual(self.m.post('/api/team/people/'+self.uid+'/move',json={'group_id':self.dest,'expected_group_id':self.gid,'transfer_reason':'Cambio interno'}).status_code,200);self.assertEqual(self.other.post('/api/team/transfers/'+rid+'/decision',json={'decision':'APPROVED','group_id':self.og,'reason':'Aceptar'}).status_code,409)
 def test_receiver_accept_blocked_while_timer_active(self):
  r=self.tech.post('/api/timers/start',json={});self.assertEqual(r.status_code,200,r.text);rid=self.request()
  r=self.other.post('/api/team/transfers/'+rid+'/decision',json={'decision':'APPROVED','group_id':self.og,'reason':'Aceptar'});self.assertEqual(r.status_code,422,r.text);self.assertEqual(self.other.get('/api/state').json()['manager_transfers'][0]['status'],'SUBMITTED')

 def test_manager_can_create_and_edit_own_groups_but_not_others(self):
  account=self.state['user']['account_id'];data={'account_id':account,'manager_id':self.state['user']['id'],'service_key':'LABORATORIO','name':'Grupo del Manager'}
  r=self.m.post('/api/groups',json=data);self.assertEqual(r.status_code,200,r.text);gid=r.json()['id'];self.assertEqual(self.m.put('/api/groups/'+gid,json={**data,'name':'Nombre actualizado'}).status_code,200)
  self.assertEqual(self.other.put('/api/groups/'+gid,json={**data,'manager_id':self.os['user']['id']}).status_code,403)
  self.assertEqual(self.m.post('/api/groups',json={**data,'manager_id':self.os['user']['id']}).status_code,403)
  self.assertEqual(self.tech.post('/api/groups',json=data).status_code,403)
 def test_cross_account_acceptance_keeps_ot_guard_data_and_origin(self):
  receiver=TestClient(self.s.app);self.assertEqual(receiver.post('/api/login',json={'identity':'MGR0002','password':'manager22026'}).status_code,200);rs=receiver.get('/api/state').json();self.assertNotEqual(rs['user']['account_id'],self.state['user']['account_id'])
  ot=self.tech.post('/api/overtime',json={'scheduled_start':'2026-01-05T20:00:00-06:00','scheduled_end':'2026-01-05T22:00:00-06:00','reference':'CHG-CROSS-ACCOUNT','description':'Cambio','justification':'Servicio','impact':'Operación','in_lieu':'Cobertura'});self.assertEqual(ot.status_code,200,ot.text);oid=ot.json()['id']
  rule=self.m.post('/api/rules',json={'name':'Guardia de origen','effective_from':'2026-01-01','segments':[{'day':0,'start':'20:00','end':'00:00'}]});self.assertEqual(rule.status_code,200,rule.text)
  guard=self.tech.post('/api/guards',json={'rule_id':rule.json()['id'],'start_date':'2026-01-05','end_date':'2026-01-05'});self.assertEqual(guard.status_code,200,guard.text);gid=guard.json()['id']
  with self.s.connection() as c:before={table:dict(self.s.get(c,table,rid)) for table,rid in [('overtime',oid),('guards',gid)]}
  r=self.m.post('/api/team/transfers',json={'user_id':self.uid,'target_manager_id':rs['user']['id'],'reason':'Cambio de Cuenta aceptado por destino'});self.assertEqual(r.status_code,200,r.text)
  result=receiver.post('/api/team/transfers/'+r.json()['id']+'/decision',json={'decision':'APPROVED','group_id':rs['groups'][0]['id'],'reason':'Recepción confirmada'});self.assertEqual(result.status_code,200,result.text)
  with self.s.connection() as c:
   self.assertEqual(before['overtime'],dict(self.s.get(c,'overtime',oid)));self.assertEqual(before['guards'],dict(self.s.get(c,'guards',gid)))
  state=receiver.get('/api/state').json();self.assertEqual(next(o for o in state['overtime'] if o['id']==oid)['origin_info']['group_id'],self.gid)
  self.assertEqual(receiver.post('/api/approvals/ot/'+oid,json={'decision':'APPROVED'}).status_code,200);self.assertEqual(receiver.post('/api/approvals/guard/'+gid,json={'decision':'APPROVED'}).status_code,200)
  report=receiver.get('/api/analytics?month=2026-01').json();self.assertEqual(report['summary']['ot_minutes'],120);self.assertEqual(report['summary']['GUARD'],120);receiver.close()
