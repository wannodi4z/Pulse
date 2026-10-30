/* Alternative presentation compositions. The existing API, actions, forms and
   authorization remain owned by app.js. This module replaces the visual shell. */
(()=>{
'use strict';
const kind=document.documentElement.dataset.experience;
if(!['orbit','prisma'].includes(kind))return;
const originalRender=render,originalLogin=login;
let lastPage=null;
const fragment=html=>{const t=document.createElement('template');t.innerHTML=html;return t.content;};
function navigation(){const f=fragment(nav());return f.querySelector('nav').outerHTML;}
function brand(){return `<a href="/" class="experience-brand" aria-label="Operational Pulse"><img src="/static/favicon.svg" alt=""><span>pulse<span class="experience-name">${kind==='orbit'?'Orbit':'Prisma'}</span></span></a>`;}
function footer(){return `<footer class="main-footer"><span>Operational Pulse <b class="footer-version">v${esc(state.version)} · ${kind==='orbit'?'Orbit':'Prisma'}</b></span><button type="button" data-action="about">Acerca del proyecto ${icon('info')}</button></footer>`;}
function quickRoutes(){const f=fragment(nav());return [...f.querySelectorAll('[data-page]')].map(b=>b.dataset.page);}
function dock(){const all=quickRoutes(),preferred=isAdmin()?['dashboard','organization','admins']:isManager()?['dashboard','team','teamTime','analytics']:['dashboard','time','myAnalytics','claim','adp'];return `<nav class="prisma-dock" aria-label="Accesos rápidos">${preferred.filter(p=>all.includes(p)).map(p=>`<button type="button" data-page="${p}" class="${page===p?'selected':''}" ${page===p?'aria-current="page"':''}>${icon(p)}<span>${pageNames[p]}</span>${p==='teamTime'&&pendingCount()?`<b>${pendingCount()}</b>`:''}</button>`).join('')}<button type="button" data-experience-menu="open" aria-label="Abrir todas las opciones">${icon('organization')}<span>Más</span></button></nav>`;}
app=function(){
 const user=userMenu(),current=pageNames[page]||'Panel';
 if(kind==='orbit')return `<a class="skip-link" href="#main">Ir al contenido principal</a><div class="shell orbit-shell"><header class="orbit-header">${brand()}<div class="orbit-role"><span class="experience-live"></span>${esc(me().is_lead?'Lead':roles[me().role])}<span> / ${esc(current)}</span></div><div class="orbit-header-end"><span class="orbit-clock" data-local-clock></span>${user}</div></header><div class="orbit-navigation sidebar">${navigation()}<button class="orbit-info" type="button" data-action="about" aria-label="Acerca del proyecto">${icon('info')}</button></div><div class="workspace"><main id="main" tabindex="-1" data-experience-page="${page}">${content()}${footer()}</main></div></div>`;
 return `<a class="skip-link" href="#main">Ir al contenido principal</a><div class="shell prisma-shell"><header class="prisma-header"><div class="prisma-header-start"><button type="button" class="prisma-menu-toggle" data-experience-menu="open" aria-label="Abrir menú de navegación" aria-controls="experience-menu" aria-expanded="false"><span></span><span></span></button>${brand()}</div><div class="prisma-location"><span>ESPACIO DE TRABAJO</span><strong>${esc(current)}</strong></div><div class="prisma-header-end">${user}</div></header><div class="workspace"><main id="main" tabindex="-1" data-experience-page="${page}">${content()}${footer()}</main></div>${dock()}<dialog id="experience-menu" class="experience-launcher" aria-labelledby="experience-menu-title"><header><span class="eyebrow">TU ESPACIO PULSE</span><button type="button" data-experience-menu="close" aria-label="Cerrar menú">×</button><h2 id="experience-menu-title">¿Qué quieres hacer?</h2><p>Elige tu espacio de trabajo.</p></header><div class="sidebar">${navigation()}</div><footer><span>${esc(full(me()))} · ${esc(me().is_lead?'Lead':roles[me().role])}</span><button type="button" data-action="about" data-experience-dismiss>Acerca de Pulse ${icon('info')}</button></footer></dialog></div>`;
};
login=function(){
 const f=fragment(originalLogin()),card=f.querySelector('.login-card').outerHTML,foot=f.querySelector('.login-main>footer').outerHTML;
 if(kind==='orbit')return `<div class="login-shell orbit-access"><header>${brand()}${kyndrylBrand()}</header><main class="login-main"><div class="orbit-access-form">${card}${foot}</div><section class="orbit-access-story"><span class="eyebrow">TU OPERACIÓN, CONECTADA</span><h1>Cada hora,<br>en su lugar.</h1><p>Del trabajo diario a una captura clara.<br>Todo tu equipo, en la misma órbita.</p><div class="orbit-access-path"><span>${icon('time')}Planea</span><i>→</i><span>${icon('team')}Coordina</span><i>→</i><span>${icon('analytics')}Decide</span></div><div class="orbit-access-grid"><div><strong>01</strong><span>Calendario operativo</span></div><div><strong>02</strong><span>Tiempo con evidencia</span></div><div><strong>03</strong><span>Resultados consistentes</span></div></div></section></main><div class="experience-access-version">Operational Pulse · v1.0.10 · Orbit</div></div>`;
 return `<div class="login-shell prisma-access"><header>${brand()}${kyndrylBrand()}</header><main class="login-main"><section class="prisma-access-intro"><span class="eyebrow">CLARIDAD EN CADA MOMENTO</span><h1>Tu trabajo.<br>Una visión clara.</h1><p>Organiza tu tiempo, conecta con tu equipo<br>y convierte la actividad en resultados.</p></section>${card}${foot}<div class="prisma-access-chips"><span>${icon('time')}OT y Guardias</span><span>${icon('analytics')}Analítica</span><span>${icon('claim')}Claim y ADP</span></div></main><div class="experience-access-version">Operational Pulse · v1.0.10 · Prisma</div></div>`;
};
function decorate(){
 document.documentElement.classList.add('experience-'+kind);
 if(!state)return;
 const main=document.querySelector('#main');
 const dashboard=main?.querySelector('.workspace-view:has(>.kpis):has(>.two-columns)');if(dashboard)dashboard.classList.add('experience-dashboard');
 main?.querySelectorAll('.analytics-overview,.chart-card,.admin-account-tile').forEach(el=>el.classList.add('experience-surface'));
 if(kind==='orbit'){
  const active=document.querySelector('.orbit-navigation [aria-current=page]');if(active)active.scrollIntoView({block:'nearest',inline:'nearest'});
 }else{
  const menu=document.querySelector('#experience-menu');menu?.addEventListener('close',()=>document.querySelector('.prisma-menu-toggle')?.setAttribute('aria-expanded','false'));
 }
}
function openMenu(){const d=document.querySelector('#experience-menu');if(d&&!d.open){d.showModal();document.querySelector('.prisma-menu-toggle')?.setAttribute('aria-expanded','true');d.querySelector('[aria-current=page]')?.focus();}}
render=function(){const old=document.querySelector('#experience-menu'),wasOpen=!!old?.open,focused=document.activeElement?.dataset?.page;originalRender();decorate();if(state&&page!==lastPage){window.scrollTo({top:0,left:0,behavior:'auto'});lastPage=page;}if(!state)lastPage=null;if(wasOpen){openMenu();if(focused)document.querySelector(`#experience-menu [data-page="${focused}"]`)?.focus();}};
document.addEventListener('click',event=>{
 const toggle=event.target.closest('[data-experience-menu]');
 if(toggle){if(toggle.dataset.experienceMenu==='open')openMenu();else document.querySelector('#experience-menu')?.close();}
 if(event.target.closest('[data-page],[data-experience-dismiss]'))document.querySelector('#experience-menu')?.close();
},true);
document.addEventListener('keydown',event=>{if(kind==='prisma'&&state&&(event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();openMenu();}});
// Initial state may already have rendered before this deferred presentation module.
if(document.querySelector('.shell,.login-shell'))render();
})();
