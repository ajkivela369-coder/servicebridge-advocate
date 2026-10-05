type ApiResponse<T=any>={data:T};

async function post<T=any>(path:string, body:unknown):Promise<ApiResponse<T>>{
  const response=await fetch(path,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body),
  });
  let data:any={};
  try{data=await response.json();}catch{data={error:await response.text().catch(()=> '')};}
  if(!response.ok){
    const message=data?.error||data?.message||('Request failed: '+response.status);
    throw new Error(message);
  }
  return {data};
}

export const api={post};
