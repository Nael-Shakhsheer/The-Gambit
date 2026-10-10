// Gameplay overlays retain the imported regional scenery beneath them.
(() => {
  const art = {}, enemies = new Map(), cover = new Map(), traps = new Map(), hazards = new Map(), effectTimes = new Map(), tints = new Map();
  let scene = "";
  for (const key of ["terrain-effects", "hazard-effects", "impact-effects", "magic-effects", "projectile-effects",
    "objective-rift", "objective-ward", "puzzle-objects", "fork-signposts",
    ...["woodland", "ruins", "cavern", "frost"].map(x => "cover-"+x),
    ...["minotaur", "troll", "serpent", "wolf", "spider", "draco", "chimera"].flatMap(x => [x+"-windup", x+"-idle"]),
    "dragon-adult-idle", "dragon-adult-windup"]) {
    const image = art[key] = new Image();
    image.src = "/sprites/"+key+(key.startsWith("dragon-adult-") ? "-v2.png" : key.endsWith("-idle") ? ".png" : "-v1.png");
  }
  const clamp = value => Math.max(0, Math.min(1, value));
  function stamp(ctx,key,col,row,cell,x,y,w,h=w,color=null) {
    const image = art[key];
    if (!image?.complete || !image.naturalWidth) return false;
    ctx.save(); ctx.imageSmoothingEnabled = false;
    if (color) {
      const id = [key,col,row,color].join(":");
      let tile = tints.get(id);
      if (!tile) {
        tile = document.createElement("canvas"); tile.width = tile.height = cell;
        const g = tile.getContext("2d"); g.drawImage(image,col*cell,row*cell,cell,cell,0,0,cell,cell);
        g.globalCompositeOperation = "source-atop"; g.globalAlpha = .55; g.fillStyle = color; g.fillRect(0,0,cell,cell);
        if (tints.size > 512) tints.clear(); tints.set(id,tile);
      }
      ctx.drawImage(tile,x,y,w,h);
    } else ctx.drawImage(image,col*cell,row*cell,cell,cell,x,y,w,h);
    ctx.restore(); return true;
  }
  function observe(room) {
    const key = [room.code,room.stage].join(":");
    if (key !== scene) { enemies.clear(); cover.clear(); traps.clear(); hazards.clear(); effectTimes.clear(); scene = key; }
    const now = performance.now(), active = new Set();
    for (const e of room.enemies || []) {
      active.add(e.id);
      const a = e.bossAttack || e.roleAttack, previous = enemies.get(e.id);
      const signature = a ? a.kind+":"+a.startedAt : null;
      const facing = a ? {facingX:a.x-e.x,facingY:a.y-e.y} : null;
      const record = { ...previous, pending:signature, at:now, progress:a?.progress || 0, remaining:a?.remaining || 0 };
      if (a) {
        record.kind = a.kind;
        if (signature !== previous?.pending) record.facing = facing;
      } else if (previous?.pending) {
        // Stun cancellation has no recovery/charge: do not invent an attack release.
        record.released = e.charging || e.recovering ? now : -Infinity;
      }
      enemies.set(e.id,record);
    }
    for (const id of enemies.keys()) if (!active.has(id)) enemies.delete(id);
    active.clear();
    for (const o of room.environment?.obstacles || []) {
      active.add(o.id); const previous = cover.get(o.id);
      cover.set(o.id,{hp:o.hp,hit:o.hp < previous?.hp ? now : previous?.hit || -Infinity,
        broken:o.hp <= 0 && previous?.hp > 0 ? now : previous?.broken || -Infinity});
    }
    for (const id of cover.keys()) if (!active.has(id)) cover.delete(id);
    active.clear();
    for (const z of room.environment?.zones || []) {
      active.add(z.id); const previous = traps.get(z.id);
      traps.set(z.id,{readyAt:z.readyAt,warning:z.warning,warningLeft:z.warningLeft,at:now,
        fired:z.kind === "trap" && previous?.warning && !z.warning && z.readyAt > previous.readyAt ? now : previous?.fired || -Infinity});
    }
    for (const id of traps.keys()) if (!active.has(id)) traps.delete(id);
    active.clear();
    for (const h of room.hazards || []) {
      active.add(h.id); const previous = hazards.get(h.id);
      const ownerAttack = (room.enemies || []).find(e => e.id === h.ownerId)?.bossAttack;
      hazards.set(h.id,{active:h.active,at:now,remaining:h.windupLeft,
        duration:previous?.duration ?? (ownerAttack ? ownerAttack.releaseAt-ownerAttack.startedAt : Math.max(.01,h.windupLeft)),
        activated:h.active && !previous?.active ? now : previous?.activated ?? now});
    }
    for (const id of hazards.keys()) if (!active.has(id)) hazards.delete(id);
    active.clear();
    for (const e of room.effects || []) { active.add(e.id); if (!effectTimes.has(e.id)) effectTimes.set(e.id,{at:now,duration:Math.max(50,e.until*1000-Date.now())}); }
    for (const id of effectTimes.keys()) if (!active.has(id)) effectTimes.delete(id);
  }
  function enemy(ctx,e,x,y) {
    window.GauntletAbilityAnimations?.enemy(ctx,e,enemies.get(e.id));
    const a = e.bossAttack || e.roleAttack, record = enemies.get(e.id);
    const kind = e.kind === "monster" ? "chimera" : e.kind === "dragon" ? "dragon-adult" : e.kind;
    let column, key;
    const elapsed = performance.now()-(record?.released ?? -Infinity);
    if (a) {
      const progress = record?.pending ? clamp(record.progress+(performance.now()-record.at)/1000*(1-record.progress)/Math.max(.01,record.remaining)) : clamp(a.progress || 0);
      const group = ["charge","charger","ambusher"].includes(a.kind) ? 0 : ["slam","bruiser","breath","draco_melee"].includes(a.kind) ? 1 : 2;
      column = group*3+Math.min(2,Math.floor(progress*3)); key = kind+"-windup";
    } else if (e.charging || elapsed < 550 || e.animationUntil*1000 > Date.now()) {
      const releaseElapsed = elapsed < 550 ? elapsed : 450-(e.animationUntil*1000-Date.now());
      column = e.charging ? 6+Math.floor(performance.now()/110)%3 : 6+Math.max(0,Math.min(2,Math.floor(releaseElapsed/140))); key = kind+"-idle";
    } else if (e.kind === "draco") {
      column = (e.moving ? 3 : 0)+Math.floor(performance.now()/(e.moving ? 120 : 250))%3; key = "draco-idle";
    } else return false;
    const facing = a || e.charging || elapsed < 550 ? record?.facing || (a ? {facingX:a.x-e.x,facingY:a.y-e.y} : e) : e;
    const direction = (Math.round((Math.PI/2-Math.atan2(facing.facingY ?? 1,facing.facingX ?? 0))/(Math.PI/4))+8)%8;
    return e.kind === "dragon" ? stamp(ctx,key,column,direction+1,116,x-64,y-102,128) : stamp(ctx,key,column,direction+1,68,x-32,y-42,64);
  }
  function draw(ctx,room) {
    if (!room.environment) return;
    // Keep a complete fallback while the transparent atlases load.
    const region = ["woodland","ruins","cavern","frost"].includes(room.region) ? room.region : "woodland";
    if (!art["terrain-effects"]?.naturalWidth || !art["cover-"+region]?.naturalWidth) { drawFallback(ctx,room); return; }
    const now = performance.now(), frame = Math.floor(now/180)%4;
    ctx.save();
    for (const z of room.environment.zones || []) {
      const state = traps.get(z.id), fired = now-(state?.fired || -Infinity) < 320;
      const warningLeft = state ? Math.max(0,(state.warningLeft || 0)-(now-state.at)/1000) : z.warningLeft;
      const col = z.kind === "trap" ? fired ? 3 : z.warning ? warningLeft > .38 ? 1 : 2 : 0 : frame;
      const row = z.kind === "trap" ? 0 : z.kind === "poison" ? 1 : 2;
      ctx.save(); circle(ctx,z.x,z.y,z.radius); ctx.clip();
      stamp(ctx,"terrain-effects",col,row,128,z.x-z.radius*1.14,z.y-z.radius*1.14,z.radius*2.28);
      ctx.restore();
      ctx.strokeStyle = z.warning || fired ? "#ffb16b" : z.kind === "poison" ? "#b4da60" : z.kind === "ice" ? "#beeafa" : "#c9a674";
      ctx.lineWidth = z.warning ? 3 : 1; circle(ctx,z.x,z.y,z.radius); ctx.stroke();
      if (z.warning || fired) {
        ctx.fillStyle = "#101c24dd"; ctx.fillRect(z.x-40,z.y+z.radius+5,80,15);
        ctx.fillStyle = "#fff1c4"; ctx.font = "bold 10px monospace"; ctx.textAlign = "center";
        ctx.fillText(z.warning ? "TRAP · MOVE!" : "SPIKES!",z.x,z.y+z.radius+16);
      }
    }
    for (const o of room.environment.obstacles || []) {
      const state = cover.get(o.id), broken = o.hp <= 0, column = broken ? 2 : o.hp <= o.maxHp*.5 ? 1 : 0;
      ctx.save();
      if (!broken) { ctx.fillStyle = "#09161c77"; circle(ctx,o.x,o.y+8,26); ctx.fill(); }
      const shake = now-(state?.hit || -Infinity) < 150 && !broken ? Math.sin(now/15)*2 : 0;
      stamp(ctx,"cover-"+(o.iceWall ? 'frost' : region),column,o.kind === "rock" ? 1 : 0,64,o.x-32+shake,o.y-32,64);
      if (broken && now-(state?.broken || -Infinity) < 400) {
        const f = Math.min(3,Math.floor((now-state.broken)/100));
        stamp(ctx,"impact-effects",f,1,96,o.x-40,o.y-40,80);
      }
      if (!broken && o.hp<o.maxHp) {
        ctx.fillStyle = "#172630"; ctx.fillRect(o.x-22,o.y+27,44,5);
        ctx.fillStyle = "#e3c98b"; ctx.fillRect(o.x-21,o.y+28,42*o.hp/o.maxHp,3);
      }
      ctx.restore();
    }
    ctx.restore();
  }
  function projectile(ctx,shot) {
    const row = shot.effectKind === "rock" ? 1 : shot.effectKind === "lightning" ? 3 : shot.class === "Archer" ? 0 : ["Knight","Rogue"].includes(shot.class) && shot.effectKind !== "boss_orb" ? 4 : 2;
    const size = row === 1 || shot.effectKind === "boss_orb" ? (shot.radius || 15)*2.7 : row === 2 ? 28 : 36;
    ctx.save(); ctx.translate(shot.x,shot.y); ctx.rotate(Math.atan2(shot.vy || 0,shot.vx || 1));
    const drawn = stamp(ctx,"projectile-effects",Math.floor(performance.now()/90)%4,row,64,-size/2,-size/2,size,size,row === 2 ? shot.color : null);
    ctx.restore(); return drawn;
  }
  function effect(ctx,e) {
    const state = effectTimes.get(e.id), duration = state?.duration || 400;
    const progress = clamp(state ? (performance.now()-state.at)/duration : 1-(e.until*1000-Date.now())/400);
    const frame = Math.min(3,Math.floor(progress*4));
    const impactRows = {impact:0,burst:1,slash:2,enemy_attack:2,bleed:3,ambush:2,puzzle_solved:1};
    const magicRows = {heal:0,aura:1,cast:2,dash:3};
    const isMagic = e.type in magicRows, row = isMagic ? magicRows[e.type] : impactRows[e.type];
    if (row === undefined) return false;
    const directional = ["slash","enemy_attack","cast","dash","ambush"].includes(e.type);
    const x = directional ? e.targetX : e.x, y = directional ? e.targetY : e.y;
    const size = e.type === "burst" || e.type === "puzzle_solved" ? 96+progress*48 : e.type === "aura" ? 92 : 64;
    ctx.save(); ctx.globalAlpha = 1-progress*.65; ctx.translate(x,y);
    if (directional) ctx.rotate(Math.atan2(e.targetY-e.y,e.targetX-e.x));
    const drawn = stamp(ctx,isMagic ? "magic-effects" : "impact-effects",frame,row,96,-size/2,-size/2,size,size,["heal","bleed"].includes(e.type) ? null : e.color);
    ctx.restore(); return drawn;
  }
  function circle(ctx,x,y,r) { ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); }
  function drawFallback(ctx,room) {
    if (!room.environment) return;
    ctx.save();
    for (const z of room.environment.zones) {
      ctx.fillStyle = z.kind === "ice" ? "#bcefff55" : z.kind === "poison" ? "#679326a0" : "#342c26b0";
      ctx.strokeStyle = z.kind === "ice" ? "#beeafa" : z.kind === "poison" ? "#b4da60" : z.warning ? "#ff9b63" : "#c9a674";
      ctx.lineWidth = z.warning ? 4 : 2; circle(ctx,z.x,z.y,z.radius); ctx.fill(); ctx.stroke();
      if (z.kind === "ice") {
        ctx.strokeStyle = "#e4fcff80"; ctx.lineWidth = 2;
        for (let i=-2;i<=2;i++) { ctx.beginPath(); ctx.moveTo(z.x-50+i*10,z.y+i*20); ctx.lineTo(z.x+50+i*10,z.y+i*20-22); ctx.stroke(); }
      } else if (z.kind === "poison") {
        ctx.fillStyle = "#d6ed8a90";
        for (let i=0;i<5;i++) { circle(ctx,z.x+Math.cos(i*2)*28,z.y+Math.sin(i*2)*22,3+i%2); ctx.fill(); }
      } else {
        ctx.fillStyle = z.warning ? "#ffb66b" : "#8b7961";
        for (let i=-2;i<=2;i++) ctx.fillRect(z.x+i*10-2,z.y-11,4,22);
      }
      if (z.warning) {
        ctx.fillStyle = "#101c24dd"; ctx.fillRect(z.x-40,z.y+z.radius+5,80,15);
        ctx.fillStyle = "#fff1c4"; ctx.font = "bold 10px monospace"; ctx.textAlign = "center";
        ctx.fillText("TRAP · MOVE!",z.x,z.y+z.radius+16);
      }
    }
    for (const o of room.environment.obstacles) {
      if (o.hp <= 0) {
        ctx.fillStyle = "#b7a48d88";
        for (let i=0;i<5;i++) ctx.fillRect(o.x-18+i*8,o.y+(i%2)*7,6,4);
        continue;
      }
      ctx.fillStyle = "#09161c77"; circle(ctx,o.x,o.y+8,26); ctx.fill();
      if (o.kind === "crate") {
        ctx.fillStyle = "#67442e"; ctx.fillRect(o.x-23,o.y-24,46,46);
        ctx.fillStyle = "#bb8a50"; ctx.fillRect(o.x-20,o.y-24,40,39);
        ctx.strokeStyle = "#4a362a"; ctx.lineWidth = 5; ctx.strokeRect(o.x-21,o.y-23,42,40);
        ctx.beginPath(); ctx.moveTo(o.x-17,o.y-18); ctx.lineTo(o.x+17,o.y+11); ctx.stroke();
        ctx.fillStyle = "#e4b574"; ctx.fillRect(o.x-18,o.y-21,36,3);
      } else {
        ctx.fillStyle = "#596e75"; ctx.beginPath(); ctx.moveTo(o.x-25,o.y+15); ctx.lineTo(o.x-17,o.y-19); ctx.lineTo(o.x+12,o.y-25); ctx.lineTo(o.x+25,o.y+2); ctx.lineTo(o.x+18,o.y+20); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#95a9aa"; ctx.beginPath(); ctx.moveTo(o.x-17,o.y-19); ctx.lineTo(o.x+12,o.y-25); ctx.lineTo(o.x+5,o.y-4); ctx.lineTo(o.x-20,o.y+5); ctx.closePath(); ctx.fill();
      }
      ctx.fillStyle = "#172630"; ctx.fillRect(o.x-22,o.y+27,44,5);
      ctx.fillStyle = "#e3c98b"; ctx.fillRect(o.x-21,o.y+28,42*o.hp/o.maxHp,3);
    }
    ctx.restore();
  }
  function warnings(ctx,room) {
    ctx.save();
    const labelled = new Set();
    for (const h of room.hazards || []) {
      ctx.save(); circle(ctx,h.x,h.y,h.radius); ctx.clip();
      const state = hazards.get(h.id), now = performance.now(), activated = state?.activated ?? now;
      const progress = state ? clamp(1-Math.max(0,state.remaining-(now-state.at)/1000)/state.duration) : 0;
      const frame = !h.active ? Math.min(2,Math.floor(progress*3)) : h.kind !== "pool" ? Math.min(3,Math.floor((now-activated)/60)) : Math.floor(now/120)%4;
      const row = !h.active ? 0 : h.kind === "slam" ? 1 : h.kind === "meteor" ? 2 : 3;
      if (h.side !== 'hero') stamp(ctx,"hazard-effects",frame,row,128,h.x-h.radius*1.14,h.y-h.radius*1.14,h.radius*2.28,h.radius*2.28,row === 3 ? h.color : null);
      else if (h.active && !window.GauntletProjectiles) {
        ctx.strokeStyle='#ffe7ab';ctx.lineWidth=3;
        for(let i=0;i<12;i++){const x=h.x+Math.cos(i*2.4)*h.radius*.7,y=h.y+Math.sin(i*2.4)*h.radius*.7;ctx.beginPath();ctx.moveTo(x-4,y-12);ctx.lineTo(x,y+3);ctx.lineTo(x+4,y-4);ctx.stroke();}
      }
      ctx.restore();
      ctx.fillStyle = h.side==='hero' ? '#8ddcff22' : h.active ? "#ff684c66" : "#ffd16b33";
      ctx.strokeStyle = h.side==='hero' ? '#9de3ff' : h.active ? "#ff8d66" : "#ffdb86"; ctx.lineWidth = 3;
      ctx.setLineDash(h.active ? [] : [8,5]); circle(ctx,h.x,h.y,h.radius); ctx.fill(); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = "#fff0c8"; ctx.textAlign = "center"; ctx.font = "bold 11px monospace";
      if (!h.signatureToken || !labelled.has(h.signatureToken)) {
        ctx.fillText((h.side==='hero' ? 'ARROWS' : h.label || h.kind.toUpperCase())+(h.active ? h.side==='hero' ? ' · STRIKE' : ' · DANGER' : ' · '+h.windupLeft.toFixed(1)+'s'),h.x,h.y);
        if (h.signatureToken) labelled.add(h.signatureToken);
      }
    }
    for (const e of room.enemies || []) {
      if(e.rooted){ctx.strokeStyle='#92d26d';ctx.lineWidth=3;circle(ctx,e.x,e.y+15,23);ctx.stroke();}
      if(e.bleeding){ctx.fillStyle='#da6b80';for(let i=0;i<3;i++)ctx.fillRect(e.x-10+i*10,e.y+24,3,5);}
      const a = e.bossAttack || e.roleAttack;
      ctx.textAlign = "center"; ctx.font = "bold 10px monospace";
      const labelY = e.y+(e.boss ? 86 : e.miniBoss ? 68 : 56);
      if (!a) {
        ctx.fillStyle = e.recovering && !e.charging ? "#a8edb1" : "#fff0c8";
        const label = e.vulnerable ? 'OPENING +35%' : e.recovering && !e.charging && (e.boss || e.miniBoss || room.objective?.kind==='charge') ? "RECOVERING" : null;
        if (label) { ctx.fillStyle = "#14212cdd"; ctx.fillRect(e.x-43,labelY-10,86,14); ctx.fillStyle = e.recovering ? "#a8edb1" : "#fff0c8"; ctx.fillText(label,e.x,labelY); }
        continue;
      }
      const dash = ["charge","charger","ambusher"].includes(a.kind);
      ctx.strokeStyle = a.ally ? "#aceda8" : "#ffca78";
      if (dash) {
        const angle = Math.atan2(a.y-e.y,a.x-e.x), reach = a.kind === "charger" ? 148.5 : 77;
        const x = a.endX ?? e.x+Math.cos(angle)*reach, y = a.endY ?? e.y+Math.sin(angle)*reach;
        ctx.globalAlpha = .25; ctx.lineWidth = a.kind === "charge" ? 84 : 56;
        ctx.beginPath(); ctx.moveTo(e.x,e.y); ctx.lineTo(x,y); ctx.stroke();
        ctx.globalAlpha = 1; ctx.lineWidth = 3; ctx.setLineDash([8,5]); ctx.stroke(); ctx.setLineDash([]);
      } else if (["rocks","volley","breath","ranged","support","draco_projectile"].includes(a.kind) && !a.ally) {
        const angle = Math.atan2(a.y-e.y,a.x-e.x), count = a.kind === "breath" ? 5 : ["rocks","volley"].includes(a.kind) ? 3 : 1;
        ctx.globalAlpha = .5; ctx.lineWidth = 2; ctx.setLineDash([6,6]);
        for (let i=0;i<count;i++) { const direction=angle+(i-(count-1)/2)*.23; ctx.beginPath(); ctx.moveTo(e.x,e.y); ctx.lineTo(e.x+Math.cos(direction)*310,e.y+Math.sin(direction)*310); ctx.stroke(); }
        ctx.setLineDash([]); ctx.globalAlpha = 1;
      } else if (["bruiser","draco_melee"].includes(a.kind)) {
        ctx.fillStyle = "#ffb46633"; circle(ctx,e.x,e.y,a.kind === "draco_melee" ? 55 : 70); ctx.fill(); ctx.lineWidth = 2; ctx.stroke();
      }
      ctx.fillStyle = "#14212cee"; ctx.fillRect(e.x-63,labelY-12,126,23);
      ctx.fillStyle = a.ally ? "#aceda8" : "#ffe389";
      const time = Number.isFinite(a.remaining) ? a.remaining.toFixed(1)+"s" : "WIND-UP";
      const attackName = a.kind === "draco_projectile" ? "SHOT" : a.kind === "draco_melee" ? "BITE" : a.kind.toUpperCase();
      ctx.fillText((a.ally ? "HEAL" : attackName)+" · "+time,e.x,labelY-1);
      ctx.fillStyle = "#53616a"; ctx.fillRect(e.x-47,labelY+4,94,3);
      ctx.fillStyle = "#ffca78"; ctx.fillRect(e.x-47,labelY+4,94*(a.progress || 0),3);
    }
    ctx.restore();
  }
  function target(ctx,x,y,r=28) {
    ctx.save();ctx.strokeStyle='#ffd36b';ctx.lineWidth=3;circle(ctx,x,y+12,r);ctx.stroke();
    ctx.fillStyle='#ffd36b';ctx.beginPath();ctx.moveTo(x-6,y-62);ctx.lineTo(x+6,y-62);ctx.lineTo(x,y-54);ctx.closePath();ctx.fill();ctx.restore();
  }
  function structure(ctx,e,selected=false,friendly=false,region='woodland') {
    ctx.save();if(selected) target(ctx,e.x,e.y,34);
    ctx.fillStyle='#15211a99';circle(ctx,e.x,e.y+12,30);ctx.fill();
    const destroyed=e.hp<=0, damaged=e.hp<=e.maxHp*.5;
    const frame=destroyed ? 3 : Math.floor(performance.now()/180)%4;
    const drawn=stamp(ctx,friendly?'objective-ward':'objective-rift',frame,destroyed&&friendly?2:damaged?1:0,96,e.x-48,e.y-68,96);
    if(!drawn) {
      if(!stamp(ctx,'cover-'+region,0,1,64,e.x-32,e.y-38,64)) {
        ctx.fillStyle='#59655a';ctx.fillRect(e.x-24,e.y-38,48,48);ctx.fillStyle='#929785';ctx.fillRect(e.x-21,e.y-36,42,6);
      }
      ctx.fillStyle=friendly?'#b5e1a8':'#c5a4e0';ctx.fillRect(e.x-3,e.y-26,6,23);ctx.fillRect(e.x-9,e.y-19,18,4);
    }
    const barY=e.y-(drawn?72:51);
    ctx.fillStyle='#16271f';ctx.fillRect(e.x-30,barY,60,6);ctx.fillStyle=friendly?'#8ec995':'#d88c83';ctx.fillRect(e.x-29,barY+1,58*clamp(e.hp/Math.max(1,e.maxHp)),4);ctx.restore();
  }
  function puzzleObject(ctx,sigil,x,y,totem=false) {
    if (sigil === 'STAR') {
      // Draw the five-point sigil directly so both the rune and clue agree.
      ctx.save(); ctx.translate(Math.round(x),Math.round(y));
      ctx.fillStyle='#17171e'; ctx.fillRect(totem?-24:-38,totem?-37:-24,totem?48:76,totem?73:46);
      ctx.fillStyle='#363640'; ctx.strokeStyle='#696071'; ctx.lineWidth=3;
      ctx.beginPath();
      const frame=totem?[[-19,-31],[19,-31],[19,30],[-19,30]]:[[-30,-23],[30,-23],[37,18],[-37,18]];
      frame.forEach(([px,py],i)=>i?ctx.lineTo(px,py):ctx.moveTo(px,py));ctx.closePath();ctx.fill();ctx.stroke();
      ctx.fillStyle='#24252f';
      ctx.fillRect(totem?-14:-24,totem?-23:-18,totem?28:48,totem?48:30);
      ctx.fillStyle='#a97b34';
      for(const [px,py] of frame) { ctx.fillRect(px-4,py-3,8,6);ctx.fillStyle='#e0b45d';ctx.fillRect(px-3,py-3,6,2);ctx.fillStyle='#a97b34'; }
      const cy=totem?0:-4, outer=totem?14:19, inner=outer*.44;
      ctx.beginPath();
      for(let i=0;i<10;i++) {
        const angle=-Math.PI/2+i*Math.PI/5, radius=i%2?inner:outer;
        const px=Math.round(Math.cos(angle)*radius),py=Math.round(cy+Math.sin(angle)*radius);
        if(i)ctx.lineTo(px,py);else ctx.moveTo(px,py);
      }
      ctx.closePath();ctx.fillStyle='#eee6da';ctx.strokeStyle='#b7a9a0';ctx.lineWidth=1;ctx.fill();ctx.stroke();
      ctx.restore();return true;
    }
    const index=['SUN','MOON','LEAF','FLAME','WAVE','STAR'].indexOf(sigil);
    return stamp(ctx,'puzzle-objects',index<0?6:index,totem?1:0,96,x-48,y-48,96);
  }
  function signpost(ctx,room) {
    const index=Math.max(0,['woodland','ruins','cavern','frost'].indexOf(room.region));
    return stamp(ctx,'fork-signposts',index%2,Math.floor(index/2),128,352,44,256);
  }
  function objectives(ctx,room) { if(room.objective?.ward) structure(ctx,room.objective.ward,false,true,room.region); }
  window.GauntletCombatEnvironment = {draw,warnings,observe,enemy,projectile,effect,target,structure,objectives,puzzleObject,signpost};
})();
