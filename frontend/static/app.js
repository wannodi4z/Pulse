'use strict';
// One state owner, one central route, one event controller. No route changes on polling.
let state = null;
let page = 'dashboard';
let month = new Date().toLocaleDateString('sv-SE', {timeZone:state?.timezone||'America/Mexico_City'}).slice(0,7);
let ledger = {rows:[],ot_minutes:0,guard_minutes:0};
let pageEntrance = true;
let analyticsReport = null;
let analyticsRequestKey = '';
let analyticsFailure = null;
let analyticsDetailType = null;
let comparisonMonths = [];
let comparisonDraft = [];
let analyticsSearchTimer;
let reportSequence = 0;
const analyticsTypes = ['EMERGENCY','PLANNED','HISTORICAL','GUARD'];
const analyticsNames = {EMERGENCY:'OT emergente',PLANNED:'OT programada',HISTORICAL:'OT histórica',GUARD:'Guardia neta',ALL:'Todas las horas'};
const analyticsColors = {EMERGENCY:'#2469cf',PLANNED:'#24a8ca',HISTORICAL:'#758cba',GUARD:'#25b4a4'};
let filters = {group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};
let delegationDraftLead = '';
let busy = false;
let renderDeferred = false;
let draggedTechnician = null;
let refreshSequence = 0;
let toastTimer;
let serverOffset = 0;
const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const full = person => person ? `${person.first} ${person.last}`.trim() : 'Sin asignar';
const person = id => state?.people.find(p=>p.id===id)||state?.audit_people?.find(p=>p.id===id);
const group = id => state?.groups.find(g=>g.id===id);
const manager = gid => person(group(gid)?.manager_id);
const ownerOf = p => p?.is_lead?p.manager_id:group(p?.group_id)?.manager_id;
const me = () => state?.user;
const isAdmin = () => me()?.role==='ADMIN';
const isManager = () => me()?.role==='MANAGER';
const isTech = () => me()?.role==='USER';
const roles = {ADMIN:'Administrador',MANAGER:'Manager',USER:'Técnico'};
const statuses = {ACTIVE:'Activo',DISABLED:'Baja',PENDING_ACTIVATION:'Activación pendiente',SUBMITTED:'Pendiente',APPROVED:'Aprobado',REJECTED:'Rechazado',DOCUMENTATION:'Por documentar',RUNNING:'En curso',PAUSED:'Pausada',SCHEDULED:'Programado',COMPLETED:'Finalizado',PENDING:'Pendiente',ISSUED:'Código emitido',USED:'Recuperado',CANCELLED:'Cancelado',EXPIRED:'Vencido'};
const pageNames = {dashboard:'Panel',analytics:'Analítica',myAnalytics:'Mi analítica',records:'Consulta de registros',myRecords:'Mis registros',organization:'Cuentas',admins:'Administradores',recoveries:'Recuperación de acceso',profile:'Mi perfil',team:'Mi equipo',teamTime:'Aprobaciones',timeRules:'Reglas de guardia',time:'Mi tiempo',claim:'Claim',adp:'ADP'};
const icon = name => `<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true"><use href="/static/icons.svg#${name}"></use></svg>`;
const projectAuthors = ['Samuel Alejandro Díaz Chávez', 'Francisco Cervantes Marquez'];
const kyndrylBrand = () => '<img class="kyndryl-logo" src="/static/kyndryl-logo.svg" alt="Kyndryl" width="80" height="24">';
const initials = p => `${p?.first?.[0]||''}${p?.last?.[0]||''}`.toUpperCase();
const fmtDate = v => v ? new Date(v.length===10?`${v}T12:00:00`:v).toLocaleDateString('es-MX',{day:'2-digit',month:'short',year:'numeric',timeZone:state?.timezone||'America/Mexico_City'}) : '—';
const fmtTime = v => v ? new Date(v).toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:state?.timezone||'America/Mexico_City'}) : '—';
const range = (a,b) => `${fmtDate(a)} · ${fmtTime(a)} — ${fmtDate(b)} · ${fmtTime(b)}`;
const hours = n => new Intl.NumberFormat('es-MX',{maximumFractionDigits:2}).format((n||0)/60);
const hm = n => `${Math.floor(Math.round(n||0)/60).toString().padStart(2,'0')}:${(Math.round(n||0)%60).toString().padStart(2,'0')}`;
const badge = status => `<span class="badge ${esc(status.toLowerCase())}"><i></i>${esc(statuses[status]||status)}</span>`;
const btn = (text,action,id='',cls='secondary',attrs='') => `<button type="button" ${attrs} class="${cls}" data-action="${action}" data-id="${esc(id)}">${text}</button>`;
const field = (name,label,value='',type='text',attrs='') => `<label class="field"><span>${label}</span><input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`;
const select = (name,label,html,attrs='') => `<label class="field"><span>${label}</span><select name="${name}" ${attrs}>${html}</select></label>`;
const options = (items,current,label=x=>x.name,empty='') => (empty?`<option value="">${empty}</option>`:'')+items.map(x=>`<option value="${esc(x.id)}" ${x.id===current?'selected':''}>${esc(label(x))}</option>`).join('');
const empty = (title,copy='') => `<div class="empty"><span class="empty-icon">${icon('organization')}</span><h3>${title}</h3>${copy?`<p>${copy}</p>`:''}</div>`;
const identity = p => `<span class="avatar">${esc(initials(p))}</span><span class="identity"><strong>${esc(full(p))}</strong><small>${esc(p.employee_id||p.username)}</small></span>`;
const heading = (eyebrow,title,copy,actions='') => `<header class="page-heading"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${copy}</p></div><div class="heading-actions">${actions}</div></header>`;
const monthLabel = value => new Date(`${value}-15T12:00:00`).toLocaleDateString('es-MX',{month:'long',year:'numeric'});
const monthControl = () => `<div class="month-control">${btn('‹','month-prev','','icon-btn','aria-label="Mes anterior"')}<label><span class="sr-only">Mes de consulta</span><input type="month" id="month" value="${esc(month)}" aria-label="Mes de consulta"></label>${btn('›','month-next','','icon-btn','aria-label="Mes siguiente"')}</div>`;

async function api(path,method='GET',data){
  const response=await fetch(path,{method,credentials:'same-origin',headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined});
  const result=await response.json().catch(()=>({}));
  if(!response.ok){if(response.status===401&&state){state=null;$('#modal').close();render();}const error=Error(typeof result.detail==='string'?result.detail:'No se pudo completar la operación. Revisa los datos.');error.status=response.status;throw error;}
  return result;
}
function toast(message,error=false){
  const el=$('#toast');el.textContent=message;el.className=`visible ${error?'error':''}`;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.className='',5000);
}
function showModal(title,body,wide=false){
  const symbol=/Mover|Transferir/i.test(title)?'arrow':/persona|Técnico|Manager|administrador/i.test(title)?'team':/Guardia/i.test(title)?'timeRules':/OT|tiempo/i.test(title)?'time':/Cuenta|Grupo/i.test(title)?'organization':/baja|acceso|contraseña|Reactivar/i.test(title)?'lock':'info';
  const modal=$('#modal');modal.innerHTML=`<header class="dialog-header"><span class="dialog-emblem">${icon(symbol)}</span><div><p class="eyebrow">OPERATIONAL PULSE</p><h2 id="dialog-title">${title}</h2></div><button class="icon-btn" data-action="close" aria-label="Cerrar">×</button></header>${body}`;modal.className=wide?'wide':'';modal.setAttribute('aria-labelledby','dialog-title');if(modal.querySelector('[data-form=confirmation],[data-form=reject],[data-form=reactivate],.secret-code'))modal.classList.add('compact-dialog');else if(modal.querySelector('[data-form=guard],.about-project'))modal.classList.add('medium-dialog');if(state&&(isAdmin()||isManager())&&modal.querySelector('[data-form=person],[data-form=account],[data-form=offboard],[data-form=reactivate],[data-form=confirmation],.secret-code')){modal.classList.add('admin-dialog');if(modal.querySelector('[data-form=person]'))modal.classList.add('admin-person-dialog');if(modal.querySelector('[data-form=offboard]'))modal.classList.add('admin-offboard-dialog');if(modal.querySelector('.secret-code'))modal.classList.add('admin-code-dialog');}if(!modal.open)modal.showModal();queueMicrotask(()=>PulseLayout.dialog());
}
const formGuidance={account:'Define un código único y un nombre para identificar la Cuenta.',group:'Selecciona la Cuenta y su Manager. Los cambios de responsable requieren un motivo y conservan el equipo.',person:'Completa la identidad y la asignación. Sólo Admin administra personas; los nuevos accesos requieren activación.',ot:'Completa el periodo y la actividad para enviarlos a aprobación.',guard:'Selecciona las fechas y la regla de cobertura. La OT aprobada se descontará de la Guardia.',rule:'Configura uno o varios intervalos por día. Usa 24 horas para cobertura continua.',window:'Define el Grupo, el periodo y la actividad programada. Los Técnicos del Grupo podrán registrar su participación.',reject:'Explica qué debe corregirse. El registro conservará el motivo en su historial.',transfer:'Revisa el destino y el motivo. El Técnico conserva su estado y su historial; el acceso se actualizará.', 'group-transfer':'Elige un Manager activo de la misma Cuenta. El equipo y sus registros permanecen; la delegación anterior se revoca.',offboard:'Resuelve los destinos y pendientes antes de retirar el acceso.',reactivate:'Explica el motivo. Comparte el código nuevo por un canal corporativo para que la persona active su acceso.'};
function form(name,body,id='',submit='Guardar'){
  return `<form data-form="${name}" data-id="${esc(id)}"><div class="form-body">${formGuidance[name]?`<p class="form-instructions"><strong>Antes de enviar</strong>${formGuidance[name]}</p>`:''}${body}</div><p class="form-error" role="alert"></p><footer class="dialog-footer"><button type="button" class="secondary" data-action="close">Cancelar</button><button class="primary" type="submit">${submit}</button></footer></form>`;
}
function credentials(code,username,title='Datos de activación'){
  showModal(title,`<div class="form-body"><p>Entrega este código por un canal corporativo. La persona definirá su contraseña desde «Activar cuenta».</p>${username?`<p>Usuario: <strong>${esc(username)}</strong></p>`:''}<div class="secret-code">${esc(code)}</div><p class="muted">El código se muestra sólo al generar o regenerar el acceso.</p></div><footer class="dialog-footer">${btn('Listo','close','','primary')}</footer>`);
}
function login(){
 return `<div class="login-shell"><section class="login-story"><a class="brand login-brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>Operational<strong>Pulse</strong></span></a><div class="story-copy"><p class="eyebrow">OPERACIÓN CONECTADA</p><h1>Tu tiempo.<br><span>En orden.</span></h1><p>Planea tu actividad, registra tus horas y mantén a tu equipo en sincronía.</p><div class="login-capabilities"><div>${icon('time')}<span>OT y Guardias<strong>Cada actividad en su calendario.</strong></span></div><div>${icon('team')}<span>Tu equipo, conectado<strong>Seguimiento y aprobaciones en un lugar.</strong></span></div><div>${icon('analytics')}<span>Horas que se entienden<strong>Analítica y guías para Claim y ADP.</strong></span></div></div></div><footer><div class="login-brand-credit">${kyndrylBrand()}<span>Operational Pulse</span></div><span class="release-tag">v1.0.20</span></footer></section><main class="login-main"><div class="login-mobile-brand"><img src="/static/favicon.svg" alt=""><span>Operational<strong>Pulse</strong></span></div><div class="login-card"><span class="login-access-icon" aria-hidden="true">${icon('lock')}</span><p class="eyebrow">TU ESPACIO DE TRABAJO</p><h2>Bienvenido a Pulse</h2><p class="muted">Ingresa con tu Employee ID o usuario administrador.</p><form data-form="login">${field('identity','Employee ID o usuario','','text','required autocomplete="username" placeholder="Ej. 951357" autocapitalize="none" spellcheck="false"')}<label class="field" for="login-password"><span>Contraseña</span><span class="login-password-input"><input id="login-password" name="password" type="password" required autocomplete="current-password" placeholder="Ingresa tu contraseña"><button type="button" class="password-visibility" data-action="password-visibility" data-id="login-password" aria-label="Mostrar contraseña" aria-pressed="false">${icon('eye')}</button></span></label><p class="form-error" role="alert"></p><button type="submit" class="primary login-submit"><span>Iniciar sesión</span>${icon('arrow')}</button></form><div class="login-links">${btn('¿Olvidaste tu contraseña?','recovery-request','','link')}${btn('Activar cuenta','activate','','link')}</div><div class="login-note">${icon('info')}<p>¿Es tu primer acceso?<br><span>Usa el código de activación que recibiste.</span></p></div></div><footer><span>Operational Pulse · v1.0.20</span><button type="button" class="link" data-action="about">Acerca del proyecto ${icon('forward')}</button></footer></main></div>`;
}
function nav(){
  const work=isAdmin()?['dashboard','organization','admins','recoveries']:isManager()?['dashboard','team','teamTime','analytics','records']:['dashboard','time','myAnalytics','myRecords','claim','adp',...(state.can_approve?['team','teamTime','analytics','records']:[])];
  const settings=isAdmin()?[]:isManager()?['timeRules','recoveries']:[];
  const item=p=>`<button class="nav-item ${p===page?'active':''}" data-page="${p}" ${p===page?'aria-current="page"':''}><span class="nav-icon" aria-hidden="true">${icon(['records','myRecords'].includes(p)?'search':p)}</span><span class="nav-text">${pageNames[p]}</span>${p==='teamTime'&&pendingCount()?`<b>${pendingCount()}</b>`:''}</button>`;
  return `<aside class="sidebar enterprise-sidebar"><a class="brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span class="brand-title"><small>OPERATIONAL</small><strong>Pulse</strong></span></a><nav aria-label="Navegación principal"><p class="nav-label">ESPACIO DE TRABAJO</p>${work.map(item).join('')}${settings.length?'<div class="nav-secondary">'+settings.map(item).join('')+'</div>':''}</nav><div class="sidebar-utility"><button type="button" data-action="about">${icon('info')}<span>Acerca del proyecto</span>${icon('forward')}</button></div></aside>`;
}
function userMenu(){return `<details class="user-menu"><summary aria-label="Menú de usuario"><span class="avatar" aria-hidden="true">${esc(initials(me()))}</span><span class="user-button-copy"><strong>${esc(full(me()))}</strong><small>${esc(me().is_lead?'Lead':roles[me().role])} · ${esc(me().employee_id||me().username||'')}</small></span><span class="user-chevron" aria-hidden="true">⌄</span></summary><div><button data-page="profile">${icon('profile')} Mi perfil</button>${btn(icon('arrow')+'Cerrar sesión','logout','','logout')}</div></details>`;}
function pendingCount(){return state?[...state.overtime,...state.guards].filter(r=>r.status==='SUBMITTED'&&r.user_id!==me().id).length+(state.extensions||[]).filter(e=>e.status==='SUBMITTED'&&e.requested_by!==me().id).length:0;}
function content(){
  switch(page){
    case 'analytics':return analyticsPage(false);
    case 'myAnalytics':return analyticsPage(true);
    case 'records':return unifiedAnalyticsPage(false,true);
    case 'myRecords':return unifiedAnalyticsPage(true,true);
    case 'organization':return isAdmin()?organizationPage():dashboard();
    case 'admins':return isAdmin()?adminsPage():dashboard();
    case 'recoveries':return recoveriesPage();
    case 'profile':return profilePage();
    case 'team':return teamPage();
    case 'teamTime':return teamTimePage();
    case 'timeRules':return rulesPage();
    case 'time':return timePage();
    case 'claim':return capturePage('claim');
    case 'adp':return capturePage('adp');
    default:return dashboard();
  }
}
function app(){
  return `<a class="skip-link" href="#main">Ir al contenido principal</a><div class="shell">${nav()}<div class="workspace"><header class="topbar"><div class="topbar-context"><div class="product-signature corporate-signature">${kyndrylBrand()}</div><div class="breadcrumb"><span class="breadcrumb-home">${icon("dashboard")}</span> Espacio de trabajo <span>/</span> <strong>${pageNames[page]||'Panel'}</strong></div></div><div class="topbar-right"><div class="clock-block"><small>HORA LOCAL · MX</small><span class="local-time" data-local-clock></span></div><div class="topbar-person">${userMenu()}</div></div></header><main id="main" tabindex="-1">${content()}<footer class="main-footer"><span>Operational Pulse <b class="footer-version">v${esc(state.version)}</b></span><span class="footer-credit">Diseñado para una operación más clara.</span></footer></main></div></div>`;
}
function render(){
  renderDeferred=false;
  if(draggedTechnician)endTechnicianDrag();
  closeEntityMenu();closeGroupSearch();
  $('#app').innerHTML=state?app():login();if(state)PulseLayout.page($('#main'),page);if(state&&pageEntrance){$('#main')?.classList.add('view-enter');pageEntrance=false;}if(state&&isManager()&&page==='team')filterTeamBoard();if(state&&innerWidth<=700){const active=$('.sidebar [aria-current=page]'),nav=$('.sidebar nav');if(active&&nav)nav.scrollLeft=Math.max(0,active.offsetLeft-nav.clientWidth/2+active.offsetWidth/2);}tick();
}
async function loadLedger(){
  if(!state)return;
  const sequence=++reportSequence,reportPage=page,q=new URLSearchParams({month});
  if(['dashboard','time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);
  else if(!['myAnalytics','myRecords'].includes(page)){if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);}
  if(['analytics','myAnalytics','records','myRecords'].includes(reportPage))appendAnalyticsQuery(q);
  if(['analytics','myAnalytics','records','myRecords'].includes(reportPage)){
    try{
      const report=await api((['myAnalytics','myRecords'].includes(reportPage)?'/api/my-analytics?':'/api/analytics?')+q);
      if(sequence!==reportSequence||page!==reportPage)return;
      analyticsRequestKey=reportPage+':'+q.toString();analyticsFailure=null;analyticsReport=report;ledger={rows:report.rows,ot_minutes:report.summary.ot_minutes,guard_minutes:report.summary.GUARD};
    }catch(error){
      if(sequence===reportSequence&&page===reportPage){analyticsFailure={key:reportPage+':'+q.toString(),message:error.message};render();}
      if(error.status===403&&['analytics','records'].includes(reportPage)){
        analyticsReport=null;analyticsDetailType=null;state=await api('/api/state');page=isTech()?'myAnalytics':'dashboard';filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};await loadLedger();render();
      }
      throw error;
    }
  }else{
    if(reportPage==='claim')q.set('view','claim');const result=await api('/api/accounting?'+q);if(sequence===reportSequence&&page===reportPage)ledger=result;
  }
}

async function refresh(silent=false){
  const sequence=++refreshSequence;
  try{
    const fresh=await api('/api/state');if(sequence!==refreshSequence||silent&&(draggedTechnician||calendarDrag||chartResizeActive()))return;
    serverOffset=new Date(fresh.server_time).getTime()-Date.now();
    const previous=state?JSON.stringify({...state,server_time:''}):'';
    state=fresh;
    const lostAnalytics=['analytics','records'].includes(page)&&!isManager()&&!fresh.can_approve;
    if(lostAnalytics){page=isTech()?'myAnalytics':'dashboard';analyticsReport=null;analyticsDetailType=null;filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};}
    await loadLedger();if(sequence!==refreshSequence)return;
    if(!silent||lostAnalytics||renderDeferred||previous!==JSON.stringify({...state,server_time:''})){
      if(!silent||lostAnalytics||!draggedTechnician&&!$('#modal').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))render();else renderDeferred=true;
    }
  }catch(error){if(!silent)throw error;}
}
async function navigate(next){
  if(!state)return;pageEntrance=true;page=next;filters={group:'',person:'',status:next==='teamTime'?'SUBMITTED':'',kind:'',search:'',period:next==='teamTime'?'ALL':'MONTH'};comparisonMonths=[];clearTimeout(analyticsSearchTimer);delegationDraftLead='';analyticsDetailType=null;
  $('#modal').close();await loadLedger();render();$('#main')?.focus({preventScroll:true});
}
function tick(){
  const code=$('[data-code-expires]');if(code&&new Date(code.dataset.codeExpires).getTime()<=Date.now()+serverOffset){code.textContent='Código vencido';code.removeAttribute('data-code-expires');}
  $$('[data-elapsed]').forEach(el=>{const current=Date.now()+serverOffset,limit=el.dataset.until?new Date(el.dataset.until).getTime():current,total=Math.max(0,Math.floor((Math.min(current,limit)-new Date(el.dataset.elapsed).getTime())/1000)+Math.floor(Number(el.dataset.base)||0));if(el.dataset.until&&current>=limit&&!el.dataset.reconciled){el.dataset.reconciled='true';refresh(true).then(()=>{const modal=$('#modal');if(state&&modal.open&&modal.classList.contains('own-timer-dialog')){const o=state.overtime.find(o=>o.id===modal.dataset.overtimeId);if(o&&(o.execution!=='RUNNING'||new Date(o.scheduled_end).getTime()>Date.now()+serverOffset))ownTimerModal(o.id);}});}el.textContent=[Math.floor(total/3600),Math.floor(total/60)%60,total%60].map(x=>String(x).padStart(2,'0')).join(':');});
  if($$('[data-available-at]').some(el=>new Date(el.dataset.availableAt).getTime()<=Date.now()+serverOffset)&&!busy&&!calendarDrag&&!$('#modal').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))render();
  $$('#modal [data-action=timer-planned]').forEach(button=>{const o=state.overtime.find(o=>o.id===button.dataset.id);if(o?.execution!=='SCHEDULED')return;const ready=o.status==='APPROVED'&&Date.parse(o.scheduled_start)<=Date.now()+serverOffset&&Date.parse(o.scheduled_end)>Date.now()+serverOffset&&!state.timers.some(t=>t.user_id===me().id);button.disabled=!ready;button.textContent=ready?'Iniciar Timer':'Timer';});
  $$('[data-action=group-timer-start]').forEach(button=>{const w=(state.group_activities||[]).find(w=>w.id===button.dataset.id);button.disabled=!w||w.status!=='APPROVED'||Date.parse(w.scheduled_start)>Date.now()+serverOffset||Date.parse(w.scheduled_end)<=Date.now()+serverOffset||state.timers.some(t=>t.user_id===me().id);button.classList.toggle('primary',!button.disabled);button.classList.toggle('secondary',button.disabled);const note=$('[data-group-availability="'+button.dataset.id+'"]');if(note&&w)note.textContent=w.status!=='APPROVED'?'La actividad requiere aprobación antes de iniciar.':Date.parse(w.scheduled_start)>Date.now()+serverOffset?'Timer disponible el '+fmtDate(w.scheduled_start)+' a las '+fmtTime(w.scheduled_start)+'.':Date.parse(w.scheduled_end)<=Date.now()+serverOffset?'La ventana autorizada terminó.':'Dentro del horario autorizado. Cada integrante inicia su propio Timer.';});
  const clock=$('[data-local-clock]');if(clock)clock.textContent=new Date(Date.now()+serverOffset).toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',timeZone:state.timezone});
}
function kpi(label,value,detail,symbol,accent='',target=''){
  const tag=target?'button':'article',attrs=target?`type="button" data-action="dashboard-drill" data-id="${target}"`:'';
  return `<${tag} class="kpi ${accent} ${target?'kpi-link':''}" ${attrs}><div><span>${label}</span><i>${icon(({'⌘':'organization','♧':'team','▦':'dashboard','◎':'profile','↗':'arrow','◷':'time','≡':'teamTime','●':'time'})[symbol]||'dashboard')}</i></div><strong>${value}</strong><small>${detail}${target?icon('arrow'):''}</small></${tag}>`;
}

function upcomingActivities(){
 const current=Date.now()+serverOffset,active=state.timers.some(t=>t.user_id===me().id);
 const records=state.overtime.filter(o=>o.user_id===me().id&&o.capture_type==='PLANNED'&&o.execution==='SCHEDULED'&&o.status!=='CANCELLED'&&Date.parse(o.scheduled_end)>current).sort((a,b)=>Date.parse(a.scheduled_start)-Date.parse(b.scheduled_start));
 const documents=state.overtime.filter(o=>o.user_id===me().id&&o.status==='DOCUMENTATION').length;
 const groupPlans=availableGroupActivities().filter(w=>Date.parse(w.scheduled_end)>current);
 return `<div class="upcoming-list">${groupPlans.slice(0,3).map(w=>{const ready=w.status==='APPROVED'&&Date.parse(w.scheduled_start)<=current&&!active;return `<article class="upcoming-activity"><div><span class="small-label">OT DEL GRUPO · ${range(w.scheduled_start,w.scheduled_end)}</span><h3>${esc(w.reference)}</h3>${badge(w.status)}</div><div class="upcoming-actions">${btn('Detalle','record-detail','group:'+w.id,'link')}${btn('▶ Mi Timer','group-timer-start',w.id,ready?'primary small':'secondary small',ready?'':'disabled')}</div></article>`;}).join('')}${records.slice(0,4).map(o=>{
 const before=Date.parse(o.scheduled_start)>current,ready=!before&&o.status==='APPROVED'&&!active;
 return `<article class="upcoming-activity"><div><span class="small-label">${range(o.scheduled_start,o.scheduled_end)}</span><h3>${esc(o.reference||'OT programada')}</h3>${badge(o.status)}<p ${before?`data-available-at="${esc(o.scheduled_start)}"`:''}>${before?'Timer disponible el '+fmtDate(o.scheduled_start)+' a las '+fmtTime(o.scheduled_start)+(o.status!=='APPROVED'?' · requiere aprobación.':'.'):active?'Detén tu Timer activo antes de iniciar otra OT.':o.status!=='APPROVED'?'Falta aprobación para iniciar el Timer.':'Dentro del horario autorizado.'}</p></div><div class="upcoming-actions">${btn('Detalle','record-detail','ot:'+o.id,'link')}${btn('▶ Iniciar Timer','timer-planned',o.id,ready?'primary small':'secondary small',ready?'':'disabled')}</div></article>`;
 }).join('')||(!groupPlans.length?'<p class="upcoming-empty">No tienes OT programadas próximas. Agrégalas desde tu calendario.</p>':'')}</div><div class="upcoming-footer"><button class="secondary small" data-action="open-calendar">Abrir calendario</button>${documents?`<button class="link" data-page="time">${documents} OT por documentar</button>`:''}</div>`;
}
function dashboard(){
  if(isAdmin())return adminDashboard();
  const ownTimers=state.timers.filter(t=>t.user_id===me().id),reviewer=isManager();
  return heading('TU OPERACIÓN AL DÍA',`Hola, ${esc(me().first)}.`,isTech()?'Tu OT, tus guardias y sus aprobaciones del mes.':'Un vistazo al tiempo y las prioridades de tu equipo.',monthControl())+
  (ownTimers.length?timerPanel(ownTimers):'')+
  `<section class="kpis">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real, sin duplicados','↗','',reviewer?'ot':'')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Con OT descontada','◷','',reviewer?'guard':'')}${kpi('Por revisar',reviewer?pendingCount():state.overtime.filter(o=>o.user_id===me().id&&o.status==='SUBMITTED').length,'Solicitudes pendientes','≡','',reviewer?'pending':'')}${kpi('Timers activos',isTech()?ownTimers.length:state.timers.length,'Actualización en tiempo real','●','accent',reviewer?'running':'')}</section>
  <section class="two-columns"><article class="panel"><div class="section-heading"><div><p class="eyebrow">ANALÍTICA MENSUAL</p><h2>${esc(monthLabel(month))}</h2></div><span class="pill">Horas aprobadas</span></div>${analyticsChart()}<div class="legend"><span><i class="dot ot"></i>Tiempo extra</span><span><i class="dot guard"></i>Guardia neta</span></div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">REQUIERE TU ATENCIÓN</p><h2>${isTech()?'Próximas actividades':'Solicitudes para revisar'}</h2></div></div>${isTech()?upcomingActivities():dashboardPriorities()}</article></section>
  ${state.timers.length&&!isTech()?`<article class="panel"><div class="section-heading"><div><p class="eyebrow">AHORA</p><h2>Tu equipo en tiempo real</h2></div><span class="live-label"><i></i>En vivo</span></div>${timerPanel(state.timers)}</article>`:''}`;
}
function dashboardPriorities(){
  const pending=[...state.overtime.map(o=>({...o,kind:'ot'})),...state.guards.map(g=>({...g,kind:'guard'}))].filter(r=>r.status==='SUBMITTED'&&r.execution!=='RUNNING'&&r.user_id!==me().id).sort((a,b)=>a.created_at.localeCompare(b.created_at));
  const extra=(state.extensions||[]).filter(e=>e.status==='SUBMITTED'&&e.requested_by!==me().id).length;
  const extensionAlert=extra?`<div class="extension-alert"><strong>${extra} extensiones por revisar</strong>${btn('Revisar extensiones','dashboard-drill','pending','secondary small')}</div>`:'';
  if(!pending.length)return extensionAlert||empty('Sin solicitudes por revisar','Las solicitudes de tu equipo aparecerán aquí cuando requieran una decisión.');
  return extensionAlert+`<div class="priority-list">${pending.slice(0,3).map(r=>`<article><span class="priority-icon">${icon(r.kind==='ot'?'time':'adp')}</span><div><strong>${esc(full(person(r.user_id)))}</strong><small>${r.kind==='ot'?esc(r.reference||'Tiempo extra'):esc(r.rule_snapshot.name)} · ${fmtDate(r.created_at)}</small></div>${btn('Revisar','record-detail',r.kind+':'+r.id,'link')}</article>`).join('')}</div>${pending.length>3?btn('Ver todas las solicitudes','dashboard-drill','pending','secondary small'):''}`;
}
function analyticsChart(){
  const byDay=new Map();ledger.rows.forEach(r=>{const day=Number(r.date.slice(-2));if(!byDay.has(day))byDay.set(day,{OT:0,GUARD:0});byDay.get(day)[r.kind]+=r.minutes/60;});
  if(!byDay.size)return empty('Sin horas aprobadas en este periodo','Aquí verás el tiempo real cuando sus registros estén aprobados.');
  const days=new Date(Number(month.slice(0,4)),Number(month.slice(5)),0).getDate();
  const max=Math.max(1,...[...byDay.values()].map(d=>d.OT+d.GUARD));
  // SVG keeps the visualization self-contained and avoids inline styles under CSP.
  let bars='';for(let d=1;d<=days;d++){const v=byDay.get(d)||{OT:0,GUARD:0},x=14+(d-1)*17,h1=v.OT/max*130,h2=v.GUARD/max*130;bars+=`<rect x="${x}" y="${150-h1}" width="10" height="${h1}" rx="2" fill="#2469cf"><title>${d}: ${v.OT.toFixed(2)} h OT</title></rect><rect x="${x}" y="${150-h1-h2}" width="10" height="${h2}" rx="2" fill="#28c7c5"><title>${d}: ${v.GUARD.toFixed(2)} h Guardia</title></rect>${d===1||d%5===0?`<text x="${x+5}" y="172" text-anchor="middle" fill="#536a85" font-size="10">${d}</text>`:''}`;}
  return `<div class="chart"><svg role="img" aria-label="Horas aprobadas por día, tiempo extra y Guardia neta" viewBox="0 0 545 185"><path d="M8 150H540" stroke="#e1e7e5"/>${bars}</svg></div>`;
}
function selectedAnalyticsMonths(){return [...new Set([month,...comparisonMonths])].sort();}
function appendAnalyticsQuery(q){
  if(filters.search)q.set('q',filters.search);if(filters.status)q.set('status',filters.status);if(filters.kind)q.set('record_type',filters.kind);
  q.set('months',selectedAnalyticsMonths().join(','));q.set('period',filters.period||'MONTH');
}
function analyticsExportLink(personal){
  const q=new URLSearchParams({month});if(!personal){if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);}appendAnalyticsQuery(q);
  return `<a class="secondary button" download href="${personal?'/api/my-analytics.xlsx?':'/api/analytics.xlsx?'}${esc(q.toString())}">${icon('download')} ${personal?'Exportar analítica':'Exportar resultados'}</a>`;
}
function resultMetrics(report,compact=false){
  const metrics=[['ALL','Total aprobado',report.summary.total_minutes],['OT','OT aprobada',report.summary.ot_minutes],...analyticsTypes.map(type=>[type,analyticsNames[type],report.summary[type]])];
  return `<section class="analytics-metrics ${compact?'result-metrics':''}">${metrics.map(([type,label,minutes])=>`<button type="button" class="analytics-metric metric-${type.toLowerCase()} ${compact?(filters.kind===type||type==='ALL'&&!filters.kind?'selected':''):(analyticsDetailType===type?'selected':'')}" data-action="analytics-records" data-id="${type}" aria-label="${esc(label)}: ${hours(minutes)} horas"><span>${label}</span><strong>${hours(minutes)} <small>h</small></strong>${compact?'':`<em>Ver detalle ${icon('arrow')}</em>`}</button>`).join('')}</section>`;
}
function analyticsPage(personal){return unifiedAnalyticsPage(personal);}
function unifiedAnalyticsPage(personal=false,recordsOnly=false){
  const report=analyticsReport,groups=state.groups.filter(g=>state.scope.includes(g.id)),people=state.people.filter(p=>p.role==='USER'&&(state.scope.includes(p.group_id)||p.is_lead&&p.manager_id===(isManager()?me().id:me().manager_id))&&(!filters.group||p.group_id===filters.group));
  const header=heading(recordsOnly?'BÚSQUEDA E HISTORIAL':'INTELIGENCIA OPERATIVA',recordsOnly?(personal?'Mis registros':'Consulta de registros'):(personal?'Mi analítica':'Analítica del equipo'),recordsOnly?'Busca CHG, INC y actividades. Consulta su detalle y trazabilidad.':'Explora tendencias, composición y distribución de tus horas aprobadas.',monthControl()+analyticsExportLink(personal));
  let controls=`<section class="panel analytics-filters unified-filters"><div class="analytics-tools"><form data-form="analytics-search"><label class="search">${icon('search')}<input id="analytics-search" name="search" type="search" maxlength="500" value="${esc(filters.search)}" placeholder="Buscar CHG / INC, nombre del Técnico, Employee ID o Grupo…" aria-label="Buscar en Consulta de registros" autocomplete="off"></label><button type="submit" class="secondary">Buscar</button></form>${btn('Comparar meses','analytics-months','','secondary')}</div><div class="analytics-filter-grid">${select('filter-period','Periodo',`<option value="MONTH" ${filters.period!=='ALL'?'selected':''}>Meses seleccionados</option><option value="ALL" ${filters.period==='ALL'?'selected':''}>Todo el historial</option>`)}${personal?'':select('filter-group','Grupo',options(groups,filters.group,g=>entityCode(g)+' · '+g.name,'Todos mis Grupos'))+select('filter-person','Técnico',options(people,filters.person,full,'Todos los Técnicos'))}${select('filter-status','Estado',`<option value="">Todos los estados</option>${['SUBMITTED','APPROVED','REJECTED','DOCUMENTATION','RUNNING','PAUSED','CANCELLED'].map(s=>`<option value="${s}" ${filters.status===s?'selected':''}>${statuses[s]}</option>`).join('')}`)}${select('filter-kind','Tipo',`<option value="">OT y Guardias</option><option value="OT" ${filters.kind==='OT'?'selected':''}>Toda la OT</option>${analyticsTypes.map(t=>`<option value="${t}" ${filters.kind===t?'selected':''}>${analyticsNames[t]}</option>`).join('')}`)}</div><div class="analytics-result-context"><span id="analytics-query-status" role="status">${filters.period==='ALL'?'Todo el historial':selectedAnalyticsMonths().map(monthLabel).join(' · ')}</span>${btn('Restablecer','analytics-reset','','link')}</div></section>`;
  if(!recordsOnly)controls=`<section class="panel analytics-filters visual-only-filters"><div class="analytics-filter-grid">${personal?'':select('filter-group','Grupo',options(groups,filters.group,g=>entityCode(g)+' · '+g.name,'Todos mis Grupos'))+select('filter-person','Técnico',options(people,filters.person,full,'Todos los Técnicos'))}${select('filter-kind','Tipo de horas',`<option value="">OT y Stand By</option><option value="OT" ${filters.kind==='OT'?'selected':''}>Toda la OT</option>${analyticsTypes.map(t=>`<option value="${t}" ${filters.kind===t?'selected':''}>${analyticsNames[t]}</option>`).join('')}`)}</div><div class="analytics-result-context"><span>${selectedAnalyticsMonths().map(monthLabel).join(' · ')} · Horas aprobadas</span><div>${btn('Elegir periodos','analytics-months','','secondary')}${btn('Consultar registros','open-records','','link')}${btn('Restablecer','analytics-reset','','link')}</div></div></section>`;
  const query=new URLSearchParams({month});if(!personal){if(filters.group)query.set('group_id',filters.group);if(filters.person)query.set('user_id',filters.person);}appendAnalyticsQuery(query);
  const requestKey=page+':'+query.toString();
  if(analyticsFailure?.key===requestKey)return header+controls+`<section class="panel">${empty('No se pudieron consultar los registros','Intenta buscar nuevamente. Si el problema continúa, revisa tu conexión.')}</section>`;
  if(!report||analyticsRequestKey!==requestKey)return header+controls+`<section class="panel">${empty('Consultando registros…')}</section>`;
  if(!recordsOnly)return header+controls+`<div class="analytics-dashboard">${!report.record_count?`<section class="panel analytics-empty" role="status">${empty('Sin registros para este alcance','Selecciona otro periodo, Grupo o Técnico. No se infiere actividad a partir de cero horas.')}</section>`:''}${analyticsDashboard(report,personal)}</div>`;
  if(!report.record_count){
    const employee=personal?me():person(filters.person),title=employee?`${full(employee)} no tiene registros con estos filtros`:'No hay registros con estos filtros';
    return header+controls+resultMetrics(report,true)+`<section class="panel analytics-empty" role="status">${empty(esc(title),`${filters.period==='ALL'?'Se consultó todo el historial.':'Periodo consultado: '+selectedAnalyticsMonths().map(monthLabel).join(' · ')+'.'} Prueba otro periodo o cambia los filtros de búsqueda.`)}${btn('Restablecer filtros','analytics-reset','','secondary')}</section>`;
  }
  const counts=report.record_counts,caption=`${report.record_count} registros · ${counts.APPROVED||0} aprobados · ${counts.SUBMITTED||0} pendientes · ${counts.REJECTED||0} rechazados`;
  return header+controls+resultMetrics(report,true)+`<section class="panel table-panel result-records" id="analytics-records"><div class="section-heading padded"><div><h2>Registros encontrados</h2><p class="muted">${caption}. Las horas suman sólo tiempo real aprobado.</p></div></div><div class="table-scroll"><table><thead><tr><th>Técnico / Grupo</th><th>Referencia / Actividad</th><th>Periodo</th><th>Estado</th><th>Consulta</th></tr></thead><tbody>${report.records.map(analyticsRecordRow).join('')}</tbody></table></div>${report.records.length?'':empty('Sin registros con esta búsqueda','Cambia el texto, los filtros o los meses seleccionados.')}</section>`;
}
function analyticsDashboard(report,personal){
 if(!personal)return managerCommandDashboard(report);
 return `<div class="analytics-context-strip"><span>${icon('info')} Sólo tus horas aprobadas · ${report.record_counts.SUBMITTED||0} solicitudes pendientes fuera del total</span><span>Zona ${esc(report.timezone)} · Corte ${fmtDate(report.as_of)}</span></div>${decisionVisualDeck(report)}${captureDisciplinePanel(report)}`;
}
function managerCommandDashboard(report){
 const latest=report.comparison.at(-1),previous=report.comparison.at(-2),s=latest?.minutes||report.summary,p=previous?.minutes;
 const rate=m=>m?.ot_minutes?m.PLANNED/m.ot_minutes*100:null;
 const difference=(now,before,unit='h')=>before===undefined||before===null?(previous?'Sin base previa para comparar':'Selecciona otro mes para comparar'):`Cambio: ${now-before>0?'+':''}${unit==='pp'?analyticsNumber(now-before):hours(now-before)} ${unit} frente a ${esc(previous.month)}`;
 const card=(label,value,unit,note,change,color)=>`<article class="bi-kpi"><span>${label}</span><strong>${value}<small>${unit}</small></strong><p>${note}</p><div>${change}</div></article>`;
 const programmed=rate(s),priorRate=rate(p),current=calendarDate(new Date(Date.now()+serverOffset)).slice(0,7);
 return `<div class="bi-report-context"><span><strong>Resumen del mes más reciente · ${esc(monthLabel(latest?.month||month))}</strong>${latest?.month===current?' · En curso: parcial':''}</span><span>${report.users.length} personas · ${report.groups.length} Grupos</span></div><div class="bi-kpis">${card('OT aprobada',hours(s.ot_minutes),'h','Programada + histórica + emergente',difference(s.ot_minutes,p?.ot_minutes),'#2876c8')}${card('Stand By neto',hours(s.GUARD),'h','Guardia menos OT coincidente',difference(s.GUARD,p?.GUARD),'#1ca798')}${card('OT programada',programmed===null?'—':Math.round(programmed),programmed===null?'':'%',`${hours(s.PLANNED)} h programadas del mes`,programmed===null?'Sin OT para calcular proporción':difference(programmed,priorRate,'pp'),'#269ebd')}${card('OT emergente',hours(s.EMERGENCY),'h',s.ot_minutes?(s.EMERGENCY/s.ot_minutes*100).toFixed(1)+'% de la OT del mes':'Sin base de OT',difference(s.EMERGENCY,p?.EMERGENCY),'#cf913b')}</div><p class="bi-scope-note">Las gráficas integran todos los meses seleccionados. Los indicadores comparan el último mes seleccionado con el anterior seleccionado, con los mismos filtros; pueden ser periodos parciales.</p>${decisionVisualDeck(report)}${captureDisciplinePanel(report)}<p class="analytics-context-strip">${icon('info')} Horas aprobadas · Zona ${esc(report.timezone)} · Corte ${fmtDate(report.as_of)} · Grupos actuales</p>`;
}

function managerTrendChart(items){
 if(items.length<2)return `<div class="command-comparison-empty">${icon('analytics')}<strong>Una comparación necesita al menos dos meses</strong><p>Agrega periodos para ver la evolución de OT y Stand By, sin mezclarlos en una sola barra.</p>${btn('Seleccionar meses','analytics-months','','secondary')}</div>`;
 const max=Math.max(1,...items.flatMap(i=>[i.minutes.ot_minutes,i.minutes.GUARD]));
 return `<div class="command-trend" role="list" aria-label="Comparación de OT y Stand By">${items.map(i=>`<article role="listitem"><strong>${esc(monthLabel(i.month))}</strong><div><span>OT</span><meter min="0" max="${max}" value="${i.minutes.ot_minutes}" aria-label="OT ${esc(i.month)}"></meter><b>${hours(i.minutes.ot_minutes)} h</b></div><div class="standby"><span>SB</span><meter min="0" max="${max}" value="${i.minutes.GUARD}" aria-label="Stand By ${esc(i.month)}"></meter><b>${hours(i.minutes.GUARD)} h</b></div></article>`).join('')}</div>`;
}
function expandAnalyticsChart(kind){
 const report=analyticsReport;if(!report?.record_count)return;
 const personal=page==='myAnalytics';let title,body;
 if(kind==='distribution'){title=personal?'Horas por tipo':'Horas aprobadas por Grupo';body=(personal?analyticsComposition(report.summary):analyticsGroupChart(report.groups))+analyticsLegend()+(personal?'':analyticsGroupTable(report.groups));}
 else if(kind==='comparison'){title='Comparación mensual';body=comparisonChart(report.comparison)+analyticsLegend()+comparisonTable(report.comparison);}
 else if(kind==='hourly'){title='Horas por franja horaria';body=`<p class="muted">Cada franja corresponde a una hora del día. Se acumula el tiempo real aprobado de las fechas y personas filtradas.</p>${hourlyChart(report.hourly)}${analyticsLegend()}<div class="table-scroll"><table><thead><tr><th>Franja</th><th>OT h</th><th>Guardia neta h</th><th>Total h</th></tr></thead><tbody>${report.hourly.map(x=>`<tr><td>${String(x.hour).padStart(2,'0')}:00 — ${String(x.hour+1).padStart(2,'0')}:00</td><td>${hours(x.minutes.ot_minutes)}</td><td>${hours(x.minutes.GUARD)}</td><td>${hours(x.minutes.total_minutes)}</td></tr>`).join('')}</tbody></table></div>`;}
 else if(kind==='daily'){title='Horas por fecha';body=analyticsDailyChart(report.days);}else return;
 showModal(title,`<div class="form-body expanded-chart-body"><p class="callout">${esc(report.months.map(monthLabel).join(' · '))} · ${personal?'Sólo tus horas':'Alcance del equipo autorizado'}. Se conservan los filtros actuales y sólo suman horas aprobadas.</p>${body}</div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}</footer>`,true);
 $('#modal').classList.add('expanded-chart-dialog');
}
function hourlyChart(items){
 const max=Math.max(60,...items.map(x=>x.minutes.total_minutes));
 return `<div class="hourly-grid" role="list" aria-label="Horas aprobadas por franja">${items.map(x=>{let y=145;return `<div class="hourly-slot" role="listitem"><strong>${hours(x.minutes.total_minutes)} h</strong><svg class="hourly-bar" viewBox="0 0 40 145" preserveAspectRatio="none" role="img" aria-label="${x.hour}:00: ${hours(x.minutes.total_minutes)} horas"><rect width="40" height="145" fill="#edf3fa"/>${analyticsTypes.map(type=>{const height=x.minutes[type]/max*145;y-=height;return `<rect x="0" y="${y}" width="40" height="${height}" fill="${analyticsColors[type]}"><title>${analyticsNames[type]}: ${hours(x.minutes[type])} h</title></rect>`;}).join('')}</svg><span>${String(x.hour).padStart(2,'0')}:00</span></div>`;}).join('')}</div>`;
}
function analyticsRecordRow(r){
  const t=state.timers.find(t=>t.overtime_id===r.id),raw=state.overtime.find(o=>o.id===r.id);
  return `<tr><td><strong>${esc(r.name)}</strong><small>${esc(r.employee_id)} · ${esc(r.group_name)}</small></td><td><span class="small-label">${esc(analyticsNames[r.capture_type])}</span><strong>${esc(r.reference||'Por documentar')}</strong><small>${esc((r.description||'').slice(0,120))}</small>${r.capture_type==='HISTORICAL'?`<small class="capture-origin">${r.recovered?'Recuperado desde respaldo · no se considera backlog':`Captura posterior · ${analyticsNumber(r.capture_delay_hours)} h después del fin`}</small>`:''}</td><td>${fmtDate(r.from_at)} · ${fmtTime(r.from_at)}<small>${fmtDate(r.to_at)} · ${fmtTime(r.to_at)}</small></td><td>${badge(r.display_status)}${t?`<small class="record-live-clock" data-elapsed="${esc(t.start_at)}" data-base="${raw?.worked_seconds||0}" ${r.capture_type==='PLANNED'?`data-until="${esc(r.to_at)}"`:''}>00:00:00</small>`:''}</td><td>${btn('Detalle','record-detail',r.kind+':'+r.id,'link')}${r.status==='SUBMITTED'&&r.execution!=='RUNNING'&&r.user_id!==me().id?btn('Revisar','review-record',r.kind+':'+r.id,'link'):''}</td></tr>`;
}
async function runAnalyticsSearch(){
  clearTimeout(analyticsSearchTimer);if(!['analytics','myAnalytics','records','myRecords'].includes(page))return;
  const query=filters.search,active=document.activeElement?.id==='analytics-search',field=$('#analytics-search'),caret=field?.selectionStart;
  const status=$('#analytics-query-status');if(status)status.textContent='Buscando…';
  try{await loadLedger();if(!['analytics','myAnalytics','records','myRecords'].includes(page)||query!==filters.search)return;render();if(active){const input=$('#analytics-search');input?.focus({preventScroll:true});if(caret!=null)input?.setSelectionRange(caret,caret);}}catch(error){toast(error.message,true);}
}
function comparisonModal(){visualComparisonModal();}
function paintComparisonDraft(){const root=$('#comparison-draft');if(root)root.innerHTML=comparisonDraft.map(key=>`<span>${esc(monthLabel(key))}${key===month?'<small>Principal</small>':btn('×','comparison-remove',key,'icon-btn')}</span>`).join('');PulseLayout.dialog();}
function comparisonChart(items){
  const max=Math.max(60,...items.map(i=>i.minutes.total_minutes)),step=520/items.length;
  return `<svg class="analytics-daily" viewBox="0 0 600 220" role="img" aria-label="Comparación mensual de horas aprobadas"><path d="M25 180H575" stroke="#dbe5f1"/>${items.map((item,i)=>{let y=180;return analyticsTypes.map(type=>{const height=item.minutes[type]/max*145;y-=height;return `<rect x="${35+i*step}" y="${y}" width="${Math.max(4,step-15)}" height="${height}" fill="${analyticsColors[type]}"><title>${item.month}: ${analyticsNames[type]} ${hours(item.minutes[type])} h</title></rect>`;}).join('')+(i%Math.ceil(items.length/8)===0?`<text x="${35+i*step}" y="${Math.max(17,y-8)}" font-size="12" fill="#254563">${hours(item.minutes.total_minutes)} h</text><text x="${35+i*step}" y="202" font-size="11" fill="#526c8a">${item.month}</text>`:'');}).join('')}</svg>`;
}
function comparisonTable(items){
 const current=calendarDate(new Date(Date.now()+serverOffset)).slice(0,7);
 return `<section class="panel table-panel"><div class="section-heading padded"><h2>Comparativa por mes</h2></div><div class="table-scroll"><table class="monthly-summary"><thead><tr><th>Mes</th><th>OT programada h</th><th>OT histórica h</th><th>OT emergente h</th><th>OT total h</th><th>SB neto h</th><th>Total h</th><th>Variación</th></tr></thead><tbody>${items.map((item,i)=>{const previous=items[i-1]?.minutes.total_minutes,difference=i?item.minutes.total_minutes-previous:0;return `<tr><td>${esc(item.month)}${item.month>=current?`<small>${item.month===current?'En curso · parcial':'Periodo futuro'}</small>`:''}</td><td>${hours(item.minutes.PLANNED)}</td><td>${hours(item.minutes.HISTORICAL)}</td><td>${hours(item.minutes.EMERGENCY)}</td><td>${hours(item.minutes.ot_minutes)}</td><td>${hours(item.minutes.GUARD)}</td><td><strong>${hours(item.minutes.total_minutes)}</strong></td><td>${i?`${difference>0?'+':''}${hours(difference)} h<small>${previous?`${(difference/previous*100).toFixed(1)}%`:'Sin base previa'}</small>`:'Base'}</td></tr>`;}).join('')}</tbody></table></div><p class="muted monthly-comparison-note">Variación frente al mes anterior seleccionado. Los meses en curso son parciales.</p></section>`;
}
function analyticsVisuals(){
  const report=analyticsReport;if(!report||report.mode!=='TEAM')return;
  showModal('Análisis de resultados',`<div class="form-body"><p class="callout">${report.record_count} registros encontrados. Búsqueda: ${esc(filters.search||'Todos')}. Los pendientes y rechazados no suman horas.</p><section><h2>${report.comparison.length>1?'Comparación entre meses':'Horas por día'}</h2>${report.comparison.length>1?comparisonChart(report.comparison):analyticsDailyChart(report.days)}${report.comparison.length>1?analyticsLegend():''}</section>${report.comparison.length>1?comparisonTable(report.comparison):''}${analyticsGroupTable(report.groups)}${analyticsUserTable(report.users)}<p class="muted">Guardia neta descuenta toda la OT aprobada que se traslapa, aunque una búsqueda filtre esa OT fuera de la lista.</p></div><footer class="dialog-footer">${btn('Cerrar','close','','primary')}</footer>`,true);
  $('#modal').classList.add('analysis-dialog');$$('table',$('#modal')).forEach(table=>{const headers=$$('thead th',table).map(th=>th.textContent.trim());$$('tbody tr',table).forEach(row=>$$('td',row).forEach((td,i)=>td.dataset.label=headers[i]||''));});
}
function analyticsLegend(){return `<div class="analytics-legend">${analyticsTypes.map(type=>`<span><i class="analytics-dot type-${type.toLowerCase()}"></i>${analyticsNames[type]}</span>`).join('')}</div>`;}
function analyticsComposition(summary){
  const total=summary.total_minutes;if(!total)return empty('Aún no hay horas aprobadas','Aquí aparecerá el desglose cuando se apruebe tu tiempo real.');
  let x=0;const bars=analyticsTypes.map(type=>{const width=summary[type]/total*500;const rect=`<rect x="${x}" y="0" width="${width}" height="20" fill="${analyticsColors[type]}"><title>${analyticsNames[type]}: ${hours(summary[type])} h</title></rect>`;x+=width;return rect;}).join('');
  return `<div class="composition-total"><strong>${hours(total)} <small>horas</small></strong><span>Tiempo aprobado del periodo seleccionado</span></div><svg class="analytics-composition" viewBox="0 0 500 20" role="img" aria-label="Composición de tus horas aprobadas">${bars}</svg><div class="composition-values">${analyticsTypes.map(type=>`<div><span>${analyticsNames[type]}</span><strong>${hours(summary[type])} h</strong></div>`).join('')}</div>`;
}

let analyticsRankMetric='total_minutes';
function analyticsTechnicianRanking(users){
 const labels={total_minutes:'Total aprobado',ot_minutes:'OT aprobada',GUARD:'Stand By neto'};
 const metric=analyticsRankMetric,compare=(a,b)=>(b.minutes[metric]-a.minutes[metric])||a.name.localeCompare(b.name,'es');
 const sorted=[...users].sort(compare),low=[...users].sort((a,b)=>(a.minutes[metric]-b.minutes[metric])||a.name.localeCompare(b.name,'es'));
 const list=(items,emptyText)=>items.length?`<ol class="technician-ranking">${items.slice(0,5).map((u,i)=>`<li><button type="button" data-action="analytics-user" data-id="${esc(u.id)}"><span class="ranking-place">${i+1}</span><span><strong>${esc(u.name)}</strong><small>${esc(u.employee_id)} · ${esc(u.group_name)}</small></span><b>${hours(u.minutes[metric])} <small>h</small></b>${icon('forward')}</button></li>`).join('')}</ol>`:empty(emptyText);
 return `<section class="panel technician-rankings" id="analytics-rankings"><header class="section-heading"><div><p class="eyebrow">DISTRIBUCIÓN DE HORAS POR PERSONA</p><h2>Técnicos con más y menos horas</h2><p class="muted">Mismo periodo, búsqueda y filtros del tablero. Incluye cero horas aprobadas dentro del alcance; no es una evaluación de desempeño.</p></div><label class="field"><span>Comparar por</span><select id="analytics-rank-metric">${Object.entries(labels).map(([k,v])=>`<option value="${k}" ${metric===k?'selected':''}>${v}</option>`).join('')}</select></label></header><div class="two-columns"><section><h3>Más horas · ${labels[metric]}</h3>${list(sorted,'Sin Técnicos en este alcance')}</section><section><h3>Menos horas · ${labels[metric]}</h3>${list(low,'Sin Técnicos en este alcance')}</section></div></section>`;
}
async function analyticsParticipantsModal(id){
 const report=await api('/api/analytics/overtime/'+encodeURIComponent(id)+'/participants');
 showModal('Participación del Grupo',`<div class="form-body"><p class="callout">${esc(report.scope_note)}</p><div class="activity-participant-summary"><div><span>Actividad</span><strong>${esc(report.reference||'Sin referencia')}</strong><small>${range(report.scheduled_start,report.scheduled_end)}</small></div><div><span>Inscritos visibles</span><strong>${report.participant_count}</strong></div><div><span>Ejecutaron Timer</span><strong>${report.executed_count}</strong></div></div>${report.shared_activity?'':'<p class="muted">No hay una actividad compartida vinculada. Se muestra únicamente este registro; una referencia igual no vincula otras OT.</p>'}<div class="table-scroll"><table class="activity-participants"><thead><tr><th>Técnico / Grupo actual</th><th>Participación</th><th>Timer</th><th>Registro</th><th>Tiempo cerrado h</th><th>Aprobado h</th><th>Consulta</th></tr></thead><tbody>${report.participants.map(p=>`<tr><td><strong>${esc(p.name)}</strong><small>${esc(p.employee_id)} · ${esc(p.group_name)}</small></td><td>${p.is_source?'Autor de la programación':'Participante'}</td><td>${p.executed_timer?`${p.timer_count} ${p.timer_count===1?'tramo iniciado':'tramos iniciados'}`:'Sin iniciar'}${p.active_start?'<small>Timer en curso; el tiempo abierto aún no está aprobado.</small>':''}</td><td>${badge(p.execution==='RUNNING'?'RUNNING':p.execution==='PAUSED'?'PAUSED':p.status)}</td><td class="numeric">${hours(p.closed_seconds/60)}</td><td class="numeric">${hours(p.approved_minutes)}</td><td>${btn('Detalle','record-detail','ot:'+p.record_id,'link')}</td></tr>`).join('')}</tbody></table></div><p class="muted">Cada persona conserva su registro, documentación, Timer y aprobación. El tiempo abierto o pendiente no suma horas aprobadas.</p></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}</footer>`,true);$('#modal').classList.add('analytics-participants-dialog');
}

function analyticsGroupChart(groups){
  const active=groups.filter(g=>g.minutes.total_minutes>0),max=Math.max(1,...active.map(g=>g.minutes.total_minutes));
  if(!active.length)return empty('Sin horas aprobadas en este mes','Las horas aparecerán cuando el equipo finalice y apruebe sus registros.');
  return `<div class="analytics-ranking">${active.map(g=>{let x=0;const bars=analyticsTypes.map(type=>{const width=g.minutes[type]/max*500;const rect=`<rect x="${x}" y="0" width="${width}" height="10" fill="${analyticsColors[type]}"></rect>`;x+=width;return rect;}).join('');return `<button type="button" data-action="analytics-group" data-id="${esc(g.id)}"><span><strong>${esc(entityCode(g))} · ${esc(g.name)}</strong><small>${hours(g.minutes.total_minutes)} h ${icon('arrow')}</small></span><svg viewBox="0 0 500 10" role="img" aria-label="${esc(g.name)}: ${hours(g.minutes.total_minutes)} horas"><rect width="500" height="10" fill="#eef4fb"/>${bars}</svg><small>OT ${hours(g.minutes.ot_minutes)} h · Guardia ${hours(g.minutes.GUARD)} h</small></button>`;}).join('')}</div>`;
}
function analyticsDailyChart(days){
 const active=days.filter(day=>day.minutes.total_minutes>0).sort((a,b)=>a.date.localeCompare(b.date)),maximum=Math.max(60,...active.map(day=>day.minutes.total_minutes));
 if(!active.length)return empty('Sin horas aprobadas','Los pendientes y rechazados no suman. Revisa otro periodo o tus filtros.');
 return `<div class="daily-hours"><p class="daily-hours-help">Horas aprobadas por fecha de actividad · sólo se muestran días con horas. La barra indica el total; debajo está el desglose.</p><div class="daily-hours-list">${active.map(day=>`<article class="daily-hours-row"><header><time datetime="${esc(day.date)}">${fmtDate(day.date)}</time><strong>${hours(day.minutes.total_minutes)} <span>h</span></strong></header><meter min="0" max="${maximum}" value="${day.minutes.total_minutes}" aria-label="${esc(fmtDate(day.date))}: ${hours(day.minutes.total_minutes)} horas aprobadas"></meter><div class="daily-hours-breakdown">${analyticsTypes.filter(type=>day.minutes[type]>0).map(type=>`<span><i class="analytics-dot type-${type.toLowerCase()}"></i>${analyticsNames[type]} <b>${hours(day.minutes[type])} h</b></span>`).join('')}</div></article>`).join('')}</div></div>`;
}
function analyticsAmountCells(totals,counts){return [...analyticsTypes,'ot_minutes','total_minutes'].map(key=>`<td class="numeric ${key==='total_minutes'?'analytics-total':''}">${hours(totals[key])}${counts&&analyticsTypes.includes(key)?`<small>${counts[key]||0} ${key==='GUARD'?'solicitudes':'registros'}</small>`:''}</td>`).join('');}
function analyticsColumnHeaders(){return analyticsTypes.map(type=>`<th class="numeric"><span class="analytics-dot type-${type.toLowerCase()}"></span>${type==='GUARD'?'SB · Guardia neta':analyticsNames[type]} <small>h</small></th>`).join('')+'<th class="numeric">OT total <small>h</small></th><th class="numeric">Total <small>h</small></th>';}
function analyticsGroupTable(groups){
  return `<section class="panel table-panel"><div class="section-heading padded"><div><p class="eyebrow">POR GRUPO</p><h2>OT y Stand By por Grupo</h2><p class="muted">Horas aprobadas del periodo. El detalle distingue programadas, históricas y emergentes; los conteos son registros aprobados finalizados.</p></div><span class="pill">${groups.length} Grupos</span></div><div class="table-scroll"><table class="analytics-table"><thead><tr><th>Grupo</th><th class="numeric">Técnicos</th>${analyticsColumnHeaders()}<th></th></tr></thead><tbody>${groups.map(g=>`<tr><td><strong>${esc(g.name)}</strong><small>${esc(entityCode(g))}</small></td><td class="numeric">${g.user_count}</td>${analyticsAmountCells(g.minutes,g.approved_counts)}<td>${btn('Ver Técnicos','analytics-group',g.id,'link')}</td></tr>`).join('')}</tbody></table></div>${groups.length?'':empty('No hay Grupos en este alcance')}</section>`;
}
function analyticsUserTable(users){
  return `<section class="panel table-panel" id="analytics-users"><div class="section-heading padded"><div><p class="eyebrow">POR TÉCNICO</p><h2>Las horas de cada persona</h2></div><span class="pill">${users.length} Técnicos</span></div><div class="table-scroll"><table class="analytics-table"><thead><tr><th>Técnico / Grupo</th>${analyticsColumnHeaders()}<th></th></tr></thead><tbody>${users.map(u=>`<tr><td><strong>${esc(u.name)}</strong><small>${esc(u.employee_id)} · ${esc(u.group_name)}</small></td>${analyticsAmountCells(u.minutes,u.approved_counts)}<td>${btn('Ver horas','analytics-user',u.id,'link')}</td></tr>`).join('')}</tbody></table></div>${users.length?'':empty('No hay Técnicos en este alcance')}</section>`;
}
function analyticsDetailTable(rows){
  const selected=rows.filter(row=>analyticsDetailType==='ALL'||row.capture_type===analyticsDetailType);
  return `<section class="panel table-panel" id="analytics-records"><div class="section-heading padded"><div><p class="eyebrow">DETALLE DE HORAS · ${esc(monthLabel(month))}</p><h2>${analyticsNames[analyticsDetailType]||'Todas las horas'}</h2><p class="muted">Los registros que cruzan medianoche se muestran en tramos por día.</p></div>${btn('Cerrar detalle','analytics-detail-close','','link')}</div><div class="table-scroll"><table><thead><tr><th>Fecha</th><th>Técnico / Grupo</th><th>Tipo</th><th>Horario</th><th>Referencia</th><th class="numeric">Horas</th></tr></thead><tbody>${selected.map(row=>`<tr><td>${fmtDate(row.date)}</td><td><strong>${esc(row.name)}</strong><small>${esc(row.employee_id)} · ${esc(row.group_name)}</small></td><td><span class="analytics-type-label type-${row.capture_type.toLowerCase()}">${analyticsNames[row.capture_type]}</span></td><td>${row.start} — ${row.end}</td><td>${esc(row.reference||'—')}</td><td class="numeric analytics-total">${hours(row.minutes)}</td></tr>`).join('')}</tbody></table></div>${selected.length?'':empty('Sin horas aprobadas de este tipo','Prueba otro mes, Grupo o tipo de registro.')}</section>`;
}

let groupSearchPopup=null;
let groupSearchIndex=-1;
function organizationFinder(){return `<div class="organization-finder"><label for="organization-search">${icon('search')}<span class="sr-only">Buscar Grupo por nombre, código o Manager</span><input id="organization-search" type="search" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="group-search-results" aria-autocomplete="list" placeholder="Buscar Grupo por nombre, código o Manager…"></label><span>Encuentra un Grupo y ábrelo directamente</span></div>`;}
function closeGroupSearch(){groupSearchPopup?.remove();groupSearchPopup=null;groupSearchIndex=-1;const input=$('#organization-search');input?.setAttribute('aria-expanded','false');input?.removeAttribute('aria-activedescendant');}
function searchGroups(value){
  closeGroupSearch();const input=$('#organization-search');if(!input||!value.trim()||!isAdmin()||page!=='organization')return;
  const normalize=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
  const terms=normalize(value).trim().split(/\s+/),matches=state.groups.filter(g=>{const a=state.accounts.find(a=>a.id===g.account_id),m=person(g.manager_id),haystack=normalize(`${entityCode(g)} ${g.code} ${g.name} ${countryLabel(a?.country_code)} ${a?.code||''} ${a?.name||''} ${full(m)} ${m?.employee_id||''}`);return terms.every(term=>haystack.includes(term));});
  const anchor=input.closest('label').getBoundingClientRect(),limit=Math.max(1,Math.min(5,Math.floor((innerHeight-anchor.bottom-65)/61))),shown=matches.slice(0,limit);
  groupSearchPopup=document.createElement('div');groupSearchPopup.className='group-search-popup';groupSearchPopup.id='group-search-results';groupSearchPopup.setAttribute('role','listbox');groupSearchPopup.setAttribute('aria-label','Grupos encontrados');
  groupSearchPopup.innerHTML=`<p role="status">${matches.length?`${matches.length} ${matches.length===1?'Grupo encontrado':'Grupos encontrados'}${matches.length>limit?' · Precisa la búsqueda para ver otros':''}`:'No hay Grupos con esa búsqueda'}</p>`+shown.map((g,i)=>{const a=state.accounts.find(a=>a.id===g.account_id);return `<button type="button" role="option" aria-selected="false" id="group-result-${i}" data-action="group-search-open" data-id="${esc(g.id)}"><span class="group-result-icon">${icon('organization')}</span><span><strong>${esc(g.name)}</strong><small>${esc(entityCode(g))} · ${esc(a?.name||'')} · ${esc(g.manager_id?full(person(g.manager_id)):'Sin Manager')}</small></span>${icon('arrow')}</button>`;}).join('');
  document.body.append(groupSearchPopup);input.setAttribute('aria-expanded','true');
  const width=Math.min(Math.max(anchor.width,320),innerWidth-24);groupSearchPopup.style.width=width+'px';const rect=groupSearchPopup.getBoundingClientRect();groupSearchPopup.style.left=Math.max(12,Math.min(anchor.left,innerWidth-width-12))+'px';groupSearchPopup.style.top=Math.max(12,Math.min(anchor.bottom+6,innerHeight-rect.height-12))+'px';
}
function openSearchedGroup(id){
  closeGroupSearch();const card=$(`[data-group="${id}"]`);if(!card)return;
  PulseLayout.reveal(card);const input=$('#organization-search');if(input)input.value='';
  card.classList.add('group-located');setTimeout(()=>card.classList.remove('group-located'),2500);
  $('header .entity-title',card)?.focus({preventScroll:true});
}
let adminAccountId='',adminQuery='',adminCountry='',adminAttention='';
const adminLive=p=>p.status!=='DISABLED';
function adminManagers(a){return state.people.filter(p=>p.role==='MANAGER'&&p.account_id===a.id);}
function adminLead(m){return state.people.find(p=>p.is_lead&&adminLive(p)&&p.manager_id===m.id);}
function adminRecoveryPending(r){return r.status==='PENDING'||r.status==='ISSUED'&&new Date(r.expires_at).getTime()<=Date.now()+serverOffset;}
function adminFilteredAccounts(){const q=adminQuery.trim().toLocaleLowerCase('es-MX');return state.accounts.filter(a=>(!adminCountry||a.country_code===adminCountry)&&(!q||[entityCode(a),a.name,countryLabel(a.country_code),...adminManagers(a).flatMap(m=>[full(m),m.employee_id,adminLead(m)?full(adminLead(m)):'',adminLead(m)?.employee_id||''])].join(' ').toLocaleLowerCase('es-MX').includes(q)));}
function adminSearch(){return `<div class="admin-searchbar"><label>${icon('search')}<span class="sr-only">Buscar Cuenta o Manager</span><input type="search" id="admin-search" value="${esc(adminQuery)}" placeholder="Buscar Cuenta, Manager o Lead…" autocomplete="off"></label><label><span class="sr-only">País</span><select id="admin-country"><option value="">Todos los países</option>${[...new Set(state.accounts.map(a=>a.country_code))].sort().map(c=>`<option value="${esc(c)}" ${c===adminCountry?'selected':''}>${esc(countryLabel(c))}</option>`).join('')}</select></label></div>`;}
function adminMetric(label,value,copy,target,symbol){return `<button type="button" class="kpi kpi-link" data-action="admin-drill" data-id="${target}"><div><span>${label}</span><i>${icon(symbol)}</i></div><strong>${value}</strong><small>${copy}${icon('forward')}</small></button>`;}
function adminDistribution(){
 const accounts=adminFilteredAccounts(),max=Math.max(1,...accounts.map(a=>adminManagers(a).filter(m=>m.status==='ACTIVE').length));
 return `<div class="admin-distribution"><article class="panel"><div class="section-heading"><div><p class="eyebrow">DISTRIBUCIÓN</p><h2>Managers por Cuenta</h2></div><span class="pill">Activos</span></div><div class="admin-bars">${accounts.map(a=>{const n=adminManagers(a).filter(m=>m.status==='ACTIVE').length;return `<button class="admin-bar-row" data-action="organization-open" data-id="${esc(a.id)}"><span>${esc(a.name)}<small>${esc(entityCode(a))}</small></span><meter class="admin-bar-track" min="0" max="${max}" value="${n}" aria-label="${esc(a.name)}: ${n} Managers activos"></meter><b>${n}</b></button>`;}).join('')||empty('Sin resultados','Ajusta la búsqueda o el país.')}</div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">ESTRUCTURA</p><h2>Detalle por Cuenta</h2></div><span class="pill">${accounts.length} Cuentas</span></div><div class="table-scroll"><table><thead><tr><th>Cuenta</th><th>Managers activos</th><th>Leads activos</th><th>Sin Lead</th></tr></thead><tbody>${accounts.map(a=>{const ms=adminManagers(a).filter(m=>m.status==='ACTIVE');return `<tr><td><button class="admin-table-account" data-action="organization-open" data-id="${esc(a.id)}">${esc(a.name)}</button><small>${esc(entityCode(a))}</small></td><td>${ms.length}</td><td>${ms.filter(m=>adminLead(m)?.status==='ACTIVE').length}</td><td>${ms.filter(m=>!adminLead(m)).length}</td></tr>`;}).join('')}</tbody></table>${!accounts.length?empty('Sin Cuentas para mostrar','Cambia los filtros o crea una Cuenta.'):''}</div></article></div>`;
}
function paintAdminResults(){const distribution=$('#admin-distribution'),accounts=$('#admin-account-results');if(distribution)distribution.innerHTML=adminDistribution();if(accounts)accounts.innerHTML=adminAccountResults();}
function adminDashboard(){
 const managers=state.people.filter(p=>p.role==='MANAGER'&&p.status==='ACTIVE'),leads=state.people.filter(p=>p.is_lead&&p.status==='ACTIVE'),pending=state.recoveries.filter(adminRecoveryPending),missing=state.people.filter(p=>p.role==='MANAGER'&&adminLive(p)&&!adminLead(p)),vacant=state.accounts.filter(a=>!adminManagers(a).some(adminLive)),activation=state.people.filter(p=>(p.role!=='USER'||p.is_lead)&&p.status==='PENDING_ACTIVATION');
 return heading('ADMINISTRACIÓN','Tu organización, de un vistazo','Distribución de Cuentas, responsables y accesos que requieren atención.',btn('＋ Nueva Cuenta','account-new','','primary'))+`<section class="admin-dashboard"><div class="kpis">${adminMetric('Cuentas',state.accounts.length,'Cuentas operativas registradas','accounts','organization')}${adminMetric('Managers activos',managers.length,'Responsables con acceso activo','managers','team')}${adminMetric('Leads activos',leads.length,'Backups con acceso activo','leads','profile')}${adminMetric('Recuperaciones pendientes',pending.length,'Incluye códigos vencidos','recoveries','recoveries')}</div><div class="admin-dashboard-body"><section class="admin-structure">${adminSearch()}<div id="admin-distribution">${adminDistribution()}</div></section><aside class="panel admin-attention"><p class="eyebrow">SIGUIENTE PASO</p><h2>Requiere atención</h2>${[['missing',missing.length,'Managers sin Lead','Asigna un backup para completar el equipo.'],['vacant',vacant.length,'Cuentas sin Manager','Agrega su primer responsable.'],['activation',activation.length,'Accesos por activar','Consulta o regenera el código de activación.'],['recoveries',pending.length,'Recuperaciones pendientes','Valida la identidad antes de emitir un código.']].map(([id,n,title,copy])=>`<button class="admin-attention-item" data-action="admin-drill" data-id="${id}"><span><strong>${title}</strong><small>${copy}</small></span><b>${n}</b>${icon('forward')}</button>`).join('')}</aside></div></section>`;
}
function adminAccountResults(){
 let accounts=adminFilteredAccounts();if(adminAttention==='vacant')accounts=accounts.filter(a=>!adminManagers(a).some(adminLive));
 if(['missing','activation','leads'].includes(adminAttention))accounts=accounts.filter(a=>adminManagers(a).some(m=>adminAttention==='missing'?adminLive(m)&&!adminLead(m):adminAttention==='activation'?m.status==='PENDING_ACTIVATION'||adminLead(m)?.status==='PENDING_ACTIVATION':!!adminLead(m)));
 return `<div class="admin-account-grid">${accounts.map(a=>{const ms=adminManagers(a).filter(adminLive),ls=ms.filter(m=>adminLead(m));return `<article class="admin-account-tile"><div class="admin-tile-top"><span class="account-chip">${esc(entityCode(a))}</span>${moreActions('account',a.id,'Cuenta '+a.name)}</div><p class="eyebrow">${esc(countryLabel(a.country_code))}</p><h2>${esc(a.name)}</h2><p class="muted">${ms.length} Managers vigentes · ${ls.length} Leads asignados</p><footer>${btn('Abrir Cuenta','organization-open',a.id,'primary')}${btn('Agregar Manager','manager-new',a.id,'secondary')}</footer></article>`;}).join('')||empty('Sin Cuentas para mostrar','Ajusta los filtros o crea una Cuenta.')}</div>`;
}
function organizationPage(){
 const a=state.accounts.find(a=>a.id===adminAccountId);
 if(!a)return heading('ESTRUCTURA ORGANIZATIVA','Cuentas','Administra Cuentas, Managers y Leads desde un solo espacio.',btn('＋ Nueva Cuenta','account-new','','primary'))+`<section class="admin-accounts">${adminSearch()}${adminAttention?`<div class="admin-filter-note">Vista: ${esc(({missing:'Managers sin Lead',vacant:'Cuentas sin Manager',activation:'Accesos por activar',leads:'Leads asignados',managers:'Managers'})[adminAttention]||'Cuentas')} ${btn('Mostrar todo','admin-clear','','link')}</div>`:''}<div id="admin-account-results">${adminAccountResults()}</div></section>`;
 let managers=adminManagers(a);if(adminAttention==='missing')managers=managers.filter(m=>adminLive(m)&&!adminLead(m));if(adminAttention==='activation')managers=managers.filter(m=>m.status==='PENDING_ACTIVATION'||adminLead(m)?.status==='PENDING_ACTIVATION');
 return heading('CUENTA · '+entityCode(a),a.name,countryLabel(a.country_code)+' · Managers y Leads de esta Cuenta.',btn('← Cuentas','admin-back','','secondary')+btn('Editar Cuenta','account-edit',a.id,'secondary')+btn('＋ Agregar Manager','manager-new',a.id,'primary'))+`<section class="admin-account-detail" data-account="${esc(a.id)}"><div class="admin-detail-summary"><span><b>${adminManagers(a).filter(adminLive).length}</b> Managers vigentes</span><span><b>${adminManagers(a).filter(m=>adminLead(m)).length}</b> Leads asignados</span><span>${state.groups.filter(g=>g.account_id===a.id).length} Grupos · consulta de estructura</span>${moreActions('account',a.id,a.name)}</div><div class="admin-manager-grid">${managers.map(m=>managerBlock(m,state.groups.filter(g=>g.manager_id===m.id))).join('')||empty('Sin Managers para mostrar',adminAttention?'No hay Managers que coincidan con el filtro.':'Agrega el primer Manager de esta Cuenta.')}</div></section>`;
}
function managerBlock(m,groups){
 const archived=state.people.filter(p=>p.role==='USER'&&p.status==='DISABLED'&&p.manager_id===m.id&&!p.group_id),lead=adminLead(m),techs=state.people.filter(p=>!p.is_lead&&groups.some(g=>g.id===p.group_id)&&adminLive(p));
 return `<article class="admin-manager-card" data-manager="${esc(m.id)}"><header>${identity(m)}${badge(m.status)}${moreActions('manager',m.id,full(m))}</header><div class="admin-manager-context">${groups.length?`${groups.length} Grupos · ${techs.length} Técnicos`:'Sin Grupos asignados'}</div><section class="admin-lead-slot"><p class="eyebrow">LEAD · BACKUP DEL MANAGER</p>${lead?`<div class="admin-lead-person">${identity(lead)}${badge(lead.status)}${moreActions('person',lead.id,full(lead))}</div>`:`<div class="admin-lead-empty">${icon('profile')}<span>Sin Lead asignado</span></div>`}</section><footer class="admin-card-actions">${btn('Editar Manager','person-edit',m.id,'secondary')}${lead?btn('Editar Lead','person-edit',lead.id,'secondary'):m.status!=='DISABLED'?btn('＋ Agregar Lead','lead-new',m.id,'primary'):''}${m.status==='PENDING_ACTIVATION'?btn('Activar Manager','activation-code',m.id,'link'):''}${lead?.status==='PENDING_ACTIVATION'?btn('Activar Lead','activation-code',lead.id,'link'):''}</footer>${archived.length?`<details class="admin-archived"><summary>Leads dados de baja (${archived.length})</summary>${archived.map(p=>`<div><span><strong>${esc(full(p))}</strong><small>${esc(p.employee_id)}</small></span>${btn('Reactivar','person-reactivate',p.id,'secondary small')}</div>`).join('')}</details>`:''}</article>`;
}
function groupCard(g){
  const people=state.people.filter(p=>p.role==='USER'&&p.group_id===g.id);
  return `<article class="group-card" data-group="${esc(g.id)}" data-drop-group="${esc(g.id)}"><header><div><span class="entity-overline">GRUPO · ${esc(entityCode(g))}</span><div class="group-title-line"><h3><button type="button" class="entity-title" data-action="group-edit" data-id="${esc(g.id)}" aria-label="Editar Grupo ${esc(g.name)}">${esc(g.name)}</button></h3><button type="button" class="group-count-open" data-action="group-details" data-id="${esc(g.id)}">${people.length} ${people.length===1?'Técnico':'Técnicos'} ↗</button></div></div><div class="entity-actions"><button type="button" class="secondary small group-overview-header-action" data-action="organizer-open" data-id="${esc(g.id)}">Organizar</button>${moreActions('group',g.id,'Grupo '+g.name)}</div></header><div class="group-overview-actions">${btn('Ver '+people.length+' Técnicos','group-details',g.id,'link')}${btn('Organizar','organizer-open',g.id,'secondary small')}</div><div class="technicians">${people.map(u=>`<div class="technician" data-person="${esc(u.id)}" draggable="${u.status!=='DISABLED'&&!state.timers.some(t=>t.user_id===u.id)}"><span class="drag-handle" title="Arrastrar Técnico" aria-hidden="true">${icon('drag')}</span><button type="button" class="technician-open" data-action="person-edit" data-id="${esc(u.id)}" aria-label="Editar ${esc(full(u))}"><span class="avatar">${esc(initials(u))}</span><span class="identity"><strong>${esc(full(u))}${u.is_lead?'<span class="lead-pill">Lead</span>':''}</strong><small>${esc(u.employee_id)} <i>·</i> ${esc(statuses[u.status])}</small></span></button><div class="entity-actions"><button type="button" class="move-person" data-action="person-transfer" data-id="${esc(u.id)}" aria-label="Mover a ${esc(full(u))} de Grupo" title="Mover a otro Grupo">${icon('move')}</button>${moreActions('person',u.id,full(u))}</div></div>`).join('')||'<p class="quiet-empty">Aún no hay Técnicos en este Grupo.</p>'}</div><footer>${btn('＋ Agregar Técnico','tech-new',g.id,'secondary')}</footer></article>`;
}
function adminsPage(){return heading('GOBERNANZA','Administradores','Accesos con autoridad para administrar la estructura y las cuentas.',btn('＋ Administrador','admin-new','','primary'))+peopleTable(state.people.filter(p=>p.role==='ADMIN'));}
function peopleTable(people,search=false){
  return `<section class="panel table-panel">${search?`<div class="team-search-bar"><label class="search"><span>${icon('search')}</span><input id="team-search" placeholder="Buscar por nombre, Employee ID o correo" aria-label="Buscar Técnicos"></label></div>`:''}<div class="table-scroll"><table><thead><tr><th>Persona</th><th>Correo</th><th>Rol / Grupo</th><th>Estado</th><th class="right">Acciones</th></tr></thead><tbody>${people.map(p=>`<tr data-search-row="${esc(`${full(p)} ${p.employee_id||p.username} ${p.email}`.toLowerCase())}"><td><div class="table-identity">${identity(p)}${p.is_lead?'<span class="lead-pill">Lead</span>':''}</div></td><td>${esc(p.email)}</td><td>${esc(p.role==='USER'?p.is_lead?'Lead del Manager':group(p.group_id)?.name||'Sin Grupo':roles[p.role])}</td><td>${badge(p.status)}</td><td><div class="row-actions">${isAdmin()?btn('Editar','person-edit',p.id,'secondary small')+moreActions(p.role==='MANAGER'?'manager':'person',p.id,full(p)):''}${isManager()&&p.role==='USER'&&!p.is_lead&&p.status!=='DISABLED'?btn('Editar','person-edit',p.id,'secondary small')+btn('Mover','team-move',p.id,'secondary small'):''}${isManager()&&p.is_lead&&p.status==='ACTIVE'?btn(currentDelegation()?.lead_id===p.id?'Editar delegación':'Delegar','delegation-inline',p.id,'secondary small'):''}${isAdmin()&&p.status==='PENDING_ACTIVATION'?btn('Activación','activation-code',p.id,'link'):''}</div></td></tr>`).join('')}</tbody></table></div>${!people.length?empty('Sin personas todavía','Los nuevos integrantes aparecerán aquí.'):''}</section>`;
}
function teamPage(){
  const people=state.people.filter(p=>p.role==='USER'&&((state.scope.includes(p.group_id)||p.is_lead&&p.manager_id===me().id)||p.is_lead&&p.manager_id===me().id)),current=isManager()?currentDelegation():null;
  return heading('PERSONAS','Mi equipo','Agrega y edita tus Técnicos. Arrastra una tarjeta para cambiarla de Grupo.',isManager()?btn('Traslados de Técnicos'+((state.manager_transfers||[]).filter(r=>r.status==='SUBMITTED'&&r.target_manager_id===me().id).length?' · '+state.manager_transfers.filter(r=>r.status==='SUBMITTED'&&r.target_manager_id===me().id).length:''),'manager-transfers','','secondary')+btn('＋ Grupo','manager-group-new',me().id,'secondary')+btn('＋ Agregar Técnico','tech-new','','primary'):'')+
  (isManager()?'<section class="team-kanban-workspace">':'')+
  (isManager()?managerTeamBoard(people):peopleTable(people,true))+
  (isManager()&&state.delegations.length?`<details class="delegation-history panel"><summary>Historial de delegaciones</summary><div class="delegation-list">${state.delegations.map(d=>`<article><div><strong>${esc(full(person(d.lead_id)))}</strong><small>${d.end_at?range(d.start_at,d.end_at):'Desde '+fmtDate(d.start_at)+' · Hasta revocación manual'} · ${d.group_ids.length} Grupos</small></div><span class="pill">${d.revoked_at?'Revocada':d.end_at&&new Date(d.end_at).getTime()<=Date.now()+serverOffset?'Finalizada':new Date(d.start_at).getTime()>Date.now()+serverOffset?'Programada':'Activa'}</span></article>`).join('')}</div></details>`:'')+(isManager()?'</section>':'');
}
let teamBoardQuery='',teamBoardDrag='';
function managerTeamBoard(people){
 const leads=people.filter(p=>p.is_lead&&p.status!=='DISABLED'),groups=state.groups.filter(g=>g.manager_id===me().id);
 return `<div class="team-board-lead">${leads.map(l=>`<div>${identity(l)}<span class="lead-pill">Lead del Manager</span>${currentDelegation()?.lead_id===l.id?'<span class="team-delegation-active">Delegación activa · hasta revocación</span>'+btn('Revocar','delegation-revoke',currentDelegation().id,'secondary small'):l.status==='ACTIVE'?btn('Delegar','delegation-inline',l.id,'secondary small'):badge(l.status)}</div>`).join('')||'<p>Sin Lead asignado. Admin puede incorporarlo a tu equipo.</p>'}</div>${delegationDraftLead?inlineDelegationForm(person(delegationDraftLead)):''}<div class="team-board-toolbar"><label>${icon('search')}<input id="team-board-search" type="search" value="${esc(teamBoardQuery)}" placeholder="Buscar Técnico, Employee ID o Grupo…" aria-label="Buscar en el tablero"></label><span>${groups.length} Grupos · ${people.filter(p=>!p.is_lead&&p.status!=='DISABLED').length} Técnicos</span></div><div class="team-board-hint">${icon('info')}<span>Arrastra a otro Grupo para mover al Técnico. Revisa el destino y confirma; no requiere autorización de Admin.</span></div><div class="team-kanban" aria-label="Técnicos por Grupo">${groups.map(g=>`<section class="team-lane" data-team-destination="${esc(g.id)}" aria-label="Grupo ${esc(g.name)}"><header><span class="entity-overline">${esc(entityCode(g))}</span><h2><button class="entity-title" data-action="group-edit" data-id="${esc(g.id)}" aria-label="Editar Grupo ${esc(g.name)}">${esc(g.name)}</button></h2><span class="team-lane-count">${people.filter(p=>!p.is_lead&&p.group_id===g.id&&p.status!=='DISABLED').length} Técnicos</span></header><div class="team-lane-cards">${people.filter(p=>!p.is_lead&&p.group_id===g.id&&p.status!=='DISABLED').map(p=>{const pendingTransfer=(state.manager_transfers||[]).find(r=>r.user_id===p.id&&r.status==='SUBMITTED');return `<article class="team-tech-card" draggable="true" data-team-person="${esc(p.id)}" data-board-search="${esc((full(p)+' '+p.employee_id+' '+g.name+' '+entityCode(g)).toLowerCase())}"><span class="team-card-grip" aria-hidden="true">${icon('drag')}</span><button class="team-card-open" data-action="team-details" data-id="${esc(p.id)}" aria-label="Ver ficha de ${esc(full(p))}">${identity(p)}</button><div class="team-card-meta">${badge(p.status)}${pendingTransfer?'<span class="team-card-indicator">Traslado pendiente</span>':''}${state.timers.some(t=>t.user_id===p.id)?'<span class="team-card-indicator">Timer activo</span>':''}<button class="team-card-details" data-action="team-details" data-id="${esc(p.id)}" aria-label="Detalles de ${esc(full(p))}"><span>Ver ficha</span>${icon('forward')}</button></div></article>`;}).join('')||'<p class="team-lane-empty">Sin Técnicos asignados</p>'}</div><p class="team-lane-no-results" hidden>Sin coincidencias en este Grupo</p><footer>${btn('＋ Agregar Técnico','tech-new',g.id,'link')}</footer></section>`).join('')||empty('Sin Grupos asignados','Admin debe asignar los Grupos de tu equipo.')}</div><p id="team-board-empty" hidden>No hay coincidencias. Ajusta la búsqueda.</p>`;
}
function filterTeamBoard(){const q=teamBoardQuery.trim().toLowerCase();let total=0;$$('.team-lane').forEach(lane=>{let count=0;$$('.team-tech-card',lane).forEach(card=>{card.hidden=!!q&&!card.dataset.boardSearch.includes(q);if(!card.hidden)count++;});total+=count;const note=$('.team-lane-no-results',lane);if(note)note.hidden=!q||count>0;});const empty=$('#team-board-empty');if(empty)empty.hidden=!q||total>0;}
function currentDelegation(){
  return state.delegations.filter(d=>d.manager_id===me().id&&!d.revoked_at&&(!d.end_at||new Date(d.end_at).getTime()>Date.now()+serverOffset)).at(-1)||null;
}
function inlineDelegationForm(lead){
  if(!lead)return '';
  const current=currentDelegation(),same=current?.lead_id===lead.id,groups=state.groups.filter(g=>state.scope.includes(g.id));
  return `<section class="panel inline-delegation" id="delegation-editor"><div class="section-heading"><div><p class="eyebrow">DELEGACIÓN DEL MANAGER</p><h2>${esc(full(lead))}</h2><p class="muted">Cubrirá a todo el equipo del Manager. La delegación inicia al guardar y permanece hasta que la revoques.</p></div><button type="button" class="icon-btn" data-action="delegation-cancel" aria-label="Cerrar edición">${icon('close')}</button></div><form data-form="delegation"><input type="hidden" name="lead_id" value="${esc(lead.id)}"><div class="form-body"><p class="callout">La delegación cubre automáticamente todos los Grupos del Manager (${groups.length}). Podrá aprobar y rechazar OT de sus Técnicos, salvo sus propios registros.</p><p class="callout">${current&&!same?`Al guardar, ${esc(full(lead))} sustituirá a ${esc(full(person(current.lead_id)))}. `:''}La asignación anterior se revoca al guardar. Sólo habrá una persona delegada para este Manager. No vence automáticamente. Puedes revocarla desde Mi equipo; no se permite autoaprobación.</p></div><p class="form-error" role="alert"></p><div class="inline-form-actions"><button type="button" class="secondary" data-action="delegation-cancel">Cancelar</button><button type="submit" class="primary">${same?'Guardar delegación':'Asignar delegación'}</button></div></form></section>`;
}

function timerPanel(timers,pausedRecords=[],documents=[]){
  return `<section class="timer-list">${timers.map(t=>{const o=state.overtime.find(o=>o.id===t.overtime_id),u=person(t.user_id),g=group(u?.group_id),own=t.user_id===me().id;return `<article class="timer-card timer-running"><div class="timer-identity"><span class="timer-state-mark">${icon('time')}</span><div class="timer-copy"><span class="small-label">${own?'TU TIMER ACTIVO':esc(full(u))}</span><strong>${o?.capture_type==='EMERGENCY'?'OT de emergencia':'OT programada'}</strong><small>${esc(g?.name||'Sin Grupo')} · ${esc(u?.employee_id||'')}</small><small>${esc(o?.reference||'Por documentar')} · Inicio: ${fmtTime(t.start_at)}</small>${o?.capture_type==='PLANNED'?`<small>Autorizada hasta ${fmtDate(o.scheduled_end)} · ${fmtTime(o.scheduled_end)}</small>`:''}</div></div><div class="timer-measure"><span class="small-label">TIEMPO TRANSCURRIDO</span><span class="timer-clock" data-elapsed="${esc(t.start_at)}" data-base="${o?.worked_seconds||0}" ${o?.capture_type==='PLANNED'?`data-until="${esc(o.scheduled_end)}"`:''}>00:00:00</span><span class="timer-running-label"><span class="live-dot"></span> En curso</span></div><div class="timer-actions">${isManager()||state.can_approve?btn('Ver actividad','timer-open',t.overtime_id,'secondary small'):''}${own&&o?.capture_type==='PLANNED'?extensionControl(o):''}${own?btn(o?.capture_type==='EMERGENCY'?'Detener y documentar':'Detener Timer','timer-stop',t.id,'danger'):''}${own&&o?.capture_type==='EMERGENCY'?'<small class="timer-next-step">Después, documenta la actividad para enviarla a aprobación.</small>':''}</div></article>`;}).join('')}${pausedRecords.map(pausedTimerCard).join('')}${documents.map(documentationCard).join('')}</section>`;
}
function documentationCard(o){
 return `<article class="timer-documentation" data-documentation-id="${esc(o.id)}"><span class="documentation-icon">${icon('info')}</span><div><span class="small-label">SIGUIENTE PASO · DOCUMENTACIÓN</span><h3>Timer detenido. Falta documentar la OT.</h3><p>${range(o.start_at,o.end_at)} · ${hours((o.worked_seconds||0)/60)} h registradas</p><small>Completa la referencia y la actividad para enviarla a aprobación. Las horas aún no suman al total aprobado.</small></div>${btn('Documentar OT','ot-edit',o.id,'primary')}</article>`;
}
function pausedTimerCard(o){
 const canResume=o.status==='APPROVED'&&new Date(o.scheduled_end).getTime()>Date.now()+serverOffset;
 return `<article class="timer-card timer-paused" data-paused-timer="${esc(o.id)}"><span class="paused-marker">${icon('time')}</span><div><span class="small-label">TU TIMER PAUSADO</span><strong>${esc(o.reference||'OT programada')}</strong><small>${hours((o.worked_seconds||0)/60)} h trabajadas · la espera no suma tiempo.</small><small>Fin autorizado: ${fmtDate(o.scheduled_end)} · ${fmtTime(o.scheduled_end)}</small></div><div class="timer-actions">${canResume?btn('Reanudar Timer','timer-planned',o.id,'primary'):btn('Reanudar Timer','timer-planned',o.id,'secondary','disabled')}${extensionControl(o)}${btn('Finalizar tiempo trabajado','paused-finish',o.id,'secondary')}${btn('Detalle','record-detail','ot:'+o.id,'link')}</div></article>`;
}
function ownTimerModal(id){
 const o=state.overtime.find(o=>o.id===id&&o.user_id===me().id);if(!o)return;
 const t=state.timers.find(t=>t.overtime_id===id&&t.user_id===me().id),paused=o.execution==='PAUSED';
 if(!t&&!paused)return detailModal('ot:'+id);
 const planned=o.capture_type==='PLANNED',canResume=paused&&o.status==='APPROVED'&&Date.parse(o.scheduled_end)>Date.now()+serverOffset;
 const elapsed=Number(o.worked_seconds)||0,clock=[Math.floor(elapsed/3600),Math.floor(elapsed/60)%60,Math.floor(elapsed)%60].map(n=>String(n).padStart(2,'0')).join(':');
 const notice=paused?'La ventana autorizada terminó. Solicita una extensión; la espera no suma tiempo. Tras su aprobación, pulsa Reanudar.':planned?'El Timer se pausará al terminar la ventana autorizada. Si necesitas más tiempo, solicita una extensión.':'Al detener el Timer se abrirá la documentación. Completa la OT para enviarla a aprobación; el aviso permanecerá hasta que la envíes.';
 showModal(planned?'Timer de OT programada':'Timer de emergencia',`<div class="form-body timer-dialog-body"><div class="timer-dialog-subject"><div><span class="small-label">${planned?'ACTIVIDAD PROGRAMADA':'REGISTRO DE EMERGENCIA'}</span><h3>${esc(o.reference||'OT por documentar')}</h3><p>${esc(group(me().group_id)?.name||'Lead del Manager')} · ${esc(me().employee_id)}</p></div>${badge(paused?'PAUSED':'RUNNING')}</div><section class="timer-dialog-clock ${paused?'is-paused':''}" ${paused?`data-paused-timer="${esc(id)}"`:''}><span class="small-label">${paused?'TIEMPO TRABAJADO':'TIEMPO TRANSCURRIDO'}</span><strong ${t?`data-elapsed="${esc(t.start_at)}" data-base="${elapsed}" ${planned?`data-until="${esc(o.scheduled_end)}"`:''}`:''}>${clock}</strong><span class="timer-dialog-state">${paused?icon('time'):'<i class="live-dot"></i>'}${paused?'En pausa · espera sin cargo':'En curso · registrando tu tiempo'}</span></section><div class="timer-dialog-period"><div><span>Inicio del trabajo</span><strong>${fmtDate(o.start_at||t?.start_at)} · ${fmtTime(o.start_at||t?.start_at)}</strong></div>${planned?`<div><span>Fin autorizado</span><strong>${fmtDate(o.scheduled_end)} · ${fmtTime(o.scheduled_end)}</strong></div>`:''}</div><div class="timer-dialog-notice">${icon('info')}<p>${notice}</p></div>${planned?`<div class="timer-dialog-extension">${extensionControl(o)}</div>`:''}</div><footer class="dialog-footer timer-dialog-footer">${btn('Cerrar','close','','secondary')}${paused?btn('Finalizar tiempo trabajado','paused-finish',id,'secondary')+btn('Reanudar Timer','timer-planned',id,canResume?'primary':'secondary',canResume?'':'disabled'):btn(planned?'Detener Timer':'Detener y documentar','timer-stop',t.id,'danger')}</footer>`);
 $('#modal').classList.add('own-timer-dialog','focused-timer-dialog');$('#modal').dataset.overtimeId=id;tick();
}
function recordTimerControl(o){
 if(o.capture_type!=='PLANNED')return '';
 if(state.timers.some(t=>t.overtime_id===o.id)||o.execution==='PAUSED')return btn('Ver Timer','own-timer-open',o.id,'secondary');
 if(o.execution!=='SCHEDULED')return '';
 const ready=o.status==='APPROVED'&&new Date(o.scheduled_start).getTime()<=Date.now()+serverOffset&&new Date(o.scheduled_end).getTime()>Date.now()+serverOffset;
 return btn(ready?'Iniciar Timer':'Timer','timer-planned',o.id,ready?'primary':'secondary',ready?'':`disabled aria-describedby="ot-availability-${esc(o.id)}"`);
}
function extensionControl(o){
  if(!['RUNNING','PAUSED'].includes(o.execution)||!o.start_at)return '';
  const pending=(state.extensions||[]).find(e=>e.overtime_id===o.id&&e.status==='SUBMITTED');
  return pending?`<span class="pill">Extensión pendiente</span>${btn('Cancelar solicitud','extension-cancel',pending.id,'link')}`:btn('Solicitar extensión','extension-new',o.id,'secondary small');
}
function extensionHistory(o){
  const events=(state.extensions||[]).filter(e=>e.overtime_id===o.id);if(!events.length)return '';
  return `<div class="extension-history">${events.map(e=>`<p><strong>Extensión ${esc(({APPROVED:'autorizada',REJECTED:'rechazada',SUBMITTED:'pendiente',CANCELLED:'cancelada'})[e.status]||e.status)}</strong> · hasta ${fmtDate(e.requested_end)} ${fmtTime(e.requested_end)}${e.decision_reason?`<br>${esc(e.decision_reason)}`:''}</p>`).join('')}</div>`;
}
function extensionReview(){
  const pending=(state.extensions||[]).filter(e=>e.status==='SUBMITTED'&&e.requested_by!==me().id);if(!pending.length)return '';
  return `<section class="panel extension-review"><div class="section-heading"><div><p class="eyebrow">AUTORIZACIÓN DE TIEMPO ADICIONAL</p><h2>Extensiones pendientes</h2></div><span class="pill">${pending.length}</span></div><div class="record-list">${pending.map(e=>{const o=state.overtime.find(o=>o.id===e.overtime_id),u=person(e.requested_by);return `<article class="record-card"><div><span class="small-label">${esc(group(u?.group_id)?.name)}</span><h3>${esc(full(u))} · ${esc(u?.employee_id)}</h3><p>${esc(o?.reference)} · ${esc(o?.description)}</p><small>Fin autorizado: ${fmtDate(e.previous_end)} ${fmtTime(e.previous_end)}<br>Nuevo fin solicitado: ${fmtDate(e.requested_end)} ${fmtTime(e.requested_end)}</small><p>${esc(e.reason)}</p></div><div class="entity-actions">${btn('Autorizar extensión','extension-approve',e.id,'primary small')}${btn('Rechazar','extension-reject',e.id,'text-danger')}</div></article>`;}).join('')}</div></section>`;
}
function extensionModal(id){
  const o=state.overtime.find(o=>o.id===id);if(!o)return;
  showModal('Solicitar extensión de OT',form('extension',`<p class="callout"><strong>${esc(o.reference)}</strong><br>Fin autorizado: ${fmtDate(o.scheduled_end)} · ${fmtTime(o.scheduled_end)}. Si llega esa hora, el Timer se pausa hasta que se autorice la extensión.</p>${field('requested_end','Nueva fecha y hora de fin *','','datetime-local','required')}<label class="field"><span>Motivo de la extensión *</span><textarea name="reason" rows="3" required></textarea></label><p class="muted footnote">La espera no se cuenta como tiempo trabajado. Si se autoriza después de la pausa, deberás pulsar Reanudar.</p>`,id,'Solicitar extensión'));
  $('#modal').classList.add('medium-dialog');
}

function exportLink(extra=''){
  const q=new URLSearchParams({month});if(['time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);else{if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);if(filters.kind)q.set('kind',filters.kind);}
  if(page==='claim')q.set('view','claim');
  return `<a class="secondary button" href="/api/export.xlsx?${esc(q.toString())}" download>↓ Excel ${extra||'aprobados'}</a>`;
}
let calendarDrag=null,calendarRangeMode=false,calendarRangeStart=null,calendarSuppressClickUntil=0;
function paintCalendarRange(start,end){
 const [a,b]=[start,end].sort();
 $$('[data-calendar-date]').forEach(cell=>{const d=cell.dataset.calendarDate;cell.classList.toggle('calendar-selected',d>=a&&d<=b);cell.classList.toggle('calendar-range-start',d===a);cell.classList.toggle('calendar-range-end',d===b);});
 const hint=$('#calendar-selection-hint');if(hint)hint.textContent=start===end?'Inicio: '+fmtDate(start)+'. Selecciona el día final.':'Guardia del '+fmtDate(a)+' al '+fmtDate(b)+'.';
}
function resetCalendarRange(){calendarRangeStart=null;$$('.calendar-selected').forEach(cell=>cell.classList.remove('calendar-selected','calendar-range-start','calendar-range-end'));const hint=$('#calendar-selection-hint');if(hint)hint.textContent=calendarRangeMode?'Selecciona el día inicial y después el final.':'Un clic registra OT. Arrastra varios días para solicitar una Guardia.';}
function calendarGuardRange(start,end){
 const [a,b]=[start,end].sort();
 if(me()?.is_lead){resetCalendarRange();return toast('El Lead puede registrar OT; no solicita Guardias.',true);}
 if((Date.parse(b)-Date.parse(a))/86400000>31){resetCalendarRange();return toast('Selecciona un periodo de hasta 32 días para la Guardia.',true);}
 calendarRangeMode=false;resetCalendarRange();$('[data-action=calendar-range]')?.setAttribute('aria-pressed','false');guardModal(a,b);
}
function calendarPickRange(day){
 if(!calendarRangeStart){calendarRangeStart=day;paintCalendarRange(day,day);return;}
 calendarGuardRange(calendarRangeStart,day);
 const toggle=$('[data-action=calendar-range]');if(toggle)toggle.setAttribute('aria-pressed','false');
}
function availableGroupActivities(){return (state.group_activities||[]).filter(w=>!state.overtime.some(o=>o.user_id===me().id&&o.window_id===w.id));}
function groupActivityModal(id){
 const w=(state.group_activities||[]).find(w=>w.id===id);if(!w)return toast('La actividad ya no está disponible para tu Grupo.',true);
 const current=Date.now()+serverOffset,ready=w.status==='APPROVED'&&Date.parse(w.scheduled_start)<=current&&Date.parse(w.scheduled_end)>current&&!state.timers.some(t=>t.user_id===me().id);
 showModal('OT programada del Grupo',`<div class="form-body"><div class="group-activity-title"><span class="small-label">ACTIVIDAD DEL GRUPO</span><h3>${esc(w.reference)}</h3>${badge(w.status)}</div><p>${esc(w.description)}</p><dl><dt>Ventana programada</dt><dd>${range(w.scheduled_start,w.scheduled_end)}</dd><dt>Registrada por</dt><dd>${esc(w.author_name)}</dd></dl><p class="callout">Cada integrante registra sus propios tramos de trabajo. Inicia tu Timer cuando participes y detenlo al terminar; tus horas se revisan individualmente.</p><p class="group-activity-availability" data-group-availability="${esc(w.id)}">${w.status!=='APPROVED'?'La actividad requiere aprobación antes de iniciar.':Date.parse(w.scheduled_start)>current?'Timer disponible el '+fmtDate(w.scheduled_start)+' a las '+fmtTime(w.scheduled_start)+'.':'El Timer está disponible dentro de la ventana autorizada.'}</p></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}${btn('Iniciar mi Timer','group-timer-start',id,ready?'primary':'secondary',ready?'':'disabled')}</footer>`);$('#modal').classList.add('admin-dialog','group-activity-dialog');
}
function calendarDate(value){return new Date(value).toLocaleDateString('sv-SE',{timeZone:state?.timezone||'America/Mexico_City'});}
function calendarEvents(day){
 const events=[];
 for(const o of state.overtime.filter(o=>o.user_id===me().id)){
  const start=recordStart(o),end=o.end_at||o.scheduled_end||new Date(Date.now()+serverOffset).toISOString();
  if(calendarDate(start)>day||calendarDate(end)<day)continue;
  // A midnight end belongs to the preceding day, unless the record starts at that instant.
  if(calendarDate(end)===day&&fmtTime(end)==='00:00'&&calendarDate(start)!==day)continue;
  events.push({key:'ot:'+o.id,kind:o.capture_type==='PLANNED'?'planned':o.capture_type==='EMERGENCY'?'emergency':'historical',title:o.reference||'OT por documentar',time:calendarDate(start)===day?fmtTime(start):'Continúa',status:o.status});
 }
 for(const w of availableGroupActivities()){
  if(calendarDate(w.scheduled_start)>day||calendarDate(w.scheduled_end)<day||calendarDate(w.scheduled_end)===day&&fmtTime(w.scheduled_end)==='00:00'&&calendarDate(w.scheduled_start)!==day)continue;
  events.push({key:'group:'+w.id,kind:'planned',title:'Grupo · '+w.reference,time:calendarDate(w.scheduled_start)===day?fmtTime(w.scheduled_start):'Continúa',status:w.status});
 }
 for(const g of state.guards.filter(g=>g.user_id===me().id)){
  const parts=(g.timeline_days||[]).filter(p=>p.date===day);
  if(!parts.length&&((g.timeline_days||[]).length||g.start_date!==day))continue;
  events.push({key:'guard:'+g.id,kind:'guard',title:g.rule_snapshot.name,time:'Guardia',status:g.status});
 }
 return events.sort((a,b)=>(a.kind==='guard'?-1:1)-(b.kind==='guard'?-1:1)||a.time.localeCompare(b.time)||a.key.localeCompare(b.key));
}
function monthlyCalendar(expanded=false){
 const [year,number]=month.split('-').map(Number),first=new Date(Date.UTC(year,number-1,1)),days=new Date(Date.UTC(year,number,0)).getUTCDate();
 const offset=first.getUTCDay(),count=Math.ceil((offset+days)/7)*7,visibleEvents=expanded?(innerHeight<680?0:1):(innerHeight>=900&&innerWidth>=700?2:1),today=calendarDate(new Date(Date.now()+serverOffset));
 const cells=Array.from({length:count},(_,i)=>{
  const date=new Date(Date.UTC(year,number-1,i-offset+1)),day=date.toISOString().slice(0,10),outside=day.slice(0,7)!==month,events=calendarEvents(day);
  return `<div class="calendar-day ${outside?'calendar-outside':''} ${day===today?'calendar-today':''}" data-calendar-date="${day}" data-action="${expanded?'calendar-day':'calendar-new'}" data-id="${day}"><div class="calendar-day-head">${btn(String(date.getUTCDate()),expanded?'calendar-day':'calendar-new',day,'calendar-date-button',`aria-label="Registrar OT el ${esc(fmtDate(day))}${day<today?', fecha pasada':''}" ${day===today?'aria-current="date"':''}`)}${expanded&&events.length?btn(String(events.length),'calendar-day',day,'calendar-preview-count',`aria-label="Ver ${events.length} actividades del ${esc(fmtDate(day))}"`):''}${expanded?'':btn('＋','calendar-new',day,'calendar-add',`aria-label="Agregar registro el ${esc(fmtDate(day))}"`)}</div><div class="calendar-events">${events.slice(0,visibleEvents).map(e=>`<button type="button" class="calendar-event calendar-${e.kind} ${['REJECTED','CANCELLED'].includes(e.status)?'calendar-inactive':''}" data-action="record-detail" data-id="${esc(e.key)}" aria-label="${esc(e.title+' · '+e.time+' · '+statuses[e.status])}" title="${esc(e.title+' · '+statuses[e.status])}">${e.kind==='guard'?'':`<span>${esc(e.time)}</span>`}<strong>${esc(e.title)}</strong><i class="calendar-status ${e.status.toLowerCase()}" aria-hidden="true"></i></button>`).join('')}${events.length>visibleEvents?btn('+'+(events.length-visibleEvents)+' más','calendar-day',day,'calendar-more'):''}</div></div>`;
 }).join('');
 return `<section class="panel monthly-calendar" data-view-label="Calendario"><header class="calendar-heading"><div><h2>${esc(monthLabel(month))}</h2></div><div class="calendar-heading-actions">${expanded?`<button type="button" class="secondary small" data-action="calendar-preview-prev" aria-label="Mes anterior">‹</button><input type="month" data-preview-month value="${esc(month)}" aria-label="Mes del calendario ampliado"><button type="button" class="secondary small" data-action="calendar-preview-next" aria-label="Mes siguiente">›</button>${btn('Hoy','calendar-preview-today','','secondary small')}`:`${btn('Ampliar calendario','calendar-preview','','secondary small')}${!me().is_lead?btn('Seleccionar periodo','calendar-range','','secondary small',`aria-pressed="${calendarRangeMode}"`):''}${btn('Hoy','calendar-today','','secondary small')}`}</div></header><div class="calendar-legend"><span class="planned">OT programada</span><span class="historical">OT histórica</span><span class="emergency">Emergencia</span><span class="guard">Guardia</span><small id="${expanded?'calendar-preview-hint':'calendar-selection-hint'}" class="calendar-selection-hint" role="status">${expanded?'Selecciona un día para ver su agenda o abre una actividad.':calendarRangeMode?'Selecciona el día inicial y después el final.':'Un clic registra OT. Arrastra varios días para solicitar una Guardia.'}</small></div><div class="calendar-scroll"><div class="calendar-weekdays">${['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'].map(d=>`<span>${d}</span>`).join('')}</div><div class="calendar-grid">${cells}</div></div></section>`;
}
function calendarPreviewModal(){
 showModal('Calendario ampliado',`<div class="form-body calendar-preview-body">${monthlyCalendar(true)}</div><footer class="dialog-footer">${btn('Cerrar vista previa','close','','secondary')}</footer>`,true);
 $('#modal').classList.add('calendar-preview-dialog');
}
async function navigateCalendarPreview(delta){
 if(delta===0)month=calendarDate(new Date(Date.now()+serverOffset)).slice(0,7);
 else{const [y,m]=month.split('-').map(Number);month=new Date(Date.UTC(y,m-1+delta,1)).toISOString().slice(0,7);}
 await loadLedger();render();calendarPreviewModal();
}
function calendarNewRecord(day){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(day))return;
 otModal();const form=$('#modal [data-form=ot]');
 form.elements.scheduled_start.value=day+'T09:00';form.elements.scheduled_end.value=day+'T10:00';
 if(day===calendarDate(new Date(Date.now()+serverOffset))){
  const next=new Date(Date.now()+serverOffset+3600000),end=new Date(next.getTime()+3600000);
  form.elements.scheduled_start.value=localInput(next.toISOString());form.elements.scheduled_end.value=localInput(end.toISOString());
 }
 syncOtType();
}
function calendarDayModal(day){
 const events=calendarEvents(day);
 showModal('Agenda · '+fmtDate(day),`<div class="form-body calendar-agenda"><p>OT y Guardias de este día. Abre un registro para consultar sus detalles.</p>${events.map(e=>`<button type="button" class="calendar-agenda-event calendar-${e.kind}" data-action="record-detail" data-id="${esc(e.key)}"><span>${esc(e.time)}</span><strong>${esc(e.title)}</strong>${badge(e.status)}</button>`).join('')}</div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}${btn('Registrar OT','calendar-new',day,'primary')}</footer>`);$('#modal').classList.add('admin-dialog','calendar-day-dialog');
}
function calendarDocumentationNotice(){
 const pending=state.overtime.filter(o=>o.user_id===me().id&&o.status==='DOCUMENTATION'&&o.execution!=='RUNNING');
 return pending.length?`<div class="guard-rule-notice calendar-documentation-notice" role="status">${icon('info')}<span>Tienes ${pending.length} OT por documentar. Completa la actividad para enviarla a aprobación.</span>${btn('Documentar OT','ot-edit',pending[0].id,'secondary small')}</div>`:'';
}
function timePage(){
  return heading('HORAS EXTRA Y GUARDIAS','Mi tiempo','Programa y registra OT, solicita guardias y revisa tus horas aprobadas.',monthControl()+exportLink()+btn('Respaldo / Recuperar','time-recovery','','secondary'))+
  monthlyCalendar()+
  timerPanel(state.timers.filter(t=>t.user_id===me().id),state.overtime.filter(o=>o.user_id===me().id&&o.execution==='PAUSED'),state.overtime.filter(o=>o.user_id===me().id&&o.status==='DOCUMENTATION'&&o.execution!=='RUNNING'))+
  `<section class="time-actions">${btn('＋ Programar OT','ot-new','','primary')}${btn('⚡ Iniciar emergencia','timer-start','','secondary')}${!me().is_lead?btn('＋ Solicitar Guardia','guard-new','','secondary'):''}${state.guards.some(g=>g.user_id===me().id&&g.rule_changed)?`<div class="guard-rule-notice" role="status">${icon('info')}<span>Tu Manager actualizó una regla de Guardia. Tienes ${state.guards.filter(g=>g.user_id===me().id&&g.rule_changed).length} solicitudes que necesitan revisión.</span>${state.guards.filter(g=>g.user_id===me().id&&g.rule_changed).slice(0,1).map(g=>btn(fmtDate(g.start_date)+' · Revisar','guard-edit',g.id,'secondary small')).join('')}</div>`:''}${calendarDocumentationNotice()}</section><section class="kpis three">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real trabajado','↗')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Guardia aprobada menos OT','◷')}${kpi('Total del mes',`${hours(ledger.ot_minutes+ledger.guard_minutes)} <em>h</em>`,'Mismo cálculo en Claim y ADP','▦')}</section>`;
}
function recordStart(o){return o.start_at||o.scheduled_start||o.created_at;}
function teamTimePage(){
  const people=state.people.filter(p=>p.role==='USER'&&(state.scope.includes(p.group_id)||p.is_lead&&p.manager_id===me().id));
  return heading('DECISIONES PENDIENTES','Aprobaciones','Revisa OT, Guardias y extensiones pendientes de tu equipo.')+`<section class="panel filters"><div>${select('filter-group','Grupo',options(state.groups,filters.group,g=>g.name,'Todos los Grupos'))}${select('filter-person','Técnico',options(people.filter(p=>!filters.group||p.group_id===filters.group),filters.person,full,'Todos los Técnicos'))}${select('filter-kind','Solicitud',`<option value="">OT y Guardias</option><option value="OT" ${filters.kind==='OT'?'selected':''}>Tiempo extra</option><option value="GUARD" ${filters.kind==='GUARD'?'selected':''}>Guardia</option>`)}</div><p class="muted footnote approvals-note">Sólo solicitudes pendientes, de todos los periodos. Para consultar registros y comparar horas, abre Analítica.</p></section>`+extensionReview()+`<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Técnico / Grupo</th><th>Registro</th><th>Periodo</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>${teamRows()}</tbody></table></div>${!teamRecords().length?empty('No hay solicitudes pendientes con estos filtros','Los registros aprobados y rechazados se consultan en Analítica.'):''}</section>`;
}
function teamRecords(){
  const endMonth=new Date(Number(month.slice(0,4)),Number(month.slice(5)),1).toLocaleDateString('sv-SE');
  return [...state.overtime.map(o=>({...o,kind:'ot',filterKind:'OT',a:o.start_at||o.scheduled_start||o.created_at,b:o.end_at||o.scheduled_end||o.created_at})),...state.guards.map(g=>({...g,kind:'guard',filterKind:'GUARD',a:g.start_date,b:g.end_date}))].filter(r=>{
    const u=person(r.user_id);return r.status==='SUBMITTED'&&r.execution!=='RUNNING'&&r.user_id!==me().id&&(state.scope.includes(u?.group_id)||u?.is_lead&&u.manager_id===me().id)&&(!filters.group||u.group_id===filters.group)&&(!filters.person||u.id===filters.person)&&(!filters.kind||r.filterKind===filters.kind)&&(!filters.status||r.status===filters.status||filters.status==='RUNNING'&&r.execution==='RUNNING')&&(filters.period==='ALL'||r.a.slice(0,10)<endMonth&&r.b.slice(0,10)>=month+'-01');
  }).sort((a,b)=>b.created_at.localeCompare(a.created_at));
}
function teamRows(){return teamRecords().map(r=>`<tr><td><strong>${esc(full(person(r.user_id)))}</strong><small>${esc(person(r.user_id)?.employee_id)} · ${esc(person(r.user_id)?.is_lead?'Lead del Manager':group(person(r.user_id)?.group_id)?.name)}</small></td><td><span class="small-label">${r.kind==='ot'?'TIEMPO EXTRA':'GUARDIA'}</span><strong>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</strong><small>${esc(r.description||'')}</small></td><td>${fmtDate(r.a)}<small>${r.kind==='ot'?`${fmtTime(r.a)} — ${fmtTime(r.b)}`:fmtDate(r.b)}</small></td><td>${badge(r.execution==='RUNNING'?'RUNNING':r.execution==='PAUSED'?'PAUSED':r.status)}</td><td><div class="row-actions">${btn('Detalle','record-detail',`${r.kind}:${r.id}`,'link')}${page==='teamTime'&&r.status==='SUBMITTED'&&r.user_id!==me().id&&r.execution!=='RUNNING'?btn('Aprobar','approve',`${r.kind}:${r.id}`,'primary small')+btn('Rechazar','reject',`${r.kind}:${r.id}`,'text-danger'):''}</div></td></tr>`).join('');}
function rulesPage(){
  const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  return heading('COBERTURA OPERATIVA','Reglas de Guardia','Las solicitudes conservan una copia de la regla vigente al momento de crearse.',btn('＋ Crear regla','rule-new','','primary'))+
  `<div class="rules-grid">${state.rules.map(r=>`<article class="panel"><span class="small-label">VIGENTE DESDE ${fmtDate(r.effective_from)}</span><h2>${esc(r.name)}</h2>${r.manager_id===me().id?`<div class="entity-actions">${btn('Editar','rule-edit',r.id,'secondary')}${btn('Eliminar','rule-delete',r.id,'text-danger')}</div>`:''}<div class="rule-segments">${days.map((day,i)=>{const segments=r.segments.filter(s=>Number(s.day)===i);return segments.length?`<div><strong>${day}</strong><span>${segments.map(s=>s.start==='00:00'&&s.end==='00:00'?'24 horas':`${esc(s.start)} — ${esc(s.end)}${s.end<=s.start?' (+1 día)':''}`).join('<br>')}</span></div>`:'';}).join('')}</div></article>`).join('')||empty('Define la cobertura de tu equipo','Agrega segmentos por día para habilitar solicitudes de Guardia.')}</div>`;
}
function timeRecoveryModal(){
 showModal('Respaldo y recuperación de horas',form('time-recovery-preview',`<p class="callout">Descarga el respaldo de ${esc(monthLabel(month))} con tus horas finalizadas. El Excel de aprobados se descarga por separado. Al cambiar de versión conserva también tu base de datos; no necesitas reimportar si tus registros siguen en Pulse.</p><a class="secondary button recovery-download" download href="/api/time-backup.pulse?month=${esc(month)}">${icon('download')} Descargar respaldo Pulse</a><section class="recovery-upload"><h3>Recuperar mis horas</h3><p>Selecciona un respaldo de Pulse o un Excel anterior de Tiempo aprobado. Primero verás los horarios, duplicados y posibles traslapes; todavía no se guarda ninguna hora.</p><label class="field"><span>Archivo .pulse o Excel anterior .xlsx · máximo 6 MB</span><input type="file" name="backup_file" accept=".pulse,.xlsx" required></label><p class="muted">Sólo se recuperan registros de tu Employee ID. No se conservan aprobaciones. La OT incompleta queda por documentar antes de enviarse al Manager.</p></section>`,'','Revisar archivo'),true);
 $('#modal').classList.add('recovery-dialog');
}
function timeRecoveryPreview(report,filename){
 const labels={READY:'Listo para recuperar',DUPLICATE:'Duplicado · se omite',CONFLICT:'Traslape · se omite'};
 showModal('Revisar horas del respaldo',form('time-recovery-confirm',`<p class="callout">${esc(filename)} · ${report.ready} registros disponibles · ${report.duplicates} duplicados · ${report.conflicts} con traslapes. Se omiten los duplicados y conflictos sin modificar tus registros actuales.</p>${report.warnings.map(w=>`<p class="callout recovery-warning">${esc(w)}</p>`).join('')}<p>Las horas recuperadas no sumarán a Claim ni ADP hasta aprobarse. Si falta documentación de OT, deberás completarla primero. Las Guardias recuperadas conservan los intervalos del archivo, sin aplicar automáticamente la regla actual.</p><div class="table-scroll recovery-preview-table"><table><thead><tr><th>Registro</th><th>Periodo</th><th>Horas</th><th>Resultado</th></tr></thead><tbody>${report.rows.map(r=>`<tr><td><strong>${r.kind==='OT'?'OT histórica':'Guardia'}</strong><small>${esc(r.reference||'Sin referencia')}</small></td><td>${fmtDate(r.start_at)} · ${fmtTime(r.start_at)}<small>${fmtDate(r.end_at)} · ${fmtTime(r.end_at)}</small></td><td>${hours(r.minutes)}</td><td>${esc(labels[r.status])}${r.status==='READY'?`<small>${r.needs_documentation?'Falta documentación de OT':'Volverá a aprobación'}</small>`:''}</td></tr>`).join('')}</tbody></table></div><label class="checkbox"><input name="confirm" type="checkbox" required><span>Revisé los horarios y acepto recuperar sólo los registros disponibles, con nueva revisión del Manager.</span></label>`,report.id,'Recuperar horas'),true);
 $('#modal').classList.add('recovery-dialog');if(!report.ready)$('#modal button[type=submit]').disabled=true;
}
function claimCaptureMinutes(minutes){return Math.round((minutes/60+Number.EPSILON)*100)/100*60;}
function claimWeekTotal(week,kind){return Array.from({length:7},(_,i)=>claimCaptureMinutes(claimDayMinutes(claimDateOffset(week,i),kind))).reduce((sum,n)=>sum+n,0);}
function claimWeekRows(week){return ledger.rows.filter(r=>r.date>=week&&r.date<=claimDateOffset(week,6));}
function claimDateOffset(day,n){const date=new Date(day+'T12:00:00Z');date.setUTCDate(date.getUTCDate()+n);return date.toISOString().slice(0,10);}
function claimDayMinutes(day,kind){return ledger.rows.filter(r=>r.date===day&&r.kind===kind).reduce((sum,r)=>sum+r.minutes,0);}
function claimPage(){
 const start=ledger.period_start;if(!start)return heading('GUÍA DE CAPTURA','Claim','Horas decimales aprobadas de sábado a viernes.',monthControl());
 const weeks=[];for(let day=start;day<=ledger.period_end;day=claimDateOffset(day,7))weeks.push(day);
 return heading('LISTO PARA CAPTURAR','Claim','Semanas de sábado a viernes · Stand By y OT en horas decimales.',monthControl()+exportLink('Claim'))+
 `<section class="capture-summary claim-summary"><div><span>Stand By · mes seleccionado</span><strong>${hours(ledger.month_guard_minutes)} <small>h</small></strong></div><div><span>OT · mes seleccionado</span><strong>${hours(ledger.month_ot_minutes)} <small>h</small></strong></div><p>Horas aprobadas, sin duplicados.<br><strong>90 minutos = 1.5 horas decimales.</strong></p></section>`+
 weeks.map(week=>{
 const dates=Array.from({length:7},(_,i)=>claimDateOffset(week,i)),rows=claimWeekRows(week),total=claimWeekTotal(week,'GUARD')+claimWeekTotal(week,'OT');
 return `<section class="panel claim-week" data-claim-week="${week}" data-view-label="${esc(fmtDate(week)+' → '+fmtDate(dates[6]))}"><header class="claim-week-heading"><div><p class="eyebrow">SEMANA CLAIM · SÁBADO A VIERNES</p><h2>${fmtDate(week)} — ${fmtDate(dates[6])}</h2><p>Captura cada concepto en su fila. Los valores están expresados en horas decimales.</p></div><span class="pill">${hours(total)} h · semana completa</span></header><div class="claim-matrix-scroll"><table class="claim-matrix"><thead><tr><th scope="col">Concepto</th><th scope="col">Total</th>${dates.map((day,i)=>`<th scope="col" class="${day.slice(0,7)!==month?'claim-adjacent':''}"><span>${['Sáb','Dom','Lun','Mar','Mié','Jue','Vie'][i]}</span><strong>${day.slice(8,10)}.${day.slice(5,7)}</strong></th>`).join('')}</tr></thead><tbody>${[['GUARD','Stand By','Guardia neta'],['OT','OT','Tiempo extra']].map(([kind,title,description])=>`<tr data-claim-kind="${kind}"><th scope="row"><strong>${title}</strong><small>${description}</small></th><td class="claim-row-total">${hours(claimWeekTotal(week,kind))}</td>${dates.map(day=>`<td data-claim-date="${day}" data-minutes="${claimDayMinutes(day,kind)}" class="${day.slice(0,7)!==month?'claim-adjacent':''}">${hours(claimCaptureMinutes(claimDayMinutes(day,kind)))}</td>`).join('')}</tr>`).join('')}</tbody><tfoot><tr><th scope="row">Total diario</th><td>${hours(total)}</td>${dates.map(day=>`<td>${hours(claimCaptureMinutes(claimDayMinutes(day,'GUARD'))+claimCaptureMinutes(claimDayMinutes(day,'OT')))}</td>`).join('')}</tr></tfoot></table></div><footer class="claim-week-footer"><span>Stand By = Guardia aprobada − OT coincidente. Captura a 2 decimales; los totales suman los valores diarios.</span>${btn('Ver desglose','claim-detail',week,'link')}</footer>${dates.some(day=>day.slice(0,7)!==month)?'<p class="claim-boundary-note">Esta semana incluye días del mes anterior o siguiente. El total semanal los incluye; los indicadores superiores muestran sólo el mes seleccionado.</p>':''}</section>`;
 }).join('');
}
function claimWeekDetail(week){
 const rows=claimWeekRows(week).slice().sort((a,b)=>(a.start_at||a.date+a.start).localeCompare(b.start_at||b.date+b.start));
 const standby=claimWeekTotal(week,'GUARD'),ot=claimWeekTotal(week,'OT');
 showModal('Desglose de Claim',`<div class="form-body claim-detail"><p class="callout">${fmtDate(week)} — ${fmtDate(claimDateOffset(week,6))} · Semana de sábado a viernes. Sólo tiempo aprobado.</p><div class="claim-detail-summary"><span>Stand By <strong>${hours(standby)} h</strong></span><span>OT <strong>${hours(ot)} h</strong></span><span>Total semanal <strong>${hours(standby+ot)} h</strong></span></div><p class="muted">Horas decimales: 90 minutos = 1.5 h. Los totales de captura suman cada día redondeado a dos decimales; el detalle muestra cada tramo y puede diferir por redondeo.</p><div class="table-scroll"><table class="claim-detail-table"><thead><tr><th>Fecha</th><th>Horario</th><th>Concepto</th><th>Referencia</th><th>Horas decimales</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${fmtDate(r.date)}</td><td>${esc(r.start)} — ${esc(r.end)}${r.end==='00:00'?'<small>Fin al día siguiente</small>':''}</td><td><span class="analytics-type-label ${r.kind==='GUARD'?'type-guard':'type-planned'}">${r.kind==='GUARD'?'Stand By':'OT'}</span></td><td>${esc(r.reference||(r.kind==='GUARD'?'Guardia neta':'—'))}</td><td class="numeric"><strong>${hours(r.minutes)}</strong></td></tr>`).join('')}</tbody></table></div>${rows.length?'':empty('Sin horas aprobadas','Esta semana no tiene tiempo aprobado para capturar.')}</div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}</footer>`,true);
 $('#modal').classList.add('claim-detail-dialog');
}
function capturePage(kind){
  if(kind==='claim')return claimPage();
  const grouped=new Map();ledger.rows.forEach(r=>{const day=new Date(r.date+'T12:00:00'),weekday=day.getDay(),offset=kind==='claim'?(weekday+1)%7:weekday;day.setDate(day.getDate()-offset);const week=day.toLocaleDateString('sv-SE');if(!grouped.has(week))grouped.set(week,[]);grouped.get(week).push(r);});
  return heading('CAPTURA MENSUAL',kind==='claim'?'Claim':'ADP',kind==='claim'?'Guía semanal de sábado a viernes. Sólo tiempo aprobado.':'Guía semanal de domingo a sábado. Inicio y duración HH:MM.',monthControl()+exportLink())+
  `<section class="capture-summary"><div><span>Tiempo extra</span><strong>${hours(ledger.ot_minutes)} <small>h</small></strong></div><div><span>Guardia neta</span><strong>${hours(ledger.guard_minutes)} <small>h</small></strong></div><p>Una misma fuente de cálculo.<br><strong>Sin duplicar OT ni traslapes con Guardia.</strong></p></section>`+
  ([...grouped].map(([week,rows])=>`<section class="panel table-panel"><div class="section-heading padded"><div><p class="eyebrow">SEMANA ${kind==='claim'?'CLAIM':'ADP'}</p><h2>Desde ${fmtDate(week)}</h2></div><span class="pill">${hours(rows.reduce((n,r)=>n+r.minutes,0))} h</span></div><div class="table-scroll"><table><thead><tr><th>Fecha</th><th>Tipo</th><th>Referencia</th><th>Inicio</th><th>${kind==='claim'?'Horas decimales':'Duración HH:MM'}</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${fmtDate(r.date)}</td><td>${r.kind==='OT'?'Onsite Overtime':'Stand-by'}</td><td>${esc(r.reference||'—')}</td><td>${r.start}</td><td><strong>${kind==='claim'?hours(r.minutes):hm(r.minutes)}</strong></td></tr>`).join('')}</tbody></table></div></section>`).join('')||empty('Sin tiempo aprobado en este mes','Tus registros aparecerán después de la aprobación de tu Manager o Lead delegado.'));
}
function recoveriesPage(){
  return heading('ACCESO SEGURO','Recuperación de acceso',isAdmin()?'Recuperaciones de Administradores, Managers y Leads. Atiende también Técnicos sin Manager activo.':'Valida la identidad de los Técnicos de tus Grupos antes de emitir un código.')+
  `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Persona</th><th>Solicitud</th><th>Estado</th><th>Vigencia</th><th class="right">Acciones</th></tr></thead><tbody>${state.recoveries.map(r=>{const expired=r.status==='ISSUED'&&new Date(r.expires_at).getTime()<=Date.now()+serverOffset,closed=['USED','CANCELLED'].includes(r.status);return `<tr><td><strong>${esc(full(person(r.user_id)))}</strong><small>${esc(person(r.user_id)?.employee_id||person(r.user_id)?.username)}</small></td><td>${fmtDate(r.created_at)}</td><td>${badge(expired?'EXPIRED':r.status)}</td><td>${r.expires_at?`${fmtDate(r.expires_at)} · ${fmtTime(r.expires_at)}`:'—'}</td><td><div class="row-actions">${!closed?`${r.code_available?btn('Ver código','recovery-view',r.id,'link'):''}${btn(r.status==='ISSUED'?'Regenerar':'Generar código','recovery-issue',r.id,'secondary small')}`:'—'}</div></td></tr>`;}).join('')}</tbody></table></div>${!state.recoveries.length?empty('Todo en orden','No hay solicitudes asignadas a tu responsabilidad.'):''}</section>`;
}
function recoveryCodeModal(result,title,regenerated=false){
  showModal(title,`<div class="form-body"><p>Acceso de <strong>${esc(result.username)}</strong>. Entrega el código únicamente después de validar su identidad.</p><div class="secret-code" data-code-expires="${esc(result.expires_at)}">${esc(result.code)}</div><p class="muted">Vence el ${fmtDate(result.expires_at)} a las ${fmtTime(result.expires_at)}. Sólo puede usarse una vez.${regenerated?' El código anterior ya no funciona.':' Consultarlo no extiende su vigencia.'}</p></div><footer class="dialog-footer">${btn('Listo','close','','primary')}</footer>`);
}

function profilePage(){
  const u=me();
  return heading('TU CUENTA','Mi perfil','Tu información personal y la seguridad de tu acceso.')+
  `<section class="profile-grid"><article class="panel"><div class="profile-person">${identity(u)}<span class="pill">${roles[u.role]}${u.is_lead?' · Lead':''}</span></div><form data-form="profile"><div class="form-body">${field('first','Nombre',u.first,'text','required')}${field('last','Apellido',u.last,'text','required')}${field('email','Correo',u.email,'email','required')}</div><p class="form-error" role="alert"></p><button class="primary">Guardar perfil</button></form></article><article class="panel"><p class="eyebrow">SEGURIDAD</p><h2>Cambiar contraseña</h2><p class="muted">Usa al menos 10 caracteres. Al guardar, volverás a iniciar sesión.</p><form data-form="password"><div class="form-body">${field('current','Contraseña actual','','password','required autocomplete="current-password"')}${field('password','Nueva contraseña','','password','required minlength="10" autocomplete="new-password"')}${field('confirm','Confirmar contraseña','','password','required minlength="10" autocomplete="new-password"')}</div><p class="form-error" role="alert"></p><button class="secondary">Actualizar contraseña</button></form></article></section>`;
}

function entityCode(entity){return entity?.display_code||entity?.code||'';}
function countryLabel(code){if(!code)return 'País sin definir';try{return new Intl.DisplayNames(['es-MX'],{type:'region'}).of(code)||code;}catch{return code;}}
function keyPart(value){const key=String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase().replace(/[^A-Z0-9]+/g,'-').replace(/^-|-$/g,'');return ({'Z-OS':'ZOS','SO-LINUX':'LINUX','SO-UNIX':'UNIX','BD-ORACLE':'ORACLE'})[key]||key;}
function countryOptions(selected){return '<option value="">Selecciona el país</option>'+(state.country_codes||['MX']).map(code=>({code,label:countryLabel(code)})).sort((a,b)=>a.label.localeCompare(b.label,'es-MX')).map(c=>`<option value="${c.code}" ${c.code===selected?'selected':''}>${esc(c.label)} (${c.code})</option>`).join('');}
function accountModal(id=''){
  const a=state.accounts.find(a=>a.id===id)||{},hasGroups=state.groups.some(g=>g.account_id===id),country=a.country_code||(id?'':'MX');
  showModal(id?'Editar Cuenta':'Nueva Cuenta',form('account',`<div class="entity-form-context"><span>${icon('organization')}</span><p>Un país puede tener varias Cuentas. La clave internacional se genera con el país y la clave de la Cuenta.</p></div><div class="form-grid">${select('country_code','País *',countryOptions(country),`required ${hasGroups&&a.country_code?'disabled':''}`)}${field('account_preview','Clave internacional','','text','readonly aria-live="polite"')}</div><div class="entity-form-fields">${field('code','Clave de Cuenta, sin país *',a.base_code||a.code,'text',`required maxlength="24" placeholder="Ej. BNTE" autocomplete="off" ${hasGroups?'readonly':''}`)}${field('name','Nombre de la Cuenta *',a.name,'text','required maxlength="100" placeholder="Ej. Banorte"')}</div>${hasGroups?'<p class="entity-form-note">El país y la clave conservan la identidad de los Grupos. Puedes editar el nombre de la Cuenta.</p>':''}`,id,id?'Guardar cambios':'Crear Cuenta'));
  $('#modal').classList.add('entity-dialog','account-dialog');syncAccountCode();
}
function syncAccountCode(){const f=$('[data-form=account]');if(!f)return;const country=f.elements.country_code.value;let base=keyPart(f.elements.code.value);if(country&&base.startsWith(country+'-'))base=base.slice(country.length+1);f.elements.account_preview.value=country&&base?country+'-'+base:'Selecciona país y clave';}
function serviceLabel(key){return ({'CICS-MQ':'CICS/MQ',DB2:'Db2',ZOS:'z/OS',LINUX:'Linux',UNIX:'Unix',ORACLE:'Oracle',WINDOWS:'Windows','SQL-SERVER':'SQL Server'})[key]||key;}
function groupModal(id='',aid='',mid=''){
  const g=group(id)||{},selected=g.account_id||aid||state.accounts[0]?.id;
  if(!selected)return toast('Crea una Cuenta primero.',true);
  if(isManager()){
   showModal(id?'Editar Grupo':'Nuevo Grupo',form('group',`<input type="hidden" name="account_id" value="${esc(me().account_id)}"><input type="hidden" name="manager_id" value="${esc(me().id)}"><input type="hidden" name="platform_code" value="${esc(g.platform_code||'')}"><p class="admin-dialog-intro">El Grupo pertenecerá a tu equipo y a tu Cuenta. Después podrás agregar o mover Técnicos.</p>${field('service_key','Especialidad *',g.service_key||'','text','required maxlength="50" list="service-catalog" placeholder="Ej. Linux, Oracle o z/OS"')}${field('name','Nombre del Grupo *',g.name,'text','required maxlength="100"')}<datalist id="service-catalog"></datalist><p class="code-preview">Código sugerido: <output name="code_preview"></output>. Se confirma al guardar.</p>`,id,id?'Guardar cambios':'Crear Grupo'));$('#modal').classList.add('admin-dialog');syncGroupCode();if(id)$('#modal .dialog-footer').insertAdjacentHTML('afterbegin',btn('Eliminar Grupo','group-delete',id,'secondary group-removal-trigger'));return;
  }
  showModal(id?'Editar Grupo':'Nuevo Grupo',form('group',`<p class="entity-form-note">Busca una especialidad o escribe una nueva. Se guardará en el catálogo de esta Cuenta.</p><input type="hidden" name="platform_code" value="${esc(g.platform_code||'')}"><div class="form-grid">${select('account_id','Cuenta *',options(state.accounts,selected,x=>entityCode(x)+' · '+x.name),'required')}${select('manager_id','Manager',managerOptions(selected,g.manager_id||mid))}</div><div class="form-grid">${field('service_key','Especialidad *',g.service_key||'','text','required maxlength="50" list="service-catalog" placeholder="Ej. Linux y Oracle" autocomplete="off"')}${field('name','Nombre del Grupo *',g.name,'text','required maxlength="100" placeholder="Ej. Operación distribuida · Producción"')}</div><datalist id="service-catalog"></datalist><p class="entity-form-note code-preview">Código: <output name="code_preview"></output></p>`,id,id?'Guardar cambios':'Crear Grupo'));
  $('#modal').classList.add('entity-dialog','group-dialog');syncGroupCode();
}
async function groupRemovalModal(id){
 const impact=await api('/api/groups/'+id+'/removal-impact'),members=impact.members;
 showModal('Eliminar Grupo',form('group-removal',`<input type="hidden" name="expected" value="${esc(impact.expected)}"><div class="group-removal-summary"><span class="entity-overline">GRUPO A ELIMINAR</span><strong>${esc(impact.group.name)}</strong><small>${esc(entityCode(impact.group))} · ${members.length} Técnicos</small></div><p class="callout">${members.length?'Antes de eliminar el Grupo, mueve a todos sus Técnicos a otro Grupo de tu equipo.':'Este Grupo no tiene Técnicos asignados.'} Se conservan la identidad y el historial de OT, Guardias y traslados.</p>${members.length?`<div class="group-removal-members">${members.map(p=>`<span>${esc(full(p))}<small>${esc(p.employee_id)} · ${esc(statuses[p.status])}</small></span>`).join('')}</div>${select('destination_group_id','Mover Técnicos al Grupo *',options(impact.destinations,'',g=>g.name+' · '+entityCode(g),'Selecciona el Grupo receptor'),'required')}${!impact.destinations.length?'<p class="group-removal-warning">Crea primero otro Grupo en tu equipo para recibir a los Técnicos.</p>':''}`:''}${field('reason','Motivo *','','text','required maxlength="2000"')}<label class="checkbox"><input type="checkbox" name="confirm" required><span>Revisé el destino y confirmo eliminar el Grupo.</span></label>`,id,members.length?'Mover y eliminar Grupo':'Eliminar Grupo'));
 $('#modal').classList.add('admin-dialog','group-removal-dialog');$('#modal .form-instructions')?.remove();
 if(members.length&&!impact.destinations.length)$('#modal [type=submit]').disabled=true;
}
function syncGroupCode(){
 const f=$('[data-form=group]');if(!f)return;
 const a=state.accounts.find(a=>a.id===f.elements.account_id.value),service=keyPart(f.elements.service_key.value),saved=group(f.dataset.id),platform=f.elements.platform_code.value;
 const names=[...new Set([...(state.specialties||[]).filter(x=>x.account_id===a?.id).map(x=>x.name),...Object.values(state.service_catalog||{}).flat().map(serviceLabel)])];
 $('#service-catalog').innerHTML=names.map(name=>`<option value="${esc(name)}"></option>`).join('');
 f.elements.service_key.setCustomValidity(!a?.country_code?'Primero define el país de la Cuenta.':service.length>24?'Resume la especialidad en una clave de hasta 24 caracteres.':'');
 if(!a?.country_code||!service){f.elements.code_preview.value='Se genera al elegir la especialidad';return;}
 if(saved?.standard_code&&saved.account_id===a.id&&saved.service_key===service)f.elements.code_preview.value=saved.standard_code;
 else{const stem=entityCode(a)+(platform?'-'+platform:'')+'-'+service,used=new Set(state.groups.filter(g=>g.id!==f.dataset.id).flatMap(g=>[g.code,g.standard_code]).filter(Boolean));let key=stem,n=1;while(used.has(key))key=stem+'-'+String(++n).padStart(2,'0');f.elements.code_preview.value=key;}
 if(!f.dataset.id&&(!f.elements.name.value||f.elements.name.value===f.dataset.autoName)){const label=f.elements.service_key.value+' · '+a.name;f.elements.name.value=label;f.dataset.autoName=label;}
}
function managerOptions(aid,selected){return options(state.people.filter(p=>p.role==='MANAGER'&&p.status!=='DISABLED'&&p.account_id===aid),selected,full,'Sin Manager');}
function groupCheckboxes(aid,mid){
  const available=state.groups.filter(g=>g.account_id===aid&&(!g.manager_id||g.manager_id===mid));
  return available.map(g=>`<label class="checkbox"><input type="checkbox" name="group_ids" value="${esc(g.id)}" ${g.manager_id===mid&&mid?'checked':''}><span>${esc(entityCode(g))} · ${esc(g.name)}</span></label>`).join('')||'<p class="muted">No hay Grupos disponibles. Puedes asignarlos después.</p>';
}
function personModal(id='',role='USER',context=''){
 const p=person(id)||{},r=p.role||(role==='LEAD'?'USER':role),lead=!!p.is_lead||role==='LEAD',aid=p.account_id||(r==='MANAGER'?context:'')||state.accounts[0]?.id;
 if(r==='MANAGER'&&!state.accounts.length)return toast('Crea una Cuenta primero.',true);
 if(r==='USER'&&!lead&&!state.groups.length)return toast('Crea un Grupo primero.',true);
 if(isManager()){
  const own=state.groups.filter(g=>g.manager_id===me().id);if(!own.length)return toast('Necesitas un Grupo asignado antes de agregar Técnicos.',true);
  if(id&&(p.role!=='USER'||p.is_lead))return toast('Sólo puedes editar a tus Técnicos.',true);
  const fixedGroup=!id&&own.find(g=>g.id===context);
  showModal(id?'Editar Técnico':'Nuevo Técnico',form('person',`<input type="hidden" name="role" value="USER"><p class="admin-dialog-intro">${id?'Actualiza los datos del Técnico. Su historial se conserva.':'Al crear al Técnico recibirás su código de activación.'}</p><div class="admin-fields">${field('first','Nombre *',p.first,'text','required')}${field('last','Apellidos *',p.last,'text','required')}${field('employee_id','Employee ID *',p.employee_id,'text',`required ${id?'readonly':''}`)}${field('email','Correo corporativo *',p.email,'email','required')}</div>${fixedGroup?`<input type="hidden" name="group_id" value="${esc(fixedGroup.id)}"><div class="fixed-group-context"><span>Se agregará a</span><strong>${esc(fixedGroup.name)}</strong><small>${esc(entityCode(fixedGroup))}</small></div>`:select('group_id','Grupo *',options(own,p.group_id||own[0].id,g=>g.name+' · '+entityCode(g)),'required')}${id?field('transfer_reason','Motivo si cambia de Grupo','','text','placeholder="Sólo si cambias el Grupo"'):''}`,id,id?'Guardar cambios':'Crear Técnico'));$('#modal .form-instructions')?.remove();$('#modal').classList.add('admin-dialog');if(id){const f=$('#modal [data-form=person]');f.dataset.originalGroup=p.group_id;f.elements.transfer_reason.closest('.field').hidden=true;f.elements.transfer_reason.disabled=true;}return;
 }
 const available=state.people.filter(x=>x.role==='MANAGER'&&x.status!=='DISABLED'),mid=p.manager_id||(lead?context:'')||available[0]?.id;
 if(r==='MANAGER'||r==='ADMIN'||lead){
  const label=lead?'Lead':r==='MANAGER'?'Manager':'Administrador',title=(id?'Editar ':'Nuevo ')+label;
  const names=`<section class="admin-form-section"><h3>Datos personales</h3><div class="admin-fields">${field('first','Nombre *',p.first,'text','required autocomplete="given-name"')}${field('last','Apellidos *',p.last,'text','required autocomplete="family-name"')}</div></section>`;
  const access=`<section class="admin-form-section"><h3>Identidad de acceso</h3><div class="admin-fields">${r==='ADMIN'?field('username','Usuario *',p.username,'text','required autocomplete="off"'):field('employee_id','Employee ID *',p.employee_id,'text',`required autocomplete="off" ${id?'readonly':''}`)}${field('email','Correo corporativo *',p.email,'email','required autocomplete="email"')}</div></section>`;
  const assignment=r==='MANAGER'?select('account_id','Cuenta *',options(state.accounts,aid,x=>entityCode(x)+' · '+x.name),'required'):lead?`<label id="lead-option" hidden><input type="checkbox" name="is_lead" checked></label><div id="person-manager-field">${select('manager_id','Manager responsable *',options(available,mid,full,'Selecciona un Manager'),'required')}</div><div id="person-group-field" hidden>${select('group_id','Grupo',options(state.groups,'',x=>x.name),'disabled')}</div>`:'';
  const note=id?'El Employee ID conserva la identidad y el historial de esta persona.':'Al crear el acceso recibirás un código para que la persona defina su contraseña.';
  const content=`<input type="hidden" name="role" value="${r}"><p class="admin-dialog-intro">${id?'Actualiza sus datos y revisa su asignación.':'Completa los datos para incorporar a '+label.toLowerCase()+' a la organización.'}</p>${names}${access}${assignment?`<section class="admin-form-section admin-assignment"><h3>Asignación</h3>${assignment}${lead?'<p class="admin-role-note" id="lead-note"></p>':''}</section>`:''}${lead&&id?field('transfer_reason','Motivo del cambio de Manager','','text','placeholder="Sólo si cambias al responsable"'):''}<p class="admin-form-note">${icon('info')}${id&&r==='ADMIN'?'Los cambios no modifican su contraseña ni sus permisos de Administrador.':note}</p>`;
  showModal(title,form('person',content,id,id?'Guardar cambios':'Crear '+label));$('#modal .form-instructions')?.remove();const f=$('#modal [data-form=person]');if(lead&&id)f.dataset.originalManager=p.manager_id;syncLeadOption();return;
 }
 showModal(id?'Editar persona':lead?'Nuevo Lead':r==='MANAGER'?'Nuevo Manager':r==='ADMIN'?'Nuevo administrador':'Nuevo Técnico',form('person',`<input name="role" type="hidden" value="${r}"><div class="form-grid">${field('first','Nombre *',p.first,'text','required')}${field('last','Apellido *',p.last,'text','required')}</div>${r==='ADMIN'?field('username','Usuario *',p.username,'text','required'):field('employee_id','Employee ID *',p.employee_id,'text',`required ${id?'readonly':''}`)}${field('email','Correo *',p.email,'email','required')}${r==='MANAGER'?select('account_id','Cuenta *',options(state.accounts,aid,x=>entityCode(x)+' · '+x.name),'required'):''}${r==='USER'?`<label class="checkbox" id="lead-option" ${lead?'hidden':''}><input name="is_lead" type="checkbox" ${lead?'checked':''} ><span>Lead directo del Manager · sólo OT</span></label><div id="person-manager-field">${select('manager_id','Manager del Lead *',options(available,mid,full,'Selecciona un Manager'))}</div><div id="person-group-field">${select('group_id','Grupo del Técnico *',options(state.groups,p.group_id||context,x=>entityCode(x)+' · '+x.name,'Selecciona un Grupo'))}</div><p class="muted" id="lead-note"></p>${id?field('transfer_reason','Motivo si cambia la asignación','','text','placeholder="Explica el movimiento"'):''}`:''}`,id));syncLeadOption();
}
function syncLeadOption(){
 const f=$('[data-form=person]');if(!f?.elements.group_id||!f.elements.is_lead)return;
 const lead=f.elements.is_lead.checked;
 if(f.dataset.originalManager&&f.elements.transfer_reason){const changed=f.elements.manager_id.value!==f.dataset.originalManager,reason=f.elements.transfer_reason;reason.closest('.field').hidden=!changed;reason.disabled=!changed;reason.required=changed;}
 $('#person-manager-field').hidden=!lead;f.elements.manager_id.disabled=!lead;f.elements.manager_id.required=lead;
 $('#person-group-field').hidden=lead;f.elements.group_id.disabled=lead;f.elements.group_id.required=!lead;
 const holder=state.people.find(p=>p.is_lead&&p.status!=='DISABLED'&&p.manager_id===f.elements.manager_id.value&&p.id!==f.dataset.id);
 f.elements.manager_id.setCustomValidity(lead&&holder?'Este Manager ya tiene un Lead.':'');
 $('#lead-note').textContent=lead?(holder?'Lead actual: '+full(holder)+' · '+holder.employee_id:'Sin Grupo. Puede registrar OT; no Guardias. Sólo aprueba al equipo con delegación activa, nunca su propia OT.'):'El Técnico pertenece a un Grupo y conserva sus registros al trasladarse.';
}
let entityPopup=null;
let entityPopupTrigger=null;
function moreActions(kind,id,label){if(id===me().id)return '';return `<button type="button" class="entity-more" data-action="entity-menu" data-id="${esc(kind+':'+id)}" aria-label="Más opciones de ${esc(label)}" aria-expanded="false" aria-controls="entity-actions-popup">${icon('more')}</button>`;}
function closeEntityMenu(restore=false){
  entityPopup?.remove();entityPopup=null;
  if(entityPopupTrigger?.isConnected){entityPopupTrigger.setAttribute('aria-expanded','false');if(restore)entityPopupTrigger.focus();}
  entityPopupTrigger=null;
}
function openEntityMenu(key,trigger){
  const [kind,id]=key.split(':'),same=entityPopupTrigger===trigger;closeEntityMenu();if(same)return;
  let actions='',title='';
  if(kind==='account'){const a=state.accounts.find(a=>a.id===id);if(!a)return;title=a.name;actions=btn('Editar Cuenta','account-edit',id)+btn('Eliminar Cuenta','account-delete',id,'text-danger');}
  else if(kind==='group'){const g=group(id);if(!g)return;title=g.name;actions=btn('Editar Grupo','group-edit',id)+btn('Transferir Grupo','group-transfer',id)+btn('Eliminar Grupo','group-delete',id,'text-danger');}
  else{const p=person(id);if(!p)return;title=full(p);actions=(p.status==='PENDING_ACTIVATION'&&p.role!=='USER'?btn('Editar datos','person-edit',id):'')+(p.status==='PENDING_ACTIVATION'&&kind!=='manager'?btn('Generar código de activación','activation-code',id):'')+lifecycleActions(p);}
  entityPopup=document.createElement('div');entityPopup.className='entity-popup';entityPopup.id='entity-actions-popup';entityPopup.setAttribute('role','group');entityPopup.setAttribute('aria-label','Acciones de '+title);
  entityPopup.innerHTML=`<p>${esc(title)}</p>${actions}`;const actionIcons={'manager-new':'team','group-new':'plus','account-edit':'organization','account-delete':'close','group-edit':'organization','group-transfer':'arrow','group-delete':'close','person-edit':'profile','person-transfer':'arrow','activation-code':'key','person-offboard':'lock','person-reactivate':'key'};$$('button',entityPopup).forEach(item=>item.insertAdjacentHTML('afterbegin',icon(actionIcons[item.dataset.action]||'info')));document.body.append(entityPopup);entityPopupTrigger=trigger;trigger.setAttribute('aria-expanded','true');
  const anchor=trigger.getBoundingClientRect(),rect=entityPopup.getBoundingClientRect();
  entityPopup.style.left=Math.max(12,Math.min(anchor.right-rect.width,innerWidth-rect.width-12))+'px';
  entityPopup.style.top=Math.max(12,Math.min(anchor.bottom+8,innerHeight-rect.height-12))+'px';
  $('button',entityPopup)?.focus();
}
function lifecycleActions(p){
  if(p.id===me().id)return '';
  if(p.status==='DISABLED'&&p.role==='MANAGER'&&state.groups.some(g=>g.manager_id===p.id))return btn('Regularizar baja','person-offboard',p.id,'text-danger');
  return p.status==='DISABLED'?btn('Reactivar','person-reactivate',p.id,'link'):btn('Dar de baja','person-offboard',p.id,'text-danger');
}
function transferProblem(source,destination){
  if(!source||source.role!=='USER'||source.status==='DISABLED')return 'Este Técnico no tiene un acceso activo para transferir.';
  if(state.timers.some(t=>t.user_id===source.id))return 'Detén el Timer del Técnico antes de cambiarlo de Grupo.';
  if(!destination||person(destination.manager_id)?.status!=='ACTIVE')return 'El Grupo de destino necesita un Manager activo.';
  if(source.group_id===destination.id)return 'El Técnico ya pertenece a este Grupo.';
  if(source.is_lead&&state.people.some(p=>p.id!==source.id&&p.is_lead&&p.status!=='DISABLED'&&group(p.group_id)?.manager_id===destination.manager_id))return 'El Manager de destino ya tiene un Lead. Retira una designación antes de trasladarlo.';
  return '';
}
function transferDestinationCard(g){return g?`<span class="transfer-route-label">DESTINO</span><button type="button" class="transfer-change" data-action="transfer-change-target">Cambiar Grupo</button><strong>${esc(g.name)}</strong><small>${esc(full(person(g.manager_id)))} · ${esc(state.accounts.find(a=>a.id===g.account_id)?.name||'')}</small>`:'<span class="transfer-route-label">DESTINO</span><strong>Selecciona un Grupo</strong><small>Verás aquí a su Manager responsable.</small>';}
function technicianDetailsModal(id){
 const p=person(id),g=group(p?.group_id);if(!isManager()||!p||p.is_lead||g?.manager_id!==me().id)return;
 const a=state.accounts.find(a=>a.id===g.account_id),pending=(state.manager_transfers||[]).find(r=>r.user_id===id&&r.status==='SUBMITTED'),timer=state.timers.some(t=>t.user_id===id);
 showModal('Ficha del Técnico',`<div class="form-body technician-sheet"><div class="technician-sheet-identity">${identity(p)}${badge(p.status)}</div><dl class="technician-facts"><div><dt>Correo corporativo</dt><dd>${esc(p.email)}</dd></div><div><dt>Grupo / especialidad</dt><dd>${esc(g.name)}<small>${esc(entityCode(g))}</small></dd></div><div><dt>Cuenta</dt><dd>${esc(a?.name||'Sin Cuenta')} · ${esc(entityCode(a))}</dd></div><div><dt>Actividad</dt><dd>${timer?'Timer en curso':'Sin Timer activo'}${pending?' · Traslado pendiente de aceptación':''}</dd></div></dl><p class="admin-form-note">${icon('drag')}Para cambiar de Grupo, arrastra su tarjeta en el tablero. También puedes usar Mover para elegir Grupo, Manager o Cuenta.</p><div class="technician-sheet-options">${btn('Editar Técnico','person-edit',id,'primary')}${btn('Mover','team-move',id,'secondary')}${pending?btn('Ver traslado pendiente','manager-transfers',id,'link'):''}${p.status==='PENDING_ACTIVATION'?btn('Generar código de activación','activation-code',id,'secondary'):''}</div></div><footer class="dialog-footer">${p.status!=='DISABLED'?btn('Dar de baja','person-offboard',id,'secondary technician-offboard'):''}${btn('Cerrar','close','','secondary')}</footer>`);$('#modal').classList.add('admin-dialog','technician-sheet-dialog');
}
function managerTransferModal(id){technicianMoveModal(id,'external');}
function managerTransfersModal(){
 const requests=[...(state.manager_transfers||[])].sort((a,b)=>b.created_at.localeCompare(a.created_at));
 showModal('Traslados de Técnicos',`<div class="form-body"><p class="callout">Recibidos: acepta eligiendo un Grupo propio o rechaza con motivo. Enviados: consulta el estado o cancela mientras estén pendientes.</p><div class="record-list">${requests.map(r=>`<article class="record-card"><div class="grow"><strong>${esc(r.user_name)} · ${esc(r.employee_id)}</strong><p>${r.target_manager_id===me().id?'Recibido de '+esc(r.source_name):'Enviado a '+esc(r.target_name)}</p><p>${esc(r.reason)}</p>${badge(r.status)}${r.decision_reason?`<p>Resolución: ${esc(r.decision_reason)}</p>`:''}</div>${r.status==='SUBMITTED'?`<div class="entity-actions">${r.target_manager_id===me().id?btn('Aceptar','manager-transfer-accept',r.id,'primary')+btn('Rechazar','manager-transfer-reject',r.id,'secondary'):btn('Cancelar traslado','manager-transfer-cancel',r.id,'secondary')}</div>`:''}</article>`).join('')||empty('Sin traslados','Aquí aparecerán los traslados enviados y recibidos.')}</div></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}</footer>`);$('#modal').classList.add('admin-dialog','team-requests-dialog');PulseLayout.dialog();
}
function managerTransferDecision(id,decision){
 const r=(state.manager_transfers||[]).find(r=>r.id===id);if(!r)return;if(decision==='APPROVED'&&!state.groups.some(g=>g.manager_id===me().id))return toast('Crea un Grupo de tu equipo antes de aceptar el traslado.',true);
 showModal(decision==='APPROVED'?'Aceptar traslado':decision==='REJECTED'?'Rechazar traslado':'Cancelar traslado',form('manager-transfer-decision',`<input type="hidden" name="decision" value="${decision}"><p class="callout">${esc(r.user_name)} · ${esc(r.employee_id)}. ${decision==='APPROVED'?'Al confirmar, el Técnico y su historial pasan a tu equipo.':'Indica el motivo; el Técnico conserva su asignación actual.'}</p>${decision==='APPROVED'?select('group_id','Grupo receptor *',options(state.groups.filter(g=>g.manager_id===me().id),'',g=>g.name,'Selecciona uno de tus Grupos'),'required'):''}${field('reason','Motivo de la resolución *','','text','required')}`,id,decision==='APPROVED'?'Aceptar y trasladar':'Confirmar'));$('#modal').classList.add('admin-dialog');
}
function teamMoveModal(id,destinationId=''){technicianMoveModal(id,'group',destinationId);}
function technicianMoveModal(id,mode='group',destinationId=''){
 const p=person(id),source=group(p?.group_id);if(!isManager()||!p||p.is_lead||source?.manager_id!==me().id)return;
 const groups=state.groups.filter(g=>g.manager_id===me().id&&g.id!==p.group_id),managers=state.manager_directory||[];
 if(!groups.length&&!managers.length)return toast('No hay destinos disponibles para este Técnico.',true);
 const selectedMode=mode==='group'&&!groups.length?'external':mode==='external'&&!managers.length?'group':mode;
 const accounts=[...new Map(managers.map(m=>[m.account_id,{id:m.account_id,name:m.account_name,code:m.account_code}])).values()].sort((a,b)=>a.name.localeCompare(b.name,'es-MX'));
 showModal('Mover Técnico',form('team-relocate',`<input type="hidden" name="expected_group_id" value="${esc(p.group_id)}"><input type="hidden" name="mode" value="${selectedMode}"><div class="request-person move-subject">${identity(p)}<div class="move-origin"><span>ORIGEN</span><strong>${esc(source.name)}</strong><small>${esc(entityCode(state.accounts.find(a=>a.id===source.account_id)))}</small></div></div><div class="move-mode-tabs" role="group" aria-label="Tipo de movimiento"><button type="button" data-action="move-mode" data-id="group" ${!groups.length?'disabled':''}>${icon('team')}Entre mis Grupos</button><button type="button" data-action="move-mode" data-id="external" ${!managers.length?'disabled':''}>${icon('organization')}Otro Manager / Cuenta</button></div><div class="move-group-fields">${select('group_id','Grupo de destino *',options(groups,destinationId||groups[0]?.id,g=>g.name+' · '+entityCode(g)),'required')}</div><div class="move-external-fields"><div class="move-destination-filters">${select('move_account','Filtrar por Cuenta',options(accounts,'',a=>a.code+' · '+a.name,'Todas las Cuentas'))}<label class="field"><span>Buscar Manager</span><input id="move-manager-search" name="manager_query" type="search" autocomplete="off" placeholder="Nombre o Employee ID"></label></div>${select('target_manager_id','Manager de destino *',options(managers,'',m=>full(m)+' · '+m.employee_id+' · '+m.account_code+' · '+m.account_name,'Selecciona un Manager'),'required')}<p id="move-manager-results" class="move-results" aria-live="polite"></p></div><label class="field"><span>Motivo del movimiento *</span><input name="reason" required maxlength="2000" placeholder="Describe el motivo del cambio"></label><div id="move-route-summary" class="move-summary" aria-live="polite"></div>`,id,selectedMode==='group'?'Confirmar movimiento':'Enviar al Manager'));$('#modal').classList.add('admin-dialog','team-transfer-dialog','team-relocate-dialog');syncTechnicianMove(selectedMode);filterMoveManagers();
}
function syncTechnicianMove(mode){
 const f=$('[data-form=team-relocate]');if(!f)return;f.elements.mode.value=mode;
 $('.move-group-fields',f).hidden=mode!=='group';$('.move-external-fields',f).hidden=mode!=='external';
 f.elements.group_id.disabled=mode!=='group';f.elements.group_id.required=mode==='group';
 ['target_manager_id','move_account','manager_query'].forEach(name=>f.elements[name].disabled=mode!=='external');f.elements.target_manager_id.required=mode==='external';
 $$('[data-action=move-mode]',f).forEach(b=>{b.classList.toggle('selected',b.dataset.id===mode);b.setAttribute('aria-pressed',String(b.dataset.id===mode));});
 $('[type=submit]',f).textContent=mode==='group'?'Confirmar movimiento':'Enviar al Manager';updateMoveSummary();requestAnimationFrame(()=>PulseLayout.dialog());
}
function filterMoveManagers(){
 const f=$('[data-form=team-relocate]');if(!f)return;
 const current=f.elements.target_manager_id.value,query=normalizeGroupSearch(f.elements.manager_query.value),account=f.elements.move_account.value;
 const managers=(state.manager_directory||[]).filter(m=>(!account||m.account_id===account)&&normalizeGroupSearch(full(m)+' '+m.employee_id+' '+m.account_name+' '+m.account_code).includes(query));
 f.elements.target_manager_id.innerHTML=options(managers,managers.some(m=>m.id===current)?current:'',m=>full(m)+' · '+m.employee_id+' · '+m.account_code+' · '+m.account_name,managers.length?'Selecciona un Manager':'Sin Managers con estos filtros');
 $('#move-manager-results').textContent=managers.length?(managers.length===1?'1 Manager encontrado':managers.length+' Managers encontrados'):'Sin coincidencias. Cambia la Cuenta o la búsqueda.';updateMoveSummary();
}
function updateMoveSummary(){
 const f=$('[data-form=team-relocate]');if(!f)return;
 const external=f.elements.mode.value==='external',manager=(state.manager_directory||[]).find(m=>m.id===f.elements.target_manager_id.value),destination=group(f.elements.group_id.value),pending=(state.manager_transfers||[]).some(r=>r.user_id===f.dataset.id&&r.status==='SUBMITTED');
 $('#move-route-summary').textContent=external?(manager?'Destino: '+manager.account_code+' · '+manager.account_name+' → '+full(manager)+'. El Manager debe aceptar y elegir el Grupo receptor.':'Selecciona Cuenta y Manager. El Técnico permanece en origen hasta que el destino acepte.'):(destination?'Destino: '+destination.name+'. Se aplica directamente al confirmar.':'Selecciona otro Grupo de tu equipo.');
 if(!external&&pending)$('#move-route-summary').textContent+=' El traslado pendiente quedará cancelado.';
}
function requestTransferModal(id,destinationId=''){teamMoveModal(id,destinationId);}
function transferRequestsModal(){if(isManager())managerTransfersModal();else toast('Los traslados entre equipos los resuelven los Managers.',true);}
function transferModal(id,wholeGroup=false,destinationId=''){
  const source=wholeGroup?group(id):person(id);
  if(!wholeGroup){
    if(state.timers.some(t=>t.user_id===id))return toast('Detén el Timer del Técnico antes de cambiarlo de Grupo.',true);
    if(source?.status==='DISABLED')return toast('Reactiva al Técnico antes de transferirlo.',true);
    if(destinationId&&transferProblem(source,group(destinationId)))return toast(transferProblem(source,group(destinationId)),true);
  }
  const choices=wholeGroup?state.people.filter(p=>p.role==='MANAGER'&&p.status==='ACTIVE'&&p.account_id===source.account_id&&p.id!==source.manager_id):state.groups.filter(g=>!transferProblem(source,g));
  if(!choices.length)return toast(wholeGroup?'Crea y activa un Manager de destino en esta Cuenta.':'No hay Grupos de destino disponibles. Revisa la asignación de Manager y Lead.',true);
  if(wholeGroup){showModal('Transferir Grupo',form('group-transfer',`<p class="callout">${esc(source.name)} · El equipo conserva su historial y permanece activo.</p>${select('manager_id','Manager de destino *',options(choices,'',full,'Selecciona un destino'),'required')}${field('transfer_reason','Motivo del movimiento *','','text','required')}`,id,'Confirmar transferencia'));return;}
  const origin=group(source.group_id);
  showModal('Mover Técnico',form('transfer',`<input type="hidden" name="expected_group_id" value="${esc(source.group_id)}"><div class="transfer-person">${identity(source)}<span class="pill">${source.is_lead?'Técnico · Lead':'Técnico'}</span></div><div class="transfer-route"><div><span class="transfer-route-label">ORIGEN</span><strong>${esc(origin?.name)}</strong><small>${esc(full(person(origin?.manager_id)))}</small></div><span class="transfer-route-arrow">${icon('arrow')}</span><div id="transfer-destination">${transferDestinationCard(group(destinationId))}</div></div><div class="transfer-target-selector" ${destinationId?'hidden':''}>${select('group_id','Grupo de destino *',options(choices,destinationId,g=>`${g.code} · ${g.name} — ${full(person(g.manager_id))}`,'Selecciona un Grupo'),'required')}</div>${field('transfer_reason','Motivo del traslado *','','text','required placeholder="Describe brevemente el motivo"')}<div class="quick-reasons"><span>Motivos frecuentes</span><button type="button" data-action="transfer-reason" data-id="Reorganización del equipo">Reorganización</button><button type="button" data-action="transfer-reason" data-id="Cobertura operativa">Cobertura operativa</button></div><p class="transfer-footnote">Conserva identidad e historial. Las sesiones actuales se cerrarán para aplicar los permisos del nuevo Grupo.</p>`,id,'Confirmar traslado'));
  $('#modal').classList.add('transfer-dialog');
}
const normalizeGroupSearch=s=>String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().trim();
let organizationOverview=false;
let organizer=null,organizerDrag=null;
function organizerOpen(sourceId=''){
 if(!isAdmin())return;
 const choices=state.groups.filter(g=>person(g.manager_id)?.status==='ACTIVE');
 if(choices.length<2)return toast('Se necesitan al menos dos Grupos con Manager activo.',true);
 const source=choices.find(g=>g.id===sourceId)||choices[0],destination=choices.find(g=>g.id!==source.id);
 organizer={source:source.id,destination:destination.id,moves:{},query:'',reason:'',pages:{source:0,destination:0},size:4,review:false,reviewPage:0};
 showModal('Organizar Técnicos',`<div id="organizer-root"></div>`,true);$('#modal').classList.add('organizer-dialog');paintOrganizer();
}
function boardPeople(gid){return state.people.filter(p=>p.role==='USER'&&!p.is_lead&&p.status!=='DISABLED'&&(organizer.moves[p.id]||p.group_id)===gid&&normalizeGroupSearch(full(p)+' '+p.employee_id).includes(normalizeGroupSearch(organizer.query))).sort((a,b)=>full(a).localeCompare(full(b),'es-MX'));}
function organizerPager(total,index,action,id=''){
 const count=Math.max(1,Math.ceil(total/organizer.size));index=Math.min(index,count-1);
 return `<nav class="organizer-pages"><button type="button" class="secondary small" data-action="${action}" data-id="${id}:${index-1}" ${index===0?'disabled':''}>←</button><span>${total?index+1:0} de ${total?count:0}</span><button type="button" class="secondary small" data-action="${action}" data-id="${id}:${index+1}" ${index>=count-1?'disabled':''}>→</button></nav>`;
}
function organizerLane(side){
 const gid=organizer[side],g=group(gid),people=boardPeople(gid),count=Math.max(1,Math.ceil(people.length/organizer.size));organizer.pages[side]=Math.min(organizer.pages[side],count-1);
 const list=people.slice(organizer.pages[side]*organizer.size,(organizer.pages[side]+1)*organizer.size);
 const groups=state.groups.filter(g=>person(g.manager_id)?.status==='ACTIVE');
 return `<section class="organizer-column" data-board-lane="${side}" data-board-group="${esc(gid)}"><label class="field"><span>${side==='source'?'ORIGEN':'DESTINO'}</span><select name="board-${side}" aria-label="Grupo ${side==='source'?'origen':'destino'}">${options(groups,gid,x=>state.accounts.find(a=>a.id===x.account_id)?.name+' · '+x.name+' · '+full(person(x.manager_id)))}</select></label><div class="organizer-lane-context"><strong>${esc(full(person(g?.manager_id)))}</strong><span>${people.length} Técnicos</span></div><div class="organizer-tech-list">${list.map(p=>{const blocked=state.timers.some(t=>t.user_id===p.id),changed=!!organizer.moves[p.id];return `<article class="organizer-tech ${changed?'staged':''}" data-board-person="${esc(p.id)}" draggable="${!blocked}"><span class="organizer-grip" aria-hidden="true">${icon('drag')}</span><div><strong>${esc(full(p))}</strong><small>${esc(p.employee_id)}${blocked?' · Timer activo':changed?' · Cambio pendiente':''}</small></div><button type="button" class="icon-btn" data-action="organizer-move" data-id="${esc(p.id+':'+(side==='source'?organizer.destination:organizer.source))}" aria-label="Mover a ${esc(full(p))} al otro Grupo" ${blocked?'disabled':''}>${side==='source'?'→':'←'}</button></article>`;}).join('')||'<div class="organizer-empty">'+icon('team')+'<span>Sin Técnicos con este filtro</span><small>Arrastra aquí para asignar</small></div>'}</div>${organizerPager(people.length,organizer.pages[side],'organizer-page',side)}</section>`;
}
function paintOrganizer(){
 if(!organizer||!$('#organizer-root'))return;
 const moves=Object.entries(organizer.moves),focus=document.activeElement?.id,caret=document.activeElement?.selectionStart;
 let body;
 if(organizer.review){const count=Math.max(1,Math.ceil(moves.length/organizer.size));organizer.reviewPage=Math.min(organizer.reviewPage,count-1);body=`<p class="organizer-notice">Los registros de OT, Guardias e historial siguen con cada Técnico. Cambiar de responsable actualiza permisos y cierra sus sesiones.</p><div class="organizer-review-list">${moves.slice(organizer.reviewPage*organizer.size,(organizer.reviewPage+1)*organizer.size).map(([id,gid])=>{const p=person(id);return `<article><div><strong>${esc(full(p))}</strong><small>${esc(p.employee_id)}</small></div><div><span>${esc(group(p.group_id)?.name)} → <strong>${esc(group(gid)?.name)}</strong></span><small>${esc(full(person(group(gid)?.manager_id)))}</small></div>${btn('Deshacer','organizer-undo',id,'link')}</article>`;}).join('')}</div>${organizerPager(moves.length,organizer.reviewPage,'organizer-review-page')}`;}
 else body=`<div class="organizer-toolbar"><p>Arrastra Técnicos entre Grupos. Los cambios se aplican sólo al confirmar.</p><label class="search"><input id="organizer-search" value="${esc(organizer.query)}" placeholder="Buscar Técnico o Employee ID" aria-label="Buscar Técnico"></label></div><div class="organizer-lanes">${organizerLane('source')}${organizerLane('destination')}</div>`;
 $('#organizer-root').innerHTML=`<div class="organizer-workspace">${body}<div class="organizer-bottom"><span><strong>${moves.length}</strong> cambios pendientes · Lead fuera de Grupos</span>${moves.length?btn('Deshacer todos','organizer-reset','','link'):''}${organizer.review?`<label class="field"><span>Motivo de los movimientos *</span><input id="organizer-reason" value="${esc(organizer.reason)}" maxlength="500" placeholder="Ej. Reorganización de especialidades" required></label>`:''}<p class="organizer-error" role="alert"></p></div></div><footer class="dialog-footer">${btn('Cancelar','close','','secondary')}${organizer.review?btn('Volver al tablero','organizer-back','','secondary')+btn('Confirmar movimientos','organizer-save','','primary'):btn('Revisar '+moves.length+' cambios','organizer-review','','primary',moves.length?'':'disabled')}</footer>`;
 if(focus==='organizer-search'){$('#organizer-search')?.focus({preventScroll:true});if(caret!=null)$('#organizer-search')?.setSelectionRange(caret,caret);}
 requestAnimationFrame(()=>{if(!organizer)return;const lane=$(organizer.review?'.organizer-review-list':'.organizer-tech-list');if(!lane)return;const row=organizer.review?(innerWidth<=700?93:72):(innerWidth<=700?66:58),size=Math.max(1,Math.min(6,Math.floor(lane.clientHeight/row)));if(size!==organizer.size){organizer.size=size;organizer.pages={source:0,destination:0};organizer.reviewPage=0;paintOrganizer();}});
}
function stageOrganizerMove(id,gid){
 if(!organizer)return;const p=person(id),g=group(gid);if(!p||p.is_lead||p.status==='DISABLED')return;
 if(state.timers.some(t=>t.user_id===id))return toast('Detén el Timer antes de mover al Técnico.',true);
 if(!g||person(g.manager_id)?.status!=='ACTIVE')return toast('El destino necesita un Manager activo.',true);
 if(gid===p.group_id)delete organizer.moves[id];else organizer.moves[id]=gid;
 paintOrganizer();
}
function endTechnicianDrag(){draggedTechnician=null;document.body.classList.remove('is-dragging-technician');$('#drag-destinations')?.remove();$$('.drop-ready,.drop-invalid,.is-drag-source').forEach(node=>node.classList.remove('drop-ready','drop-invalid','is-drag-source'));}
function startTechnicianDrag(event){
  const card=event.target.closest('.technician[draggable=true]');if(!card||!isAdmin()||busy||$('#modal').open)return;
  const source=person(card.dataset.person);draggedTechnician=source.id;closeEntityMenu();
  event.dataTransfer.setData('application/x-pulse-technician',source.id);event.dataTransfer.setData('text/plain',source.employee_id);event.dataTransfer.effectAllowed='move';
  card.classList.add('is-drag-source');document.body.classList.add('is-dragging-technician');
  const accountId=group(source.group_id)?.account_id,targets=state.groups.filter(g=>g.account_id===accountId&&!transferProblem(source,g)).slice(0,4);
  const tray=document.createElement('aside');tray.id='drag-destinations';tray.className='drag-destinations';tray.setAttribute('aria-label','Destinos para el Técnico');
  tray.innerHTML=`<p><strong>Mover a ${esc(full(source))}</strong><span>Suelta en un Grupo o elige otro destino</span></p><div>${targets.map(g=>`<div class="drag-destination" data-drop-group="${esc(g.id)}"><strong>${esc(g.name)}</strong><small>${esc(full(person(g.manager_id)))}</small></div>`).join('')}<div class="drag-destination drag-destination-picker" data-drop-picker>Elegir otro Grupo ${icon('arrow')}</div></div>`;document.body.append(tray);
}
async function lifecycleModal(id){
  const impact=await api(`/api/admin/people/${id}/impact`),p=impact.person;
  const groups=impact.groups.map(g=>`<fieldset><legend>${esc(entityCode(g))} · ${esc(g.name)} · ${g.members.length} Técnicos</legend>${select('transfer:'+g.id,'Manager de destino *',options(impact.candidates.filter(m=>m.account_id===g.account_id),'',full,'Selecciona un Manager activo'),'required')}</fieldset>`).join('');
  const documents=impact.documents.map((o,i)=>`<fieldset data-offboard-document="${esc(o.id)}"><legend>Documentar OT pendiente ${i+1}</legend>${['reference','description','justification','impact','in_lieu'].map((k,j)=>`<label class="field"><span>${['Referencia completa CHG / INC','Descripción','Justificación','Impacto','Por qué no aplica tiempo compensatorio'][j]} *</span><input data-key="${k}" value="${esc(o[k]||'')}" required></label>`).join('')}</fieldset>`).join('');
  showModal('Revisar baja · '+esc(full(p)),form('offboard',`<input type="hidden" name="expected" value="${esc(impact.expected)}"><p class="callout">Se conservan la identidad y todos los registros. Las solicitudes pendientes pasan al responsable del Grupo. Se cancelan ${impact.scheduled.length} OT sin ejecutar y se limita o cancela la cobertura de ${impact.guards.length} Guardias.</p>${impact.direct_leads?.length?select('lead_manager_id','Manager de destino para el Lead *',options(impact.candidates.filter(m=>m.account_id===p.account_id),'',full,'Selecciona el reemplazo'),'required'):''}${groups?`${select('bulk_destination','Asignar todos los Grupos a',options(impact.candidates.filter(m=>m.account_id===p.account_id),'',full,'Elige un destino común (opcional)'))}<div class="offboard-transfers">${groups}</div><aside class="offboard-replacement"><div><strong>¿Necesitas un reemplazo nuevo?</strong><p>Créalo y activa su acceso antes del traspaso. El Manager actual sigue activo hasta confirmar.</p></div>${btn('Crear Manager','manager-new',p.account_id,'secondary')}</aside>`:''}${impact.timers.length?'<label class="checkbox"><input name="stop_timers" type="checkbox" required><span>Autorizar el cierre del Timer activo a la hora de confirmar la baja.</span></label>':''}${documents}${field('reason','Motivo de la baja *','','text','required')}<label class="checkbox"><input name="confirm" type="checkbox" required><span>Revisé el impacto y las transferencias. Confirmo retirar el acceso y las delegaciones.</span></label><p class="muted offboard-review-note">Si cambian los datos, vuelve a abrir la revisión.</p>`,id,'Confirmar baja'),p.role==='MANAGER');
}
function localInput(value){
  if(!value)return '';
  const parts=new Intl.DateTimeFormat('sv-SE',{timeZone:state?.timezone||'America/Mexico_City',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(value));
  const v=t=>parts.find(p=>p.type===t)?.value;return `${v('year')}-${v('month')}-${v('day')}T${v('hour')}:${v('minute')}`;
}
function otModal(id=''){
 const o=state.overtime.find(o=>o.id===id)||{},actual=!!id&&o.execution==='COMPLETED',parts=o.actual_segments||[];
 const period=`<div class="form-grid">${field(actual?'actual_start':'scheduled_start',actual?'Inicio trabajado *':'Inicio *',localInput(actual?o.start_at:o.scheduled_start),'datetime-local','required')}${field(actual?'actual_end':'scheduled_end',actual?'Fin trabajado *':'Fin *',localInput(actual?o.end_at:o.scheduled_end),'datetime-local','required')}</div>`;
 const segments=actual&&o.capture_type==='PLANNED'&&parts.length>1?`<details class="ot-correction-segments"><summary>Revisar horarios por tramo (${parts.length}) · las pausas no suman tiempo</summary>${parts.map((p,i)=>`<div class="form-grid" data-correction-segment><label class="field"><span>Tramo ${i+1} · inicio *</span><input type="datetime-local" data-segment-start value="${esc(localInput(p.start_at))}" required></label><label class="field"><span>Tramo ${i+1} · fin *</span><input type="datetime-local" data-segment-end value="${esc(localInput(p.end_at))}" required></label></div>`).join('')}</details>`:'';
 showModal(id?(o.status==='DOCUMENTATION'?'Documentar OT':'Editar y reenviar OT'):'Registrar tiempo extra',form('ot',`${id?`<input type="hidden" name="expected_revision" value="${o.revision}">`:''}${period}${actual?'<p class="callout ot-time-guidance">Puedes corregir el horario trabajado. El cambio requiere un motivo y nueva aprobación; Claim y ADP se recalculan al autorizarlo.</p>':'<p id="ot-type-preview" class="callout ot-type-preview" role="status"></p>'}${segments}${actual?field('time_change_reason','Motivo del cambio de horario *','','text','maxlength="2000"'):''}${field('reference','Referencia completa CHG / INC *',o.reference,'text','required placeholder="CHG1234567"')}<label class="field"><span>Descripción *</span><textarea name="description" required rows="2">${esc(o.description)}</textarea></label><label class="field"><span>Justificación *</span><textarea name="justification" required rows="2">${esc(o.justification)}</textarea></label><label class="field"><span>Impacto si no se aprueba *</span><textarea name="impact" required rows="2">${esc(o.impact)}</textarea></label><label class="field"><span>Por qué no aplica tiempo compensatorio *</span><textarea name="in_lieu" required rows="2">${esc(o.in_lieu)}</textarea></label>`,id,'Enviar a aprobación'));
 const f=$('#modal [data-form=ot]');
 if(actual){f.dataset.originalActualStart=f.elements.actual_start.value;f.dataset.originalActualEnd=f.elements.actual_end.value;f.dataset.originalStartIso=o.start_at;f.dataset.originalEndIso=o.end_at;$$('[data-correction-segment]',f).forEach((node,i)=>{for(const [selector,key] of [['[data-segment-start]','start_at'],['[data-segment-end]','end_at']]){const input=$(selector,node);input.dataset.originalValue=input.value;input.dataset.originalAt=parts[i][key];}});syncActualOtCorrection();}else syncOtType();
}
function syncActualOtCorrection(target){
 const f=$('#modal [data-form=ot]');if(!f?.elements.actual_start)return;
 const nodes=$$('[data-correction-segment]',f),a=f.elements.actual_start,b=f.elements.actual_end;
 if(nodes.length&&target===a)$('[data-segment-start]',nodes[0]).value=a.value;
 if(nodes.length&&target===b)$('[data-segment-end]',nodes.at(-1)).value=b.value;
 if(nodes.length&&target?.hasAttribute('data-segment-start'))a.value=$('[data-segment-start]',nodes[0]).value;
 if(nodes.length&&target?.hasAttribute('data-segment-end'))b.value=$('[data-segment-end]',nodes.at(-1)).value;
 const changed=a.value!==f.dataset.originalActualStart||b.value!==f.dataset.originalActualEnd||$$('[data-correction-segment] input',f).some(input=>input.value!==input.dataset.originalValue);
 f.dataset.timeChanged=String(changed);const reason=f.elements.time_change_reason;reason.required=changed;reason.disabled=!changed;reason.closest('.field').hidden=!changed;
 b.setCustomValidity(changed&&b.value<=a.value?'El fin debe ser posterior al inicio.':'');
}
function syncOtType(){
  const f=$('[data-form=ot]'),preview=$('#ot-type-preview');if(!f||!preview)return;
  const a=f.elements.scheduled_start,b=f.elements.scheduled_end,current=localInput(new Date(Date.now()+serverOffset).toISOString());
  if(!a||!b)return;a.setCustomValidity('');b.setCustomValidity('');
  if(!a.value||!b.value){preview.textContent='Elige inicio y fin. El sistema identificará automáticamente si la OT es programada o histórica.';return;}
  const start=a.value,end=b.value;
  const message=end<=start?'El fin debe ser posterior al inicio.':end<=current?'Captura histórica excepcional · El periodo ya terminó. Evita acumular registros: programa la OT y usa su Timer; ante una emergencia, inicia el Timer al atenderla. Explica en la justificación por qué se registra después y por qué no se utilizó el Timer. Requiere revisión del Manager.':start>current?'OT programada · La actividad aún no comienza. Necesita aprobación antes de iniciar tu Timer.':'El periodo está en curso. Si es una actividad no programada, inicia el Timer de emergencia; evita esperar al final para capturarla como histórica.';
  preview.textContent=message;const historical=end>start&&end<=current;preview.classList.toggle('historical-guidance',historical);const justification=f.elements.justification;if(justification){const label=justification.closest('label')?.querySelector('span');if(label)label.textContent=historical?'Justificación de la actividad y de la captura posterior *':'Justificación *';justification.placeholder=historical?'Explica la actividad, por qué se captura después y por qué no se utilizó el Timer.':'';}const invalid=end<=start||start<=current&&end>current;preview.classList.toggle('date-warning',invalid);if(invalid)b.setCustomValidity(message);
}
async function guardRevisionModal(id){
 const review=await api('/api/guards/'+id+'/revision'),g=review.guard;
 if(!review.rules.length)return toast('Tu Manager debe crear una regla para que puedas actualizar esta Guardia.',true);
 const selected=review.rules.find(r=>r.id===g.rule_snapshot.id)?.id||review.rules[0].id;
 const ruleOptions=review.rules.map(r=>`<option value="${esc(r.id)}" data-token="${esc(r.token)}" ${r.id===selected?'selected':''}>${esc(r.name)} · desde ${fmtDate(r.effective_from)}</option>`).join('');
 showModal('Revisar Guardia',form('guard-revision',`<input type="hidden" name="expected" value="${esc(review.expected)}"><input type="hidden" name="rule_token"><p class="callout">Revisa la regla y el periodo. Al confirmar, esta misma solicitud vuelve a aprobación; sus horas dejan de sumar al aprobado hasta que el Manager la autorice nuevamente.</p>${select('rule_id','Regla actual *',ruleOptions,'required')}<div class="form-grid">${field('start_date','Inicio *',g.start_date,'date','required')}${field('end_date','Fin *',g.end_date,'date','required')}</div><p id="guard-date-help" class="callout" role="status"></p><details class="guard-rule-preview"><summary>Ver intervalos de la regla seleccionada</summary><div id="guard-revision-intervals"></div></details>${field('reason','Motivo del ajuste *','','text','required maxlength="2000"')}<label class="checkbox"><input name="confirm" type="checkbox" required><span>Revisé el cambio y confirmo reenviar la Guardia a aprobación.</span></label>`,id,'Actualizar y reenviar'));
 $('#modal').classList.add('admin-dialog','guard-revision-dialog');$('#modal [data-form=guard-revision]').guardRules=review.rules;syncGuardDates();
}
function guardModal(startDate='',endDate=''){
  if(!state.rules.length)return toast('Tu Manager debe crear una regla de Guardia primero.',true);
  showModal('Solicitar Guardia',form('guard',select('rule_id','Regla de Guardia *',options(state.rules,'',x=>`${x.name} · vigente para Guardias desde ${fmtDate(x.effective_from)}`),'required')+`<div class="form-grid">${field('start_date','Fecha de inicio *','','date','required')}${field('end_date','Fecha de fin *','','date','required')}</div><p id="guard-date-help" class="callout" role="status"></p><p class="callout">La solicitud es individual y requiere aprobación. La OT aprobada se descuenta de la Guardia al calcular el neto.</p>`,'','Enviar solicitud'));
  const f=$('#modal [data-form=guard]');if(startDate)f.elements.start_date.value=startDate;if(endDate)f.elements.end_date.value=endDate;syncGuardDates();
}
function syncGuardDates(){
  const f=$('[data-form=guard],[data-form=guard-revision]');if(!f)return;
  const r=(f.guardRules||state.rules).find(r=>r.id===f.elements.rule_id.value),start=f.elements.start_date,end=f.elements.end_date,help=$('#guard-date-help');
  if(!r)return;
  if(f.elements.rule_token)f.elements.rule_token.value=f.elements.rule_id.selectedOptions[0]?.dataset.token||'';
  const preview=$('#guard-revision-intervals');if(preview)preview.innerHTML=r.segments.map(s=>`<span>${['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][s.day]} · ${esc(s.start)} — ${esc(s.end)}${s.end<=s.start?' (+1 día)':''}</span>`).join('');
  start.min=r.effective_from;end.min=start.value||r.effective_from;
  const invalid=start.value&&start.value<r.effective_from;
  const message=`La regla «${r.name}» aplica a Guardias que comienzan el ${fmtDate(r.effective_from)} o después.`;
  start.setCustomValidity(invalid?message+' El inicio seleccionado es '+fmtDate(start.value)+'.':'');
  end.setCustomValidity(end.value&&start.value&&end.value<start.value?'La fecha de fin debe ser igual o posterior al inicio.':'');
  help.textContent=invalid?message+' Tu solicitud empieza el '+fmtDate(start.value)+', antes de esa vigencia.':message+(start.value?' Periodo seleccionado: '+fmtDate(start.value)+(end.value?' al '+fmtDate(end.value):'')+'.':' La vigencia se compara con el inicio solicitado, no con la fecha de hoy.');
  help.classList.toggle('date-warning',!!invalid);
}
function ruleModal(id=''){
  const saved=state.rules.find(r=>r.id===id);
  const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  showModal(saved?'Editar regla de Guardia':'Nueva regla de Guardia',form('rule',field('name','Nombre de la regla *',saved?.name||'','text','required')+field('effective_from','Vigente desde *',saved?.effective_from||new Date().toLocaleDateString('sv-SE'),'date','required')+`<div class="weekly-rule-intro">${icon('time')}<p>Configura uno o varios intervalos por día. Un fin anterior al inicio, como 20:00 → 00:00, termina al día siguiente.</p></div><section class="rule-bulk"><h3>Configura una vez y aplica a varios días</h3><p>Primero define los horarios de un día; luego cópialos a los días seleccionados.</p><div class="rule-copy-targets">${days.map((day,i)=>`<label class="checkbox"><input type="checkbox" data-copy-day="${i}" ${i<5?'checked':''}>${day}</label>`).join('')}</div>${btn('Copiar día abierto a seleccionados','rule-copy','','secondary')}</section><div class="rule-day-tabs" role="group" aria-label="Día que deseas configurar">${days.map((day,i)=>`<button type="button" data-action="rule-day-open" data-id="${i}" aria-pressed="${i===0}">${day}<small data-day-count="${i}"></small></button>`).join('')}</div><div class="rule-editor-layout"><div class="weekly-rule-days">${days.map((day,i)=>`<section class="rule-day" data-rule-day="${i}" ${i?'hidden':''}><header><label class="checkbox"><input type="checkbox" name="days" value="${i}"><strong>${day}</strong></label><label class="checkbox rule-full-day"><input type="checkbox" name="full_day_${i}" data-full-day="${i}" disabled><span>24 horas</span></label></header><div class="rule-day-content" hidden><div class="rule-intervals">${ruleInterval(i,0)}</div><button type="button" class="link rule-add" data-action="rule-add" data-id="${i}">＋ Agregar intervalo</button><p class="rule-full-note" hidden>Cobertura completa · 00:00 a 00:00 del día siguiente.</p></div></section>`).join('')}</div><aside class="rule-live-preview" aria-live="polite"></aside></div><p class="callout">Las Guardias existentes conservan su cobertura original. Si cambias o retiras la regla, el Técnico recibe un aviso para revisar y reenviar sus solicitudes a aprobación.${saved?` Esta regla está vinculada a ${state.guards.filter(g=>g.rule_snapshot?.id===saved.id).length} solicitudes existentes.`:''}</p>`,id),true);
  if(saved){$$('[data-rule-day]').forEach(section=>{const day=Number(section.dataset.ruleDay),segments=saved.segments.filter(s=>Number(s.day)===day);if(!segments.length)return;$('[name=days]',section).checked=true;const full=segments.length===1&&segments[0].start===segments[0].end&&segments[0].start==='00:00';$('[data-full-day]',section).checked=full;$('.rule-intervals',section).innerHTML=segments.map((segment,i)=>ruleInterval(day,i)).join('');$$('[data-rule-segment]',section).forEach((row,i)=>{$('[data-start]',row).value=segments[i].start;$('[data-end]',row).value=segments[i].end;});syncRuleDay(section);});}
  $$('[data-rule-day]').forEach(syncRuleDay);paintRulePreview();
}
function paintRulePreview(){
 const box=$('.rule-live-preview');if(!box)return;
 const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'],minute=t=>Number(t.slice(0,2))*60+Number(t.slice(3));let total=0,intervals=[];
 const body=$$('[data-rule-day]').map(section=>{const day=Number(section.dataset.ruleDay),enabled=$('[name=days]',section).checked,full=$('[data-full-day]',section).checked;
 const parts=!enabled?[]:full?[{a:0,n:1440}]:$$('[data-rule-segment]',section).map(row=>{const a=minute($('[data-start]',row).value||'00:00'),b=minute($('[data-end]',row).value||'00:00');return {a,n:(b-a+1440)%1440||1440};});
 const duration=parts.reduce((n,x)=>n+x.n,0);total+=duration;parts.forEach(x=>{const a=day*1440+x.a,b=a+x.n;intervals.push([a,Math.min(b,10080)]);if(b>10080)intervals.push([0,b-10080]);});
 return `<div class="rule-preview-day"><span>${days[day]}</span><strong>${hours(duration)} h</strong><svg class="rule-coverage-track" viewBox="0 0 1440 12" preserveAspectRatio="none" role="img" aria-label="${days[day]}: ${hours(duration)} horas">${parts.map(x=>`<rect x="${x.a}" y="0" width="${Math.min(x.n,1440-x.a)}" height="12" fill="#149eaa"/>`).join('')}</svg></div>`;}).join('');
 intervals.sort((a,b)=>a[0]-b[0]);let end=-1,overlap=false;for(const [a,b] of intervals){if(a<end)overlap=true;end=Math.max(end,b);}
 box.innerHTML=`<h3>Vista previa semanal</h3><p class="muted">Bloques por día de inicio · los cruces continúan al siguiente día.</p>${body}<div class="rule-week-total">${hours(total)} h <small>semanales antes de descontar OT</small></div>${overlap?'<p class="rule-overlap" role="alert">Hay horarios traslapados. Corrige los intervalos antes de guardar.</p>':''}`;
 $('[data-form=rule] button[type=submit]').disabled=overlap;
}
function copyRuleDay(){
 const source=$('[data-rule-day]:not([hidden])');if(!source)return;
 const enabled=$('[name=days]',source).checked,full=$('[data-full-day]',source).checked;
 const values=$$('[data-rule-segment]',source).map(row=>[$('[data-start]',row).value,$('[data-end]',row).value]);
 $$('[data-copy-day]:checked').forEach(target=>{const day=target.dataset.copyDay,section=$(`[data-rule-day="${day}"]`);if(section===source)return;$('[name=days]',section).checked=enabled;$('[data-full-day]',section).checked=full;$('.rule-intervals',section).innerHTML=values.map((v,i)=>ruleInterval(day,i)).join('');$$('[data-rule-segment]',section).forEach((row,i)=>{$('[data-start]',row).value=values[i][0];$('[data-end]',row).value=values[i][1];});syncRuleDay(section);});paintRulePreview();toast('Horarios copiados. Revisa la vista previa semanal.');
}
function refitRuleEditor(){
  const editor=$('[data-form=rule]');if(!editor)return;
  $$('.rule-intervals',editor).forEach(list=>{if(!list._viewport)return;list._viewport.children.forEach(row=>row.classList.remove('viewport-off'));list._viewport.control.remove();delete list._viewport;});
  PulseLayout.dialog();
  PulseLayout.reveal($('[data-rule-day]:not([hidden])',editor));
}
function ruleInterval(day,index){
  return `<div class="rule-interval" data-rule-segment><label><span>Inicio</span><input type="time" name="start_${day}${index?'_'+index:''}" data-start value="00:00" aria-label="Inicio intervalo ${index+1}" disabled></label><span class="interval-arrow">→</span><label><span>Fin</span><input type="time" name="end_${day}${index?'_'+index:''}" data-end value="08:00" aria-label="Fin intervalo ${index+1}" disabled></label><small data-interval-note>Del mismo día</small><button type="button" class="icon-btn" data-action="rule-remove" aria-label="Eliminar intervalo">${icon('close')}</button></div>`;
}
function syncRuleDay(section){
  const enabled=$('[name="days"]',section).checked,full=$('[data-full-day]',section).checked;
  $('[data-full-day]',section).disabled=!enabled;$('.rule-day-content',section).hidden=!enabled;
  $('.rule-intervals',section).hidden=full;$('.rule-add',section).hidden=full;$('.rule-full-note',section).hidden=!full;
  const count=$(`[data-day-count="${section.dataset.ruleDay}"]`);if(count)count.textContent=enabled?(full?'24 h':$$('[data-rule-segment]',section).length+' intervalos'):'Sin cobertura';
  $$('[data-rule-segment]',section).forEach(row=>{const a=$('[data-start]',row),b=$('[data-end]',row);a.disabled=b.disabled=!enabled||full;a.required=b.required=enabled&&!full;$('[data-interval-note]',row).textContent=a.value===b.value?'24 horas':b.value<a.value?'Termina al día siguiente':'Del mismo día';});
  paintRulePreview();
}


const accessDraft = {identity:''};
function accessField(name,label,{value='',type='text',placeholder='',hint='',symbol='profile',autofocus=false}={}){
  const id='access-'+name, password=type==='password';
  return `<label class="field access-field" for="${id}"><span>${label}</span><span class="access-input">${icon(symbol)}<input id="${id}" name="${name}" type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}" required ${password?'minlength="10" autocomplete="new-password"':name==='identity'?'autocomplete="username" autocapitalize="none" spellcheck="false"':'autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="40"'} ${autofocus?'autofocus':''} aria-describedby="${id}-hint access-error">${password?`<button type="button" class="password-visibility" data-action="password-visibility" data-id="${id}" aria-label="Mostrar contraseña" aria-pressed="false">${icon('eye')}</button>`:''}</span><small id="${id}-hint" class="access-hint">${hint}</small></label>`;
}
function accessShell(title,subtitle,symbol,body,{wide=false,success=false}={}){
  showModal(title,body);
  const modal=$('#modal');modal.className=`access-modal ${wide?'access-wide':''} ${success?'access-success':''}`;
  $('.dialog-header',modal).outerHTML=`<header class="access-header"><div class="access-topline"><span class="access-brand">${icon('time')} OPERATIONAL PULSE</span><button type="button" class="icon-btn" data-action="close" aria-label="Cerrar">${icon('close')}</button></div><div class="access-intro"><span class="access-hero-icon">${icon(symbol)}</span><div><p class="eyebrow">${success?'TODO LISTO':'TU ACCESO, PASO A PASO'}</p><h2 id="dialog-title">${title}</h2></div></div><p class="access-subtitle">${subtitle}</p></header>`;
  $('[autofocus]',modal)?.focus();
}
function accessForm(name,body,submit,secondary='Volver al inicio'){
  return `<form data-form="${name}" class="access-form"><div class="access-body">${body}<p id="access-error" class="form-error" role="alert" tabindex="-1"></p></div><footer class="access-footer"><button type="button" class="access-back" data-action="close">${icon('back')} ${secondary}</button><button type="submit" class="primary access-submit">${submit} ${icon('forward')}</button></footer><div class="access-footnote">${icon('lock')} Acceso a tu espacio de trabajo</div></form>`;
}
function accessSteps(current){
  return `<ol class="access-steps" aria-label="Proceso de recuperación">${['Solicita','Valida tu identidad','Restablece'].map((label,i)=>`<li class="${i===current?'current':i<current?'complete':''}" ${i===current?'aria-current="step"':''}><span>${i<current?icon('check'):i+1}</span><small>${label}</small></li>`).join('')}</ol>`;
}
function publicModal(kind){
  const current=$('.access-form [name="identity"]');if(current)accessDraft.identity=current.value;
  const identity=accessField('identity','Employee ID o usuario',{value:accessDraft.identity,placeholder:'Ej. tu Employee ID',autofocus:true});
  if(kind==='activate'){
    const body=`<section class="access-section"><div class="access-section-title"><span>01</span><div><h3>Verifica tu cuenta</h3><p>Usa los datos que te entregó Administración.</p></div></div><div class="access-fields-grid">${identity}${accessField('code','Código de activación',{placeholder:'ACT-XXXXXXXXXX',hint:'Lo recibes de Administración.',symbol:'key'})}</div></section><section class="access-section"><div class="access-section-title"><span>02</span><div><h3>Define tu contraseña</h3><p>Será tu acceso personal a Operational Pulse.</p></div></div><div class="access-fields-grid">${accessField('password','Contraseña',{type:'password',placeholder:'Al menos 10 caracteres',symbol:'lock'})}${accessField('confirm','Confirmar contraseña',{type:'password',placeholder:'Escríbela una vez más',symbol:'lock'})}</div><div class="password-checks" aria-live="polite"><span data-password-check="length">${icon('check')} Al menos 10 caracteres</span><span data-password-check="match">${icon('check')} Las contraseñas coinciden</span></div></section>`;
    accessShell('Activa tu cuenta','Tu primer paso para conectar con tu equipo. Confirma tu acceso y crea una contraseña.', 'key',accessForm('activate',body,'Activar mi cuenta'),{wide:true});
  }
  if(kind==='request'){
    const body=`${accessSteps(0)}<div class="access-copy"><h3>Vamos a ayudarte a volver.</h3><p>Ingresa tu usuario para solicitar la recuperación. Tu Manager valida los accesos de Técnicos; Administración atiende a Administradores, Managers y Leads.</p></div>${identity}<div class="access-assistance">${icon('info')}<p>El código se entrega por un canal corporativo; no se envía un correo automático.</p></div><button type="button" class="access-alternative" data-action="recovery-complete"><span class="alternative-icon">${icon('key')}</span><span><strong>¿Ya tienes un código?</strong><small>Continúa para crear tu nueva contraseña.</small></span>${icon('forward')}</button>`;
    accessShell('Recupera tu acceso','Un proceso sencillo para volver a tu espacio de trabajo.', 'recoveries',accessForm('recovery-request',body,'Solicitar recuperación'));
  }
  if(kind==='complete'){
    const body=`${accessSteps(2)}<section class="access-section"><div class="access-section-title"><span>${icon('key')}</span><div><h3>Confirma tu acceso</h3><p>Ten a la mano el código que te entregó tu responsable.</p></div></div><div class="access-fields-grid">${identity}${accessField('code','Código de recuperación',{placeholder:'REC-XXXXXXXXXXXX',hint:'Tiene una vigencia de 15 minutos y un solo uso.',symbol:'key'})}</div></section><section class="access-section"><div class="access-section-title"><span>${icon('lock')}</span><div><h3>Elige una nueva contraseña</h3><p>Al guardar, las sesiones anteriores se cerrarán.</p></div></div><div class="access-fields-grid">${accessField('password','Nueva contraseña',{type:'password',placeholder:'Al menos 10 caracteres',symbol:'lock'})}${accessField('confirm','Confirmar contraseña',{type:'password',placeholder:'Escríbela una vez más',symbol:'lock'})}</div><div class="password-checks" aria-live="polite"><span data-password-check="length">${icon('check')} Al menos 10 caracteres</span><span data-password-check="match">${icon('check')} Las contraseñas coinciden</span></div></section><button type="button" class="access-inline-link" data-action="recovery-request">${icon('back')} Necesito solicitar otro código</button>`;
    accessShell('Crea tu nuevo acceso','Confirma el código de recuperación y vuelve a tomar el control de tu cuenta.', 'lock',accessForm('recovery-complete',body,'Guardar contraseña'),{wide:true});
  }
}
function accessResult(kind,username){
  accessDraft.identity=username;
  const pending=kind==='request';
  const title=pending?'Solicitud recibida':kind==='activate'?'Tu cuenta está lista':'Contraseña actualizada';
  const subtitle=pending?'El siguiente paso es validar tu identidad.':kind==='activate'?'Ya puedes comenzar a trabajar con tu equipo.':'Todo listo para volver a tu espacio de trabajo.';
  const copy=pending?'Si tu cuenta está activa, tu solicitud quedó registrada. Contacta a tu Manager o a Administración para que valide tu identidad y te entregue un código de recuperación.':kind==='activate'?'Tu acceso se activó correctamente. Inicia sesión con tu usuario y la contraseña que acabas de crear.':'Tu nueva contraseña se guardó y las sesiones anteriores se cerraron. Ya puedes iniciar sesión de nuevo.';
  const body=`<div class="access-result-body">${pending?accessSteps(1):''}<div class="access-result-account">${icon('profile')}<div><small>USUARIO</small><strong>${esc(username)}</strong></div><span class="access-result-pill">${pending?'En validación':'Listo'}</span></div><p>${copy}</p>${pending?`<div class="access-assistance">${icon('time')}<p>Cuando recibas tu código, tendrás 15 minutos para utilizarlo. Sólo puede usarse una vez.</p></div>`:''}<button class="primary access-result-primary" data-action="${pending?'recovery-complete':'access-login'}">${pending?'Ya tengo mi código':'Ir a iniciar sesión'} ${icon('forward')}</button>${pending?'<button class="access-result-back" data-action="access-login">Volver al inicio de sesión</button>':''}</div>`;
  accessShell(title,subtitle,pending?'recoveries':'check',body,{success:true});
}

function ownerRecordActions(kind,r){
 if(!isTech()||r.user_id!==me().id)return '';
 if(kind==='guard')return !me().is_lead&&r.status!=='CANCELLED'?btn(r.rule_changed?'Revisar cambio':'Editar Guardia','guard-edit',r.id,'secondary'):'';
 const active=state.timers.some(t=>t.overtime_id===r.id);
 if(active||r.execution==='PAUSED')return btn('Ver Timer','own-timer-open',r.id,'primary');
 return btn(r.status==='DOCUMENTATION'?'Documentar OT':'Editar y reenviar','ot-edit',r.id,'secondary')+recordTimerControl(r);
}
function recordAvailability(r){
 if(r.capture_type!=='PLANNED'||r.execution!=='SCHEDULED'||r.user_id!==me().id)return '';
 const future=Date.parse(r.scheduled_start)>Date.now()+serverOffset;
 return `<p class="callout" id="ot-availability-${esc(r.id)}">${future?'Timer disponible el '+fmtDate(r.scheduled_start)+' a las '+fmtTime(r.scheduled_start)+'.':Date.parse(r.scheduled_end)<=Date.now()+serverOffset?'La ventana terminó sin iniciar. Edita y reenvía para solicitar otro horario.':'El Timer requiere aprobación y una ventana autorizada vigente.'}</p>`;
}
function detailModal(key){
  const [kind,id]=key.split(':');if(kind==='group')return groupActivityModal(id);const r=(kind==='ot'?state.overtime:state.guards).find(r=>r.id===id);if(!r)return toast('El registro cambió o ya no está en tu alcance.',true);
  const logs=state.audit.filter(a=>a.entity_id===id),activeTimer=state.timers.find(t=>t.overtime_id===id),segments=r.execution==='COMPLETED'&&r.actual_segments?.length?r.actual_segments:(state.timer_segments||[]).filter(t=>t.overtime_id===id);
  showModal('Detalle del registro',`<div class="form-body"><p class="form-instructions"><strong>Revisa antes de decidir</strong>Consulta el periodo, la documentación y la trazabilidad. Si tienes autoridad, puedes aprobar o explicar el rechazo al final.</p>${kind==='ot'&&r.capture_type==='HISTORICAL'&&!r.recovery_info?'<p class="callout historical-guidance"><strong>Captura posterior · revisión de contexto</strong><br>La OT histórica debe ser excepcional. Revisa la justificación de la actividad, el motivo de captura posterior y por qué no se utilizó el Timer. Este aviso no cambia la aprobación ni las horas.</p>':''}${r.recovery_info?`<p class="callout">Recuperado desde Excel · ${esc(r.recovery_info.origin)}. Las horas requieren nueva revisión. ${kind==='guard'?'Se conservan los intervalos del archivo como cobertura fija; no es una nueva regla semanal.':''}</p>`:''}<div class="detail-hero">${identity(person(r.user_id))}${badge(r.execution==='RUNNING'?'RUNNING':r.execution==='PAUSED'?'PAUSED':r.status)}</div>${r.execution==='RUNNING'?`<div class="detail-live"><span class="live-dot"></span><span>Timer activo</span><strong data-elapsed="${esc(activeTimer?.start_at||r.start_at)}" data-base="${r.worked_seconds||0}" ${r.capture_type==='PLANNED'?`data-until="${esc(r.scheduled_end)}"`:''}>00:00:00</strong></div>`:''}<dl>${r.origin_info?`<dt>${r.origin_info.inferred?'Grupo al incorporar trazabilidad':'Grupo de origen'}</dt><dd>${esc(r.origin_info.group_code)} · ${esc(r.origin_info.group_name)} · ${esc(r.origin_info.account_name)}</dd>`:''}${kind==='guard'&&r.timeline_days?`<dt>Cobertura total del periodo</dt><dd class="guard-detail-total">${hours(r.timeline_days.reduce((sum,day)=>sum+day.segments.reduce((n,p)=>n+(Date.parse(p.end_at)-Date.parse(p.start_at))/60000,0),0))} h</dd>`:''}<dt>Registro</dt><dd>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</dd><dt>Periodo</dt><dd>${kind==='ot'?range(r.start_at||r.scheduled_start,r.end_at||r.scheduled_end):`${fmtDate(r.start_date)} → ${fmtDate(r.end_date)}`}</dd>${kind!=='ot'&&r.rule_snapshot?.coverage_end_at?`<dt>Cierre administrativo</dt><dd>${fmtDate(r.rule_snapshot.coverage_end_at)} · ${fmtTime(r.rule_snapshot.coverage_end_at)}</dd>`:''}${kind==='ot'?`<dt>Descripción</dt><dd>${esc(r.description||'—')}</dd><dt>Justificación</dt><dd>${esc(r.justification||'—')}</dd><dt>Impacto</dt><dd>${esc(r.impact||'—')}</dd><dt>Tiempo compensatorio</dt><dd>${esc(r.in_lieu||'—')}</dd><dt>Revisiones</dt><dd>${r.revision}</dd>`:''}</dl>${kind==='ot'&&segments.length?`<section class="worked-segments"><h3>Tramos trabajados${r.time_corrected?' · horario corregido':''}</h3><p class="muted">La espera entre tramos no suma OT. Tiempo cerrado: ${hours((r.worked_seconds||0)/60)} h.</p><div class="timer-segment-list">${segments.map(t=>`<p>${range(t.start_at,t.end_at)}${!t.end_at?' · En curso':''}</p>`).join('')}</div></section>`:''}${kind==='ot'?recordAvailability(r):''}${kind==='ot'&&r.capture_type==='PLANNED'&&(isManager()||state.can_approve)?`<section class="analytics-activity-link"><div><h3>Participación del Grupo</h3><p class="muted">Consulta quién se inscribió, quién ejecutó su Timer y sus tiempos individuales.</p></div>${btn('Ver participantes','analytics-participants',r.id,'secondary')}</section>`:''}<h3>Trazabilidad</h3><div class="audit-list">${logs.map(a=>{let d={};try{d=JSON.parse(a.detail)}catch{}return `<div><span></span><p><strong>${esc(auditLabel(a.action))}</strong><small>${fmtDate(a.created_at)} · ${fmtTime(a.created_at)} · ${esc(a.actor_id?full(person(a.actor_id)):'Sistema')}</small>${d.decision?`<small>${esc(statuses[d.decision]||d.decision)}</small>`:''}${d.to?`<small>Nuevo fin: ${fmtDate(d.to)} · ${fmtTime(d.to)}</small>`:''}${d.reason?`<small>${esc(d.reason)}</small>`:''}</p></div>`;}).join('')||'<p class="muted">Sin eventos disponibles.</p>'}</div></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}${ownerRecordActions(kind,r)}${!['analytics','records'].includes(page)&&state.can_approve&&r.user_id!==me().id&&r.status==='SUBMITTED'&&r.execution!=='RUNNING'?btn('Rechazar','reject',key,'text-danger')+btn('Aprobar','approve',key,'primary'):''}</footer>`);tick();
}
function auditLabel(action){return {DEMO_CREATE_OT:'Registro de OT de demostración',DEMO_APPROVE_OT:'Aprobación simulada de OT',DEMO_REJECT_OT:'Rechazo simulado de OT',DEMO_REQUEST_GUARD:'Solicitud de Guardia de demostración',DEMO_APPROVE_GUARD:'Aprobación simulada de Guardia',RECOVER_TIME_FROM_EXCEL:'Horas recuperadas desde Excel; requieren nueva revisión',RECOVER_TIME_BATCH:'Recuperación de respaldo Excel',PAUSE_PLANNED_WINDOW:'Timer pausado al terminar la ventana',REQUEST_OT_EXTENSION:'Extensión solicitada',DECIDE_OT_EXTENSION:'Extensión revisada',CANCEL_OT_EXTENSION:'Extensión cancelada',FINISH_PAUSED_OT:'Tiempo trabajado enviado a revisión',CREATE_OT:'Registro de OT',EDIT_OT_REOPEN_APPROVAL:'Edición y reenvío a aprobación',CORRECT_OT_TIME:'Horario corregido; tramos originales conservados',REQUEST_GUARD:'Solicitud de Guardia',REVISE_GUARD:'Guardia actualizada y reenviada a aprobación',APPROVED:'Aprobado',REJECTED:'Rechazado',START_TIMER:'Timer iniciado',STOP_TIMER:'Timer detenido',JOIN_SHARED_OT:'Participación en actividad programada',ADMIN_STOP_TIMER_ON_OFFBOARD:'Timer cerrado por baja administrativa',ADMIN_DOCUMENT_ON_OFFBOARD:'Documentación completada durante la baja',CANCEL_SCHEDULE_ON_OFFBOARD:'OT sin ejecutar cancelada por baja',CLOSE_GUARD_ON_OFFBOARD:'Cobertura cerrada por baja',TRANSFER_PERSON:'Técnico transferido',TRANSFER_GROUP:'Grupo transferido',OFFBOARD_PERSON:'Baja de acceso',REACTIVATE_PERSON:'Reactivación solicitada'}[action]||action;}

async function perform(action,id,button){
  if(action!=='entity-menu')closeEntityMenu();
  const confirmations={
    'account-delete':['Eliminar Cuenta','Sólo se puede eliminar una Cuenta vacía. Primero mueve o elimina sus Grupos.'],
    'activation-code':['Regenerar activación','El código anterior dejará de funcionar. Comparte el nuevo código con la persona por un canal corporativo.'],
    'rule-delete':['Eliminar regla de Guardia','La regla dejará de estar disponible para nuevas solicitudes. Las Guardias existentes conservan su cobertura y su historial.'],
    'paused-finish':['Finalizar OT pausada','Se enviará a revisión únicamente el tiempo trabajado. Las solicitudes de extensión pendientes se cancelarán.'],
    'timer-start':['Iniciar OT de emergencia','El Timer comenzará al confirmar. Deténlo al terminar y completa la documentación para solicitar aprobación.']
  };
  if(confirmations[action]&&button?.dataset.confirmed!=='true'){
    const [title,instruction]=confirmations[action];
    showModal(title,form('confirmation',`<input type="hidden" name="action" value="${esc(action)}"><input type="hidden" name="target" value="${esc(id)}"><p class="form-instructions"><strong>Antes de confirmar</strong>${instruction}</p>`,'','Confirmar'));return;
  }
  switch(action){
    case 'entity-menu':openEntityMenu(id,button);return;
    case 'password-visibility':{const input=id==='login-password'?$('#login-password'):$('#'+id,$('#modal'));if(!input||!['password','confirm'].includes(input.name))return;const reveal=input.type==='password';input.type=reveal?'text':'password';button.setAttribute('aria-pressed',String(reveal));button.setAttribute('aria-label',reveal?'Ocultar contraseña':'Mostrar contraseña');button.innerHTML=icon(reveal?'eye-off':'eye');return;}
    case 'access-login':$('#modal').close();{const input=$('[data-form="login"] [name="identity"]');if(input){input.value=accessDraft.identity;$('[data-form="login"] [name="password"]')?.focus();}}return;
    case 'analytics-months':comparisonModal();return;
    case 'open-records':{const saved={...filters},months=[...comparisonMonths],series=$('#modal').open&&$('#modal').classList.contains('expanded-chart-dialog')?$('#modal').dataset.chartSeries:'ALL';if(['OT',...analyticsTypes].includes(series))saved.kind=series;await navigate(['myAnalytics','myRecords'].includes(page)?'myRecords':'records');filters=saved;comparisonMonths=months;await loadLedger();render();return;}
    case 'comparison-add':{const field=$('[name=compare_month]',$('#modal'));if(!field.value){field.focus();return;}if(!comparisonDraft.includes(field.value)){if(comparisonDraft.length>=24)return toast('Selecciona hasta 24 meses.',true);comparisonDraft.push(field.value);comparisonDraft.sort();}field.value='';paintComparisonDraft();return;}
    case 'comparison-remove':comparisonDraft=comparisonDraft.filter(key=>key!==id||key===month);paintComparisonDraft();paintMonthGrid();return;
    case 'comparison-preset':applyComparisonPreset(id);return;
    case 'comparison-year':comparisonYear+=Number(id);paintMonthGrid();return;
    case 'comparison-toggle':if(id===month)return;if(comparisonDraft.includes(id))comparisonDraft=comparisonDraft.filter(k=>k!==id);else{if(comparisonDraft.length>=24)return toast('Selecciona hasta 24 meses.',true);comparisonDraft.push(id);comparisonDraft.sort();}paintComparisonDraft();paintMonthGrid();return;
    case 'chart-layout-edit':case 'chart-layout-show':case 'chart-layout-reset':case 'chart-layout-hide':case 'chart-layout-visibility':chartLayoutAction(action,id);return;
    case 'decision-detail':decisionDetailModal(id);return;
    case 'chart-series':{const [kind,chosen]=id.split(':');if(!chartSeriesOptions(kind).length)return;const selected=$('#modal').dataset.chartKind===kind?$('#modal').dataset.chartSeries:'ALL';decisionDetailModal(kind,chosen===selected?'ALL':chosen,chosen);return;}
    case 'analytics-participants':await analyticsParticipantsModal(id);return;
    case 'chart-expand':expandAnalyticsChart(id);return;
    case 'analytics-visuals':analyticsVisuals();return;
    case 'analytics-reset':filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};comparisonMonths=[];clearTimeout(analyticsSearchTimer);await loadLedger();render();return;
    case 'review-record':{state=await api('/api/state');await navigate('teamTime');const [kind,recordId]=id.split(':');detailModal(kind+':'+recordId);return;}
    case 'analytics-records':if(['analytics','myAnalytics','records','myRecords'].includes(page)){filters.kind=id==='ALL'?'':id;await loadLedger();render();}else{analyticsDetailType=id;render();PulseLayout.reveal($('#analytics-records'));}return;
    case 'analytics-detail-close':analyticsDetailType=null;render();return;
    case 'analytics-group':$('#modal').close();filters.group=id;filters.person='';await loadLedger();render();PulseLayout.reveal($('#analytics-users'));return;
    case 'analytics-user':$('#modal').close();filters.person=id;analyticsDetailType='ALL';await loadLedger();render();PulseLayout.reveal($('#analytics-records'));return;
    case 'about':aboutProject();return;
    case 'close':$('#modal').close();return;
    case 'logout':await api('/api/logout','POST',{});state=null;page='dashboard';$('#modal').close();render();return;
    case 'group-search-open':openSearchedGroup(id);return;
    case 'account-new':accountModal();return;
    case 'account-edit':accountModal(id);return;
    case 'manager-group-new':{const m=person(id);groupModal('',m.account_id,m.id);return;}
    case 'group-new':groupModal('',id);return;
    case 'group-edit':groupModal(id);return;
    case 'lead-new':personModal('','LEAD',id);return;
    case 'manager-new':personModal('','MANAGER',id);return;
    case 'tech-new':personModal('','USER',id);return;
    case 'admin-new':personModal('','ADMIN');return;
    case 'person-edit':personModal(id);return;
    case 'transfer-request-new':requestTransferModal(id);return;
    case 'transfer-requests':transferRequestsModal();return;
    case 'transfer-request-review':{const r=state.transfer_requests.find(r=>r.id===id);if(person(r.user_id)?.group_id!==r.source_group_id)return toast('El Técnico ya cambió de Grupo. Rechaza la solicitud indicando el motivo.',true);transferModal(r.user_id);const f=$('[data-form=transfer]');if(f){const hidden=document.createElement('input');hidden.type='hidden';hidden.name='transfer_request_id';hidden.value=r.id;f.append(hidden);f.elements.transfer_reason.value=r.reason;const note=document.createElement('p');note.className='callout';note.textContent='Destino solicitado por el Manager: '+r.destination;$('.form-body',f).prepend(note);PulseLayout.dialog();}return;}
    case 'transfer-request-reject':showModal('Rechazar solicitud de cambio',form('transfer-request-reject',field('reason','Motivo *','','text','required'),id,'Rechazar'));$('#modal').classList.add('compact-dialog');return;
    case 'group-details':organizationOverview=false;render();PulseLayout.reveal($('[data-group="'+id+'"]'));return;
    case 'organizer-open':organizerOpen(id);return;
    case 'organizer-move':{const [p,g]=id.split(':');stageOrganizerMove(p,g);return;}
    case 'organizer-undo':delete organizer.moves[id];if(!Object.keys(organizer.moves).length)organizer.review=false;paintOrganizer();return;
    case 'organizer-reset':organizer.moves={};organizer.review=false;paintOrganizer();return;
    case 'organizer-review':if(!Object.keys(organizer.moves).length)return;organizer.review=true;paintOrganizer();return;
    case 'organizer-back':organizer.review=false;paintOrganizer();return;
    case 'organizer-page':{const [side,n]=id.split(':');organizer.pages[side]=Math.max(0,Number(n));paintOrganizer();return;}
    case 'organizer-review-page':organizer.reviewPage=Math.max(0,Number(id.split(':')[1]));paintOrganizer();return;
    case 'organizer-save':{if(!organizer.reason.trim()){$('.organizer-error').textContent='Indica el motivo antes de confirmar.';$('#organizer-reason').focus();return;}try{const response=await api('/api/admin/organization/transfers','POST',{reason:organizer.reason,moves:Object.entries(organizer.moves).map(([user_id,to_group_id])=>({user_id,to_group_id,from_group_id:person(user_id).group_id}))});$('#modal').close();await refresh();toast(response.moved+' Técnicos trasladados.');}catch(error){$('.organizer-error').textContent=error.message;}return;}
    case 'manager-transfer-new':managerTransferModal(id);return;
    case 'manager-transfers':managerTransfersModal();return;
    case 'manager-transfer-accept':managerTransferDecision(id,'APPROVED');return;
    case 'manager-transfer-reject':managerTransferDecision(id,'REJECTED');return;
    case 'manager-transfer-cancel':managerTransferDecision(id,'CANCELLED');return;
    case 'move-mode':syncTechnicianMove(id);return;
    case 'team-details':technicianDetailsModal(id);return;
    case 'team-move':teamMoveModal(id);return;
    case 'person-transfer':transferModal(id);return;
    case 'transfer-change-target':{const selector=$('.transfer-target-selector');selector.hidden=false;PulseLayout.dialog();PulseLayout.reveal($('[name=group_id]',selector));$('[name=group_id]',selector).focus();return;}
    case 'transfer-reason':{const field=$('[data-form=transfer] [name=transfer_reason]');field.value=id;$$('.quick-reasons button').forEach(b=>b.classList.toggle('selected',b.dataset.id===id));return;}
    case 'group-transfer':transferModal(id,true);return;
    case 'person-offboard':await lifecycleModal(id);return;
    case 'person-reactivate':showModal('Reactivar acceso',form('reactivate',`<p class="callout">${esc(full(person(id)))} recibirá un código nuevo y definirá otra contraseña. No se restauran delegaciones, capacidad Lead ni asignaciones anteriores.</p>${field('reason','Motivo de reactivación *','','text','required')}`,id,'Generar activación'));return;
    case 'organization-open':adminAccountId=id;await navigate('organization');return;
    case 'admin-back':adminAccountId='';render();return;
    case 'admin-clear':adminAttention='';adminQuery='';adminCountry='';render();return;
    case 'admin-drill':adminAccountId='';adminAttention=['missing','vacant','activation','leads','managers'].includes(id)?id:'';adminQuery='';adminCountry='';await navigate(id==='recoveries'?'recoveries':'organization');return;
    case 'account-delete':await api('/api/accounts/'+id,'DELETE');break;
    case 'group-delete':await groupRemovalModal(id);return;
    case 'activation-code':{const r=await api(`/api/people/${id}/activation`,'POST',{});credentials(r.activation_code,person(id)?.username);return;}
    case 'activate':publicModal('activate');return;
    case 'recovery-request':publicModal('request');return;
    case 'recovery-complete':publicModal('complete');return;
    case 'recovery-view':{const result=await api(`/api/recoveries/${id}/view`,'POST',{});recoveryCodeModal(result,'Código vigente');return;}
    case 'recovery-issue':{const previous=state.recoveries.find(r=>r.id===id),regenerated=previous?.status==='ISSUED';const result=await api(`/api/recoveries/${id}/issue`,'POST',{});await refresh();recoveryCodeModal(result,regenerated?'Código regenerado':'Código generado',regenerated);return;}
    case 'open-calendar':await navigate('time');PulseLayout.reveal($('.monthly-calendar'));return;
    case 'calendar-preview':calendarPreviewModal();return;
    case 'calendar-preview-prev':await navigateCalendarPreview(-1);return;
    case 'calendar-preview-next':await navigateCalendarPreview(1);return;
    case 'calendar-preview-today':await navigateCalendarPreview(0);return;
    case 'calendar-range':calendarRangeMode=!calendarRangeMode;resetCalendarRange();button?.setAttribute('aria-pressed',String(calendarRangeMode));return;
    case 'calendar-new':if(calendarRangeMode)calendarPickRange(id);else calendarNewRecord(id);return;
    case 'calendar-day':calendarDayModal(id);return;
    case 'calendar-today':month=calendarDate(new Date(Date.now()+serverOffset)).slice(0,7);await loadLedger();render();$('.monthly-calendar')?.scrollIntoView({block:'nearest'});PulseLayout.reveal($('.monthly-calendar'));return;
    case 'group-timer-start':{const joined=await api('/api/windows/'+id+'/join','POST',{});await api('/api/timers/start','POST',{overtime_id:joined.id});$('#modal').close();await refresh();ownTimerModal(joined.id);toast('Tu Timer inició para la actividad del Grupo.');return;}
    case 'time-recovery':timeRecoveryModal();return;
    case 'claim-detail':claimWeekDetail(id);return;
    case 'ot-new':otModal();return;
    case 'ot-edit':otModal(id);return;
    case 'guard-new':guardModal();return;
    case 'guard-edit':await guardRevisionModal(id);return;
    case 'rule-new':ruleModal();return;
    case 'rule-edit':ruleModal(id);return;
    case 'rule-delete':await api('/api/rules/'+id,'DELETE');break;
    case 'window-join':await api(`/api/windows/${id}/join`,'POST',{});break;
    case 'delegation-inline':delegationDraftLead=id;render();PulseLayout.reveal($('#delegation-editor'));$('#delegation-editor button[type=submit]')?.focus({preventScroll:true});return;
    case 'delegation-cancel':delegationDraftLead='';render();return;
    case 'rule-copy':copyRuleDay();return;
    case 'rule-day-open':$$('[data-rule-day]').forEach(section=>section.hidden=section.dataset.ruleDay!==id);$$('[data-action=rule-day-open]').forEach(tab=>tab.setAttribute('aria-pressed',String(tab.dataset.id===id)));return;
    case 'rule-add':{const section=$(`[data-rule-day="${id}"]`);const index=Date.now();$('.rule-intervals',section).insertAdjacentHTML('beforeend',ruleInterval(id,index));syncRuleDay(section);refitRuleEditor();const input=$$('[data-start]',section).at(-1);PulseLayout.reveal(input);input?.focus({preventScroll:true});return;}
    case 'rule-remove':{const row=button.closest('[data-rule-segment]'),section=row.closest('[data-rule-day]');row.remove();if(!$('.rule-interval',section))$('.rule-intervals',section).innerHTML=ruleInterval(section.dataset.ruleDay,0);syncRuleDay(section);refitRuleEditor();return;}
    case 'dashboard-drill':{await navigate(id==='pending'?'teamTime':'records');filters.kind=id==='ot'?'OT':id==='guard'?'GUARD':id==='running'?'OT':'';filters.status=id==='pending'?'SUBMITTED':id==='running'?'RUNNING':'APPROVED';filters.period=['pending','running'].includes(id)?'ALL':'MONTH';await loadLedger();render();PulseLayout.reveal(id==='pending'?($('.extension-review')||$('.table-panel')):$('#analytics-records'));return;}
    case 'timer-open':{const record=state.overtime.find(o=>o.id===id);if(!record)return;await navigate('records');filters.person=record.user_id;filters.status='RUNNING';filters.period='ALL';await loadLedger();render();detailModal('ot:'+id);return;}
    case 'delegation-revoke':await api('/api/delegations/'+id,'DELETE');delegationDraftLead='';break;
    case 'timer-start':{const result=await api('/api/timers/start','POST',{});month=calendarDate(new Date(Date.now()+serverOffset)).slice(0,7);$('#modal').close();await refresh();const timer=state.timers.find(t=>t.id===result.id);if(timer)ownTimerModal(timer.overtime_id);toast('Timer de emergencia iniciado.');return;}
    case 'extension-new':extensionModal(id);return;
    case 'extension-cancel':await api('/api/extensions/'+id,'DELETE');break;
    case 'extension-approve':await api('/api/extensions/'+id+'/decision','POST',{decision:'APPROVED'});break;
    case 'extension-reject':showModal('Rechazar extensión',form('extension-reject',`<label class="field"><span>Motivo del rechazo *</span><textarea name="reason" rows="3" required></textarea></label>`,id,'Rechazar extensión'));$('#modal').classList.add('compact-dialog');return;
    case 'paused-finish':await api('/api/overtime/'+id+'/finish','POST',{});break;
    case 'own-timer-open':ownTimerModal(id);return;
    case 'timer-planned':await api('/api/timers/start','POST',{overtime_id:id});$('#modal').close();await refresh();ownTimerModal(id);toast('Timer iniciado.');return;
    case 'timer-stop':{const oid=state.timers.find(t=>t.id===id)?.overtime_id;await api(`/api/timers/${id}/stop`,'POST',{});$('#modal').close();await refresh();const o=state.overtime.find(o=>o.id===oid);if(o?.status==='DOCUMENTATION'){otModal(oid);toast('Timer detenido. Documenta la OT para enviarla a aprobación.');}else toast('Timer detenido. La OT se envió a revisión.');return;}
    case 'approve':{const [kind,identity]=id.split(':');await api(`/api/approvals/${kind}/${identity}`,'POST',{decision:'APPROVED'});$('#modal').close();break;}
    case 'reject':showModal('Rechazar registro',form('reject',`<label class="field"><span>Motivo del rechazo *</span><textarea name="reason" rows="4" required></textarea></label>`,id,'Rechazar registro'));return;
    case 'record-detail':await refresh();detailModal(id);return;
    case 'month-prev':case 'month-next':{const d=new Date(`${month}-15T12:00:00`);d.setMonth(d.getMonth()+(action==='month-next'?1:-1));month=d.toLocaleDateString('sv-SE').slice(0,7);if(['analytics','myAnalytics','records','myRecords'].includes(page))filters.period='MONTH';await loadLedger();render();return;}
    default:return;
  }
  await refresh();toast('Cambios guardados.');
}
async function submitForm(f){
  const fd=new FormData(f),data=Object.fromEntries(fd),kind=f.dataset.form,id=f.dataset.id;
  if(['activate','recovery-request','recovery-complete'].includes(kind)){data.identity=data.identity.trim();if(data.code)data.code=data.code.trim().toUpperCase();}
  if(['password','activate','recovery-complete'].includes(kind)&&data.password!==data.confirm)throw Error('Las contraseñas no coinciden.');
  let response;
  switch(kind){
    case 'confirmation':$('#modal').close();await perform(data.action,data.target,{dataset:{confirmed:'true'}});return;
    case 'login':await api('/api/login','POST',data);pageEntrance=true;page='dashboard';await refresh();return;
    case 'activate':await api('/api/activate','POST',data);accessResult('activate',data.identity);return;
    case 'recovery-request':await api('/api/recoveries','POST',data);accessResult('request',data.identity);return;
    case 'recovery-complete':await api('/api/recoveries/complete','POST',data);accessResult('complete',data.identity);return;
    case 'analytics-search':filters.search=String(data.search||'').trim();await runAnalyticsSearch();return;
    case 'analytics-months':{if(data.compare_month&&!comparisonDraft.includes(data.compare_month))comparisonDraft.push(data.compare_month);if(comparisonDraft.length>24)throw Error('Selecciona hasta 24 meses.');comparisonMonths=comparisonDraft.filter(key=>key!==month);filters.period='MONTH';$('#modal').close();await loadLedger();render();return;}
    case 'account':await api('/api/accounts'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'group':data.specialty_name=data.service_key;await api('/api/groups'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'person':if(f.querySelector('[name=group_ids]'))data.group_ids=fd.getAll('group_ids');data.is_lead=fd.has('is_lead');response=await api('/api/people'+(id?'/'+id:''),id?'PUT':'POST',data);await refresh();if(page==='organization'){const target=data.role==='MANAGER'?$('[data-manager="'+response.id+'"]'):data.is_lead?$('[data-manager="'+data.manager_id+'"]'):$('[data-group="'+data.group_id+'"]');if(target)PulseLayout.reveal(target);}if(response.activation_code){credentials(response.activation_code,data.username||data.employee_id);return;}break;
    case 'team-relocate':if(data.mode==='group')await api('/api/team/people/'+id+'/move','POST',{group_id:data.group_id,expected_group_id:data.expected_group_id,transfer_reason:data.reason});else await api('/api/team/transfers','POST',{user_id:id,target_manager_id:data.target_manager_id,expected_group_id:data.expected_group_id,reason:data.reason});break;
    case 'manager-transfer':await api('/api/team/transfers','POST',{...data,user_id:id});break;
    case 'manager-transfer-decision':await api('/api/team/transfers/'+id+'/decision','POST',data);break;
    case 'team-move':await api('/api/team/people/'+id+'/move','POST',data);break;
    case 'transfer-request':await api('/api/transfer-requests','POST',{...data,user_id:id});$('#modal').close();break;
    case 'transfer-request-reject':await api('/api/admin/transfer-requests/'+id+'/reject','POST',data);$('#modal').close();break;
    case 'transfer':await api(`/api/admin/people/${id}/transfer`,'POST',data);break;
    case 'group-transfer':{const source=group(id);await api('/api/groups/'+id,'PUT',{...source,...data});break;}
    case 'reactivate':response=await api(`/api/admin/people/${id}/reactivate`,'POST',data);await refresh();credentials(response.activation_code,response.username);return;
    case 'guard-revision':data.confirm=fd.has('confirm');await api('/api/guards/'+id,'PUT',data);month=data.start_date.slice(0,7);break;
    case 'group-removal':data.confirm=fd.has('confirm');await api('/api/groups/'+id,'DELETE',data);break;
    case 'offboard':{data.confirm=fd.has('confirm');data.stop_timers=fd.has('stop_timers');data.transfers=Object.fromEntries([...fd].filter(([k])=>k.startsWith('transfer:')).map(([k,v])=>[k.slice(9),v]));data.documents=$$('[data-offboard-document]',f).map(section=>({id:section.dataset.offboardDocument,...Object.fromEntries($$('input,textarea',section).map(input=>[input.dataset.key,input.value]))}));await api(`/api/admin/people/${id}/offboard`,'POST',data);break;}
    case 'profile':await api('/api/profile','PUT',data);break;
    case 'password':await api('/api/password','PUT',data);state=null;render();toast('Contraseña actualizada. Vuelve a iniciar sesión.');return;
    case 'extension':await api('/api/overtime/'+id+'/extensions','POST',data);break;
    case 'extension-reject':await api('/api/extensions/'+id+'/decision','POST',{decision:'REJECTED',reason:data.reason});break;
    case 'ot':{if(f.elements.actual_start){if(f.dataset.timeChanged==='true'){if(data.actual_start===f.dataset.originalActualStart)data.actual_start=f.dataset.originalStartIso;if(data.actual_end===f.dataset.originalActualEnd)data.actual_end=f.dataset.originalEndIso;const nodes=$$('[data-correction-segment]',f),value=input=>input.value===input.dataset.originalValue?input.dataset.originalAt:input.value;if(nodes.length)data.actual_segments=nodes.map(n=>({start_at:value($('[data-segment-start]',n)),end_at:value($('[data-segment-end]',n))}));}else{delete data.actual_start;delete data.actual_end;}}await api('/api/overtime'+(id?'/'+id:''),id?'PUT':'POST',data);if(data.scheduled_start||data.actual_start)month=(data.scheduled_start||data.actual_start).slice(0,7);break;}
    case 'time-recovery-preview':{const file=fd.get('backup_file');if(!file||!file.size)throw Error('Selecciona un respaldo Pulse o un Excel anterior.');if(file.size>6000000)throw Error('El archivo supera 6 MB.');const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(Error('No se pudo leer el archivo.'));reader.readAsDataURL(file);});const report=await api('/api/time-recovery/preview','POST',{content:encoded});timeRecoveryPreview(report,file.name);return;}
    case 'time-recovery-confirm':{const result=await api('/api/time-recovery/'+id+'/confirm','POST',{confirm:fd.has('confirm')});if(result.created&&result.month)month=result.month;$('#modal').close();await refresh();toast(`${result.created} registros recuperados: ${result.submitted} a revisión y ${result.documentation} por documentar. Las horas aún no están aprobadas.`);return;}
    case 'guard':await api('/api/guards','POST',data);month=data.start_date.slice(0,7);break;
    case 'rule':data.segments=$$('[data-rule-day]',f).flatMap(section=>{if(!$('[name=days]',section).checked)return [];const day=Number(section.dataset.ruleDay);return $('[data-full-day]',section).checked?[{day,start:'00:00',end:'00:00'}]:$$('[data-rule-segment]',section).map(row=>({day,start:$('[data-start]',row).value,end:$('[data-end]',row).value}));});await api('/api/rules'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'delegation':data.replace_current=true;await api('/api/delegations','POST',data);delegationDraftLead='';break;
    case 'reject':{const [recordType,identity]=id.split(':');await api(`/api/approvals/${recordType}/${identity}`,'POST',{decision:'REJECTED',reason:data.reason});break;}
    default:return;
  }
  $('#modal').close();await refresh();toast('Cambios guardados.');
}
function bind(){
  document.addEventListener('dragstart',event=>{const card=event.target.closest('.team-tech-card');if(!card||!isManager())return;teamBoardDrag=card.dataset.teamPerson;event.dataTransfer.setData('text/plain',teamBoardDrag);event.dataTransfer.effectAllowed='move';card.classList.add('team-card-dragging');});
  document.addEventListener('dragover',event=>{if(!teamBoardDrag)return;const lane=event.target.closest('[data-team-destination]');if(lane&&lane.dataset.teamDestination!==person(teamBoardDrag)?.group_id){event.preventDefault();event.dataTransfer.dropEffect='move';$$('.team-lane').forEach(n=>n.classList.toggle('team-lane-target',n===lane));}});
  document.addEventListener('drop',event=>{if(!teamBoardDrag)return;const lane=event.target.closest('[data-team-destination]'),id=teamBoardDrag;teamBoardDrag='';$$('.team-lane').forEach(n=>n.classList.remove('team-lane-target'));$$('.team-card-dragging').forEach(n=>n.classList.remove('team-card-dragging'));if(lane&&lane.dataset.teamDestination!==person(id)?.group_id){event.preventDefault();teamMoveModal(id,lane.dataset.teamDestination);}});
  document.addEventListener('dragend',()=>{teamBoardDrag='';$$('.team-lane-target,.team-card-dragging').forEach(n=>n.classList.remove('team-lane-target','team-card-dragging'));});

  document.addEventListener('keydown',event=>{
    if(event.target.id!=='organization-search'||!groupSearchPopup)return;
    const results=$$('[role=option]',groupSearchPopup);
    if(event.key==='Escape'){event.preventDefault();closeGroupSearch();}
    else if((event.key==='ArrowDown'||event.key==='ArrowUp')&&results.length){event.preventDefault();groupSearchIndex=groupSearchIndex<0?(event.key==='ArrowDown'?0:results.length-1):(groupSearchIndex+(event.key==='ArrowDown'?1:-1)+results.length)%results.length;results.forEach((r,i)=>r.setAttribute('aria-selected',String(i===groupSearchIndex)));event.target.setAttribute('aria-activedescendant',results[groupSearchIndex].id);}
    else if(event.key==='Enter'&&results.length){event.preventDefault();openSearchedGroup(results[Math.max(0,groupSearchIndex)].dataset.id);}
  });
  document.addEventListener('focusin',event=>{if(groupSearchPopup&&!event.target.closest('.organization-finder,.group-search-popup'))closeGroupSearch();});

  document.addEventListener('dragstart',event=>{const card=event.target.closest('.organizer-tech[draggable=true]');if(!card||!organizer)return;organizerDrag=card.dataset.boardPerson;event.dataTransfer.setData('text/plain',organizerDrag);event.dataTransfer.effectAllowed='move';});
  document.addEventListener('dragover',event=>{if(!organizerDrag||!organizer)return;const lane=event.target.closest('[data-board-group]');if(lane){event.preventDefault();event.dataTransfer.dropEffect='move';}});
  document.addEventListener('drop',event=>{if(!organizerDrag||!organizer)return;const lane=event.target.closest('[data-board-group]');if(lane){event.preventDefault();const id=organizerDrag;organizerDrag=null;stageOrganizerMove(id,lane.dataset.boardGroup);}});
  document.addEventListener('dragend',()=>organizerDrag=null);
  document.addEventListener('dragstart',startTechnicianDrag);
  document.addEventListener('dragend',endTechnicianDrag);
  document.addEventListener('dragover',event=>{
    if(!draggedTechnician||!isAdmin())return;
    const target=event.target.closest('[data-drop-group],[data-drop-picker]');if(!target)return;
    event.preventDefault();$$('.drop-ready,.drop-invalid').forEach(n=>n.classList.remove('drop-ready','drop-invalid'));
    const problem=target.hasAttribute('data-drop-picker')?'':transferProblem(person(draggedTechnician),group(target.dataset.dropGroup));
    target.dataset.dropHint=problem||'Suelta para revisar el traslado';target.classList.add(problem?'drop-invalid':'drop-ready');event.dataTransfer.dropEffect=problem?'none':'move';
  });
  document.addEventListener('drop',event=>{
    const target=event.target.closest('[data-drop-group],[data-drop-picker]');if(!draggedTechnician||!target||!isAdmin())return;
    event.preventDefault();const id=draggedTechnician,destination=target.dataset.dropGroup;endTechnicianDrag();
    transferModal(id,false,destination||'');
  });
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&draggedTechnician)endTechnicianDrag();});
  document.addEventListener('keydown',event=>{if(!entityPopup)return;if(event.key==='Escape'){event.preventDefault();closeEntityMenu(true);}else if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();const buttons=$$('button',entityPopup),index=buttons.indexOf(document.activeElement);buttons[(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length]?.focus();}});
  document.addEventListener('focusin',event=>{if(entityPopup&&!entityPopup.contains(event.target)&&event.target!==entityPopupTrigger)closeEntityMenu();});
  window.addEventListener('resize',()=>{closeGroupSearch();closeEntityMenu();if(draggedTechnician)endTechnicianDrag();if(organizer)paintOrganizer();});
  document.addEventListener('click',async event=>{
    if(!event.target.closest('.organization-finder,.group-search-popup'))closeGroupSearch();
    if(!event.target.closest('.entity-popup,[data-action=entity-menu]'))closeEntityMenu();
    const target=event.target.closest('[data-page],[data-action]');if(!target||busy)return;
    event.preventDefault();busy=true;target.disabled=true;target.setAttribute('aria-busy','true');
    try{if(target.dataset.page){if(target.dataset.page==='organization'){adminAccountId='';adminAttention='';}await navigate(target.dataset.page);}else await perform(target.dataset.action,target.dataset.id||'',target);}catch(error){toast(error.message,true);}finally{busy=false;if(target.isConnected){target.disabled=false;target.removeAttribute('aria-busy');}}
  });
  document.addEventListener('submit',async event=>{
    const f=event.target.closest('[data-form]');if(!f)return;event.preventDefault();if(f.dataset.form==='ot')syncOtType();if(busy||!PulseLayout.validate(f))return;
    busy=true;const button=$('[type="submit"], button:not([type])',f),buttonContent=button?.innerHTML;const isAccess=f.classList.contains('access-form');if(button){button.disabled=true;if(isAccess)button.innerHTML='<span class="access-spinner" aria-hidden="true"></span> Procesando…';}f.setAttribute('aria-busy','true');const err=$('.form-error',f);if(err)err.textContent='';
    try{await submitForm(f);}catch(error){if(err&&err.isConnected){err.textContent=error.message;err.tabIndex=-1;err.focus({preventScroll:true});PulseLayout.reveal(err);}else toast(error.message,true);}finally{busy=false;f.removeAttribute('aria-busy');if(button?.isConnected){button.disabled=false;if(isAccess)button.innerHTML=buttonContent;}}
  });
  document.addEventListener('change',async event=>{
    const target=event.target,f=target.closest('form');
    if(f?.dataset.form==='transfer-request'&&target.name==='request_group'){const g=group(target.value),input=f.elements.destination;$('#request-custom-destination').hidden=!!g;input.value=g?entityCode(g)+' · '+g.name:'';$('#request-route-target').textContent=g?g.name:'Otro Grupo o Manager';requestAnimationFrame(()=>PulseLayout.dialog());return;}
    if(f?.dataset.form==='team-relocate'){if(target.name==='move_account')filterMoveManagers();else if(['target_manager_id','group_id'].includes(target.name))updateMoveSummary();}
    if(target.name==='bulk_destination'&&target.value){$$('[name^="transfer:"]',target.form).forEach(input=>input.value=target.value);return;}
    if(target.id==='admin-country'){adminCountry=target.value;paintAdminResults();return;}
    if(target.hasAttribute('data-manager-jump')){const account=$('[data-account="'+target.dataset.managerJump+'"]'),node=target.value==='__unassigned'?$('.unassigned',account):$('[data-manager="'+target.value+'"]',account);PulseLayout.reveal(node);return;}
    if(organizer&&['board-source','board-destination'].includes(target.name)){const side=target.name.slice(6),old=organizer[side];organizer[side]=target.value;if(organizer.source===organizer.destination)organizer[side==='source'?'destination':'source']=old;organizer.pages={source:0,destination:0};paintOrganizer();return;}
    if(f?.dataset.form==='guard')syncGuardDates();
    if(f?.dataset.form==='ot')syncOtType();
    if(target.closest('[data-rule-day]')){syncRuleDay(target.closest('[data-rule-day]'));if(target.type==='checkbox')refitRuleEditor();}
    if(f?.dataset.form==='account')syncAccountCode();
    if(f?.dataset.form==='group'){if(target.name==='account_id')f.elements.manager_id.innerHTML=managerOptions(target.value,'');syncGroupCode();}
    if(f?.dataset.form==='person'&&target.name==='account_id'&&$('#group-checks'))$('#group-checks').innerHTML=groupCheckboxes(target.value,f.dataset.id);
    if(f?.dataset.form==='person'&&['group_id','manager_id','is_lead'].includes(target.name)){if(f.dataset.originalGroup&&f.elements.transfer_reason){const reason=f.elements.transfer_reason,changed=f.elements.group_id.value!==f.dataset.originalGroup;reason.closest('.field').hidden=!changed;reason.disabled=!changed;reason.required=changed;requestAnimationFrame(()=>PulseLayout.dialog());}syncLeadOption();if(f.dataset.originalManager)requestAnimationFrame(()=>PulseLayout.dialog());}
    if(f?.dataset.form==='transfer'&&target.name==='group_id')$('#transfer-destination').innerHTML=transferDestinationCard(group(target.value));
    try{
      if(target.hasAttribute('data-preview-month')){if(!target.value)return;month=target.value;await loadLedger();render();calendarPreviewModal();return;}
      if(target.id==='analytics-rank-metric'){analyticsRankMetric=target.value;render();PulseLayout.reveal($('#analytics-rankings'));return;}
      if(target.id==='month'){if(!target.value)return;month=target.value;if(['analytics','myAnalytics','records','myRecords'].includes(page))filters.period='MONTH';await loadLedger();render();}
      if(target.name?.startsWith('filter-')){const key=target.name.slice(7);filters[key]=target.value;if(key==='group')filters.person='';await loadLedger();render();}
    }catch(error){toast(error.message,true);}
  });
  document.addEventListener('input',event=>{
    if(organizer&&event.target.id==='organizer-search'){organizer.query=event.target.value;organizer.pages={source:0,destination:0};paintOrganizer();return;}
    if(organizer&&event.target.id==='organizer-reason'){organizer.reason=event.target.value;return;}
    if(event.target.closest('[data-rule-day]'))syncRuleDay(event.target.closest('[data-rule-day]'));
    if(event.target.closest('[data-form=account]'))syncAccountCode();
    if(event.target.closest('[data-form=group]'))syncGroupCode();
    if(event.target.id==='analytics-search'){const previous=filters.search;filters.search=event.target.value;clearTimeout(analyticsSearchTimer);analyticsSearchTimer=setTimeout(runAnalyticsSearch,350);}

    if(event.target.id==='organization-search')searchGroups(event.target.value);
    if(event.target.id==='move-manager-search'){filterMoveManagers();return;}
    if(event.target.id==='team-board-search'){teamBoardQuery=event.target.value;filterTeamBoard();return;}
    if(event.target.id==='admin-search'){adminQuery=event.target.value;paintAdminResults();}
    if(event.target.closest('[data-form=guard],[data-form=guard-revision]'))syncGuardDates();
    if(event.target.closest('[data-form=ot]')){syncOtType();syncActualOtCorrection(event.target);}
    if(event.target.closest('.access-form')){
      const f=event.target.form;
      if(event.target.name==='identity')accessDraft.identity=event.target.value;
      if(f?.elements.password){const password=f.elements.password.value,confirm=f.elements.confirm.value;f.querySelector('[data-password-check="length"]')?.classList.toggle('satisfied',password.length>=10);f.querySelector('[data-password-check="match"]')?.classList.toggle('satisfied',confirm.length>0&&password===confirm);}
    }
    if(event.target.id==='team-search'){$$('[data-search-row]').forEach(row=>{row.hidden=!row.dataset.searchRow.includes(event.target.value.trim().toLowerCase());});PulseLayout.filterSearch(event.target.value);}
  });
  $('#modal').addEventListener('close',()=>{if(!$('#modal').open){organizer=null;organizerDrag=null;$('#modal').replaceChildren();setTimeout(()=>{if(renderDeferred&&state&&!busy&&!$('#modal').open)render();},0);}});
  $('#modal').addEventListener('click',event=>{if(event.target===$('#modal')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close();}});
}
bind();
refresh().catch(error=>{if(!state)render();else toast(error.message,true);});
setInterval(tick,1000);
setInterval(()=>{if(state&&!busy&&!draggedTechnician&&!teamBoardDrag&&!document.hidden&&!$('#modal').open&&!$('#delegation-editor')&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))refresh(true);},5000);

function aboutProject(){
  showModal('Acerca de Operational Pulse',`<div class="about-project"><div class="about-brand"><img src="/static/favicon.svg" width="50" height="50" alt=""><div><strong>Operational Pulse</strong><span>Versión 1.0.20 · OT y guardias</span></div>${kyndrylBrand()}</div><p>Control de horas extra (OT) y guardias, con timers, aprobaciones, historial y reportes en un solo lugar.</p><div class="about-divider"></div><p class="eyebrow">AUTORES DEL PROYECTO</p><div class="author-list">${projectAuthors.map(name=>`<article><span class="author-avatar">${esc(name.split(' ').slice(0,2).map(n=>n[0]).join(''))}</span><div><strong>${esc(name)}</strong><small>Autor del proyecto</small></div></article>`).join('')}</div><div class="about-bottom"><span class="live-dot"></span>Una operación más clara, desde el primer día.</div></div><footer class="dialog-footer">${btn('Cerrar','close','','primary')}</footer>`);
}

// Only real interaction renews the idle session; polling and Timer ticks do not.
let lastInteraction=Date.now(),lastActivitySent=0,idleClosing=false,activityTrailing;
async function closeIdleSession(){
 if(!state||idleClosing)return;
 idleClosing=true;refreshSequence++;
 try{await fetch('/api/logout',{method:'POST',credentials:'same-origin'});}finally{
 state=null;page='dashboard';$('#modal').close();render();
 toast('Tu sesión terminó por 5 minutos de inactividad. Inicia sesión nuevamente.',true);idleClosing=false;
 }
}
for(const type of ['pointerdown','pointermove','keydown','input','wheel','touchstart'])document.addEventListener(type,event=>{
 if(!event.isTrusted||!state)return;
 if(Date.now()-lastInteraction>=300000){void closeIdleSession();return;}
 lastInteraction=Date.now();
 clearTimeout(activityTrailing);activityTrailing=setTimeout(()=>{if(state&&!idleClosing)void api('/api/session/activity','POST',{}).catch(()=>{});},1000);
 if(Date.now()-lastActivitySent>30000){lastActivitySent=Date.now();void api('/api/session/activity','POST',{}).catch(()=>{});}
},{passive:true});
setInterval(()=>{if(!state){lastInteraction=Date.now();return;}if(Date.now()-lastInteraction>=300000)void closeIdleSession();},1000);
document.addEventListener('visibilitychange',()=>{if(state&&Date.now()-lastInteraction>=300000)void closeIdleSession();});

// Pointer range selection never intercepts existing records or their Details buttons.
document.addEventListener('pointerdown',event=>{
 const day=event.target.closest('[data-calendar-date]');
 if(!day||event.button!==0||event.pointerType!=='mouse'||busy||$('#modal').open||event.target.closest('.calendar-event,.calendar-more'))return;
 calendarDrag={start:day.dataset.calendarDate,end:day.dataset.calendarDate,x:event.clientX,y:event.clientY,moved:false,pointer:event.pointerId};
});
document.addEventListener('pointermove',event=>{
 if(!calendarDrag||event.pointerId!==calendarDrag.pointer)return;
 const day=document.elementFromPoint(event.clientX,event.clientY)?.closest('[data-calendar-date]');
 if(!day)return;
 if(Math.hypot(event.clientX-calendarDrag.x,event.clientY-calendarDrag.y)>5)calendarDrag.moved=true;
 if(calendarDrag.moved){calendarDrag.end=day.dataset.calendarDate;paintCalendarRange(calendarDrag.start,calendarDrag.end);}
});
document.addEventListener('pointerup',event=>{
 if(!calendarDrag||event.pointerId!==calendarDrag.pointer)return;
 const selection=calendarDrag;calendarDrag=null;
 if(selection.moved&&selection.start!==selection.end&&document.elementFromPoint(event.clientX,event.clientY)?.closest('[data-calendar-date]')){calendarSuppressClickUntil=Date.now()+350;calendarGuardRange(selection.start,selection.end);}
 else if(!calendarRangeMode)resetCalendarRange();
});
document.addEventListener('pointercancel',()=>{calendarDrag=null;resetCalendarRange();});
document.addEventListener('click',event=>{
 if(Date.now()<calendarSuppressClickUntil){const inside=event.target.closest('.monthly-calendar');calendarSuppressClickUntil=0;if(inside){event.preventDefault();event.stopImmediatePropagation();}}
},true);
document.addEventListener('keydown',event=>{if(event.key==='Escape'){calendarDrag=null;calendarRangeMode=false;resetCalendarRange();$('[data-action=calendar-range]')?.setAttribute('aria-pressed','false');}});

let calendarPreviewResize;
window.addEventListener('resize',()=>{if(!$('#modal')?.open||!$('#modal').classList.contains('calendar-preview-dialog'))return;clearTimeout(calendarPreviewResize);calendarPreviewResize=setTimeout(()=>{if($('#modal')?.open&&$('#modal').classList.contains('calendar-preview-dialog'))calendarPreviewModal();},80);});
