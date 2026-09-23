type ApiResponse<T=any> = { data:T };

async function request<T=any>(method:string,url:string,data?:any):Promise<ApiResponse<T>>{
  let target=url;
  const init:RequestInit={method,headers:{}};
  if(method==='GET'&&data&&typeof data==='object'){
    const params=new URLSearchParams();
    Object.entries(data).forEach(([key,value])=>{
      if(value!==undefined&&value!==null)params.set(key,String(value));
    });
    const qs=params.toString();
    if(qs)target += (target.includes('?')?'&':'?')+qs;
  }else if(data!==undefined){
    (init.headers as Record<string,string>)['content-type']='application/json';
    init.body=JSON.stringify(data);
  }

  const response=await fetch(target,init);
  const text=await response.text();
  let payload:any=text;
  try{payload=text?JSON.parse(text):{};}catch{}
  if(!response.ok){
    const err:any=new Error(payload?.error||payload?.message||`HTTP ${response.status}`);
    err.response={data:payload,status:response.status};
    throw err;
  }
  return {data:payload as T};
}

export const api={
  get:<T=any>(url:string,data?:any)=>request<T>('GET',url,data),
  post:<T=any>(url:string,data?:any)=>request<T>('POST',url,data),
  put:<T=any>(url:string,data?:any)=>request<T>('PUT',url,data),
  delete:<T=any>(url:string,data?:any)=>request<T>('DELETE',url,data),
};
