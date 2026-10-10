// Flight art is separate from HUD icons. Every missile keeps its animation age across polls.
(() => {
  const root=document.currentScript?.dataset.spriteRoot || '/sprites/';
  const packs={},shots=new Map(),fields=new Map();let scene='';
  for(const key of ['missiles','spells','enemy']){const img=packs[key]=new Image();img.src=root+'flight-'+key+'-v1.png';}
  const rows={
    quick_arrow:['missiles',0,36,'tip','#e5d6ad'],snare_arrow:['missiles',1,39,'tip','#a3e985'],
    deadeye_arrow:['missiles',2,78,'tip','#ffe89b'],rain_arrow:['missiles',3,34,'tip','#e9ecdc'],
    radiant_flask:['missiles',4,23,'center','#ffd779'],sanctified_vial:['missiles',5,23,'center','#fff3c5'],
    briar_pod:['missiles',6,32,'tip','#a1e776'],thorn_spike:['missiles',7,32,'tip','#dded9a'],
    flying_dagger:['missiles',8,28,'tip','#d9c5fc'],
    arc_bolt:['spells',0,35,'tip','#b38cff'],frost_lance:['spells',1,40,'tip','#97edff'],
    quickstring_note:['spells',2,29,'tip','#ffc88e'],life_spark:['spells',3,27,'tip','#a4f5ec'],
    bird_lightning:['spells',4,38,'tip','#95ddff'],holy_bolt:['spells',5,29,'tip','#fff0a3'],
    fireball:['enemy',0,35,'tip','#ffae69'],ice_comet:['enemy',1,35,'tip','#b4edff'],
    dark_orb:['enemy',2,34,'tip','#bca0e9'],arcane_orb:['enemy',3,35,'tip','#d7a4ff'],
    storm_bolt:['enemy',4,36,'tip','#b4e7ff'],venom_glob:['enemy',5,30,'tip','#b6e57c'],
    nature_seed:['enemy',6,30,'tip','#b6e57c'],tumbling_rock:['enemy',7,35,'center','#bdad95']
  };
  const heroStyles={piercing_volley:'quick_arrow',snare_shot:'snare_arrow',deadeye:'deadeye_arrow',
    arc_burst:'arc_bolt',frost_lance:'frost_lance',radiant_flask:'radiant_flask',sanctified_throw:'sanctified_vial',
    briar_burst:'briar_pod',thornshot:'thorn_spike',quickstring:'quickstring_note',life_spark:'life_spark'};
  const affinityStyles={Fire:'fireball',Ice:'ice_comet',Dark:'dark_orb',Arcane:'arcane_orb',Storm:'storm_bolt',Poison:'venom_glob',Nature:'nature_seed'};
  const clamp=n=>Math.max(0,Math.min(1,n));
  function style(shot,room) {
    if(shot.effectKind==='rock')return 'tumbling_rock';
    if(shot.effectKind==='lightning')return 'bird_lightning';
    if(shot.side==='hero')return heroStyles[shot.abilityId] || ({Archer:'quick_arrow',Rogue:'flying_dagger',Knight:'flying_dagger',Cleric:'radiant_flask',Druid:'briar_pod',Bard:'quickstring_note',Healer:'life_spark'})[shot.class] || 'arc_bolt';
    if(shot.class==='Archer')return 'quick_arrow';
    if(['Rogue','Knight'].includes(shot.class) && shot.effectKind!=='boss_orb')return 'flying_dagger';
    const owner=room?.enemies?.find(e=>e.id===shot.ownerId);
    if(owner?.affinity && affinityStyles[owner.affinity])return affinityStyles[owner.affinity];
    const color=String(shot.color || '').toLowerCase();
    const known={'#f47745':'fireball','#85dcf2':'ice_comet','#79618e':'dark_orb','#bb83ff':'arcane_orb','#e9dd72':'storm_bolt','#92d64f':'venom_glob','#64c78d':'nature_seed'};
    return known[color] || (shot.class==='Healer'||shot.class==='Cleric'?'holy_bolt':'arcane_orb');
  }
  function observe(room) {
    const key=[room.code,room.stage].join(':');
    if(key!==scene || !['combat','chest','stage_exit','cleared'].includes(room.phase)){shots.clear();fields.clear();scene=key;}
    const now=performance.now(),live=new Set();
    for(const shot of room.projectiles || []){live.add(shot.id);if(!shots.has(shot.id))shots.set(shot.id,{at:now,style:style(shot,room)});}
    for(const id of shots.keys())if(!live.has(id))shots.delete(id);
    live.clear();
    for(const h of room.hazards || []){
      if(h.side!=='hero'||h.kind!=='arrow_rain')continue;
      live.add(h.id);const prior=fields.get(h.id);
      fields.set(h.id,{at:now,remaining:h.windupLeft,active:h.active,activated:h.active?(prior?.activated ?? now):null});
    }
    for(const id of fields.keys())if(!live.has(id))fields.delete(id);
  }
  function fallback(ctx,key,frame) {
    const r=rows[key],color=r[4],length=r[2];ctx.fillStyle=color;ctx.strokeStyle=color;
    if(key.includes('arrow')||key==='thorn_spike'||key==='briar_pod'||key==='flying_dagger'){
      ctx.lineWidth=key==='deadeye_arrow'?4:2;ctx.beginPath();ctx.moveTo(-length+7,0);ctx.lineTo(-5,0);ctx.stroke();
      const head=key==='deadeye_arrow'?10:5;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(-head,-head*.6);ctx.lineTo(-head,head*.6);ctx.closePath();ctx.fill();
      ctx.fillRect(-length+2,-3-frame%2,9,2);ctx.fillRect(-length+2,2+frame%2,9,2);
    }else if(key.includes('flask')||key.includes('vial')){
      ctx.rotate(frame*Math.PI/2);ctx.fillRect(-6,-7,12,15);ctx.fillRect(-2,-11,4,5);ctx.fillStyle='#fff5d8';ctx.fillRect(-4,-5,3,7);
    }else{
      ctx.beginPath();ctx.arc(-6,0,5+frame%2,0,Math.PI*2);ctx.fill();ctx.fillStyle='#fff5dd';ctx.fillRect(-8,-2,4,4);
      for(let i=0;i<5;i++){ctx.globalAlpha=.6-i*.1;ctx.fillStyle=color;ctx.fillRect(-13-i*4,Math.round(Math.sin(frame+i)*3),3,2);}
    }
  }
  function variant(ctx,key,x,y,angle=0,age=0,scale=1) {
    const r=rows[key];if(!r)return false;
    const speed=r[0]==='missiles'?110:80,frame=Math.floor(Math.max(0,age)/speed)%4,img=packs[r[0]];
    ctx.save();ctx.imageSmoothingEnabled=false;ctx.translate(x,y);ctx.rotate(angle);ctx.scale(scale,scale);
    const tip=r[3]==='tip',anchor=tip?78:48;
    if(img?.complete && img.naturalWidth)ctx.drawImage(img,frame*96,r[1]*96,96,96,-anchor,-48,96,96);
    else fallback(ctx,key,frame);
    ctx.restore();return true;
  }
  function draw(ctx,shot) {
    const record=shots.get(shot.id),key=record?.style || style(shot),r=rows[key];
    const age=performance.now()-(record?.at ?? performance.now()),angle=Math.atan2(shot.vy||0,shot.vx||1);
    const scale=shot.side==='enemy'?Math.min(1.7,Math.max(.8,(shot.radius||7)/10)):1;
    ctx.save();ctx.translate(shot.x,shot.y);ctx.rotate(angle);ctx.fillStyle=r[4];
    if(!key.includes('flask')&&!key.includes('vial')&&key!=='tumbling_rock') {
      const length=key==='deadeye_arrow'?80:r[2],magic=r[0]!=='missiles';
      for(let i=0;i<5;i++){
        const phase=(age/60+i*1.7)%5;ctx.globalAlpha=(1-phase/5)*.4;
        ctx.fillRect(Math.round(-length-7-phase*4),Math.round(Math.sin(age/70+i)*(magic?4:1)),magic?3:4,magic?3:1);
      }
    }
    ctx.restore();variant(ctx,key,shot.x,shot.y,angle,age,scale);return true;
  }
  function rain(ctx,room) {
    const now=performance.now();
    for(const h of room.hazards || []){
      if(h.side!=='hero'||h.kind!=='arrow_rain')continue;
      const record=fields.get(h.id),remaining=record?Math.max(0,record.remaining-(now-record.at)/1000):h.windupLeft;
      const age=h.active ? .65+(now-(record?.activated ?? now))/1000 : .65-remaining;
      ctx.save();
      for(let i=0;i<12;i++){
        const a=i*2.399963,r=Math.sqrt((i+.5)/12)*h.radius*.8,x=h.x+Math.cos(a)*r,y=h.y+Math.sin(a)*r;
        const launch=.23+i*.018,travel=(age-launch)/.42;
        if(travel>=0 && travel<1)variant(ctx,'rain_arrow',x,y-146+146*travel,Math.PI/2,now+i*45,1);
        else if(h.active && travel>=1 && travel<1.5){ctx.globalAlpha=1-clamp((travel-1)*2);ctx.fillStyle='#f3e6ba';ctx.fillRect(Math.round(x-3),Math.round(y),6,2);ctx.fillRect(Math.round(x),Math.round(y-3),2,5);}
      }
      ctx.restore();
    }
  }
  window.GauntletProjectiles={observe,draw,variant,rain,style};
})();
