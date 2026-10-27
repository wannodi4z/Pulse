'use strict';
// One state owner, one central route, one event controller. No route changes on polling.
let state = null;
let page = 'dashboard';
let month = new Date().toLocaleDateString('sv-SE', {timeZone:'America/Mexico_City'}).slice(0,7);
let ledger = {rows:[],ot_minutes:0,guard_minutes:0};
let filters = {group:'',person:'',status:'',kind:'',search:''};
let busy = false;
let refreshSequence = 0;
let toastTimer;
let serverOffset = 0;
const $ = (selector, root=document) => root.querySelector(selector);
const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const full = person => person ? `${person.first} ${person.last}`.trim() : 'Sin asignar';
const person = id => state?.people.find(p=>p.id===id);
const group = id => state?.groups.find(g=>g.id===id);
const manager = gid => person(group(gid)?.manager_id);
const me = () => state?.user;
const isAdmin = () => me()?.role==='ADMIN';
const isManager = () => me()?.role==='MANAGER';
const isTech = () => me()?.role==='USER';
const roles = {ADMIN:'Administrador',MANAGER:'Manager',USER:'Técnico'};
const statuses = {ACTIVE:'Activo',DISABLED:'Deshabilitado',PENDING_ACTIVATION:'Activación pendiente',SUBMITTED:'Pendiente',APPROVED:'Aprobado',REJECTED:'Rechazado',DOCUMENTATION:'Por documentar',RUNNING:'En curso',SCHEDULED:'Programado',COMPLETED:'Finalizado',PENDING:'Pendiente',ISSUED:'Código emitido',USED:'Recuperado'};
const pageNames = {dashboard:'Panel',organization:'Organización',admins:'Administradores',recoveries:'Recuperación de acceso',profile:'Mi perfil',team:'Mi equipo',teamTime:'Tiempo del equipo',timeRules:'Reglas de guardia',time:'Mi tiempo',claim:'Claim',adp:'ADP'};
const symbols = {dashboard:'▦',organization:'⌘',admins:'◇',recoveries:'↻',profile:'◎',team:'♧',teamTime:'≡',timeRules:'⚙',time:'◷',claim:'▤',adp:'▥'};
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
  if(!response.ok){if(response.status===401&&state){state=null;render();}throw Error(typeof result.detail==='string'?result.detail:'No se pudo completar la operación. Revisa los datos.');}
  return result;
}
function toast(message,error=false){
  const el=$('#toast');el.textContent=message;el.className=`visible ${error?'error':''}`;clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.className='',5000);
}
function showModal(title,body,wide=false){
  const modal=$('#modal');modal.innerHTML=`<header class="dialog-header"><div><p class="eyebrow">OPERATIONAL PULSE</p><h2>${title}</h2></div><button class="icon-btn" data-action="close" aria-label="Cerrar">×</button></header>${body}`;modal.className=wide?'wide':'';if(!modal.open)modal.showModal();
}
function form(name,body,id='',submit='Guardar'){
  return `<form data-form="${name}" data-id="${esc(id)}"><div class="form-body">${body}</div><p class="form-error" role="alert"></p><footer class="dialog-footer"><button type="button" class="secondary" data-action="close">Cancelar</button><button class="primary" type="submit">${submit}</button></footer></form>`;
}
function credentials(code,username,title='Datos de activación'){
  showModal(title,`<div class="form-body"><p>Entrega este código por un canal corporativo. La persona definirá su contraseña desde «Activar cuenta».</p>${username?`<p>Usuario: <strong>${esc(username)}</strong></p>`:''}<div class="secret-code">${esc(code)}</div><p class="muted">El código se muestra sólo al generar o regenerar el acceso.</p></div><footer class="dialog-footer">${btn('Listo','close','','primary')}</footer>`);
}
function login(){
  return `<div class="login-shell"><section class="login-story"><a class="brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>Operational<span class="brand-light">Pulse</span></span></a><div class="story-copy"><p class="eyebrow">TU OPERACIÓN, EN SINTONÍA</p><h1>Más claridad.<br>Mejor equipo.</h1><p>Personas, tiempo y decisiones.<br>Un solo espacio para conectar tu operación.</p><div class="pulse-line"><span></span><i></i><span></span></div></div><footer>Un espacio de trabajo para tu equipo <span>v2.0.0</span></footer></section><main class="login-main"><div class="login-card"><p class="eyebrow">BIENVENIDO A TU ESPACIO</p><h2>Comienza tu jornada</h2><p class="muted">Ingresa con tu Employee ID o usuario administrador.</p><form data-form="login">${field('identity','Usuario o Employee ID','','text','required autocomplete="username"')}${field('password','Contraseña','','password','required autocomplete="current-password"')}<p class="form-error" role="alert"></p><button class="primary login-submit">Iniciar sesión <span>→</span></button></form><div class="login-links">${btn('¿Olvidaste tu contraseña?','recovery-request','','link')}${btn('Activar cuenta','activate','','link')}</div><div class="login-note"><span>◇</span><p>Acceso interno<br><small>Tu información y tu equipo, en un mismo lugar.</small></p></div></div><footer>Operational Pulse · Gestión operativa</footer></main></div>`;
}
function nav(){
  const items=isAdmin()?['dashboard','organization','admins','recoveries','profile']:isManager()?['dashboard','team','teamTime','timeRules','recoveries','profile']:['dashboard','time','claim','adp',...(state.can_approve?['team','teamTime','recoveries']:[]),'profile'];
  return `<aside class="sidebar"><a class="brand" href="/" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>Operational<span class="brand-light">Pulse</span></span></a><p class="nav-label">ESPACIO DE TRABAJO</p><nav aria-label="Navegación principal">${items.map(p=>`<button class="nav-item ${p===page?'active':''}" data-page="${p}" ${p===page?'aria-current="page"':''}><span aria-hidden="true">${symbols[p]}</span>${pageNames[p]}${p==='teamTime'&&pendingCount()?`<b>${pendingCount()}</b>`:''}</button>`).join('')}</nav><div class="sidebar-bottom"><div class="workspace-tag"><i></i>Operación conectada<small>Operational Pulse · v${esc(state.version)}</small></div>${btn('↗ &nbsp; Cerrar sesión','logout','','logout')}</div></aside>`;
}
function pendingCount(){return state?[...state.overtime,...state.guards].filter(r=>r.status==='SUBMITTED'&&r.user_id!==me().id).length:0;}
function content(){
  switch(page){
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
  return `<div class="shell">${nav()}<div class="workspace"><header class="topbar"><div class="breadcrumb">Espacio de trabajo <span>/</span> <strong>${pageNames[page]||'Panel'}</strong></div><div class="topbar-right"><span class="local-time" data-local-clock></span><div class="topbar-person">${identity(me())}<span class="role-label">${roles[me().role]}${me().is_lead?' · Lead':''}</span></div></div></header><main id="main" tabindex="-1">${content()}<footer class="main-footer"><span>Operational Pulse</span><span>Hecho para una operación más clara.</span></footer></main></div></div>`;
}
function render(){
  $('#app').innerHTML=state?app():login();tick();
}
async function loadLedger(){
  if(!state)return;
  const q=new URLSearchParams({month});
  if(['time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);
  else{if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);}
  ledger=await api('/api/accounting?'+q);
}
async function refresh(silent=false){
  const sequence=++refreshSequence;
  try{
    const fresh=await api('/api/state');if(sequence!==refreshSequence)return;
    serverOffset=new Date(fresh.server_time).getTime()-Date.now();
    const previous=state?JSON.stringify({...state,server_time:''}):'';
    state=fresh;
    await loadLedger();if(sequence!==refreshSequence)return;
    if(!silent||previous!==JSON.stringify({...state,server_time:''})){
      if(!silent||!$('#modal').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))render();
    }
  }catch(error){if(!silent)throw error;}
}
async function navigate(next){
  if(!state)return;page=next;filters={group:'',person:'',status:'',kind:'',search:''};
  $('#modal').close();await loadLedger();render();$('#main')?.focus({preventScroll:true});
}
function tick(){
  $$('[data-elapsed]').forEach(el=>{const total=Math.max(0,Math.floor((Date.now()+serverOffset-new Date(el.dataset.elapsed).getTime())/1000));el.textContent=[Math.floor(total/3600),Math.floor(total/60)%60,total%60].map(x=>String(x).padStart(2,'0')).join(':');});
  const clock=$('[data-local-clock]');if(clock)clock.textContent=new Date(Date.now()+serverOffset).toLocaleTimeString('es-MX',{hour:'2-digit',minute:'2-digit',timeZone:state.timezone});
}
function kpi(label,value,detail,symbol,accent=''){
  return `<article class="kpi ${accent}"><div><span>${label}</span><i>${symbol}</i></div><strong>${value}</strong><small>${detail}</small></article>`;
}
function dashboard(){
  if(isAdmin()){
    return heading('VISTA GENERAL','Todo empieza con tu equipo.','Organiza personas y responsabilidades para que la operación fluya.',btn('＋ Crear cuenta','account-new','','primary'))+
    `<section class="welcome-banner"><div><span class="pill">ADMINISTRACIÓN</span><h2>Una estructura clara.<br>Un equipo conectado.</h2><p>De la Cuenta al Técnico: cada persona en su lugar.</p><button class="primary light" data-page="organization">Explorar organización <span>↗</span></button></div><div class="org-illustration" aria-hidden="true"><span>Cuenta</span><i></i><div><span>Manager</span><span>Manager</span></div><i></i><div><span>Grupo</span><span>Grupo</span><span>Grupo</span></div><p>● &nbsp; ● &nbsp; ● &nbsp; ● &nbsp; ●</p></div></section>
    <section class="kpis">${kpi('Cuentas',state.accounts.length,'La base de tu estructura','⌘')}${kpi('Managers',state.people.filter(p=>p.role==='MANAGER').length,'Responsables de la operación','♧')}${kpi('Grupos',state.groups.length,'Equipos conectados','▦')}${kpi('Técnicos',state.people.filter(p=>p.role==='USER').length,`${state.people.filter(p=>p.is_lead).length} con capacidad Lead`,'◎')}</section>
    <section class="two-columns"><article class="panel"><div class="section-heading"><div><p class="eyebrow">PRÓXIMOS PASOS</p><h2>Construye tu organización</h2></div></div><div class="step-row"><span>01</span><div><strong>Crea una Cuenta operativa</strong><small>Define el nombre y el código de tu operación.</small></div>${btn('Crear','account-new','','link')}</div><div class="step-row"><span>02</span><div><strong>Conecta Managers y Grupos</strong><small>Asigna responsabilidades dentro de cada Cuenta.</small></div><button class="link" data-page="organization">Organizar</button></div><div class="step-row"><span>03</span><div><strong>Incorpora a tus Técnicos</strong><small>Asigna su Grupo y, si corresponde, capacidad Lead.</small></div><button class="link" data-page="organization">Agregar</button></div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">ACCESOS</p><h2>Atención pendiente</h2></div></div><div class="attention-number">${state.recoveries.filter(r=>r.status==='PENDING').length}<small>solicitudes de recuperación</small></div><button class="secondary" data-page="recoveries">Revisar solicitudes →</button><p class="muted footnote">La información aparece cuando tu equipo comienza a trabajar. Sin datos de demostración.</p></article></section>`;
  }
  const ownTimers=state.timers.filter(t=>t.user_id===me().id);
  return heading('TU OPERACIÓN AL DÍA',`Hola, ${esc(me().first)}.`,isTech()?'Tu tiempo, tus próximos pasos y el avance del mes.':'Un vistazo al tiempo y las prioridades de tu equipo.',monthControl())+
  (ownTimers.length?timerPanel(ownTimers):'')+
  `<section class="kpis">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real, sin duplicados','↗')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Con OT descontada','◷')}${kpi('Por revisar',isTech()?state.overtime.filter(o=>o.user_id===me().id&&o.status==='SUBMITTED').length:pendingCount(),'Solicitudes pendientes','≡')}${kpi('Timers activos',state.timers.length,'Actualización en tiempo real','●','accent')}</section>
  <section class="two-columns"><article class="panel"><div class="section-heading"><div><p class="eyebrow">ANALÍTICA MENSUAL</p><h2>${esc(monthLabel(month))}</h2></div><span class="pill">Horas aprobadas</span></div>${analyticsChart()}<div class="legend"><span><i class="dot ot"></i>Tiempo extra</span><span><i class="dot guard"></i>Guardia neta</span></div></article><article class="panel"><div class="section-heading"><div><p class="eyebrow">REQUIERE TU ATENCIÓN</p><h2>El siguiente paso</h2></div></div>${isTech()?`<div class="attention-number">${state.overtime.filter(o=>o.user_id===me().id&&o.status==='DOCUMENTATION').length}<small>registros por documentar</small></div><button class="secondary" data-page="time">Ir a Mi tiempo →</button>`:`<div class="attention-number">${pendingCount()}<small>registros pendientes de revisión</small></div><button class="secondary" data-page="teamTime">Revisar tiempo del equipo →</button>`}<div class="quick-note">${isTech()?'Claim, ADP y Excel se calculan sobre el mismo tiempo aprobado.':'La autoridad de los Leads depende de una delegación temporal activa.'}</div></article></section>
  ${state.timers.length&&!isTech()?`<article class="panel"><div class="section-heading"><div><p class="eyebrow">AHORA</p><h2>Tu equipo en tiempo real</h2></div><span class="live-label"><i></i>En vivo</span></div>${timerPanel(state.timers)}</article>`:''}`;
}
function analyticsChart(){
  const byDay=new Map();ledger.rows.forEach(r=>{const day=Number(r.date.slice(-2));if(!byDay.has(day))byDay.set(day,{OT:0,GUARD:0});byDay.get(day)[r.kind]+=r.minutes/60;});
  if(!byDay.size)return empty('Tu mes está por comenzar','Aquí verás las horas aprobadas de tu operación.');
  const days=new Date(Number(month.slice(0,4)),Number(month.slice(5)),0).getDate();
  const max=Math.max(1,...[...byDay.values()].map(d=>d.OT+d.GUARD));
  // SVG keeps the visualization self-contained and avoids inline styles under CSP.
  let bars='';for(let d=1;d<=days;d++){const v=byDay.get(d)||{OT:0,GUARD:0},x=14+(d-1)*17,h1=v.OT/max*130,h2=v.GUARD/max*130;bars+=`<rect x="${x}" y="${150-h1}" width="10" height="${h1}" rx="2" fill="#286b70"><title>${d}: ${v.OT.toFixed(2)} h OT</title></rect><rect x="${x}" y="${150-h1-h2}" width="10" height="${h2}" rx="2" fill="#a5d7c7"><title>${d}: ${v.GUARD.toFixed(2)} h Guardia</title></rect>${d===1||d%5===0?`<text x="${x+5}" y="172" text-anchor="middle" fill="#748287" font-size="10">${d}</text>`:''}`;}
  return `<div class="chart"><svg role="img" aria-label="Horas aprobadas por día, tiempo extra y Guardia neta" viewBox="0 0 545 185"><path d="M8 150H540" stroke="#e1e7e5"/>${bars}</svg></div>`;
}
function organizationPage(){
  return heading('PERSONAS Y ESTRUCTURA','Organización','Cada Cuenta, sus Managers y los equipos que hacen que todo suceda.',btn('＋ Nueva cuenta','account-new','','primary'))+
  `<div class="organization-summary"><span><b>${state.accounts.length}</b> Cuentas</span><span><b>${state.people.filter(p=>p.role==='MANAGER').length}</b> Managers</span><span><b>${state.groups.length}</b> Grupos</span><span><b>${state.people.filter(p=>p.role==='USER').length}</b> Técnicos</span><span class="muted">Lead es una capacidad, no un nivel jerárquico.</span></div>`+
  (state.accounts.length?state.accounts.map(a=>{
    const groups=state.groups.filter(g=>g.account_id===a.id),managers=state.people.filter(p=>p.role==='MANAGER'&&p.account_id===a.id),techs=state.people.filter(p=>groups.some(g=>g.id===p.group_id)),unassigned=groups.filter(g=>!g.manager_id);
    return `<section class="account-block" data-account="${esc(a.id)}"><header class="account-header"><span class="account-code">${esc(a.code)}</span><div class="grow"><p class="eyebrow">CUENTA OPERATIVA</p><h2>${esc(a.name)}</h2><p>${managers.length} Managers <span>·</span> ${groups.length} Grupos <span>·</span> ${techs.length} Técnicos</p></div><div class="entity-actions">${btn('Editar','account-edit',a.id)}${btn('Eliminar','account-delete',a.id,'text-danger')}${btn('＋ Manager','manager-new',a.id)}${btn('＋ Grupo','group-new',a.id,'primary')}</div></header><div class="account-body">${managers.map(m=>managerBlock(m,groups.filter(g=>g.manager_id===m.id))).join('')}${unassigned.length?`<section class="unassigned"><div class="section-heading"><h3>Grupos sin Manager</h3><span class="pill">Pendientes de asignación</span></div><div class="group-grid">${unassigned.map(groupCard).join('')}</div></section>`:''}${!groups.length&&!managers.length?empty('Una Cuenta lista para crecer','Agrega tu primer Manager o Grupo para comenzar.') : ''}</div></section>`;
  }).join(''):empty('Dale forma a tu operación','Crea tu primera Cuenta. Después podrás agregar Managers, Grupos y Técnicos.'));
}
function managerBlock(m,groups){
  const summary=groups.length>1?`Multigrupo · ${groups.length} grupos`:groups.length?'1 grupo':'Sin grupos asignados';
  return `<section class="manager-block" data-manager="${esc(m.id)}"><header class="manager-header">${identity(m)}<div class="manager-meta"><span class="small-label">MANAGER</span><span>${summary}</span></div><div class="entity-actions">${m.status==='PENDING_ACTIVATION'?btn('Activación','activation-code',m.id,'link'):''}${btn('Editar','person-edit',m.id)}</div></header><div class="group-grid">${groups.map(groupCard).join('')||empty('Sin Grupos asignados','Edita al Manager para asignar Grupos de esta Cuenta.')}</div></section>`;
}
function groupCard(g){
  const people=state.people.filter(p=>p.role==='USER'&&p.group_id===g.id);
  return `<article class="group-card" data-group="${esc(g.id)}"><header><div><span class="small-label">GRUPO · ${esc(g.code)}</span><h3>${esc(g.name)}</h3><small>${people.length} Técnicos</small></div><div class="entity-actions">${btn('Editar','group-edit',g.id,'link')}${btn('Eliminar','group-delete',g.id,'text-danger')}</div></header><div class="technicians">${people.map(u=>`<div class="technician" data-person="${esc(u.id)}">${identity(u)}${u.is_lead?'<span class="lead-pill">Lead</span>':''}${btn('Editar','person-edit',u.id,'link')}</div>`).join('')||'<p class="quiet-empty">Aún no hay Técnicos en este Grupo.</p>'}</div><footer>${btn('＋ Agregar Técnico','tech-new',g.id,'link')}</footer></article>`;
}
function adminsPage(){return heading('GOBERNANZA','Administradores','Accesos con autoridad para administrar la estructura y las cuentas.',btn('＋ Administrador','admin-new','','primary'))+peopleTable(state.people.filter(p=>p.role==='ADMIN'));}
function peopleTable(people){
  return `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Persona</th><th>Correo</th><th>Rol / Grupo</th><th>Estado</th><th class="right">Acciones</th></tr></thead><tbody>${people.map(p=>`<tr data-search-row="${esc(`${full(p)} ${p.employee_id||p.username} ${p.email}`.toLowerCase())}"><td><div class="table-identity">${identity(p)}${p.is_lead?'<span class="lead-pill">Lead</span>':''}</div></td><td>${esc(p.email)}</td><td>${esc(p.role==='USER'?group(p.group_id)?.name||'Sin Grupo':roles[p.role])}</td><td>${badge(p.status)}</td><td><div class="row-actions">${btn('Editar','person-edit',p.id,'link')}${isAdmin()&&p.status==='PENDING_ACTIVATION'?btn('Activación','activation-code',p.id,'link'):''}</div></td></tr>`).join('')}</tbody></table></div>${!people.length?empty('Sin personas todavía','Los nuevos integrantes aparecerán aquí.'):''}</section>`;
}
function teamPage(){
  const people=state.people.filter(p=>p.role==='USER'&&state.scope.includes(p.group_id));
  return heading('PERSONAS','Mi equipo','Técnicos de los Grupos bajo tu responsabilidad.',isManager()?btn('＋ Técnico','tech-new',state.groups[0]?.id||'','primary'):'')+
  `<section class="panel compact"><label class="search"><span>⌕</span><input id="team-search" placeholder="Buscar por nombre, Employee ID o correo" aria-label="Buscar Técnicos"></label></section>`+peopleTable(people)+
  (isManager()?`<section class="panel"><div class="section-heading"><div><p class="eyebrow">CONTINUIDAD OPERATIVA</p><h2>Delegación temporal</h2><p class="muted">Asigna un Lead como backup sin cambiar su capacidad.</p></div>${btn('＋ Delegar','delegation-new','','secondary')}</div>${state.delegations.length?`<div class="delegation-list">${state.delegations.map(d=>`<article><div><strong>${esc(full(person(d.lead_id)))}</strong><small>${range(d.start_at,d.end_at)} · ${d.group_ids.length} Grupos</small></div>${d.revoked_at?'<span class="pill">Revocada</span>':new Date(d.end_at)<=new Date()?'<span class="pill">Finalizada</span>':btn('Revocar','delegation-revoke',d.id,'text-danger')}</article>`).join('')}</div>`:empty('Sin delegaciones','La aprobación permanece con el Manager.')}</section>`:'');
}
function timerPanel(timers){
  return `<section class="timer-list">${timers.map(t=>`<article class="timer-card"><span class="live-dot"></span><div><span class="small-label">${t.user_id===me().id?'TU TIMER ACTIVO':esc(full(person(t.user_id)))}</span><strong>${state.overtime.find(o=>o.id===t.overtime_id)?.capture_type==='EMERGENCY'?'OT de emergencia':'OT programada'}</strong><small>Inicio: ${fmtTime(t.start_at)}</small></div><span class="timer-clock" data-elapsed="${esc(t.start_at)}">00:00:00</span>${t.user_id===me().id?btn('■ Detener','timer-stop',t.id,'danger'):''}</article>`).join('')}</section>`;
}
function exportLink(extra=''){
  const q=new URLSearchParams({month});if(['time','claim','adp'].includes(page)&&isTech())q.set('user_id',me().id);else{if(filters.group)q.set('group_id',filters.group);if(filters.person)q.set('user_id',filters.person);if(filters.kind)q.set('kind',filters.kind);}
  return `<a class="secondary button" href="/api/export.xlsx?${esc(q.toString())}" download>↓ Excel ${extra||'aprobados'}</a>`;
}
function timePage(){
  const own=state.overtime.filter(o=>o.user_id===me().id&&(o.start_at||o.scheduled_start||o.created_at).slice(0,7)===month);
  const guards=state.guards.filter(g=>g.user_id===me().id&&g.start_date.slice(0,7)<=month&&g.end_date.slice(0,7)>=month);
  const shared=state.windows.filter(w=>w.group_id===me().group_id&&w.status==='APPROVED'&&new Date(w.scheduled_end)>new Date());
  return heading('TU JORNADA','Mi tiempo','Programa, registra y da seguimiento a tu tiempo operativo.',monthControl()+exportLink())+
  timerPanel(state.timers.filter(t=>t.user_id===me().id))+
  `<section class="time-actions">${btn('＋ Programar OT','ot-new','','primary')}${btn('⚡ Iniciar emergencia','timer-start','','secondary')}${btn('＋ Solicitar Guardia','guard-new','','secondary')}</section><section class="kpis three">${kpi('Tiempo extra aprobado',`${hours(ledger.ot_minutes)} <em>h</em>`,'Tiempo real trabajado','↗')}${kpi('Guardia neta',`${hours(ledger.guard_minutes)} <em>h</em>`,'Guardia aprobada menos OT','◷')}${kpi('Total del mes',`${hours(ledger.ot_minutes+ledger.guard_minutes)} <em>h</em>`,'Mismo cálculo en Claim y ADP','▦')}</section>
  ${shared.length?`<section class="panel"><div class="section-heading"><div><p class="eyebrow">CON TU GRUPO</p><h2>OT programada compartida</h2></div></div><div class="record-list">${shared.map(w=>`<article class="record-card"><div><span class="small-label">${esc(w.reference)}</span><h3>${esc(w.description)}</h3><p>${range(w.scheduled_start,w.scheduled_end)}</p></div>${state.overtime.some(o=>o.window_id===w.id&&o.user_id===me().id)?'<span class="pill">Ya participas</span>':btn('Participar','window-join',w.id,'secondary')}</article>`).join('')}</div></section>`:''}
  <section class="panel"><div class="section-heading"><div><p class="eyebrow">TIEMPO EXTRA</p><h2>Tus registros</h2></div><span class="pill">${own.length} registros</span></div><div class="record-list">${own.map(otCard).join('')||empty('Sin OT en este mes','Programa una OT o inicia un Timer de emergencia.')}</div></section>
  <section class="panel"><div class="section-heading"><div><p class="eyebrow">COBERTURA</p><h2>Guardias</h2></div></div><div class="record-list">${guards.map(g=>`<article class="record-card"><div><span class="small-label">${esc(g.rule_snapshot.name)}</span><h3>${fmtDate(g.start_date)} → ${fmtDate(g.end_date)}</h3><p>Solicitud individual · ${esc(g.id.slice(0,8).toUpperCase())}</p></div>${badge(g.status)}</article>`).join('')||empty('Sin Guardias en este mes','Solicita cobertura con una regla vigente de tu Manager.')}</div></section>`;
}
function otCard(o){
  const active=state.timers.some(t=>t.overtime_id===o.id),canStart=o.status==='APPROVED'&&o.execution==='SCHEDULED'&&new Date(o.scheduled_start)<=new Date()&&new Date(o.scheduled_end)>new Date();
  return `<article class="record-card"><div class="grow"><div class="record-title"><span class="small-label">${o.capture_type==='EMERGENCY'?'EMERGENCIA':o.capture_type==='HISTORICAL'?'OT HISTÓRICA':'OT PROGRAMADA'}</span>${badge(active?'RUNNING':o.status)}</div><h3>${esc(o.reference||'Pendiente de documentación')}</h3><p>${esc(o.description||'Detén el Timer y documenta el trabajo realizado.')}</p><small>${o.start_at?`Real: ${range(o.start_at,o.end_at)}`:`Programado: ${range(o.scheduled_start,o.scheduled_end)}`}</small>${o.revision?`<small>Revisión ${o.revision} · La última edición requiere aprobación.</small>`:''}</div><div class="entity-actions">${!active?btn(o.status==='DOCUMENTATION'?'Documentar':'Editar y reenviar','ot-edit',o.id,'secondary'):''}${canStart?btn('▶ Iniciar','timer-planned',o.id,'primary'):''}</div></article>`;
}
function teamTimePage(){
  const people=state.people.filter(p=>p.role==='USER'&&state.scope.includes(p.group_id));
  return heading('OPERACIÓN Y TRAZABILIDAD','Tiempo del equipo','Aprobaciones e historial unificados. Revisa cada decisión en su contexto.',monthControl()+btn('＋ OT compartida','window-new','','primary')+exportLink())+
  `<section class="panel filters"><div>${select('filter-group','Grupo',options(state.groups,filters.group,x=>x.name,'Todos los Grupos'))}${select('filter-person','Técnico',options(people.filter(p=>!filters.group||p.group_id===filters.group),filters.person,full,'Todos los Técnicos'))}${select('filter-status','Estado',`<option value="">Todos los estados</option>${['SUBMITTED','APPROVED','REJECTED','DOCUMENTATION','RUNNING'].map(s=>`<option value="${s}" ${filters.status===s?'selected':''}>${statuses[s]}</option>`).join('')}`)}${select('filter-kind','Tipo',`<option value="">OT y Guardias</option><option value="OT" ${filters.kind==='OT'?'selected':''}>Tiempo extra</option><option value="GUARD" ${filters.kind==='GUARD'?'selected':''}>Guardia</option>`)}</div><p class="muted footnote">Excel incluye únicamente tiempo real aprobado del mes y alcance seleccionados.</p></section>`+
  timerPanel(state.timers.filter(t=>!filters.person||t.user_id===filters.person).filter(t=>!filters.group||person(t.user_id)?.group_id===filters.group))+
  `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Técnico / Grupo</th><th>Registro</th><th>Periodo</th><th>Estado</th><th class="right">Acciones</th></tr></thead><tbody>${teamRows()}</tbody></table></div>${!teamRecords().length?empty('No hay registros con estos filtros','Los tiempos enviados por tu equipo aparecerán aquí.'):''}</section>`;
}
function teamRecords(){
  const endMonth=new Date(Number(month.slice(0,4)),Number(month.slice(5)),1).toLocaleDateString('sv-SE');
  return [...state.overtime.map(o=>({...o,kind:'ot',filterKind:'OT',a:o.start_at||o.scheduled_start||o.created_at,b:o.end_at||o.scheduled_end||o.created_at})),...state.guards.map(g=>({...g,kind:'guard',filterKind:'GUARD',a:g.start_date,b:g.end_date}))].filter(r=>{
    const u=person(r.user_id);return state.scope.includes(u?.group_id)&&(!filters.group||u.group_id===filters.group)&&(!filters.person||u.id===filters.person)&&(!filters.kind||r.filterKind===filters.kind)&&(!filters.status||r.status===filters.status||filters.status==='RUNNING'&&r.execution==='RUNNING')&&r.a.slice(0,10)<endMonth&&r.b.slice(0,10)>=month+'-01';
  }).sort((a,b)=>b.created_at.localeCompare(a.created_at));
}
function teamRows(){return teamRecords().map(r=>`<tr><td><strong>${esc(full(person(r.user_id)))}</strong><small>${esc(person(r.user_id)?.employee_id)} · ${esc(group(person(r.user_id)?.group_id)?.name)}</small></td><td><span class="small-label">${r.kind==='ot'?'TIEMPO EXTRA':'GUARDIA'}</span><strong>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</strong><small>${esc(r.description||'')}</small></td><td>${fmtDate(r.a)}<small>${r.kind==='ot'?`${fmtTime(r.a)} — ${fmtTime(r.b)}`:fmtDate(r.b)}</small></td><td>${badge(r.execution==='RUNNING'?'RUNNING':r.status)}</td><td><div class="row-actions">${btn('Detalle','record-detail',`${r.kind}:${r.id}`,'link')}${r.status==='SUBMITTED'&&r.user_id!==me().id&&r.execution!=='RUNNING'?btn('Aprobar','approve',`${r.kind}:${r.id}`,'primary small')+btn('Rechazar','reject',`${r.kind}:${r.id}`,'text-danger'):''}</div></td></tr>`).join('');}
function rulesPage(){
  const days=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
  return heading('COBERTURA OPERATIVA','Reglas de Guardia','Las solicitudes conservan una copia de la regla vigente al momento de crearse.',btn('＋ Crear regla','rule-new','','primary'))+
  `<div class="rules-grid">${state.rules.map(r=>`<article class="panel"><span class="small-label">VIGENTE DESDE ${fmtDate(r.effective_from)}</span><h2>${esc(r.name)}</h2><div class="rule-segments">${r.segments.map(s=>`<div><strong>${days[s.day]}</strong><span>${esc(s.start)} — ${esc(s.end)}${s.end<=s.start?' (+1 día)':''}</span></div>`).join('')}</div></article>`).join('')||empty('Define la cobertura de tu equipo','Agrega segmentos por día para habilitar solicitudes de Guardia.')}</div>`;
}
function capturePage(kind){
  const grouped=new Map();ledger.rows.forEach(r=>{const day=new Date(r.date+'T12:00:00'),weekday=day.getDay(),offset=kind==='claim'?(weekday+1)%7:weekday;day.setDate(day.getDate()-offset);const week=day.toLocaleDateString('sv-SE');if(!grouped.has(week))grouped.set(week,[]);grouped.get(week).push(r);});
  return heading('CAPTURA MENSUAL',kind==='claim'?'Claim':'ADP',kind==='claim'?'Guía semanal de sábado a viernes. Sólo tiempo aprobado.':'Guía semanal de domingo a sábado. Inicio y duración HH:MM.',monthControl()+exportLink())+
  `<section class="capture-summary"><div><span>Tiempo extra</span><strong>${hours(ledger.ot_minutes)} <small>h</small></strong></div><div><span>Guardia neta</span><strong>${hours(ledger.guard_minutes)} <small>h</small></strong></div><p>Una misma fuente de cálculo.<br><strong>Sin duplicar OT ni traslapes con Guardia.</strong></p></section>`+
  ([...grouped].map(([week,rows])=>`<section class="panel table-panel"><div class="section-heading padded"><div><p class="eyebrow">SEMANA ${kind==='claim'?'CLAIM':'ADP'}</p><h2>Desde ${fmtDate(week)}</h2></div><span class="pill">${hours(rows.reduce((n,r)=>n+r.minutes,0))} h</span></div><div class="table-scroll"><table><thead><tr><th>Fecha</th><th>Tipo</th><th>Referencia</th><th>Inicio</th><th>${kind==='claim'?'Horas decimales':'Duración HH:MM'}</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${fmtDate(r.date)}</td><td>${r.kind==='OT'?'Onsite Overtime':'Stand-by'}</td><td>${esc(r.reference||'—')}</td><td>${r.start}</td><td><strong>${kind==='claim'?hours(r.minutes):hm(r.minutes)}</strong></td></tr>`).join('')}</tbody></table></div></section>`).join('')||empty('Sin tiempo aprobado en este mes','Tus registros aparecerán después de la aprobación de tu Manager o Lead delegado.'));
}
function recoveriesPage(){
  return heading('ACCESO SEGURO','Recuperación de acceso','Valida la identidad de la persona antes de emitir un código de un solo uso.')+
  `<section class="panel table-panel"><div class="table-scroll"><table><thead><tr><th>Persona</th><th>Solicitud</th><th>Estado</th><th>Vigencia</th><th class="right">Acción</th></tr></thead><tbody>${state.recoveries.map(r=>`<tr><td><strong>${esc(full(person(r.user_id)))}</strong><small>${esc(person(r.user_id)?.employee_id||person(r.user_id)?.username)}</small></td><td>${fmtDate(r.created_at)}</td><td>${badge(r.status)}</td><td>${r.expires_at?`${fmtDate(r.expires_at)} · ${fmtTime(r.expires_at)}`:'—'}</td><td class="right">${r.status!=='USED'&&r.user_id!==me().id?btn(r.status==='ISSUED'?'Reemitir código':'Emitir código','recovery-issue',r.id,'secondary small'):'—'}</td></tr>`).join('')}</tbody></table></div>${!state.recoveries.length?empty('Todo en orden','No hay solicitudes de recuperación en tu alcance.'):''}</section>`;
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
  showModal(id?'Editar Grupo':'Nuevo Grupo',form('group',select('account_id','Cuenta *',options(state.accounts,selected,x=>`${x.code} · ${x.name}`),'required')+field('code','Código de Grupo *',g.code,'text','required maxlength="24"')+field('name','Nombre del Grupo *',g.name,'text','required maxlength="100"')+select('manager_id','Manager',managerOptions(selected,g.manager_id)),id));
}
function managerOptions(aid,selected){return options(state.people.filter(p=>p.role==='MANAGER'&&p.account_id===aid),selected,full,'Sin Manager');}
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
  showModal(id?'Editar persona':r==='MANAGER'?'Nuevo Manager':r==='ADMIN'?'Nuevo administrador':'Nuevo Técnico',form('person',`<input name="role" type="hidden" value="${r}"><div class="form-grid">${field('first','Nombre *',p.first,'text','required')}${field('last','Apellido *',p.last,'text','required')}</div>${r==='ADMIN'?field('username','Usuario *',p.username,'text','required autocomplete="off"'):field('employee_id','Employee ID *',p.employee_id,'text',`required ${id?'readonly':''}`)}${field('email','Correo *',p.email,'email','required')}${r==='MANAGER'?select('account_id','Cuenta *',options(state.accounts,aid,x=>`${x.code} · ${x.name}`),'required')+`<fieldset><legend>Grupos disponibles</legend><div id="group-checks">${groupCheckboxes(aid,id)}</div></fieldset><p class="muted footnote">Sólo aparecen los Grupos de esta Cuenta que están libres o ya pertenecen a este Manager.</p>`:''}${r==='USER'?select('group_id','Grupo *',options(availableGroups,gid,x=>`${x.code} · ${x.name}`),'required')+`<label class="checkbox" id="lead-option"><input name="is_lead" type="checkbox" ${p.is_lead?'checked':''}><span>Designar como Lead</span></label><p class="muted" id="lead-note"></p><p class="muted footnote">Ser Lead no habilita aprobaciones. La delegación temporal se administra por separado.</p>`:''}${id?select('status','Estado',Object.entries({ACTIVE:'Activo',DISABLED:'Deshabilitado',PENDING_ACTIVATION:'Activación pendiente'}).filter(([s])=>s===p.status||s==='DISABLED'||s==='ACTIVE'&&p.status!=='PENDING_ACTIVATION').map(([s,l])=>`<option value="${s}" ${p.status===s?'selected':''}>${l}</option>`).join('')):'<p class="callout">La cuenta se creará pendiente de activación. Recibirás un código para su primer acceso.</p>'}`,id));
  syncLeadOption();
}
function syncLeadOption(){
  const form=$('[data-form="person"]');if(!form?.elements.group_id)return;
  const holder=state.people.find(p=>p.group_id===form.elements.group_id.value&&p.is_lead&&p.id!==form.dataset.id);
  $('#lead-option').hidden=!!holder;form.elements.is_lead.disabled=!!holder;if(holder)form.elements.is_lead.checked=false;
  $('#lead-note').textContent=holder?`Lead actual del grupo: ${full(holder)} · ${holder.employee_id}`:'';
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
  showModal('Nueva regla de Guardia',form('rule',field('name','Nombre de la regla *','','text','required')+field('effective_from','Vigente desde *',new Date().toLocaleDateString('sv-SE'),'date','required')+`<fieldset><legend>Segmentos semanales</legend><p class="muted footnote">Selecciona los días con cobertura. Si el fin es igual o anterior al inicio, termina al día siguiente.</p>${['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].map((day,i)=>`<div class="segment-row"><label class="checkbox"><input type="checkbox" name="days" value="${i}"><span>${day}</span></label><input name="start_${i}" type="time" value="00:00" aria-label="Inicio ${day}"><span>→</span><input name="end_${i}" type="time" value="08:00" aria-label="Fin ${day}"></div>`).join('')}</fieldset>`));
}
function windowModal(){
  const groups=state.groups.filter(g=>state.scope.includes(g.id));
  if(!groups.length)return toast('No hay Grupos disponibles en tu alcance.',true);
  showModal('OT compartida con el Grupo',form('window',select('group_id','Grupo *',options(groups,'',x=>`${x.code} · ${x.name}`),'required')+`<div class="form-grid">${field('scheduled_start','Inicio *','','datetime-local','required')}${field('scheduled_end','Fin *','','datetime-local','required')}</div>`+field('reference','Referencia completa CHG / INC *','','text','required')+`<label class="field"><span>Descripción *</span><textarea name="description" required rows="3"></textarea></label><p class="callout">Cada Técnico podrá participar una sola vez y ejecutar su propio Timer. Su tiempo real se enviará a aprobación al detenerlo.</p>`,'','Publicar ventana'));
}
function delegationModal(){
  const leads=state.people.filter(p=>p.is_lead&&state.scope.includes(p.group_id));
  if(!leads.length)return toast('Designa un Técnico como Lead antes de delegar.',true);
  showModal('Delegar autoridad temporal',form('delegation',select('lead_id','Lead *',options(leads,'',full),'required')+`<div class="form-grid">${field('start_at','Desde *',localInput(new Date().toISOString()),'datetime-local','required')}${field('end_at','Hasta *','','datetime-local','required')}</div><fieldset><legend>Grupos bajo la delegación</legend>${state.groups.filter(g=>state.scope.includes(g.id)).map(g=>`<label class="checkbox"><input type="checkbox" name="group_ids" value="${esc(g.id)}"><span>${esc(g.name)}</span></label>`).join('')}</fieldset><p class="callout">El Lead no podrá aprobar sus propios registros. Puedes revocar la delegación en cualquier momento.</p>`,'','Activar delegación'));
}
function publicModal(kind){
  if(kind==='activate')showModal('Activar cuenta',form('activate',field('identity','Employee ID o usuario *','','text','required autocomplete="username"')+field('code','Código de activación *','','text','required autocomplete="off"')+field('password','Crea tu contraseña *','','password','required minlength="10" autocomplete="new-password"')+field('confirm','Confirma tu contraseña *','','password','required minlength="10" autocomplete="new-password"'),'','Activar cuenta'));
  if(kind==='request')showModal('Recuperar acceso',form('recovery-request',`<p class="muted">Tu Manager o un administrador validará tu identidad y te entregará un código temporal.</p>${field('identity','Employee ID o usuario *','','text','required')}<button type="button" class="link" data-action="recovery-complete">Ya tengo un código</button>`,'','Solicitar recuperación'));
  if(kind==='complete')showModal('Restablecer contraseña',form('recovery-complete',field('identity','Employee ID o usuario *','','text','required')+field('code','Código temporal *','','text','required')+field('password','Nueva contraseña *','','password','required minlength="10"')+field('confirm','Confirmar contraseña *','','password','required minlength="10"'),'','Restablecer'));
}
function detailModal(key){
  const [kind,id]=key.split(':'),r=(kind==='ot'?state.overtime:state.guards).find(r=>r.id===id);if(!r)return;
  const logs=state.audit.filter(a=>a.entity_id===id);
  showModal('Detalle del registro',`<div class="form-body"><div class="detail-hero">${identity(person(r.user_id))}${badge(r.status)}</div><dl><dt>Registro</dt><dd>${esc(r.reference||r.rule_snapshot?.name||'Por documentar')}</dd><dt>Periodo</dt><dd>${kind==='ot'?range(r.start_at||r.scheduled_start,r.end_at||r.scheduled_end):`${fmtDate(r.start_date)} → ${fmtDate(r.end_date)}`}</dd>${kind==='ot'?`<dt>Descripción</dt><dd>${esc(r.description||'—')}</dd><dt>Justificación</dt><dd>${esc(r.justification||'—')}</dd><dt>Impacto</dt><dd>${esc(r.impact||'—')}</dd><dt>Tiempo compensatorio</dt><dd>${esc(r.in_lieu||'—')}</dd><dt>Revisiones</dt><dd>${r.revision}</dd>`:''}</dl><h3>Trazabilidad</h3><div class="audit-list">${logs.map(a=>{let d={};try{d=JSON.parse(a.detail)}catch{}return `<div><span></span><p><strong>${esc(auditLabel(a.action))}</strong><small>${fmtDate(a.created_at)} · ${fmtTime(a.created_at)} · ${esc(full(person(a.actor_id)))}</small>${d.reason?`<small>${esc(d.reason)}</small>`:''}</p></div>`;}).join('')||'<p class="muted">Sin eventos disponibles.</p>'}</div></div><footer class="dialog-footer">${btn('Cerrar','close','','secondary')}</footer>`);
}
function auditLabel(action){return {CREATE_OT:'Registro de OT',EDIT_OT_REOPEN_APPROVAL:'Edición y reenvío a aprobación',REQUEST_GUARD:'Solicitud de Guardia',APPROVED:'Aprobado',REJECTED:'Rechazado',START_TIMER:'Timer iniciado',STOP_TIMER:'Timer detenido',JOIN_SHARED_OT:'Participación en OT compartida'}[action]||action;}

async function perform(action,id,button){
  switch(action){
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
    case 'account-delete':if(!confirm('¿Eliminar esta Cuenta vacía?'))return;await api('/api/accounts/'+id,'DELETE');break;
    case 'group-delete':if(!confirm('¿Eliminar este Grupo vacío? Se conserva cualquier Grupo con historial.'))return;await api('/api/groups/'+id,'DELETE');break;
    case 'activation-code':{if(!confirm('¿Generar un nuevo código? El código anterior dejará de funcionar.'))return;const r=await api(`/api/people/${id}/activation`,'POST',{});credentials(r.activation_code,person(id)?.username);return;}
    case 'activate':publicModal('activate');return;
    case 'recovery-request':publicModal('request');return;
    case 'recovery-complete':publicModal('complete');return;
    case 'recovery-issue':{const r=await api(`/api/recoveries/${id}/issue`,'POST',{});await refresh();showModal('Código de recuperación',`<div class="form-body"><p>Entrega este código después de validar la identidad de la persona.</p><div class="secret-code">${esc(r.code)}</div><p>Vence el ${fmtDate(r.expires_at)} a las ${fmtTime(r.expires_at)}. Sólo puede usarse una vez.</p></div><footer class="dialog-footer">${btn('Listo','close','','primary')}</footer>`);return;}
    case 'ot-new':otModal();return;
    case 'ot-edit':otModal(id);return;
    case 'guard-new':guardModal();return;
    case 'rule-new':ruleModal();return;
    case 'window-new':windowModal();return;
    case 'window-join':await api(`/api/windows/${id}/join`,'POST',{});break;
    case 'delegation-new':delegationModal();return;
    case 'delegation-revoke':if(!confirm('¿Revocar esta delegación? La capacidad Lead se conserva.'))return;await api('/api/delegations/'+id,'DELETE');break;
    case 'timer-start':if(!confirm('¿Iniciar ahora un Timer de OT de emergencia?'))return;await api('/api/timers/start','POST',{});break;
    case 'timer-planned':await api('/api/timers/start','POST',{overtime_id:id});break;
    case 'timer-stop':await api(`/api/timers/${id}/stop`,'POST',{});break;
    case 'approve':{const [kind,identity]=id.split(':');await api(`/api/approvals/${kind}/${identity}`,'POST',{decision:'APPROVED'});break;}
    case 'reject':showModal('Rechazar registro',form('reject',`<label class="field"><span>Motivo del rechazo *</span><textarea name="reason" rows="4" required></textarea></label>`,id,'Rechazar registro'));return;
    case 'record-detail':detailModal(id);return;
    case 'month-prev':case 'month-next':{const d=new Date(`${month}-15T12:00:00`);d.setMonth(d.getMonth()+(action==='month-next'?1:-1));month=d.toLocaleDateString('sv-SE').slice(0,7);await loadLedger();render();return;}
    default:return;
  }
  await refresh();toast('Cambios guardados.');
}
async function submitForm(f){
  const fd=new FormData(f),data=Object.fromEntries(fd),kind=f.dataset.form,id=f.dataset.id;
  if(['password','activate','recovery-complete'].includes(kind)&&data.password!==data.confirm)throw Error('Las contraseñas no coinciden.');
  let response;
  switch(kind){
    case 'login':await api('/api/login','POST',data);page='dashboard';await refresh();return;
    case 'activate':await api('/api/activate','POST',data);$('#modal').close();toast('Cuenta activada. Ya puedes iniciar sesión.');return;
    case 'recovery-request':response=await api('/api/recoveries','POST',data);$('#modal').close();toast(response.message);return;
    case 'recovery-complete':await api('/api/recoveries/complete','POST',data);$('#modal').close();toast('Contraseña actualizada. Ya puedes iniciar sesión.');return;
    case 'account':await api('/api/accounts'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'group':await api('/api/groups'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'person':data.group_ids=fd.getAll('group_ids');data.is_lead=fd.has('is_lead');response=await api('/api/people'+(id?'/'+id:''),id?'PUT':'POST',data);await refresh();if(response.activation_code){credentials(response.activation_code,data.username||data.employee_id);return;}break;
    case 'profile':await api('/api/profile','PUT',data);break;
    case 'password':await api('/api/password','PUT',data);state=null;render();toast('Contraseña actualizada. Vuelve a iniciar sesión.');return;
    case 'ot':await api('/api/overtime'+(id?'/'+id:''),id?'PUT':'POST',data);break;
    case 'guard':await api('/api/guards','POST',data);break;
    case 'rule':data.segments=fd.getAll('days').map(day=>({day:Number(day),start:data['start_'+day],end:data['end_'+day]}));await api('/api/rules','POST',data);break;
    case 'window':await api('/api/windows','POST',data);break;
    case 'delegation':data.group_ids=fd.getAll('group_ids');await api('/api/delegations','POST',data);break;
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
    busy=true;const button=$('[type="submit"], button:not([type])',f);if(button)button.disabled=true;const err=$('.form-error',f);if(err)err.textContent='';
    try{await submitForm(f);}catch(error){if(err&&err.isConnected)err.textContent=error.message;else toast(error.message,true);}finally{busy=false;if(button?.isConnected)button.disabled=false;}
  });
  document.addEventListener('change',async event=>{
    const target=event.target,f=target.closest('form');
    if(f?.dataset.form==='group'&&target.name==='account_id')f.elements.manager_id.innerHTML=managerOptions(target.value,'');
    if(f?.dataset.form==='person'&&target.name==='account_id')$('#group-checks').innerHTML=groupCheckboxes(target.value,f.dataset.id);
    if(f?.dataset.form==='person'&&target.name==='group_id')syncLeadOption();
    try{
      if(target.id==='month'){if(!target.value)return;month=target.value;await loadLedger();render();}
      if(target.name?.startsWith('filter-')){const key=target.name.slice(7);filters[key]=target.value;if(key==='group')filters.person='';await loadLedger();render();}
    }catch(error){toast(error.message,true);}
  });
  document.addEventListener('input',event=>{
    if(event.target.id==='team-search'){$$('[data-search-row]').forEach(row=>{row.hidden=!row.dataset.searchRow.includes(event.target.value.trim().toLowerCase());});}
  });
  $('#modal').addEventListener('click',event=>{if(event.target===$('#modal')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)event.target.close();}});
}
bind();
refresh().catch(error=>{if(!state)render();else toast(error.message,true);});
setInterval(tick,1000);
setInterval(()=>{if(state&&!busy&&!document.hidden&&!$('#modal').open&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))refresh(true);},5000);
