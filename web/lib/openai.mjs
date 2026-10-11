export async function openai(endpoint,body){
 if(!process.env.OPENAI_API_KEY)throw new Error('線上 AI 金鑰尚未設定。');
 const response=await fetch('https://api.openai.com/v1/'+endpoint,{method:'POST',headers:{Authorization:'Bearer '+process.env.OPENAI_API_KEY,'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(25000)});
 if(!response.ok){
  if(response.status===429)throw new Error('AI 配額不足或請求過多，請稍後重試。');
  if(response.status===401)throw new Error('線上 AI 金鑰驗證失敗，請聯絡管理者。');
  throw new Error('AI 服務暫時無法完成請求，請稍後重試。');
 }
 return response.json();
}
export function responseText(response){
 const text=(response.output??[]).flatMap(x=>x.content??[]).filter(x=>x.type==='output_text').map(x=>x.text).join('\n');
 if(!text.trim())throw new Error('AI 回傳空白內容，請重試。');return text.trim();
}
