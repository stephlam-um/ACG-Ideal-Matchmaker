import test from 'node:test';
import assert from 'node:assert/strict';
import match from '../api/match.js';
import catalog from '../api/catalog.js';
test('invalid request never needs an API key',async()=>{
 const response=await match.fetch(new Request('http://localhost/api/match',{method:'POST',body:JSON.stringify({description:'',k:5})}));
 assert.equal(response.status,400);
});
test('catalog reveals no secrets or vectors',async()=>{
 const response=catalog.fetch();const data=await response.json();
 assert.equal(data.count,80);assert.equal(data.characters.length,80);assert.equal(data.vectors,undefined);assert.equal(data.OPENAI_API_KEY,undefined);
 assert.equal(new Set(data.characters.map(c=>c.id)).size,80);
 assert.ok(data.characters.slice(50).every(c=>c.source_url?.startsWith('https://') && c.series && c.moe_traits.length>=3));
});
test('method restriction',async()=>assert.equal((await match.fetch(new Request('http://localhost/api/match'))).status,405));
