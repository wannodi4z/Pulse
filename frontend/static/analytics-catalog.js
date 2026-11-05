'use strict';
// A catalog of analyses, not additional sources of data. Everything uses the scoped report.
const chartCatalog={
 trend:{title:'Tendencia mensual',type:'LÍNEAS · EVOLUCIÓN',category:'Periodo',scope:'all',description:'Compara OT y Stand By entre meses.'},
 monthlybars:{title:'Horas mensuales por tipo',type:'BARRAS APILADAS · MESES',category:'Periodo',scope:'all',description:'Identifica qué tipo de hora explica el volumen mensual.'},
 groups:{title:'OT y Stand By por Grupo',type:'BARRAS · GRUPOS',category:'Organización',scope:'team',description:'Compara los dos conceptos entre Grupos.'},
 mix:{title:'Composición de horas aprobadas',type:'ANILLO · COMPOSICIÓN',category:'Composición',scope:'all',description:'Distribución de Stand By y las tres modalidades de OT.'},
 waterfall:{title:'Qué explica el cambio en OT',type:'CASCADA · VARIACIÓN',category:'Periodo',scope:'all',description:'Descompone el cambio entre el primer y último mes.'},
 heatmap:{title:'Mapa de intensidad por hora',type:'MAPA DE CALOR · HORAS',category:'Periodo',scope:'all',description:'Localiza franjas con más horas acumuladas.'},
 area:{title:'Acumulado por tipo de hora',type:'ÁREA APILADA · ACUMULADO',category:'Periodo',scope:'all',description:'Sigue el crecimiento acumulado por fecha y concepto.'},
 pareto:{title:'OT aprobada por Técnico',type:'RANKING · OT',category:'Personas',scope:'team',description:'Ordena Técnicos por horas de OT aprobada.'},
 scatter:{title:'Balance de OT y Stand By por persona',type:'DISPERSIÓN · PERSONAS',category:'Personas',scope:'team',description:'Explora combinaciones de OT y Stand By por persona.'},
 daily:{title:'Horas aprobadas por día',type:'COLUMNAS APILADAS · FECHAS',category:'Periodo',scope:'all',extra:true,series:true,description:'Encuentra días con mayor volumen por tipo de hora.'},
 weekday:{title:'Distribución por día de la semana',type:'BARRAS · SEMANA',category:'Periodo',scope:'all',extra:true,series:true,description:'Contrasta el volumen acumulado de lunes a domingo.'},
 ottypes:{title:'Composición de la OT',type:'BARRAS · MODALIDAD',category:'Composición',scope:'all',extra:true,description:'Separa OT programada, histórica y emergente sin Stand By.'},
 groupmix:{title:'Tipos de hora por Grupo',type:'BARRAS APILADAS · GRUPOS',category:'Organización',scope:'team',extra:true,series:true,description:'Desglosa las cuatro modalidades dentro de cada Grupo.'},
 technicianmix:{title:'Tipos de hora por Técnico',type:'BARRAS APILADAS · PERSONAS',category:'Personas',scope:'team',extra:true,series:true,description:'Compara la composición de horas de cada Técnico.'},
 sbtech:{title:'Stand By neto por Técnico',type:'RANKING · STAND BY',category:'Personas',scope:'team',extra:true,description:'Revisa la distribución de cobertura neta entre personas.'},
 lowot:{title:'Técnicos con menos OT registrada',type:'RANKING ASCENDENTE · OT',category:'Personas',scope:'team',extra:true,description:'Incluye cero horas para revisar el contexto de registro.'},
 monthlydelta:{title:'Cambio mensual por tipo',type:'BARRAS DIVERGENTES · CAMBIO',category:'Periodo',scope:'all',extra:true,series:true,description:'Muestra aumentos y reducciones frente al mes seleccionado anterior.'},
 accounts:{title:'Horas de la Cuenta por tipo',type:'BARRAS APILADAS · CUENTA',category:'Organización',scope:'executive',extra:true,series:true,description:'Consolida sólo las horas de la Cuenta dentro de tu alcance.'},
 managers:{title:'Horas por Manager',type:'BARRAS APILADAS · MANAGERS',category:'Organización',scope:'executive',extra:true,series:true,description:'Compara equipos bajo los Managers autorizados.'},
 planningtrend:{title:'Evolución de modalidades de OT',type:'LÍNEAS · MODALIDADES',category:'Composición',scope:'all',extra:true,series:true,description:'Sigue por separado OT programada, histórica y emergente.'}
};
Object.entries(chartCatalog).forEach(([k,v])=>visualTitles[k]=v.title);
function buildCatalogDataset(kind,r){
 const types=accumulationTypes,total=m=>types.reduce((n,t)=>n+Number(m[t]||0),0),item=(label,m)=>({label,minutes:m});
 if(kind==='daily')return {items:r.days.map(d=>item(d.date,d.minutes)),stacked:true};
 if(kind==='weekday'){
  const days=Array.from({length:7},()=>Object.fromEntries(types.map(t=>[t,0])));
  r.days.forEach(d=>{const i=(new Date(d.date+'T12:00:00Z').getUTCDay()+6)%7;types.forEach(t=>days[i][t]+=d.minutes[t]||0);});
  return {items:days.map((m,i)=>item(['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'][i],m)),stacked:true};
 }
 if(kind==='ottypes')return {items:['PLANNED','HISTORICAL','EMERGENCY'].map(t=>item(accumulationLabels[t],{[t]:r.summary[t]})),stacked:true};
 if(kind==='groupmix')return {items:[...r.groups].sort((a,b)=>b.minutes.total_minutes-a.minutes.total_minutes).map(g=>item(g.name,g.minutes)),horizontal:true,stacked:true};
 if(kind==='technicianmix')return {items:[...r.users].sort((a,b)=>b.minutes.total_minutes-a.minutes.total_minutes).map(u=>item(u.name,u.minutes)),horizontal:true,stacked:true};
 if(kind==='sbtech'||kind==='lowot'){
  const key=kind==='sbtech'?'GUARD':'ot_minutes',sorted=[...r.users].sort((a,b)=>kind==='lowot'?a.minutes[key]-b.minutes[key]:b.minutes[key]-a.minutes[key]);
  return {items:sorted.map(u=>item(u.name,{[key]:u.minutes[key]})),horizontal:true,keys:[key]};
 }
 if(kind==='monthlydelta')return {items:r.comparison.slice(1).map((m,i)=>item(m.month,Object.fromEntries(types.map(t=>[t,m.minutes[t]-r.comparison[i].minutes[t]])))),divergent:true};
 if(kind==='managers')return {items:(r.managers||[]).map(m=>item(m.name,m.minutes)),horizontal:true,stacked:true};
 if(kind==='accounts'){
  const a=state.accounts.find(a=>a.id===me().account_id)||state.accounts[0];
  return {items:[item(a?.name||'Cuenta del alcance',r.summary)],horizontal:true,stacked:true};
 }
 return {items:r.comparison.map(m=>item(m.month,m.minutes)),lines:true,keys:['PLANNED','HISTORICAL','EMERGENCY']};
}
function catalogDataset(kind,r){const d=buildCatalogDataset(kind,r);if(r.visible_series&&chartCatalog[kind].series)d.keys=(d.keys||accumulationTypes).filter(k=>r.visible_series.includes(k));return d;}
function catalogVisualData(kind,r){
 const d=catalogDataset(kind,r),keys=d.keys||accumulationTypes,delta=kind==='monthlydelta';
 const notes={daily:'Cada columna suma las horas aprobadas de una fecha; se separan los cuatro tipos.',weekday:'Suma horas de todas las fechas que caen en cada día de la semana. No es un promedio ni una jornada individual.',ottypes:'Sólo OT aprobada. La OT histórica es captura posterior y debe revisarse como excepción.',groupmix:'Compara modalidades y volumen por Grupo del alcance actual.',technicianmix:'Compara las horas aprobadas de las personas del alcance. El volumen no mide desempeño.',sbtech:'Stand By neto: cobertura aprobada menos OT coincidente. Incluye personas con cero horas.',lowot:'Orden de menor a mayor OT registrada, incluidas personas con cero. Cero horas no implica inactividad; revisa periodo y contexto.',monthlydelta:'Cada barra compara con el mes seleccionado inmediatamente anterior. Positivo = aumento; negativo = reducción. Los meses omitidos no se interpretan como cero. Los periodos parciales afectan la comparación.',accounts:'Total de la Cuenta dentro de los filtros actuales. DPE sólo incluye sus Managers; no representa necesariamente toda la Cuenta.',managers:'Horas de los equipos de Managers visibles. No amplía tu alcance ni compara rendimiento.',planningtrend:'Cada línea muestra horas de una modalidad de OT por mes. No incluye Stand By. Los meses en curso son parciales.'};
 return {columns:[delta||d.lines?'Mes':'Concepto',...keys.map(t=>(accumulationLabels[t]||'Toda la OT')+' h'),delta?'Cambio total h':'Total h'],rows:d.items.map(i=>[i.label,...keys.map(t=>hours(i.minutes[t]||0)),hours(keys.reduce((n,t)=>n+(i.minutes[t]||0),0))]),summary:notes[kind]+(d.horizontal&&d.items.length>8?' La vista previa muestra 8 elementos; esta tabla incluye todos.':'')};
}
function catalogChart(kind,r){
 const d=catalogDataset(kind,r),keys=d.keys||accumulationTypes,color=t=>analyticsColors[t]||'#2469cf',sum=m=>keys.reduce((n,t)=>n+(m[t]||0),0),items=d.horizontal?d.items.slice(0,8):d.items;
 if(!items.length||d.lines&&items.length<2)return '<div class="decision-chart-empty">'+(d.lines||d.divergent?'Selecciona al menos dos meses.':'Sin datos para esta selección.')+'</div>';
 const axes=(max,y)=>[0,.5,1].map(v=>`<path d="M60 ${y(max*v)}H605" stroke="#e2eaf3"/><text x="52" y="${y(max*v)+4}" text-anchor="end" fill="#657d94" font-size="10">${hours(max*v)}</text>`).join('');
 let body='';
 if(d.lines){
  const max=Math.max(60,...items.flatMap(i=>keys.map(t=>i.minutes[t]||0))),y=v=>235-v/max*185,x=i=>60+i/Math.max(1,items.length-1)*540;
  body=axes(max,y)+keys.map(t=>`<polyline points="${items.map((i,n)=>x(n)+','+y(i.minutes[t]||0)).join(' ')}" fill="none" stroke="${color(t)}" stroke-width="2.5"/>`+items.map((i,n)=>`<circle cx="${x(n)}" cy="${y(i.minutes[t]||0)}" r="4" fill="${color(t)}"><title>${esc(i.label+' · '+accumulationLabels[t]+': '+hours(i.minutes[t]||0)+' h')}</title></circle>`).join('')).join('')+items.map((i,n)=>n%Math.ceil(items.length/6)===0||n===items.length-1?`<text x="${x(n)}" y="260" text-anchor="middle" font-size="10" fill="#657d94">${esc(i.label)}</text>`:'').join('');
 }else if(d.horizontal){
  const max=Math.max(60,...items.map(i=>sum(i.minutes))),row=220/items.length;
  body=items.map((i,n)=>{let x=210;const y=35+n*row;return `<text x="12" y="${y+14}" font-size="11" fill="#315777">${esc(i.label.length>26?i.label.slice(0,24)+'…':i.label)}</text>`+keys.map(t=>{const v=i.minutes[t]||0,w=v/max*320,part=`<rect x="${x}" y="${y}" width="${w}" height="${Math.min(21,row*.65)}" fill="${color(t)}"><title>${esc(i.label+' · '+(accumulationLabels[t]||'OT')+': '+hours(v)+' h')}</title></rect>`;x+=w;return part;}).join('')+`<text x="${Math.min(600,x+7)}" y="${y+14}" font-size="11" fill="#315777">${hours(sum(i.minutes))} h</text>`;}).join('');
 }else if(d.divergent){
  const max=Math.max(60,...items.flatMap(i=>[keys.reduce((n,t)=>n+Math.max(0,i.minutes[t]||0),0),keys.reduce((n,t)=>n+Math.max(0,-(i.minutes[t]||0)),0)])),step=530/items.length,y=v=>145-v/max*95;
  body=`<path d="M60 145H605" stroke="#9eb2c6"/><text x="50" y="150" text-anchor="end" fill="#657d94" font-size="10">0</text><text x="50" y="48" text-anchor="end" font-size="10" fill="#657d94">+${hours(max)}</text><text x="50" y="244" text-anchor="end" font-size="10" fill="#657d94">−${hours(max)}</text>`+items.map((i,n)=>{let positive=0,negative=0;return keys.map(t=>{const v=i.minutes[t]||0,from=v>=0?positive:negative;if(v>=0)positive+=v;else negative+=v;return `<rect x="${65+n*step}" y="${y(Math.max(from,from+v))}" width="${step*.65}" height="${Math.abs(v)/max*95}" fill="${color(t)}"><title>${esc(i.label+' · '+accumulationLabels[t]+': '+(v>0?'+':'')+hours(v)+' h')}</title></rect>`;}).join('')+`<text x="${65+n*step+step*.3}" y="270" text-anchor="middle" font-size="10" fill="#657d94">${esc(i.label)}</text>`;}).join('');
 }else{
  const max=Math.max(60,...items.map(i=>sum(i.minutes))),step=530/items.length,y=v=>235-v/max*185;
  body=axes(max,y)+items.map((i,n)=>{let total=0;return keys.map(t=>{const v=i.minutes[t]||0;total+=v;return `<rect x="${65+n*step}" y="${y(total)}" width="${Math.max(2,step*.68)}" height="${v/max*185}" fill="${color(t)}"><title>${esc(i.label+' · '+(accumulationLabels[t]||'OT')+': '+hours(v)+' h')}</title></rect>`;}).join('')+(n%Math.ceil(items.length/6)===0||n===items.length-1?`<text x="${65+n*step+step*.3}" y="260" text-anchor="middle" font-size="10" fill="#657d94">${esc(kind==='daily'?i.label.slice(5):i.label)}</text>`:'');}).join('');
 }
 return decisionSvg(visualTitles[kind],body)+`<div class="catalog-chart-key">${keys.map(t=>`<span><i class="analytics-dot type-${t==='ot_minutes'?'emergency':t.toLowerCase()}"></i>${esc(accumulationLabels[t]||'OT')}</span>`).join('')}</div>`;
}
function openChartCatalog(){
 const prefs=readChartLayout(),available=availableChartKinds();
 showModal('Elegir gráficas',form('chart-catalog',`<p class="callout">Empieza con las gráficas sugeridas y agrega sólo las que necesitas. Las opciones dependen de tu rol y alcance.</p><label class="field"><span>Buscar en el catálogo</span><input type="search" data-catalog-search placeholder="Ej. Técnico, Grupo, evolución…"></label><div class="chart-catalog">${['Periodo','Composición','Organización','Personas'].map(category=>{const kinds=available.filter(k=>chartCatalog[k].category===category);return kinds.length?`<section><h3>${category}</h3><div>${kinds.map(k=>`<label class="catalog-choice" data-catalog-label="${esc(chartCatalog[k].title.toLowerCase())}"><input type="checkbox" name="chart" value="${k}" ${prefs[k].visible?'checked':''}><span><strong>${esc(chartCatalog[k].title)}</strong><small>${esc(chartCatalog[k].description)}</small></span></label>`).join('')}</div></section>`:'';}).join('')}</div><p class="muted" data-catalog-count>${available.filter(k=>prefs[k].visible).length} seleccionadas · ${available.length} disponibles en tu alcance</p>`,'','Aplicar selección'),true);
 $('#modal').classList.add('chart-catalog-dialog');
}
document.addEventListener('input',event=>{
 if(!event.target.matches('[data-catalog-search]'))return;const q=event.target.value.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 document.querySelectorAll('.catalog-choice').forEach(e=>e.hidden=!e.dataset.catalogLabel.normalize('NFD').replace(/[\u0300-\u036f]/g,'').includes(q));
});
document.addEventListener('change',event=>{const f=event.target.closest('[data-form=chart-catalog]');if(f)f.querySelector('[data-catalog-count]').textContent=f.querySelectorAll('[name=chart]:checked').length+' seleccionadas · '+availableChartKinds().length+' disponibles en tu alcance';});

let analyticsFilterDraft=null;
function analyticsControls(recordsOnly,personal){
 const count=['group','person','kind','manager','dpe',...(recordsOnly?['status']:[])].filter(k=>filters[k]).length+(recordsOnly&&filters.period==='ALL'?1:0);
 const scope=filters.person?full(person(filters.person)):filters.group?group(filters.group)?.name:filters.manager?full(person(filters.manager)):filters.dpe?full(person(filters.dpe)):personal?'Mis horas':'Alcance autorizado';
 const period=recordsOnly?(filters.period==='ALL'?'Todo el historial':monthLabel(month)):selectedAnalyticsMonths().length===1?monthLabel(month):selectedAnalyticsMonths().length+' meses · '+monthLabel(selectedAnalyticsMonths()[0])+' — '+monthLabel(selectedAnalyticsMonths().at(-1));
 return `<section class="panel analytics-compact-controls ${recordsOnly?'history-controls':''}">${recordsOnly?`<form data-form="analytics-search"><label class="search">${icon('search')}<input id="analytics-search" name="search" type="search" maxlength="500" value="${esc(filters.search)}" placeholder="Buscar CHG / INC, Técnico, Employee ID o Grupo…" aria-label="Buscar en Consulta de registros" autocomplete="off"></label><button type="submit" class="primary">Buscar</button></form>`:`<div class="analytics-selection"><strong>${esc(scope||'Alcance seleccionado')}</strong><span>${esc(period)} · Horas aprobadas</span></div>`}<div class="compact-control-actions">${btn(icon('settings')+' Filtros'+(count?' · '+count:''),'analytics-filters','','secondary',`aria-haspopup="dialog"`)}${!recordsOnly?btn('Comparar meses','analytics-months','','secondary'):''}${isExecutive()?btn(icon('organization')+' Estructura','analytics-tree','','secondary'):''}</div>${recordsOnly?`<p id="analytics-query-status" role="status">${esc(period)}${count?' · '+count+' filtros activos':''}</p>`:''}</section>`;
}
function openAnalyticsFilters(draft){
 const recordsOnly=['records','myRecords'].includes(page),personal=['myAnalytics','myRecords'].includes(page),d=draft||{...filters};analyticsFilterDraft=d;
 const managers=state.people.filter(p=>p.role==='MANAGER'&&(!d.dpe||p.parent_id===d.dpe)),managerIds=new Set(managers.filter(m=>!d.manager||m.id===d.manager).map(m=>m.id)),groups=state.groups.filter(g=>state.scope.includes(g.id)&&(!isExecutive()||managerIds.has(g.manager_id))),people=state.people.filter(p=>p.role==='USER'&&(p.is_lead?isExecutive()?managerIds.has(p.manager_id):p.manager_id===(isManager()?me().id:me().manager_id):groups.some(g=>g.id===p.group_id))&&(!d.group||p.group_id===d.group));
 showModal(recordsOnly?'Filtros de búsqueda':'Filtros de analítica',form('analytics-view-filters',`<p class="callout">${recordsOnly?'Consulta un mes o todo el historial. Los cambios se aplican al pulsar Buscar registros.':'Selecciona el alcance de todas las gráficas. Los periodos se eligen desde Comparar meses.'}</p>${recordsOnly?select('period','Periodo',`<option value="MONTH" ${d.period!=='ALL'?'selected':''}>Mes seleccionado · ${esc(monthLabel(month))}</option><option value="ALL" ${d.period==='ALL'?'selected':''}>Todo el historial</option>`):''}${isExecutive()?(me().role==='DP'?select('dpe','DPE',options(state.people.filter(p=>p.role==='DPE'),d.dpe,full,'Todos los DPE')):'')+select('manager','Manager',options(managers,d.manager,full,'Todos mis Managers')):''}${!personal?select('group','Grupo',options(groups,d.group,g=>entityCode(g)+' · '+g.name,'Todos mis Grupos'))+select('person','Técnico',options(people,d.person,full,'Todos los Técnicos')):''}${select('kind','Tipo de horas',`<option value="">OT y Stand By</option><option value="OT" ${d.kind==='OT'?'selected':''}>Toda la OT</option>${analyticsTypes.map(t=>`<option value="${t}" ${d.kind===t?'selected':''}>${analyticsNames[t]}</option>`).join('')}`)}${recordsOnly?select('status','Estado',`<option value="">Todos los estados</option>${['SUBMITTED','APPROVED','REJECTED','DOCUMENTATION','RUNNING','PAUSED','CANCELLED'].map(s=>`<option value="${s}" ${d.status===s?'selected':''}>${statuses[s]}</option>`).join('')}`):''}<div class="filter-reset-action">${btn('Limpiar selección','analytics-filter-clear','','link')}</div>`,'',recordsOnly?'Buscar registros':'Aplicar filtros'),true);
 $('#modal').classList.add('analytics-filter-dialog');
}
document.addEventListener('change',event=>{
 const f=event.target.closest('[data-form=analytics-view-filters]');if(!f||!analyticsFilterDraft)return;
 const d={...analyticsFilterDraft,...Object.fromEntries(new FormData(f))},key=event.target.name;
 if(key==='dpe'){d.manager='';d.group='';d.person='';}if(key==='manager'){d.group='';d.person='';}if(key==='group')d.person='';
 analyticsFilterDraft=d;if(['dpe','manager','group'].includes(key))openAnalyticsFilters(d);
});
