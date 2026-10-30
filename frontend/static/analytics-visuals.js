'use strict';
// Presentation only: every value comes from the authorized, filtered analytics report.
let comparisonYear=0;
function analyticsNumber(value){return new Intl.NumberFormat('es-MX',{maximumFractionDigits:2}).format(value||0);}
function shiftAnalyticsMonth(key,offset){const [y,m]=key.split('-').map(Number),d=new Date(Date.UTC(y,m-1+offset,1));return d.toISOString().slice(0,7);}
function visualComparisonModal(){
 comparisonDraft=selectedAnalyticsMonths();comparisonYear=Number(month.slice(0,4));
 showModal('Comparar periodos',form('analytics-months',`<p class="callout">Elige un periodo rápido o marca los meses que quieras comparar. Todos usarán la misma búsqueda y filtros. Los periodos rápidos terminan en el mes principal, que siempre se incluye.</p><div class="period-presets">${[['2','Mes anterior + principal'],['3','Últimos 3 meses'],['6','Últimos 6 meses'],['12','Últimos 12 meses'],['year','Año hasta el mes principal'],['annual','Mismo mes · año anterior']].map(([id,label])=>btn(label,'comparison-preset',id,'secondary')).join('')}</div><div class="month-picker-heading">${btn('‹','comparison-year','-1','secondary')}<strong id="comparison-year-label"></strong>${btn('›','comparison-year','1','secondary')}</div><div id="comparison-month-grid" class="comparison-month-grid"></div><p class="muted">Haz clic para seleccionar o quitar · hasta 24 meses, incluso de distintos años.</p><div id="comparison-draft" class="comparison-draft"></div>`,'','Aplicar comparación'),true);
 $('#modal').classList.add('visual-period-dialog');paintComparisonDraft();paintMonthGrid();
}
function paintMonthGrid(){
 const root=$('#comparison-month-grid');if(!root)return;$('#comparison-year-label').textContent=comparisonYear;
 root.innerHTML=Array.from({length:12},(_,i)=>{const key=comparisonYear+'-'+String(i+1).padStart(2,'0'),selected=comparisonDraft.includes(key);return `<button type="button" data-action="comparison-toggle" data-id="${key}" aria-pressed="${selected}" ${key===month?'disabled':''}><strong>${esc(new Date(Date.UTC(comparisonYear,i,15)).toLocaleDateString('es-MX',{month:'short',timeZone:'UTC'}))}</strong><small>${key===month?'Principal':selected?'Seleccionado':'Seleccionar'}</small></button>`;}).join('');
}
function applyComparisonPreset(key){
 if(key==='annual')comparisonDraft=[shiftAnalyticsMonth(month,-12),month];
 else {const count=key==='year'?Number(month.slice(5,7)):Number(key);comparisonDraft=Array.from({length:count},(_,i)=>shiftAnalyticsMonth(month,i-count+1));}
 comparisonYear=Number(month.slice(0,4));paintComparisonDraft();paintMonthGrid();
}
const visualTitles={trend:'Tendencia mensual',monthlybars:'Horas mensuales por tipo',mix:'Composición de horas aprobadas',groups:'OT y Stand By por Grupo',waterfall:'Qué explica el cambio en OT'};
function decisionVisualData(kind,r){
 if(kind==='monthlybars')return {columns:['Mes','SB neto h','OT programada h','OT histórica h','OT emergente h','Total h'],rows:r.comparison.map(i=>[monthLabel(i.month),...accumulationTypes.map(t=>hours(i.minutes[t])),hours(i.minutes.total_minutes)]),summary:'Cada barra representa un mes. Sus colores separan Stand By neto, OT programada, histórica y emergente; la altura es el total aprobado. Permite identificar qué concepto crece o disminuye entre los meses seleccionados. Los periodos en curso son parciales.'};
 if(['heatmap','area','pareto','scatter'].includes(kind))return extraVisualData(kind,r);
 if(kind==='mix'){const total=r.summary.total_minutes;return {columns:['Concepto','Horas aprobadas','Participación'],rows:analyticsTypes.map(t=>[analyticsNames[t],hours(r.summary[t]),total?(r.summary[t]/total*100).toFixed(1)+'%':'Sin base']),summary:total?`El periodo acumula ${hours(total)} h aprobadas: ${hours(r.summary.ot_minutes)} h de OT y ${hours(r.summary.GUARD)} h de Stand By neto. La Guardia descuenta OT coincidente.`:'No hay horas aprobadas para calcular una composición.'};}
 if(kind==='groups'){const groups=[...r.groups].sort((a,b)=>b.minutes.ot_minutes-a.minutes.ot_minutes),top=groups[0];return {columns:['Grupo','OT h','Stand By h','Total h'],rows:groups.map(g=>[g.name,hours(g.minutes.ot_minutes),hours(g.minutes.GUARD),hours(g.minutes.total_minutes)]),summary:top&&r.summary.ot_minutes?`${top.name} concentra ${(top.minutes.ot_minutes/r.summary.ot_minutes*100).toFixed(1)}% de la OT aprobada. Compara por separado OT y Stand By; son conceptos distintos, no una medida de desempeño.`:'No hay OT aprobada para identificar concentración. La tabla conserva los Grupos del alcance.'};}
 const a=r.comparison[0],b=r.comparison.at(-1);
 if(kind==='waterfall'){const comparable=r.comparison.length>1;return {columns:['Componente','Horas de OT'],rows:comparable?[[`Base · ${monthLabel(a.month)}`,hours(a.minutes.ot_minutes)],...['PLANNED','HISTORICAL','EMERGENCY'].map(t=>[analyticsNames[t]+' · cambio',hours(b.minutes[t]-a.minutes[t])]),[`Cierre · ${monthLabel(b.month)}`,hours(b.minutes.ot_minutes)]]:[],summary:comparable?`La OT ${b.minutes.ot_minutes>=a.minutes.ot_minutes?'aumentó':'disminuyó'} ${hours(Math.abs(b.minutes.ot_minutes-a.minutes.ot_minutes))} h entre ${monthLabel(a.month)} y ${monthLabel(b.month)}. La cascada descompone esa diferencia por tipo de captura, no atribuye causas operativas. Stand By no forma parte de esta cascada.`:'Selecciona dos o más meses. La cascada compara el primer y el último mes seleccionados.'};}
 return {columns:['Mes','OT h','Stand By neto h','Total h'],rows:r.comparison.map(i=>[monthLabel(i.month),hours(i.minutes.ot_minutes),hours(i.minutes.GUARD),hours(i.minutes.total_minutes)]),summary:r.comparison.length>1?`Evolución de ${monthLabel(a.month)} a ${monthLabel(b.month)}. OT y Stand By usan la misma escala en horas. Los meses en curso son parciales; los espacios entre meses no seleccionados no representan cero horas.`:'Selecciona más meses para ver una tendencia; con un solo periodo no se infiere evolución.'};
}
function decisionSvg(title,body){return `<svg class="decision-svg" viewBox="0 0 640 300" role="img" aria-label="${esc(title)}">${body}</svg>`;}
function decisionChart(kind,r){
 if(kind==='monthlybars')return monthlyTypeBars(r);
 if(['heatmap','area','pareto','scatter'].includes(kind))return extraDecisionChart(kind,r);
 const axis=(max)=>[0,.5,1].map(v=>`<path d="M55 ${235-v*190}H610" stroke="#e2eaf3"/><text x="47" y="${239-v*190}" text-anchor="end" fill="#71859a" font-size="11">${hours(max*v)}</text>`).join('');
 if(kind==='mix'){
  const total=r.summary.total_minutes;if(!total)return `<div class="decision-chart-empty">Sin horas aprobadas para mostrar proporciones.</div>`;
  let angle=-Math.PI/2;const slices=analyticsTypes.filter(t=>r.summary[t]>0).map(t=>{const portion=r.summary[t]/total,end=angle+portion*Math.PI*2,x=210+96*Math.cos(angle),y=135+96*Math.sin(angle),ex=210+96*Math.cos(end),ey=135+96*Math.sin(end);const path=portion>.999999?`<circle cx="210" cy="135" r="96" fill="${analyticsColors[t]}"/>`:`<path d="M210 135L${x} ${y}A96 96 0 ${portion>.5?1:0} 1 ${ex} ${ey}Z" fill="${analyticsColors[t]}" stroke="white" stroke-width="2"/>`;angle=end;return `<g><title>${analyticsNames[t]}: ${hours(r.summary[t])} h (${(portion*100).toFixed(1)}%)</title>${path}</g>`;}).join('');
  return decisionSvg(visualTitles[kind],slices+`<circle cx="210" cy="135" r="56" fill="white" pointer-events="none"/><text x="210" y="140" pointer-events="none" text-anchor="middle" font-size="26" fill="#173f60" font-weight="700">${hours(total)} h</text><text x="350" y="110" font-size="32" fill="#173f60" font-weight="700">${hours(total)} h</text><text x="350" y="140" font-size="13" fill="#657d94">Total aprobado</text><text x="350" y="174" font-size="12" fill="#657d94">OT ${hours(r.summary.ot_minutes)} h</text><text x="350" y="195" font-size="12" fill="#657d94">SB ${hours(r.summary.GUARD)} h</text>`)+analyticsLegend();
 }
 if(kind==='groups'){
  const groups=[...r.groups].sort((a,b)=>b.minutes.ot_minutes-a.minutes.ot_minutes).slice(0,6),max=Math.max(60,...groups.flatMap(g=>[g.minutes.ot_minutes,g.minutes.GUARD]));
  if(!groups.length)return '<div class="decision-chart-empty">Sin Grupos en el alcance actual.</div>';
  return `<div class="decision-group-bars">${groups.map(g=>`<div><strong>${esc(g.name)}</strong><div><span>OT</span><meter min="0" max="${max}" value="${g.minutes.ot_minutes}" aria-label="${esc(g.name)} OT"></meter><b>${hours(g.minutes.ot_minutes)} h</b></div><div class="sb"><span>SB</span><meter min="0" max="${max}" value="${g.minutes.GUARD}" aria-label="${esc(g.name)} Stand By"></meter><b>${hours(g.minutes.GUARD)} h</b></div></div>`).join('')}</div><p class="decision-footnote">${r.groups.length>6?'Se muestran los 6 Grupos con más OT. El detalle incluye todos.':'Escala común · OT en azul · Stand By en verde.'}</p>`;
 }
 if(r.comparison.length<2)return `<div class="decision-chart-empty">Selecciona al menos dos meses para ${kind==='trend'?'ver la tendencia':'explicar la variación'}.</div>`;
 if(kind==='trend'){
  const items=r.comparison,max=Math.max(60,...items.flatMap(i=>[i.minutes.ot_minutes,i.minutes.GUARD])),index=k=>Number(k.slice(0,4))*12+Number(k.slice(5,7)),first=index(items[0].month),span=Math.max(1,index(items.at(-1).month)-first),x=i=>55+(index(i.month)-first)/span*555,y=v=>235-v/max*190;
  return decisionSvg(visualTitles[kind],axis(max)+[['ot_minutes','#2469cf','OT'],['GUARD','#25b4a4','Stand By']].filter(([key])=>!r.visible_series||(key==='GUARD'?r.visible_series.includes('GUARD'):r.visible_series.some(t=>t!=='GUARD'))).map(([key,color,label])=>`<polyline points="${items.map(i=>x(i)+','+y(i.minutes[key])).join(' ')}" fill="none" stroke="${color}" stroke-width="3"/>${items.map(i=>`<circle cx="${x(i)}" cy="${y(i.minutes[key])}" r="5" fill="${color}" stroke="white" stroke-width="2"><title>${monthLabel(i.month)} · ${r.visible_series?label+': '+hours(i.minutes[key])+' h':'OT: '+hours(i.minutes.ot_minutes)+' h · Stand By: '+hours(i.minutes.GUARD)+' h'}</title></circle>`).join('')}`).join('')+items.filter((_,i)=>i%Math.ceil(items.length/6)===0||i===items.length-1).map(i=>`<text x="${x(i)}" y="260" text-anchor="middle" fill="#657d94" font-size="11">${esc(i.month)}</text>`).join('')+`<text x="55" y="20" fill="#657d94" font-size="11">Horas aprobadas</text>`)+`<div class="decision-key"><span><i class="decision-key-ot"></i>OT</span><span><i class="decision-key-sb"></i>Stand By neto</span></div>`;
 }
 const first=r.comparison[0],last=r.comparison.at(-1),parts=[{label:first.month,from:0,to:first.minutes.ot_minutes,total:true}];let running=first.minutes.ot_minutes;
 for(const t of ['PLANNED','HISTORICAL','EMERGENCY']){const diff=last.minutes[t]-first.minutes[t];parts.push({label:{PLANNED:'Programada',HISTORICAL:'Histórica',EMERGENCY:'Emergente'}[t],from:running,to:running+diff,diff});running+=diff;}
 parts.push({label:last.month,from:0,to:last.minutes.ot_minutes,total:true});const max=Math.max(60,...parts.flatMap(p=>[p.from,p.to])),y=v=>235-v/max*190;
 return decisionSvg(visualTitles[kind],axis(max)+parts.map((p,i)=>{const x=70+i*110,color=p.total?'#2469cf':p.diff>=0?'#dc923d':'#25a698',value=p.total?p.to:p.diff;return `<rect x="${x}" y="${y(Math.max(p.from,p.to))}" width="68" height="${Math.max(2,Math.abs(p.to-p.from)/max*190)}" fill="${color}" rx="3"><title>${esc(p.label)}: ${hours(value)} h</title></rect><text x="${x+34}" y="${y(Math.max(p.from,p.to))-8}" text-anchor="middle" fill="#315474" font-size="12">${!p.total&&value>0?'+':''}${hours(value)} h</text><text x="${x+34}" y="260" text-anchor="middle" fill="#657d94" font-size="11">${esc(p.label)}</text>${i<4?`<path d="M${x+68} ${y(p.to)}H${x+110}" stroke="#a9bbcc" stroke-dasharray="4 3"/>`:''}`;}).join(''))+`<p class="decision-footnote">Azul: OT inicial/final · Naranja: aumento · Verde: reducción. No indica si el cambio es bueno o malo.</p>`;
}
function decisionVisualButton(kind,report){
 const labels={trend:'LÍNEAS · EVOLUCIÓN',monthlybars:'BARRAS APILADAS · TIPOS DE HORA',groups:'BARRAS · DISTRIBUCIÓN',mix:'ANILLO · COMPOSICIÓN',waterfall:'CASCADA · VARIACIÓN',heatmap:'MAPA DE CALOR · FRANJAS',area:'ÁREA APILADA · ACUMULACIÓN',pareto:'RANKING · HORAS Y PARTICIPACIÓN',scatter:'DISPERSIÓN · DISTRIBUCIÓN'};
 return `<button class="decision-card-open" type="button" data-action="decision-detail" data-id="${kind}" aria-label="Abrir detalle: ${visualTitles[kind]}"><span class="decision-card-type">${labels[kind]}</span><h3>${visualTitles[kind]}</h3>${decisionChart(kind,report)}<span class="decision-card-cta">Ver resumen y tabla ${icon('forward')}</span></button>`;
}
function decisionVisualDeck(report){
 if(report.mode==='TEAM')return configurableAnalyticsDeck(report);
 const kinds=report.mode==='PERSONAL'?['trend','mix','waterfall','area','heatmap']:['trend','groups','mix','waterfall','heatmap','area','pareto','scatter'];
 return `<section class="decision-section"><header class="section-heading"><div><h2>Tu operación, en gráficas</h2></div></header><div class="decision-grid">${kinds.map(kind=>`<article class="panel decision-card ${kind==='trend'?'decision-dual':''}">${kind==='trend'?`<div class="decision-dual-pane">${decisionVisualButton('trend',report)}</div><div class="decision-dual-pane">${decisionVisualButton('monthlybars',report)}</div>`:decisionVisualButton(kind,report)}</article>`).join('')}</div></section>`;
}
function monthlyTypeBars(report){
 const items=report.comparison,max=Math.max(60,...items.map(i=>i.minutes.total_minutes)),step=530/Math.max(1,items.length);
 const axes=[0,.5,1].map(v=>`<path d="M60 ${235-v*180}H600" stroke="#e0e9f2"/><text x="52" y="${239-v*180}" text-anchor="end" font-size="10" fill="#687f95">${hours(max*v)}</text>`).join('');
 const bars=items.map((i,index)=>{let y=235;const tip=monthLabel(i.month)+' · '+(report.visible_series||accumulationTypes).map(t=>accumulationLabels[t]+': '+hours(i.minutes[t])+' h').join(' · ')+' · Total '+hours(i.minutes.total_minutes)+' h';return `<g><title>${esc(tip)}</title><rect x="${65+index*step}" y="55" width="${Math.max(3,step*.7)}" height="180" fill="transparent"/>${accumulationTypes.map(t=>{const height=i.minutes[t]/max*180;y-=height;return `<rect x="${65+index*step}" y="${y}" width="${Math.max(3,step*.7)}" height="${height}" fill="${analyticsColors[t]}"/>`;}).join('')}</g>${index%Math.ceil(items.length/6)===0||index===items.length-1?`<text x="${65+index*step+step*.35}" y="260" text-anchor="middle" font-size="10" fill="#687f95">${esc(i.month)}</text>`:''}`;}).join('');
 return decisionSvg(visualTitles.monthlybars,axes+bars+'<text x="60" y="25" font-size="12" fill="#476a89">Horas aprobadas por mes</text>')+analyticsLegend();
}
function chartSeriesOptions(kind){
 if(kind==='trend')return [{id:'OT',label:'Toda la OT',color:'ot'},{id:'GUARD',label:'Stand By neto',color:'guard'}];
 return ['area','monthlybars','mix'].includes(kind)?accumulationTypes.map(id=>({id,label:accumulationLabels[id],color:id.toLowerCase()})):[];
}
function projectChartSeries(report,series){
 if(series==='ALL')return report;
 const projected=structuredClone(report),keep=series==='OT'?analyticsTypes.filter(t=>t!=='GUARD'):[series];
 const project=minutes=>{for(const type of analyticsTypes)if(!keep.includes(type))minutes[type]=0;minutes.ot_minutes=analyticsTypes.filter(t=>t!=='GUARD').reduce((sum,t)=>sum+Number(minutes[t]||0),0);minutes.total_minutes=minutes.ot_minutes+Number(minutes.GUARD||0);};
 project(projected.summary);for(const collection of ['days','comparison','hourly','groups','users'])for(const item of projected[collection]||[])project(item.minutes);
 projected.visible_series=keep;return projected;
}
function decisionDetailModal(kind,series='ALL',focusSeries=''){
 const original=analyticsReport,options=chartSeriesOptions(kind);if(!original||!visualTitles[kind])return;
 if(series!=='ALL'&&!options.some(o=>o.id===series))return;
 const r=projectChartSeries(original,series),d=decisionVisualData(kind,r),active=options.find(o=>o.id===series),oldScroll=$('#modal .form-body')?.scrollTop||0;
 let summary=d.summary;
 if(active){
  if(kind==='area'){const index=1+accumulationTypes.indexOf(series);d.columns=['Fecha',active.label+' · acumulado h'];d.rows=d.rows.map(row=>[row[0],row[index]]);summary=`Sólo ${active.label}: ${hours(r.summary.total_minutes)} h acumuladas aprobadas. La escala y los datos emergentes corresponden a este tipo; la tabla muestra su acumulado por fecha.`;}
  if(kind==='monthlybars'){const index=1+accumulationTypes.indexOf(series);d.columns=['Mes',active.label+' h'];d.rows=d.rows.map(row=>[row[0],row[index]]);summary=`Sólo ${active.label}: ${hours(r.summary.total_minutes)} h aprobadas en los meses seleccionados. Cada barra muestra las horas de ese mes.`;}
  if(kind==='mix'){d.rows=d.rows.filter((_,index)=>analyticsTypes[index]===series);summary=`Sólo ${active.label}: ${hours(r.summary.total_minutes)} h aprobadas. La proporción es 100% de la selección visible; Ver todos recupera la composición completa.`;}
  if(kind==='trend'){const index=series==='OT'?1:2;d.columns=['Mes',active.label+' h'];d.rows=d.rows.map(row=>[row[0],row[index]]);summary=`Evolución de ${active.label}: ${hours(r.summary.total_minutes)} h aprobadas en los meses seleccionados. Cada punto corresponde a un mes; los periodos en curso son parciales.`;}
 }
 const chart=document.createElement('div');chart.innerHTML=decisionChart(kind,r);
 if(options.length)chart.querySelectorAll('.area-type-totals,.analytics-legend,.decision-key').forEach(node=>node.remove());
 const legend=options.length?`<section class="interactive-chart-legend" aria-label="Filtrar series de esta gráfica"><p>Selecciona un tipo para verlo solo. Vuelve a pulsarlo o elige Ver todos para restablecer.</p><div>${btn('Ver todos','chart-series',kind+':ALL','secondary small',`aria-pressed="${series==='ALL'}"`)}${options.map(o=>`<button type="button" class="series-option ${active&&o.id!==series?'series-muted':''}" data-action="chart-series" data-id="${kind}:${o.id}" aria-pressed="${series===o.id}"><i class="analytics-dot type-${o.color}"></i><span>${o.label}</span><b>${hours(o.id==='OT'?original.summary.ot_minutes:original.summary[o.id])} h</b></button>`).join('')}</div><span class="chart-series-status" role="status">${active?'Mostrando sólo '+active.label:'Mostrando todos los tipos'} · selección local de esta gráfica</span></section>`:'';
 showModal(visualTitles[kind],`<div class="form-body decision-detail"><p class="callout"><strong>Lectura del periodo</strong><br>${esc(summary)}</p>${chart.innerHTML}${legend}<p class="muted">${esc(r.months.map(monthLabel).join(' · '))} · Se conservan los filtros del dashboard. Sólo horas aprobadas; los meses en curso son parciales.</p><div class="table-scroll"><table><thead><tr>${d.columns.map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${d.rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${d.rows.length?'':empty('Sin datos para esta selección','Prueba otro tipo o periodo.')}</div><footer class="dialog-footer">${btn('Consultar registros','open-records','','secondary')}${btn('Cerrar','close','','secondary')}</footer>`,true);
 $('#modal').classList.add('expanded-chart-dialog');$('#modal').dataset.chartSeries=series;$('#modal').dataset.chartKind=kind;
 if(focusSeries){const body=$('#modal .form-body');if(body)body.scrollTop=oldScroll;$('#modal [data-action="chart-series"][data-id="'+kind+':'+focusSeries+'"]')?.focus({preventScroll:true});}
}

const accumulationTypes=['GUARD','PLANNED','HISTORICAL','EMERGENCY'];
const accumulationLabels={GUARD:'Stand By neto',PLANNED:'OT programada',HISTORICAL:'OT histórica',EMERGENCY:'OT emergente'};
function accumulationSeries(report){
 const accumulated=Object.fromEntries(accumulationTypes.map(t=>[t,0]));
 return [...report.days].filter(d=>d.minutes.total_minutes>0).sort((a,b)=>a.date.localeCompare(b.date)).map(d=>{
  const daily=Object.fromEntries(accumulationTypes.map(t=>[t,Number(d.minutes[t]||0)]));
  accumulationTypes.forEach(t=>accumulated[t]+=daily[t]);
  return {date:d.date,daily,accumulated:{...accumulated},total:accumulationTypes.reduce((n,t)=>n+accumulated[t],0)};
 });
}

Object.assign(visualTitles,{heatmap:'Mapa de intensidad por hora',area:'Acumulado por tipo de hora',pareto:'OT aprobada por Técnico',scatter:'Balance de OT y Stand By por persona'});
function extraVisualData(kind,r){
 if(kind==='heatmap'){const peak=[...r.hourly].sort((a,b)=>b.minutes.total_minutes-a.minutes.total_minutes)[0];return {columns:['Hora del día','OT h','Stand By h','Total h'],rows:r.hourly.map(i=>[String(i.hour).padStart(2,'0')+':00',hours(i.minutes.ot_minutes),hours(i.minutes.GUARD),hours(i.minutes.total_minutes)]),summary:peak?.minutes.total_minutes?`La franja con más horas acumuladas es ${String(peak.hour).padStart(2,'0')}:00: ${hours(peak.minutes.total_minutes)} h. Suma personas y fechas del alcance; no es una jornada individual ni indica cuántas personas estuvieron simultáneamente.`:'No hay horas aprobadas para identificar una franja de mayor intensidad.'};}
 if(kind==='area'){
  const rows=accumulationSeries(r),last=rows.at(-1);
  return {columns:['Fecha','SB acumulado h','Programada acumulada h','Histórica acumulada h','Emergente acumulada h','Total acumulado h'],rows:rows.map(d=>[fmtDate(d.date),...accumulationTypes.map(t=>hours(d.accumulated[t])),hours(d.total)]),summary:last?`Se acumulan ${hours(last.total)} h aprobadas: Stand By ${hours(last.accumulated.GUARD)} h, OT programada ${hours(last.accumulated.PLANNED)} h, histórica ${hours(last.accumulated.HISTORICAL)} h y emergente ${hours(last.accumulated.EMERGENCY)} h. Cada franja de color aporta al total apilado. Al señalar una fecha puedes ver el acumulado y las horas del día por tipo. Acumulación no equivale a variación entre meses; los periodos omitidos no añaden horas.`:'No hay horas aprobadas para mostrar acumulación por tipo.'};
 }
 if(kind==='scatter')return {columns:['Técnico','Employee ID','Grupo','Stand By h · eje X','OT h · eje Y'],rows:r.users.map(u=>[u.name,u.employee_id,u.group_name,hours(u.minutes.GUARD),hours(u.minutes.ot_minutes)]),summary:'Cada punto representa una persona. El eje horizontal muestra Stand By neto y el vertical OT aprobada. Permite detectar combinaciones de horas diferentes para investigar su contexto; no mide carga contratada, productividad ni desempeño. Puntos coincidentes pueden superponerse.'};
 const sorted=[...r.users].sort((a,b)=>b.minutes.ot_minutes-a.minutes.ot_minutes||a.name.localeCompare(b.name,'es')),total=r.summary.ot_minutes,top=sorted[0];
 return {columns:['Técnico','OT aprobada h','Participación en la OT del alcance'],rows:sorted.map(u=>[u.name,hours(u.minutes.ot_minutes),total?(u.minutes.ot_minutes/total*100).toFixed(1)+'%':'Sin base']),summary:total&&top?`${top.name} registra ${hours(top.minutes.ot_minutes)} h, ${(top.minutes.ot_minutes/total*100).toFixed(1)}% de las ${hours(total)} h de OT aprobada del alcance. Cada barra muestra una persona: longitud = horas y porcentaje = su parte del total. Orden de mayor a menor; no es una evaluación de desempeño. La tabla incluye personas con cero horas.`:'No hay OT aprobada en el alcance. Se conservan las personas con cero horas, sin inventar porcentajes.'};
}
function extraDecisionChart(kind,r){
 if(kind==='heatmap'){
  const max=Math.max(1,...r.hourly.map(i=>i.minutes.total_minutes));return `<div class="decision-heatmap" role="img" aria-label="Intensidad de horas aprobadas por hora del día">${r.hourly.map(i=>{const value=i.minutes.total_minutes;return `<span data-heat-value="${value}" data-heat-max="${max}"><strong>${String(i.hour).padStart(2,'0')}:00</strong><small>${hours(value)} h</small></span>`;}).join('')}</div><p class="decision-footnote">Más oscuro = más horas acumuladas. Suma personas y fechas.</p>`;
 }
 if(kind==='scatter'){
  if(!r.users.length)return '<div class="decision-chart-empty">Sin personas en este alcance.</div>';
  const mx=Math.max(60,...r.users.map(u=>u.minutes.GUARD)),my=Math.max(60,...r.users.map(u=>u.minutes.ot_minutes));
  return decisionSvg(visualTitles[kind],[0,.5,1].map(v=>`<path d="M65 ${235-v*180}H600" stroke="#e2eaf3"/><text x="55" y="${239-v*180}" text-anchor="end" font-size="11" fill="#687f95">${hours(my*v)}</text><text x="${65+v*535}" y="255" text-anchor="middle" font-size="11" fill="#687f95">${hours(mx*v)}</text>`).join('')+r.users.map(u=>`<circle cx="${65+u.minutes.GUARD/mx*535}" cy="${235-u.minutes.ot_minutes/my*180}" r="7" fill="#278ac3" fill-opacity=".55" stroke="#fff" stroke-width="1.5"><title>${esc(u.name)} · ${esc(u.employee_id)}: OT ${hours(u.minutes.ot_minutes)} h · SB ${hours(u.minutes.GUARD)} h</title></circle>`).join('')+'<text x="65" y="30" font-size="12" fill="#476a89">OT aprobada · h</text><text x="320" y="285" text-anchor="middle" font-size="12" fill="#476a89">Stand By neto · h</text>');
 }
 if(kind==='area'){
  const days=accumulationSeries(r);if(!days.length)return '<div class="decision-chart-empty">Sin horas aprobadas para acumular.</div>';
  const stamp=d=>Date.parse(d+'T12:00:00Z'),from=stamp(days[0].date),span=Math.max(86400000,stamp(days.at(-1).date)-from),max=Math.max(60,days.at(-1).total),x=d=>days.length===1?595:65+(stamp(d.date)-from)/span*530,y=v=>235-v/max*180;
  const boundary=(d,limit)=>accumulationTypes.slice(0,limit).reduce((n,t)=>n+d.accumulated[t],0);
  const bands=accumulationTypes.map((type,index)=>{
   if(!days.at(-1).accumulated[type])return '';
   const upper=days.length===1?'65,'+y(boundary(days[0],index+1))+' 595,'+y(boundary(days[0],index+1)):days.map(d=>x(d)+','+y(boundary(d,index+1))).join(' '),lower=days.length===1?'595,'+y(boundary(days[0],index))+' 65,'+y(boundary(days[0],index)):[...days].reverse().map(d=>x(d)+','+y(boundary(d,index))).join(' ');
   return `<polygon data-area-series="${type}" points="${upper} ${lower}" fill="${analyticsColors[type]}" fill-opacity=".52"/><polyline points="${upper}" fill="none" stroke="${analyticsColors[type]}" stroke-width="1.8"/>`;
  }).join('');
  const visible=r.visible_series||accumulationTypes;
  const points=days.map(d=>`<circle cx="${x(d)}" cy="${y(d.total)}" r="3.5" fill="#315777" stroke="white" stroke-width="1"><title>${esc(d.date)} · Acumulado: ${visible.map(t=>accumulationLabels[t]+' '+hours(d.accumulated[t])+' h').join(' · ')} · Total ${hours(d.total)} h. Horas del día: ${visible.map(t=>accumulationLabels[t]+' '+hours(d.daily[t])+' h').join(' · ')}</title></circle>`).join('');
  return decisionSvg(visualTitles[kind],[0,.5,1].map(v=>`<path d="M65 ${y(max*v)}H600" stroke="#e0e9f2"/><text x="55" y="${y(max*v)+4}" text-anchor="end" fill="#687f95" font-size="10">${hours(max*v)}</text>`).join('')+bands+points+`<text x="65" y="25" font-size="12" fill="#476a89">Total acumulado · ${hours(days.at(-1).total)} h</text><text x="65" y="263" font-size="11" fill="#687f95">${esc(days[0].date)}</text><text x="595" y="263" text-anchor="end" font-size="11" fill="#687f95">${esc(days.at(-1).date)}</text>`)+`<div class="area-type-totals">${accumulationTypes.map(t=>`<span><i class="analytics-dot type-${t.toLowerCase()}"></i>${accumulationLabels[t]} <b>${hours(days.at(-1).accumulated[t])} h</b></span>`).join('')}</div>`;
 }
 const sorted=[...r.users].sort((a,b)=>b.minutes.ot_minutes-a.minutes.ot_minutes||a.name.localeCompare(b.name,'es')),total=r.summary.ot_minutes,max=Math.max(1,...sorted.map(u=>u.minutes.ot_minutes));
 if(!sorted.length)return '<div class="decision-chart-empty">Sin personas en el alcance actual.</div>';
 return `<div class="decision-people-ranking">${sorted.slice(0,8).map(u=>{const share=total?(u.minutes.ot_minutes/total*100).toFixed(1)+'%':'Sin base';return `<div><header><strong>${esc(u.name)}</strong><b>${hours(u.minutes.ot_minutes)} h</b></header><div><meter min="0" max="${max}" value="${u.minutes.ot_minutes}" aria-label="${esc(u.name)}: ${hours(u.minutes.ot_minutes)} h de OT aprobada · ${share} del total"></meter><span>${share}</span></div></div>`;}).join('')}</div><p class="decision-footnote">Porcentaje sobre ${hours(total)} h de OT aprobada. ${sorted.length>8?'Se muestran las 8 personas con más OT; el detalle incluye todas.':'Ordenado de mayor a menor; incluye cero horas.'} No mide desempeño.</p>`;
}

function captureDisciplinePanel(report){
 const t=report.timeliness;if(!t)return '';
 return `<section class="panel capture-discipline bi-capture"><div class="bi-capture-heading"><div><strong>Captura oportuna</strong><span>Periodos seleccionados · evitar backlog</span></div><div><b>${t.historical_records} / ${t.manual_ot_records}</b><span>OT históricas no recuperadas</span></div><div><b>${t.average_delay_hours===null?'—':analyticsNumber(t.average_delay_hours)+' h'}</b><span>Demora media de captura histórica</span></div></div><details><summary>Regla de registro y criterio del indicador</summary><p>Programa la OT antes de ejecutarla y utiliza el Timer. Ante una emergencia, inicia el Timer al atenderla. La captura histórica es una excepción: explica por qué registras después y por qué no se utilizó el Timer para revisión del Manager.</p><p>Desde el fin de la actividad hasta crear el registro. Incluye los estados consultados excepto cancelados. ${t.recovered_ot_records} OT recuperadas de respaldo excluidas. ${t.historical_share===null?'Sin base de proporción.':t.historical_share+'% de registros no recuperados son históricos.'} Este indicador no determina un incumplimiento ni modifica horas o aprobaciones.</p></details></section>`;
}

// Tooltips are in the top layer, including when charts are inside a modal.
(function installDecisionTooltips(){
 let current=null,tooltip=null,scheduled=false;
 function tipElement(){if(tooltip)return tooltip;tooltip=document.createElement('div');tooltip.id='pulse-chart-tooltip';tooltip.className='pulse-chart-tooltip';tooltip.setAttribute('role','tooltip');tooltip.setAttribute('popover','manual');document.body.append(tooltip);return tooltip;}
 function hide(){if(tooltip){if(tooltip.matches(':popover-open'))tooltip.hidePopover();tooltip.hidden=true;}if(current)current.removeAttribute('aria-describedby');current=null;}
 function show(target,x,y){const text=target?.dataset.chartTip;if(!text)return hide();const tip=tipElement();if(current&&current!==target)current.removeAttribute('aria-describedby');current=target;if(tip.textContent!==text)tip.textContent=text;tip.hidden=false;target.setAttribute('aria-describedby',tip.id);if(!tip.matches(':popover-open'))tip.showPopover();const box=target.getBoundingClientRect(),left=Number.isFinite(x)?x:box.left+box.width/2,top=Number.isFinite(y)?y:box.top;const width=tip.offsetWidth,height=tip.offsetHeight;tip.style.left=Math.max(8,Math.min(innerWidth-width-8,left+14))+'px';tip.style.top=Math.max(8,Math.min(innerHeight-height-8,top-height-12))+'px';}
 function annotate(){scheduled=false;if(current&&!current.isConnected)hide();document.querySelectorAll('.decision-card svg title,.decision-detail svg title').forEach(title=>{const node=title.parentElement;node.dataset.chartTip=title.textContent;node.setAttribute('tabindex','0');node.setAttribute('aria-label',title.textContent);title.remove();});document.querySelectorAll('.decision-group-bars meter,.decision-people-ranking meter,.decision-heatmap>span').forEach(node=>{if(node.matches('meter')){const row=node.parentElement;if(!node.dataset.chartBaseLabel)node.dataset.chartBaseLabel=node.getAttribute('aria-label')||'';const amount=row.querySelector('b')?.textContent;node.dataset.chartTip=node.dataset.chartBaseLabel+(amount?': '+amount:'');}else {const intensity=Number(node.dataset.heatValue)/Math.max(1,Number(node.dataset.heatMax));node.style.backgroundColor='rgba(30,105,183,'+(.08+intensity*.85)+')';node.style.color=intensity>.45?'#fff':'#315779';node.dataset.chartTip=node.querySelector('strong').textContent+' · '+node.querySelector('small').textContent;}node.setAttribute('tabindex','0');node.setAttribute('aria-label',node.dataset.chartTip);});}
 function prepare(){if(!scheduled){scheduled=true;requestAnimationFrame(annotate);}}
 document.addEventListener('pointermove',event=>{const target=event.target.closest?.('[data-chart-tip]');if(target)show(target,event.clientX,event.clientY);else if(current)hide();},{passive:true});
 document.addEventListener('focusin',event=>{const target=event.target.closest?.('[data-chart-tip]');if(target)show(target);else hide();});
 document.addEventListener('focusout',hide);document.addEventListener('pointerdown',event=>{if(event.pointerType==='touch'){const target=event.target.closest?.('[data-chart-tip]');if(target)show(target,event.clientX,event.clientY);else hide();}},{passive:true});
 document.addEventListener('keydown',event=>{if(event.key==='Escape')hide();});document.addEventListener('wheel',hide,{passive:true});document.addEventListener('touchmove',hide,{passive:true});window.addEventListener('blur',hide);window.addEventListener('resize',hide);document.addEventListener('pointerout',event=>{if(!event.relatedTarget)hide();});
 new MutationObserver(prepare).observe(document.documentElement,{childList:true,subtree:true});prepare();
})();
