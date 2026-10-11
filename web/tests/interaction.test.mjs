import test from 'node:test';
import assert from 'node:assert/strict';
const ui = await import('../interaction.mjs').catch(()=>({}));
test('adding preferences preserves the draft, avoids duplicates and respects the input limit',()=>{
 assert.equal(typeof ui.addPreference,'function');
 assert.equal(ui.addPreference('冷靜','溫柔'),'冷靜；溫柔');
 assert.equal(ui.addPreference('冷靜；溫柔','溫柔'),'冷靜；溫柔');
 assert.equal(ui.addPreference('a'.repeat(2000),'溫柔'),'a'.repeat(2000));
});
test('catalog search combines name/trait matching, series and favorites',()=>{
 assert.equal(typeof ui.filterCharacters,'function');
 const items=[{id:1,name:'甲',series:'作品A',moe_traits:['溫柔']},{id:2,name:'乙',series:'作品B',moe_traits:['溫柔']}];
 assert.deepEqual(ui.filterCharacters(items,{query:' 溫柔 ',series:'作品B'}).map(c=>c.id),[2]);
 assert.deepEqual(ui.filterCharacters(items,{favoritesOnly:true,favorites:new Set([1])}).map(c=>c.id),[1]);
 assert.equal(ui.filterCharacters(items,{query:'不存在'}).length,0);
});
