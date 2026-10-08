// Predict only the local hero. The server still decides every hit and collision.
(() => {
  const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
  const paths = [[[480,540],[480,320],[260,170],[0,170]], [[480,540],[480,320],[700,170],[960,170]]];
  function walkable(room,x,y) {
    if (room.phase === 'routes') return paths.some(path => path.slice(1).some((b,i) => {
      const a=path[i], dx=b[0]-a[0], dy=b[1]-a[1];
      const t=clamp(((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy),0,1);
      return Math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)<=54;
    }));
    if (room.phase === 'town') {
      if (!room.townInterior) return !(room.townHouses || []).some(h => Math.abs(x-h.x)<69 && y>h.y-78 && y<h.y+35);
      return room.innFloor !== 2 || y>=340 || (room.innRooms || []).some(r => !r.locked && Math.abs(x-r.x)<(y>=310?25:68) && y>=130);
    }
    return !(room.environment?.obstacles || []).some(o => o.hp>0 && Math.hypot(x-o.x,y-o.y)<o.radius+12);
  }
  function move(room,p,dx,dy,speed,dt) {
    const interior=room.phase==='town' && room.townInterior;
    const cover=['combat','chest','stage_exit'].includes(room.phase);
    if (cover) for (const o of room.environment?.obstacles || []) {
      if (o.hp<=0) continue;
      const ox=p.x-o.x, oy=p.y-o.y, distance=Math.hypot(ox,oy);
      if (distance<o.radius+12) { p.x=o.x+(distance?ox/distance:1)*(o.radius+13); p.y=o.y+(distance?oy/distance:0)*(o.radius+13); }
    }
    let vx=dx*speed,vy=dy*speed;
    if (room.phase==='combat' && (room.environment?.zones || []).some(z=>z.kind==='ice' && Math.hypot(p.x-z.x,p.y-z.y)<z.radius)) {
      const blend=Math.min(1,dt*3.5);
      vx=p.slideVx+(vx-p.slideVx)*blend; vy=p.slideVy+(vy-p.slideVy)*blend;
    }
    p.slideVx=vx; p.slideVy=vy;
    const steps=cover?Math.max(1,Math.ceil(Math.hypot(vx,vy)*dt/8)):1;
    for (let i=0;i<steps;i++) {
      const x=clamp(p.x+vx*dt/steps,interior?180:28,interior?780:932);
      const y=clamp(p.y+vy*dt/steps,interior?100:30,interior?476:510);
      if (walkable(room,x,p.y)) p.x=x;
      if (walkable(room,p.x,y)) p.y=y;
    }
    return p;
  }
  function create() {
    let anchor=null, scene='', history=[], correction={x:0,y:0,start:0};
    function remember(input,now) {
      const length=Math.max(1,Math.hypot(input.x,input.y));
      const direction={x:input.x/length,y:input.y/length};
      const previous=history.at(-1);
      if (!previous || previous.x!==direction.x || previous.y!==direction.y) history.push({at:now,...direction});
      while(history.length>1 && history[1].at<now-2000) history.shift();
    }
    function predicted(room,now) {
      if (!anchor) return null;
      const p={...anchor};
      const end=Math.min(now,anchor.received+250);
      let direction={x:0,y:0}, index=0;
      while(index<history.length && history[index].at<=anchor.at) direction=history[index++];
      for(let t=anchor.at;t<end;) {
        while(index<history.length && history[index].at<=t) direction=history[index++];
        const next=Math.min(end,t+50,history[index]?.at ?? Infinity);
        move(room,p,direction.x,direction.y,anchor.speed,(next-t)/1000); t=next;
      }
      return p;
    }
    function position(room,now) {
      const p=predicted(room,now); if(!p) return null;
      const weight=clamp(1-(now-correction.start)/100,0,1);
      return {x:p.x+correction.x*weight,y:p.y+correction.y*weight};
    }
    function update(room,now,roundTrip=0) {
      const own=room.players.find(p=>p.id===room.you);
      const nextScene=[room.code,room.stage,room.phase,room.townInterior,room.innFloor,room.puzzle?.id].join(':');
      const previous=nextScene===scene ? position(room,now) : null;
      scene=nextScene;
      if (!own || !room.movement || !['combat','town','routes','stage_exit','chest','puzzle','peace'].includes(room.phase)) {anchor=null;return;}
      anchor={...room.movement, received:now, at:now-Math.min(100,roundTrip/2)-Math.min(100,room.movement.age*1000)};
      if (own.status!=='alive' || room.movementLocked) {
        anchor.speed=0; anchor.slideVx=anchor.slideVy=0;
      }
      const next=predicted(room,now);
      const error=previous?Math.hypot(previous.x-next.x,previous.y-next.y):Infinity;
      correction={x:error<60?previous.x-next.x:0,y:error<60?previous.y-next.y:0,start:now};
      if (own.status!=='alive' || room.movementLocked) correction.x=correction.y=0;
    }
    return {remember,update,position};
  }
  window.GauntletMovement={create,move,walkable};
})();
