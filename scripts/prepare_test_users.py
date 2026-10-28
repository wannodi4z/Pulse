"""Explicit test-only initialization. Never imported by normal application startup."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(os.environ.get('PULSE_TEST_DB_PATH', ROOT/'pruebas'/'operational_pulse.db')).resolve()
if TEST_DB == (ROOT/'operational_pulse.db').resolve():
    raise SystemExit('Usa una base de pruebas separada; no se modifica la base principal.')
os.environ['PULSE_DB_PATH'] = str(TEST_DB)
import server


def prepare():
    with server.connection(True) as c:
        existing = c.execute("SELECT id FROM accounts WHERE code='PULSE-PRUEBAS'").fetchone()
        account = existing['id'] if existing else server.uid()
        if not existing:
            c.execute('INSERT INTO accounts(id,code,name) VALUES(?,?,?)', (account, 'PULSE-PRUEBAS', 'Cuenta de pruebas'))
        manager = c.execute("SELECT * FROM users WHERE employee_id='MGR0001'").fetchone()
        if manager and manager['role'] != 'MANAGER':
            raise ValueError('MGR0001 ya existe con otro rol. No se modificó.')
        manager_id = manager['id'] if manager else server.uid()
        if not manager:
            c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,account_id,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                      (manager_id,'MANAGER','MGR0001','MGR0001','Manager','Pruebas','manager@example.test',account,'ACTIVE',server.password_hash('manager12026'),server.now()))
            server.audit(c,None,'CREATE_TEST_USER',manager_id,{'employee_id':'MGR0001'})
        existing_group = c.execute("SELECT * FROM groups WHERE code='PULSE-GRUPO-PRUEBAS'").fetchone()
        group_id = existing_group['id'] if existing_group else server.uid()
        if not existing_group:
            c.execute('INSERT INTO groups(id,account_id,manager_id,code,name) VALUES(?,?,?,?,?)', (group_id,account,manager_id,'PULSE-GRUPO-PRUEBAS','Grupo de pruebas'))
        for employee,password,first,lead in [('SL0001','lead120261','Lead',1),('951357','tecnico12026','Técnico',0)]:
            user = c.execute('SELECT * FROM users WHERE employee_id=?',(employee,)).fetchone()
            if user:
                if user['role']!='USER':
                    raise ValueError(f'{employee} ya existe con otro rol. No se modificó.')
                continue
            identity = server.uid()
            c.execute('INSERT INTO users(id,role,username,employee_id,first,last,email,group_id,is_lead,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                      (identity,'USER',employee,employee,first,'Pruebas',employee+'@example.test',group_id,lead,'ACTIVE',server.password_hash(password),server.now()))
            server.audit(c,None,'CREATE_TEST_USER',identity,{'employee_id':employee})
    return TEST_DB


if __name__ == '__main__':
    print('Base de pruebas lista:', prepare())
    print('Usuarios iniciales: MGR0001 (Manager), SL0001 (Técnico Lead), 951357 (Técnico).')
    print('Los usuarios ya existentes conservan sus datos y contraseña. No se crea OT, Guardia ni delegación.')
