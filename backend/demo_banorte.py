"""Opt-in demo initialization; never merge or overwrite an existing organization.

A locally supplied demo/banorte_organization.json extends the six test accounts.
The organization attachment is not part of the public source repository.
"""
import json
DEMO_PEOPLE=(
 ('DP','DP00001','Eric','Perez','manager12026'),
 ('DPE','DPE0001','Octavio','Lopez','manager12026'),
 ('MANAGER','MGR0001','Yao','Pegueros','manager12026'),
 ('LEAD','SL0001','Francisco Javier','Cervantes Marquez','lead120261'),
 ('USER','951357','Samuel Alejandro','Díaz Chávez','tecnico12026'),
 ('USER','951358','Marco Antonio','Flores Rosas','tecnico12026'),
)
def demo_template(n):
 path=n['ROOT']/'demo'/'banorte_organization.json'
 if path.exists():
  data=json.loads(path.read_text(encoding='utf-8'))
  people=data['people']
 else:
  people=[{'role':role,'employee_id':emp,'first':first,'last':last,'parent_employee_id':None if role=='DP' else 'DP00001' if role=='DPE' else 'DPE0001' if role=='MANAGER' else 'MGR0001'} for role,emp,first,last,_ in DEMO_PEOPLE]
 if not people:raise ValueError('La plantilla de demo no contiene personas.')
 by_id={p['employee_id']:p for p in people}
 if len(by_id)!=len(people):raise ValueError('Identificadores de demo duplicados.')
 parents={'DP':None,'DPE':'DP','MANAGER':'DPE','LEAD':'MANAGER','USER':'MANAGER'}
 for p in people:
  role=p['role'];parent=p.get('parent_employee_id');employee=p['employee_id']
  if role not in parents or not str(employee).strip() or not p['first'].strip() or not p['last'].strip():raise ValueError('Persona de demo inválida.')
  if parents[role] is None:
   if parent:raise ValueError('El DP no tiene padre dentro de la Cuenta.')
  elif parent not in by_id or by_id[parent]['role']!=parents[role]:raise ValueError('Jerarquía de demo inválida.')
 return people

def seed_banorte_demo(n):
 with n['connection'](True) as c:
  if c.execute('SELECT 1 FROM accounts LIMIT 1').fetchone() or c.execute("SELECT 1 FROM users WHERE role!='ADMIN' LIMIT 1").fetchone():return False
  people=demo_template(n);account=n['uid']();ids={p['employee_id']:n['uid']() for p in people}
  c.execute('INSERT INTO accounts(id,code,name,country_code,base_code) VALUES(?,?,?,?,?)',(account,'MX-BNTE','Banorte','MX','BNTE'))
  # Hierarchical order keeps foreign keys enabled throughout initialization.
  order={'DP':0,'DPE':1,'MANAGER':2,'LEAD':3,'USER':3}
  for p in sorted(people,key=lambda p:order[p['role']]):
   role=p['role'];employee=p['employee_id'];parent=ids.get(p.get('parent_employee_id'));password='lead120261' if role=='LEAD' else 'tecnico12026' if role=='USER' else 'manager12026'
   c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,group_id,is_lead,manager_id,parent_id,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
    (ids[employee],'USER' if role=='LEAD' else role,employee,employee,p['first'],p['last'],'',account if role in ('DP','DPE','MANAGER') else None,None,role=='LEAD',parent if role=='LEAD' else None,parent if role in ('DPE','MANAGER') else None,'ACTIVE',n['password_hash'](password),n['now']()))
  for manager in [p for p in people if p['role']=='MANAGER']:
   c.execute('INSERT INTO ot_policies VALUES(?,?,?,?,?)',(ids[manager['employee_id']],1,'21:00','08:00',n['now']()))
   technicians=[p for p in people if p['role']=='USER' and p.get('parent_employee_id')==manager['employee_id']]
   if not technicians:continue
   group=n['uid']();yao=manager['employee_id']=='MGR0001';platform,service=('MF','ZOS') if yao else ('OTHER','GENERAL')
   code=n['standard_group_code'](c,n['get'](c,'accounts',account),platform,service)
   name='Mainframe · Pruebas' if yao else 'Equipo de '+manager['first']+' '+manager['last']
   c.execute('INSERT INTO groups(id,account_id,manager_id,code,name,platform_code,service_key,standard_code) VALUES(?,?,?,?,?,?,?,?)',(group,account,ids[manager['employee_id']],code,name,platform,service,code))
   for p in technicians:c.execute('UPDATE users SET group_id=? WHERE id=?',(group,ids[p['employee_id']]))
  n['validate_manager_leads'](c,[ids[p['employee_id']] for p in people if p['role']=='MANAGER'])
  n['audit'](c,None,'INITIALIZE_BANORTE_TEST_BRANCH',account,{'people':len(people),'hours':0,'purpose':'Requested demo; level-based test roles, Lead assigned separately from job title'})
 return True
