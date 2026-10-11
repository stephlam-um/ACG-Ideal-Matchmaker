export function prepareIndex(vectors) {
 if (!Array.isArray(vectors)||!vectors.length) throw new Error('角色向量為空');
 const dimensions=vectors[0].length;
 return vectors.map(row=>{
  if(!row.length||row.length!==dimensions||row.some(x=>!Number.isFinite(x)))throw new Error('角色向量格式無效');
  const norm=Math.hypot(...row);if(!norm)throw new Error('角色向量為零');
  return row.map(x=>x/norm);
 });
}
export function search(query,index,k=5){
 if(!Array.isArray(query)||query.length!==index[0].length||query.some(x=>!Number.isFinite(x)))throw new Error('查詢向量維度無效');
 const norm=Math.hypot(...query);if(!norm)throw new Error('查詢向量為零');
 const scores=index.map(row=>row.reduce((sum,x,i)=>sum+x*query[i]/norm,0));
 const min=Math.min(...scores),span=Math.max(...scores)-min;
 return scores.map((raw,index)=>({index,score:Math.abs(span)<1e-8?50:(raw-min)/span*100,cosine:raw})).sort((a,b)=>b.score-a.score||a.index-b.index).slice(0,k);
}
export function validateInput(body){
 if(typeof body?.description!=='string'||!body.description.trim()||body.description.length>2000)throw new Error('請輸入 1–2000 字的理想型描述。');
 const k=body.k??5;if(!Number.isInteger(k)||k<3||k>10)throw new Error('結果數量必須介於 3 與 10。');
 return {description:body.description.trim(),k};
}
