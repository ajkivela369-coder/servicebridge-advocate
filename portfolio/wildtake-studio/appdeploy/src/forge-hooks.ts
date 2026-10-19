import { useEffect, useState, type SetStateAction } from 'react';

export function useForgeState<T>(key:string, initial:T|(()=>T)) {
  const [value,setValue]=useState<T>(()=>{try{const raw=sessionStorage.getItem('forge.project.'+key);if(raw!==null)return JSON.parse(raw) as T;}catch{}return typeof initial==='function'?(initial as ()=>T)():initial;});
  useEffect(()=>{try{sessionStorage.setItem('forge.project.'+key,JSON.stringify(value));}catch{}},[key,value]);
  return [value,setValue] as const;
}

export function useForgePageMode<T extends 'Simple'|'Pro'>(initial:T){
  const current=()=>location.pathname.endsWith('/pro')||/-pro\.html$/.test(location.pathname)?'Pro':'Simple';
  const [mode,setMode]=useState<T>(current() as T);
  const change=(next:SetStateAction<T>)=>{
    const value=typeof next==='function'?(next as (old:T)=>T)(mode):next;
    const base=location.pathname.replace(/\/pro$/, '').replace(/\/(?:index\.html)?$/, '');
    history.pushState(null,'',value==='Pro'?base+'/pro':base+'/');
    setMode(value);document.body.dataset.pageMode=value.toLowerCase();(window as any).ForgeShell?.reflectMode(value.toLowerCase());
  };
  useEffect(()=>{const pop=()=>{const next=current() as T;setMode(next);document.body.dataset.pageMode=next.toLowerCase();(window as any).ForgeShell?.reflectMode(next.toLowerCase());};window.addEventListener('popstate',pop);return()=>window.removeEventListener('popstate',pop);},[]);
  useEffect(()=>{(window as any).ForgeApp={...(window as any).ForgeApp,navigateMode:(next:string)=>change((next==='pro'?'Pro':'Simple') as T)};},[mode]);
  return [mode,change] as const;
}

export function useForgeAssistant(appId:string,context:unknown,advancedHeadings:string[]=[],managesPages=false){
  useEffect(()=>{
    const body=document.body;body.dataset.forgeApp=appId;
    const base=location.pathname.replace(/\/pro$/, '').replace(/\/(?:index\.html)?$/, '');
    body.dataset.simpleUrl=base+'/';body.dataset.proUrl=base+'/pro';
    if(managesPages)body.dataset.managesPages='true';
    (window as any).ForgeApp={...(window as any).ForgeApp,assistantApp:appId,context:()=>JSON.stringify(context).slice(0,15000)};
    const mark=()=>{for(const h of document.querySelectorAll('h2,h3')){if(advancedHeadings.includes(h.textContent?.trim()||''))h.closest('section')?.classList.add('forge-pro-feature');}};mark();
    const observer=new MutationObserver(mark);observer.observe(document.getElementById('root')!,{childList:true,subtree:true});
    if(!(window as any).ForgeShell&&!document.getElementById('forgeSharedAssistant')){const script=document.createElement('script');script.id='forgeSharedAssistant';script.src=base+'/forge-shell.js';document.body.append(script);}
    return()=>observer.disconnect();
  },[appId,context,managesPages]);
}
