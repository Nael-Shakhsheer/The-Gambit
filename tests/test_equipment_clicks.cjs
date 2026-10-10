const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

// Small DOM adapter: retain actual node identity and delegated click bubbling.
class Element {
  constructor(tag = 'div') {
    this.tagName = tag; this.dataset = {}; this.children = []; this.listeners = {};
    this.classes = new Set(); this.classList = {
      add: (...names) => names.forEach(n => this.classes.add(n)),
      toggle: (name, force) => {
        const add = force ?? !this.classes.has(name);
        if (add) this.classes.add(name); else this.classes.delete(name);
        return add;
      },
    };
  }
  append(...nodes) { nodes.forEach(n => { n.parent = this; this.children.push(n); }); }
  replaceChildren(...nodes) {
    this.children.forEach(n => n.parent = null); this.children = []; this.append(...nodes);
  }
  setAttribute(name, value) { this[name] = value; }
  addEventListener(name, fn) { (this.listeners[name] ??= []).push(fn); }
  set innerHTML(value) {
    this.replaceChildren();
    for (const match of value.matchAll(/<(span|b|small)(?: class="([^"]+)")?>/g)) {
      const node = new Element(match[1]); node.className = match[2] || ''; this.append(node);
    }
  }
  matches(selector) {
    if (selector.startsWith('.')) return this.className?.split(' ').includes(selector.slice(1));
    if (selector.startsWith('[data-')) {
      const key = selector.slice(6, -1).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      return key in this.dataset;
    }
    return this.tagName === selector;
  }
  querySelectorAll(selector) {
    const matches = [];
    const visit = node => node.children.forEach(child => {
      if (selector.split(',').some(s => child.matches(s.trim()))) matches.push(child);
      visit(child);
    });
    visit(this); return matches;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) { return this.matches(selector) ? this : this.parent?.closest(selector); }
  contains(node) { return node === this || this.children.some(child => child.contains(node)); }
  async click() {
    if (this.disabled) return;
    for (let node = this; node; node = node.parent) {
      for (const listener of node.listeners.click || []) await listener({target: this});
    }
  }
}
const elements = new Map();
const $ = selector => {
  if (!elements.has(selector)) elements.set(selector, new Element());
  return elements.get(selector);
};
const actions = [];
const context = { $, document: {createElement: tag => new Element(tag)}, window: {},
  Date, lastPrivateNotice: '', privateNoticeUntil: 0, lastTownSignature: '',
  decorateItemLabel() {}, appendEquipmentComparison() {}, createItemSprite() { return null; },
  async sendAction(action, payload) { actions.push({action, ...payload}); }, notice() {}, refresh() {},
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function renderQuickPouch('), source.indexOf('function renderToolHotbar(')), context);
vm.runInContext(source.slice(source.indexOf('function renderTown('), source.indexOf('function showPuzzleDialogue(')), context);
vm.runInContext(source.slice(source.indexOf('$("#quickPouch").addEventListener'), source.indexOf('$("#quickGear").addEventListener')), context);
const item = (id, slot, kind) => ({id, slot, kind, name:id, rarity:'Common', description:'Fixture', sell:1});
const heal = item('heal', 'utility', 'heal'), mana = item('mana', 'utility', 'mana');
const room = {you:'hero', host:'hero', phase:'combat', players:[{id:'hero', status:'alive', hp:100, maxHp:100}],
  inventory:[item('sword','tool','weapon'), heal, mana], utilitySlots:[heal,mana,null], toolSlots:[null,null],
  mana:100, maxMana:100, abilitySlots:[{cooldownRemaining:10}], town:'Fixture', runes:0, shopStock:[]};
context.renderQuickPouch(room); context.renderUtilityHotbar(room); context.renderTown(room);
const equipButtons = $('#quickPouch').querySelectorAll('[data-equip-item]');
const useButtons = $('#quickPouch').querySelectorAll('[data-use-item]');
const hotbar = $('#utilityHotbar').children.slice();
const shopButtons = $('#pouchItems').querySelectorAll('[data-equip-item]');
assert.ok(useButtons.every(b => b.disabled), 'Full health/mana utilities begin disabled');
for (let frame = 0; frame < 15; frame++) {
  room.abilitySlots[0].cooldownRemaining -= .1;
  room.players[0].hp -= 1; room.mana -= .1;
  context.renderQuickPouch(room); context.renderUtilityHotbar(room); context.renderTown(room);
  for (const button of equipButtons) assert.ok($('#quickPouch').contains(button), 'Polling must keep a pressed equipment button attached');
  hotbar.forEach((button, index) => assert.equal($('#utilityHotbar').children[index], button));
  for (const button of shopButtons) assert.ok($('#pouchItems').contains(button));
}
assert.ok(useButtons.every(b => !b.disabled), 'Availability refreshes without replacing buttons');
async function verifyClicks() {
  for (const button of equipButtons) await button.click();
  assert.equal(actions.length, 8);
  assert.deepEqual(actions.map(a => [a.item,a.slot]), [['sword',0],['sword',1],['heal',0],['heal',1],['heal',2],['mana',0],['mana',1],['mana',2]]);
  room.players[0].status = 'downed'; context.renderQuickPouch(room); context.renderUtilityHotbar(room);
  assert.ok(useButtons.every(b => b.disabled));
  assert.ok(hotbar.every(b => b.disabled));
  room.inventory = room.inventory.slice(1); room.toolSlots[1] = item('sword','tool','weapon');
  context.renderQuickPouch(room);
  assert.equal($('#quickPouch').querySelectorAll('[data-equip-item]').length, 6, 'Real equipment changes still rebuild the pouch');
  console.log('Equipment clicks persist through cooldown/HP/mana polling; all two tool and three utility slots dispatch correctly.');
}
verifyClicks().catch(error => { console.error(error); process.exitCode = 1; });
