const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../static/audio.js'),'utf8');
let now=1000, played=[], saved=null, documentHidden=false;
const listeners={};
class Context {
  constructor(){this.state='suspended';this.currentTime=0;this.destination={};}
  async resume(){this.state='running';}
  createGain(){return {gain:{value:0,setTargetAtTime(){}},connect(){},disconnect(){}};}
  createDynamicsCompressor(){return {threshold:{},knee:{},ratio:{},connect(){}};}
  createStereoPanner(){return {pan:{},connect(){},disconnect(){}};}
  createBufferSource(){return {connect(){},disconnect(){},start(){played.push(this.buffer);},stop(){this.onended?.();}};}
  async decodeAudioData(data){return data;}
}
const document={get hidden(){return documentHidden;},querySelectorAll(){return [];},addEventListener(t,fn){listeners[t]=fn;}};
const sandbox={document,window:{AudioContext:Context,addEventListener(t,fn){listeners[t]=fn;}},
  localStorage:{getItem(){return null;},setItem(k,v){saved=JSON.parse(v);}},performance:{now:()=>now},
  fetch:async url=>({ok:true,arrayBuffer:async()=>url})};
vm.createContext(sandbox);vm.runInContext(source,sandbox);
const audio=sandbox.window.GauntletAudio;
const hero={id:'me',class:'Knight',hp:150,maxHp:150,damageTaken:0,status:'alive',animation:'light',animationUntil:0,x:480,y:300};
let room={code:'TEST',you:'me',stage:1,phase:'combat',players:[hero],enemies:[],effects:[],chest:null};
function observe(changes={}){now+=120;room={...room,...changes};audio.observe(room);}
function has(name){return played.includes('audio/'+name+'.wav');}
(async()=>{
  observe({effects:[{id:'old',type:'dash'}]});assert.equal(played.length,0,'First snapshot stays silent');
  await audio.unlock();
  observe();assert.equal(played.length,0,'Unlock never replays earlier events');
  observe({players:[{...hero,animationUntil:1}]});assert.ok(has('blade'));
  const count=played.length;observe();assert.equal(played.length,count,'Same attack is not replayed');
  observe({players:[{...hero,animationUntil:2,animation:'ultimate',damageTaken:1,hp:140}],effects:[{id:'dash1',type:'dash',x:480,y:300}]});
  assert.ok(has('ultimate'));assert.ok(has('hurt'));assert.ok(has('dash'));
  observe({players:[{...hero,status:'downed',hp:0}]});assert.ok(has('down'));
  observe({players:[hero]});assert.ok(has('revive'));
  observe({phase:'chest',effects:[],chest:{opened:false}});assert.ok(has('clear'));
  observe({chest:{opened:true},privateNotice:'Chest loot: Common Sword'});assert.ok(has('loot'));
  // Disconnect/reconnect gaps, background tabs and new scenes use a silent baseline.
  now+=1000;const beforeGap=played.length;
  observe({phase:'combat',effects:[{id:'stale',type:'dash'}]});assert.equal(played.length,beforeGap);
  documentHidden=true;listeners.visibilitychange();observe({effects:[{id:'hidden',type:'dash'}]});
  documentHidden=false;observe();assert.equal(played.length,beforeGap);
  observe({stage:2,effects:[{id:'newscene',type:'dash'}]});assert.equal(played.length,beforeGap);
  listeners.input({target:{matches:s=>s==='[data-audio-mute]',checked:true}});
  assert.equal(saved.muted,true);observe({effects:[{id:'muted',type:'dash'}]});assert.equal(played.length,beforeGap);
  listeners.input({target:{matches:s=>s==='[data-audio-mute]',checked:false}});
  observe();assert.equal(played.length,beforeGap,'Unmuting does not replay suppressed sounds');
  audio.reset();observe({code:'OTHER',effects:[{id:'join',type:'dash'}]});assert.equal(played.length,beforeGap);
  // Simultaneous effect spam is bounded, important local damage can displace ambience.
  observe({effects:Array.from({length:50},(_,i)=>({id:'spam'+i,type:'impact'}))});
  assert.equal(played.length,beforeGap+1,'A burst of identical impacts is coalesced');
  const manifest=JSON.parse(fs.readFileSync(path.join(__dirname,'../art/audio/sounds.json')));
  audio.reset();
  const voiceStart=played.length;
  for(const name of Object.keys(manifest.sounds)) audio.play(name,{priority:0});
  assert.equal(played.length-voiceStart,10,'Simultaneous voices are capped');
  now+=150;assert.equal(audio.play('hurt',{priority:3}),true,'Important damage displaces a lower-priority voice');
  // A fresh page reads persisted mute and handles unavailable audio gracefully.
  const persisted={...sandbox,window:{AudioContext:Context,addEventListener(){}},
    localStorage:{getItem(){return '{"volume":0.3,"muted":true}';},setItem(){}}};
  vm.createContext(persisted);vm.runInContext(source,persisted);
  await persisted.window.GauntletAudio.unlock();
  assert.equal(persisted.window.GauntletAudio.play('loot'),false,'Saved mute survives page initialization');
  const unavailable={...sandbox,window:{addEventListener(){}},localStorage:{getItem(){throw Error('Storage restricted');}}};
  vm.createContext(unavailable);vm.runInContext(source,unavailable);
  await unavailable.window.GauntletAudio.unlock();assert.equal(unavailable.window.GauntletAudio.play('loot'),false);
  for(const name of Object.keys(manifest.sounds)) {
    const wav=fs.readFileSync(path.join(__dirname,'../static/audio',name+'.wav'));
    assert.equal(wav.toString('ascii',0,4),'RIFF');assert.equal(wav.readUInt32LE(24),44100);
    assert.equal(wav.readUInt16LE(22),1);assert.equal(wav.readUInt16LE(34),16);
    let peak=0;
    for(let i=44;i<wav.length;i+=2) peak=Math.max(peak,Math.abs(wav.readInt16LE(i)));
    assert.ok(peak>0 && peak<22000,name+' is audible and bounded');
    assert.equal(wav.readUInt32LE(40),wav.length-44);
  }
  console.log('Audio: activation, confirmed attacks, deduplication, damage, dash, down/revive, loot, reconnect, mute, bursts and 20 WAV files passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
