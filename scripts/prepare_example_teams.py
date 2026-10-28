"""Explicit example setup: two Accounts, two Managers per Account and one Lead per Manager."""
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
        bnte=c.execute("SELECT id FROM accounts WHERE base_code='BNTE' AND country_code='MX'").fetchone()['id']
        def user(emp,role,first,last,password,*,account=None,group=None,manager=None,lead=False):
            old=c.execute('SELECT * FROM users WHERE employee_id=?',(emp,)).fetchone()
            if old:
                if old['role']!=role:raise ValueError(emp+' ya existe con otro rol.')
                if role=='MANAGER' and old['account_id']!=account:raise ValueError(emp+' pertenece a otra Cuenta. No se trasladó.')
                return old['id']  # Preserve existing passwords, memberships, status and records.
            identity=server.uid()
            c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,group_id,is_lead,status,password_hash,created_at,manager_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(identity,role,emp,emp,first,last,emp.lower()+'@example.test',account,group,int(lead),'ACTIVE',server.password_hash(password),server.now(),manager))
            server.audit(c,None,'PROVISION_EXAMPLE_TEAM',identity,{'employee_id':emp})
            return identity
        m2=user('MGR0002','MANAGER','Mariana','Torres','manager22026',account=aid)
        m3=user('MGR0003','MANAGER','Roberto','Salinas','manager32026',account=bnte)
        m4=user('MGR0004','MANAGER','Patricia','Ramos','manager42026',account=aid)
        for emp,first,last,password,mid in [('SL0002','Luis','Navarro','lead220261',m2),('SL0003','Valeria','Mendoza','lead320261',m3),('SL0004','Diego','Ortega','lead420261',m4)]:
            user(emp,'USER',first,last,password,manager=mid,lead=True)
        def groups_for(account_id,mid,specs):
            ac=server.get(c,'accounts',account_id);result=[]
            for key,label in specs:
                existing=c.execute('SELECT * FROM groups WHERE account_id=? AND manager_id=? AND service_key=?',(account_id,mid,key)).fetchone()
                gid=existing['id'] if existing else server.uid()
                if not existing:
                    code=server.standard_group_code(c,ac,'',key)
                    c.execute('INSERT INTO groups(id,account_id,manager_id,code,name,service_key,standard_code) VALUES(?,?,?,?,?,?,?)',(gid,account_id,mid,code,label,key,code))
                    c.execute('INSERT OR IGNORE INTO specialties VALUES(?,?,?,?)',(server.uid(),account_id,key,key.title()))
                result.append(gid)
            return result
        g2=groups_for(aid,m2,[('LINUX','Linux · Producción'),('ORACLE','Oracle · Bases de datos'),('CLOUD','Cloud · Operación')])
        g3=groups_for(bnte,m3,[('CICS-MQ','CICS y MQ · Aplicaciones'),('DB2','Db2 · Desarrollo'),('STORAGE','Almacenamiento')])
        g4=groups_for(aid,m4,[('UNIX','Unix · Operación'),('WINDOWS','Windows · Plataforma'),('POSTGRESQL','PostgreSQL · Bases de datos')])
        bg=[g['id'] for g in c.execute("SELECT id FROM groups WHERE account_id=? AND code LIKE 'BNTE-PRUEBA-%' ORDER BY code",(bnte,))]
        for i,(first,last) in enumerate([('Ana','López'),('Carlos','Medina'),('Elena','Ruiz'),('Jorge','Santos'),('Paola','Ríos')],2):
            user(f'TEC{i:04}','USER',first,last,'tecnico12026',group=bg[i-2] if i<4 else g3[i-4])
        for i,(first,last) in enumerate([('Andrea','Vega'),('Diego','Cruz'),('Fernanda','Mora'),('Miguel','Reyes'),('Sofía','Castro'),('Ricardo','Luna')],7):
            user(f'TEC{i:04}','USER',first,last,'tecnico12026',group=g2[i-7] if i<10 else g4[i-10])
        server.validate_manager_leads(c,[m2,m3,m4])
    return {'accounts':2,'managers':4,'leads':4,'technicians':12}

if __name__=='__main__':
    print(provision())
