const BASE = import.meta.env.VITE_API_URL || '';
export const token = () => localStorage.getItem('obd2_token');
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
  const auth=token();
  const response=await fetch(`${BASE}${path}`,{...options,headers:{'Content-Type':'application/json',...(auth?{Authorization:`Bearer ${auth}`}:{ }),...options.headers}});
  if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||'No fue posible completar la operación');}
  return response.json();
}

export async function apiForm<T>(path:string, body:FormData):Promise<T>{
  const auth=token();
  const response=await fetch(`${BASE}${path}`,{method:'POST',body,headers:{...(auth?{Authorization:`Bearer ${auth}`}:{})}});
  if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||'No fue posible cargar el archivo');}
  return response.json();
}

export async function downloadFile(path:string, filename:string){
  const auth=token();
  const response=await fetch(`${BASE}${path}`,{headers:{...(auth?{Authorization:`Bearer ${auth}`}:{})}});
  if(!response.ok)throw new Error('No fue posible descargar el documento');
  const url=URL.createObjectURL(await response.blob());
  const link=document.createElement('a');link.href=url;link.download=filename;link.click();URL.revokeObjectURL(url);
}
