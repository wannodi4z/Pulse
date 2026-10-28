"""Explicitly provision the requested Banorte test access in the application's normal DB."""
from pathlib import Path
import sys
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server


def provision():
    created = []
    with server.connection(True) as c:
        account = c.execute("SELECT * FROM accounts WHERE code='BNTE' OR (country_code='MX' AND base_code='BNTE')").fetchone()
        aid = account['id'] if account else server.uid()
        if not account:
            c.execute('INSERT INTO accounts(id,code,name,country_code,base_code) VALUES(?,?,?,?,?)',(aid,'BNTE','Banorte','MX','BNTE'))
        elif not account['country_code']:
            c.execute("UPDATE accounts SET country_code='MX',base_code='BNTE' WHERE id=?",(aid,))
        account=dict(server.get(c,'accounts',aid))
        specs=[('MGR0001','manager12026','MANAGER','Manager',False),('SL0001','lead120261','USER','Lead',True),('951357','tecnico12026','USER','Técnico',False)]
        existing={emp:c.execute('SELECT * FROM users WHERE employee_id=?',(emp,)).fetchone() for emp,*_ in specs}
        for emp,_,role,_,_ in specs:
            user=existing[emp]
            if user and user['role']!=role:
                raise ValueError(f'{emp} ya tiene otro rol. No se modificó ningún usuario.')
            if user and user['status']=='DISABLED':
                raise ValueError(f'{emp} está dado de baja. Reactívalo desde Administración antes de configurar el acceso.')
        manager=existing['MGR0001'];mid=manager['id'] if manager else server.uid()
        if manager and manager['account_id']!=aid:
            raise ValueError('MGR0001 pertenece a otra Cuenta. Usa Organización para transferirlo primero.')
        if not manager:
            c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (mid,'MANAGER','MGR0001','MGR0001','Manager','Pruebas','manager@example.test',aid,'PENDING_ACTIVATION',server.now()))
        groups=[]
        for n,(platform,service,label) in enumerate([('MF','ZOS','z/OS'),('OPEN','LINUX','Linux'),('MF','CICS-MQ','CICS/MQ'),('MF','DB2','Db2'),('OPEN','UNIX','Unix'),('OPEN','ORACLE','Oracle')],1):
            code=f'BNTE-PRUEBA-{n:02}'
            group=c.execute('SELECT * FROM groups WHERE code=?',(code,)).fetchone()
            if group and (group['account_id']!=aid or group['manager_id'] not in (None,mid)):
                raise ValueError(f'{code} ya pertenece a otra Cuenta o Manager. No se modificó.')
            gid=group['id'] if group else server.uid()
            if group:
                c.execute('UPDATE groups SET manager_id=? WHERE id=?',(mid,gid))
            else:
                c.execute('INSERT INTO groups(id,account_id,manager_id,code,name) VALUES(?,?,?,?,?)',(gid,aid,mid,code,f'{label} · Banorte · Pruebas'))
            if not group or not group['service_key']:
                standard=server.standard_group_code(c,account,platform,service,gid)
                c.execute('UPDATE groups SET platform_code=?,service_key=?,standard_code=? WHERE id=?',(platform,service,standard,gid))
            groups.append(gid)
        for emp,password,role,first,lead in specs:
            user=existing[emp]
            identity=user['id'] if user else mid if role=='MANAGER' else server.uid()
            if role=='USER':
                gid=None if lead else groups[1]
                if user and lead and user['manager_id'] not in (None,mid):raise ValueError('SL0001 pertenece a otro Manager.')
                if user and user['group_id'] and not lead:
                    current=server.get(c,'groups',user['group_id'])
                    if current['account_id']!=aid or current['manager_id']!=mid:
                        raise ValueError(f'{emp} está en otro equipo. Usa Organización para transferirlo primero.')
                    gid=user['group_id']  # Keep existing Banorte memberships and all their history.
                if not user:
                    c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,group_id,is_lead,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                              (identity,role,emp,emp,first,'Pruebas',emp+'@example.test',gid,int(lead),'PENDING_ACTIVATION',server.now()))
                else:
                    c.execute('UPDATE users SET group_id=?,is_lead=?,manager_id=? WHERE id=?',(gid,int(lead),mid if lead else None,identity))
                    if user['is_lead'] and not lead:
                        server.revoke_authority(c,None,'Configuración explícita de accesos BNTE',lead_ids=[identity])
            if role=='USER':c.execute('UPDATE users SET manager_id=? WHERE id=?',(mid if lead else None,identity))
            current=server.get(c,'users',identity)
            changed=current['status']!='ACTIVE' or not server.password_matches(password,current['password_hash'])
            if changed:
                c.execute("UPDATE users SET status='ACTIVE',password_hash=?,activation_hash=NULL WHERE id=?",(server.password_hash(password),identity))
                server.invalidate_sessions(c,identity)
                c.execute("UPDATE recoveries SET status='CANCELLED',code_hash=NULL WHERE user_id=? AND status IN ('PENDING','ISSUED')",(identity,))
                c.execute('DELETE FROM recovery_code_vault WHERE recovery_id IN (SELECT id FROM recoveries WHERE user_id=? AND status=\'CANCELLED\')',(identity,))
                server.audit(c,None,'PROVISION_BNTE_TEST_ACCESS',identity,{'employee_id':emp,'account':'BNTE','status':'ACTIVE'})
            created.append({'employee_id':emp,'id':identity,'role':role})
        server.validate_manager_leads(c,[mid])
    return created


if __name__=='__main__':
    try:
        provision()
    except (ValueError,server.HTTPException,sqlite3.IntegrityError) as error:
        message=getattr(error,'detail',str(error))
        raise SystemExit('Configuración no aplicada: '+message) from None
    print('Banorte · BNTE configurada en:',server.DB)
    print('MGR0001 activo: Manager de seis Grupos de prueba: z/OS, CICS/MQ, Db2, Linux, Unix y Oracle.')
    print('SL0001 activo: Lead directo de MGR0001, sin Grupo, sólo OT. 951357 activo: Técnico.')
    print('Contraseñas: las solicitadas. No se crean OT, Guardias, Timers ni delegación.')
