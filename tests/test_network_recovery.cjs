const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const timers = [], requests = [], cleared = [];
const session = {room:'TEST',player:'hero'};
const context = {
  AbortController, window:{location:{protocol:'http:'}},
  setTimeout(fn, ms) { timers.push({fn,ms}); return timers.length; },
  clearTimeout(id) { cleared.push(id); },
  fetch(url, options) {
    requests.push({url,...options});
    if (requests.length === 1) return new Promise((resolve,reject) => {
      options.signal.addEventListener('abort',()=>reject(Object.assign(new Error('timeout'),{name:'AbortError'})));
    });
    return Promise.resolve({ok:true,json:async()=>({ok:true})});
  },
  session, inputBusy:false, pendingInput:{session,direction:{x:1,y:0,attack:false}}, inputSequence:0,
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('async function api('),source.indexOf('function sendAction(')),context);
vm.runInContext(source.slice(source.indexOf('function flushMovement('),source.indexOf('window.addEventListener("keydown"')),context);
(async()=>{
  context.flushMovement();
  assert.equal(context.inputBusy,true);
  context.pendingInput = {session,direction:{x:0,y:0,attack:false}};
  context.flushMovement();
  assert.equal(requests.length,1,'Only one input request is in flight');
  assert.equal(timers[0].ms,5000);
  timers[0].fn();
  await new Promise(setImmediate);
  assert.equal(requests.length,2,'A stuck request must not block movement forever');
  assert.equal(JSON.parse(requests[1].body).x,0,'The latest release supersedes stale movement');
  assert.equal(JSON.parse(requests[1].body).sequence,2);
  assert.equal(context.inputBusy,false);
  assert.deepEqual(cleared,[1,2]);
  console.log('Timed-out movement requests release the queue and send the newest input.');
})().catch(error=>{console.error(error);process.exitCode=1;});
