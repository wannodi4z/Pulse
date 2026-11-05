"""Explicit organizational movements with four-sided executive consent and atomic application."""
import hashlib
import json
from fastapi import Body,Depends


def install_organization_transfers(app,n):
    connection=n['connection'];get=n['get'];rows=n['rows'];fail=n['fail'];audit=n['audit'];current=n['current_user'];admin=n['admin']
    with connection(True) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS organization_transfers(id TEXT PRIMARY KEY,subject_id TEXT NOT NULL REFERENCES users(id),created_by TEXT NOT NULL REFERENCES users(id),plan TEXT NOT NULL,fingerprint TEXT NOT NULL,reviewers TEXT NOT NULL,decisions TEXT NOT NULL,status TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)''')
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_open_organization_transfer ON organization_transfers(subject_id) WHERE status IN ('PENDING','READY')")

    def active(c,identity,role):
        p=get(c,'users',identity)
        if p['role']!=role or p['status']!='ACTIVE':fail('Selecciona un '+role+' activo.')
        return p

    def chain(c,manager):
        dpe=active(c,manager.get('parent_id'),'DPE');dp=active(c,dpe.get('parent_id'),'DP')
        if dpe['account_id']!=manager['account_id'] or dp['account_id']!=manager['account_id']:fail('Completa una jerarquía coherente DP/DPE en ambas Cuentas.')
        return dpe,dp

    def build(c,data):
        subject=get(c,'users',data.get('subject_id'))
        if subject['status']!='ACTIVE' or not(subject['role']=='MANAGER' or subject['role']=='USER' and subject['is_lead']):fail('Sólo se trasladan Managers o Leads activos.')
        source=subject if subject['role']=='MANAGER' else active(c,subject['manager_id'],'MANAGER')
        source_dpe,source_dp=chain(c,source)
        if subject['role']=='MANAGER':
            target=active(c,data.get('target_id'),'DPE');target_dp=active(c,target.get('parent_id'),'DP')
            if target['account_id']!=target_dp['account_id']:fail('La jerarquía de destino no es válida.')
            if target['id']==subject.get('parent_id'):fail('Selecciona un DPE de destino distinto del actual.')
            target_dpe=target;groups=[g for g in rows(c,'groups') if g['manager_id']==subject['id']]
            requested=data.get('groups',{})
            if not isinstance(requested,dict) or set(requested)!={g['id'] for g in groups}:fail('Revisa el destino de todos los Grupos del Manager.')
            destinations={}
            for g in groups:
                destination=requested[g['id']]
                if destination=='FOLLOW':destinations[g['id']]='FOLLOW'
                else:
                    replacement=active(c,destination,'MANAGER')
                    if replacement['id']==subject['id'] or replacement['account_id']!=source['account_id']:fail('Los Grupos que permanecen requieren otro Manager activo de origen.')
                    destinations[g['id']]=replacement['id']
            leads=[p for p in rows(c,'users') if p['is_lead'] and p['manager_id']==subject['id'] and p['status']!='DISABLED']
            lead_target=data.get('lead_target','FOLLOW')
            if leads and lead_target!='FOLLOW':
                replacement=active(c,lead_target,'MANAGER')
                if replacement['id']==subject['id'] or replacement['account_id']!=source['account_id']:fail('El Lead que permanece necesita otro Manager de origen.')
                if c.execute("SELECT 1 FROM users WHERE is_lead=1 AND manager_id=? AND status!='DISABLED'",(lead_target,)).fetchone():fail('El Manager de destino del Lead ya tiene un Lead.')
            elif not leads:lead_target='FOLLOW'
            cohort=[p for p in rows(c,'users') if p['group_id'] in destinations or p['id'] in {l['id'] for l in leads}]
            plan={'subject_id':subject['id'],'target_id':target['id'],'groups':destinations,'lead_target':lead_target}
        else:
            target=active(c,data.get('target_id'),'MANAGER');target_dpe,target_dp=chain(c,target)
            if target['id']==source['id']:fail('Selecciona otro Manager.')
            if c.execute("SELECT 1 FROM users WHERE is_lead=1 AND manager_id=? AND status!='DISABLED' AND id<>?",(target['id'],subject['id'])).fetchone():fail('El Manager de destino ya tiene un Lead.')
            groups=[];cohort=[subject];leads=[subject];plan={'subject_id':subject['id'],'target_id':target['id'],'groups':{},'lead_target':'FOLLOW'}
        if subject['role']=='MANAGER' and source['account_id']!=target['account_id'] and any(v=='FOLLOW' for v in plan['groups'].values()) and get(c,'accounts',target['account_id'])['country_code'] not in n['COUNTRY_CODES']:fail('Define el país de la Cuenta de destino antes de mover Grupos.')
        participants={}
        for side,dpe,dp in [('Origen',source_dpe,source_dp),('Destino',target_dpe,target_dp)]:
            for person in (dpe,dp):
                item=participants.setdefault(person['id'],{'id':person['id'],'name':person['first']+' '+person['last'],'role':person['role'],'sides':[]});item['sides'].append(side)
        tracked=[subject,source,target,source_dpe,source_dp,target_dpe,target_dp,*cohort]
        for mid in set(plan['groups'].values())|{plan['lead_target']}:
            if mid!='FOLLOW':
                tracked.append(get(c,'users',mid));tracked.extend(p for p in rows(c,'users') if p['is_lead'] and p['manager_id']==mid)
        identity_fields=('id','role','status','account_id','group_id','manager_id','parent_id','is_lead')
        evidence={'plan':plan,'people':sorted([{k:p.get(k) for k in identity_fields} for p in {p['id']:p for p in tracked}.values()],key=lambda p:p['id']),'groups':sorted(groups,key=lambda g:g['id']),'delegations':[d for d in rows(c,'delegations') if not d['revoked_at'] and (d['manager_id']==source['id'] or d['lead_id'] in {p['id'] for p in cohort})]}
        fingerprint=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
        names=lambda p:{k:p.get(k) for k in ('id','first','last','employee_id','role')}
        affected={p['id'] for p in cohort}
        impact={'active_timers':sum(t['user_id'] in affected and not t['end_at'] for t in rows(c,'timers')),'pending_hours':sum(r['user_id'] in affected and r['status']=='SUBMITTED' for table in ('overtime','guards') for r in rows(c,table)),'pending_moves':sum(r['user_id'] in affected and r['status']=='SUBMITTED' for table in ('manager_transfers','transfer_requests') for r in rows(c,table))}
        details={'impact':impact,'subject':names(subject),'source_manager':names(source),'source_account':get(c,'accounts',source['account_id']),'target_account':get(c,'accounts',target['account_id']),'target':names(target),'groups':[{'id':g['id'],'name':g['name'],'destination':plan['groups'][g['id']],'technicians':sum(p['group_id']==g['id'] for p in cohort)} for g in groups],'people':[names(p) for p in cohort],'source_dpe':names(source_dpe),'target_dpe':names(target_dpe)}
        return plan,fingerprint,list(participants.values()),details

    def visible(actor,record):return actor['role']=='ADMIN' or actor['id']==record['subject_id'] or actor['id'] in {r['id'] for r in json.loads(record['reviewers'])}

    def present(c,record):
        result={**record,'plan':json.loads(record['plan']),'reviewers':json.loads(record['reviewers']),'decisions':json.loads(record['decisions'])}
        if record['status'] not in ('PENDING','READY'):
            result['stale']=False;result['details']=result['plan'].get('snapshot',{});result.pop('fingerprint',None);return result
        try:
            _,fingerprint,_,details=build(c,result['plan']);result['stale']=fingerprint!=record['fingerprint'];result['details']=details
        except Exception as error:
            from fastapi import HTTPException
            if not isinstance(error,HTTPException):raise
            result['stale']=True;result['details']=json.loads(record['plan']).get('snapshot',{})
        result.pop('fingerprint',None)
        return result

    @app.get('/api/organization-transfers')
    def listing(actor=Depends(current)):
        with connection() as c:return [present(c,r) for r in rows(c,'organization_transfers') if visible(actor,r)]

    @app.post('/api/organization-transfers/preview')
    def preview(data:dict=Body(...),actor=Depends(admin)):
        with connection() as c:
            plan,fingerprint,reviewers,details=build(c,data)
            return {'plan':plan,'fingerprint':fingerprint,'reviewers':reviewers,'details':details}

    @app.post('/api/organization-transfers')
    def create(data:dict=Body(...),actor=Depends(admin)):
        reason=n['text'](data,'reason')
        with connection(True) as c:
            plan,fingerprint,reviewers,details=build(c,data)
            if data.get('fingerprint')!=fingerprint:fail('El equipo cambió; revisa nuevamente la propuesta.',409)
            plan['snapshot']=details
            if c.execute("SELECT 1 FROM organization_transfers WHERE subject_id=? AND status IN ('PENDING','READY')",(plan['subject_id'],)).fetchone():fail('La persona ya tiene un traslado en curso.',409)
            identity=n['uid']();stamp=n['now']()
            c.execute('INSERT INTO organization_transfers VALUES(?,?,?,?,?,?,?,?,?,?,?)',(identity,plan['subject_id'],actor['id'],json.dumps(plan),fingerprint,json.dumps(reviewers),'{}','PENDING',reason,stamp,stamp))
            audit(c,actor,'REQUEST_ORGANIZATION_TRANSFER',identity,{'reason':reason})
        return {'id':identity}

    @app.post('/api/organization-transfers/{identity}/decision')
    def decision(identity:str,data:dict=Body(...),actor=Depends(current)):
        value=data.get('decision');reason=n['text'](data,'reason')
        if value not in ('APPROVED','REJECTED'):fail('Decisión inválida.')
        with connection(True) as c:
            r=get(c,'organization_transfers',identity)
            if actor['role'] not in ('DP','DPE') or actor['id'] not in {p['id'] for p in json.loads(r['reviewers'])}:fail('No te corresponde autorizar este traslado.',403)
            if r['status']!='PENDING':fail('La solicitud ya no está pendiente.',409)
            _,fingerprint,_,_=build(c,json.loads(r['plan']))
            if fingerprint!=r['fingerprint']:fail('La estructura cambió. Admin debe preparar una nueva solicitud.',409)
            decisions=json.loads(r['decisions'])
            if actor['id'] in decisions:fail('Ya registraste tu decisión.',409)
            decisions[actor['id']]={'decision':value,'reason':reason,'at':n['now']()}
            status='REJECTED' if value=='REJECTED' else 'READY' if len(decisions)==len(json.loads(r['reviewers'])) else 'PENDING'
            c.execute('UPDATE organization_transfers SET decisions=?,status=?,updated_at=? WHERE id=?',(json.dumps(decisions),status,n['now'](),identity))
            audit(c,actor,'DECIDE_ORGANIZATION_TRANSFER',identity,{'decision':value,'reason':reason})
        return {'ok':True,'status':status}

    @app.post('/api/organization-transfers/{identity}/cancel')
    def cancel(identity:str,data:dict=Body(...),actor=Depends(admin)):
        reason=n['text'](data,'reason')
        with connection(True) as c:
            r=get(c,'organization_transfers',identity)
            if r['status'] not in ('PENDING','READY'):fail('La solicitud ya terminó.',409)
            c.execute("UPDATE organization_transfers SET status='CANCELLED',updated_at=? WHERE id=?",(n['now'](),identity));audit(c,actor,'CANCEL_ORGANIZATION_TRANSFER',identity,{'reason':reason})
        return {'ok':True}

    @app.post('/api/organization-transfers/{identity}/apply')
    def apply(identity:str,data:dict=Body(...),actor=Depends(admin)):
        if data.get('confirm') is not True:fail('Confirma la aplicación del traslado.')
        with connection(True) as c:
            r=get(c,'organization_transfers',identity)
            if r['status']!='READY':fail('Faltan autorizaciones o el traslado ya terminó.',409)
            plan,fingerprint,_,details=build(c,json.loads(r['plan']))
            if fingerprint!=r['fingerprint']:fail('La estructura cambió. Cancela y prepara otra solicitud.',409)
            ids={p['id'] for p in details['people']}
            if any(t['user_id'] in ids and not t['end_at'] for t in rows(c,'timers')):fail('Hay Timers activos en el equipo afectado. Deténlos antes de aplicar.',409)
            if any(t['user_id'] in ids and t['status']=='SUBMITTED' for table in ('manager_transfers','transfer_requests') for t in rows(c,table)):fail('Resuelve los movimientos de Técnicos pendientes antes de aplicar.',409)
            subject=get(c,'users',plan['subject_id']);source=subject if subject['role']=='MANAGER' else get(c,'users',subject['manager_id']);target=get(c,'users',plan['target_id'])
            for person_id in ids:
                person=get(c,'users',person_id)
                for table in ('overtime','guards'):
                    for record in c.execute('SELECT id FROM '+table+' WHERE user_id=?',(person_id,)).fetchall():n['capture_origin'](c,record['id'],person,inferred=True)
            n['revoke_authority'](c,actor,r['reason'],manager_ids=[source['id']] if subject['role']=='MANAGER' else [],lead_ids=[p['id'] for p in details['people'] if get(c,'users',p['id'])['is_lead']])
            if subject['role']=='MANAGER':
                account=get(c,'accounts',target['account_id'])
                for gid,destination in plan['groups'].items():
                    if destination=='FOLLOW':
                        group=get(c,'groups',gid)
                        if group['account_id']!=target['account_id']:
                            code=n['standard_group_code'](c,account,group['platform_code'] or 'OTHER',group['service_key'] or 'GENERAL')
                            c.execute('UPDATE groups SET account_id=?,code=?,standard_code=? WHERE id=?',(target['account_id'],code,code,gid))
                    else:c.execute('UPDATE groups SET manager_id=? WHERE id=?',(destination,gid))
                if plan['lead_target']!='FOLLOW':c.execute("UPDATE users SET manager_id=? WHERE manager_id=? AND is_lead=1 AND status!='DISABLED'",(plan['lead_target'],subject['id']))
                c.execute('UPDATE users SET account_id=?,parent_id=? WHERE id=?',(target['account_id'],target['id'],subject['id']))
            else:c.execute('UPDATE users SET manager_id=? WHERE id=?',(target['id'],subject['id']))
            n['validate_manager_leads'](c,[source['id'],target['id']] if subject['role']!='MANAGER' else [subject['id']])
            n['reopen_recoveries'](c,actor,ids,r['reason'])
            c.execute("UPDATE organization_transfers SET status='APPLIED',updated_at=? WHERE id=?",(n['now'](),identity));audit(c,actor,'APPLY_ORGANIZATION_TRANSFER',identity,{'plan':plan,'reason':r['reason']})
        return {'ok':True}
