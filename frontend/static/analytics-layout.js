'use strict';
// Per-user presentation preferences only. Never alter authorized reports or chart-series filters.
const chartLayoutKinds=['trend','monthlybars','groups','mix','waterfall','heatmap','area','pareto','scatter'];
const chartLayoutWidths=[4,6,8,12],chartLayoutHeights=[300,380,480,600];
const chartWidthNames={4:'Compacta · ⅓',6:'Media · ½',8:'Amplia · ⅔',12:'Completa'};
const chartHeightNames={300:'Compacta',380:'Normal',480:'Alta',600:'Muy alta'};
const chartLayoutCache=new Map(),chartLayoutEditing=new Set();
let chartResize=null;
function chartResizeActive(){return Boolean(chartResize);}
function chartLayoutKey(){return 'pulse.analytics.layout.v1:'+me().id+':TEAM';}
function defaultChartLayout(){return Object.fromEntries(chartLayoutKinds.map(kind=>[kind,{visible:true,width:4,height:380}]));}
function readChartLayout(){
 const key=chartLayoutKey();if(chartLayoutCache.has(key))return chartLayoutCache.get(key);
 const result=defaultChartLayout();let stored;
 try{stored=JSON.parse(localStorage.getItem(key)||'null');}catch{}
 if(stored?.version===1&&stored.charts&&typeof stored.charts==='object')for(const kind of chartLayoutKinds){const c=stored.charts[kind];if(!c||typeof c!=='object')continue;result[kind]={visible:typeof c.visible==='boolean'?c.visible:true,width:chartLayoutWidths.includes(c.width)?c.width:4,height:chartLayoutHeights.includes(c.height)?c.height:380};}
 chartLayoutCache.set(key,result);return result;
}
function saveChartLayout(){
 try{localStorage.setItem(chartLayoutKey(),JSON.stringify({version:1,charts:readChartLayout()}));return true;}
 catch{toast('El diseño se conserva durante esta sesión; este navegador no permite guardarlo.',true);return false;}
}
function chartLayoutStatus(message){const status=document.querySelector('#chart-layout-status');if(status)status.textContent=message;}
function chartTile(kind,report,pref,editing){
 const template=document.createElement('template');template.innerHTML=decisionVisualButton(kind,report);
 const button=template.content.firstElementChild,footer=button.lastElementChild,heading=document.createElement('div'),plot=document.createElement('div');heading.className='chart-tile-heading';plot.className='chart-tile-plot';
 heading.append(button.firstElementChild);heading.append(button.firstElementChild);
 while(button.firstChild&&button.firstChild!==footer)plot.append(button.firstChild);
 button.prepend(heading,plot);button.classList.add('chart-tile-open');
 const controls=editing?`<div class="chart-tile-controls"><label><span>Ancho</span><select data-chart-width="${kind}" aria-label="Ancho de ${visualTitles[kind]}">${chartLayoutWidths.map(width=>`<option value="${width}" ${pref.width===width?'selected':''}>${chartWidthNames[width]}</option>`).join('')}</select></label><label><span>Altura</span><select data-chart-height="${kind}" aria-label="Altura de ${visualTitles[kind]}">${chartLayoutHeights.map(height=>`<option value="${height}" ${pref.height===height?'selected':''}>${chartHeightNames[height]}</option>`).join('')}</select></label>${btn('Ocultar','chart-layout-hide',kind,'link small')}</div>`:'';
 return `<article class="panel decision-card chart-tile" data-chart-kind="${kind}" data-width="${pref.width}" data-height="${pref.height}">${controls}${button.outerHTML}${editing?`<button type="button" class="chart-resize-handle" data-chart-resize="${kind}" aria-label="Redimensionar ${visualTitles[kind]}. Arrastra o usa las flechas del teclado." title="Arrastra para ajustar ancho y altura; también puedes usar las flechas">◢</button>`:''}</article>`;
}
function configurableAnalyticsDeck(report){
 const prefs=readChartLayout(),editing=chartLayoutEditing.has(chartLayoutKey()),visible=chartLayoutKinds.filter(kind=>prefs[kind].visible);
 return `<section class="decision-section personalized-charts ${editing?'chart-editing':''}"><header class="section-heading chart-layout-header"><div><h2>Tu operación, en gráficas</h2><p id="chart-layout-status" role="status">${editing?'Elige tamaño o arrastra la esquina. Se guarda para tu usuario en este navegador.':'Tu vista personal · '+visible.length+' de '+chartLayoutKinds.length+' gráficas visibles'}</p></div><div>${btn(editing?'Listo':'Personalizar tablero','chart-layout-edit','','secondary small',`aria-pressed="${editing}"`)}${btn('Restaurar diseño','chart-layout-reset','','link small')}</div></header>${editing?`<section class="chart-visibility-panel" aria-label="Elegir gráficas visibles"><p><strong>Gráficas visibles</strong> · Pulsa para mostrar u ocultar. En pantallas pequeñas se adapta el ancho sin cambiar tus tamaños guardados.</p><div>${chartLayoutKinds.map(kind=>`<button type="button" data-action="chart-layout-visibility" data-id="${kind}" aria-pressed="${prefs[kind].visible}"><span aria-hidden="true">${prefs[kind].visible?'✓':'＋'}</span>${visualTitles[kind]}</button>`).join('')}</div></section>`:''}<div class="decision-grid chart-layout-grid">${visible.map(kind=>chartTile(kind,report,prefs[kind],editing)).join('')}</div>${visible.length?'':`<div class="panel chart-layout-empty"><h3>No hay gráficas visibles</h3><p>Elige las que necesitas para construir tu tablero.</p>${btn('Elegir gráficas','chart-layout-show','','secondary')}</div>`}</section>`;
}
function repaintChartLayout(message='',focusAction='',kind=''){
 cancelChartResize();
 const old=document.querySelector('.personalized-charts');if(!old||!analyticsReport||analyticsReport.mode!=='TEAM')return;
 const main=document.querySelector('#main'),scroll=main?.scrollTop||0,template=document.createElement('template');template.innerHTML=configurableAnalyticsDeck(analyticsReport);old.replaceWith(template.content.firstElementChild);
 if(main)main.scrollTop=scroll;if(message)chartLayoutStatus(message);
 if(focusAction){const target=document.querySelector('.personalized-charts [data-action="'+focusAction+'"]'+(kind?'[data-id="'+kind+'"]':''));target?.focus({preventScroll:true});}
}
function chartLayoutAction(action,kind){
 if(analyticsReport?.mode!=='TEAM')return;
 const prefs=readChartLayout();
 if(action==='chart-layout-edit'){const key=chartLayoutKey();chartLayoutEditing.has(key)?chartLayoutEditing.delete(key):chartLayoutEditing.add(key);repaintChartLayout('','chart-layout-edit');return;}
 if(action==='chart-layout-show'){chartLayoutEditing.add(chartLayoutKey());repaintChartLayout('Selecciona las gráficas que deseas mostrar.','chart-layout-edit');return;}
 if(action==='chart-layout-reset'){chartLayoutCache.set(chartLayoutKey(),defaultChartLayout());const saved=saveChartLayout();repaintChartLayout(saved?'Diseño original restaurado.':'Diseño original restaurado durante esta sesión.','chart-layout-reset');return;}
 if(!chartLayoutKinds.includes(kind))return;
 if(action==='chart-layout-hide'||action==='chart-layout-visibility'){prefs[kind].visible=action==='chart-layout-hide'?false:!prefs[kind].visible;const saved=saveChartLayout();repaintChartLayout((prefs[kind].visible?'Mostrada: ':'Oculta: ')+visualTitles[kind]+(saved?'. Diseño guardado.':'. Sólo durante esta sesión.'),'chart-layout-visibility',kind);}
}
function updateChartTile(card,kind,pref){
 card.dataset.width=String(pref.width);card.dataset.height=String(pref.height);
 const width=card.querySelector('[data-chart-width]'),height=card.querySelector('[data-chart-height]');if(width)width.value=String(pref.width);if(height)height.value=String(pref.height);
 chartLayoutStatus(visualTitles[kind]+' · '+chartWidthNames[pref.width]+' · altura '+chartHeightNames[pref.height]);
}
function cancelChartResize(){
 if(!chartResize)return;const drag=chartResize;chartResize=null;if(drag.card.isConnected)updateChartTile(drag.card,drag.kind,drag.original);drag.handle.classList.remove('is-resizing');try{drag.handle.releasePointerCapture(drag.pointer);}catch{}
}
document.addEventListener('change',event=>{
 const input=event.target;if(!input.matches('[data-chart-width],[data-chart-height]')||analyticsReport?.mode!=='TEAM')return;
 const kind=input.dataset.chartWidth||input.dataset.chartHeight;if(!chartLayoutKinds.includes(kind))return;
 const dimension=input.hasAttribute('data-chart-width')?'width':'height',value=Number(input.value),allowed=dimension==='width'?chartLayoutWidths:chartLayoutHeights;if(!allowed.includes(value))return;
 const pref=readChartLayout()[kind];pref[dimension]=value;updateChartTile(input.closest('.chart-tile'),kind,pref);if(saveChartLayout())chartLayoutStatus('Tamaño guardado: '+visualTitles[kind]+'.');
});
document.addEventListener('pointerdown',event=>{
 const handle=event.target.closest?.('[data-chart-resize]');if(!handle||event.button!==0||analyticsReport?.mode!=='TEAM'||innerWidth<=650)return;
 const card=handle.closest('.chart-tile'),grid=card.closest('.chart-layout-grid'),kind=handle.dataset.chartResize,pref=readChartLayout()[kind];if(!pref)return;
 cancelChartResize();event.preventDefault();event.stopPropagation();const rect=card.getBoundingClientRect();chartResize={handle,card,kind,pointer:event.pointerId,x:event.clientX,y:event.clientY,width:rect.width,height:rect.height,gridWidth:grid.clientWidth,gap:parseFloat(getComputedStyle(grid).columnGap)||12,original:{...pref},preview:{...pref}};handle.setPointerCapture(event.pointerId);handle.classList.add('is-resizing');
});
document.addEventListener('pointermove',event=>{
 const drag=chartResize;if(!drag||event.pointerId!==drag.pointer)return;event.preventDefault();
 const width=drag.width+event.clientX-drag.x,height=drag.height+event.clientY-drag.y,allowed=innerWidth<=1100?[6,12]:chartLayoutWidths;
 const pixels=span=>(drag.gridWidth+drag.gap)*span/12-drag.gap;
 drag.preview.width=allowed.reduce((best,n)=>Math.abs(pixels(n)-width)<Math.abs(pixels(best)-width)?n:best,allowed[0]);drag.preview.height=chartLayoutHeights.reduce((best,n)=>Math.abs(n-height)<Math.abs(best-height)?n:best,chartLayoutHeights[0]);updateChartTile(drag.card,drag.kind,drag.preview);
},{passive:false});
document.addEventListener('pointerup',event=>{
 const drag=chartResize;if(!drag||event.pointerId!==drag.pointer)return;chartResize=null;drag.handle.classList.remove('is-resizing');if(!drag.card.isConnected)return;
 readChartLayout()[drag.kind]={...drag.preview};if(saveChartLayout())chartLayoutStatus('Tamaño guardado: '+visualTitles[drag.kind]+'.');try{drag.handle.releasePointerCapture(drag.pointer);}catch{}
});
document.addEventListener('pointercancel',cancelChartResize);document.addEventListener('lostpointercapture',event=>{if(chartResize?.pointer===event.pointerId)cancelChartResize();});window.addEventListener('resize',cancelChartResize);window.addEventListener('blur',cancelChartResize);
document.addEventListener('keydown',event=>{
 if(event.key==='Escape'&&chartResize){cancelChartResize();chartLayoutStatus('Cambio de tamaño cancelado.');return;}
 const handle=event.target.closest?.('[data-chart-resize]');if(!handle||!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||analyticsReport?.mode!=='TEAM')return;
 event.preventDefault();event.stopPropagation();const kind=handle.dataset.chartResize,pref=readChartLayout()[kind],horizontal=['ArrowLeft','ArrowRight'].includes(event.key),dimension=horizontal?'width':'height',choices=horizontal?chartLayoutWidths:chartLayoutHeights,step=['ArrowLeft','ArrowUp'].includes(event.key)?-1:1;
 pref[dimension]=choices[Math.max(0,Math.min(choices.length-1,choices.indexOf(pref[dimension])+step))];updateChartTile(handle.closest('.chart-tile'),kind,pref);if(saveChartLayout())chartLayoutStatus('Tamaño guardado: '+visualTitles[kind]+'.');
});
