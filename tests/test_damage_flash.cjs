// Run with Node and @napi-rs/canvas available (bundled in the Codex runtime).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createCanvas, loadImage } = require('@napi-rs/canvas');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
let now = 1000;
const sandbox = {
  window: {},
  drawImportedHero: () => false,
  performance: { now: () => now },
  document: { createElement: () => createCanvas(128, 128) },
};
vm.createContext(sandbox);
vm.runInContext(source.slice(source.indexOf('const motionTracks ='), source.indexOf('let motionScene =')) +
  'let motionScene = "", lastSnapshotAt = 0, lastSentMove = "";\n' +
  source.slice(source.indexOf('function updateMotionTracks('), source.indexOf('function animateWorld(')) +
  source.slice(source.indexOf('function drawDamageTint('), source.indexOf('function drawWorld(')), sandbox);
const snapshot = (hp, damageTaken, maxHp = 100, code = 'TEST') => ({
  code, stage: 1, phase: 'combat', players: [{ id: 'hero', hp, maxHp, damageTaken, x: 30, y: 30 }],
  enemies: [{ id: 'enemy', hp, maxHp, damageTaken, x: 60, y: 30 }],
});
function render(group = 'player', id = 'hero') {
  const canvas = createCanvas(100, 100);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#123456'; ctx.fillRect(0, 0, 100, 100);
  sandbox.drawDamageTint(ctx, group, { id }, 30, 30, (target) => {
    target.fillStyle = '#00ff00'; target.fillRect(25, 25, 10, 10);
  });
  return { body: [...ctx.getImageData(30, 30, 1, 1).data], background: [...ctx.getImageData(20, 20, 1, 1).data] };
}
sandbox.updateMotionTracks(snapshot(100, 0));
assert.deepEqual(render().body, [0, 255, 0, 255], 'Initial snapshots do not flash');
now += 100;
sandbox.updateMotionTracks(snapshot(90, 1));
assert.ok(render().body[0] > render().body[1], 'Hero takes on a red hue');
assert.ok(render('enemy', 'enemy').body[0] > render('enemy', 'enemy').body[1], 'Enemy takes on a red hue');
assert.deepEqual(render().background, [18, 52, 86, 255], 'Transparent surroundings stay unchanged');
now += 180;
const faded = render().body;
assert.ok(faded[0] > 0 && faded[0] < 100, 'The hue fades smoothly');
now += 60;
sandbox.updateMotionTracks(snapshot(90, 1));
assert.deepEqual(render().body, [0, 255, 0, 255], 'Repeated snapshots do not restart an expired flash');
now += 100;
sandbox.updateMotionTracks(snapshot(100, 1));
assert.deepEqual(render().body, [0, 255, 0, 255], 'Healing does not flash');
sandbox.updateMotionTracks(snapshot(100, 2));
assert.ok(render().body[0] > render().body[1], 'Damage followed by healing before polling still flashes');
sandbox.updateMotionTracks(snapshot(100, 2, 100, 'NEW'));
assert.deepEqual(render().body, [0, 255, 0, 255], 'Changing rooms clears old flashes');
sandbox.updateMotionTracks(snapshot(50, 2, 50, 'NEW'));
assert.deepEqual(render().body, [0, 255, 0, 255], 'Changing class HP does not flash');
now += 100;
sandbox.updateMotionTracks(snapshot(45, undefined, 50, 'NEW'));
assert.ok(render().body[0] > render().body[1], 'HP changes support servers started before this update');
now += 240;
assert.deepEqual(render().body, [0, 255, 0, 255]);
console.log('Damage tracking, fade timing, hero/enemy tint pixels and alpha isolation: OK');

const companions = ['bird', 'wolf', 'bear', 'golem'].map((kind) => ({
  id: kind, kind, name: kind, x: 100, y: 100, hp: 100, maxHp: 100,
  damageTaken: 0, color: '#85dcf2', facingX: 1, animationUntil: 0, moving: false,
}));
const summonSnapshot = () => ({ ...snapshot(100, 0), summons: companions });
function renderSummon(summon) {
  const canvas = createCanvas(200, 200);
  sandbox.drawSummon(canvas.getContext('2d'), summon);
  const ctx = canvas.getContext('2d');
  return {
    body: [...ctx.getImageData(100, 90, 1, 1).data],
    ring: [...ctx.getImageData(72, 112, 1, 1).data],
    outside: [...ctx.getImageData(50, 50, 1, 1).data],
  };
}
sandbox.updateMotionTracks(summonSnapshot());
const beforeHit = companions.map(renderSummon);
for (const summon of companions) { summon.hp -= 10; summon.damageTaken += 1; }
now += 100;
sandbox.updateMotionTracks(summonSnapshot());
companions.forEach((summon, index) => {
  const flashed = renderSummon(summon);
  assert.equal(flashed.body[3], 255, summon.kind + ' has opaque body art');
  assert.ok(flashed.body[0] > beforeHit[index].body[0], summon.kind + ' damage raises red');
  assert.ok(flashed.body[1] < beforeHit[index].body[1], summon.kind + ' damage lowers green');
  assert.deepEqual(flashed.ring, beforeHit[index].ring, 'Elemental ring retains its color');
  assert.deepEqual(flashed.outside, [0, 0, 0, 0], 'Summon art retains transparent surroundings');
});
console.log('All four summon renderers and isolated summon damage tints: OK');


(async () => {
  sandbox.heroSprites = {};
  sandbox.SPRITE_DIRECTIONS = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west'];
  vm.runInContext(source.slice(source.indexOf('function drawImportedHero('), source.indexOf('async function api(')), sandbox);
  for (const key of ['Wolf', 'Druid', 'Archer', 'Cleric', 'Rogue', 'Bard', 'Healer', 'LightningBird', 'FireWolf', 'IceBear', 'NatureGolem']) {
    const base = path.join(__dirname, '../static/sprites/' + key.toLowerCase() + '-idle');
    sandbox.heroSprites[key] = { image: await loadImage(base + '.png'), sheet: JSON.parse(fs.readFileSync(base + '.json')).spritesheet };
    const canvas = createCanvas(200, 200), ctx = canvas.getContext('2d');
    assert.ok(sandbox.drawImportedHero(ctx, { class: key, status: 'alive', animationUntil: 0 }, 100, 100));
    assert.ok(ctx.getImageData(65, 60, 70, 70).data.some((v, i) => i % 4 === 3 && v > 0), key + ' paints real PNG pixels');
  }
  const sprites = companions.map((s, i) => ({ ...s, id: 'imported-' + i, status: 'alive', hp: 100, damageTaken: 0,
    abilityId: ['lightning_bird', 'fire_wolf', 'ice_bear', 'nature_golem'][i] }));
  function realPixels(summon) {
    const canvas = createCanvas(200, 200), ctx = canvas.getContext('2d');
    sandbox.drawSummon(ctx, summon);
    return ctx.getImageData(80, 65, 40, 40).data;
  }
  sandbox.updateMotionTracks({ ...snapshot(100, 0, 100, 'IMPORTED'), summons: sprites });
  const originals = sprites.map(realPixels);
  now += 100;
  for (const s of sprites) { s.hp = 90; s.damageTaken = 1; }
  sandbox.updateMotionTracks({ ...snapshot(100, 0, 100, 'IMPORTED'), summons: sprites });
  sprites.forEach((s, i) => {
    const hit = realPixels(s);
    let greenBefore = 0, greenAfter = 0;
    for (let pixel = 0; pixel < hit.length; pixel += 4) {
      assert.equal(hit[pixel + 3], originals[i][pixel + 3], s.name + ' damage preserves imported alpha');
      greenBefore += originals[i][pixel + 1]; greenAfter += hit[pixel + 1];
    }
    assert.ok(greenAfter < greenBefore, s.name + ' imported art takes red damage hue');
  });
  console.log('All eleven new PNGs render; all four imported summons retain alpha and damage feedback: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
