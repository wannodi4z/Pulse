'use strict';
// Viewport presentation only. Moves existing DOM nodes; never changes application data.
window.PulseLayout=(()=>{
  const memory=new Map();
  const q=(s,r=document)=>r.querySelector(s),all=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let dialogState=null,resizeFrame;
  function name(node,index){
    if(node.dataset.viewLabel)return node.dataset.viewLabel;
    const known={'welcome-banner':'Bienvenida',kpis:'Indicadores','organization-summary':'Resumen de estructura','analytics-metrics':'Totales por tipo','analytics-criteria':'Criterios de cálculo','analytics-method':'Cómo se calcula','analytics-personal-scope':'Mi alcance','delegation-summary':'Backup del Manager','inline-delegation':'Configurar delegación','profile-grid':'Mi cuenta'};
    for(const [cls,title] of Object.entries(known))if(node.classList.contains(cls))return title;
    return q('h2,h3',node)?.textContent.trim()||q('legend',node)?.textContent.trim()||(node.matches('.time-actions')?'Registrar tiempo':node.matches('.timer-list')?'Timers activos':node.querySelector('[data-search-row]')?'Personas':node.matches('.table-panel')?'Registros':`Sección ${index+1}`);
  }
  function pager(count,index,key,label,change){
    const bar=document.createElement('nav');bar.className='viewport-pagination';bar.setAttribute('aria-label',label);
    bar.innerHTML=`<button type="button" aria-label="Anterior: ${esc(label)}">← Anterior</button><label>${esc(label)} <select aria-label="${esc(label)}">${Array.from({length:count},(_,i)=>`<option value="${i}">${i+1} de ${count}</option>`).join('')}</select></label><button type="button" aria-label="Siguiente: ${esc(label)}">Siguiente →</button>`;
    const select=q('select',bar),buttons=all('button',bar);
    function update(value){index=Math.max(0,Math.min(count-1,value));memory.set(key,index);select.value=String(index);buttons[0].disabled=index===0;buttons[1].disabled=index===count-1;change(index);}
    buttons[0].onclick=()=>update(index-1);buttons[1].onclick=()=>update(index+1);select.onchange=()=>update(Number(select.value));update(index);return bar;
  }
  function compose(main,key,heading,footer){
    const roots=()=>[...main.children].filter(n=>n!==heading&&n!==footer);
    const sticky=[];
    const pin=selector=>{const node=q(':scope > '+selector,main);if(node){node.classList.add('workspace-context');sticky.push(node);}};
    const bundle=(nodes,label)=>{nodes=nodes.filter(Boolean);if(!nodes.length)return;const section=document.createElement('section');section.className='workspace-view';section.dataset.viewLabel=label;main.insertBefore(section,nodes[0]);nodes.forEach(n=>section.append(n));return section;};
    if(key==='organization')pin('.organization-summary');
    if(key==='teamTime')pin('.filters');
    if(key==='team')pin('.delegation-summary');
    if(key==='time'){
      pin('.time-actions');
      const totals=q(':scope > .kpis',main);if(totals){totals.classList.add('workspace-totals');pin('.kpis');}
    }
    if(key==='claim'||key==='adp')pin('.capture-summary');
    if(key==='analytics'||key==='myAnalytics'){
      pin('.analytics-filters');pin('.analytics-personal-scope');
      const charts=q(':scope > .analytics-charts',main),metrics=q(':scope > .analytics-metrics',main),criteria=q(':scope > .analytics-criteria',main),method=q(':scope > .analytics-method',main);
      bundle([metrics,charts,criteria,method],'Resumen mensual');
    }
    if(key==='dashboard'){
      q(':scope > .welcome-banner',main)?.remove();
      const metrics=q(':scope > .kpis',main),panels=q(':scope > .two-columns',main);
      bundle([metrics,panels],'Resumen y prioridades');
    }
    roots().forEach(n=>{
      if(n.matches('.table-panel')&&q('[data-search-row]',n))n.dataset.viewLabel='Personas';
      if(n.matches('.timer-list'))n.dataset.viewLabel='Actividades en curso';
      if(n.matches('.delegation-history'))n.dataset.viewLabel='Historial de delegaciones';
      if(n.matches('.inline-delegation'))n.dataset.viewLabel='Asignar backup temporal';
    });
    return {sticky,items:roots().filter(n=>!sticky.includes(n)&&(n.textContent.trim()||n.querySelector('input,button,svg')))};
  }
  function page(main,key){
    if(!main)return;
    const heading=q(':scope > .page-heading',main),footer=q(':scope > .main-footer',main);
    const {sticky,items}=compose(main,key,heading,footer);
    if(!items.length)return;
    const stage=document.createElement('div');stage.className='viewport-stage';main.insertBefore(stage,footer);
    sticky.forEach(n=>main.insertBefore(n,stage));
    items.forEach(n=>stage.append(n));
    const bar=document.createElement('nav');bar.className='viewport-sections';bar.setAttribute('aria-label','Secciones de esta página');
    bar.hidden=items.length<2;
    bar.innerHTML=`<label>${key==='organization'?'Cuenta':'Contenido'} <select aria-label="Vista de la página">${items.map((n,i)=>`<option value="${i}">${esc(name(n,i))}</option>`).join('')}</select></label><span class="viewport-location" aria-live="polite"></span><div><button type="button" data-section-prev aria-label="Vista anterior">←</button><button type="button" data-section-next aria-label="Vista siguiente">→</button></div>`;
    main.insertBefore(bar,stage);let index=Math.min(memory.get('section:'+key)||0,items.length-1);
    function show(next){
      index=Math.max(0,Math.min(items.length-1,next));memory.set('section:'+key,index);
      items.forEach((n,i)=>n.classList.toggle('viewport-off',i!==index));q('select',bar).value=String(index);q('.viewport-location',bar).textContent=`${index+1} / ${items.length}`;
      q('[data-section-prev]',bar).disabled=index===0;q('[data-section-next]',bar).disabled=index===items.length-1;
      fitCollection(items[index],stage.clientHeight,key+':'+index);useAvailableSpace(items[index],stage.clientHeight,key+':'+index);
    }
    q('select',bar).onchange=e=>show(Number(e.target.value));q('[data-section-prev]',bar).onclick=()=>show(index-1);q('[data-section-next]',bar).onclick=()=>show(index+1);
    stage._show=target=>{const i=items.findIndex(n=>n===target||n.contains(target));if(i>=0)show(i);};show(index);
  }
  function fitCollection(root,budget,key){
    all('.group-card',root).forEach(card=>{const footer=q(':scope > footer',card),actions=q(':scope > header .entity-actions',card);if(footer&&actions){[...footer.children].forEach(node=>actions.append(node));footer.remove();}});
    // Table and repeated-card pagination retains every row, header and delegated action.
    const selectors='tbody,.technicians,.group-grid,.account-body,.record-list,.rules-grid,.priority-list,.analytics-ranking,.audit-list,.rule-intervals,.rule-segments,.offboard-transfers,.delegation-group-options,#group-checks,.delegation-list,.admin-account-list';
    const lists=all(selectors,root).reverse();
    if(root.matches(selectors))lists.push(root);
    lists.forEach((list,li)=>{
      if(list._viewport)return;
      const children=[...list.children].filter(n=>!n.classList.contains('viewport-pagination'));
      if(children.length<2)return;
      const table=list.tagName==='TBODY';const height=children.reduce((total,n)=>total+n.getBoundingClientRect().height,0);
      if(height<Math.max(130,budget*.55)&&root.getBoundingClientRect().height<=budget)return;
      const overhead=Math.max(70,root.getBoundingClientRect().height-height)+42;
      let size=table?Math.max(1,Math.floor((budget-overhead)/Math.max(45,height/children.length))):list.matches('.organization-board')&&innerWidth>=1050?2:1;
      size=Math.min(size,children.length);if(size>=children.length)return;
      const count=Math.ceil(children.length/size),id=key+':list:'+li;
      const label=table?'Filas':list.matches('.technicians')?'Técnicos':list.matches('.group-grid')?'Grupos':list.matches('.account-body')?'Managers':list.matches('.rule-intervals')?'Intervalos':list.matches('.rule-segments')?'Días':list.matches('.rules-grid')?'Reglas':'Elementos';
      const control=pager(count,Math.min(memory.get(id)||0,count-1),id,label,value=>children.forEach((n,i)=>n.classList.toggle('viewport-off',Math.floor(i/size)!==value)));
      list._viewport={children,size,control};
      if(table){const wrapper=list.closest('.table-scroll')||list.parentElement;wrapper.after(control);}else list.after(control);
    });
    // Split tall paired panels into a single panel per view, without scaling typography.
    all('.two-columns,.profile-grid',root).concat(root.matches('.two-columns,.profile-grid')?[root]:[]).forEach((list,i)=>{
      if(list._viewport||list.getBoundingClientRect().height<=budget)return;
      const nodes=[...list.children];if(nodes.length<2)return;
      const id=key+':panels:'+i,control=pager(nodes.length,memory.get(id)||0,id,'Panel',value=>nodes.forEach((n,j)=>n.classList.toggle('viewport-off',j!==value)));
      list.classList.add('viewport-single-column');list.after(control);list._viewport={children:nodes,control};
    });
  }
  function useAvailableSpace(root,budget,key){
    // Once parent pagination has selected an entity, fill the remaining space with its members.
    all('.technicians',root).forEach((list,i)=>{
      const holder=list._viewport;if(!holder||!list.getClientRects().length)return;
      const {children}=holder,select=q('select',holder.control),first=Number(select.value)*holder.size;
      let size=holder.size;
      for(let candidate=size+1;candidate<=children.length;candidate++){
        const pageIndex=Math.floor(first/candidate),count=Math.ceil(children.length/candidate);
        children.forEach((node,j)=>node.classList.toggle('viewport-off',Math.floor(j/candidate)!==pageIndex));
        holder.control.hidden=count===1;
        if(root.getBoundingClientRect().height>budget-4)break;
        size=candidate;
      }
      const pageIndex=Math.floor(first/size),count=Math.ceil(children.length/size);
      children.forEach((node,j)=>node.classList.toggle('viewport-off',Math.floor(j/size)!==pageIndex));holder.control.hidden=false;
      if(size===holder.size)return;
      if(count===1){holder.control.remove();delete list._viewport;return;}
      const id=key+':members:'+i,control=pager(count,pageIndex,id,'Técnicos',value=>children.forEach((node,j)=>node.classList.toggle('viewport-off',Math.floor(j/size)!==value)));
      holder.control.replaceWith(control);list._viewport={children,size,control};
    });
  }
  function reveal(target){
    if(!target)return;const ruleDay=target.closest('[data-rule-day]');if(ruleDay){all('[data-rule-day]').forEach(n=>n.hidden=n!==ruleDay);all('[data-action=rule-day-open]').forEach(n=>n.setAttribute('aria-pressed',String(n.dataset.id===ruleDay.dataset.ruleDay)));}
    if(dialogState&&dialogState.body.contains(target)){const i=dialogState.pages.findIndex(part=>part.contains(target));if(i>=0)dialogState.show(i);}
    const stage=target.closest('.viewport-stage');stage?._show(target);
    let parent=target;
    while(parent&&parent!==stage){
      const holder=parent.parentElement?._viewport;
      if(holder?.children){const i=holder.children.indexOf(parent);if(i>=0){const select=q('select',holder.control);select.value=String(Math.floor(i/(holder.size||1)));select.dispatchEvent(new Event('change'));}}
      parent=parent.parentElement;
    }
  }
  function filterSearch(value){
    all('[data-search-row]').forEach(row=>{if(value)row.classList.remove('viewport-off');});
    all('tbody').forEach(list=>{if(list._viewport){list._viewport.control.hidden=!!value;if(!value)q('select',list._viewport.control).dispatchEvent(new Event('change'));}});
  }
  function unwrapDialog(){
    if(!dialogState)return;const {body,pages,bar,form}=dialogState;
    pages.forEach(part=>{while(part.firstChild)body.insertBefore(part.firstChild,bar);part.remove();});bar.remove();body.classList.remove('wizard-body');
    if(form){form.noValidate=false;all('[type=submit]',form).forEach(b=>b.hidden=false);}dialogState=null;
  }
  function dialog(){
    const modal=q('#modal');if(!modal?.open)return;
    const continuing=!!dialogState?.body.isConnected;
    if(continuing)unwrapDialog();else dialogState=null;
    const form=q(':scope > form',modal),body=q(':scope > form > .form-body,:scope > form > .access-body,:scope > .form-body,:scope > .about-project',modal);
    if(!body)return;
    if(body.scrollHeight>body.clientHeight+1)fitCollection(body,Math.max(140,body.clientHeight-58),'dialog-lists');
    if(body.scrollHeight<=body.clientHeight+1)return;
    const cap=Math.max(140,body.clientHeight-58),nodes=[...body.children],pages=[];
    const fragments=[];
    function flatten(node){
      if(node.getBoundingClientRect().height>cap&&node.children.length>1&&node.matches('.form-grid,.access-section,.access-fields-grid')){
        if(node.matches('fieldset')){const legend=q('legend',node);if(legend)fragments.push(legend);}
        [...node.children].filter(n=>n.tagName!=='LEGEND').forEach(flatten);node.remove();
      }else fragments.push(node);
    }
    nodes.forEach(flatten);
    body.classList.add('wizard-body');const bar=document.createElement('nav');bar.className='wizard-navigation';body.append(bar);
    let current=document.createElement('section');current.className='wizard-step';pages.push(current);body.insertBefore(current,bar);
    fragments.forEach(node=>{
      current.append(node);
      if(current.getBoundingClientRect().height>cap&&current.children.length>1){node.remove();current=document.createElement('section');current.className='wizard-step';pages.push(current);body.insertBefore(current,bar);current.append(node);}
    });
    const initial=continuing?Math.min(memory.get('dialog:'+q('#dialog-title',modal)?.textContent)||0,pages.length-1):0;
    let index=initial;
    function show(value){index=Math.max(0,Math.min(pages.length-1,value));memory.set('dialog:'+q('#dialog-title',modal)?.textContent,index);pages.forEach((part,i)=>part.hidden=i!==index);bar.innerHTML=`<button type="button" data-step-back ${index===0?'disabled':''}>← Anterior</button><span aria-live="polite">Paso ${index+1} de ${pages.length}</span><button type="button" data-step-next ${index===pages.length-1?'disabled':''}>Continuar →</button>`;
      if(form)all('[type=submit]',form).forEach(b=>b.hidden=index!==pages.length-1);
      q('[data-step-back]',bar).onclick=()=>show(index-1);q('[data-step-next]',bar).onclick=()=>{const invalid=all('input,select,textarea',pages[index]).find(n=>!n.disabled&&!n.checkValidity());if(invalid){reveal(invalid);invalid.reportValidity();return;}show(index+1);};
    }
    if(form)form.noValidate=true;
    dialogState={body,pages,bar,form,show};show(initial);
  }
  function validate(form){
    const invalid=all('input,select,textarea',form).find(n=>!n.disabled&&!n.checkValidity());
    if(!invalid)return true;
    if(dialogState?.form===form){const index=dialogState.pages.findIndex(part=>part.contains(invalid));if(index>=0)dialogState.show(index);}
    reveal(invalid);invalid.reportValidity();return false;
  }
  document.addEventListener('close',()=>{dialogState=null;},true);
  window.addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{dialog();const stage=q('.viewport-stage');if(stage){all('*',stage).forEach(list=>{if(list._viewport){list._viewport.children.forEach(n=>n.classList.remove('viewport-off'));list._viewport.control.remove();delete list._viewport;list.classList.remove('viewport-single-column');}});const active=[...stage.children].find(n=>!n.classList.contains('viewport-off'));if(active){fitCollection(active,stage.clientHeight,'resize');useAvailableSpace(active,stage.clientHeight,'resize');}}});});
  return {page,dialog,reveal,validate,filterSearch};
})();
