/* Rebuild the shipped Bfxr bank with Node's standard library only. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '../..');
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'sounds.json')));
const output = path.join(root, 'static/audio');
fs.mkdirSync(output, { recursive: true });
const sandbox = vm.createContext({ console });
vm.runInContext(`const SAMPLE_RATE=44100, CONVERSION_FACTOR=2*Math.PI/44100;
const TEMPLATES_JSON={}; const AUDIO_CONTEXT={createBuffer(c,n,r){
  const data=new Float32Array(n); return {getChannelData(){return data;},copyToChannel(src){data.set(src);}};
}}; function ULBS(){};`, sandbox);
for (const file of ['globals.js','Bfxr_DSP.js','RealizedSound.js','SynthBase.js','Bfxr.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'vendor', file), 'utf8'), sandbox, { filename: file });
}
const metrics = {};
for (const [name, recipe] of Object.entries(manifest.sounds)) {
  sandbox.recipe = recipe;
  const samples = vm.runInContext(`(() => {
    let seed=recipe.seed;
    Math.random=()=>{seed|=0; seed=seed+0x6D2B79F5|0;
      let t=Math.imul(seed^seed>>>15,1|seed); t=t+Math.imul(t^t>>>7,61|t)^t;
      return ((t^t>>>14)>>>0)/4294967296;};
    const synth=new Bfxr(); synth.apply_params(recipe.params); synth.generate_sound();
    return synth.sound.getBuffer();
  })()`, sandbox);
  // Bound level, trim long silence, and ramp edges to avoid playback clicks.
  let end = samples.length;
  while (end > 441 && Math.abs(samples[end - 1]) < .0001) end--;
  let peak = 0;
  for (let i=0;i<end;i++) {
    if (!Number.isFinite(samples[i])) throw Error(name + ': invalid sample');
    peak = Math.max(peak, Math.abs(samples[i]));
  }
  if (!peak || end > 44100 * 2) throw Error(name + ': invalid length or silent sound');
  const gain = .65 / peak;
  const wav = Buffer.alloc(44 + end * 2);
  wav.write('RIFF'); wav.writeUInt32LE(wav.length-8,4); wav.write('WAVEfmt ',8);
  wav.writeUInt32LE(16,16); wav.writeUInt16LE(1,20); wav.writeUInt16LE(1,22);
  wav.writeUInt32LE(44100,24); wav.writeUInt32LE(88200,28);
  wav.writeUInt16LE(2,32); wav.writeUInt16LE(16,34); wav.write('data',36);
  wav.writeUInt32LE(end*2,40);
  let sum=0;
  for(let i=0;i<end;i++) {
    const value=samples[i]*gain*Math.min(1,i/88,(end-1-i)/176);
    sum+=value*value; wav.writeInt16LE(Math.round(value*32767),44+i*2);
  }
  fs.writeFileSync(path.join(output, name+'.wav'),wav);
  metrics[name]={seconds: +(end/44100).toFixed(3), rms: +Math.sqrt(sum/end).toFixed(4), bytes:wav.length};
}
fs.writeFileSync(path.join(__dirname,'metrics.json'), JSON.stringify(metrics,null,2)+'\n');
console.log('Built '+Object.keys(metrics).length+' Bfxr sounds.');
