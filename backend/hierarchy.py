"""Non-destructive role migration. Executive scope is read-only and derived live."""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def migrate_executive_roles(path):
    if not path.exists():
        return
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
        if not row or "'DP'" in row[0]:
            return
        original = row[0]
        expanded = re.sub(r"\(\s*'ADMIN'\s*,\s*'MANAGER'\s*,\s*'USER'\s*\)", "('ADMIN','MANAGER','USER','DP','DPE')", original)
        if expanded == original:
            raise RuntimeError('No se reconoce el esquema de roles; no se modificó la base de datos.')
        backup_dir = path.parent / 'backups'
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / ('antes_v121_' + datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f') + '.sqlite3')
        with sqlite3.connect(backup) as dest:
            db.backup(dest)
        objects = db.execute("SELECT sql FROM sqlite_master WHERE tbl_name='users' AND sql IS NOT NULL AND type IN ('index','trigger')").fetchall()
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute('BEGIN IMMEDIATE')
        try:
            create = re.sub(r'^(CREATE TABLE\s+)(?:IF NOT EXISTS\s+)?["`\[]?users["`\]]?', r'\1users_v121', expanded, count=1, flags=re.I)
            db.execute(create)
            db.execute('INSERT INTO users_v121 SELECT * FROM users')
            db.execute('DROP TABLE users')
            db.execute('ALTER TABLE users_v121 RENAME TO users')
            for (sql,) in objects:
                db.execute(sql)
            if db.execute('PRAGMA foreign_key_check').fetchone():
                raise RuntimeError('La migración detectó referencias inválidas; se conserva la base anterior.')
            db.commit()
        except Exception:
            db.rollback()
            raise
