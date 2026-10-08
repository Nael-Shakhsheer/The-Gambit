const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
let modal = false, sends = 0;
let chestDraw;
const chestPreview = { Date, Math, window: { GauntletTownSprites: { chest(_ctx, state) { chestDraw = state; return true; } } } };
vm.createContext(chestPreview);
vm.runInContext(source.slice(source.indexOf('function drawTreasureChest('), source.indexOf('function drawCombatEffects(')), chestPreview);
const chestContext = { save() {}, restore() {}, beginPath() {}, arc() {}, fill() {}, fillText() {} };
for (const opened of [false, true]) {
  chestPreview.drawTreasureChest(chestContext, { x:480, y:270, runesAwarded:true, opened });
  assert.equal(chestDraw.opened, opened, 'Chest art uses the viewer share, not shared rune collection');
}
console.log('Chest animation respects personal opening state.');
const held = { latestRoom: { phase: 'combat', waveCountdown: 0 }, moveState: { x: 1, y: 0, attack: false },
  document: { querySelector: () => modal }, sendMovement: () => sends++ };
vm.createContext(held);
vm.runInContext(source.slice(source.indexOf('let attackPointerId ='), source.indexOf('$("#attackButton").textContent')), held);
const event = (id, button = 0) => ({ pointerId: id, button, preventDefault() {}, currentTarget: { setPointerCapture() {} } });
held.beginHeldAttack(event(1, 2));
assert.equal(held.moveState.attack, false, 'Right click does not attack');
held.beginHeldAttack(event(1));
assert.equal(held.moveState.attack, true);
assert.equal(held.moveState.x, 1, 'Starting an attack preserves movement');
held.endHeldAttack(event(2));
assert.equal(held.moveState.attack, true, 'Releasing a movement finger does not end attack');
held.endHeldAttack(event(1));
assert.equal(held.moveState.attack, false);
assert.equal(held.moveState.x, 1, 'Ending attack preserves movement');
held.beginHeldAttack(event(3)); held.endHeldAttack();
assert.equal(held.moveState.attack, false, 'Focus loss cancels attack');
modal = true; held.beginHeldAttack(event(4));
assert.equal(held.moveState.attack, false, 'Dialogs block attacks');
assert.ok(sends >= 4);

for (const key of ['Troll', 'Spider', 'Wolf', 'Druid', 'LightningBird', 'FireWolf', 'IceBear', 'NatureGolem', 'Archer', 'Cleric', 'Rogue', 'Bard', 'Healer']) {
const meta = JSON.parse(fs.readFileSync(path.join(__dirname, '../static/sprites/' + key.toLowerCase() + '-idle.json'), 'utf8'));
const png = fs.readFileSync(path.join(__dirname, '../static/sprites/' + key.toLowerCase() + '-idle.png'));
assert.equal(png.readUInt32BE(16), 612); assert.equal(png.readUInt32BE(20), 612);
const directions = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west'];
let clock = 10000, drawn;
const sprite = { heroSprites: { [key]: { sheet: meta.spritesheet, image: { complete: true, naturalWidth: 612 } } },
  SPRITE_DIRECTIONS: directions, Date: { now: () => clock } };
vm.createContext(sprite);
vm.runInContext(source.slice(source.indexOf('function drawImportedHero('), source.indexOf('async function api(')), sprite);
const ctx = { save() {}, restore() {}, drawImage(...args) { drawn = args; } };
for (let row = 0; row < 8; row++) {
  const angle = Math.PI / 2 - row * Math.PI / 4;
  for (const [mode, frames] of Object.entries(meta.animations)) {
    for (let frame = 0; frame < 3; frame++) {
      clock = mode === 'attack' ? 10000 + frame * 130 : (60 + frame) * (key === 'Druid' ? (mode === 'walk' ? 300 : 550) : 180);
      const player = { status: 'alive', facingX: Math.cos(angle), facingY: Math.sin(angle), moving: mode === 'walk', animationUntil: mode === 'attack' ? 10.45 : 0 };
      assert.ok(sprite.drawImportedHero(ctx, player, 100, 100, key));
      assert.equal(drawn[1], frames[frame] * 68, `${mode} frame ${frame}`);
      assert.equal(drawn[2], (row + 1) * 68, `${directions[row]} animation row`);
      assert.equal(drawn[3], 68); assert.equal(drawn[4], 68);
    }
  }
}
}
console.log('Held attack: mouse button, release, multi-touch, movement and dialog checks passed.');
console.log('Thirteen imported enemy/hero/summon sheets: all 936 directional animation cells and asset dimensions passed.');
