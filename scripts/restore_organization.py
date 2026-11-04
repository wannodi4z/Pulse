"""Restore a .pulseorg backup offline, refusing to overwrite an existing database or key."""
import argparse
import getpass
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from backend.system_admin import open_backup,MAX_PACKAGE


def restore_backup(backup,destination,password):
    backup=Path(backup).expanduser().resolve();destination=Path(destination).expanduser().resolve()
    if backup.stat().st_size>MAX_PACKAGE:raise ValueError('El archivo supera el tamaño permitido.')
    database,key,manifest=open_backup(backup.read_bytes(),password)
    destination.mkdir(parents=True,exist_ok=True)
    target=destination/'operational_pulse.db';key_target=destination/'operational_pulse.key'
    if target.exists() or key_target.exists():raise ValueError('La carpeta ya contiene una base o clave. Elige una instalación nueva; no se reemplazaron sus archivos.')
    with tempfile.TemporaryDirectory(dir=destination) as temporary:
        staged=Path(temporary)/'organization.sqlite3';staged.write_bytes(database);staged.chmod(0o600)
        with sqlite3.connect('file:'+str(staged)+'?mode=ro',uri=True) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or db.execute('PRAGMA foreign_key_check').fetchone():raise ValueError('La base no supera las comprobaciones de integridad.')
            for table in ('users','accounts','groups','overtime','guards'):db.execute('SELECT count(*) FROM '+table).fetchone()
        key_staged=Path(temporary)/'recovery.key'
        if key:key_staged.write_bytes(key);key_staged.chmod(0o600)
        created=[]
        try:
            if key:os.link(key_staged,key_target);created.append(key_target)
            os.link(staged,target);created.append(target)
        except Exception:
            for file in created:file.unlink(missing_ok=True)
            raise
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--backup');parser.add_argument('--destination',default=str(ROOT));args=parser.parse_args()
    filename=args.backup or input('Ruta del archivo .pulseorg: ').strip().strip('"').strip("'")
    password=getpass.getpass('Contraseña del respaldo: ')
    try:manifest=restore_backup(filename,args.destination,password)
    except (OSError,ValueError,sqlite3.Error) as error:print('No se restauró la organización: '+str(error),file=sys.stderr);return 1
    print('Organización recuperada. Corte: '+manifest['created_at']+'. Inicia Pulse e ingresa con tus credenciales.');return 0

if __name__=='__main__':raise SystemExit(main())
