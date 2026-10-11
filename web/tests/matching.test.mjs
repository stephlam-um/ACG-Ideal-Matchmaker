import test from 'node:test';
import assert from 'node:assert/strict';
import { prepareIndex, search, validateInput } from '../lib/matching.mjs';
test('normalized retrieval has stable ordering and bounds',()=>{
 const index=prepareIndex([[1,0],[0,1],[-1,0]]);
 assert.deepEqual(search([1,0],index,2).map(x=>[x.index,x.score]),[[0,100],[1,50]]);
});
test('reject incompatible and invalid vectors',()=>{
 assert.throws(()=>prepareIndex([[0,0]]));
 assert.throws(()=>search([1],prepareIndex([[1,0]]),5));
});
test('validate before model calls',()=>{
 assert.throws(()=>validateInput({description:' ',k:5}));
 assert.throws(()=>validateInput({description:'x',k:500}));
 assert.equal(validateInput({description:' x ',k:5}).description,'x');
});
