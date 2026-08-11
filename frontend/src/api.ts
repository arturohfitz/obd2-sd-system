const BASE = import.meta.env.VITE_API_URL || '';
export const token = () => localStorage.getItem('obd2_token');
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
  const auth=token();
  const response=await fetch(`${BASE}${path}`,{...options,headers:{'Content-Type':'application/json',...(auth?{Authorization:`Bearer ${auth}`}:{ }),...options.headers}});
  if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||'No fue posible completar la operación');}
  return response.json();
}
