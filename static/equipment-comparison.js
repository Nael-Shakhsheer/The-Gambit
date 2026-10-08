(() => {
  const sign = value => (value >= 0 ? '+' : '−') + Math.abs(value);
  function compare(item, slots, index) {
    const old = slots[index];
    if (item.slot === 'utility') return {stats: old ? 'Replace '+old.name : 'Empty slot', detail: item.description || ''};
    const before = new Map(slots.filter(Boolean).filter(i=>i.effect).map(i=>[i.effect,i.effectLabel]));
    const after = new Map(slots.map((i,n)=>n===index?item:i).filter(Boolean).filter(i=>i.effect).map(i=>[i.effect,i.effectLabel]));
    const gains = [...after].filter(([key])=>!before.has(key)).map(([,label])=>'Gain '+label);
    const losses = [...before].filter(([key])=>!after.has(key)).map(([,label])=>'Lose '+label);
    const stats = 'DMG '+sign((item.damage||0)-(old?.damage||0))+' · ARM '+sign((item.armor||0)-(old?.armor||0));
    return {stats, detail: [old ? 'Replaces '+old.name : 'Empty slot', ...gains, ...losses].join('. '), gains, losses};
  }
  window.GauntletEquipment = {compare};
})();
