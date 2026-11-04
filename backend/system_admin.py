"""Admin configuration and portable, password-encrypted disaster recovery snapshots.
No email is sent. Restoration is deliberately offline into a new database location.
"""
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import secrets
import sqlite3
import tempfile
import zipfile

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from fastapi import Body, Depends
from fastapi.responses import StreamingResponse

MAGIC=b'PULSE-ORG-1\n'
MAX_PACKAGE=180*1024*1024
MAX_DATABASE=256*1024*1024


def backup_cipher(password,salt):
    if not isinstance(password,str) or not 12<=len(password)<=1024:
        raise ValueError('Usa una contraseña de respaldo de 12 a 1024 caracteres.')
    return Fernet(base64.urlsafe_b64encode(Scrypt(salt=salt,length=32,n=2**14,r=8,p=1).derive(password.encode('utf-8'))))


def seal_backup(database,key,manifest,password):
    stream=io.BytesIO()
    manifest={**manifest,'format':'PULSE-ORG-1','database_sha256':hashlib.sha256(database).hexdigest(),'has_recovery_key':key is not None}
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
        archive.writestr('organization.sqlite3',database)
        if key:archive.writestr('recovery.key',key)
    salt=secrets.token_bytes(16)
    return MAGIC+salt+backup_cipher(password,salt).encrypt(stream.getvalue())


def open_backup(payload,password):
    if len(payload)>MAX_PACKAGE or not payload.startswith(MAGIC):raise ValueError('El archivo no es un respaldo integral de Pulse válido.')
    salt=payload[len(MAGIC):len(MAGIC)+16]
    try:plain=backup_cipher(password,salt).decrypt(payload[len(MAGIC)+16:])
    except InvalidToken:raise ValueError('Contraseña incorrecta o respaldo dañado.') from None
    try:
        with zipfile.ZipFile(io.BytesIO(plain)) as archive:
            names=archive.namelist()
            if len(names)!=len(set(names)) or set(names) not in ({'manifest.json','organization.sqlite3'},{'manifest.json','organization.sqlite3','recovery.key'}):raise ValueError('Contenido de respaldo no reconocido.')
            if sum(item.file_size for item in archive.infolist())>MAX_DATABASE+65536:raise ValueError('El respaldo supera el tamaño permitido.')
            if archive.getinfo('manifest.json').file_size>65536 or ('recovery.key' in names and archive.getinfo('recovery.key').file_size>1024):raise ValueError('Metadatos de respaldo inválidos.')
            manifest=json.loads(archive.read('manifest.json'))
            if not isinstance(manifest,dict):raise ValueError('Manifiesto de respaldo inválido.')
            if not isinstance(manifest.get('created_at'),str) or not isinstance(manifest.get('version'),str):raise ValueError('El manifiesto no incluye versión y fecha válidas.')
            data=archive.read('organization.sqlite3');key=archive.read('recovery.key') if 'recovery.key' in names else None
            if manifest.get('format')!='PULSE-ORG-1' or manifest.get('database_sha256')!=hashlib.sha256(data).hexdigest() or manifest.get('has_recovery_key')!=(key is not None):raise ValueError('El contenido del respaldo no coincide con su manifiesto.')
            if key:Fernet(key)
            return data,key,manifest
    except (zipfile.BadZipFile,KeyError,UnicodeError,json.JSONDecodeError) as error:raise ValueError('El respaldo está dañado.') from error


def prepare_snapshot(path,stamp):
    """Freeze only the copy: never carry sessions or accumulating timers through a disaster."""
    with sqlite3.connect(path) as db:
        db.row_factory=sqlite3.Row
        for table in ('sessions','session_activity','login_attempts','recovery_code_vault'):db.execute('DELETE FROM '+table)
        db.execute("UPDATE recoveries SET status='PENDING',code_hash=NULL,expires_at=NULL WHERE status='ISSUED'")
        active=list(db.execute('SELECT t.*,o.capture_type,o.scheduled_end FROM timers t JOIN overtime o ON o.id=t.overtime_id WHERE t.end_at IS NULL'))
        for timer in active:
            end=stamp
            if timer['capture_type']=='PLANNED' and timer['scheduled_end'] and datetime.fromisoformat(timer['scheduled_end'])<datetime.fromisoformat(end):end=timer['scheduled_end']
            if datetime.fromisoformat(end)<datetime.fromisoformat(timer['start_at']):raise ValueError('Se detectó un Timer con fecha de inicio posterior al corte de respaldo.')
            db.execute('UPDATE timers SET end_at=? WHERE id=?',(end,timer['id']))
            status='DOCUMENTATION' if timer['capture_type']=='EMERGENCY' else 'SUBMITTED'
            db.execute("UPDATE overtime SET end_at=?,execution='COMPLETED',status=?,approved_by=NULL,updated_at=? WHERE id=?",(end,status,stamp,timer['overtime_id']))
            db.execute("UPDATE ot_extensions SET status='CANCELLED',decision_reason='Cierre al corte del respaldo de recuperación',decided_at=? WHERE overtime_id=? AND status='SUBMITTED'",(stamp,timer['overtime_id']))
            db.execute('INSERT INTO audit VALUES(?,?,?,?,?,?)',(secrets.token_hex(16),None,'RECOVERY_SNAPSHOT_TIMER_CLOSED',timer['overtime_id'],json.dumps({'reason':'Cierre sólo en la copia de recuperación; no modifica la operación original.','end_at':end}),stamp))
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('La copia no superó la validación de integridad.')
        db.commit()
        db.execute('VACUUM')  # Remove deleted session/reset material from the portable file.
        return len(active)


def install_system_admin(app,namespace):
    connection=namespace['connection'];admin=namespace['admin'];fail=namespace['fail'];audit=namespace['audit'];cipher=namespace['recovery_cipher']
    with connection(True) as db:db.execute('CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL)')

    def smtp_config(db):
        row=db.execute("SELECT value FROM system_settings WHERE key='smtp'").fetchone()
        return json.loads(row['value']) if row else {'host':'','port':587,'security':'STARTTLS','username':'','from_address':'','from_name':'Operational Pulse'}

    def clean_config(data):
        result={}
        for key,limit in [('host',253),('username',254),('from_address',254),('from_name',100)]:
            value=str(data.get(key,'')).strip()
            if len(value)>limit or any(ch in value for ch in '\r\n\x00'):fail('Revisa los campos del servidor de correo.')
            result[key]=value
        if not result['host'] or re.search(r'[^A-Za-z0-9._:\-\[\]]',result['host']):fail('Escribe el nombre o IP del servidor SMTP, sin URL ni ruta.')
        try:port=int(data.get('port',587))
        except (TypeError,ValueError):fail('Puerto SMTP inválido.')
        if not 1<=port<=65535:fail('El puerto SMTP debe estar entre 1 y 65535.')
        security=data.get('security','STARTTLS')
        if security not in ('STARTTLS','SSL','NONE'):fail('Selecciona una modalidad de conexión válida.')
        if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+',result['from_address']):fail('Indica un correo de remitente válido.')
        return {**result,'port':port,'security':security}

    @app.get('/api/admin/settings')
    def settings(actor=Depends(admin)):
        with connection() as db:
            config=smtp_config(db);config.pop('password_encrypted',None)
            stored=smtp_config(db)
            return {'smtp':{**config,'password_configured':bool(stored.get('password_encrypted'))},'mail_delivery_enabled':False,'counts':{table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in ('accounts','groups','users','overtime','guards')},'version':namespace['VERSION']}

    @app.put('/api/admin/settings/smtp')
    def save_smtp(data:dict=Body(...),actor=Depends(admin)):
        config=clean_config(data);password=data.get('password','')
        if not isinstance(password,str) or len(password)>4096:fail('Contraseña SMTP inválida.')
        with connection(True) as db:
            previous=smtp_config(db)
            config['password_encrypted']='' if data.get('clear_password') is True else previous.get('password_encrypted','')
            if password:config['password_encrypted']=cipher(create=True).encrypt(password.encode()).decode()
            db.execute("INSERT INTO system_settings(key,value,updated_at) VALUES('smtp',?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",(json.dumps(config),namespace['now']()))
            audit(db,actor,'SAVE_SMTP_SETTINGS','smtp',{'host':config['host'],'port':config['port'],'security':config['security'],'delivery_enabled':False})
        return {'ok':True,'mail_delivery_enabled':False}

    @app.post('/api/admin/organization-backup')
    def organization_backup(data:dict=Body(...),actor=Depends(admin)):
        password=data.get('password')
        try:backup_cipher(password,b'\0'*16)
        except ValueError as error:fail(str(error))
        with connection(True) as db:audit(db,actor,'EXPORT_ORGANIZATION_BACKUP','organization',{'format':'PULSE-ORG-1'})
        with tempfile.TemporaryDirectory() as folder:
            snapshot=Path(folder)/'organization.sqlite3'
            with sqlite3.connect(namespace['DB']) as source,sqlite3.connect(snapshot) as target:source.backup(target)
            stamp=datetime.now(timezone.utc).isoformat()
            try:closed=prepare_snapshot(snapshot,stamp)
            except ValueError as error:fail(str(error),409)
            if snapshot.stat().st_size>MAX_DATABASE:fail('La base supera el tamaño permitido para el respaldo descargable.',413)
            key=namespace['RECOVERY_KEY'].read_bytes() if namespace['RECOVERY_KEY'].is_file() else None
            with sqlite3.connect(snapshot) as db:
                encrypted=db.execute("SELECT value FROM system_settings WHERE key='smtp'").fetchone()
                needs_key=encrypted and json.loads(encrypted[0]).get('password_encrypted')
                if needs_key and key is None:fail('Falta la clave local para recuperar la configuración de correo. Guarda nuevamente su contraseña antes del respaldo.',409)
            if key:
                try:Fernet(key)
                except ValueError:fail('La clave local está dañada; corrígela antes de generar el respaldo.',409)
            payload=seal_backup(snapshot.read_bytes(),key,{'version':namespace['VERSION'],'created_at':stamp,'closed_timers_in_copy':closed,'sessions_included':False},password)
        if len(payload)>MAX_PACKAGE:fail('El respaldo cifrado supera el tamaño permitido.',413)
        filename='Operational_Pulse_Organizacion_'+datetime.now(namespace['TZ']).strftime('%Y-%m-%d_%H%M%S')+'.pulseorg'
        return StreamingResponse(io.BytesIO(payload),media_type='application/octet-stream',headers={'Content-Disposition':'attachment; filename="'+filename+'"'})
