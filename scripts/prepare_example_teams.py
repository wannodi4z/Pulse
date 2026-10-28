"""Explicit example setup: two Accounts, two Managers, two direct Leads and twelve Technicians."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.prepare_banorte_users import provision as provision_banorte
import server

def provision():
    provision_banorte()
    with server.connection(True) as c:
        account=c.execute("SELECT * FROM accounts WHERE country_code='MX' AND base_code='ACME'").fetchone()
        aid=account['id'] if account else server.uid()
        if not account:c.execute('INSERT INTO accounts(id,code,name,country_code,base_code) VALUES(?,?,?,?,?)',(aid,'MX-ACME','Acme México','MX','ACME'))
        def user(emp,role,first,last,password,*,account=None,group=None,manager=None,lead=False):
            old=c.execute('SELECT * FROM users WHERE employee_id=?',(emp,)).fetchone()
            if old:
                if old['role']!=role:raise ValueError(emp+' ya existe con otro rol.')
                return old['id']  # Preserve manual access, passwords, moves and status on rerun.
            identity=server.uid()
            c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,group_id,is_lead,status,password_hash,created_at,manager_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(identity,role,emp,emp,first,last,emp.lower()+'@example.test',account,group,int(lead),'ACTIVE',server.password_hash(password),server.now(),manager))
            server.audit(c,None,'PROVISION_EXAMPLE_TEAM',identity,{'employee_id':emp})
            return identity
        mid=user('MGR0002','MANAGER','Mariana','Torres','manager22026',account=aid)
        user('SL0002','USER','Luis','Navarro','lead220261',manager=mid,lead=True)
        ac=server.get(c,'accounts',aid);groups=[]
        for key,label in [('LINUX','Linux · Producción'),('ORACLE','Oracle · Bases de datos'),('CLOUD','Cloud · Operación')]:
            existing=c.execute('SELECT * FROM groups WHERE account_id=? AND service_key=?',(aid,key)).fetchone()
            gid=existing['id'] if existing else server.uid()
            if not existing:
                code=server.standard_group_code(c,ac,'',key)
                c.execute('INSERT INTO groups(id,account_id,manager_id,code,name,service_key,standard_code) VALUES(?,?,?,?,?,?,?)',(gid,aid,mid,code,label,key,code))
                c.execute('INSERT OR IGNORE INTO specialties VALUES(?,?,?,?)',(server.uid(),aid,key,key.title()))
            groups.append(gid)
        bnte=c.execute("SELECT id FROM accounts WHERE base_code='BNTE' AND country_code='MX'").fetchone()['id']
        bg=[g['id'] for g in c.execute('SELECT id FROM groups WHERE account_id=? ORDER BY code',(bnte,))]
        for i,(first,last) in enumerate([('Ana','López'),('Carlos','Medina'),('Elena','Ruiz'),('Jorge','Santos'),('Paola','Ríos')],2):
            user(f'TEC{i:04}','USER',first,last,'tecnico12026',group=bg[(i-2)%len(bg)])
        for i,(first,last) in enumerate([('Andrea','Vega'),('Diego','Cruz'),('Fernanda','Mora'),('Miguel','Reyes'),('Sofía','Castro'),('Ricardo','Luna')],7):
            user(f'TEC{i:04}','USER',first,last,'tecnico12026',group=groups[(i-7)%len(groups)])
        server.validate_manager_leads(c,[mid])
    return {'accounts':2,'managers':2,'leads':2,'technicians':12}

if __name__=='__main__':
    print(provision())
