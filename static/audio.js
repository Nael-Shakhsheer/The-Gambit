/* Confirmed snapshot feedback; no sound changes gameplay or sends an action. */
(() => {
  'use strict';
  const NAMES = ['blade','bow','magic','potion','bard','special','ultimate','dash','hit','hurt','heal','loot','select','interact','down','revive','clear','warning','impact','curse'];
  const LIGHT = {Knight:'blade',Rogue:'blade',Archer:'bow',Wizard:'magic',Druid:'magic',Cleric:'potion',Bard:'bard',Healer:'heal'};
  const clamp = (n, low, high) => Math.max(low, Math.min(high, n));
  let volume=.45, muted=false;
  try {
    const saved=JSON.parse(localStorage.getItem('gauntlet-audio') || 'null');
    if (saved && Number.isFinite(saved.volume)) volume=clamp(saved.volume,0,1);
    muted=saved?.muted === true;
  } catch {}
  let context=null, master=null, loading=null, loadFailures=0;
  const buffers=new Map(), active=new Map(), lastPlay=new Map();
  let previous=null, previousAt=0, scene='', seen=new Set(), baseline=true;
  function status() {
    return !window.AudioContext && !window.webkitAudioContext ? 'Audio unavailable in this browser.' :
      muted ? 'Sound muted.' : volume===0 ? 'Volume is zero.' :
      !context || context.state!=='running' ? 'Click, tap or press a key to activate sound.' :
      loading ? 'Loading sounds…' : loadFailures ? 'Some sounds could not load. Refresh to retry.' : 'Sound ready.';
  }
  function updateControls() {
    document.querySelectorAll('[data-audio-volume]').forEach(e=>{e.value=String(Math.round(volume*100));});
    document.querySelectorAll('[data-audio-value]').forEach(e=>{e.textContent=Math.round(volume*100)+'%';});
    document.querySelectorAll('[data-audio-mute]').forEach(e=>{e.checked=muted;});
    document.querySelectorAll('[data-audio-status]').forEach(e=>{e.textContent=status();});
  }
  function applySettings() {
    if(master) master.gain.setTargetAtTime(muted ? 0 : volume,context.currentTime,.015);
    try { localStorage.setItem('gauntlet-audio',JSON.stringify({volume,muted})); } catch {}
    updateControls();
  }
  async function unlock() {
    if (document.hidden) return;
    try {
      const Ctor=window.AudioContext || window.webkitAudioContext;
      if (!Ctor) {updateControls();return;}
      if(!context) {
        context=new Ctor(); master=context.createGain();
        // A compressor and bounded voices keep simultaneous party effects controlled.
        const limiter=context.createDynamicsCompressor();
        limiter.threshold.value=-12; limiter.knee.value=6; limiter.ratio.value=12;
        master.connect(limiter); limiter.connect(context.destination);
        master.gain.value=muted ? 0 : volume;
        context.onstatechange=updateControls;
      }
      if(context.state!=='running') await context.resume();
      if(!loading && !buffers.size && !loadFailures) {
        loading=Promise.all(NAMES.map(async name=>{
          try {
            const response=await fetch('audio/'+name+'.wav');
            if(!response.ok) throw Error('Missing sound');
            const buffer=await context.decodeAudioData(await response.arrayBuffer());
            buffers.set(name,buffer);
          } catch {loadFailures++;}
        }));
        updateControls();
      }
      if(loading) {await loading;loading=null;}
    } catch { /* Autoplay rejection never interrupts the game. Another gesture retries. */ }
    updateControls();
  }
  function stopAll() {
    for(const source of active.keys()) {try{source.stop();}catch{}}
    active.clear();
  }
  function play(name,{gain=.5,x,y,local=false,priority=0}={}) {
    if(muted || !volume || document.hidden || !context || context.state!=='running' || !buffers.has(name)) return false;
    const now=performance.now(), interval=['hit','impact','heal'].includes(name) ? 100 : name==='select' ? 70 : 65;
    if(now-(lastPlay.get(name) ?? -Infinity)<interval) return false;
    const listener=previous?.players?.find(p=>p.id===previous.you);
    let pan=0;
    if(!local && listener && Number.isFinite(x) && Number.isFinite(y)) {
      const distance=Math.hypot(x-listener.x,y-listener.y);
      gain*=clamp(1-distance/1000,.15,1); pan=clamp((x-listener.x)/480,-.7,.7);
    }
    if(active.size>=10) {
      const victim=[...active].find(([,p])=>p<priority);
      if(!victim) return false;
      try{victim[0].stop();}catch{} active.delete(victim[0]);
    }
    const source=context.createBufferSource(), level=context.createGain();
    source.buffer=buffers.get(name); level.gain.value=clamp(gain,0,1);
    source.connect(level);
    let panner=null;
    if(context.createStereoPanner) {panner=context.createStereoPanner();panner.pan.value=pan;level.connect(panner);panner.connect(master);}
    else level.connect(master);
    active.set(source,priority); lastPlay.set(name,now);
    source.onended=()=>{active.delete(source);source.disconnect();level.disconnect();panner?.disconnect();};
    source.start(); return true;
  }
  function reset() {previous=null;previousAt=0;scene='';seen.clear();baseline=true;stopAll();lastPlay.clear();}
  function observe(room) {
    const now=performance.now(), nextScene=[room.code,room.you,room.stage].join(':');
    const initialize=baseline || !previous || scene!==nextScene || now-previousAt>750 || document.hidden;
    const old=previous;
    previous=room;previousAt=now;scene=nextScene;baseline=false;
    const effects=room.effects || [];
    if(initialize) {
      seen=new Set(effects.map(e=>e.id));
      return;
    }
    if(old.phase!==room.phase) {
      if(room.phase==='cleared') play('clear',{gain:.8,priority:3});
      else if(room.phase==='defeat') play('down',{gain:.7,priority:3});
      else if(['chest','stage_exit'].includes(room.phase) && old.phase==='combat') play('clear',{gain:.55,priority:2});
    }
    const sameCombat=room.phase==='combat' && old.phase==='combat';
    for(const player of room.players || []) {
      const prior=old.players?.find(p=>p.id===player.id);
      if(!prior || prior.class!==player.class) continue;
      const local=player.id===room.you, options={x:player.x,y:player.y,local,gain:local ? .65 : .35,priority:local?2:1};
      if(sameCombat && player.status==='alive' && player.animationUntil>prior.animationUntil) {
        const cue=player.animation==='ultimate'?'ultimate':player.animation==='special'?'special':LIGHT[player.class] || 'magic';
        play(cue,options);
      }
      if(sameCombat && (player.damageTaken>prior.damageTaken || player.hp<prior.hp)) play(local?'hurt':'hit',options);
      if(player.status!==prior.status) {
        if(player.status==='downed' || player.status==='fallen') play('down',options);
        else if(player.status==='alive' && sameCombat) play('revive',options);
      }
    }
    if(sameCombat) {
      for(const enemy of room.enemies || []) {
        const prior=old.enemies?.find(e=>e.id===enemy.id);
        if(prior && (enemy.damageTaken>prior.damageTaken || enemy.hp<prior.hp)) play('hit',{x:enemy.x,y:enemy.y,gain:.32});
        if(prior && enemy.bossPhase>prior.bossPhase) play('warning',{gain:.65,priority:3});
      }
    }
    for(const effect of effects) {
      if(seen.has(effect.id)) continue;
      seen.add(effect.id);
      const cues={dash:'dash',heal:'heal',impact:'impact',puzzle_solved:'clear',ambush:'warning',enemy_attack:LIGHT[effect.class] || 'blade'};
      const cue=cues[effect.type];
      if(cue && (room.phase==='combat' || ['heal','puzzle_solved'].includes(effect.type))) play(cue,{x:effect.x,y:effect.y,gain:effect.type==='enemy_attack'?.22:.4,priority:effect.type==='dash'?1:0});
    }
    // Keep expired IDs for a short overlap window while bounding long-run memory.
    if(seen.size>256) seen=new Set(effects.map(e=>e.id));
    if(room.chest?.opened && !old.chest?.opened && old.phase==='chest') play(room.curse && !old.curse?'curse':'loot',{gain:.7,local:true,priority:2});
    if(room.privateNotice && room.privateNotice!==old.privateNotice && /^(Chest (opened|loot|loot claimed):|Rune cache:|Restoration chest:|CURSED:)/.test(room.privateNotice)) play(room.privateNotice.startsWith('CURSED:')?'curse':'loot',{gain:.7,local:true,priority:2});
    if((room.townInteraction!==old.townInteraction && room.townInteraction) || room.townInterior!==old.townInterior || room.innFloor!==old.innFloor) play('interact',{gain:.4,local:true});
    if(room.privateNotice && room.privateNotice!==old.privateNotice && /checkpoint.*saved|checkpoint set|rest.*bed/i.test(room.privateNotice)) play('heal',{gain:.6,local:true,priority:2});
  }
  window.GauntletAudio={observe,reset,unlock,play};
  document.addEventListener('pointerdown',unlock,{capture:true,passive:true});
  document.addEventListener('keydown',e=>{if(!e.repeat) unlock();},{capture:true});
  document.addEventListener('visibilitychange',()=>{if(document.hidden){baseline=true;stopAll();}});
  window.addEventListener('blur',()=>{baseline=true;stopAll();});
  document.addEventListener('input',e=>{
    if(e.target.matches('[data-audio-volume]')) {volume=clamp(Number(e.target.value)/100,0,1);applySettings();}
    if(e.target.matches('[data-audio-mute]')) {muted=e.target.checked;applySettings();if(muted)stopAll();}
  });
  document.addEventListener('click',async e=>{
    if(e.target.closest('[data-audio-open]')) window.openInfo?.('audioDialog');
    if(e.target.closest('[data-audio-test]')) {await unlock();play('loot',{gain:.65,local:true,priority:3});}
    else if(e.target.closest('button') && !e.target.closest('#attackButton,#dashButton,#reviveButton,[data-audio-open]')) play('select',{gain:.2,local:true});
  });
  updateControls();
})();
