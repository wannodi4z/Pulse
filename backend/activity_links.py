"""Activity links are identifiers, not credentials or permission grants."""
from fastapi import Depends

def install_activity_links(app,n):
 @app.get('/api/activities/{identity}')
 def activity(identity:str,actor=Depends(n['current_user'])):
  n['operational'](actor)
  with n['connection']() as c:
   window=c.execute('SELECT * FROM windows WHERE id=?',(identity,)).fetchone();own=None
   if window:
    w=dict(window);own=c.execute('SELECT * FROM overtime WHERE window_id=? AND user_id=?',(identity,actor['id'])).fetchone()
    if not own and (actor['is_lead'] or actor['group_id']!=w['group_id']):n['fail']('Actividad fuera de tu alcance.',404)
    reference=w['reference'];start=w['scheduled_start'];end=w['scheduled_end'];approved=w['status']=='APPROVED'
   else:
    own=c.execute('SELECT * FROM overtime WHERE id=? AND user_id=?',(identity,actor['id'])).fetchone()
    if not own or own['capture_type']!='PLANNED':n['fail']('Actividad fuera de tu alcance.',404)
    reference=own['reference'];start=own['scheduled_start'];end=own['scheduled_end'];approved=own['status']=='APPROVED'
   active=c.execute('SELECT * FROM timers WHERE user_id=? AND end_at IS NULL',(actor['id'],)).fetchone()
   same=bool(active and own and active['overtime_id']==own['id']);eligible=approved and (not own or own['status']=='APPROVED' and own['execution'] in ('SCHEDULED','PAUSED')) and not active
   current=n['parse_at'](n['now']());ready=eligible and n['parse_at'](start)<=current<n['parse_at'](end)
   return {'id':identity,'reference':reference,'start_at':start,'end_at':end,'approved':approved,'eligible':bool(eligible),'can_start':bool(ready),'overtime_id':own['id'] if own else None,'window_id':w['id'] if window else None,'active_same':same,'active_other':bool(active and not same),'execution':own['execution'] if own else 'SCHEDULED'}
