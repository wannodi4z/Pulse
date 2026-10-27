"""Operational Pulse 2.0: server-owned authorization, SQLite transactions and time accounting."""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

VERSION = '1.0.0'
ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('PULSE_DB_PATH', ROOT / 'operational_pulse.db'))
TZ = ZoneInfo(os.environ.get('PULSE_TIMEZONE', 'America/Mexico_City'))
SESSION_SECONDS = 8 * 3600
app = FastAPI(title='Operational Pulse', version=VERSION)


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def uid():
    return uuid.uuid4().hex


def fail(message, status=422):
    raise HTTPException(status_code=status, detail=message)


def password_hash(value):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', value.encode(), salt, 260000)
    return base64.b64encode(salt + digest).decode()


def password_matches(value, stored):
    try:
        raw = base64.b64decode(stored)
        return hmac.compare_digest(raw[16:], hashlib.pbkdf2_hmac('sha256', value.encode(), raw[:16], 260000))
    except (ValueError, TypeError):
        return False


@contextmanager
def connection(write=False):
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    try:
        if write:
            c.execute('BEGIN IMMEDIATE')
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connection(True) as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY, code TEXT UNIQUE COLLATE NOCASE NOT NULL, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS groups(id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id), manager_id TEXT REFERENCES users(id), code TEXT UNIQUE COLLATE NOCASE NOT NULL, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, role TEXT NOT NULL CHECK(role IN ('ADMIN','MANAGER','USER')), username TEXT UNIQUE COLLATE NOCASE NOT NULL, employee_id TEXT UNIQUE COLLATE NOCASE, first TEXT NOT NULL, last TEXT NOT NULL, email TEXT NOT NULL, account_id TEXT REFERENCES accounts(id), group_id TEXT REFERENCES groups(id), is_lead INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL, password_hash TEXT, activation_hash TEXT, created_at TEXT NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS one_lead ON users(group_id) WHERE is_lead=1;
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS delegations(id TEXT PRIMARY KEY, manager_id TEXT NOT NULL REFERENCES users(id), lead_id TEXT NOT NULL REFERENCES users(id), group_ids TEXT NOT NULL, start_at TEXT NOT NULL, end_at TEXT NOT NULL, revoked_at TEXT);
        CREATE TABLE IF NOT EXISTS rules(id TEXT PRIMARY KEY, manager_id TEXT NOT NULL REFERENCES users(id), name TEXT NOT NULL, effective_from TEXT NOT NULL, segments TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS windows(id TEXT PRIMARY KEY, group_id TEXT NOT NULL REFERENCES groups(id), created_by TEXT NOT NULL REFERENCES users(id), scheduled_start TEXT NOT NULL, scheduled_end TEXT NOT NULL, reference TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS overtime(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), window_id TEXT REFERENCES windows(id), capture_type TEXT NOT NULL, scheduled_start TEXT, scheduled_end TEXT, start_at TEXT, end_at TEXT, reference TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', justification TEXT NOT NULL DEFAULT '', impact TEXT NOT NULL DEFAULT '', in_lieu TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, execution TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 0, approved_by TEXT REFERENCES users(id), created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS unique_actual_ot ON overtime(user_id,start_at,end_at) WHERE start_at IS NOT NULL AND end_at IS NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS unique_participation ON overtime(user_id,window_id) WHERE window_id IS NOT NULL;
        CREATE TABLE IF NOT EXISTS timers(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), overtime_id TEXT NOT NULL REFERENCES overtime(id), start_at TEXT NOT NULL, end_at TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_timer ON timers(user_id) WHERE end_at IS NULL;
        CREATE TABLE IF NOT EXISTS guards(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), start_date TEXT NOT NULL, end_date TEXT NOT NULL, rule_snapshot TEXT NOT NULL, status TEXT NOT NULL, approved_by TEXT REFERENCES users(id), created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS recoveries(id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), status TEXT NOT NULL, code_hash TEXT, expires_at TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY, actor_id TEXT REFERENCES users(id), action TEXT NOT NULL, entity_id TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS login_attempts(identity TEXT PRIMARY KEY, failures INTEGER NOT NULL, locked_until TEXT);
        ''')
        # Only a genuinely new database receives bootstrap administrators. Existing data is never reset.
        if c.execute('SELECT count(*) FROM users').fetchone()[0] == 0 and c.execute('SELECT count(*) FROM audit').fetchone()[0] == 0:
            for n, surname in [(1, 'Principal'), (2, 'Respaldo')]:
                c.execute('INSERT INTO users(id,role,username,first,last,email,status,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                          (uid(), 'ADMIN', f'admin{n}', 'Administrador', surname, f'admin{n}@operationalpulse.local', 'ACTIVE', password_hash(f'admin{n}2026'), now()))


init_db()


def rows(c, table):
    return [dict(r) for r in c.execute(f'SELECT * FROM {table}')]


def get(c, table, identity):
    row = c.execute(f'SELECT * FROM {table} WHERE id=?', (identity,)).fetchone()
    if row is None:
        fail('No se encontró el registro.', 404)
    return dict(row)


def audit(c, actor, action, entity, detail=''):
    c.execute('INSERT INTO audit VALUES(?,?,?,?,?,?)', (uid(), actor['id'] if actor else None, action, entity, json.dumps(detail, ensure_ascii=False), now()))


def public_user(u):
    return {k: v for k, v in dict(u).items() if k not in ('password_hash', 'activation_hash')}


def current_user(request: Request):
    token = request.cookies.get('pulse_session', '')
    hashed = hashlib.sha256(token.encode()).hexdigest()
    with connection() as c:
        row = c.execute('SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>? AND u.status=?', (hashed, now(), 'ACTIVE')).fetchone()
        if row is None:
            fail('Inicia sesión para continuar.', 401)
        return dict(row)


def admin(user=Depends(current_user)):
    if user['role'] != 'ADMIN':
        fail('Esta acción requiere una cuenta administradora.', 403)
    return user


def scope(c, user):
    if user['role'] == 'ADMIN':
        return {g['id'] for g in rows(c, 'groups')}
    if user['role'] == 'MANAGER':
        return {r[0] for r in c.execute('SELECT id FROM groups WHERE manager_id=?', (user['id'],))}
    ids = set()
    if user['is_lead']:
        for d in c.execute('SELECT * FROM delegations WHERE lead_id=? AND revoked_at IS NULL AND start_at<=? AND end_at>?', (user['id'], now(), now())):
            allowed = {r[0] for r in c.execute('SELECT id FROM groups WHERE manager_id=?', (d['manager_id'],))}
            own = c.execute('SELECT manager_id FROM groups WHERE id=?', (user['group_id'],)).fetchone()
            if own and own[0] == d['manager_id']:
                ids.update(set(json.loads(d['group_ids'])) & allowed)
    return ids


def operational(user):
    if user['role'] != 'USER':
        fail('Esta función es para Técnicos.', 403)


def authorized_target(c, actor, target, approval=False):
    if actor['role'] == 'ADMIN' and not approval:
        return
    if target['group_id'] not in scope(c, actor) or (approval and target['id'] == actor['id']):
        fail('No tienes autoridad sobre este registro.', 403)


def text(data, key, required=True):
    value = str(data.get(key, '')).strip()
    if required and not value:
        fail('Completa los campos obligatorios.')
    if len(value) > 4000:
        fail('El texto es demasiado largo.')
    return value


def parse_at(value):
    try:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=TZ)
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        fail('La fecha y hora no son válidas.')


def interval(data, a, b):
    start, end = parse_at(data.get(a)), parse_at(data.get(b))
    if end <= start:
        fail('El fin debe ser posterior al inicio.')
    if end - start > timedelta(days=31):
        fail('El intervalo no puede exceder 31 días.')
    return start.isoformat(), end.isoformat()


def valid_reference(data):
    import re
    ref = text(data, 'reference').upper()
    if not re.fullmatch(r'(CHG|INC)[A-Z0-9-]+', ref):
        fail('Usa una referencia completa CHG o INC.')
    return ref


def invalidate_sessions(c, identity):
    c.execute('DELETE FROM sessions WHERE user_id=?', (identity,))


@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        origin = request.headers.get('origin')
        if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
            return Response('Origen no permitido.', status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return Response('Origen no permitido.', status_code=403)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    response.headers['X-Operational-Pulse-Build'] = VERSION
    return response


@app.exception_handler(sqlite3.IntegrityError)
async def integrity_error(request, exc):
    return __import__('fastapi').responses.JSONResponse(status_code=409, content={'detail': 'El registro está duplicado o tiene relaciones que impiden guardar el cambio.'})


@app.get('/api/health')
def health():
    with connection() as c:
        c.execute('SELECT 1').fetchone()
    return {'status': 'ok', 'version': VERSION, 'timezone': str(TZ)}


@app.post('/api/login')
def login(response: Response, request: Request, data: dict = Body(...)):
    identity = text(data, 'identity').lower()
    password = text(data, 'password')
    with connection(True) as c:
        attempt = c.execute('SELECT * FROM login_attempts WHERE identity=?', (identity,)).fetchone()
        if attempt and attempt['locked_until'] and attempt['locked_until'] > now():
            fail('Demasiados intentos. Espera 15 minutos.', 429)
        u = c.execute('SELECT * FROM users WHERE username=? COLLATE NOCASE OR employee_id=? COLLATE NOCASE', (identity, identity)).fetchone()
        good = u and u['status'] == 'ACTIVE' and password_matches(password, u['password_hash'])
        if not good:
            failures = (attempt['failures'] if attempt and (not attempt['locked_until'] or attempt['locked_until'] > now()) else 0) + 1
            lock = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat() if failures >= 8 else None
            c.execute('INSERT INTO login_attempts VALUES(?,?,?) ON CONFLICT(identity) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until', (identity, failures, lock))
        else:
            c.execute('DELETE FROM login_attempts WHERE identity=?', (identity,))
            token = secrets.token_urlsafe(40)
            c.execute('DELETE FROM sessions WHERE expires_at<=?', (now(),))
            c.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), u['id'], (datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS)).isoformat()))
            audit(c, dict(u), 'LOGIN', u['id'])
    if not good:
        fail('Usuario o contraseña incorrectos, o cuenta pendiente de activación.', 401)
    response.set_cookie('pulse_session', token, max_age=SESSION_SECONDS, httponly=True, samesite='strict', secure=request.url.scheme == 'https')
    return {'user': public_user(u)}


@app.post('/api/logout')
def logout(request: Request, response: Response):
    token = request.cookies.get('pulse_session', '')
    with connection(True) as c:
        c.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie('pulse_session')
    return {'ok': True}


@app.post('/api/activate')
def activate(data: dict = Body(...)):
    identity, code, password = text(data, 'identity'), text(data, 'code'), text(data, 'password')
    if len(password) < 10:
        fail('La contraseña debe tener al menos 10 caracteres.')
    with connection(True) as c:
        u = c.execute('SELECT * FROM users WHERE username=? COLLATE NOCASE', (identity,)).fetchone()
        if not u or u['status'] != 'PENDING_ACTIVATION' or not password_matches(code, u['activation_hash']):
            fail('La cuenta o el código de activación no son válidos.')
        c.execute("UPDATE users SET status='ACTIVE',password_hash=?,activation_hash=NULL WHERE id=?", (password_hash(password), u['id']))
        audit(c, dict(u), 'ACTIVATE', u['id'])
    return {'ok': True}


@app.get('/api/state')
def state(user=Depends(current_user)):
    with connection() as c:
        group_ids = scope(c, user)
        people = rows(c, 'users')
        visible = {p['id'] for p in people if p['id'] == user['id'] or p['group_id'] in group_ids}
        if user['role'] == 'ADMIN':
            visible = {p['id'] for p in people}
        groups = rows(c, 'groups')
        own_ids = group_ids | ({user['group_id']} if user['group_id'] else set())
        shown_groups = groups if user['role'] == 'ADMIN' else [g for g in groups if g['id'] in own_ids]
        accounts = rows(c, 'accounts')
        visible_entities = visible | {r['id'] for table in ('overtime', 'guards', 'timers') for r in rows(c, table) if r['user_id'] in visible}
        result = {'user': public_user(user), 'can_approve': user['role'] == 'MANAGER' or bool(group_ids) and user['role'] == 'USER', 'scope': list(group_ids), 'version': VERSION, 'timezone': str(TZ), 'server_time': now(),
                  'accounts': accounts if user['role'] == 'ADMIN' else [a for a in accounts if any(g['account_id'] == a['id'] for g in shown_groups)],
                  'groups': shown_groups, 'people': [public_user(p) for p in people if p['id'] in visible or p['role'] == 'MANAGER' and any(g['manager_id'] == p['id'] for g in shown_groups)],
                  'overtime': [r for r in rows(c, 'overtime') if r['user_id'] in visible],
                  'guards': [r for r in rows(c, 'guards') if r['user_id'] in visible],
                  'timers': [r for r in rows(c, 'timers') if r['user_id'] in visible and not r['end_at']],
                  'windows': [r for r in rows(c, 'windows') if user['role'] == 'ADMIN' or r['group_id'] in own_ids],
                  'rules': [dict(r, segments=json.loads(r['segments'])) for r in rows(c, 'rules') if user['role'] == 'ADMIN' or r['manager_id'] == user['id'] or any(g['manager_id'] == r['manager_id'] for g in shown_groups)],
                  'delegations': [dict(d, group_ids=json.loads(d['group_ids'])) for d in rows(c, 'delegations') if user['role'] == 'ADMIN' or d['manager_id'] == user['id'] or d['lead_id'] == user['id']],
                  'recoveries': [r for r in rows(c, 'recoveries') if user['role'] == 'ADMIN' or next((p for p in people if p['id'] == r['user_id']), {}).get('group_id') in group_ids] if user['role'] != 'USER' or group_ids else [],
                  'audit': [a for a in rows(c, 'audit') if user['role'] == 'ADMIN' or a['actor_id'] in visible or a['entity_id'] in visible_entities][-300:]}
        for g in result['guards']:
            g['rule_snapshot'] = json.loads(g['rule_snapshot'])
        for r in result['recoveries']:
            r.pop('code_hash', None)
        return result


@app.post('/api/accounts')
@app.put('/api/accounts/{identity}')
def save_account(data: dict = Body(...), identity: str = '', actor=Depends(admin)):
    code, name = text(data, 'code').upper(), text(data, 'name')
    with connection(True) as c:
        if identity:
            get(c, 'accounts', identity)
            c.execute('UPDATE accounts SET code=?,name=? WHERE id=?', (code, name, identity))
        else:
            identity = uid()
            c.execute('INSERT INTO accounts VALUES(?,?,?)', (identity, code, name))
        audit(c, actor, 'SAVE_ACCOUNT', identity)
    return {'id': identity}


@app.delete('/api/accounts/{identity}')
def delete_account(identity: str, actor=Depends(admin)):
    with connection(True) as c:
        get(c, 'accounts', identity)
        if c.execute('SELECT 1 FROM groups WHERE account_id=?', (identity,)).fetchone():
            fail('La Cuenta contiene Grupos. Muévelos o elimínalos primero.')
        if c.execute('SELECT 1 FROM users WHERE account_id=?', (identity,)).fetchone():
            fail('La Cuenta contiene Managers. Muévelos primero.')
        c.execute('DELETE FROM accounts WHERE id=?', (identity,))
        audit(c, actor, 'DELETE_ACCOUNT', identity)
    return {'ok': True}


@app.post('/api/groups')
@app.put('/api/groups/{identity}')
def save_group(data: dict = Body(...), identity: str = '', actor=Depends(admin)):
    aid, mid = text(data, 'account_id'), data.get('manager_id') or None
    with connection(True) as c:
        get(c, 'accounts', aid)
        old = get(c, 'groups', identity) if identity else None
        if mid:
            m = get(c, 'users', mid)
            if m['role'] != 'MANAGER' or m['account_id'] != aid:
                fail('El Manager debe pertenecer a la misma Cuenta que el Grupo.')
        if old:
            c.execute('UPDATE groups SET code=?,name=?,account_id=?,manager_id=? WHERE id=?', (text(data, 'code').upper(), text(data, 'name'), aid, mid, identity))
            if old['manager_id'] != mid:
                # A change of Manager never silently transfers delegated approval rights.
                for d in rows(c, 'delegations'):
                    if identity in json.loads(d['group_ids']) and not d['revoked_at']:
                        c.execute('UPDATE delegations SET revoked_at=? WHERE id=?', (now(), d['id']))
        else:
            identity = uid()
            c.execute('INSERT INTO groups VALUES(?,?,?,?,?)', (identity, aid, mid, text(data, 'code').upper(), text(data, 'name')))
        audit(c, actor, 'SAVE_GROUP', identity)
    return {'id': identity}


@app.delete('/api/groups/{identity}')
def delete_group(identity: str, actor=Depends(admin)):
    with connection(True) as c:
        get(c, 'groups', identity)
        if c.execute('SELECT 1 FROM users WHERE group_id=?', (identity,)).fetchone() or c.execute('SELECT 1 FROM windows WHERE group_id=?', (identity,)).fetchone():
            fail('El Grupo tiene Técnicos o historial. Muévelos o conserva el Grupo para mantener su trazabilidad.')
        c.execute('DELETE FROM groups WHERE id=?', (identity,))
        audit(c, actor, 'DELETE_GROUP', identity)
    return {'ok': True}


@app.post('/api/people')
@app.put('/api/people/{identity}')
def save_person(data: dict = Body(...), identity: str = '', actor=Depends(current_user)):
    with connection(True) as c:
        old = get(c, 'users', identity) if identity else None
        role = old['role'] if old else text(data, 'role')
        if role not in ('ADMIN', 'MANAGER', 'USER'):
            fail('Rol no válido.')
        if actor['role'] != 'ADMIN':
            if role != 'USER':
                fail('Sólo Administración puede crear Managers y administradores.', 403)
            if old:
                authorized_target(c, actor, old)
            if data.get('group_id') not in scope(c, actor):
                fail('El Grupo no está en tu alcance.', 403)
        aid = data.get('account_id') if role == 'MANAGER' else None
        gid = data.get('group_id') if role == 'USER' else None
        lead = bool(data.get('is_lead')) and role == 'USER'
        if aid:
            get(c, 'accounts', aid)
        elif role == 'MANAGER':
            fail('El Manager debe pertenecer a una Cuenta.')
        if role == 'USER':
            get(c, 'groups', gid)
            if lead and c.execute('SELECT 1 FROM users WHERE group_id=? AND is_lead=1 AND id<>?', (gid, identity)).fetchone():
                fail('Este Grupo ya tiene Lead.')
            if old and old['is_lead'] and old['group_id'] != gid and c.execute('SELECT 1 FROM users WHERE group_id=? AND is_lead=1', (gid,)).fetchone():
                fail('No se puede mover un Lead a un Grupo que ya tiene otro Lead.')
        group_ids = list(dict.fromkeys(data.get('group_ids', []))) if role == 'MANAGER' else []
        for g_id in group_ids:
            g = get(c, 'groups', g_id)
            if g['account_id'] != aid:
                fail('Un Manager no puede administrar Grupos de distintas Cuentas.')
            if g['manager_id'] and g['manager_id'] != identity:
                fail('El Grupo ya pertenece a otro Manager.')
        if old and role == 'MANAGER':
            for g in c.execute('SELECT * FROM groups WHERE manager_id=?', (identity,)):
                if g['account_id'] != aid and g['id'] not in group_ids:
                    fail('Mueve o desasigna los Grupos actuales antes de cambiar la Cuenta del Manager.')
        status = data.get('status', old['status'] if old else 'PENDING_ACTIVATION')
        if status not in ('ACTIVE', 'DISABLED', 'PENDING_ACTIVATION'):
            fail('Estado no válido.')
        if old and old['role'] == 'ADMIN' and status != 'ACTIVE':
            active_count = c.execute("SELECT count(*) FROM users WHERE role='ADMIN' AND status='ACTIVE'").fetchone()[0]
            if active_count <= 1 or old['id'] == actor['id']:
                fail('No puedes desactivar tu propia cuenta ni al último administrador activo.')
        username = text(data, 'username') if role == 'ADMIN' else text(data, 'employee_id').upper()
        employee_id = None if role == 'ADMIN' else username
        code = None
        if old:
            if status == 'ACTIVE' and not old['password_hash']:
                fail('La persona debe activar su cuenta y definir su contraseña primero.')
            if role == 'USER' and (gid != old['group_id'] or not lead):
                c.execute('UPDATE delegations SET revoked_at=? WHERE lead_id=? AND revoked_at IS NULL', (now(), identity))
            c.execute('UPDATE users SET username=?,employee_id=?,first=?,last=?,email=?,account_id=?,group_id=?,is_lead=?,status=? WHERE id=?',
                      (username, employee_id, text(data, 'first'), text(data, 'last'), text(data, 'email'), aid, gid, int(lead), status, identity))
            if status != 'ACTIVE':
                invalidate_sessions(c, identity)
        else:
            identity = uid()
            code = 'ACT-' + secrets.token_hex(5).upper()
            c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (identity, role, username, employee_id, text(data, 'first'), text(data, 'last'), text(data, 'email'), aid, gid, int(lead), 'PENDING_ACTIVATION', None, password_hash(code), now()))
        if role == 'MANAGER':
            c.execute('UPDATE groups SET manager_id=NULL WHERE manager_id=?', (identity,))
            for g_id in group_ids:
                c.execute('UPDATE groups SET manager_id=? WHERE id=?', (identity, g_id))
            for d in c.execute('SELECT * FROM delegations WHERE manager_id=? AND revoked_at IS NULL', (identity,)).fetchall():
                if not set(json.loads(d['group_ids'])).issubset(set(group_ids)):
                    c.execute('UPDATE delegations SET revoked_at=? WHERE id=?', (now(), d['id']))
        audit(c, actor, 'SAVE_PERSON', identity)
    return {'id': identity, 'activation_code': code}


@app.post('/api/people/{identity}/activation')
def new_activation(identity: str, actor=Depends(admin)):
    with connection(True) as c:
        u = get(c, 'users', identity)
        if u['status'] != 'PENDING_ACTIVATION':
            fail('La cuenta ya está activa. Usa recuperación de acceso.')
        code = 'ACT-' + secrets.token_hex(5).upper()
        c.execute('UPDATE users SET activation_hash=? WHERE id=?', (password_hash(code), identity))
        audit(c, actor, 'REGENERATE_ACTIVATION', identity)
    return {'activation_code': code}


@app.put('/api/profile')
def profile(data: dict = Body(...), actor=Depends(current_user)):
    with connection(True) as c:
        c.execute('UPDATE users SET first=?,last=?,email=? WHERE id=?', (text(data, 'first'), text(data, 'last'), text(data, 'email'), actor['id']))
        audit(c, actor, 'PROFILE', actor['id'])
    return {'ok': True}


@app.put('/api/password')
def change_password(data: dict = Body(...), actor=Depends(current_user)):
    if not password_matches(text(data, 'current'), actor['password_hash']):
        fail('La contraseña actual no es correcta.')
    password = text(data, 'password')
    if len(password) < 10:
        fail('Usa al menos 10 caracteres.')
    with connection(True) as c:
        c.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(password), actor['id']))
        invalidate_sessions(c, actor['id'])
        audit(c, actor, 'CHANGE_PASSWORD', actor['id'])
    return {'ok': True, 'reauthenticate': True}


@app.post('/api/recoveries')
def request_recovery(data: dict = Body(...)):
    with connection(True) as c:
        u = c.execute('SELECT * FROM users WHERE username=? COLLATE NOCASE', (text(data, 'identity'),)).fetchone()
        if u and u['status'] == 'ACTIVE' and not c.execute("SELECT 1 FROM recoveries WHERE user_id=? AND status='PENDING'", (u['id'],)).fetchone():
            c.execute('INSERT INTO recoveries VALUES(?,?,?,?,?,?)', (uid(), u['id'], 'PENDING', None, None, now()))
    return {'message': 'Si la cuenta está activa, se registró la solicitud. Contacta a tu Manager o a Administración.'}


@app.post('/api/recoveries/{identity}/issue')
def issue_recovery(identity: str, actor=Depends(current_user)):
    with connection(True) as c:
        r = get(c, 'recoveries', identity)
        if r['status'] == 'USED':
            fail('Esta solicitud ya fue utilizada.')
        target = get(c, 'users', r['user_id'])
        if target['id'] == actor['id']:
            fail('Otra persona autorizada debe validar tu recuperación.', 403)
        authorized_target(c, actor, target, approval=actor['role'] != 'ADMIN')
        code = 'REC-' + secrets.token_hex(6).upper()
        expires = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
        c.execute("UPDATE recoveries SET status='ISSUED',code_hash=?,expires_at=? WHERE id=?", (password_hash(code), expires, identity))
        audit(c, actor, 'ISSUE_RECOVERY', identity)
    return {'code': code, 'expires_at': expires}


@app.post('/api/recoveries/complete')
def complete_recovery(data: dict = Body(...)):
    password = text(data, 'password')
    if len(password) < 10:
        fail('Usa al menos 10 caracteres.')
    with connection(True) as c:
        u = c.execute('SELECT * FROM users WHERE username=? COLLATE NOCASE', (text(data, 'identity'),)).fetchone()
        requests = c.execute("SELECT * FROM recoveries WHERE user_id=? AND status='ISSUED' AND expires_at>?", (u['id'] if u else '', now())).fetchall()
        r = next((r for r in requests if password_matches(text(data, 'code'), r['code_hash'])), None)
        if not r:
            fail('Código inválido o vencido.')
        c.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(password), u['id']))
        c.execute("UPDATE recoveries SET status='USED',code_hash=NULL WHERE id=?", (r['id'],))
        invalidate_sessions(c, u['id'])
        audit(c, dict(u), 'RESET_PASSWORD', u['id'])
    return {'ok': True}


@app.post('/api/delegations')
def delegate(data: dict = Body(...), actor=Depends(current_user)):
    if actor['role'] != 'MANAGER':
        fail('Sólo el Manager puede delegar su autoridad.', 403)
    start, end = interval(data, 'start_at', 'end_at')
    ids = list(dict.fromkeys(data.get('group_ids', [])))
    with connection(True) as c:
        lead = get(c, 'users', text(data, 'lead_id'))
        allowed = scope(c, actor)
        if not lead['is_lead'] or lead['group_id'] not in allowed or not ids or not set(ids).issubset(allowed):
            fail('Selecciona un Lead de tu equipo y Grupos bajo tu autoridad.')
        identity = uid()
        c.execute('INSERT INTO delegations VALUES(?,?,?,?,?,?,NULL)', (identity, actor['id'], lead['id'], json.dumps(ids), start, end))
        audit(c, actor, 'DELEGATE', identity)
    return {'id': identity}


@app.delete('/api/delegations/{identity}')
def revoke(identity: str, actor=Depends(current_user)):
    with connection(True) as c:
        d = get(c, 'delegations', identity)
        if d['manager_id'] != actor['id']:
            fail('Sólo el Manager que delegó puede revocar.', 403)
        c.execute('UPDATE delegations SET revoked_at=? WHERE id=?', (now(), identity))
        audit(c, actor, 'REVOKE_DELEGATION', identity)
    return {'ok': True}


@app.post('/api/rules')
def add_rule(data: dict = Body(...), actor=Depends(current_user)):
    if actor['role'] != 'MANAGER':
        fail('Sólo el Manager crea reglas de Guardia.', 403)
    segments = data.get('segments', [])
    if not segments:
        fail('Agrega al menos un segmento de Guardia.')
    for s in segments:
        try:
            if int(s['day']) not in range(7):
                raise ValueError()
            time.fromisoformat(s['start'])
            time.fromisoformat(s['end'])
        except (KeyError, ValueError, TypeError):
            fail('Revisa los días y horas de la regla.')
    try:
        effective = date.fromisoformat(text(data, 'effective_from')).isoformat()
    except ValueError:
        fail('Fecha de vigencia inválida.')
    identity = uid()
    with connection(True) as c:
        c.execute('INSERT INTO rules VALUES(?,?,?,?,?)', (identity, actor['id'], text(data, 'name'), effective, json.dumps(segments)))
        audit(c, actor, 'CREATE_RULE', identity)
    return {'id': identity}


@app.post('/api/guards')
def add_guard(data: dict = Body(...), actor=Depends(current_user)):
    operational(actor)
    try:
        a, b = date.fromisoformat(text(data, 'start_date')), date.fromisoformat(text(data, 'end_date'))
    except ValueError:
        fail('Fechas inválidas.')
    if b < a or (b - a).days > 31:
        fail('La Guardia debe durar entre 1 y 32 días.')
    identity = uid()
    with connection(True) as c:
        rule = get(c, 'rules', text(data, 'rule_id'))
        g = get(c, 'groups', actor['group_id'])
        if rule['manager_id'] != g['manager_id'] or rule['effective_from'] > a.isoformat():
            fail('Selecciona una regla vigente de tu Manager.')
        snapshot = dict(rule, segments=json.loads(rule['segments']))
        c.execute('INSERT INTO guards VALUES(?,?,?,?,?,?,?,?)', (identity, actor['id'], str(a), str(b), json.dumps(snapshot), 'SUBMITTED', None, now()))
        audit(c, actor, 'REQUEST_GUARD', identity)
    return {'id': identity}


@app.post('/api/windows')
def add_window(data: dict = Body(...), actor=Depends(current_user)):
    a, b = interval(data, 'scheduled_start', 'scheduled_end')
    gid = text(data, 'group_id')
    with connection(True) as c:
        if gid not in scope(c, actor) or actor['role'] == 'ADMIN':
            fail('Sólo el Manager o Lead delegado del Grupo puede programar OT compartida.', 403)
        identity = uid()
        c.execute('INSERT INTO windows VALUES(?,?,?,?,?,?,?,?,?)', (identity, gid, actor['id'], a, b, valid_reference(data), text(data, 'description'), 'APPROVED', now()))
        audit(c, actor, 'SHARED_WINDOW', identity)
    return {'id': identity}


def insert_ot(c, actor, data, window=None):
    identity = uid()
    capture = data.get('capture_type', 'PLANNED')
    if capture not in ('PLANNED', 'HISTORICAL', 'EMERGENCY'):
        fail('Tipo de OT inválido.')
    if window:
        capture = 'PLANNED'
        a, b = window['scheduled_start'], window['scheduled_end']
        ref, description = window['reference'], window['description']
    elif capture != 'EMERGENCY':
        a, b = interval(data, 'scheduled_start', 'scheduled_end')
        ref, description = valid_reference(data), text(data, 'description')
    else:
        a = b = None
        ref = description = ''
    if capture == 'HISTORICAL' and parse_at(b) > datetime.now(timezone.utc):
        fail('La OT histórica debe haber finalizado.')
    actual_a, actual_b = (a, b) if capture == 'HISTORICAL' else (None, None)
    execution = 'COMPLETED' if capture == 'HISTORICAL' else 'SCHEDULED' if capture == 'PLANNED' else 'RUNNING'
    status = 'APPROVED' if window else 'DOCUMENTATION' if capture == 'EMERGENCY' else 'SUBMITTED'
    c.execute('INSERT INTO overtime VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
              (identity, actor['id'], window['id'] if window else None, capture, a, b, actual_a, actual_b, ref, description, text(data, 'justification', False), text(data, 'impact', False), text(data, 'in_lieu', False), status, execution, 0, None, now(), now()))
    return identity


@app.post('/api/overtime')
def add_overtime(data: dict = Body(...), actor=Depends(current_user)):
    operational(actor)
    if data.get('capture_type') == 'EMERGENCY':
        fail('Inicia la OT de emergencia con el Timer.')
    with connection(True) as c:
        identity = insert_ot(c, actor, data)
        audit(c, actor, 'CREATE_OT', identity)
    return {'id': identity}


@app.post('/api/windows/{identity}/join')
def join_window(identity: str, actor=Depends(current_user)):
    operational(actor)
    with connection(True) as c:
        w = get(c, 'windows', identity)
        if w['group_id'] != actor['group_id'] or w['status'] != 'APPROVED' or parse_at(w['scheduled_end']) <= datetime.now(timezone.utc):
            fail('Esta ventana no está disponible para tu Grupo.')
        otid = insert_ot(c, actor, {}, w)
        audit(c, actor, 'JOIN_SHARED_OT', otid)
    return {'id': otid}


@app.put('/api/overtime/{identity}')
def edit_ot(identity: str, data: dict = Body(...), actor=Depends(current_user)):
    with connection(True) as c:
        o = get(c, 'overtime', identity)
        if o['user_id'] != actor['id']:
            fail('Sólo el Técnico propietario puede editar su OT.', 403)
        if o['execution'] == 'RUNNING':
            fail('Detén el Timer antes de documentar.')
        ref = valid_reference(data)
        if o['execution'] == 'SCHEDULED':
            a, b = interval(data, 'scheduled_start', 'scheduled_end')
            c.execute('UPDATE overtime SET scheduled_start=?,scheduled_end=? WHERE id=?', (a, b, identity))
        c.execute("UPDATE overtime SET reference=?,description=?,justification=?,impact=?,in_lieu=?,status='SUBMITTED',approved_by=NULL,revision=revision+1,updated_at=? WHERE id=?", (ref, text(data, 'description'), text(data, 'justification'), text(data, 'impact'), text(data, 'in_lieu'), now(), identity))
        audit(c, actor, 'EDIT_OT_REOPEN_APPROVAL', identity, {'previous_status': o['status'], 'revision': o['revision'] + 1})
    return {'ok': True}


@app.post('/api/timers/start')
def start_timer(data: dict = Body(...), actor=Depends(current_user)):
    operational(actor)
    with connection(True) as c:
        if c.execute('SELECT 1 FROM timers WHERE user_id=? AND end_at IS NULL', (actor['id'],)).fetchone():
            fail('Ya tienes un Timer activo.')
        otid = data.get('overtime_id')
        if otid:
            o = get(c, 'overtime', otid)
            if o['user_id'] != actor['id'] or o['status'] != 'APPROVED' or o['execution'] != 'SCHEDULED':
                fail('La OT debe ser tuya, estar aprobada y pendiente de iniciar.')
            if parse_at(o['scheduled_start']) > datetime.now(timezone.utc):
                fail('La ventana programada todavía no inicia.')
            if parse_at(o['scheduled_end']) <= datetime.now(timezone.utc):
                fail('La ventana programada ya terminó.')
        else:
            otid = insert_ot(c, actor, {'capture_type': 'EMERGENCY'})
        identity, stamp = uid(), now()
        c.execute('INSERT INTO timers VALUES(?,?,?,?,NULL)', (identity, actor['id'], otid, stamp))
        c.execute("UPDATE overtime SET execution='RUNNING',start_at=?,updated_at=? WHERE id=?", (stamp, stamp, otid))
        audit(c, actor, 'START_TIMER', otid)
    return {'id': identity}


@app.post('/api/timers/{identity}/stop')
def stop_timer(identity: str, actor=Depends(current_user)):
    with connection(True) as c:
        t = get(c, 'timers', identity)
        if t['user_id'] != actor['id']:
            fail('Sólo el Técnico propietario puede detener el Timer.', 403)
        if t['end_at']:
            fail('El Timer ya está detenido.')
        stamp = now()
        c.execute('UPDATE timers SET end_at=? WHERE id=?', (stamp, identity))
        o = get(c, 'overtime', t['overtime_id'])
        status = 'DOCUMENTATION' if o['capture_type'] == 'EMERGENCY' else 'SUBMITTED'
        c.execute("UPDATE overtime SET end_at=?,execution='COMPLETED',status=?,approved_by=NULL,updated_at=? WHERE id=?", (stamp, status, stamp, o['id']))
        audit(c, actor, 'STOP_TIMER', o['id'])
    return {'ok': True}


@app.post('/api/approvals/{kind}/{identity}')
def decide(kind: str, identity: str, data: dict = Body(...), actor=Depends(current_user)):
    table = {'ot': 'overtime', 'guard': 'guards'}.get(kind)
    if not table:
        fail('Tipo de registro inválido.')
    decision = text(data, 'decision')
    if decision not in ('APPROVED', 'REJECTED'):
        fail('Decisión inválida.')
    with connection(True) as c:
        r = get(c, table, identity)
        authorized_target(c, actor, get(c, 'users', r['user_id']), approval=True)
        if actor['role'] == 'ADMIN':
            fail('Las aprobaciones corresponden al Manager o Lead delegado.', 403)
        if r['status'] != 'SUBMITTED' or kind == 'ot' and r['execution'] == 'RUNNING':
            fail('El registro no está pendiente de aprobación.')
        if decision == 'REJECTED' and not text(data, 'reason', False):
            fail('Agrega el motivo del rechazo.')
        c.execute(f'UPDATE {table} SET status=?,approved_by=? WHERE id=?', (decision, actor['id'], identity))
        audit(c, actor, decision, identity, {'kind': kind, 'reason': text(data, 'reason', False)})
    return {'ok': True}


# All accounting/export/capture views share this implementation, including cross-midnight splits.
def union_intervals(intervals):
    result = []
    for a, b in sorted(intervals):
        if b <= a:
            continue
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def subtract_intervals(a, b, cuts):
    parts = [(a, b)]
    for ca, cb in union_intervals(cuts):
        remaining = []
        for pa, pb in parts:
            if cb <= pa or ca >= pb:
                remaining.append((pa, pb))
            else:
                if pa < ca:
                    remaining.append((pa, ca))
                if cb < pb:
                    remaining.append((cb, pb))
        parts = remaining
    return parts


def accounting(c, visible, month=None):
    if month:
        try:
            first = date.fromisoformat(month + '-01')
        except ValueError:
            fail('Mes inválido.')
        lower = datetime.combine(first, time(), TZ)
        upper = datetime.combine((first.replace(day=28) + timedelta(days=4)).replace(day=1), time(), TZ)
    people = {u['id']: u for u in rows(c, 'users')}
    approved = [o for o in rows(c, 'overtime') if o['user_id'] in visible and o['status'] == 'APPROVED' and o['execution'] == 'COMPLETED' and o['start_at'] and o['end_at']]
    ots = {}
    for o in approved:
        ots.setdefault(o['user_id'], []).append((parse_at(o['start_at']), parse_at(o['end_at'])))
    output = []

    def append_parts(user_id, kind, a, b, ref, description, entity_id):
        a, b = a.astimezone(TZ), b.astimezone(TZ)
        if month:
            a, b = max(a, lower), min(b, upper)
        while a < b:
            midnight = datetime.combine(a.date() + timedelta(days=1), time(), TZ)
            stop = min(b, midnight)
            minutes = round((stop.astimezone(timezone.utc) - a.astimezone(timezone.utc)).total_seconds() / 60, 4)
            if minutes:
                p = people[user_id]
                output.append({'id': entity_id, 'user_id': user_id, 'employee_id': p['employee_id'], 'name': f"{p['first']} {p['last']}", 'group_id': p['group_id'], 'kind': kind, 'date': str(a.date()), 'start': a.strftime('%H:%M'), 'end': stop.strftime('%H:%M'), 'start_at': a.isoformat(), 'end_at': stop.isoformat(), 'minutes': minutes, 'hours': round(minutes / 60, 4), 'reference': ref, 'description': description})
            a = stop

    # Overlapping approved OT is counted once, even when two different records overlap.
    for user_id, intervals in ots.items():
        prior = []
        for o in sorted([o for o in approved if o['user_id'] == user_id], key=lambda o: (o['start_at'], o['id'])):
            a, b = parse_at(o['start_at']), parse_at(o['end_at'])
            for pa, pb in subtract_intervals(a, b, prior):
                append_parts(user_id, 'OT', pa, pb, o['reference'], o['description'], o['id'])
            prior.append((a, b))
    guard_intervals = {}
    for g in rows(c, 'guards'):
        if g['user_id'] not in visible or g['status'] != 'APPROVED':
            continue
        rule = json.loads(g['rule_snapshot'])
        day, last = date.fromisoformat(g['start_date']), date.fromisoformat(g['end_date'])
        while day <= last:
            for s in rule['segments']:
                if int(s['day']) != day.weekday():
                    continue
                a = datetime.combine(day, time.fromisoformat(s['start']), TZ)
                b = datetime.combine(day, time.fromisoformat(s['end']), TZ)
                if b <= a:
                    b += timedelta(days=1)
                guard_intervals.setdefault(g['user_id'], []).append((a, b))
            day += timedelta(days=1)
    for user_id, intervals in guard_intervals.items():
        for a, b in union_intervals(intervals):
            for pa, pb in subtract_intervals(a, b, ots.get(user_id, [])):
                append_parts(user_id, 'GUARD', pa, pb, '', 'Guardia neta', '')
    return sorted(output, key=lambda r: (r['date'], r['start'], r['name']))


def selected_users(c, actor, user_id=None, group_id=None):
    allowed = scope(c, actor)
    visible = {u['id'] for u in rows(c, 'users') if u['role'] == 'USER' and (u['id'] == actor['id'] or u['group_id'] in allowed)}
    if actor['role'] == 'ADMIN':
        visible = {u['id'] for u in rows(c, 'users') if u['role'] == 'USER'}
    if user_id:
        if user_id not in visible:
            fail('El Técnico no está en tu alcance.', 403)
        visible &= {user_id}
    if group_id:
        visible &= {u['id'] for u in rows(c, 'users') if u['group_id'] == group_id}
    return visible


@app.get('/api/accounting')
def capture(month: str, user_id: str | None = None, group_id: str | None = None, actor=Depends(current_user)):
    with connection() as c:
        result = accounting(c, selected_users(c, actor, user_id, group_id), month)
    return {'rows': result, 'ot_minutes': round(sum(r['minutes'] for r in result if r['kind'] == 'OT'), 4), 'guard_minutes': round(sum(r['minutes'] for r in result if r['kind'] == 'GUARD'), 4), 'timezone': str(TZ)}


@app.get('/api/export.xlsx')
def export_excel(month: str, user_id: str | None = None, group_id: str | None = None, kind: str | None = None, actor=Depends(current_user)):
    with connection() as c:
        result = accounting(c, selected_users(c, actor, user_id, group_id), month)
        if kind:
            if kind not in ('OT', 'GUARD'):
                fail('Tipo de exportación inválido.')
            result = [r for r in result if r['kind'] == kind]
        groups = {g['id']: g for g in rows(c, 'groups')}
    wb = Workbook()
    ws = wb.active
    ws.title = 'Tiempo aprobado'
    ws.append(['Fecha', 'Employee ID', 'Técnico', 'Grupo', 'Tipo', 'Inicio', 'Fin', 'Duración HH:MM', 'Horas decimales', 'Referencia', 'Descripción'])
    for r in result:
        mins = round(r['minutes'])
        # Prevent spreadsheet formula execution from user-supplied labels.
        safe = lambda v: "'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v
        ws.append([r['date'], safe(r['employee_id']), safe(r['name']), safe(groups.get(r['group_id'], {}).get('name', '')), 'Onsite Overtime' if r['kind'] == 'OT' else 'Stand-by', r['start'], r['end'], f'{mins // 60:02}:{mins % 60:02}', r['hours'], safe(r['reference']), safe(r['description'])])
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='173E48')
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 24
    summary = wb.create_sheet('Resumen')
    summary.append(['Mes', month])
    summary.append(['Zona horaria', str(TZ)])
    summary.append(['Horas OT', sum(r['hours'] for r in result if r['kind'] == 'OT')])
    summary.append(['Horas Guardia neta', sum(r['hours'] for r in result if r['kind'] == 'GUARD')])
    summary.append(['Criterio', 'Sólo aprobados; OT única; Guardia menos OT; división por día local.'])
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename="Operational_Pulse_{month}.xlsx"'})


app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


@app.get('/')
def index():
    return FileResponse(ROOT / 'index.html')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=5510)
