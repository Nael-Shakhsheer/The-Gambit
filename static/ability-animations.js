// Shared cast choreography: relative server time, persistent cast IDs, native pixel art.
(() => {
  const sprites = {}, icons = {}, motions = new Map(), casts = new Map(), births = new Map();
  const spriteRoot = document.currentScript?.dataset.spriteRoot || '/sprites/';
  const heroes = ['Knight','Wizard','Archer','Cleric','Rogue','Druid','Bard','Healer'];
  const designs = {
    shield_bash:['Knight','shield','#f6d17d'], cleaving_arc:['Knight','slash','#f6d17d'],
    iron_wall:['Knight','ward','#c6e1ee'], challenge:['Knight','sound','#ffb85e'],
    guardian_cry:['Knight','ward','#ffe49a'], earthshaker:['Knight','earth','#e0ac70'],
    arc_burst:['Wizard','arcane','#b38cff'], frost_lance:['Wizard','ice','#97edff'],
    spell_surge:['Wizard','arcane','#b38cff'], blink:['Wizard','shadow','#b38cff'],
    team_aegis:['Wizard','ward','#b9beff'], arcane_cataclysm:['Wizard','arcane','#e09cff'],
    piercing_volley:['Archer','arrow','#dfed9a'], snare_shot:['Archer','vine','#95dc7f'],
    eagle_eye:['Archer','focus','#ffe79d'], quickstep:['Archer','wind','#bceea6'],
    rain_of_arrows:['Archer','rain','#ffe79d'], deadeye:['Archer','arrow','#fff3ad'],
    radiant_flask:['Cleric','flask','#ffd779'], sanctified_throw:['Cleric','flask','#fff3c5'],
    splash_mend:['Cleric','heal','#9af2b9'], blessed_vial:['Cleric','ward','#ffe4a0'],
    sanctuary_rain:['Cleric','rain','#ffedb5'], cleansing_splash:['Cleric','revive','#fff8d5'],
    backstab:['Rogue','slash','#c2a4ef'], fan_of_blades:['Rogue','blades','#d9c5fc'],
    vanish:['Rogue','shadow','#b587e7'], shadowstep:['Rogue','shadow','#d9b0ff'],
    death_bloom:['Rogue','blades','#f097dc'], execution:['Rogue','slash','#e6b2ff'],
    briar_burst:['Druid','vine','#a1e776'], thornshot:['Druid','vine','#dded9a'],
    lightning_bird:['Druid','lightning','#95ddff'], fire_wolf:['Druid','fire','#ffb365'],
    ice_bear:['Druid','ice','#bdefff'], nature_golem:['Druid','earth','#b1eb8c'],
    discord_note:['Bard','sound','#eb9bc9'], quickstring:['Bard','sound','#ffc88e'],
    battle_anthem:['Bard','sound','#ffb779'], fleet_rhythm:['Bard','wind','#aee9ec'],
    grand_crescendo:['Bard','sound','#ffd798'], rallying_chord:['Bard','heal','#edb9fa'],
    life_spark:['Healer','heal','#a4f5ec'], healing_ray:['Healer','heal','#c5ffea'],
    major_mend:['Healer','heal','#a4f5ec'], quick_revival:['Healer','revive','#d2fff5'],
    miracle:['Healer','heal','#e4fff9'], mass_revival:['Healer','revive','#fff7c6']
  };
  for (const hero of heroes) {
    const img = sprites[hero] = new Image();
    img.src = spriteRoot+hero.toLowerCase()+'-abilities-v1.png';
  }
  for (const id of Object.keys(designs)) {
    const img = icons[id] = new Image(); img.src = spriteRoot+'ability-'+id+'-v1.png';
  }
  let scene = '';
  const clamp = n => Math.max(0,Math.min(1,n));
  const castPhase = room => ['combat','chest','stage_exit','cleared'].includes(room.phase);
  const elapsed = record => record.elapsed+(performance.now()-record.at)/1000;
  const progress = record => clamp(elapsed(record)/record.duration);
  function observe(room) {
    const key = [room.code,room.you,room.stage].join(':');
    if (key !== scene || !castPhase(room)) {
      motions.clear(); casts.clear(); births.clear(); scene = key;
    }
    if (!castPhase(room)) return;
    const now = performance.now(), live = new Set();
    for (const p of room.players || []) {
      live.add(p.id);
      const cast = p.abilityAnimation;
      if (!cast || cast.stage !== room.stage || p.status !== 'alive' || cast.heroClass !== p.class) { motions.delete(p.id); continue; }
      const prior = motions.get(p.id);
      // Do not restart a pose on every multiplayer snapshot.
      if (cast.id !== prior?.id) motions.set(p.id,{...cast,at:now});
      else if (Math.abs(elapsed(prior)-cast.elapsed)>.2) { prior.elapsed=cast.elapsed; prior.at=now; }
    }
    for (const id of motions.keys()) if (!live.has(id)) motions.delete(id);
    live.clear();
    for (const e of room.effects || []) {
      if (e.type !== 'ability_cast' || e.stage !== room.stage) continue;
      live.add(e.id);
      if (!casts.has(e.id)) casts.set(e.id,{...e,elapsed:e.elapsed ?? Math.max(0,e.duration-(e.until*1000-Date.now())/1000),at:now});
    }
    for (const [id,c] of casts) if (!live.has(id) || elapsed(c)>=c.duration) casts.delete(id);
    live.clear();
    for (const s of room.summons || []) {
      live.add(s.id);
      if (s.emergeRemaining>0 && !births.has(s.id)) births.set(s.id,{duration:1.1,elapsed:1.1-s.emergeRemaining,at:now});
    }
    for (const [id,b] of births) if (!live.has(id) || elapsed(b)>=b.duration) births.delete(id);
  }
  function motion(p) {
    const r = motions.get(p.id);
    return p.status==='alive' && r?.heroClass===p.class && elapsed(r)<r.duration ? r : null;
  }
  function hero(ctx,p,x,y) {
    const r=motion(p), img=sprites[p.class];
    if (!r || !img?.complete || !img.naturalWidth) return false;
    const t=elapsed(r), step=t<.10?0:t<(r.attackType==='light'?.22:.32)?1:2;
    const group={light:0,special:1,ultimate:2}[r.attackType];
    const dir=(Math.round((Math.PI/2-Math.atan2(r.facingY ?? 1,r.facingX ?? 0))/(Math.PI/4))+8)%8;
    ctx.save(); ctx.imageSmoothingEnabled=false;
    // Export contains all eight directions, including deterministic mirrors.
    const sway=r.attackType==='ultimate' && t>.32 ? Math.round(Math.sin(t*32)) : 0;
    ctx.drawImage(img,(group*3+step)*96,dir*96,96,96,x-48+sway,y-72,96,96);
    ctx.restore(); return true;
  }
  function pixel(ctx,x,y,size,color) { ctx.fillStyle=color;ctx.fillRect(Math.round(x),Math.round(y),size,size); }
  function ring(ctx,x,y,r,color,alpha=1,spin=0) {
    ctx.save();ctx.globalAlpha*=alpha;ctx.strokeStyle=color;ctx.lineWidth=2;
    // Polygon edges and ticks retain the pixel style and don't fill danger zones.
    ctx.beginPath();
    for(let i=0;i<=24;i++) {const a=i*Math.PI/12+spin,px=Math.round(x+Math.cos(a)*r),py=Math.round(y+Math.sin(a)*r*.42);if(i)ctx.lineTo(px,py);else ctx.moveTo(px,py);}
    ctx.stroke();
    for(let i=0;i<8;i++){const a=i*Math.PI/4+spin;pixel(ctx,x+Math.cos(a)*r-2,y+Math.sin(a)*r*.42-2,4,color);}
    ctx.restore();
  }
  function glyph(ctx,id,x,y,size,angle=0) {
    const img=icons[id];if(!img?.complete || !img.naturalWidth)return;
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(x,y);ctx.rotate(angle);
    ctx.drawImage(img,-size/2,-size/2,size,size);ctx.restore();
  }
  function emitter(ctx,type,color,x,y,t,size=1,seed=0) {
    const fade=1-clamp(t);
    ctx.save();ctx.globalAlpha*=fade;
    for(let i=0;i<12;i++) {
      const a=i*Math.PI/6+seed*.17, r=(7+t*36)*size;
      const px=x+Math.cos(a)*r, py=y+Math.sin(a)*r*.6-t*25*size;
      if(type==='ice') {ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(Math.round(px),Math.round(py-6));ctx.lineTo(Math.round(px+3),Math.round(py));ctx.lineTo(Math.round(px),Math.round(py+3));ctx.lineTo(Math.round(px-3),Math.round(py));ctx.closePath();ctx.fill();}
      else if(type==='sound') {ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(px,py);ctx.lineTo(px,py-7);ctx.lineTo(px+4,py-5);ctx.stroke();pixel(ctx,px-3,py,4,color);}
      else if(type==='lightning') {ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(px-4,py-7);ctx.lineTo(px+2,py-2);ctx.lineTo(px-2,py+1);ctx.lineTo(px+4,py+6);ctx.stroke();}
      else {pixel(ctx,px,py,type==='earth'?5:type==='fire'?4:3,color);if(type==='heal'||type==='revive'){pixel(ctx,px-2,py+1,7,color);pixel(ctx,px+1,py-2,2,'#fffaf0');}}
    }
    ctx.restore();
  }
  function ground(ctx,p) {
    const r=motion(p);if(!r)return;
    const [,type,color]=designs[r.abilityId] || [p.class,'arcane',p.color], t=progress(r);
    ctx.save();
    if(r.kind==='summon') {
      const radius=r.attackType==='ultimate'?51:36;
      ring(ctx,p.x,p.y+17,radius*(.45+.55*Math.min(1,t*4)),color,1-t*.5,t*.8);
      ring(ctx,p.x,p.y+17,radius*.72,color,.6,-t*.8);
      for(let i=0;i<4;i++) {const a=i*Math.PI/2+t;glyph(ctx,r.abilityId,p.x+Math.cos(a)*radius*.7,p.y+17+Math.sin(a)*radius*.3,15);}
    } else if(r.attackType!=='light') ring(ctx,p.x,p.y+16,r.attackType==='ultimate'?43:28,color,.8*(1-t),t);
    if(r.attackType==='ultimate') ring(ctx,p.x,p.y+18,18+72*t,color,(1-t)*.7);
    ctx.restore();
  }
  function front(ctx,room) {
    if(!castPhase(room))return;
    for(const c of casts.values()) {
      const p=room.players?.find(p=>p.id===c.ownerId && p.class===c.heroClass);
      if(!p || p.status!=='alive' || p.connected===false || p.indoors)continue;
      const t=progress(c), [,type,color]=designs[c.abilityId] || [c.heroClass,'arcane','#c6dcff'];
      const isUlt=c.attackType==='ultimate', size=isUlt?1.8:c.attackType==='special'?1.1:.5;
      ctx.save();ctx.globalAlpha=(1-t)*.9;
      if(isUlt){ctx.shadowColor=color;ctx.shadowBlur=7;}
      const burst=clamp((elapsed(c)-.18)/(c.duration-.18));
      emitter(ctx,type,color,p.x,p.y-19,burst,size,c.id.charCodeAt(0));
      if(isUlt) {
        // Vertical ribbons erupt from the HERO, visible to every client.
        for(let i=0;i<9;i++) {
          const dx=(i-4)*10, h=(38+(i%3)*19)*Math.sin(Math.PI*Math.min(1,t*1.5));
          pixel(ctx,p.x+dx,p.y+12-h,3,h>0?color:'transparent');
          ctx.fillStyle=color;ctx.globalAlpha=(1-t)*.32;
          ctx.fillRect(Math.round(p.x+dx),Math.round(p.y+12-h),3,Math.max(0,Math.round(h)));
          ctx.globalAlpha=(1-t)*.9;
        }
        const textY=p.y-107-12*t;
        ctx.font='bold 11px monospace';ctx.textAlign='center';
        ctx.fillStyle='#101622';ctx.fillText(c.name.toUpperCase(),p.x+1,textY+1);
        ctx.fillStyle=color;ctx.fillText(c.name.toUpperCase(),p.x,textY);
      }
      if(type==='ward') {
        ctx.strokeStyle=color;ctx.lineWidth=isUlt?3:2;
        ctx.beginPath();ctx.moveTo(p.x-22,p.y-45);ctx.lineTo(p.x+22,p.y-45);ctx.lineTo(p.x+19,p.y-12);ctx.lineTo(p.x,p.y+4);ctx.lineTo(p.x-19,p.y-12);ctx.closePath();ctx.stroke();
      } else if(type==='wind'||type==='shadow') {
        ctx.strokeStyle=color;ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(c.x,c.y-8);ctx.lineTo(p.x,p.y-8);ctx.stroke();
      } else if(type==='blades') {
        for(let i=0;i<5;i++){const a=i*Math.PI*2/5+t*4;glyph(ctx,'backstab',p.x+Math.cos(a)*(26+t*40),p.y-15+Math.sin(a)*(16+t*20),22,a);}
      } else if(type==='rain' && c.abilityId==='rain_of_arrows') {
        if(t>.35)for(let i=0;i<7;i++){const phase=(t*3+i*.13)%1;glyph(ctx,'piercing_volley',c.targetX+(i-3)*14,c.targetY-70+phase*85,24,Math.PI/2);}
      } else if(type==='slash' && t<.7) {
        const a=Math.atan2(c.facingY,c.facingX),r=28+(isUlt?32:16)*t;
        ctx.strokeStyle=color;ctx.lineWidth=isUlt?5:3;ctx.beginPath();ctx.arc(p.x,p.y-7,r,a-.8,a+.8);ctx.stroke();
      }
      if(c.abilityId==='earthshaker') {
        glyph(ctx,c.abilityId,p.x+19,p.y-53+Math.min(1,t*4)*45,42);
        if(t>.2)ring(ctx,p.x,p.y+12,12+75*t,color,1-t);
      } else if(c.abilityId==='challenge' && t<.65) {
        glyph(ctx,c.abilityId,p.x+12,p.y-27,24);
      } else if(c.abilityId==='eagle_eye') {
        glyph(ctx,c.abilityId,p.x,p.y-63,28);
      } else if(c.abilityId==='frost_lance' && t<.4) {
        glyph(ctx,c.abilityId,p.x+20,p.y-26,26);
      } else if(c.abilityId==='sanctuary_rain') {
        for(let i=0;i<7;i++){const f=(t*2+i*.16)%1;pixel(ctx,p.x+(i-3)*14,p.y-65+f*83,3,color);}
      }
      if(c.kind==='team_heal'||c.kind==='team_ward'||c.kind==='team_damage'||c.kind==='team_speed'||c.kind==='revive'||c.kind==='team_revive') {
        // Follow the server's actual affected recipients (no false range or heal claims).
        for(const id of c.recipientIds || []) {
          if(id===p.id)continue;
          const ally=room.players?.find(a=>a.id===id);if(!ally || ally.indoors || ally.connected===false)continue;
          emitter(ctx,type,color,ally.x,ally.y-13,t,.5);
        }
      }
      ctx.restore();
    }
  }
  function projectile(ctx,shot) {
    const design=designs[shot.abilityId];
    if(!design || shot.side!=='hero' || shot.summonId)return false;
    const [,type,color]=design, img=icons[shot.abilityId];
    if(!img?.naturalWidth)return false;
    const big=shot.abilityId==='deadeye', angle=Math.atan2(shot.vy||0,shot.vx||1);
    ctx.save();ctx.imageSmoothingEnabled=false;
    // Literal ice shards, potion bottles, thorns, arrows and notes use their art.
    const size=big?48:type==='flask'?27:type==='sound'?22:28;
    for(let i=3;i>0;i--){ctx.globalAlpha=.12*(4-i);pixel(ctx,shot.x-Math.cos(angle)*i*7,shot.y-Math.sin(angle)*i*7,big?5:3,color);}
    ctx.globalAlpha=1;glyph(ctx,shot.abilityId,shot.x,shot.y,size,type==='flask'?performance.now()/160:angle);
    ctx.restore();return true;
  }
  function summonGround(ctx,s) {
    const b=births.get(s.id);if(!b)return;
    const t=progress(b);ring(ctx,s.x,s.y+14,s.kind==='golem'?46:s.kind==='bear'?39:27,s.color,1-t,t);
    emitter(ctx,s.affinity==='Fire'?'fire':s.affinity==='Ice'?'ice':s.kind==='bird'?'lightning':'earth',s.color,s.x,s.y+8,t,.8);
  }
  function summonScale(s) { const b=births.get(s.id);return b?.duration ? .35+.65*Math.min(1,progress(b)*2) : 1; }
  function summonFront(ctx,s) {
    if(s.animationUntil*1000<=Date.now())return;
    const t=clamp(1-(s.animationUntil*1000-Date.now())/300);
    const a=Math.atan2(s.facingY,s.facingX),x=s.x+Math.cos(a)*23,y=s.y-12+Math.sin(a)*16;
    emitter(ctx,s.kind==='bird'?'lightning':s.kind==='wolf'?'fire':s.kind==='bear'?'ice':'earth',s.color,x,y,t,.55);
  }
  function enemy(ctx,e,record) {
    const pending=e.bossAttack||e.roleAttack, age=performance.now()-(record?.released ?? -Infinity);
    const basic=clamp(1-(e.animationUntil*1000-Date.now())/450);
    if(!pending && age>550 && e.animationUntil*1000<=Date.now())return;
    const kind=pending?.kind || record?.kind || e.combatRole;
    const t=pending ? clamp((record?.progress || 0)+(performance.now()-(record?.at || performance.now()))/1000*(1-(record?.progress || 0))/Math.max(.01,record?.remaining || 1)) : age<550?clamp(age/550):basic;
    const a=Math.atan2(record?.facing?.facingY ?? e.facingY ?? 1,record?.facing?.facingX ?? e.facingX ?? 0);
    const type=kind==='support'?'heal':['charge','charger','ambusher'].includes(kind)?'wind':['slam','bruiser','draco_melee','rocks'].includes(kind)?'earth':e.affinity==='Fire'?'fire':e.affinity==='Ice'?'ice':e.affinity==='Storm'?'lightning':e.affinity==='Poison'?'vine':'arcane';
    const color=kind==='support'?'#a4efb5':e.color;
    ctx.save();ctx.globalAlpha=pending ? .7 : 1-t;
    const reach=e.kind==='dragon'?46:e.kind==='draco'?26:18;
    const x=e.x+Math.cos(a)*reach,y=e.y-(e.kind==='dragon'?53:19)+Math.sin(a)*reach*.65;
    if(pending) {
      const radius=4+t*13;
      ring(ctx,kind==='support'?e.x:x,kind==='support'?e.y+13:y,radius,color,.9,t);
      if(type==='wind'||type==='earth')ring(ctx,e.x,e.y+13,13+t*18,color,.6,t);
      // Breath/volley energy concentrates at the committed mouth/weapon facing.
      for(let i=0;i<6;i++){const b=i*Math.PI/3+performance.now()/180;pixel(ctx,x+Math.cos(b)*radius,y+Math.sin(b)*radius*.7,2+t*2,color);}
    } else emitter(ctx,type,color,x,y,t,e.boss?1.1:.6);
    ctx.restore();
  }
  window.GauntletAbilityAnimations={observe,hero,motion,ground,front,projectile,summonGround,summonScale,summonFront,enemy};
})();
