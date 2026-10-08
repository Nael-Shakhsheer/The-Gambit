const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
let clock = 0, drawn;
const sandbox = { window: {}, Date: { now: () => clock }, Image: class { constructor() { this.complete=true; this.naturalWidth=612; } },
  fetch: async route => ({ ok: true, json: async () => JSON.parse(fs.readFileSync(path.join(__dirname, '../static', route))) }) };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../static/town-sprites.js'),'utf8'),sandbox);
(async () => {
  await new Promise(setImmediate);
  const renderer = sandbox.window.GauntletTownSprites;
  const ctx = { save(){}, restore(){}, drawImage(...args){ drawn=args; } };
  const directions=['south','south-east','east','north-east','north','north-west','west','south-west'];
  for (const key of ['Merchant','Guildmaster','Alchemist','Innkeeper',...Array.from({length:8},(_,i)=>'Villager'+String(i+1).padStart(2,'0'))]) {
    const png=fs.readFileSync(path.join(__dirname,'../static/sprites/'+key.toLowerCase()+'-idle.png'));
    assert.equal(png.readUInt32BE(16),612);assert.equal(png.readUInt32BE(20),612);
    for (let row=0;row<8;row++) for (const [mode,start] of [['idle',0],['walk',3],['gesture',6]]) for (let frame=0;frame<3;frame++) {
      clock=frame*180;
      assert.ok(renderer.character(ctx,key,100,100,{direction:directions[row],mode}));
      assert.equal(drawn[1],(start+frame)*68);assert.equal(drawn[2],(row+1)*68);
    }
  }
  const png=fs.readFileSync(path.join(__dirname,'../static/sprites/treasure-chest.png'));
  assert.equal(png.readUInt32BE(16),612);assert.equal(png.readUInt32BE(20),136);
  for(const opened of [false,true])for(let frame=0;frame<9;frame++) {
    clock=frame*160;
    assert.ok(renderer.chest(ctx,{x:100,y:100,opened}));
    assert.equal(drawn[1],frame*68);assert.equal(drawn[2],opened?68:0);
    assert.equal(drawn[6],66,'Chest destination stays fixed: bob is baked into frames');
  }
  console.log('All864 NPC/villager directional cells and18 floating chest frames passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
