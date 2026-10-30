"""Append synthetic workflow records; preserve all existing rows and Samuel's October 2026."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import shutil
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
TZ=ZoneInfo('America/Mexico_City')
NAMESPACE=uuid.UUID('a869f159-b9f2-42f0-aec8-100d657807f8')
MONTHS=tuple(f'2026-{m:02}' for m in range(5,11))

def key(*parts):return uuid.uuid5(NAMESPACE,'|'.join(map(str,parts))).hex

def stamp(day,hour=0,minute=0):return datetime.combine(day,datetime.min.time(),TZ).replace(hour=hour,minute=minute)

def excluded(person,start,end):
    is_samuel=str(person['employee_id'])=='951357'
    return is_samuel and start<stamp(date(2026,11,1)) and end>stamp(date(2026,10,1))

def insert(c,table,values):
    columns=list(values)
    c.execute('INSERT INTO '+table+'('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',[values[k] for k in columns])

def protected_october(c):
    """Hash existing October records/children for the explicitly protected employee."""
    people={r['id'] for r in c.execute("SELECT id FROM users WHERE employee_id='951357'")}
    records=[];ids=set()
    for table in ('overtime','guards'):
        for row in c.execute('SELECT * FROM '+table):
            r=dict(row)
            if r['user_id'] not in people:continue
            if table=='overtime':
                intervals=[(r.get('start_at') or r.get('scheduled_start'),r.get('end_at') or r.get('scheduled_end'))]
                touches=any(a and b and datetime.fromisoformat(a)<stamp(date(2026,11,1)) and datetime.fromisoformat(b)>stamp(date(2026,10,1)) for a,b in intervals)
            else:
                # Include September 30 as a conservative boundary for cross-midnight coverage.
                touches=r['start_date']<='2026-10-31' and r['end_date']>='2026-09-30'
            if touches:records.append((table,r));ids.add(r['id'])
    for table,column in [('timers','overtime_id'),('ot_time_corrections','overtime_id'),('ot_extensions','overtime_id'),('record_origins','record_id'),('audit','entity_id')]:
        for row in c.execute('SELECT * FROM '+table):
            r=dict(row)
            if r[column] in ids:records.append((table,r))
    return hashlib.sha256(json.dumps(records,sort_keys=True,default=str).encode()).hexdigest()

def populate(db_path,*,clock=None,backup=True):
    db=Path(db_path).resolve()
    if not db.is_file():raise ValueError('No existe la base. Abre Pulse una vez y vuelve a ejecutar la carga.')
    current=(clock or datetime.now(TZ)).astimezone(TZ)
    c=sqlite3.connect(db,timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
    result={'overtime':0,'guards':0,'timers':0,'rules':0,'people':0,'managers':0,'skipped_existing':0,'protected_october_unchanged':False}
    try:
        available={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required={'record_origins','ot_time_corrections','ot_group_activities','ot_extensions','audit','users','rules','windows','overtime','guards','timers'}
        if not required<=available:raise ValueError('Abre Pulse con start.command de esta versión una vez para actualizar su estructura; ciérralo y vuelve a cargar los datos.')
        if c.execute('SELECT count(*) FROM timers WHERE end_at IS NULL').fetchone()[0]:raise ValueError('Hay Timers activos. Deténlos antes de cargar datos de prueba.')
        if backup:
            destination=db.parent/'backups'/('antes_demo_'+current.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]+'.sqlite3')
            destination.parent.mkdir(parents=True,exist_ok=True)
            with sqlite3.connect(destination) as copy:c.backup(copy)
            result['backup']=str(destination)
        c.execute('BEGIN IMMEDIATE')
        if c.execute('SELECT count(*) FROM timers WHERE end_at IS NULL').fetchone()[0]:raise ValueError('Se inició un Timer durante la carga. No se agregaron datos.')
        before=protected_october(c)
        people=[dict(r) for r in c.execute("SELECT * FROM users WHERE role='USER' AND status='ACTIVE' ORDER BY employee_id")]
        groups={r['id']:dict(r) for r in c.execute('SELECT * FROM groups')}
        accounts={r['id']:dict(r) for r in c.execute('SELECT * FROM accounts')}
        managers={r['id']:dict(r) for r in c.execute("SELECT * FROM users WHERE role='MANAGER' AND status='ACTIVE'")}
        used=set();covered=set()
        def audit(entity,actor,action,when,detail=None):
            insert(c,'audit',{'id':key(entity,action),'actor_id':actor,'action':action,'entity_id':entity,'detail':json.dumps({'synthetic':True,'dataset':'PULSE-DEMO-2026',**(detail or {})},ensure_ascii=False),'created_at':when.isoformat()})
        def origin(identity,p,mid):
            g=groups.get(p['group_id']);a=accounts[managers[mid]['account_id']]
            insert(c,'record_origins',{'record_id':identity,'snapshot':json.dumps({'group_id':p['group_id'],'group_name':g['name'] if g else 'Lead del Manager','group_code':g.get('standard_code') or g['code'] if g else '', 'account_name':a['name'],'account_code':a['code'],'manager_id':mid,'inferred':False})})
        def add_ot(p,mid,period,slot,kind,start,end,status='APPROVED',future=False):
            if excluded(p,start,end):return
            identity=key('OT',p['id'],period,slot)
            if c.execute('SELECT 1 FROM overtime WHERE id=?',(identity,)).fetchone():result['skipped_existing']+=1;return
            if not future and c.execute('SELECT 1 FROM overtime WHERE user_id=? AND start_at=? AND end_at=?',(p['id'],start.isoformat(),end.isoformat())).fetchone():return
            created=start-timedelta(days=2) if kind=='PLANNED' else end+timedelta(hours=8) if kind=='HISTORICAL' else start
            execution='SCHEDULED' if future or status=='REJECTED' else 'COMPLETED'
            wid=None;source=False
            if kind=='PLANNED' and p['group_id']:
                # Completed plans were preapproved; final actual-time review can still be pending.
                share=status!='REJECTED' and (not future or status=='APPROVED')
                wid=key('window',p['group_id'] if share else p['id'],period,slot)
                existing=c.execute('SELECT * FROM windows WHERE id=?',(wid,)).fetchone()
                if not existing:
                    source=True
                    insert(c,'windows',{'id':wid,'group_id':p['group_id'],'created_by':p['id'],'scheduled_start':start.isoformat(),'scheduled_end':end.isoformat(),'reference':'CHGDEMO'+wid[:12].upper(),'description':'[DEMO] Mantenimiento y validación del servicio','status':'APPROVED' if share else status,'created_at':created.isoformat()})
                else:
                    # Every linked participant uses the exact activity window.
                    start=datetime.fromisoformat(existing['scheduled_start']);end=datetime.fromisoformat(existing['scheduled_end'])
            reference=('INC' if kind=='EMERGENCY' else 'CHG')+'DEMO'+(wid or identity)[:12].upper()
            docs=status!='DOCUMENTATION'
            values={'id':identity,'user_id':p['id'],'window_id':wid,'capture_type':kind,'scheduled_start':start.isoformat() if kind!='EMERGENCY' else None,'scheduled_end':end.isoformat() if kind!='EMERGENCY' else None,'start_at':start.isoformat() if execution=='COMPLETED' else None,'end_at':end.isoformat() if execution=='COMPLETED' else None,'reference':reference if docs else '', 'description':'[DEMO] '+{'PLANNED':'Mantenimiento programado y verificación','HISTORICAL':'Captura excepcional por indisponibilidad del acceso','EMERGENCY':'Recuperación de servicio e incidente'}[kind] if docs else '', 'justification':('[DEMO] Acceso a Pulse no disponible durante la intervención; se documenta excepcionalmente al recuperar acceso.' if kind=='HISTORICAL' else '[DEMO] Continuidad del servicio fuera de jornada.') if docs else '', 'impact':'[DEMO] Riesgo de indisponibilidad del servicio.' if docs else '', 'in_lieu':'[DEMO] Cobertura operativa requiere disponibilidad del equipo.' if docs else '', 'status':status,'execution':execution,'revision':0,'approved_by':mid if status=='APPROVED' else None,'created_at':created.isoformat(),'updated_at':(end+timedelta(hours=12) if execution=='COMPLETED' else created).isoformat()}
            insert(c,'overtime',values);origin(identity,p,mid)
            if source:
                snapshot={k:values[k] for k in ('reference','description','justification','impact','in_lieu','scheduled_start','scheduled_end')}
                insert(c,'ot_group_activities',{'source_id':identity,'window_id':wid,'authorized_by':mid if status not in ('REJECTED',) and (not future or status=='APPROVED') else None,'snapshot':json.dumps(snapshot)})
            if execution=='COMPLETED' and kind!='HISTORICAL':
                insert(c,'timers',{'id':key(identity,'timer'),'user_id':p['id'],'overtime_id':identity,'start_at':start.isoformat(),'end_at':end.isoformat()});result['timers']+=1
            audit(identity,p['id'],'DEMO_CREATE_OT',created,{'capture_type':kind,'scenario':slot})
            if status=='APPROVED':audit(identity,mid,'DEMO_APPROVE_OT',max(end,created) if not future else created+timedelta(hours=1))
            elif status=='REJECTED':audit(identity,mid,'DEMO_REJECT_OT',created+timedelta(hours=1),{'reason':'[DEMO] Falta autorización para la intervención propuesta.'})
            result['overtime']+=1;covered.add(p['id']);used.add(mid)
        def rule(mid):
            rid=key('rule',mid)
            found=c.execute('SELECT * FROM rules WHERE id=?',(rid,)).fetchone()
            if found:return {**dict(found),'segments':json.loads(found['segments'])}
            segments=[{'day':d,'start':'20:00' if d<5 else '00:00','end':'00:00'} for d in range(7)]
            value={'id':rid,'manager_id':mid,'name':'[DEMO] Cobertura semanal de prueba','effective_from':'2026-05-01','segments':segments}
            insert(c,'rules',{**value,'segments':json.dumps(segments)});result['rules']+=1;return value
        for index,p in enumerate(people):
            g=groups.get(p['group_id']);mid=p.get('manager_id') if p['is_lead'] else g.get('manager_id') if g else None
            if mid not in managers:continue
            snapshot=rule(mid) if not p['is_lead'] else None
            for mi,period in enumerate(MONTHS):
                first=date.fromisoformat(period+'-01')
                if first>current.date():continue
                for slot,day,kind,status in [('plan-a',4,'PLANNED','APPROVED'),('plan-b',11,'PLANNED','APPROVED'),('plan-c',18,'PLANNED','APPROVED'),('incident',14,'EMERGENCY','APPROVED'),('exception',21,'HISTORICAL','APPROVED' if (index+mi)%3==0 else 'SUBMITTED'),('actual-review',24,'PLANNED','SUBMITTED'),('documentation',25,'EMERGENCY','DOCUMENTATION'),('rejected-plan',26,'PLANNED','REJECTED')]:
                    start=stamp(first.replace(day=day),20 if kind=='EMERGENCY' else 21)
                    duration=60+(index*19+mi*23)%150 if kind=='EMERGENCY' else 90+(index%4)*30+mi*15
                    end=start+timedelta(minutes=duration)
                    if end<=current:add_ot(p,mid,period,slot,kind,start,end,status)
                if snapshot:
                    saturday=first.replace(day=8)
                    while saturday.weekday()!=5:saturday+=timedelta(days=1)
                    for slot,a,b,status in [('week',saturday,saturday+timedelta(days=6),'APPROVED'),('day',first.replace(day=23),first.replace(day=23),'SUBMITTED' if index%2 else 'REJECTED')]:
                        if b>=current.date() or excluded(p,stamp(a),stamp(b)+timedelta(days=1)):continue
                        identity=key('guard',p['id'],period,slot)
                        if c.execute('SELECT 1 FROM guards WHERE id=?',(identity,)).fetchone():result['skipped_existing']+=1;continue
                        created=stamp(a)-timedelta(days=3)
                        insert(c,'guards',{'id':identity,'user_id':p['id'],'start_date':a.isoformat(),'end_date':b.isoformat(),'rule_snapshot':json.dumps(snapshot),'status':status,'approved_by':mid if status=='APPROVED' else None,'created_at':created.isoformat()})
                        origin(identity,p,mid);audit(identity,p['id'],'DEMO_REQUEST_GUARD',created)
                        if status=='APPROVED':audit(identity,mid,'DEMO_APPROVE_GUARD',created+timedelta(hours=1))
                        result['guards']+=1
            # Future November activities: approval and timer gating can be inspected without active timers.
            for slot,day,status in [('future-approved',4,'APPROVED'),('future-pending',9,'SUBMITTED')]:
                start=stamp(date(2026,11,day),21)
                if start>current:add_ot(p,mid,'2026-11',slot,'PLANNED',start,start+timedelta(hours=2),status,True)
            # A preapproved scheduled activity available now; never start a Timer automatically.
            start=current.replace(second=0,microsecond=0)-timedelta(minutes=15);end=start+timedelta(hours=2)
            add_ot(p,mid,current.date().isoformat(),'ready-today','PLANNED',start,end,'APPROVED',True)
        result['people']=len(covered);result['managers']=len(used)
        after=protected_october(c)
        if before!=after:raise ValueError('La protección de octubre de Samuel detectó un cambio; carga revertida.')
        if list(c.execute('PRAGMA foreign_key_check')):raise ValueError('Se detectó una referencia inválida; carga revertida.')
        result['protected_october_unchanged']=True;c.commit();return result
    except Exception:c.rollback();raise
    finally:c.close()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',default=os.environ.get('PULSE_DB_PATH',str(ROOT/'operational_pulse.db')));args=parser.parse_args()
    target=Path(args.db).resolve()
    if not target.exists() and target==(ROOT/'operational_pulse.db').resolve():
        bundled=ROOT/'fixtures/operacion_demo_2026.sqlite3'
        if not bundled.is_file():bundled=ROOT/'fixtures/banorte_pruebas.sqlite3'
        with bundled.open('rb') as source,target.open('xb') as destination:shutil.copyfileobj(source,destination)
    print(json.dumps(populate(target),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
