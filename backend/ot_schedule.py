"""Daily authorized work windows; real Timer segments remain the source of hours."""
import json,re
from datetime import datetime,time,timedelta,timezone
from fastapi import Body,Depends
from zoneinfo import ZoneInfo

def install_ot_schedule(app,n):
 connection=n['connection'];get=n['get'];fail=n['fail'];parse=n['parse_at']
 with connection(True) as c:
  c.execute('CREATE TABLE IF NOT EXISTS ot_policies(manager_id TEXT PRIMARY KEY REFERENCES users(id),enabled INTEGER NOT NULL,start_time TEXT NOT NULL,end_time TEXT NOT NULL,updated_at TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS ot_schedules(overtime_id TEXT PRIMARY KEY REFERENCES overtime(id),snapshot TEXT NOT NULL)')
 def policy(c,manager):
  row=c.execute('SELECT * FROM ot_policies WHERE manager_id=?',(manager,)).fetchone() if manager else None
  return {**dict(row),'enabled':bool(row['enabled']),'configured':True} if row else {'manager_id':manager,'enabled':False,'configured':False,'start_time':'21:00','end_time':'08:00','timezone':str(n['TZ'])}
 def snapshot(c,identity):
  row=c.execute('SELECT snapshot FROM ot_schedules WHERE overtime_id=?',(identity,)).fetchone()
  return json.loads(row['snapshot']) if row else None
 def windows(o,s):
  if not s:return [(parse(o['scheduled_start']),parse(o['scheduled_end']))]
  start,end=parse(o['scheduled_start']),parse(o['scheduled_end']);tz=ZoneInfo(s.get('timezone',str(n['TZ'])));day=start.astimezone(tz).date()-timedelta(days=1);last=end.astimezone(tz).date();result=[]
  if (last-day).days>33:fail('La programación diaria no puede exceder 31 días.')
  while day<=last:
   a=datetime.combine(day,time.fromisoformat(s['start_time']),tzinfo=tz);b=datetime.combine(day,time.fromisoformat(s['end_time']),tzinfo=tz)
   if b<=a:b+=timedelta(days=1)
   a=max(a,start);b=min(b,end)
   if b>a:result.append((a.astimezone(timezone.utc),b.astimezone(timezone.utc)))
   day+=timedelta(days=1)
  return result
 def request_schedule(c,actor,data,a,b):
  p=policy(c,n['owner_manager'](c,actor));requested=data.get('daily_window') in (True,'on','true','1',1)
  if not requested and not p['enabled']:return None
  s={k:p[k] for k in ('manager_id','start_time','end_time')};s['timezone']=str(n['TZ']);s['created_at']=n['now']()
  if not any(end>parse(n['now']()) for _,end in windows({'scheduled_start':a,'scheduled_end':b},s)):fail('No hay una ventana diaria futura dentro del periodo seleccionado. Revisa las fechas y el horario del Manager.')
  return s
 def store(c,identity,s):
  if s:c.execute('INSERT OR REPLACE INTO ot_schedules VALUES(?,?)',(identity,json.dumps(s)))
  else:c.execute('DELETE FROM ot_schedules WHERE overtime_id=?',(identity,))
 def availability(c,o,s=None):
  s=s if s is not None else snapshot(c,o['id']);stamp=parse(n['now']());slots=windows(o,s);active=next(((a,b) for a,b in slots if a<=stamp<b),None);upcoming=next(((a,b) for a,b in slots if a>stamp),None)
  return {'schedule':s,'window_open':bool(active),'window_end':active[1].isoformat() if active else None,'next_window_start':upcoming[0].isoformat() if upcoming else None,'next_window_end':upcoming[1].isoformat() if upcoming else None}
 def limit(c,o,start):
  s=snapshot(c,o['id']);instant=parse(start)
  if not s:return o['scheduled_end']
  tz=ZoneInfo(s.get('timezone',str(n['TZ'])));day=instant.astimezone(tz).date()
  for date in (day-timedelta(days=1),day):
   a=datetime.combine(date,time.fromisoformat(s['start_time']),tzinfo=tz);b=datetime.combine(date,time.fromisoformat(s['end_time']),tzinfo=tz)
   if b<=a:b+=timedelta(days=1)
   a=max(a,parse(o['scheduled_start']));b=min(b,parse(o['scheduled_end']))
   if a<=instant<b:return b.astimezone(timezone.utc).isoformat()
  return start
 n.update(ot_policy=policy,ot_schedule_snapshot=snapshot,ot_daily_windows=windows,ot_request_schedule=request_schedule,ot_store_schedule=store,ot_schedule_availability=availability,ot_timer_limit=limit)
 @app.get('/api/ot-policy')
 def get_policy(actor=Depends(n['current_user'])):
  with connection() as c:
   mid=actor['id'] if actor['role']=='MANAGER' else n['owner_manager'](c,actor) if actor['role']=='USER' else None
   if not mid:fail('El horario operativo corresponde al equipo de un Manager.',403)
   return policy(c,mid)
 @app.put('/api/ot-policy')
 def save_policy(data:dict=Body(...),actor=Depends(n['current_user'])):
  if actor['role']!='MANAGER':fail('Sólo el Manager configura el horario de su equipo.',403)
  a,b=str(data.get('start_time','')),str(data.get('end_time',''))
  for value in (a,b):
   if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',value):fail('Usa horas válidas HH:MM.')
  if a==b:fail('Inicio y fin deben ser distintos. Desactiva la restricción para permitir horario continuo.')
  if not isinstance(data.get('enabled'),bool):fail('Indica si el horario está habilitado.')
  with connection(True) as c:
   c.execute('INSERT OR REPLACE INTO ot_policies VALUES(?,?,?,?,?)',(actor['id'],int(data['enabled']),a,b,n['now']()));n['audit'](c,actor,'SET_OT_DAILY_POLICY',actor['id'],{'enabled':data['enabled'],'start':a,'end':b})
  return {'ok':True}

 @app.post('/api/overtime/{identity}/pause')
 def pause(identity:str,actor=Depends(n['current_user'])):
  n['operational'](actor)
  with connection(True) as c:
   o=get(c,'overtime',identity)
   if o['user_id']!=actor['id']:fail('Sólo el propietario pausa su Timer.',403)
   if o['execution']=='PAUSED':return {'ok':True}
   if o['capture_type']!='PLANNED' or o['execution']!='RUNNING':fail('No hay un Timer programado en curso.')
   t=c.execute('SELECT * FROM timers WHERE overtime_id=? AND end_at IS NULL',(identity,)).fetchone()
   if not t:fail('El Timer ya cambió; actualiza la vista.',409)
   stamp=n['now']();end=min(parse(stamp),parse(limit(c,o,t['start_at']))).isoformat()
   c.execute('UPDATE timers SET end_at=? WHERE id=?',(end,t['id']))
   c.execute("UPDATE overtime SET end_at=?,execution='PAUSED',updated_at=? WHERE id=?",(end,stamp,identity))
   n['audit'](c,actor,'PAUSE_PLANNED_TRANCHE',identity,{'end_at':end})
  return {'ok':True}
