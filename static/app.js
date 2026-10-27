'use strict';
// One state owner, one central route, one event controller. No route changes on polling.
let state = null;
let page = 'dashboard';
let month = new Date().toLocaleDateString('sv-SE', {timeZone:'America/Mexico_City'}).slice(0,7);
let ledger = {rows:[],ot_minutes:0,guard_minutes:0};
let analyticsReport = null;
let analyticsDetailType = null;
let reportSequence = 0;
const analyticsTypes = ['EMERGENCY','PLANNED','HISTORICAL','GUARD'];
const analyticsNames = {EMERGENCY:'OT emergente',PLANNED:'OT programada',HISTORICAL:'OT histórica',GUARD:'Guardia neta',ALL:'Todas las horas'};
const analyticsColors = {EMERGENCY:'#2469cf',PLANNED:'#24a8ca',HISTORICAL:'#758cba',GUARD:'#25b4a4'};
let filters = {group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};
let delegationDraftLead = '';
let busy = false;
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
const me = () => state?.user;
const isAdmin = () => me()?.role==='ADMIN';
const isManager = () => me()?.role==='MANAGER';
const isTech = () => me()?.role==='USER';
const roles = {ADMIN:'Administrador',MANAGER:'Manager',USER:'Técnico'};
const statuses = {ACTIVE:'Activo',DISABLED:'Baja',PENDING_ACTIVATION:'Activación pendiente',SUBMITTED:'Pendiente',APPROVED:'Aprobado',REJECTED:'Rechazado',DOCUMENTATION:'Por documentar',RUNNING:'En curso',SCHEDULED:'Programado',COMPLETED:'Finalizado',PENDING:'Pendiente',ISSUED:'Código emitido',USED:'Recuperado',CANCELLED:'Cancelado',EXPIRED:'Vencido'};
const pageNames = {dashboard:'Panel',analytics:'Analítica del equipo',myAnalytics:'Mi resumen',organization:'Organización',admins:'Administradores',recoveries:'Recuperación de acceso',profile:'Mi perfil',team:'Mi equipo',teamTime:'Tiempo del equipo',timeRules:'Reglas de guardia',time:'Mi tiempo',claim:'Claim',adp:'ADP'};
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
const btn = (text,action,id='',cls='secondary') => `<button class="${cls}" data-action="${action}" data-id="${esc(id)}">${text}</button>`;
const field = (name,label,value='',type='text',attrs='') => `<label class="field"><span>${label}</span><input name="${name}" type="${type}" value="${esc(value)}" ${attrs}></label>`;
const select = (name,label,html,attrs='') => `<label class="field"><span>${label}</span><select name="${name}" ${attrs}>${html}</select></label>`;
const options = (items,current,label=x=>x.name,empty='') => (empty?`<option value="">${empty}</option>`:'')+items.map(x=>`<option value="${esc(x.id)}" ${x.id===current?'selected':''}>${esc(label(x))}</option>`).join('');
const empty = (title,copy='') => `<div class="empty"><span class="empty-icon">◇</span><h3>${title}</h3>${copy?`<p>${copy}</p>`:''}</div>`;
const identity = p => `<span class="avatar">${esc(initials(p))}</span><span class="identity"><strong>${esc(full(p))}</strong><small>${esc(p.employee_id||p.username)}</small></span>`;
const heading = (eyebrow,title,copy,actions='') => `<header class="page-heading"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p>${copy}</p></div><div class="heading-actions">${actions}</div></header>`;
const monthLabel = value => new Date(`${value}-15T12:00:00`).toLocaleDateString('es-MX',{month:'long',year:'numeric'});
const monthControl = () => `<div class="month-control">${btn('‹','month-prev','','icon-btn')}<label><span class="sr-only">Mes de consulta</span><input type="month" id="month" value="${esc(month)}" aria-label="Mes de consulta"></label>${btn('›','month-next','','icon-btn')}</div>`;

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
  const modal=$('#modal');modal.innerHTML=`<header class="dialog-header"><div><p class="eyebrow">OPERATIONAL PULSE</p><h2 id="dialog-title">${title}</h2></div><button class="icon-btn" data-action="close" aria-label="Cerrar">×</button></header>${body}`;modal.className=wide?'wide':'';modal.setAttribute('aria-labelledby','dialog-title');if(!modal.open)modal.showModal();
}
const formGuidance={account:'Define un código único y un nombre para identificar la Cuenta.',group:'Selecciona la Cuenta y su Manager. Los cambios de responsable requieren un motivo y conservan el equipo.',person:'Completa la identidad y la asignación. Sólo Admin administra personas; los nuevos accesos requieren activación.',ot:'Indica el periodo y documenta la actividad. Revisa los datos antes de enviarlos a aprobación.',guard:'Selecciona las fechas y la regla de cobertura. La OT aprobada se descontará de la Guardia.',rule:'Configura uno o varios intervalos por día. Usa 24 horas para cobertura continua.',window:'Define el Grupo, el periodo y la actividad compartida. Cada Técnico registrará su participación.',reject:'Explica qué debe corregirse. El registro conservará el motivo en su historial.',transfer:'Elige el Grupo de destino y explica el movimiento. La persona permanece activa; su sesión se cerrará para actualizar el acceso.', 'group-transfer':'Elige un Manager activo de la misma Cuenta. El equipo y sus registros permanecen; la delegación anterior se revoca.',offboard:'Resuelve los destinos y pendientes antes de retirar el acceso.',reactivate:'Explica el motivo. Comparte el código nuevo por un canal corporativo para que la persona active su acceso.'};
function form(name,body,id='',submit='Guardar'){
  return `<form data-form="${name}" data-id="${esc(id)}"><div class="form-body">${formGuidance[name]?`<p class="form-instructions"><strong>Cómo completar este paso</strong>${formGuidance[name]}</p>`:''}${body}</div><p class="form-error" role="alert"></p><footer class="dialog-footer"><button type="button" class="secondary" data-action="close">Cancelar</button><button class="primary" type="submit">${submit}</button></footer></form>`;
}
function credentials(code,username,title='Datos de activación'){
  showModal(title,`<div class="form-body"><p>Entrega este código por un canal corporativo. La persona definirá su contraseña desde «Activar cuenta».</p>${username?`<p>Usuario: <strong>${esc(username)}</strong></p>`:''}<div class="secret-code">${esc(code)}</div><p class="muted">El código se muestra sólo al generar o regenerar el acceso.</p></div><footer class="dialog-footer">${btn('Listo','close','','primary')}</footer>`);
}
function login(){
  return `<div class="login-shell"><section class="login-story"><a class="brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>Operational<span class="brand-light">Pulse</span></span></a><div class="story-copy"><p class="eyebrow">CONTROL DE TIEMPO EXTRA</p><h1>Planea.<br>Trabaja. Controla.</h1><p>Registra tiempo extra, gestiona guardias<br>y consulta tus horas aprobadas.</p><div class="pulse-line"><span></span><i></i><span></span></div></div><footer><div class="login-brand-credit">${kyndrylBrand()}<span>Operación conectada. Mejores resultados.</span></div><span class="release-tag">v1.3.1</span></footer></section><main class="login-main"><div class="login-card"><p class="eyebrow">ACCESO A OPERATIONAL PULSE</p><h2>Control de OT y guardias</h2><p class="muted">Ingresa con tu Employee ID o usuario administrador.</p><form data-form="login">${field('identity','Usuario o Employee ID','','text','required autocomplete="username"')}<label class="field" for="login-password"><span>Contraseña</span><span class="login-password-input"><input id="login-password" name="password" type="password" required autocomplete="current-password"><button type="button" class="password-visibility" data-action="password-visibility" data-id="login-password" aria-label="Mostrar contraseña" aria-pressed="false">${icon('eye')}</button></span></label><p class="form-error" role="alert"></p><button type="submit" class="primary login-submit">Iniciar sesión <span>→</span></button></form><div class="login-links">${btn('¿Olvidaste tu contraseña?','recovery-request','','link')}${btn('Activar cuenta','activate','','link')}</div><div class="login-note"><span>◇</span><p>Acceso interno<br><small>Control de OT, guardias y aprobaciones.</small></p></div></div><footer>Operational Pulse · OT y guardias <button class="link" data-action="about">Acerca del proyecto</button></footer></main></div>`;
}
function nav(){
  const items=isAdmin()?['dashboard','organization','admins','recoveries','profile']:isManager()?['dashboard','team','teamTime','analytics','timeRules','recoveries','profile']:['dashboard','time','myAnalytics','claim','adp',...(state.can_approve?['team','teamTime','analytics']:[]),'profile'];
  return `<aside class="sidebar"><a class="brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>Operational<span class="brand-light">Pulse</span></span></a><p class="nav-label">ESPACIO DE TRABAJO</p><nav aria-label="Navegación principal">${items.map(p=>`<button class="nav-item ${p===page?'active':''}" data-page="${p}" ${p===page?'aria-current="page"':''}><span aria-hidden="true">${icon(p)}</span>${pageNames[p]}${p==='teamTime'&&pendingCount()?`<b>${pendingCount()}</b>`:''}</button>`).join('')}</nav><div class="sidebar-bottom"><div class="sidebar-brand">${kyndrylBrand()}<span>Espacio de operación digital</span></div><div class="workspace-tag"><i></i>Operación conectada<small>Operational Pulse · v${esc(state.version)}</small></div>${btn(icon('arrow')+'Cerrar sesión','logout','','logout')}</div></aside>`;
}
function pendingCount(){return state?[...state.overtime,...state.guards].filter(r=>r.status==='SUBMITTED'&&r.user_id!==me().id).length:0;}
function content(){
  switch(page){
    case 'analytics':return analyticsPage(false);
    case 'myAnalytics':return analyticsPage(true);
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
  return `<div class="shell">${nav()}<div class="workspace"><header class="topbar"><div class="breadcrumb"><span class="breadcrumb-home">${icon("dashboard")}</span> Espacio de trabajo <span>/</span> <strong>${pageNames[page]||'Panel'}</strong></div><div class="topbar-right"><div class="clock-block"><small>HORA LOCAL · MX</small><span class="local-time" data-local-clock></span></div><div class="topbar-person">${identity(me())}<span class="role-label">${roles[me().role]}${me().is_lead?' · Lead':''}</span></div></div></header><main id="main" tabindex="-1">${content()}<footer class="main-footer"><span>Operational Pulse <b class="footer-version">v${esc(state.version)}</b></span><button class="link" data-action="about">${icon("info")} Acerca del proyecto y autores</button></footer></main></div></div>`;
}
function render(){
  $('#app').innerHTML=state?app():login();tick();
}
async function loadLedger(){
  if(!state)return;
  const sequence=++reportSequence,reportPage=page,q=new URLSearchParams({month});
  if(['dashboard','time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);
  else if(page!=='myAnalytics'){if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);}
  if(['analytics','myAnalytics'].includes(reportPage)){
    try{
      const report=await api((reportPage==='myAnalytics'?'/api/my-analytics?':'/api/analytics?')+q);
      if(sequence!==reportSequence||page!==reportPage)return;
      analyticsReport=report;ledger={rows:report.rows,ot_minutes:report.summary.ot_minutes,guard_minutes:report.summary.GUARD};
    }catch(error){
      if(error.status===403&&reportPage==='analytics'){
        analyticsReport=null;analyticsDetailType=null;state=await api('/api/state');page=isTech()?'myAnalytics':'dashboard';filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};await loadLedger();render();
      }
      throw error;
    }
  }else{
    const result=await api('/api/accounting?'+q);if(sequence===reportSequence&&page===reportPage)ledger=result;
  }
}

async function refresh(silent=false){
  const sequence=++refreshSequence;
  try{
    const fresh=await api('/api/state');if(sequence!==refreshSequence)return;
    serverOffset=new Date(fresh.server_time).getTime()-Date.now();
    const previous=state?JSON.stringify({...state,server_time:''}):'';
    state=fresh;
    const lostAnalytics=page==='analytics'&&!isManager()&&!fresh.can_approve;
    if(lostAnalytics){page=isTech()?'myAnalytics':'dashboard';analyticsReport=null;analyticsDetailType=null;filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};}
    await loadLedger();if(sequence!==refreshSequence)return;
    if(!silent||lostAnalytics||previous!==JSON.stringify({...state,server_time:''})){
      if(!silent||lostAnalytics||!$('#modal').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))render();
    }
  }catch(error){if(!silent)throw error;}
}
async function navigate(next){
  if(!state)return;page=next;filters={group:'',person:'',status:'',kind:'',search:'',period:'MONTH'};delegationDraftLead='';analyticsDetailType=null;
  $('#modal').close();await loadLedger();render();$('#main')?.focus({preventScroll:true});
}
function tick(){
  const code=$('[data-code-expires]');if(code&&new Date(code.dataset.codeExpires).getTime()<=Date.now()+serverOffset){code.textContent='Código vencido';code.removeAttribute('data-code-expires');}
  $$('[data-elapsed]').forEach(el=>{const total=Math.max(0,Math.floor((Date.now()+serverOffset-new Date(el.dataset.elapsed).getTime())/1000));el.textContent=[Math.floor(total/3600),Math.floor(total/60)%60,total%60].map(x=>String(x).padStart(2,'0')).join(':');});
  const clock=$('[data-local-clock]');if(clock)clock.textContent=new Date(Date.now()+serverOffset).toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',timeZone:state.timezone});
}
function kpi(label,value,detail,symbol,accent='',target=''){
  const tag=target?'button':'article',attrs=target?`type="button" data-action="dashboard-drill" data-id="${target}"`:'';
  return `<${tag} class="kpi ${accent} ${target?'kpi-link':''}" ${attrs}><div><span>${label}</span><i>${icon(({'⌘':'organization','♧':'team','▦':'dashboard','◎':'profile','↗':'arrow','◷':'time','≡':'teamTime','●':'time'})[symbol]||'dashboard')}</i></div><strong>${value}</strong><small>${detail}${target?icon('arrow'):''}</small></${tag}>`;
}

function dashboard(){
  if(isAdmin()){
    return heading('VISTA GENERAL','Todo empieza con tu equipo.','Organiza personas y responsabilidades para que la operación fluya.',btn('＋ Crear cuenta','account-new','','primary'))+
    `<section class="welcome-banner"><div><span class="pill">ADMINISTRACIÓN</span><h2>Una estructura clara.<br>Un equipo conectado.</h2><p>De la Cuenta al Técnico: cada persona en su lugar.</p><button class="primary light" data-page="organization">Explorar organización <span>${icon("arrow")}</span></button></div><div class="org-illustration" aria-hidden="true"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="visual-center">${icon('organization')}<span>Una sola operación</span><strong>Todo conectado.</strong></div><div class="visual-chip chip-top">${icon('team')}<span>Personas</span><i></i></div><div class="visual-chip chip-left">${icon('time')}<span>Tiempo</span><i></i></div><div class="visual-chip chip-bottom">${icon('check')}<span>Decisiones</span><i></i></div></div></section>
    <section class="kpis">${kpi('Cuentas',state.accounts.length,'La base de tu estructura','⌘')}${kpi('Managers',state.people.filter(p=>p.role==='MANAGER').length,'Responsables de la operación','♧')}${kpi('Grupos',state.groups.length,'Equipos conectados','▦')}${kpi('Técnicos',state.people.filter(p=>p.role==='USER').length,`${state.people.filter(p=>p.is_lead).length} con capacidad Lead`,'◎')}</section>
    <section class="two-columns"><article class="panel"><div class="section-heading"><div><p class="eyebrow">PRÓXIMOS PASOS</p><h2>Construye tu organización</h2></div></div><div class="step-row"><span>01</span><div><strong>Crea una Cuenta operativa</strong><small>Define el nombre y el código de tu operación.</small></div>${btn('Crear','account-new','','link')}</div><div class="step-row"><span>02</span><div><strong>Conecta Managers y Grupos</strong><small>Asigna responsabilidades dentro de cada Cuenta.</small></div><button class="link" data-page="organization">Organizar</button></div><div class="step-row"><span>03</span><div><strong>Incorpora a tus Técnicos</strong><small>Asigna su Grupo y, si corresponde, capacidad Lead.</small></div><button class="link" data-page="organization">Agregar</button></div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">ACCESOS</p><h2>Atención pendiente</h2></div></div><div class="attention-number">${state.recoveries.filter(r=>r.status==='PENDING').length}<small>solicitudes de recuperación</small></div><button class="secondary" data-page="recoveries">Revisar solicitudes →</button><p class="muted footnote">La información aparece cuando tu equipo comienza a trabajar. Sin datos de demostración.</p></article></section>`;
  }
  const ownTimers=state.timers.filter(t=>t.user_id===me().id),reviewer=isManager();
  return heading('TU OPERACIÓN AL DÍA',`Hola, ${esc(me().first)}.`,isTech()?'Tu OT, tus guardias y sus aprobaciones del mes.':'Un vistazo al tiempo y las prioridades de tu equipo.',monthControl())+
  (ownTimers.length?timerPanel(ownTimers):'')+
  `<section class="kpis">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real, sin duplicados','↗','',reviewer?'ot':'')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Con OT descontada','◷','',reviewer?'guard':'')}${kpi('Por revisar',reviewer?pendingCount():state.overtime.filter(o=>o.user_id===me().id&&o.status==='SUBMITTED').length,'Solicitudes pendientes','≡','',reviewer?'pending':'')}${kpi('Timers activos',isTech()?ownTimers.length:state.timers.length,'Actualización en tiempo real','●','accent',reviewer?'running':'')}</section>
  <section class="two-columns"><article class="panel"><div class="section-heading"><div><p class="eyebrow">ANALÍTICA MENSUAL</p><h2>${esc(monthLabel(month))}</h2></div><span class="pill">Horas aprobadas</span></div>${analyticsChart()}<div class="legend"><span><i class="dot ot"></i>Tiempo extra</span><span><i class="dot guard"></i>Guardia neta</span></div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">REQUIERE TU ATENCIÓN</p><h2>${isTech()?'El siguiente paso':'Solicitudes para revisar'}</h2></div></div>${isTech()?`<div class="attention-number">${state.overtime.filter(o=>o.user_id===me().id&&o.status==='DOCUMENTATION').length}<small>registros por documentar</small></div><button class="secondary" data-page="time">Ir a Mi tiempo →</button>`:dashboardPriorities()}${isTech()?'<div class="quick-note">Claim, ADP y Excel se calculan sobre el mismo tiempo aprobado.</div>':''}</article></section>
  ${state.timers.length&&!isTech()?`<article class="panel"><div class="section-heading"><div><p class="eyebrow">AHORA</p><h2>Tu equipo en tiempo real</h2></div><span class="live-label"><i></i>En vivo</span></div>${timerPanel(state.timers)}</article>`:''}`;
}
function dashboardPriorities(){
  const pending=[...state.overtime.map(o=>({...o,kind:'ot'})),...state.guards.map(g=>({...g,kind:'guard'}))].filter(r=>r.status==='SUBMITTED'&&r.execution!=='RUNNING'&&r.user_id!==me().id).sort((a,b)=>a.created_at.localeCompare(b.created_at));
  if(!pending.length)return empty('Sin solicitudes por revisar','Las solicitudes de tu equipo aparecerán aquí cuando requieran una decisión.');
  return `<div class="priority-list">${pending.slice(0,3).map(r=>`<article><span class="priority-icon">${icon(r.kind==='ot'?'time':'adp')}</span><div><strong>${esc(full(person(r.user_id)))}</strong><small>${r.kind==='ot'?esc(r.reference||'Tiempo extra'):esc(r.rule_snapshot.name)} · ${fmtDate(r.created_at)}</small></div>${btn('Revisar','record-detail',r.kind+':'+r.id,'link')}</article>`).join('')}</div>${pending.length>3?btn('Ver todas las solicitudes','dashboard-drill','pending','secondary small'):''}`;
}
function analyticsChart(){
  const byDay=new Map();ledger.rows.forEach(r=>{const day=Number(r.date.slice(-2));if(!byDay.has(day))byDay.set(day,{OT:0,GUARD:0});byDay.get(day)[r.kind]+=r.minutes/60;});
  if(!byDay.size)return empty('Tu mes está por comenzar','Aquí verás las horas aprobadas de tu operación.');
  const days=new Date(Number(month.slice(0,4)),Number(month.slice(5)),0).getDate();
  const max=Math.max(1,...[...byDay.values()].map(d=>d.OT+d.GUARD));
  // SVG keeps the visualization self-contained and avoids inline styles under CSP.
  let bars='';for(let d=1;d<=days;d++){const v=byDay.get(d)||{OT:0,GUARD:0},x=14+(d-1)*17,h1=v.OT/max*130,h2=v.GUARD/max*130;bars+=`<rect x="${x}" y="${150-h1}" width="10" height="${h1}" rx="2" fill="#2469cf"><title>${d}: ${v.OT.toFixed(2)} h OT</title></rect><rect x="${x}" y="${150-h1-h2}" width="10" height="${h2}" rx="2" fill="#28c7c5"><title>${d}: ${v.GUARD.toFixed(2)} h Guardia</title></rect>${d===1||d%5===0?`<text x="${x+5}" y="172" text-anchor="middle" fill="#536a85" font-size="10">${d}</text>`:''}`;}
  return `<div class="chart"><svg role="img" aria-label="Horas aprobadas por día, tiempo extra y Guardia neta" viewBox="0 0 545 185"><path d="M8 150H540" stroke="#e1e7e5"/>${bars}</svg></div>`;
}
function analyticsExportLink(personal){
  const q=new URLSearchParams({month});if(!personal){if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);}
  return `<a class="secondary button" download href="${personal?'/api/my-analytics.xlsx?':'/api/analytics.xlsx?'}${esc(q.toString())}">${icon('download')} Exportar analítica</a>`;
}
function analyticsPage(personal){
  const report=analyticsReport,correct=report&&report.month===month&&report.mode===(personal?'PERSONAL':'TEAM')&&(personal||report.filters.group_id===(filters.group||null)&&report.filters.user_id===(filters.person||null));
  const header=heading(personal?'TU TIEMPO APROBADO':'HORAS Y DISTRIBUCIÓN',personal?'Mi resumen mensual':'Analítica del equipo',personal?'Tus horas de OT y Guardia, separadas por tipo y día.':'Horas por Grupo, Técnico y tipo de registro. Un mismo cálculo para toda la operación.',monthControl()+analyticsExportLink(personal));
  if(!correct)return header+`<section class="panel">${empty('Cargando el desglose del mes…')}</section>`;
  const groups=state.groups.filter(g=>state.scope.includes(g.id)),people=state.people.filter(p=>p.role==='USER'&&state.scope.includes(p.group_id)&&(!filters.group||p.group_id===filters.group));
  const controls=personal?`<div class="analytics-personal-scope">${icon('profile')}<span>Resumen exclusivo de <strong>${esc(full(me()))}</strong> · ${esc(me().employee_id)}</span><span class="pill">Sólo tus horas</span></div>`:`<section class="panel analytics-filters"><div>${select('filter-group','Grupo',options(groups,filters.group,g=>g.code+' · '+g.name,'Todos mis Grupos'))}${select('filter-person','Técnico',options(people,filters.person,full,'Todos los Técnicos del alcance'))}</div><p>Se muestran únicamente los Grupos bajo tu responsabilidad${isTech()?' delegada y vigente':''}.</p></section>`;
  const metrics=[['ALL','Total aprobado',report.summary.total_minutes],...analyticsTypes.map(type=>[type,analyticsNames[type],report.summary[type]])];
  return header+controls+`<section class="analytics-metrics">${metrics.map(([type,label,minutes])=>`<button type="button" class="analytics-metric metric-${type.toLowerCase()} ${analyticsDetailType===type?'selected':''}" data-action="analytics-records" data-id="${type}" aria-expanded="${analyticsDetailType===type}" aria-controls="analytics-records"><span>${label}</span><strong>${hours(minutes)} <small>h</small></strong><em>Ver detalle ${icon('arrow')}</em></button>`).join('')}</section><div class="analytics-criteria">${icon('info')}<p><strong>Horas reales aprobadas.</strong> Las OT programadas aún sin ejecutar y las solicitudes pendientes no suman horas. Guardia neta descuenta la OT que se traslapa.</p></div><section class="two-columns analytics-charts"><article class="panel"><div class="section-heading"><div><p class="eyebrow">${personal?'COMPOSICIÓN':'DISTRIBUCIÓN POR GRUPO'}</p><h2>${personal?'¿En qué se distribuyen tus horas?':'Horas de tus Grupos'}</h2></div><span class="pill">${esc(monthLabel(month))}</span></div>${personal?analyticsComposition(report.summary):analyticsGroupChart(report.groups)}${analyticsLegend()}</article><article class="panel"><div class="section-heading"><div><p class="eyebrow">EVOLUCIÓN DEL MES</p><h2>Horas por día</h2></div></div>${analyticsDailyChart(report.days)}${analyticsLegend()}</article></section>${personal?'':analyticsGroupTable(report.groups)+analyticsUserTable(report.users)}${analyticsDetailType?analyticsDetailTable(report.rows):''}<p class="analytics-method">Zona operativa: ${esc(report.timezone)}. Los intervalos que cruzan medianoche se dividen por día. ${personal?'Tu resumen no incluye horas de otras personas.':'La agrupación usa el Grupo actual de cada Técnico.'}</p>`;
}
function analyticsLegend(){return `<div class="analytics-legend">${analyticsTypes.map(type=>`<span><i class="analytics-dot type-${type.toLowerCase()}"></i>${analyticsNames[type]}</span>`).join('')}</div>`;}
function analyticsComposition(summary){
  const total=summary.total_minutes;if(!total)return empty('Aún no hay horas aprobadas','Aquí aparecerá el desglose cuando se apruebe tu tiempo real.');
  let x=0;const bars=analyticsTypes.map(type=>{const width=summary[type]/total*500;const rect=`<rect x="${x}" y="0" width="${width}" height="20" fill="${analyticsColors[type]}"><title>${analyticsNames[type]}: ${hours(summary[type])} h</title></rect>`;x+=width;return rect;}).join('');
  return `<div class="composition-total"><strong>${hours(total)} <small>horas</small></strong><span>Tiempo aprobado del mes</span></div><svg class="analytics-composition" viewBox="0 0 500 20" role="img" aria-label="Composición de tus horas aprobadas">${bars}</svg><div class="composition-values">${analyticsTypes.map(type=>`<div><span>${analyticsNames[type]}</span><strong>${hours(summary[type])} h</strong></div>`).join('')}</div>`;
}
function analyticsGroupChart(groups){
  const active=groups.filter(g=>g.minutes.total_minutes>0),max=Math.max(1,...active.map(g=>g.minutes.total_minutes));
  if(!active.length)return empty('Sin horas aprobadas en este mes','Las horas aparecerán cuando el equipo finalice y apruebe sus registros.');
  return `<div class="analytics-ranking">${active.map(g=>{let x=0;const bars=analyticsTypes.map(type=>{const width=g.minutes[type]/max*500;const rect=`<rect x="${x}" y="0" width="${width}" height="10" fill="${analyticsColors[type]}"></rect>`;x+=width;return rect;}).join('');return `<button type="button" data-action="analytics-group" data-id="${esc(g.id)}"><span><strong>${esc(g.code)} · ${esc(g.name)}</strong><small>${hours(g.minutes.total_minutes)} h ${icon('arrow')}</small></span><svg viewBox="0 0 500 10" role="img" aria-label="${esc(g.name)}: ${hours(g.minutes.total_minutes)} horas"><rect width="500" height="10" fill="#eef4fb"/>${bars}</svg></button>`;}).join('')}</div>`;
}
function analyticsDailyChart(days){
  if(!days.length)return empty('El mes, día a día','Sólo el tiempo real aprobado forma parte de esta gráfica.');
  const daily=new Map(days.map(d=>[Number(d.date.slice(-2)),d.minutes])),count=new Date(Number(month.slice(0,4)),Number(month.slice(5)),0).getDate(),max=Math.max(60,...days.map(d=>d.minutes.total_minutes)),step=540/count;
  let bars='';for(let day=1;day<=count;day++){const item=daily.get(day),x=24+(day-1)*step;let y=164;if(item)for(const type of analyticsTypes){const height=item[type]/max*135;y-=height;bars+=`<rect x="${x}" y="${y}" width="${Math.max(5,step-6)}" height="${height}" fill="${analyticsColors[type]}"><title>${day}: ${analyticsNames[type]} ${hours(item[type])} h</title></rect>`;}if(day===1||day%5===0||day===count)bars+=`<text x="${x+4}" y="185" text-anchor="middle" fill="#587394" font-size="10">${day}</text>`;}
  return `<svg class="analytics-daily" viewBox="0 0 580 200" role="img" aria-label="Horas aprobadas por día y tipo"><path d="M20 29H570M20 97H570M20 164H570" stroke="#e6eef7"/><text x="20" y="17" fill="#557293" font-size="10">${hours(max)} h</text>${bars}</svg>`;
}
function analyticsAmountCells(totals){return [...analyticsTypes,'total_minutes'].map(key=>`<td class="numeric ${key==='total_minutes'?'analytics-total':''}">${hours(totals[key])}</td>`).join('');}
function analyticsColumnHeaders(){return analyticsTypes.map(type=>`<th class="numeric"><span class="analytics-dot type-${type.toLowerCase()}"></span>${analyticsNames[type]} <small>h</small></th>`).join('')+'<th class="numeric">Total <small>h</small></th>';}
function analyticsGroupTable(groups){
  return `<section class="panel table-panel"><div class="section-heading padded"><div><p class="eyebrow">POR GRUPO</p><h2>La distribución de tu operación</h2></div><span class="pill">${groups.length} Grupos</span></div><div class="table-scroll"><table class="analytics-table"><thead><tr><th>Grupo</th><th class="numeric">Técnicos</th>${analyticsColumnHeaders()}<th></th></tr></thead><tbody>${groups.map(g=>`<tr><td><strong>${esc(g.name)}</strong><small>${esc(g.code)}</small></td><td class="numeric">${g.user_count}</td>${analyticsAmountCells(g.minutes)}<td>${btn('Ver Técnicos','analytics-group',g.id,'link')}</td></tr>`).join('')}</tbody></table></div>${groups.length?'':empty('No hay Grupos en este alcance')}</section>`;
}
function analyticsUserTable(users){
  return `<section class="panel table-panel" id="analytics-users"><div class="section-heading padded"><div><p class="eyebrow">POR TÉCNICO</p><h2>Las horas de cada persona</h2></div><span class="pill">${users.length} Técnicos</span></div><div class="table-scroll"><table class="analytics-table"><thead><tr><th>Técnico / Grupo</th>${analyticsColumnHeaders()}<th></th></tr></thead><tbody>${users.map(u=>`<tr><td><strong>${esc(u.name)}</strong><small>${esc(u.employee_id)} · ${esc(u.group_name)}</small></td>${analyticsAmountCells(u.minutes)}<td>${btn('Ver horas','analytics-user',u.id,'link')}</td></tr>`).join('')}</tbody></table></div>${users.length?'':empty('No hay Técnicos en este alcance')}</section>`;
}
function analyticsDetailTable(rows){
  const selected=rows.filter(row=>analyticsDetailType==='ALL'||row.capture_type===analyticsDetailType);
  return `<section class="panel table-panel" id="analytics-records"><div class="section-heading padded"><div><p class="eyebrow">DETALLE DE HORAS · ${esc(monthLabel(month))}</p><h2>${analyticsNames[analyticsDetailType]||'Todas las horas'}</h2><p class="muted">Los registros que cruzan medianoche se muestran en tramos por día.</p></div>${btn('Cerrar detalle','analytics-detail-close','','link')}</div><div class="table-scroll"><table><thead><tr><th>Fecha</th><th>Técnico / Grupo</th><th>Tipo</th><th>Horario</th><th>Referencia</th><th class="numeric">Horas</th></tr></thead><tbody>${selected.map(row=>`<tr><td>${fmtDate(row.date)}</td><td><strong>${esc(row.name)}</strong><small>${esc(row.employee_id)} · ${esc(row.group_name)}</small></td><td><span class="analytics-type-label type-${row.capture_type.toLowerCase()}">${analyticsNames[row.capture_type]}</span></td><td>${row.start} — ${row.end}</td><td>${esc(row.reference||'—')}</td><td class="numeric analytics-total">${hours(row.minutes)}</td></tr>`).join('')}</tbody></table></div>${selected.length?'':empty('Sin horas aprobadas de este tipo','Prueba otro mes, Grupo o tipo de registro.')}</section>`;
}

function organizationPage(){
  return heading('PERSONAS Y ESTRUCTURA','Organización','Cada Cuenta, sus Managers y los equipos que hacen que todo suceda.',btn('＋ Nueva cuenta','account-new','','primary'))+
  `<div class="organization-summary"><span><b>${state.accounts.length}</b> Cuentas</span><span><b>${state.people.filter(p=>p.role==='MANAGER').length}</b> Managers</span><span><b>${state.groups.length}</b> Grupos</span><span><b>${state.people.filter(p=>p.role==='USER').length}</b> Técnicos</span><span class="muted">Un Lead por Manager · backup con delegación independiente.</span></div>`+
  (state.accounts.length?state.accounts.map(a=>{
    const groups=state.groups.filter(g=>g.account_id===a.id),managers=state.people.filter(p=>p.role==='MANAGER'&&p.account_id===a.id),techs=state.people.filter(p=>groups.some(g=>g.id===p.group_id)),unassigned=groups.filter(g=>!g.manager_id);
    return `<section class="account-block" data-account="${esc(a.id)}"><header class="account-header"><span class="account-code">${esc(a.code)}</span><div class="grow"><p class="eyebrow">CUENTA OPERATIVA</p><h2>${esc(a.name)}</h2><p>${managers.length} Managers <span>·</span> ${groups.length} Grupos <span>·</span> ${techs.length} Técnicos</p></div><div class="entity-actions">${btn('Editar','account-edit',a.id)}${btn('Eliminar','account-delete',a.id,'text-danger')}${btn('＋ Manager','manager-new',a.id)}${btn('＋ Grupo','group-new',a.id,'primary')}</div></header><div class="account-body">${managers.map(m=>managerBlock(m,groups.filter(g=>g.manager_id===m.id))).join('')}${unassigned.length?`<section class="unassigned"><div class="section-heading"><h3>Grupos sin Manager</h3><span class="pill">Pendientes de asignación</span></div><div class="group-grid">${unassigned.map(groupCard).join('')}</div></section>`:''}${!groups.length&&!managers.length?empty('Una Cuenta lista para crecer','Agrega tu primer Manager o Grupo para comenzar.') : ''}</div></section>`;
  }).join(''):empty('Dale forma a tu operación','Crea tu primera Cuenta. Después podrás agregar Managers, Grupos y Técnicos.'));
}
function managerBlock(m,groups){
  const leads=state.people.filter(p=>p.is_lead&&p.status!=='DISABLED'&&groups.some(g=>g.id===p.group_id));
  const summary=groups.length>1?`Multigrupo · ${groups.length} grupos`:groups.length?'1 grupo':'Sin grupos asignados';
  return `<section class="manager-block" data-manager="${esc(m.id)}"><header class="manager-header">${identity(m)}<div class="manager-meta"><span class="small-label">MANAGER</span><span>${summary}</span>${badge(m.status)}</div><div class="entity-actions">${m.status==='PENDING_ACTIVATION'?btn('Activación','activation-code',m.id,'link'):''}${btn('Editar','person-edit',m.id)}${lifecycleActions(m)}</div></header><p class="manager-backup">${leads.length>1?'⚠ Hay varias designaciones heredadas. Admin debe retirar las adicionales y conservar un solo Lead.':leads.length?`Backup Lead: ${esc(full(leads[0]))} · ${esc(leads[0].employee_id)}`:'Backup Lead: sin designar'}</p><div class="group-grid">${groups.map(groupCard).join('')||empty('Sin Grupos asignados','Edita al Manager para asignar Grupos de esta Cuenta.')}</div></section>`;
}
function groupCard(g){
  const people=state.people.filter(p=>p.role==='USER'&&p.group_id===g.id);
  return `<article class="group-card" data-group="${esc(g.id)}"><header><div><span class="small-label">GRUPO · ${esc(g.code)}</span><h3>${esc(g.name)}</h3><small>${people.length} Técnicos</small></div><div class="entity-actions">${btn('Editar','group-edit',g.id,'link')}${btn('Transferir','group-transfer',g.id,'link')}${btn('Eliminar','group-delete',g.id,'text-danger')}</div></header><div class="technicians">${people.map(u=>`<div class="technician" data-person="${esc(u.id)}">${identity(u)}${u.is_lead?'<span class="lead-pill">Lead</span>':''}${badge(u.status)}<div class="entity-actions">${btn('Editar','person-edit',u.id,'link')}${btn('Transferir','person-transfer',u.id,'link')}${lifecycleActions(u)}</div></div>`).join('')||'<p class="quiet-empty">Aún no hay Técnicos en este Grupo.</p>'}</div><footer>${btn('＋ Agregar Técnico','tech-new',g.id,'link')}</footer></article>`;
}
function adminsPage(){return heading('GOBERNANZA','Administradores','Accesos con autoridad para administrar la estructura y las cuentas.',btn('＋ Administrador','admin-new','','primary'))+peopleTable(state.people.filter(p=>p.role==='ADMIN'));}
function peopleTable(people){
  return `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Persona</th><th>Correo</th><th>Rol / Grupo</th><th>Estado</th><th class="right">Acciones</th></tr></thead><tbody>${people.map(p=>`<tr data-search-row="${esc(`${full(p)} ${p.employee_id||p.username} ${p.email}`.toLowerCase())}"><td><div class="table-identity">${identity(p)}${p.is_lead?'<span class="lead-pill">Lead</span>':''}</div></td><td>${esc(p.email)}</td><td>${esc(p.role==='USER'?group(p.group_id)?.name||'Sin Grupo':roles[p.role])}</td><td>${badge(p.status)}</td><td><div class="row-actions">${isAdmin()?btn('Editar','person-edit',p.id,'link')+lifecycleActions(p):''}${isManager()&&p.is_lead&&p.status==='ACTIVE'?btn(currentDelegation()?.lead_id===p.id?'Editar delegación':'Delegar','delegation-inline',p.id,'secondary small'):''}${isAdmin()&&p.status==='PENDING_ACTIVATION'?btn('Activación','activation-code',p.id,'link'):''}</div></td></tr>`).join('')}</tbody></table></div>${!people.length?empty('Sin personas todavía','Los nuevos integrantes aparecerán aquí.'):''}</section>`;
}
function teamPage(){
  const people=state.people.filter(p=>p.role==='USER'&&state.scope.includes(p.group_id)),current=isManager()?currentDelegation():null;
  return heading('PERSONAS','Mi equipo','Consulta a tus Técnicos y administra la delegación temporal. Las altas y cambios de personas corresponden a Admin.')+
  (isManager()?`<section class="delegation-summary"><span class="delegation-summary-icon">${icon('team')}</span><div><p class="eyebrow">BACKUP DEL MANAGER · UNA PERSONA</p><h3>${current?esc(full(person(current.lead_id))):'Sin delegación asignada'}</h3><p>${current?`${range(current.start_at,current.end_at)} · ${current.group_ids.length} Grupos`:'Elige «Delegar» junto a un Lead activo de tu equipo.'}</p></div>${current?`<span class="pill">${new Date(current.start_at).getTime()>Date.now()+serverOffset?'Programada':'Activa'}</span>${btn('Revocar','delegation-revoke',current.id,'text-danger')}`:''}</section>`:'')+
  `<section class="panel compact"><label class="search"><span>${icon('search')}</span><input id="team-search" placeholder="Buscar por nombre, Employee ID o correo" aria-label="Buscar Técnicos"></label></section>`+peopleTable(people)+
  (isManager()&&delegationDraftLead?inlineDelegationForm(person(delegationDraftLead)):'')+
  (isManager()&&state.delegations.length?`<details class="delegation-history panel"><summary>Historial de delegaciones</summary><div class="delegation-list">${state.delegations.map(d=>`<article><div><strong>${esc(full(person(d.lead_id)))}</strong><small>${range(d.start_at,d.end_at)} · ${d.group_ids.length} Grupos</small></div><span class="pill">${d.revoked_at?'Revocada':new Date(d.end_at).getTime()<=Date.now()+serverOffset?'Finalizada':new Date(d.start_at).getTime()>Date.now()+serverOffset?'Programada':'Activa'}</span></article>`).join('')}</div></details>`:'');
}
function currentDelegation(){
  return state.delegations.filter(d=>d.manager_id===me().id&&!d.revoked_at&&new Date(d.end_at).getTime()>Date.now()+serverOffset).at(-1)||null;
}
function inlineDelegationForm(lead){
  if(!lead)return '';
  const current=currentDelegation(),same=current?.lead_id===lead.id,groups=state.groups.filter(g=>state.scope.includes(g.id));
  const start=same?current.start_at:new Date(Date.now()+serverOffset).toISOString(),end=same?current.end_at:new Date(Date.now()+serverOffset+8*3600000).toISOString();
  return `<section class="panel inline-delegation" id="delegation-editor"><div class="section-heading"><div><p class="eyebrow">DELEGACIÓN TEMPORAL</p><h2>${esc(full(lead))}</h2><p class="muted">Define la vigencia y los Grupos que podrá revisar. Su capacidad Lead se conserva.</p></div><button type="button" class="icon-btn" data-action="delegation-cancel" aria-label="Cerrar edición">${icon('close')}</button></div><form data-form="delegation"><input type="hidden" name="lead_id" value="${esc(lead.id)}"><div class="form-body"><div class="form-grid">${field('start_at','Desde *',localInput(start),'datetime-local','required')}${field('end_at','Hasta *',localInput(end),'datetime-local','required')}</div><fieldset><legend>Grupos bajo la delegación</legend><div class="delegation-group-options">${groups.map(g=>`<label class="checkbox"><input type="checkbox" name="group_ids" value="${esc(g.id)}" ${!same||current.group_ids.includes(g.id)?'checked':''}><span>${esc(g.code)} · ${esc(g.name)}</span></label>`).join('')}</div></fieldset><p class="callout">${current&&!same?`Al guardar, ${esc(full(lead))} sustituirá a ${esc(full(person(current.lead_id)))}. `:''}La asignación anterior se revoca al guardar. Sólo habrá una persona delegada para este Manager. La vigencia máxima es de 31 días y no se permite autoaprobación.</p></div><p class="form-error" role="alert"></p><div class="inline-form-actions"><button type="button" class="secondary" data-action="delegation-cancel">Cancelar</button><button type="submit" class="primary">${same?'Guardar delegación':'Asignar delegación'}</button></div></form></section>`;
}

function timerPanel(timers){
  return `<section class="timer-list">${timers.map(t=>`<article class="timer-card"><span class="live-dot"></span><div><span class="small-label">${t.user_id===me().id?'TU TIMER ACTIVO':esc(full(person(t.user_id)))}</span><strong>${state.overtime.find(o=>o.id===t.overtime_id)?.capture_type==='EMERGENCY'?'OT de emergencia':'OT programada'}</strong><small>Inicio: ${fmtTime(t.start_at)}</small></div><span class="timer-clock" data-elapsed="${esc(t.start_at)}">00:00:00</span><div class="timer-actions">${isManager()||state.can_approve?btn('Ver actividad','timer-open',t.overtime_id,'secondary small'):''}${t.user_id===me().id?btn('■ Detener','timer-stop',t.id,'danger'):''}</div></article>`).join('')}</section>`;
}

function exportLink(extra=''){
  const q=new URLSearchParams({month});if(['time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);else{if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);if(filters.kind)q.set('kind',filters.kind);}
  return `<a class="secondary button" href="/api/export.xlsx?${esc(q.toString())}" download>↓ Excel ${extra||'aprobados'}</a>`;
}
function timePage(){
  const own=state.overtime.filter(o=>o.user_id===me().id&&(o.start_at||o.scheduled_start||o.created_at).slice(0,7)===month);
  const guards=state.guards.filter(g=>g.user_id===me().id&&g.start_date.slice(0,7)<=month&&g.end_date.slice(0,7)>=month);
  const shared=state.windows.filter(w=>w.group_id===me().group_id&&w.status==='APPROVED'&&new Date(w.scheduled_end)>new Date());
  return heading('HORAS EXTRA Y GUARDIAS','Mi tiempo','Programa y registra OT, solicita guardias y revisa tus horas aprobadas.',monthControl()+exportLink())+
  timerPanel(state.timers.filter(t=>t.user_id===me().id))+
  `<section class="time-actions">${btn('＋ Programar OT','ot-new','','primary')}${btn('⚡ Iniciar emergencia','timer-start','','secondary')}${btn('＋ Solicitar Guardia','guard-new','','secondary')}</section><section class="kpis three">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real trabajado','↗')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Guardia aprobada menos OT','◷')}${kpi('Total del mes',`${hours(ledger.ot_minutes+ledger.guard_minutes)} <em>h</em>`,'Mismo cálculo en Claim y ADP','▦')}</section>
  ${shared.length?`<section class="panel"><div class="section-heading"><div><p class="eyebrow">CON TU GRUPO</p><h2>OT programada compartida</h2></div></div><div class="record-list">${shared.map(w=>`<article class="record-card"><div><span class="small-label">${esc(w.reference)}</span><h3>${esc(w.description)}</h3><p>${range(w.scheduled_start,w.scheduled_end)}</p></div>${state.overtime.some(o=>o.window_id===w.id&&o.user_id===me().id)?'<span class="pill">Ya participas</span>':btn('Participar','window-join',w.id,'secondary')}</article>`).join('')}</div></section>`:''}
  <section class="panel"><div class="section-heading"><div><p class="eyebrow">TIEMPO EXTRA</p><h2>Tus registros</h2></div><span class="pill">${own.length} registros</span></div><div class="record-list">${own.map(otCard).join('')||empty('Sin OT en este mes','Programa una OT o inicia un Timer de emergencia.')}</div></section>
  <section class="panel"><div class="section-heading"><div><p class="eyebrow">COBERTURA</p><h2>Guardias</h2></div></div><div class="record-list">${guards.map(g=>`<article class="record-card"><div><span class="small-label">${esc(g.rule_snapshot.name)}</span><h3>${fmtDate(g.start_date)} → ${fmtDate(g.end_date)}</h3><p>Solicitud individual · ${esc(g.id.slice(0,8).toUpperCase())}</p>${g.rule_snapshot.coverage_end_at?`<p class="muted">Cobertura cerrada: ${fmtDate(g.rule_snapshot.coverage_end_at)} · ${fmtTime(g.rule_snapshot.coverage_end_at)}</p>`:''}</div>${badge(g.status)}</article>`).join('')||empty('Sin Guardias en este mes','Solicita cobertura con una regla vigente de tu Manager.')}</div></section>`;
}
function otCard(o){
  const active=state.timers.some(t=>t.overtime_id===o.id),canStart=o.status==='APPROVED'&&o.execution==='SCHEDULED'&&new Date(o.scheduled_start)<=new Date()&&new Date(o.scheduled_end)>new Date();
  return `<article class="record-card"><div class="grow"><div class="record-title"><span class="small-label">${o.capture_type==='EMERGENCY'?'EMERGENCIA':o.capture_type==='HISTORICAL'?'OT HISTÓRICA':'OT PROGRAMADA'}</span>${badge(active?'RUNNING':o.status)}</div><h3>${esc(o.reference||'Pendiente de documentación')}</h3><p>${esc(o.description||'Detén el Timer y documenta el trabajo realizado.')}</p><small>${o.start_at?`Real: ${range(o.start_at,o.end_at)}`:`Programado: ${range(o.scheduled_start,o.scheduled_end)}`}</small>${o.revision?`<small>Revisión ${o.revision} · La última edición requiere aprobación.</small>`:''}</div><div class="entity-actions">${!active?btn(o.status==='DOCUMENTATION'?'Documentar':'Editar y reenviar','ot-edit',o.id,'secondary'):''}${canStart?btn('▶ Iniciar','timer-planned',o.id,'primary'):''}</div></article>`;
}
function teamTimePage(){
  const people=state.people.filter(p=>p.role==='USER'&&state.scope.includes(p.group_id));
  return heading('OPERACIÓN Y TRAZABILIDAD','Tiempo del equipo','Aprobaciones e historial unificados. Revisa cada decisión en su contexto.',monthControl()+btn('＋ OT compartida','window-new','','primary')+exportLink())+
  `<section class="panel filters"><div>${select('filter-period','Periodo',`<option value="MONTH" ${filters.period==='MONTH'?'selected':''}>Mes seleccionado</option><option value="ALL" ${filters.period==='ALL'?'selected':''}>Todos los periodos</option>`)}${select('filter-group','Grupo',options(state.groups,filters.group,x=>x.name,'Todos los Grupos'))}${select('filter-person','Técnico',options(people.filter(p=>!filters.group||p.group_id===filters.group),filters.person,full,'Todos los Técnicos'))}${select('filter-status','Estado',`<option value="">Todos los estados</option>${['SUBMITTED','APPROVED','REJECTED','DOCUMENTATION','RUNNING'].map(s=>`<option value="${s}" ${filters.status===s?'selected':''}>${statuses[s]}</option>`).join('')}`)}${select('filter-kind','Tipo',`<option value="">OT y Guardias</option><option value="OT" ${filters.kind==='OT'?'selected':''}>Tiempo extra</option><option value="GUARD" ${filters.kind==='GUARD'?'selected':''}>Guardia</option>`)}</div><p class="muted footnote">Excel incluye únicamente tiempo real aprobado del mes y alcance seleccionados.</p></section>`+
  timerPanel(state.timers.filter(t=>(!filters.kind||filters.kind==='OT')&&(!filters.status||filters.status==='RUNNING')&&(!filters.person||t.user_id===filters.person)&&(!filters.group||person(t.user_id)?.group_id===filters.group)))+
  `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Técnico / Grupo</th><th>Registro</th><th>Periodo</th><th>Estado</th><th class="right">Acciones</th></tr></thead><tbody>${teamRows()}</tbody></table></div>${!teamRecords().length?empty('No hay registros con estos filtros','Los tiempos enviados por tu equipo aparecerán aquí.'):''}</section>`;
}
function teamRecords(){
  const endMonth=new Date(Number(month.slice(0,4)),Number(month.slice(5)),1).toLocaleDateString('sv-SE');
  return [...state.overtime.map(o=>({...o,kind:'ot',filterKind:'OT',a:o.start_at||o.scheduled_start||o.created_at,b:o.end_at||o.scheduled_end||o.created_at})),...state.guards.map(g=>({...g,kind:'guard',filterKind:'GUARD',a:g.start_date,b:g.end_date}))].filter(r=>{
    const u=person(r.user_id);return state.scope.includes(u?.group_id)&&(!filters.group||u.group_id===filters.group)&&(!filters.person||u.id===filters.person)&&(!filters.kind||r.filterKind===filters.kind)&&(!filters.status||r.status===filters.status||filters.status==='RUNNING'&&r.execution==='RUNNING')&&(filters.period==='ALL'||r.a.slice(0,10)<endMonth&&r.b.slice(0,10)>=month+'-01');
  }).sort((a,b)=>b.created_at.localeCompare(a.created_at));
}
function teamRows(){return teamRecords().map(r=>`<tr><td><strong>${esc(full(person(r.user_id)))}</strong><small>${esc(person(r.user_id)?.employee_id)} · ${esc(group(person(r.user_id)?.group_id)?.name)}</small></td><td><span class="small-label">${r.kind==='ot'?'TIEMPO EXTRA':'GUARDIA'}</span><strong>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</strong><small>${esc(r.description||'')}</small></td><td>${fmtDate(r.a)}<small>${r.kind==='ot'?`${fmtTime(r.a)} — ${fmtTime(r.b)}`:fmtDate(r.b)}</small></td><td>${badge(r.execution==='RUNNING'?'RUNNING':r.status)}</td><td><div class="row-actions">${btn('Detalle','record-detail',`${r.kind}:${r.id}`,'link')}${r.status==='SUBMITTED'&&r.user_id!==me().id&&r.execution!=='RUNNING'?btn('Aprobar','approve',`${r.kind}:${r.id}`,'primary small')+btn('Rechazar','reject',`${r.kind}:${r.id}`,'text-danger'):''}</div></td></tr>`).join('');}
function rulesPage(){
  const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  return heading('COBERTURA OPERATIVA','Reglas de Guardia','Las solicitudes conservan una copia de la regla vigente al momento de crearse.',btn('＋ Crear regla','rule-new','','primary'))+
  `<div class="rules-grid">${state.rules.map(r=>`<article class="panel"><span class="small-label">VIGENTE DESDE ${fmtDate(r.effective_from)}</span><h2>${esc(r.name)}</h2><div class="rule-segments">${days.map((day,i)=>{const segments=r.segments.filter(s=>Number(s.day)===i);return segments.length?`<div><strong>${day}</strong><span>${segments.map(s=>s.start==='00:00'&&s.end==='00:00'?'24 horas':`${esc(s.start)} — ${esc(s.end)}${s.end<=s.start?' (+1 día)':''}`).join('<br>')}</span></div>`:'';}).join('')}</div></article>`).join('')||empty('Define la cobertura de tu equipo','Agrega segmentos por día para habilitar solicitudes de Guardia.')}</div>`;
}
function capturePage(kind){
  const grouped=new Map();ledger.rows.forEach(r=>{const day=new Date(r.date+'T12:00:00'),weekday=day.getDay(),offset=kind==='claim'?(weekday+1)%7:weekday;day.setDate(day.getDate()-offset);const week=day.toLocaleDateString('sv-SE');if(!grouped.has(week))grouped.set(week,[]);grouped.get(week).push(r);});
  return heading('CAPTURA MENSUAL',kind==='claim'?'Claim':'ADP',kind==='claim'?'Guía semanal de sábado a viernes. Sólo tiempo aprobado.':'Guía semanal de domingo a sábado. Inicio y duración HH:MM.',monthControl()+exportLink())+
  `<section class="capture-summary"><div><span>Tiempo extra</span><strong>${hours(ledger.ot_minutes)} <small>h</small></strong></div><div><span>Guardia neta</span><strong>${hours(ledger.guard_minutes)} <small>h</small></strong></div><p>Una misma fuente de cálculo.<br><strong>Sin duplicar OT ni traslapes con Guardia.</strong></p></section>`+
  ([...grouped].map(([week,rows])=>`<section class="panel table-panel"><div class="section-heading padded"><div><p class="eyebrow">SEMANA ${kind==='claim'?'CLAIM':'ADP'}</p><h2>Desde ${fmtDate(week)}</h2></div><span class="pill">${hours(rows.reduce((n,r)=>n+r.minutes,0))} h</span></div><div class="table-scroll"><table><thead><tr><th>Fecha</th><th>Tipo</th><th>Referencia</th><th>Inicio</th><th>${kind==='claim'?'Horas decimales':'Duración HH:MM'}</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${fmtDate(r.date)}</td><td>${r.kind==='OT'?'Onsite Overtime':'Stand-by'}</td><td>${esc(r.reference||'—')}</td><td>${r.start}</td><td><strong>${kind==='claim'?hours(r.minutes):hm(r.minutes)}</strong></td></tr>`).join('')}</tbody></table></div></section>`).join('')||empty('Sin tiempo aprobado en este mes','Tus registros aparecerán después de la aprobación de tu Manager o Lead delegado.'));
}
function recoveriesPage(){
  return heading('ACCESO SEGURO','Recuperación de acceso',isAdmin()?'Valida accesos de Managers, otros administradores y Técnicos sin Manager activo.':'Valida la identidad de los Técnicos de tus Grupos antes de emitir un código.')+
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

function accountModal(id=''){
  const a=state.accounts.find(a=>a.id===id)||{};
  showModal(id?'Editar Cuenta':'Nueva Cuenta',form('account',field('code','Código de Cuenta *',a.code,'text','required maxlength="24"')+field('name','Nombre *',a.name,'text','required maxlength="100"'),id));
}
function groupModal(id='',aid=''){
  const g=group(id)||{},selected=g.account_id||aid||state.accounts[0]?.id;
  if(!selected)return toast('Crea una Cuenta primero.',true);
  showModal(id?'Editar Grupo':'Nuevo Grupo',form('group',select('account_id','Cuenta *',options(state.accounts,selected,x=>`${x.code} · ${x.name}`),'required')+field('code','Código de Grupo *',g.code,'text','required maxlength="24"')+field('name','Nombre del Grupo *',g.name,'text','required maxlength="100"')+select('manager_id','Manager',managerOptions(selected,g.manager_id))+(id?field('transfer_reason','Motivo si cambias de Manager','','text','placeholder="Explica el traspaso del Grupo"'):''),id));
}
function managerOptions(aid,selected){return options(state.people.filter(p=>p.role==='MANAGER'&&p.status!=='DISABLED'&&p.account_id===aid),selected,full,'Sin Manager');}
function groupCheckboxes(aid,mid){
  const available=state.groups.filter(g=>g.account_id===aid&&(!g.manager_id||g.manager_id===mid));
  return available.map(g=>`<label class="checkbox"><input type="checkbox" name="group_ids" value="${esc(g.id)}" ${g.manager_id===mid&&mid?'checked':''}><span>${esc(g.code)} · ${esc(g.name)}</span></label>`).join('')||'<p class="muted">No hay Grupos disponibles. Puedes asignarlos después.</p>';
}
function personModal(id='',role='USER',context=''){
  const p=person(id)||{},r=p.role||role;
  if(r==='MANAGER'&&!state.accounts.length)return toast('Crea una Cuenta primero.',true);
  const availableGroups=state.groups.filter(g=>isAdmin()||state.scope.includes(g.id));
  if(r==='USER'&&!availableGroups.length)return toast('Crea o asigna un Grupo primero.',true);
  const aid=p.account_id||(r==='MANAGER'?context:'')||state.accounts[0]?.id;
  const gid=p.group_id||(r==='USER'?context:'')||availableGroups[0]?.id;
  showModal(id?'Editar persona':r==='MANAGER'?'Nuevo Manager':r==='ADMIN'?'Nuevo administrador':'Nuevo Técnico',form('person',`<input name="role" type="hidden" value="${r}"><div class="form-grid">${field('first','Nombre *',p.first,'text','required')}${field('last','Apellido *',p.last,'text','required')}</div>${r==='ADMIN'?field('username','Usuario *',p.username,'text','required autocomplete="off"'):field('employee_id','Employee ID *',p.employee_id,'text',`required ${id?'readonly':''}`)}${field('email','Correo *',p.email,'email','required')}${r==='MANAGER'?select('account_id','Cuenta *',options(state.accounts,aid,x=>`${x.code} · ${x.name}`),'required')+`<fieldset><legend>Grupos disponibles</legend><div id="group-checks">${groupCheckboxes(aid,id)}</div></fieldset><p class="muted footnote">Sólo aparecen los Grupos de esta Cuenta que están libres o ya pertenecen a este Manager.</p>`:''}${r==='USER'?select('group_id','Grupo *',options(availableGroups,gid,x=>`${x.code} · ${x.name}`),'required')+`<label class="checkbox" id="lead-option"><input name="is_lead" type="checkbox" ${p.is_lead?'checked':''}><span>Designar como Lead</span></label><p class="muted" id="lead-note"></p><p class="muted footnote">Ser Lead no habilita aprobaciones. Es el backup de su Manager; la delegación temporal se administra por separado.</p>${id?field('transfer_reason','Motivo si cambias de Grupo','','text','placeholder="Explica el movimiento de equipo"'):''}`:''}${id?`<input type="hidden" name="status" value="${esc(p.status)}"><p class="callout">Estado: ${badge(p.status)}. Usa las acciones de Baja o Reactivar para cambiar el acceso.</p>`:'<p class="callout">La cuenta se creará pendiente de activación. Recibirás un código para su primer acceso.</p>'}`,id));
  syncLeadOption();
}
function syncLeadOption(){
  const form=$('[data-form="person"]');if(!form?.elements.group_id)return;
  const owner=group(form.elements.group_id.value)?.manager_id;
  const holder=state.people.find(p=>p.is_lead&&p.status!=='DISABLED'&&group(p.group_id)?.manager_id===owner&&p.id!==form.dataset.id);
  $('#lead-option').hidden=!!holder||!owner;form.elements.is_lead.disabled=!!holder||!owner;if(holder)form.elements.is_lead.checked=false;
  $('#lead-note').textContent=holder?`Lead actual del Manager: ${full(holder)} · ${holder.employee_id}`:!owner?'Asigna un Manager al Grupo para designar su backup Lead.':'Un solo Lead entre todos los Grupos del Manager.';
}
function lifecycleActions(p){
  if(p.id===me().id)return '';
  if(p.status==='DISABLED'&&p.role==='MANAGER'&&state.groups.some(g=>g.manager_id===p.id))return btn('Regularizar baja','person-offboard',p.id,'text-danger');
  return p.status==='DISABLED'?btn('Reactivar','person-reactivate',p.id,'link'):btn('Dar de baja','person-offboard',p.id,'text-danger');
}
function transferModal(id,wholeGroup=false){
  const source=wholeGroup?group(id):person(id);
  const choices=wholeGroup?state.people.filter(p=>p.role==='MANAGER'&&p.status==='ACTIVE'&&p.account_id===source.account_id&&p.id!==source.manager_id):state.groups.filter(g=>g.id!==source.group_id&&person(g.manager_id)?.status==='ACTIVE');
  showModal(wholeGroup?'Transferir Grupo':'Transferir Técnico',form(wholeGroup?'group-transfer':'transfer',`<p class="callout">${esc(wholeGroup?source.name:full(source))} · El movimiento conserva su estado y su historial. Sólo puede quedar un Lead por Manager.</p>${select(wholeGroup?'manager_id':'group_id',wholeGroup?'Manager de destino *':'Grupo de destino *',options(choices,'',p=>wholeGroup?full(p):`${p.code} · ${p.name} — ${full(person(p.manager_id))}`,'Selecciona un destino'),'required')}${field('transfer_reason','Motivo del movimiento *','','text','required')}`,id,'Confirmar transferencia'));
}
async function lifecycleModal(id){
  const impact=await api(`/api/admin/people/${id}/impact`),p=impact.person;
  const groups=impact.groups.map(g=>`<fieldset><legend>${esc(g.code)} · ${esc(g.name)} · ${g.members.length} Técnicos</legend>${select('transfer:'+g.id,'Manager de destino *',options(impact.candidates.filter(m=>m.account_id===g.account_id),'',full,'Selecciona un Manager activo'),'required')}</fieldset>`).join('');
  const documents=impact.documents.map((o,i)=>`<fieldset data-offboard-document="${esc(o.id)}"><legend>Documentar OT pendiente ${i+1}</legend>${['reference','description','justification','impact','in_lieu'].map((k,j)=>`<label class="field"><span>${['Referencia completa CHG / INC','Descripción','Justificación','Impacto','Por qué no aplica tiempo compensatorio'][j]} *</span><input data-key="${k}" value="${esc(o[k]||'')}" required></label>`).join('')}</fieldset>`).join('');
  showModal('Revisar baja · '+esc(full(p)),form('offboard',`<input type="hidden" name="expected" value="${esc(impact.expected)}"><p class="callout">Se conservan la identidad y todos los registros. Las solicitudes pendientes pasan al responsable del Grupo. Se cancelan ${impact.scheduled.length} OT sin ejecutar y se limita o cancela la cobertura de ${impact.guards.length} Guardias.</p>${groups?`<div class="offboard-transfers">${groups}</div><aside class="offboard-replacement"><div><strong>¿Necesitas un reemplazo nuevo?</strong><p>Créalo y activa su acceso antes del traspaso. El Manager actual sigue activo hasta confirmar.</p></div>${btn('Crear Manager','manager-new',p.account_id,'secondary')}</aside>`:''}${impact.timers.length?'<label class="checkbox"><input name="stop_timers" type="checkbox" required><span>Autorizar el cierre del Timer activo a la hora de confirmar la baja.</span></label>':''}${documents}${field('reason','Motivo de la baja *','','text','required')}<label class="checkbox"><input name="confirm" type="checkbox" required><span>Revisé el impacto y las transferencias. Confirmo retirar el acceso y las delegaciones.</span></label><p class="muted offboard-review-note">Si cambian los datos, vuelve a abrir la revisión.</p>`,id,'Confirmar baja'),true);
}
function localInput(value){
  if(!value)return '';
  const parts=new Intl.DateTimeFormat('sv-SE',{timeZone:state?.timezone||'America/Mexico_City',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(value));
  const v=t=>parts.find(p=>p.type===t)?.value;return `${v('year')}-${v('month')}-${v('day')}T${v('hour')}:${v('minute')}`;
}
function otModal(id=''){
  const o=state.overtime.find(o=>o.id===id)||{};
  showModal(id?(o.status==='DOCUMENTATION'?'Documentar OT':'Editar y reenviar OT'):'Registrar tiempo extra',form('ot',`${id?'':select('capture_type','Tipo de registro','<option value="PLANNED">OT programada</option><option value="HISTORICAL">OT histórica</option>')}${!id||o.execution==='SCHEDULED'?`<div class="form-grid">${field('scheduled_start','Inicio *',localInput(o.scheduled_start),'datetime-local','required')}${field('scheduled_end','Fin *',localInput(o.scheduled_end),'datetime-local','required')}</div>`:`<p class="callout">Tiempo real: ${range(o.start_at,o.end_at)}. El periodo del Timer permanece fijo.</p>`}${field('reference','Referencia completa CHG / INC *',o.reference,'text','required placeholder="CHG1234567"')}<label class="field"><span>Descripción *</span><textarea name="description" required rows="2">${esc(o.description)}</textarea></label><label class="field"><span>Justificación *</span><textarea name="justification" required rows="2">${esc(o.justification)}</textarea></label><label class="field"><span>Impacto si no se aprueba *</span><textarea name="impact" required rows="2">${esc(o.impact)}</textarea></label><label class="field"><span>Por qué no aplica tiempo compensatorio *</span><textarea name="in_lieu" required rows="2">${esc(o.in_lieu)}</textarea></label><p class="muted footnote">${id?'Al guardar, el registro volverá a aprobación.':'La OT programada requiere aprobación antes de iniciar el Timer.'}</p>`,id,'Enviar a aprobación'));
}
function guardModal(){
  if(!state.rules.length)return toast('Tu Manager debe crear una regla de Guardia primero.',true);
  showModal('Solicitar Guardia',form('guard',select('rule_id','Regla de Guardia *',options(state.rules,'',x=>`${x.name} · desde ${fmtDate(x.effective_from)}`),'required')+`<div class="form-grid">${field('start_date','Fecha de inicio *','','date','required')}${field('end_date','Fecha de fin *','','date','required')}</div><p class="callout">La solicitud es individual y requiere aprobación. La OT aprobada se descuenta de la Guardia al calcular el neto.</p>`,'','Enviar solicitud'));
}
function ruleModal(){
  const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  showModal('Nueva regla de Guardia',form('rule',field('name','Nombre de la regla *','','text','required')+field('effective_from','Vigente desde *',new Date().toLocaleDateString('sv-SE'),'date','required')+`<div class="weekly-rule-intro">${icon('time')}<p>Configura uno o varios intervalos por día. Un fin anterior al inicio, como 20:00 → 00:00, termina al día siguiente.</p></div><div class="rule-day-tabs" role="group" aria-label="Día que deseas configurar">${days.map((day,i)=>`<button type="button" data-action="rule-day-open" data-id="${i}" aria-pressed="${i===0}">${day}</button>`).join('')}</div><div class="weekly-rule-days">${days.map((day,i)=>`<section class="rule-day" data-rule-day="${i}" ${i?'hidden':''}><header><label class="checkbox"><input type="checkbox" name="days" value="${i}"><strong>${day}</strong></label><label class="checkbox rule-full-day"><input type="checkbox" name="full_day_${i}" data-full-day="${i}" disabled><span>24 horas</span></label></header><div class="rule-day-content" hidden><div class="rule-intervals">${ruleInterval(i,0)}</div><button type="button" class="link rule-add" data-action="rule-add" data-id="${i}">＋ Agregar intervalo</button><p class="rule-full-note" hidden>Cobertura completa · 00:00 a 00:00 del día siguiente.</p></div></section>`).join('')}</div>`),true);
}
function ruleInterval(day,index){
  return `<div class="rule-interval" data-rule-segment><label><span>Inicio</span><input type="time" name="start_${day}${index?'_'+index:''}" data-start value="00:00" aria-label="Inicio intervalo ${index+1}" disabled></label><span class="interval-arrow">→</span><label><span>Fin</span><input type="time" name="end_${day}${index?'_'+index:''}" data-end value="08:00" aria-label="Fin intervalo ${index+1}" disabled></label><small data-interval-note>Del mismo día</small><button type="button" class="icon-btn" data-action="rule-remove" aria-label="Eliminar intervalo">${icon('close')}</button></div>`;
}
function syncRuleDay(section){
  const enabled=$('[name="days"]',section).checked,full=$('[data-full-day]',section).checked;
  $('[data-full-day]',section).disabled=!enabled;$('.rule-day-content',section).hidden=!enabled;
  $('.rule-intervals',section).hidden=full;$('.rule-add',section).hidden=full;$('.rule-full-note',section).hidden=!full;
  $$('[data-rule-segment]',section).forEach(row=>{const a=$('[data-start]',row),b=$('[data-end]',row);a.disabled=b.disabled=!enabled||full;a.required=b.required=enabled&&!full;$('[data-interval-note]',row).textContent=a.value===b.value?'24 horas':b.value<a.value?'Termina al día siguiente':'Del mismo día';});
}

function windowModal(){
  const groups=state.groups.filter(g=>state.scope.includes(g.id));
  if(!groups.length)return toast('No hay Grupos disponibles en tu alcance.',true);
  showModal('OT compartida con el Grupo',form('window',select('group_id','Grupo *',options(groups,'',x=>`${x.code} · ${x.name}`),'required')+`<div class="form-grid">${field('scheduled_start','Inicio *','','datetime-local','required')}${field('scheduled_end','Fin *','','datetime-local','required')}</div>`+field('reference','Referencia completa CHG / INC *','','text','required')+`<label class="field"><span>Descripción *</span><textarea name="description" required rows="3"></textarea></label><p class="callout">Cada Técnico podrá participar una sola vez y ejecutar su propio Timer. Su tiempo real se enviará a aprobación al detenerlo.</p>`,'','Publicar ventana'));
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
    const body=`${accessSteps(0)}<div class="access-copy"><h3>Vamos a ayudarte a volver.</h3><p>Ingresa tu usuario para solicitar la recuperación. Tu Manager valida los accesos de Técnicos; Administración atiende a Managers y administradores.</p></div>${identity}<div class="access-assistance">${icon('info')}<p>El código se entrega por un canal corporativo; no se envía un correo automático.</p></div><button type="button" class="access-alternative" data-action="recovery-complete"><span class="alternative-icon">${icon('key')}</span><span><strong>¿Ya tienes un código?</strong><small>Continúa para crear tu nueva contraseña.</small></span>${icon('forward')}</button>`;
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

function detailModal(key){
  const [kind,id]=key.split(':'),r=(kind==='ot'?state.overtime:state.guards).find(r=>r.id===id);if(!r)return;
  const logs=state.audit.filter(a=>a.entity_id===id);
  showModal('Detalle del registro',`<div class="form-body"><p class="form-instructions"><strong>Revisa antes de decidir</strong>Consulta el periodo, la documentación y la trazabilidad. Si tienes autoridad, puedes aprobar o explicar el rechazo al final.</p><div class="detail-hero">${identity(person(r.user_id))}${badge(r.execution==='RUNNING'?'RUNNING':r.status)}</div>${r.execution==='RUNNING'?`<div class="detail-live"><span class="live-dot"></span><span>Timer activo</span><strong data-elapsed="${esc(r.start_at)}">00:00:00</strong></div>`:''}<dl><dt>Registro</dt><dd>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</dd><dt>Periodo</dt><dd>${kind==='ot'?range(r.start_at||r.scheduled_start,r.end_at||r.scheduled_end):`${fmtDate(r.start_date)} → ${fmtDate(r.end_date)}`}</dd>${kind!=='ot'&&r.rule_snapshot?.coverage_end_at?`<dt>Cierre administrativo</dt><dd>${fmtDate(r.rule_snapshot.coverage_end_at)} · ${fmtTime(r.rule_snapshot.coverage_end_at)}</dd>`:''}${kind==='ot'?`<dt>Descripción</dt><dd>${esc(r.description||'—')}</dd><dt>Justificación</dt><dd>${esc(r.justification||'—')}</dd><dt>Impacto</dt><dd>${esc(r.impact||'—')}</dd><dt>Tiempo compensatorio</dt><dd>${esc(r.in_lieu||'—')}</dd><dt>Revisiones</dt><dd>${r.revision}</dd>`:''}</dl><h3>Trazabilidad</h3><div class="audit-list">${logs.map(a=>{let d={};try{d=JSON.parse(a.detail)}catch{}return `<div><span></span><p><strong>${esc(auditLabel(a.action))}</strong><small>${fmtDate(a.created_at)} · ${fmtTime(a.created_at)} · ${esc(full(person(a.actor_id)))}</small>${d.reason?`<small>${esc(d.reason)}</small>`:''}</p></div>`;}).join('')||'<p class="muted">Sin eventos disponibles.</p>'}</div></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}${state.can_approve&&r.user_id!==me().id&&r.status==='SUBMITTED'&&r.execution!=='RUNNING'?btn('Rechazar','reject',key,'text-danger')+btn('Aprobar','approve',key,'primary'):''}</footer>`);tick();
}
function auditLabel(action){return {CREATE_OT:'Registro de OT',EDIT_OT_REOPEN_APPROVAL:'Edición y reenvío a aprobación',REQUEST_GUARD:'Solicitud de Guardia',APPROVED:'Aprobado',REJECTED:'Rechazado',START_TIMER:'Timer iniciado',STOP_TIMER:'Timer detenido',JOIN_SHARED_OT:'Participación en OT compartida',ADMIN_STOP_TIMER_ON_OFFBOARD:'Timer cerrado por baja administrativa',ADMIN_DOCUMENT_ON_OFFBOARD:'Documentación completada durante la baja',CANCEL_SCHEDULE_ON_OFFBOARD:'OT sin ejecutar cancelada por baja',CLOSE_GUARD_ON_OFFBOARD:'Cobertura cerrada por baja',TRANSFER_PERSON:'Técnico transferido',TRANSFER_GROUP:'Grupo transferido',OFFBOARD_PERSON:'Baja de acceso',REACTIVATE_PERSON:'Reactivación solicitada'}[action]||action;}

async function perform(action,id,button){
  const confirmations={
    'account-delete':['Eliminar Cuenta','Sólo se puede eliminar una Cuenta vacía. Primero mueve o elimina sus Grupos.'],
    'group-delete':['Eliminar Grupo','Sólo se elimina un Grupo sin personas ni historial. Conserva los Grupos con registros para mantener su trazabilidad.'],
    'activation-code':['Regenerar activación','El código anterior dejará de funcionar. Comparte el nuevo código con la persona por un canal corporativo.'],
    'timer-start':['Iniciar OT de emergencia','El Timer comenzará al confirmar. Deténlo al terminar y completa la documentación para solicitar aprobación.']
  };
  if(confirmations[action]&&button?.dataset.confirmed!=='true'){
    const [title,instruction]=confirmations[action];
    showModal(title,form('confirmation',`<input type="hidden" name="action" value="${esc(action)}"><input type="hidden" name="target" value="${esc(id)}"><p class="form-instructions"><strong>Antes de confirmar</strong>${instruction}</p>`,'','Confirmar'));return;
  }
  switch(action){
    case 'password-visibility':{const input=id==='login-password'?$('#login-password'):$('#'+id,$('#modal'));if(!input||!['password','confirm'].includes(input.name))return;const reveal=input.type==='password';input.type=reveal?'text':'password';button.setAttribute('aria-pressed',String(reveal));button.setAttribute('aria-label',reveal?'Ocultar contraseña':'Mostrar contraseña');button.innerHTML=icon(reveal?'eye-off':'eye');return;}
    case 'access-login':$('#modal').close();{const input=$('[data-form="login"] [name="identity"]');if(input){input.value=accessDraft.identity;$('[data-form="login"] [name="password"]')?.focus();}}return;
    case 'analytics-records':analyticsDetailType=id;render();$('#analytics-records')?.scrollIntoView({block:'start'});return;
    case 'analytics-detail-close':analyticsDetailType=null;render();return;
    case 'analytics-group':filters.group=id;filters.person='';await loadLedger();render();$('#analytics-users')?.scrollIntoView({block:'start'});return;
    case 'analytics-user':filters.person=id;analyticsDetailType='ALL';await loadLedger();render();$('#analytics-records')?.scrollIntoView({block:'start'});return;
    case 'about':aboutProject();return;
    case 'close':$('#modal').close();return;
    case 'logout':await api('/api/logout','POST',{});state=null;page='dashboard';$('#modal').close();render();return;
    case 'account-new':accountModal();return;
    case 'account-edit':accountModal(id);return;
    case 'group-new':groupModal('',id);return;
    case 'group-edit':groupModal(id);return;
    case 'manager-new':personModal('','MANAGER',id);return;
    case 'tech-new':personModal('','USER',id);return;
    case 'admin-new':personModal('','ADMIN');return;
    case 'person-edit':personModal(id);return;
    case 'person-transfer':transferModal(id);return;
    case 'group-transfer':transferModal(id,true);return;
    case 'person-offboard':await lifecycleModal(id);return;
    case 'person-reactivate':showModal('Reactivar acceso',form('reactivate',`<p class="callout">${esc(full(person(id)))} recibirá un código nuevo y definirá otra contraseña. No se restauran delegaciones, capacidad Lead ni asignaciones anteriores.</p>${field('reason','Motivo de reactivación *','','text','required')}`,id,'Generar activación'));return;
    case 'account-delete':await api('/api/accounts/'+id,'DELETE');break;
    case 'group-delete':await api('/api/groups/'+id,'DELETE');break;
    case 'activation-code':{const r=await api(`/api/people/${id}/activation`,'POST',{});credentials(r.activation_code,person(id)?.username);return;}
    case 'activate':publicModal('activate');return;
    case 'recovery-request':publicModal('request');return;
    case 'recovery-complete':publicModal('complete');return;
    case 'recovery-view':{const result=await api(`/api/recoveries/${id}/view`,'POST',{});recoveryCodeModal(result,'Código vigente');return;}
    case 'recovery-issue':{const previous=state.recoveries.find(r=>r.id===id),regenerated=previous?.status==='ISSUED';const result=await api(`/api/recoveries/${id}/issue`,'POST',{});await refresh();recoveryCodeModal(result,regenerated?'Código regenerado':'Código generado',regenerated);return;}
    case 'ot-new':otModal();return;
    case 'ot-edit':otModal(id);return;
    case 'guard-new':guardModal();return;
    case 'rule-new':ruleModal();return;
    case 'window-new':windowModal();return;
    case 'window-join':await api(`/api/windows/${id}/join`,'POST',{});break;
    case 'delegation-inline':delegationDraftLead=id;render();$('#delegation-editor')?.scrollIntoView({block:'center'});$('#delegation-editor [name="start_at"]')?.focus({preventScroll:true});return;
    case 'delegation-cancel':delegationDraftLead='';render();return;
    case 'rule-day-open':$$('[data-rule-day]').forEach(section=>section.hidden=section.dataset.ruleDay!==id);$$('[data-action=rule-day-open]').forEach(tab=>tab.setAttribute('aria-pressed',String(tab.dataset.id===id)));return;
    case 'rule-add':{const section=$(`[data-rule-day="${id}"]`);const index=Date.now();$('.rule-intervals',section).insertAdjacentHTML('beforeend',ruleInterval(id,index));syncRuleDay(section);$$('[data-start]',section).at(-1)?.focus();return;}
    case 'rule-remove':{const row=button.closest('[data-rule-segment]'),section=row.closest('[data-rule-day]');row.remove();if(!$('.rule-interval',section))$('.rule-intervals',section).innerHTML=ruleInterval(section.dataset.ruleDay,0);syncRuleDay(section);return;}
    case 'dashboard-drill':{await navigate('teamTime');filters.kind=id==='ot'?'OT':id==='guard'?'GUARD':'';filters.status=id==='pending'?'SUBMITTED':id==='running'?'RUNNING':'APPROVED';filters.period=['pending','running'].includes(id)?'ALL':'MONTH';await loadLedger();render();$('#main')?.focus({preventScroll:true});return;}
    case 'timer-open':{const record=state.overtime.find(o=>o.id===id);if(!record)return;await navigate('teamTime');filters.person=record.user_id;filters.kind='OT';filters.status='RUNNING';filters.period='ALL';await loadLedger();render();detailModal('ot:'+id);return;}
    case 'delegation-revoke':await api('/api/delegations/'+id,'DELETE');delegationDraftLead='';break;
    case 'timer-start':await api('/api/timers/start','POST',{});break;
    case 'timer-planned':await api('/api/timers/start','POST',{overtime_id:id});break;
    case 'timer-stop':await api(`/api/timers/${id}/stop`,'POST',{});break;
    case 'approve':{const [kind,identity]=id.split(':');await api(`/api/approvals/${kind}/${identity}`,'POST',{decision:'APPROVED'});$('#modal').close();break;}
    case 'reject':showModal('Rechazar registro',form('reject',`<label class="field"><span>Motivo del rechazo *</span><textarea name="reason" rows="4" required></textarea></label>`,id,'Rechazar registro'));return;
    case 'record-detail':detailModal(id);return;
    case 'month-prev':case 'month-next':{const d=new Date(`${month}-15T12:00:00`);d.setMonth(d.getMonth()+(action==='month-next'?1:-1));month=d.toLocaleDateString('sv-SE').slice(0,7);await loadLedger();render();return;}
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
    case 'login':await api('/api/login','POST',data);page='dashboard';await refresh();return;
    case 'activate':await api('/api/activate','POST',data);accessResult('activate',data.identity);return;
    case 'recovery-request':await api('/api/recoveries','POST',data);accessResult('request',data.identity);return;
    case 'recovery-complete':await api('/api/recoveries/complete','POST',data);accessResult('complete',data.identity);return;
    case 'account':await api('/api/accounts'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'group':await api('/api/groups'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'person':data.group_ids=fd.getAll('group_ids');data.is_lead=fd.has('is_lead');response=await api('/api/people'+(id?'/'+id:''),id?'PUT':'POST',data);await refresh();if(response.activation_code){credentials(response.activation_code,data.username||data.employee_id);return;}break;
    case 'transfer':{const source=person(id);await api('/api/people/'+id,'PUT',{...source,...data,is_lead:!!source.is_lead});break;}
    case 'group-transfer':{const source=group(id);await api('/api/groups/'+id,'PUT',{...source,...data});break;}
    case 'reactivate':response=await api(`/api/admin/people/${id}/reactivate`,'POST',data);await refresh();credentials(response.activation_code,response.username);return;
    case 'offboard':{data.confirm=fd.has('confirm');data.stop_timers=fd.has('stop_timers');data.transfers=Object.fromEntries([...fd].filter(([k])=>k.startsWith('transfer:')).map(([k,v])=>[k.slice(9),v]));data.documents=$$('[data-offboard-document]',f).map(section=>({id:section.dataset.offboardDocument,...Object.fromEntries($$('input,textarea',section).map(input=>[input.dataset.key,input.value]))}));await api(`/api/admin/people/${id}/offboard`,'POST',data);break;}
    case 'profile':await api('/api/profile','PUT',data);break;
    case 'password':await api('/api/password','PUT',data);state=null;render();toast('Contraseña actualizada. Vuelve a iniciar sesión.');return;
    case 'ot':await api('/api/overtime'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'guard':await api('/api/guards','POST',data);break;
    case 'rule':data.segments=fd.getAll('days').flatMap(day=>fd.has('full_day_'+day)?[{day:Number(day),start:'00:00',end:'00:00'}]:$$(`[data-rule-day="${day}"] [data-rule-segment]`,f).map(row=>({day:Number(day),start:$('[data-start]',row).value,end:$('[data-end]',row).value})));await api('/api/rules','POST',data);break;
    case 'window':await api('/api/windows','POST',data);break;
    case 'delegation':data.group_ids=fd.getAll('group_ids');data.replace_current=true;await api('/api/delegations','POST',data);delegationDraftLead='';break;
    case 'reject':{const [recordType,identity]=id.split(':');await api(`/api/approvals/${recordType}/${identity}`,'POST',{decision:'REJECTED',reason:data.reason});break;}
    default:return;
  }
  $('#modal').close();await refresh();toast('Cambios guardados.');
}
function bind(){
  document.addEventListener('click',async event=>{
    const target=event.target.closest('[data-page],[data-action]');if(!target||busy)return;
    event.preventDefault();busy=true;target.disabled=true;
    try{if(target.dataset.page)await navigate(target.dataset.page);else await perform(target.dataset.action,target.dataset.id||'',target);}catch(error){toast(error.message,true);}finally{busy=false;if(target.isConnected)target.disabled=false;}
  });
  document.addEventListener('submit',async event=>{
    const f=event.target.closest('[data-form]');if(!f)return;event.preventDefault();if(busy)return;
    busy=true;const button=$('[type="submit"], button:not([type])',f),buttonContent=button?.innerHTML;const isAccess=f.classList.contains('access-form');if(button){button.disabled=true;if(isAccess)button.innerHTML='<span class="access-spinner" aria-hidden="true"></span> Procesando…';}f.setAttribute('aria-busy','true');const err=$('.form-error',f);if(err)err.textContent='';
    try{await submitForm(f);}catch(error){if(err&&err.isConnected){err.textContent=error.message;if(isAccess)err.focus();}else toast(error.message,true);}finally{busy=false;f.removeAttribute('aria-busy');if(button?.isConnected){button.disabled=false;if(isAccess)button.innerHTML=buttonContent;}}
  });
  document.addEventListener('change',async event=>{
    const target=event.target,f=target.closest('form');
    if(target.closest('[data-rule-day]'))syncRuleDay(target.closest('[data-rule-day]'));
    if(f?.dataset.form==='group'&&target.name==='account_id')f.elements.manager_id.innerHTML=managerOptions(target.value,'');
    if(f?.dataset.form==='person'&&target.name==='account_id')$('#group-checks').innerHTML=groupCheckboxes(target.value,f.dataset.id);
    if(f?.dataset.form==='person'&&target.name==='group_id')syncLeadOption();
    try{
      if(target.id==='month'){if(!target.value)return;month=target.value;await loadLedger();render();}
      if(target.name?.startsWith('filter-')){const key=target.name.slice(7);filters[key]=target.value;if(key==='group')filters.person='';await loadLedger();render();}
    }catch(error){toast(error.message,true);}
  });
  document.addEventListener('input',event=>{
    if(event.target.closest('.access-form')){
      const f=event.target.form;
      if(event.target.name==='identity')accessDraft.identity=event.target.value;
      if(f?.elements.password){const password=f.elements.password.value,confirm=f.elements.confirm.value;f.querySelector('[data-password-check="length"]')?.classList.toggle('satisfied',password.length>=10);f.querySelector('[data-password-check="match"]')?.classList.toggle('satisfied',confirm.length>0&&password===confirm);}
    }
    if(event.target.id==='team-search'){$$('[data-search-row]').forEach(row=>{row.hidden=!row.dataset.searchRow.includes(event.target.value.trim().toLowerCase());});}
  });
  $('#modal').addEventListener('close',()=>{if(!$('#modal').open)$('#modal').replaceChildren();});
  $('#modal').addEventListener('click',event=>{if(event.target===$('#modal')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close();}});
}
bind();
refresh().catch(error=>{if(!state)render();else toast(error.message,true);});
setInterval(tick,1000);
setInterval(()=>{if(state&&!busy&&!document.hidden&&!$('#modal').open&&!$('#delegation-editor')&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))refresh(true);},5000);

function aboutProject(){
  showModal('Acerca de Operational Pulse',`<div class="about-project"><div class="about-brand"><img src="/static/favicon.svg" width="50" height="50" alt=""><div><strong>Operational Pulse</strong><span>Versión 1.3.1 · OT y guardias</span></div>${kyndrylBrand()}</div><p>Control de horas extra (OT) y guardias, con timers, aprobaciones, historial y reportes en un solo lugar.</p><div class="about-divider"></div><p class="eyebrow">AUTORES DEL PROYECTO</p><div class="author-list">${projectAuthors.map(name=>`<article><span class="author-avatar">${esc(name.split(' ').slice(0,2).map(n=>n[0]).join(''))}</span><div><strong>${esc(name)}</strong><small>Autor del proyecto</small></div></article>`).join('')}</div><div class="about-bottom"><span class="live-dot"></span>Una operación más clara, desde el primer día.</div></div><footer class="dialog-footer">${btn('Cerrar','close','','primary')}</footer>`);
}
