const $ = (selector) => document.querySelector(selector);
const CLASS_ORDER = ["Knight", "Wizard", "Archer", "Cleric", "Rogue", "Druid", "Bard", "Healer"];
const ITEM_SPRITE_KEYS = new Set(["healing_draught","warding_tonic","mana_draught","quickstep_elixir","route_lens","ember_oil","piercing_arrows","phoenix_flask","stormguard_charm","iron_sword","oakguard_vest","moonsteel_sword","dragonbone_armor","starfall_blade","aegis_of_dawn","sage_wand","wind_bow","sun_censer","shadow_blades","thorn_staff","travel_lute","mercy_rod"]);
function createItemSprite(item) {
  const key = ({arcane_conductor:'sage_wand',rescuers_cuirass:'oakguard_vest',summoners_staff:'thorn_staff',pursuit_blade:'shadow_blades'})[item?.key] || item?.key;
  if (!item || !ITEM_SPRITE_KEYS.has(key)) return null;
  const image = document.createElement("img");
  image.className = "item-sprite";
  image.src = "/sprites/item-" + key + "-v1.png";
  if (key !== item.key) image.dataset.build = item.effect;
  image.alt = ""; image.setAttribute("aria-hidden", "true");
  image.width = image.height = 64;
  image.draggable = false;
  image.addEventListener("error", () => image.remove(), { once: true });
  return image;
}
function decorateItemLabel(label, item) {
  label.dataset.rarity = String(item?.rarity || "common").toLowerCase();
  const image = createItemSprite(item);
  if (!image) return;
  const text = document.createElement("span");
  text.className = "item-title-text"; text.textContent = label.textContent;
  label.classList.add("item-label");
  label.replaceChildren(image, text);
}
const SYMBOLS = { Knight: "♜", Wizard: "✦", Archer: "➶", Cleric: "✚", Rogue: "⚔", Druid: "❧", Bard: "♫", Healer: "✧" };
function appendEquipmentComparison(parent, item, room) {
  const slots = item.slot === 'tool' ? room.toolSlots : room.utilitySlots;
  if (!slots || !window.GauntletEquipment) return;
  const panel = document.createElement('div'); panel.className = 'gear-comparison';
  slots.forEach((old, index) => {
    const comparison = window.GauntletEquipment.compare(item, slots, index);
    const line = document.createElement('small');
    line.textContent = (item.slot === 'tool' ? 'Tool ' : 'Utility ') + (index+1) + ': ' + comparison.stats;
    line.title = comparison.detail;
    if (comparison.gains?.length || comparison.losses?.length) line.textContent += ' · ' + [...comparison.gains, ...comparison.losses].join('; ');
    panel.append(line);
  });
  parent.append(panel);
}
function decorateHeroIcon(container, role) {
  if (!CLASS_ORDER.includes(role)) return;
  if (container.dataset.portrait === role) return;
  container.dataset.portrait = role;
  const image = document.createElement("img");
  image.src = "/sprites/portrait-" + role.toLowerCase() + "-v1.png";
  image.className = "hero-portrait"; image.width = image.height = 64;
  image.alt = ""; image.setAttribute("aria-hidden", "true"); image.draggable = false;
  image.addEventListener("error", () => { container.textContent = SYMBOLS[role]; }, { once: true });
  container.replaceChildren(image); container.classList.add("portrait-frame");
}
const DEFAULT_BINDINGS = { up: "w", down: "s", left: "a", right: "d", special: "q", ultimate: "x", revive: "e" };
const BINDING_LABELS = { up: "Move up", down: "Move down", left: "Move left", right: "Move right", special: "Special attack", ultimate: "Ultimate attack", revive: "Revive / interact" };
let keyBindings;
try { keyBindings = Object.assign({}, DEFAULT_BINDINGS, JSON.parse(localStorage.getItem("gauntlet-keybindings") || "{}")); }
catch { keyBindings = Object.assign({}, DEFAULT_BINDINGS); }
let bindingCapture = null;
let session = JSON.parse(localStorage.getItem("gauntlet-session") || "null");
let lastChatSignature = "";
let lastPuzzleId = "";
let lastPuzzleClue = "";
let puzzleDialogueTimer = null;
let lastTownSignature = "";
let lastRouteSignature = "";
let lastLoadoutSignature = "";
let lastAbilityBarSignature = "";
let lastClassSignature = "";
let lastChestSignature = "";
let lastPrivateNotice = "";
let privateNoticeUntil = 0;
let latestRoom = null;
let lastGuildSignature = "";
let guildSelected = [];
let guildBusy = false;
let arenaPointerActive = false;
let polling = false;
let moveState = { x: 0, y: 0, attack: false };
let lastSentMove = "";
let lastInputSent = 0;
let inputSequence = 0;
let inputBusy = false;
let pendingInput = null;
let localTarget = null;
const localMotion = window.GauntletMovement?.create() || {remember(){},update(){},position(){return null;}};
const motionTracks = new Map();
const damageTracks = new Map();
const DAMAGE_FLASH_MS = 220;
let damageRoom = "";
const damageLayer = document.createElement("canvas");
damageLayer.width = damageLayer.height = 256;
let motionScene = "";
let lastSnapshotAt = 0;
const terrainLayer = document.createElement("canvas");
let terrainKey = "";
const fieldArt = {};
let fieldArtRevision = 0;
const forkArt = {};
const forkLayer = document.createElement("canvas");
let forkArtRevision = 0;
let forkTerrainKey = "";
for (const region of ["woodland", "ruins", "cavern", "frost"]) {
  const image = fieldArt[region] = new Image();
  image.onload = () => { fieldArtRevision += 1; terrainKey = ""; };
  image.src = "/sprites/field-" + region + "-v1.png";
  const forkImage = forkArt[region] = new Image();
  forkImage.onload = () => { forkArtRevision += 1; forkTerrainKey = ""; };
  forkImage.src = "/sprites/fork-" + region + "-v1.png";
}
const glowLayers = new Map();
const villageArt = {};
const villageLayer = document.createElement("canvas");
let villageArtRevision = 0, villageTerrainKey = "";
const VILLAGE_BUILDINGS = ["inn", "store", "lab", "guild", "cottage", "lodge"];
const VILLAGE_ROOFS = ["#a94f3d", "#426f78", "#c56643", "#906451", "#b6773f", "#66518c"];
const VILLAGE_PROPS = ["tree", "gate", "bed", "stairs", "closed-door", "open-door"];
for (const region of ["woodland", "ruins", "cavern", "frost"]) {
  villageArt[region] = {};
  for (const kind of ["ground", "buildings", "props", "beds", "interiors", "upstairs", "hunter"]) {
    const image = villageArt[region][kind] = new Image();
    image.onload = () => { villageArtRevision++; villageTerrainKey = ""; };
    image.src = "/sprites/village-" + region + "-" + kind + "-v1.png";
  }
}
function villageImage(room, kind) {
  const image = (villageArt[room?.region] || villageArt.woodland)[kind];
  return image?.complete && image.naturalWidth ? image : null;
}
function drawVillageProp(ctx, room, kind, x, y, width, height, variant = 0) {
  const beds = kind === "bed" ? villageImage(room, "beds") : null;
  const image = beds || villageImage(room, "props");
  if (!image) return false;
  const index = VILLAGE_PROPS.indexOf(kind);
  if (index < 0) return false;
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(image, beds ? (variant % 3) * 64 : index % 3 * 64,
    beds ? 0 : Math.floor(index / 3) * 64, 64, 64, x, y, width, height);
  return true;
}
function drawVillageInteriorArt(ctx, room, house, w, h) {
  const upstairs = house?.service === "innkeeper" && room.innFloor === 2;
  const image = villageImage(room, upstairs ? "upstairs" : "interiors");
  if (!image) return false;
  ctx.imageSmoothingEnabled = false;
  if (upstairs) ctx.drawImage(image, 0, 0, w, h);
  else {
    const index = Math.max(0, VILLAGE_BUILDINGS.indexOf(house?.id));
    ctx.drawImage(image, index % 2 * 480, Math.floor(index / 2) * 270, 480, 270, 0, 0, w, h);
  }
  return true;
}
const heroSprites = {};
const SPRITE_DIRECTIONS = ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"];
for (const role of ["Knight", "Wizard", "Serpent", "Minotaur", "Troll", "Spider", "Wolf", "Draco", "Dragon", "Chimera", "Druid", "LightningBird", "FireWolf", "IceBear", "NatureGolem", "Archer", "Cleric", "Rogue", "Bard", "Healer"]) {
  const base = role === "Dragon" ? "/sprites/dragon-adult-idle-v2" : "/sprites/" + role.toLowerCase() + "-idle";
  const image = new Image();
  const sprite = heroSprites[role] = { image, sheet: null };
  image.src = base + ".png";
  fetch(base + ".json").then((response) => {
    if (!response.ok) throw new Error("Sprite metadata unavailable");
    return response.json();
  }).then((metadata) => { sprite.sheet = metadata.spritesheet; })
    .catch(() => { sprite.sheet = null; });
}

function drawImportedHero(ctx, player, x, y, spriteKey = player.class) {
  const sprite = heroSprites[spriteKey];
  if (!sprite?.sheet || !sprite.image.complete || !sprite.image.naturalWidth) return false;
  const sheet = sprite.sheet;
  const directionIndex = (Math.round((Math.PI / 2 - Math.atan2(player.facingY ?? 1, player.facingX ?? 0)) / (Math.PI / 4)) + 8) % 8;
  const row = sheet.rows.find((entry) => entry.type === "animation" && entry.direction === SPRITE_DIRECTIONS[directionIndex]);
  if (!row) return false;
  const now = Date.now();
  let frames = ["Minotaur", "Troll", "Spider", "Wolf", "Draco", "Dragon", "Chimera", "Druid", "LightningBird", "FireWolf", "IceBear", "NatureGolem", "Archer", "Cleric", "Rogue", "Bard", "Healer"].includes(spriteKey) ? (player.moving ? [3, 4, 5] : [0, 1, 2]) : player.moving ? [2, 3] : [0, 1];
  let frameIndex = Math.floor(now / (spriteKey === "Druid" ? (player.moving ? 300 : 550) : 180));
  if (player.status !== "alive") frames = [0];
  else if (player.animationUntil * 1000 > now) {
    frames = ["Serpent", "Minotaur", "Troll", "Spider", "Wolf", "Draco", "Dragon", "Chimera", "Druid", "LightningBird", "FireWolf", "IceBear", "NatureGolem", "Archer", "Cleric", "Rogue", "Bard", "Healer"].includes(spriteKey) ? [6, 7, 8] : player.animation === "ultimate" ? [8] : player.animation === "special" ? [7] : [4, 5, 6];
    frameIndex = Math.max(0, Math.min(frames.length - 1, Math.floor((now - (player.animationUntil * 1000 - 450)) / 130)));
  }
  const column = frames[frameIndex % frames.length];
  const cell = sheet.cell_size;
  ctx.imageSmoothingEnabled = false;
  ctx.save();
  if (player.status !== "alive") {
    ctx.translate(x, y); ctx.rotate(Math.PI / 2); ctx.translate(-x, -y);
  }
  ctx.drawImage(sprite.image, column * cell.width, row.row * cell.height, cell.width, cell.height,
    spriteKey === "Dragon" ? x - 64 : x - 32, spriteKey === "Dragon" ? y - 102 : y - 42,
    spriteKey === "Dragon" ? 128 : 64, spriteKey === "Dragon" ? 128 : 64);
  ctx.restore();
  return true;
}

async function api(path, data) {
  if (window.location.protocol === "file:") {
    throw new Error("Open the game at http://127.0.0.1:8000/ with server.py running. This file preview cannot connect to the game server.");
  }
  const response = await fetch(path, {
    method: data ? "POST" : "GET",
    headers: data ? { "Content-Type": "application/json" } : {},
    body: data ? JSON.stringify(data) : undefined
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Something went wrong.");
  return result;
}
function sendAction(action, extra) {
  if (!session) return Promise.resolve();
  return api("/api/action", Object.assign({ room: session.room, player: session.player, action }, extra || {}));
}
function saveSession(value) {
  session = value;
  localStorage.setItem("gauntlet-session", JSON.stringify(value));
  localStorage.setItem("gauntlet-resume", JSON.stringify(value));
  enterLobby();
  refresh();
}
function enterLobby() {
  $("#entry").classList.add("hidden");
  $("#lobby").classList.remove("hidden");
  $("#roomCodeDisplay").textContent = session.room;
  $("#connection").textContent = "CONNECTING";
  $("#connection").className = "connection connecting";
}
let combatNoticeUntil = 0;
function notice(element, message) {
  element.textContent = message;
  if (element.id === "combatNotice") combatNoticeUntil = Date.now() + 3500;
}

$("#createForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  notice($("#entryNotice"), "");
  try {
    const result = await api("/api/rooms", { name: $("#createName").value });
    saveSession({ room: result.room, player: result.player });
  } catch (error) { notice($("#entryNotice"), error.message); }
});
$("#joinForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  notice($("#entryNotice"), "");
  try {
    const result = await api("/api/join", { name: $("#joinName").value, room: $("#roomCode").value });
    saveSession({ room: result.room, player: result.player });
  } catch (error) { notice($("#entryNotice"), error.message); }
});
function renderKeyBindings() {
  const fields = $("#keyBindingFields");
  fields.replaceChildren();
  Object.entries(BINDING_LABELS).forEach(([action, label]) => {
    const row = document.createElement("div");
    row.className = "key-binding-row";
    const name = document.createElement("span"); name.textContent = label;
    const button = document.createElement("button"); button.type = "button"; button.className = "secondary key-bind";
    button.dataset.bind = action;
    button.textContent = bindingCapture === action ? "Press a key…" : String(keyBindings[action] || DEFAULT_BINDINGS[action]).toUpperCase();
    button.setAttribute("aria-label", label + " key, currently " + button.textContent);
    row.append(name, button); fields.append(row);
  });
  $("#controlHint").textContent = "Move: WASD · Dash: Space (5s) · Light attack: Left click · Special: " + String(keyBindings.special).toUpperCase() +
    " · Ultimate: " + String(keyBindings.ultimate).toUpperCase();
}
$("#openSettings").addEventListener("click", () => { $("#keySettings").classList.remove("hidden"); renderKeyBindings(); });
$("#closeSettings").addEventListener("click", () => { bindingCapture = null; $("#keySettings").classList.add("hidden"); });
$("#resetBindings").addEventListener("click", () => {
  keyBindings = Object.assign({}, DEFAULT_BINDINGS);
  localStorage.setItem("gauntlet-keybindings", JSON.stringify(keyBindings));
  bindingCapture = null; renderKeyBindings();
});
$("#keyBindingFields").addEventListener("click", (event) => {
  const button = event.target.closest("[data-bind]");
  if (button) { bindingCapture = button.dataset.bind; renderKeyBindings(); }
});
$("#roomCode").addEventListener("input", (event) => { event.target.value = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ""); });
$("#copyCode").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(session.room);
    $("#copyCode").textContent = "Copied!";
    setTimeout(() => $("#copyCode").textContent = "Copy invite code", 1600);
  } catch { $("#copyCode").textContent = "Code: " + session.room; }
});
async function returnToMainMenu(approved = false) {
  if (approved !== true && latestRoom && latestRoom.phase !== 'lobby') {
    const saved = latestRoom.checkpointSavedAt;
    $('#leaveRunCopy').textContent = 'Continue can rejoin this session while the server stays running. '+
      (saved ? 'Your disk checkpoint is the inn after stage '+latestRoom.checkpointStage+'. A server restart returns you to that bed; later progress is lost.' : 'There is no disk checkpoint yet. A server restart loses this run. Rest at an upstairs inn bed to set a checkpoint.');
    endHeldAttack(); keys.clear(); moveState.x=moveState.y=0;sendMovement(true);
    $('#leaveRunDialog').showModal(); return;
  }
  const menu = document.querySelector(".game-menu");
  if (menu) menu.open = false;
  $("#chatPanel").classList.remove("hud-open");
  $("#pouchPanel").classList.remove("hud-open");
  $("#toggleChat").textContent = "Chat";
  $("#togglePouch").textContent = "Pouch";
  const leaving = session;
  session = null;
  try { if (leaving) await api("/api/action", { ...leaving, action: "disconnect" }); } catch { /* The server also detects stale connections. */ }
  session = null;
  latestRoom = null;
  renderGuild(null);
  localStorage.removeItem("gauntlet-session");
  $("#lobby").classList.add("hidden");
  $("#entry").classList.remove("hidden");
  document.body.classList.remove("is-playing");
  $("#connection").textContent = "READY";
  $("#connection").className = "connection";
  const filePreview = window.location.protocol === "file:";
  notice($("#entryNotice"), filePreview ?
    "This file preview cannot reach multiplayer. Open the live server page instead." : "");
  $("#liveGameLink").classList.toggle("hidden", !filePreview);
  notice($("#roomNotice"), "");
  $("#continueRun").classList.toggle("hidden", !localStorage.getItem("gauntlet-resume"));
}
$("#mainMenu").addEventListener("click", returnToMainMenu);
$("#mainMenuGame").addEventListener("click", returnToMainMenu);
let runOptionsBusy = false;
$('#confirmLeaveRun').addEventListener('click', () => {$('#leaveRunDialog').close();returnToMainMenu(true);});
async function updateRunOptions() {
  if (!latestRoom || latestRoom.you !== latestRoom.host || runOptionsBusy) return;
  const difficulty = $("#difficultyChoice").value, companion = $("#npcCompanion").checked, stages=Number($('#lengthChoice').value);
  runOptionsBusy = true; $("#runOptions").disabled = true;
  try { await sendAction("runOptions", { difficulty, companion, stages }); notice($("#roomNotice"), ""); }
  catch (error) { notice($("#roomNotice"), error.message); }
  finally { runOptionsBusy = false; refresh(); }
}
$("#difficultyChoice").addEventListener("change", updateRunOptions);
$('#lengthChoice').addEventListener('change', updateRunOptions);
$("#npcCompanion").addEventListener("change", updateRunOptions);
$("#startRun").addEventListener("click", async () => {
  try { await sendAction("start"); refresh(); }
  catch (error) { notice($("#entryNotice"), error.message); }
});
$("#abilityChoices").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-ability]");
  if (!button || !latestRoom) return;
  const current = latestRoom.selectedAbilities.slice();
  const id = button.dataset.ability;
  const ability = (latestRoom.abilityOptions[latestRoom.players.find((player) => player.id === latestRoom.you)?.class] || []).find((entry) => entry.id === id);
  if (!ability) return;
  const currentRecords = latestRoom.abilityOptions[latestRoom.players.find((player) => player.id === latestRoom.you)?.class] || [];
  const category = ability.attackType;
  const next = current.filter((entry) => currentRecords.find((option) => option.id === entry)?.attackType !== category);
  if (!current.includes(id)) next.push(id);
  const order = { light: 0, special: 1, ultimate: 2 };
  next.sort((a, b) => order[currentRecords.find((option) => option.id === a)?.attackType] - order[currentRecords.find((option) => option.id === b)?.attackType]);
  try { await sendAction("loadout", { abilities: next }); notice($("#abilityNotice"), next.length + " of 3 selected."); refresh(); }
  catch (error) { notice($("#abilityNotice"), error.message); }
});
$("#abilityButtons").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-ability-slot]");
  if (!button || button.disabled) return;
  try { await sendAction("ability", { slot: Number(button.dataset.abilitySlot) }); notice($("#combatNotice"), ""); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
});
async function triggerAbility(category) {
  if (!latestRoom || latestRoom.phase !== "combat") return;
  if (latestRoom.waveCountdown) return;
  const index = latestRoom.abilitySlots.findIndex((ability) => ability.attackType === category);
  if (index < 0) return notice($("#combatNotice"), "Choose this ability in your class loadout first.");
  if (latestRoom.abilitySlots[index].summonAlive) return notice($("#combatNotice"), latestRoom.abilitySlots[index].name + " is still alive.");
  try { await sendAction("ability", { slot: index + 1 }); notice($("#combatNotice"), ""); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
}
async function triggerDash() {
  if (!latestRoom || latestRoom.phase !== "combat" || latestRoom.dashCooldown) return;
  try { await sendAction("dash"); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
}
$("#chestSwapChoices").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-chest-swap]");
  if (!button) return;
  try { await sendAction("chestClaim", { replace: button.dataset.chestSwap }); notice($("#chestNotice"), ""); refresh(); }
  catch (error) { notice($("#chestNotice"), error.message); }
});
$("#quickPouch").addEventListener("click", async (event) => {
  const use = event.target.closest("[data-use-item]");
  const equip = event.target.closest("[data-equip-item]");
  const button = use || equip;
  if (!button || button.disabled) return;
  try {
    if (use) await sendAction("useItem", { item: use.dataset.useItem });
    else await sendAction("equipItem", { item: equip.dataset.equipItem, slot: Number(equip.dataset.equipSlot) });
    notice($("#pouchNotice"), ""); refresh();
  } catch (error) { notice($("#pouchNotice"), error.message); }
});
$("#quickGear").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-unequip]");
  if (!button || button.disabled) return;
  try {
    await sendAction("unequipItem", { slotKind: button.dataset.slotKind, slot: Number(button.dataset.slot) });
    notice($("#pouchNotice"), ""); refresh();
  } catch (error) { notice($("#pouchNotice"), error.message); }
});
$("#utilityHotbar").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-use-item]");
  if (!button || button.disabled) return;
  try { await sendAction("useItem", { item: button.dataset.useItem }); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
});
async function triggerUtility(index) {
  if (!latestRoom) return;
  const item = latestRoom.utilitySlots[index];
  const own = latestRoom.players.find((player) => player.id === latestRoom.you);
  if (!item || !canUseUtility(latestRoom, item, own)) return;
  try { await sendAction("useItem", { item: item.id }); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
}
$("#toggleChat").addEventListener("click", () => {
  const panel = $("#chatPanel");
  panel.classList.toggle("hud-open");
  $("#toggleChat").textContent = panel.classList.contains("hud-open") ? "Close chat" : "Chat";
});
$("#togglePouch").addEventListener("click", () => {
  const panel = $("#pouchPanel");
  panel.classList.toggle("hud-open");
  $("#togglePouch").textContent = panel.classList.contains("hud-open") ? "Close pouch" : "Pouch";
});
$("#expandPouch").addEventListener("click", () => {
  const expanded = $("#pouchPanel").classList.toggle("pouch-expanded");
  $("#expandPouch").textContent = expanded ? "Collapse" : "Expand";
  $("#expandPouch").setAttribute("aria-expanded", String(expanded));
});
$("#shopStock").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-buy]");
  if (!button) return;
  try { await sendAction("shopBuy", { item: button.dataset.buy }); refresh(); }
  catch (error) { notice($("#townNotice"), error.message); }
});
$("#pouchItems").addEventListener("click", async (event) => {
  const sell = event.target.closest("[data-sell]");
  const use = event.target.closest("[data-use]");
  const equip = event.target.closest("[data-equip-item]");
  try {
    if (sell) await sendAction("shopSell", { item: sell.dataset.sell });
    else if (use) await sendAction("useItem", { item: use.dataset.use });
    else if (equip) await sendAction("equipItem", { item: equip.dataset.equipItem, slot: Number(equip.dataset.equipSlot) });
    else return;
    notice($("#townNotice"), "");
    refresh();
  } catch (error) { notice($("#townNotice"), error.message); }
});
$("#equipmentSlots").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-unequip]");
  if (!button) return;
  try { await sendAction("unequipItem", { slotKind: button.dataset.slotKind, slot: Number(button.dataset.slot) }); refresh(); }
  catch (error) { notice($("#townNotice"), error.message); }
});
$("#closeTownShop").addEventListener("click", async () => {
  try { await sendAction("closeShop"); refresh(); }
  catch (error) { notice($("#townNotice"), error.message); }
});
$("#checkpointResume").addEventListener("click", async () => {
  try { await sendAction("checkpointResume"); refresh(); }
  catch (error) { notice($("#defeatMessage"), error.message); }
});
$("#chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#chatInput");
  const message = input.value.trim();
  if (!message || !session) return;
  input.value = "";
  try { await sendAction("chat", { message }); }
  catch (error) { input.value = message; input.placeholder = error.message; }
});
let attackPointerId = null;
function beginHeldAttack(event) {
  if (event.button !== 0 || !latestRoom || latestRoom.phase !== "combat" || latestRoom.waveCountdown || document.querySelector("dialog[open]")) return;
  event.preventDefault();
  attackPointerId = event.pointerId;
  event.currentTarget.setPointerCapture(event.pointerId);
  moveState.attack = true; sendMovement(true);
}
function endHeldAttack(event) {
  if (event && event.pointerId !== attackPointerId) return;
  attackPointerId = null;
  moveState.attack = false; sendMovement(true);
}
$("#attackButton").textContent = "Hold · Attack";
$("#attackButton").addEventListener("pointerdown", beginHeldAttack);
window.addEventListener("pointerup", endHeldAttack);
window.addEventListener("pointercancel", endHeldAttack);
document.addEventListener("visibilitychange", () => { if (document.hidden) { keys.clear(); moveState.x = moveState.y = 0; endHeldAttack(); } });
$("#dashButton").addEventListener("pointerdown", (event) => { event.preventDefault(); triggerDash(); });
$("#interactButton").addEventListener("click", async () => {
  try { await interactWithWorld(); }
  catch (error) { notice($("#combatNotice"), error.message); }
});
$("#reviveButton").addEventListener("pointerdown", (event) => { event.preventDefault(); sendAction("revive").catch(() => {}); });
["pointerup", "pointerleave", "pointercancel"].forEach((type) => $("#reviveButton").addEventListener(type, (event) => { event.preventDefault(); sendAction("stopRevive").catch(() => {}); }));
function chooseTarget(id) {
  localTarget=id;sendAction('target',{targetId:id}).catch(()=>{localTarget=null;});
  sendMovement(true);
}
$('#targetButton').addEventListener('click',()=>chooseTarget(null));
$('#world').addEventListener('pointerdown',(event)=>{
  if (event.button===0 && latestRoom?.phase==='combat') {
    const rect=event.currentTarget.getBoundingClientRect();
    const x=(event.clientX-rect.left)*960/rect.width,y=(event.clientY-rect.top)*540/rect.height;
    const hit=latestRoom.enemies.reduce((best,e)=>{
      const distance=Math.hypot((e.x-x)*rect.width/960,(e.y-y)*rect.height/540);
      return distance<(best?.distance ?? 40)?{id:e.id,distance}:best;
    },null);
    chooseTarget(hit?.id || null);
  }
  beginHeldAttack(event);
});
["#world", "#attackButton"].forEach((selector) => $(selector).addEventListener("lostpointercapture", endHeldAttack));
$("#world").addEventListener("pointermove", () => { arenaPointerActive = true; });
$("#world").addEventListener("pointerleave", () => { arenaPointerActive = false; });
async function chooseClass(name) {
  try { await sendAction("class", { class: name }); refresh(); }
  catch (error) { notice($("#entryNotice"), error.message); }
}
async function guildAction(action, extra = {}) {
  if (guildBusy) return;
  guildBusy = true;
  renderGuild(latestRoom);
  notice($("#guildNotice"), "");
  try {
    await sendAction(action, extra);
    renderRoom(await api("/api/state?room=" + encodeURIComponent(session.room) + "&player=" + encodeURIComponent(session.player)));
  } catch (error) { notice($("#guildNotice"), error.message); }
  finally { guildBusy = false; renderGuild(latestRoom); }
}
$("#guildCancel").addEventListener("click", () => guildAction("closeShop"));
$("#guildDialog").addEventListener("cancel", (event) => { event.preventDefault(); guildAction("closeShop"); });
$("#guildBack").addEventListener("click", () => guildAction("guildBack"));
$("#guildConfirm").addEventListener("click", () => guildAction("guildChange", { abilities: guildSelected.slice() }));
$("#guildAbilityChoices").addEventListener("click", (event) => {
  const button = event.target.closest("[data-guild-ability]");
  if (!button || guildBusy) return;
  const options = latestRoom?.guildPreview?.options || [];
  const chosen = options.find((a) => a.id === button.dataset.guildAbility);
  if (!chosen) return;
  guildSelected = guildSelected.filter((id) => options.find((a) => a.id === id)?.attackType !== chosen.attackType);
  guildSelected.push(chosen.id);
  renderGuild(latestRoom);
});
function renderGuild(room) {
  const dialog = $("#guildDialog");
  if (!room || room.phase !== "town" || room.townInteraction !== "guildmaster") {
    if (dialog.open) dialog.close();
    lastGuildSignature = "";
    guildSelected = [];
    return;
  }
  if (!dialog.open) {
    keys.clear(); moveState = { x: 0, y: 0, attack: false };
    notice($("#guildNotice"), "");
    dialog.showModal();
    sendMovement(true);
  }
  const own = room.players.find((p) => p.id === room.you);
  const taken = new Set(room.players.filter((p) => p.id !== room.you).map((p) => p.class));
  const preview = room.guildPreview;
  const signature = JSON.stringify([room.code, preview]);
  if (signature !== lastGuildSignature) {
    lastGuildSignature = signature;
    guildSelected = preview ? preview.selected.slice() : [];
  }
  $("#guildTitle").textContent = preview ? "Become a " + preview.class : "Choose a new hero";
  $("#guildIntro").textContent = room.classChangeUsed ? "You have already changed class once this run. The Guildmaster cannot change it again." :
    preview ? "Your hero's six skills are shuffled. Choose one Light, one Special, and one Ultimate. Confirming uses your only class change this run." :
    "Change class once per run. Your current hero and heroes taken by teammates are off limits. You can back out without using your change.";
  $("#guildHeroes").classList.toggle("hidden", Boolean(preview));
  $("#guildSkills").classList.toggle("hidden", !preview);
  const heroes = $("#guildHeroes");
  if (!heroes.children.length) {
    CLASS_ORDER.forEach((name) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "class-card";
      button.dataset.guildClass = name;
      button.innerHTML = '<span class="class-icon"></span><span class="class-name"></span><span class="class-role"></span><span class="taken"></span>';
      button.addEventListener("click", () => guildAction("guildPreview", { class: name }));
      heroes.append(button);
    });
  }
  [...heroes.children].forEach((button) => {
    const name = button.dataset.guildClass;
    const info = room.classes[name];
    button.style.setProperty("--class-color", info.color);
    decorateHeroIcon(button.querySelector(".class-icon"), name);
    button.querySelector(".class-name").textContent = name;
    button.querySelector(".class-role").textContent = info.role;
    button.querySelector(".taken").textContent = own?.class === name ? "CURRENT HERO" : taken.has(name) ? "TAKEN" : "";
    button.disabled = guildBusy || room.classChangeUsed || own?.class === name || taken.has(name);
  });
  const choices = $("#guildAbilityChoices");
  const optionsSignature = JSON.stringify(preview?.options);
  if (choices.dataset.options !== optionsSignature) {
    choices.dataset.options = optionsSignature;
    choices.replaceChildren();
    (preview?.options || []).forEach((ability) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "ability-choice category-" + ability.attackType;
      button.dataset.guildAbility = ability.id;
      button.innerHTML = '<b></b><span></span><small></small>';
      button.querySelector("b").textContent = ability.attackType.toUpperCase() + " · " + ability.name;
      button.querySelector("span").textContent = ability.description;
      button.querySelector("small").textContent = ability.cooldown + (ability.kind === "summon" ? "s recharge after death" : "s cooldown") + " · " + ability.manaCost + " MP";
      choices.append(button);
    });
  }
  [...choices.children].forEach((button) => {
    const selected = guildSelected.includes(button.dataset.guildAbility);
    button.classList.toggle("selected", selected);
    button.setAttribute("aria-pressed", String(selected));
    button.disabled = guildBusy;
  });
  $("#guildConfirm").disabled = guildBusy || room.classChangeUsed || !preview || taken.has(preview.class) || guildSelected.length !== 3;
  $("#guildBack").disabled = guildBusy;
  $("#guildCancel").disabled = guildBusy;
}
function renderAbilityChoices(room) {
  const mine = room.players.find((player) => player.id === room.you);
  const panel = $("#abilityLoadout");
  const className = mine && mine.class;
  panel.classList.toggle("hidden", room.phase !== "lobby" || !className);
  const options = className ? room.abilityOptions[className] || [] : [];
  const signature = JSON.stringify([className, options, room.selectedAbilities, room.phase]);
  if (signature === lastLoadoutSignature) return;
  lastLoadoutSignature = signature;
  const choices = $("#abilityChoices");
  choices.replaceChildren();
  options.forEach((ability) => {
    const selected = room.selectedAbilities.includes(ability.id);
    const button = document.createElement("button");
    button.className = "ability-choice" + (selected ? " selected" : "") + " category-" + ability.attackType;
    button.dataset.ability = ability.id;
    button.setAttribute("aria-pressed", String(selected));
    button.innerHTML = '<b></b><span></span><small></small>';
    button.querySelector("b").textContent = ability.attackType.toUpperCase() + " · " + ability.name + (selected ? " · EQUIPPED" : "");
    button.querySelector("span").textContent = ability.description;
    button.querySelector("small").textContent = ability.attackType === "light" ? "Left click · " + ability.cooldown + "s cooldown" :
      String(keyBindings[ability.attackType]).toUpperCase() + " · " + ability.cooldown + (ability.kind === "summon" ? "s recharge after death" : "s cooldown") + (ability.manaCost ? " · " + ability.manaCost + " MP" : "");
    choices.append(button);
  });
  $("#abilityNotice").textContent = (room.selectedAbilities.length || 0) + " of 3 selected. Choose one Light, one Special, and one Ultimate.";
}
function renderAbilityBar(room) {
  const bar = $("#abilityButtons");
  const own = room.players.find((player) => player.id === room.you);
  const signature = JSON.stringify([room.abilitySlots, room.phase, room.waveCountdown, own && own.status,
    room.abilitySlots.map((ability) => room.mana >= ability.manaCost)]);
  if (signature === lastAbilityBarSignature) return;
  lastAbilityBarSignature = signature;
  bar.replaceChildren();
  bar.classList.toggle("hidden", room.phase !== "combat" || !room.abilitySlots.length);
  room.abilitySlots.filter((ability) => ability.attackType !== "light").forEach((ability) => {
    const button = document.createElement("button");
    button.className = "secondary ability-key";
    button.dataset.abilitySlot = String(room.abilitySlots.indexOf(ability) + 1);
    button.title = ability.description;
    const name = document.createElement("span"); name.className = "ability-name"; name.textContent = ability.name;
    const status = document.createElement("small"); status.textContent = String(keyBindings[ability.attackType]).toUpperCase() + " · " +
      (ability.summonAlive ? "Alive" : ability.cooldownLeft ? ability.cooldownLeft + "s" : "Ready") + " · " + ability.manaCost + " MP";
    button.append(name, status);
    button.disabled = room.phase !== "combat" || Boolean(room.waveCountdown) || !own || own.status !== "alive" || ability.summonAlive || ability.cooldownLeft > 0 || room.mana < ability.manaCost;
    bar.append(button);
  });
}
function renderClasses(room) {
  const grid = $("#classGrid");
  const taken = new Set(room.players.filter((player) => player.class && player.id !== room.you).map((player) => player.class));
  const mine = room.players.find((player) => player.id === room.you);
  const signature = JSON.stringify([room.phase, room.players.map((player) => [player.id, player.class]), room.classes]);
  if (signature !== lastClassSignature) {
    lastClassSignature = signature;
    grid.replaceChildren();
    CLASS_ORDER.forEach((name) => {
      const info = room.classes[name];
      const button = document.createElement("button");
      button.className = "class-card" + (mine && mine.class === name ? " selected" : "");
      button.disabled = room.phase !== "lobby" || (taken.has(name) && (!mine || mine.class !== name));
      button.style.setProperty("--class-color", info.color);
      button.innerHTML = '<span class="class-icon"></span><span class="class-name"></span><span class="class-role"></span>' +
        (taken.has(name) && (!mine || mine.class !== name) ? '<span class="taken">TAKEN</span>' : "");
      decorateHeroIcon(button.querySelector(".class-icon"), name);
      button.setAttribute("aria-pressed", String(Boolean(mine && mine.class === name)));
      button.querySelector(".class-name").textContent = name;
      button.querySelector(".class-role").textContent = info.role;
      button.addEventListener("click", () => chooseClass(name));
      grid.append(button);
    });
  }
  grid.classList.toggle("locked", room.phase !== "lobby");
  renderAbilityChoices(room);
  if (!runOptionsBusy) {
    $("#difficultyChoice").value = room.difficulty || "medium";
    $('#lengthChoice').value=String(room.totalStages || 25);
    $("#npcCompanion").checked = Boolean(room.npcCompanion);
  }
  $("#runOptions").disabled = room.phase !== "lobby" || room.you !== room.host || runOptionsBusy;
  $('#testerModeHint').classList.toggle('hidden',!room.testerMode);
}
function renderPlayers(room) {
  const list = $("#players");
  const signature = JSON.stringify([room.phase, room.host, room.you, room.players.map((player) =>
    [player.id, player.name, player.class, player.hp, player.maxHp, player.status, player.reviving, player.abilityCount])]);
  if (list.dataset.signature === signature) return;
  list.dataset.signature = signature;
  $("#partyCount").textContent = room.players.length + " / 4";
  list.replaceChildren();
  room.players.forEach((player) => {
    const item = document.createElement("div");
    item.className = "player-card" + (player.status !== "alive" ? " downed-card" : "");
    item.innerHTML = '<span class="player-dot"></span><span class="player-info"><b class="player-name"></b><small class="player-class"></small></span><span class="player-health"></span>';
    item.querySelector(".player-dot").style.background = player.color;
    decorateHeroIcon(item.querySelector(".player-dot"), player.class);
    item.querySelector(".player-name").textContent = player.name + (player.bot ? " · NPC" : player.id === room.host ? " · host" : "");
    item.querySelector(".player-class").textContent = player.reviving ? "Reviving an ally…" : !player.class ? (player.bot ? "Random hero on start" : "Choosing class") : player.abilityCount === 3 ? player.class + " · ready" : player.class + " · abilities " + player.abilityCount + "/3";
    item.querySelector(".player-health").textContent = player.class ? (player.status === "alive" ? player.hp + "/" + player.maxHp + " HP" : player.status.toUpperCase()) : "";
    list.append(item);
  });
  const own = room.players.find((player) => player.id === room.you);
  const ready = room.players.length > 0 && room.players.every((player) => player.bot || (player.class && player.abilityCount === 3));
  const start = $("#startRun");
  start.disabled = room.you !== room.host || !ready || room.phase !== "lobby";
  start.textContent = room.phase !== "lobby" ? "Run in progress" : room.you !== room.host ? "Waiting for host" : ready ? "Begin the run" : own && own.class && own.abilityCount !== 3 ? "Choose one of each ability" : own && own.class ? "Waiting for party loadouts" : "Choose a class to begin";
}
function renderChat(room) {
  const signature = room.chat.map((message) => message.id).join("|");
  if (signature === lastChatSignature) return;
  lastChatSignature = signature;
  const box = $("#chatMessages");
  box.replaceChildren();
  room.chat.forEach((message) => {
    const line = document.createElement("div");
    line.className = message.player === "system" ? "chat-line system-line" : "chat-line";
    const author = document.createElement("b");
    author.textContent = message.name;
    const body = document.createElement("span");
    body.textContent = message.message;
    line.append(author, body);
    box.append(line);
  });
  box.scrollTop = box.scrollHeight;
}
function renderRoom(room, roundTrip = 0) {
  window.GauntletAudio?.observe(room);
  // Repair notices still arriving from a process started before the UTF-8 fix.
  if (room.privateNotice) room.privateNotice=room.privateNotice.replace(/\u00e2\u20ac\u201d/g,'—');
  localMotion.remember(currentMovement(), performance.now());
  localMotion.update(room, performance.now(), roundTrip);
  inputSequence = Math.max(inputSequence, room.movement?.sequence || 0);
  updateMotionTracks(room);
  latestRoom = room;
  if (!room.enemies.some(e=>e.id===localTarget)) localTarget=null;
  $('#targetButton').classList.toggle('hidden',room.phase!=='combat');
  $('#targetButton').textContent=localTarget?'Clear target':'Auto target';
  $('#targetButton').disabled=!localTarget;
  const objective=room.objective;
  $('#objectiveHUD').classList.toggle('hidden',!objective);
  $('#objectiveHUD').textContent=objective ? (objective.kind==='ward' ? 'Protect the ward · '+objective.remaining+'s · '+objective.ward.hp+'/'+objective.ward.maxHp+' HP' : objective.kind==='rift' ? 'Destroy the rift · stop reinforcements' : 'Bait charges into rocks · counterattack') : '';
  if (typeof renderCoordination === "function") renderCoordination(room);
  renderGuild(room);
  if (typeof renderProgression === "function") renderProgression(room);
  sendMovement(false);
  notice($("#roomNotice"), "");
  $("#connection").textContent = "SYNCED";
  $("#connection").className = "connection online";
  renderClasses(room);
  renderPlayers(room);
  renderAbilityBar(room);
  renderWorldToast(room);
  renderQuickPouch(room);
  renderUtilityHotbar(room);
  renderChat(room);
  const active = room.phase !== "lobby";
  document.body.classList.toggle("is-playing", active);
  $("#arenaPanel").classList.toggle("hidden", !active);
  $("#classPanel").classList.toggle("hidden", active);
  const regionLabel = ({ woodland: "Woodland", ruins: "Ruins", cavern: "Cavern", frost: "Frostlands" })[room.region] || "Gauntlet";
  const stageLabel = room.testerMode ? "Tester " + room.stage + "/9" : "Stage " + room.stage;
  const title = room.phase === "peace" ? "A wounded hunter" : room.phase === "town" ? room.town + (room.innFloor === 2 ? " · Guest rooms" : "") :
    room.phase === "routes" ? stageLabel + " · Fork in the road" :
    room.phase === "puzzle" ? stageLabel + " · Rune chamber" :
    room.phase === "chest" ? stageLabel + " · Treasure" :
    room.phase === "stage_exit" ? stageLabel + " · Cleared" :
    room.phase === "defeat" ? stageLabel + " · Defeat" :
    room.phase === "cleared" ? "The Gauntlet · Victory" :
    room.encounterType === "large_boss" ? (room.testerMode ? stageLabel+" · " : "")+room.encounterName :
    room.encounterType === "mini_boss" ? (room.testerMode ? stageLabel+" · " : "")+"Mini-Boss · " + room.encounterName :
    room.assassinationActive ? stageLabel + " · ASSASSINATION ATTEMPT" :
    stageLabel + " · " + regionLabel + " · Wave " + room.stageWave + " / " + room.stageWaves;
  $("#stageHeading").textContent = title;
  const bossTactic = $('#bossTactic');
  bossTactic.classList.toggle('hidden', !room.bossIntel);
  bossTactic.textContent = room.bossIntel ? room.bossIntel.phaseLabel+' · '+room.bossIntel.tactic : '';
  bossTactic.title = room.bossIntel?.phaseTwoHint || '';
  $("#runeCount").textContent = room.runes + " RUNES";
  const own = room.players.find((player) => player.id === room.you);
  $("#hpLabel").textContent = own ? "HP " + own.hp + " / " + own.maxHp : "HP";
  $("#hpFill").style.width = own && own.maxHp ? Math.max(0, Math.min(100, own.hp / own.maxHp * 100)) + "%" : "0%";
  $('.health-meter').classList.toggle('health-critical',Boolean(own && own.hp/own.maxHp<.3));
  $("#manaLabel").textContent = "MANA " + Math.floor(room.mana) + " / " + room.maxMana;
  $("#manaFill").style.width = Math.max(0, Math.min(100, room.mana / room.maxMana * 100)) + "%";
  $("#waveCountdown").classList.toggle("hidden", !room.waveCountdown || room.phase !== "combat");
  $("#waveCountdown").textContent = room.waveCountdown ? "WAVE " + room.stageWave + " IN " + room.waveCountdown : "";
  $(".hud-actions").classList.toggle("hidden", ["lobby", "defeat", "cleared"].includes(room.phase));
  $("#attackButton").classList.toggle("hidden", room.phase !== "combat");
  $("#attackButton").disabled = room.phase !== "combat" || Boolean(room.waveCountdown);
  $("#dashButton").classList.toggle("hidden", room.phase !== "combat");
  $("#dashButton").disabled = room.phase !== "combat" || Boolean(room.dashCooldown);
  $("#dashButton").textContent = room.dashCooldown ? "Dash · " + room.dashCooldown + "s" : "Space · Dash";
  $("#reviveButton").classList.toggle("hidden", room.phase !== "combat");
  const interactive = ["town", "puzzle", "chest", "peace"].includes(room.phase);
  $("#interactButton").classList.toggle("hidden", !interactive);
  const lockedVillageGate = room.phase === "town" && !room.townInterior && room.nearbyNpc?.id === "gate" && room.firstTownTrainingRequired;
  $("#interactButton").disabled = Boolean(room.movementLocked || lockedVillageGate);
  if (room.phase === "peace") $("#interactButton").textContent = room.nearbyNpc ? "E · Talk to wounded hunter" : "Find the wounded hunter";
  else if (room.phase === "chest") $("#interactButton").textContent = room.chestStatus === "nearby" ? "E · Open chest" : "Find the chest";
  else if (room.phase === "routes") $("#interactButton").textContent = room.nearRoute ? "E · Take " + room.nearRoute.name : "Find a path";
  else if (room.phase === "town") {
    if (room.townInterior) $("#interactButton").textContent = room.nearbyHouse ? "E · Return to town" : room.nearbyNpc ? "E · " + room.nearbyNpc.name : "Explore the building";
    else if (room.nearbyHouse) $("#interactButton").textContent = "E · Enter " + room.nearbyHouse.name;
    else if (lockedVillageGate) $("#interactButton").textContent = "Visit the innkeeper first";
    else if (room.nearbyNpc && room.nearbyNpc.id === "gate") $("#interactButton").textContent = (room.players.find((p) => p.id === room.you)?.townExitReady ? "E · Cancel exit vote" : "E · Vote to leave") + " · " + room.townExitVotes + "/" + room.townExitTotal;
    else if (room.nearbyNpc) $("#interactButton").textContent = "E · Talk to " + room.nearbyNpc.name;
    else $("#interactButton").textContent = "Explore town";
  }
  else if (room.phase === "puzzle") $("#interactButton").textContent = room.puzzle && room.puzzle.atTotem ? "E · Read totem" : "Find your totem";
  const townActive = room.phase === "town";
  const chestActive = room.phase === "chest";
  const defeatActive = room.phase === "defeat";
  const victoryActive = room.phase === "cleared";
  if (!chestActive) lastChestSignature = "";
  $("#townPanel").classList.toggle("hidden", !townActive || room.townInteraction !== "merchant");
  $("#chestPanel").classList.toggle("hidden", !chestActive || room.chestStatus !== "pending");
  $("#defeatPanel").classList.toggle("hidden", !defeatActive || !room.canResumeAtCheckpoint);
  $("#victoryPanel").classList.toggle("hidden", !victoryActive);
  if (townActive) renderTown(room);
  if (chestActive && room.chestStatus === "pending") renderChest(room);
  $("#checkpointResume").classList.toggle("hidden", !defeatActive || !room.canResumeAtCheckpoint || room.you !== room.host);
  const routeActive = room.phase === "routes";
  const puzzleActive = room.phase === "puzzle";
  $("#world").classList.remove("hidden");
  if (!puzzleActive) {
    clearTimeout(puzzleDialogueTimer);
    $("#puzzlePanel").classList.add("hidden");
    lastPuzzleId = "";
    lastPuzzleClue = "";
  }
  $(".arena-controls").classList.toggle("hidden", defeatActive || victoryActive);
  if (puzzleActive) renderPuzzle(room);
  if (room.phase === "combat" && Date.now() > combatNoticeUntil) notice($("#combatNotice"), "");
  else if (room.phase === "routes") notice($("#combatNotice"), room.yourRouteVote ? "Waiting at the trail edge. Everyone must reach a left or right exit." : "Follow the fork left or right, then walk all the way to the screen edge to choose.");
  else if (room.phase === "stage_exit") notice($("#combatNotice"), "↑ " + room.stageExitReady + " / " + (room.activeVoterCount ?? room.activePartySize ?? room.players.length));
  else if (room.phase === "chest") notice($("#combatNotice"), room.chestStatus === "nearby" ? "Press " + String(keyBindings.revive).toUpperCase() + " to open the chest." : "Walk to the chest in the center and press " + String(keyBindings.revive).toUpperCase() + ".");
  else if (room.phase === "town") notice($("#combatNotice"), lockedVillageGate ? "Every present hunter must speak to the innkeeper before leaving this village." : room.townInterior ? (room.nearbyHouse ? "Press E at the door to return to the village." : room.nearbyNpc ? "Press E to interact with " + room.nearbyNpc.name + "." : room.innFloor === 2 ? "Rest at a bed in an unlocked room to set the party checkpoint." : "Find the shopkeeper inside, or return through the door.") : room.nearbyHouse ? "Press E to enter " + room.nearbyHouse.name + "." : room.nearbyNpc && room.nearbyNpc.id === "gate" ? "Gather at the exit and press E to vote. Everyone must be ready." : room.firstTownTrainingRequired ? "Speak to the innkeeper to discover hunter training. Rest upstairs to save your run." : "Visit the Inn, Store, Alchemy Lab, or Guild. Gather at the south gate when everyone is ready to leave.");
  else if (room.phase === "peace") notice($("#combatNotice"), room.questAccepted ? "Quest accepted · gather at the northern exit." : "Speak to the wounded hunter beside the road.");
  else if (room.phase === "puzzle") notice($("#combatNotice"), room.puzzle?.cooperative ? "Your totem holds a teammate's answer. Share clues, then choose your runes together." : "Find your totem, then stand on the rune it describes.");
}
function updateMotionTracks(room) {
  window.GauntletCombatEnvironment?.observe(room);
  const scene = [room.code, room.stage, room.phase, room.townInterior, room.innFloor, room.puzzle?.id].join(":");
  const now = performance.now();
  if (room.code !== damageRoom) { damageTracks.clear(); damageRoom = room.code; }
  if (scene !== motionScene) { motionTracks.clear(); lastSnapshotAt = 0; motionScene = scene; lastSentMove = ""; }
  const duration = lastSnapshotAt ? Math.max(50, Math.min(180, now - lastSnapshotAt)) : 100;
  const active = new Set();
  for (const [group, entities] of [["player", room.players], ["enemy", room.enemies], ["summon", room.summons || []], ["projectile", room.projectiles || []]]) {
    for (const entity of entities) {
      const key = group + ":" + entity.id;
      active.add(key);
      if (group !== "projectile") {
        const previousDamage = damageTracks.get(key);
        const hit = previousDamage && (entity.damageTaken > previousDamage.damageTaken ||
          (entity.maxHp === previousDamage.maxHp && entity.hp < previousDamage.hp && ["combat", "defeat"].includes(room.phase)));
        damageTracks.set(key, { hp: entity.hp, maxHp: entity.maxHp, damageTaken: entity.damageTaken,
          until: hit ? now + DAMAGE_FLASH_MS : previousDamage?.until || 0 });
      }
      const previous = motionTracks.get(key);
      const position = previous ? interpolatedPosition(previous, now) : entity;
      const snap = !previous || Math.hypot(entity.x - position.x, entity.y - position.y) > 120;
      motionTracks.set(key, { x: snap ? entity.x : position.x, y: snap ? entity.y : position.y,
        targetX: entity.x, targetY: entity.y, start: now, duration });
    }
  }
  for (const key of motionTracks.keys()) if (!active.has(key)) motionTracks.delete(key);
  for (const key of damageTracks.keys()) if (!active.has(key)) damageTracks.delete(key);
  lastSnapshotAt = now;
}
function interpolatedPosition(track, now) {
  const fraction = Math.max(0, Math.min(1, (now - track.start) / track.duration));
  return { x: track.x + (track.targetX - track.x) * fraction, y: track.y + (track.targetY - track.y) * fraction };
}
function animateWorld(now) {
  if (latestRoom && latestRoom.phase !== "lobby" && !document.hidden) {
    const direction = currentMovement();
    localMotion.remember(direction, now);
    sendMovement(false);
    const smooth = (group, entities) => entities.map((entity) => {
      if (group === 'player' && entity.id === latestRoom.you) {
        const position = localMotion.position(latestRoom, now);
        if (position) return { ...entity, ...position, moving: entity.status === 'alive' && Boolean(direction.x || direction.y),
          facingX: direction.x || direction.y ? direction.x : entity.facingX,
          facingY: direction.x || direction.y ? direction.y : entity.facingY };
      }
      const track = motionTracks.get(group + ":" + entity.id);
      return track ? { ...entity, ...interpolatedPosition(track, now) } : entity;
    });
    drawWorld({ ...latestRoom, players: smooth("player", latestRoom.players),
      enemies: smooth("enemy", latestRoom.enemies), summons: smooth("summon", latestRoom.summons || []), projectiles: smooth("projectile", latestRoom.projectiles || []) });
  }
  requestAnimationFrame(animateWorld);
}
requestAnimationFrame(animateWorld);
function renderChest(room) {
  const signature = JSON.stringify([room.chestStatus, room.chestDecision, room.chestOpenedCount, room.chestTotal, room.chestReward, room.inventory, room.runes]);
  if (signature === lastChestSignature) return;
  lastChestSignature = signature;
  const pending = room.chestStatus === "pending";
  const done = room.chestStatus === "done";
  $("#pendingChestLoot").classList.toggle("hidden", !pending);
  $("#chestWait").classList.toggle("hidden", !done);
  $("#chestWait").textContent = "You opened your share. Waiting for the rest of the party.";
  $("#chestProgress").textContent = room.chestOpenedCount + " / " + room.chestTotal + " adventurers have opened their share.";
  if (!pending) return;
  $("#pendingChestName").textContent = room.chestReward.name + " · " + room.chestReward.rarity;
  decorateItemLabel($("#pendingChestName"), room.chestReward);
  $("#pendingChestDesc").textContent = room.chestReward.description;
  const choices = $("#chestSwapChoices");
  choices.replaceChildren();
  room.inventory.forEach((item) => {
    const button = document.createElement("button");
    button.className = "secondary";
    button.dataset.chestSwap = item.id;
    button.textContent = "Swap out " + item.name + " and sell for " + item.sell + " Runes";
    decorateItemLabel(button, item);
    choices.append(button);
  });
}
function renderQuickPouch(room) {
  const pouch = $("#quickPouch");
  const gearPanel = $("#quickGear");
  const own = room.players.find((player) => player.id === room.you);
  if (room.privateNotice) { lastPrivateNotice = room.privateNotice; privateNoticeUntil = Date.now() + 6000; }
  const privateNotice = Date.now() < privateNoticeUntil ? lastPrivateNotice : "";
  const curseText = room.curse ? "CURSED · " + room.curse.name + " · " + room.curse.remainingStages + " combat/puzzle stages remain. " + room.curse.description + " Towns pause the timer." : privateNotice;
  const manaUsable = room.mana < room.maxMana;
  const signature = JSON.stringify([room.inventory, room.utilitySlots, room.toolSlots, room.phase, room.abilitySlots, own && own.hp, manaUsable, room.curse, curseText]);
  if (signature === pouch.dataset.signature) return;
  pouch.dataset.signature = signature;
  pouch.replaceChildren();
  $("#pouchCount").textContent = room.inventory.length + " / " + (room.pouchCapacity || 10);
  const curseStatus = $("#curseStatus");
  curseStatus.replaceChildren();
  if (room.curse && ["sluggish", "frail", "weakened"].includes(room.curse.effect)) {
    const image = document.createElement("img");
    image.src = "/sprites/curse-" + room.curse.effect + "-v1.png";
    image.alt = ""; image.width = image.height = 64; image.className = "curse-sprite";
    image.setAttribute("aria-hidden", "true"); image.draggable = false;
    image.addEventListener("error", () => image.remove(), { once: true });
    curseStatus.append(image);
  }
  const curseLabel = document.createElement("span"); curseLabel.textContent = curseText;
  curseStatus.append(curseLabel);
  $("#curseStatus").classList.toggle("hidden", !curseText);
  $("#pouchPanel").classList.toggle("hidden", room.phase === "lobby");
  room.inventory.forEach((item) => {
    const row = document.createElement("div");
    row.className = "quick-item";
    const label = document.createElement("span");
    label.textContent = item.name + " · " + item.rarity;
    decorateItemLabel(label, item);
    const controls = document.createElement("div");
    controls.className = "quick-item-actions";
    if (item.slot === "utility") {
      const use = document.createElement("button");
      use.className = "secondary"; use.dataset.useItem = item.id;
      use.textContent = item.kind === "hint" ? "Use" : "Use";
      use.disabled = !canUseUtility(room, item, own);
      controls.append(use);
      room.utilitySlots.forEach((equipped, index) => {
        const equip = document.createElement("button");
        equip.className = "secondary"; equip.dataset.equipItem = item.id; equip.dataset.equipSlot = String(index);
        equip.textContent = "U" + (index + 1);
        equip.setAttribute("aria-label", "Utility " + (index + 1));
        equip.title = equipped ? "Swap with " + equipped.name : "Equip in utility slot " + (index + 1);
        controls.append(equip);
      });
    } else if (item.slot === "tool") {
      room.toolSlots.forEach((equipped, index) => {
        const equip = document.createElement("button");
        equip.className = "secondary"; equip.dataset.equipItem = item.id; equip.dataset.equipSlot = String(index);
        equip.textContent = "Tool " + (index + 1);
        equip.title = window.GauntletEquipment?.compare(item, room.toolSlots, index).detail || (equipped ? 'Swap with '+equipped.name : 'Empty slot');
        controls.append(equip);
      });
    }
    const description = document.createElement("p");
    description.className = "pouch-item-description";
    description.textContent = item.description || "";
    row.append(label, description, controls);
    appendEquipmentComparison(row, item, room);
    pouch.append(row);
  });
  if (!room.inventory.length) {
    const empty = document.createElement("p"); empty.className = "pouch-empty";
    empty.textContent = "No carried items."; pouch.append(empty);
  }
  gearPanel.replaceChildren();
  [[room.utilitySlots, "utility"], [room.toolSlots, "tool"]].forEach(([slots, slotKind]) => {
    slots.forEach((item, index) => {
      const slot = document.createElement("div");
      slot.className = "quick-gear-slot";
      slot.classList.toggle("empty-slot", !item);
      const caption = document.createElement("small"); caption.className = "gear-caption";
      caption.textContent = (slotKind === "utility" ? "Utility" : "Tool") + " " + (index + 1);
      const label = document.createElement("span");
      label.textContent = item ? item.name : "Empty";
      if (item) decorateItemLabel(label, item);
      slot.append(caption, label);
      if (item) {
        const description = document.createElement("p");
        description.className = "pouch-item-description";
        description.textContent = item.description || "";
        slot.append(description);
        const remove = document.createElement("button");
        remove.className = "secondary"; remove.dataset.unequip = "1";
        remove.dataset.slotKind = slotKind; remove.dataset.slot = String(index);
        remove.textContent = "Unequip"; remove.disabled = room.inventory.length >= (room.pouchCapacity || 10);
        slot.append(remove);
      }
      gearPanel.append(slot);
    });
  });
  const curse = document.createElement('div');
  curse.id = 'curseSlot'; curse.className = 'quick-gear-slot curse-slot';
  curse.classList.toggle('empty-slot', !room.curse);
  const caption = document.createElement('small'); caption.className = 'gear-caption'; caption.textContent = 'Curse';
  const label = document.createElement('span'); label.className = 'item-label';
  const icon = document.createElement('span'); icon.className = 'curse-sprite-placeholder'; icon.setAttribute('aria-hidden','true');
  icon.textContent = room.curse ? '☠' : '◇';
  let image=null;
  if (['sluggish','weakened','frail'].includes(room.curse?.effect)) {
    image=document.createElement('img');image.className='item-sprite';image.alt='';image.setAttribute('aria-hidden','true');
    image.src='/sprites/curse-'+room.curse.effect+'-v1.png';image.width=image.height=64;image.draggable=false;
    image.addEventListener('error',()=>image.replaceWith(icon),{once:true});
  }
  label.append(image || icon);
  const name = document.createElement('span'); name.className = 'item-title-text'; name.textContent = room.curse?.name || 'No curse'; label.append(name);
  const duration = document.createElement('small'); duration.className = 'curse-duration';
  duration.textContent = room.curse ? room.curse.remainingStages + ' stages left' : 'Separate from pouch capacity';
  curse.append(caption,label,duration);
  curse.title=room.curse ? room.curse.name+' · '+room.curse.description+' · '+room.curse.remainingStages+' stages left' : 'No active curse';
  if (room.curse) {
    const description = document.createElement('p'); description.className = 'pouch-item-description';
    description.textContent = room.curse.description + ' Fades naturally; cannot be unequipped.'; curse.append(description);
  }
  gearPanel.append(curse);
}
function canUseUtility(room, item, own) {
  if (!item || !own || own.status !== "alive") return false;
  if (item.kind === "hint") return room.phase === "routes";
  if (item.kind === "heal") return ["combat", "town"].includes(room.phase) && own.hp < own.maxHp;
  if (item.kind === "mana") return ["combat", "town"].includes(room.phase) && room.mana < room.maxMana;
  return ["ward", "buff", "speed", "arrows"].includes(item.kind) && room.phase === "combat";
}
function renderUtilityHotbar(room) {
  const hotbar = $("#utilityHotbar");
  const own = room.players.find((player) => player.id === room.you);
  const signature = JSON.stringify([room.utilitySlots, room.phase, own && own.status, own && own.hp, room.mana >= room.maxMana]);
  if (signature === hotbar.dataset.signature) return;
  hotbar.dataset.signature = signature;
  $("#utilityLeft").replaceChildren(); $("#utilityRight").replaceChildren();
  const icons = { heal: "✚", mana: "✦", ward: "⬡", hint: "⌕", buff: "⚔", speed: "➤", arrows: "➶" };
  room.utilitySlots.forEach((item, index) => {
    const button = document.createElement("button");
    button.className = "utility-slot";
    button.setAttribute("aria-label", "Utility " + (index + 1) + ": " + (item ? item.name : "empty"));
    button.disabled = !item || !canUseUtility(room, item, own);
    if (item) {
      button.dataset.useItem = item.id;
      button.title = item.name + " · " + item.description;
      button.innerHTML = '<span class="utility-key"></span><span class="utility-icon"></span><span class="utility-name"></span>';
      button.querySelector(".utility-key").textContent = String(index + 1);
      button.querySelector(".utility-icon").textContent = icons[item.kind] || "✦";
      const image = createItemSprite(item);
      if (image) {
        const holder = button.querySelector(".utility-icon");
        holder.replaceChildren(image);
        image.addEventListener("error", () => { holder.textContent = icons[item.kind] || "✦"; }, { once: true });
      }
      button.querySelector(".utility-name").textContent = item.name;
    } else {
      button.innerHTML = '<span class="utility-key"></span><span class="utility-name">Empty</span>';
      button.querySelector(".utility-key").textContent = String(index + 1);
    }
    (index === 0 ? $("#utilityLeft") : $("#utilityRight")).append(button);
  });
}
function renderRoutes(room) {
  const signature = JSON.stringify([room.routes, room.inventory, room.utilitySlots, room.yourRouteVote]);
  if (signature === lastRouteSignature) return;
  lastRouteSignature = signature;
  const choices = $("#routeChoices");
  choices.replaceChildren();
  const alreadyVoted = Boolean(room.yourRouteVote);
  room.routes.forEach((route) => {
    const button = document.createElement("button");
    button.className = "route-choice" + (room.yourRouteVote === route.id ? " selected" : "");
    button.dataset.route = route.id;
    button.disabled = alreadyVoted;
    const title = document.createElement("b");
    title.textContent = route.name;
    const kind = document.createElement("span");
    kind.textContent = route.easier ? "CLEAR ANSWER: EASIER PATH" : (route.kind === "puzzle" ? "Separated clue puzzle" : (route.kind === "town" ? "Peaceful town and inn checkpoint" : "Enemy gauntlet"));
    const votes = document.createElement("small");
    votes.textContent = route.votes + (route.votes === 1 ? " vote" : " votes");
    button.append(title, kind, votes);
    choices.append(button);
  });
  $("#routeNotice").textContent = alreadyVoted ? "Your vote is in. Waiting for the rest of the party…" : "Choose one path. The party proceeds when everyone has voted.";
  const lenses = $("#routeHintItems");
  lenses.replaceChildren();
  room.inventory.concat(room.utilitySlots.filter(Boolean)).filter((item) => item.kind === "hint").forEach((item) => {
    const button = document.createElement("button");
    button.className = "secondary route-lens-use";
    button.dataset.useRoute = item.id;
    button.textContent = "Use " + item.name + " to reveal the easier path";
    decorateItemLabel(button, item);
    lenses.append(button);
  });
  if (!lenses.childElementCount) lenses.textContent = "A rare Pathfinder’s Lens can reveal which route is easier.";
}
function renderTown(room) {
  const signature = JSON.stringify([room.town, room.runes, room.inventory, room.utilitySlots, room.toolSlots, room.shopStock, room.you === room.host]);
  if (signature === lastTownSignature) return;
  lastTownSignature = signature;
  $("#townName").textContent = room.town + " · Inn & Market";
  const stock = $("#shopStock");
  stock.replaceChildren();
  room.shopStock.forEach((item) => {
    const card = document.createElement("div");
    card.className = "town-item";
    const details = document.createElement("div");
    details.innerHTML = '<b></b><small></small><span></span>';
    details.querySelector("b").textContent = item.name + " · " + item.rarity;
    details.querySelector("small").textContent = item.description;
    details.querySelector("span").textContent = item.price + " Runes";
    appendEquipmentComparison(details, item, room);
    decorateItemLabel(details.querySelector("b"), item);
    const buy = document.createElement("button");
    buy.className = "secondary";
    buy.dataset.buy = item.key;
    buy.textContent = "Buy";
    buy.disabled = room.runes < item.price || room.inventory.length >= (room.pouchCapacity || 10);
    card.append(details, buy);
    stock.append(card);
  });
  if (!room.shopStock.length) stock.textContent = "The merchant is sold out.";
  const pouch = $("#pouchItems");
  const own = room.players.find((player) => player.id === room.you);
  pouch.replaceChildren();
  room.inventory.forEach((item) => {
    const card = document.createElement("div");
    card.className = "town-item";
    const details = document.createElement("div");
    details.innerHTML = '<b></b><small></small><span></span>';
    details.querySelector("b").textContent = item.name + " · " + item.rarity;
    details.querySelector("small").textContent = item.description;
    details.querySelector("span").textContent = "Sell for " + item.sell + " Runes";
    appendEquipmentComparison(details, item, room);
    decorateItemLabel(details.querySelector("b"), item);
    const controls = document.createElement("div");
    controls.className = "item-actions";
    const sell = document.createElement("button");
    sell.className = "secondary"; sell.dataset.sell = item.id; sell.textContent = "Sell";
    const use = document.createElement("button");
    use.className = "secondary"; use.dataset.use = item.id; use.textContent = item.kind === "hint" ? "Use at fork" : item.kind === "ward" ? "Use in combat" : "Use";
    use.disabled = item.kind !== "heal" || !own || own.hp >= own.maxHp;
    controls.append(sell, use);
    const slotCount = item.slot === "utility" ? 3 : 2;
    for (let slot = 0; slot < slotCount; slot += 1) {
      const equip = document.createElement("button");
      equip.className = "secondary"; equip.dataset.equipItem = item.id; equip.dataset.equipSlot = String(slot);
      equip.textContent = (item.slot === "utility" ? "Utility " : "Tool ") + (slot + 1);
      controls.append(equip);
    }
    card.append(details, controls);
    pouch.append(card);
  });
  if (!room.inventory.length) pouch.textContent = "Your pouch is empty.";
  const equipment = $("#equipmentSlots");
  equipment.replaceChildren();
  [["Utility slots", room.utilitySlots, "utility"], ["Tool slots", room.toolSlots, "tool"]].forEach(([title, slots, slotKind]) => {
    const group = document.createElement("div");
    group.className = "equipment-group";
    const heading = document.createElement("b");
    heading.textContent = title;
    group.append(heading);
    slots.forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "equipment-slot";
      const label = document.createElement("span");
      label.textContent = (slotKind === "utility" ? "Utility " : "Tool ") + (index + 1) + ": " + (item ? item.name : "Empty");
      if (item) decorateItemLabel(label, item);
      row.append(label);
      if (item) {
        const remove = document.createElement("button");
        remove.className = "secondary"; remove.dataset.unequip = "1";
        remove.dataset.slotKind = slotKind; remove.dataset.slot = String(index); remove.textContent = "Unequip";
        row.append(remove);
      }
      group.append(row);
    });
    equipment.append(group);
  });
}
function showPuzzleDialogue() {
  clearTimeout(puzzleDialogueTimer);
  $("#puzzlePanel").classList.remove("hidden");
  puzzleDialogueTimer = setTimeout(() => {
    $("#puzzlePanel").classList.add("hidden");
  }, 3000);
}
async function interactWithWorld() {
  await sendAction("interact");
  if (latestRoom?.phase === "puzzle" && latestRoom.puzzle?.atTotem) showPuzzleDialogue();
  refresh();
}
function renderPuzzle(room) {
  const puzzle = room.puzzle;
  if (!puzzle) return;
  if (puzzle.id !== lastPuzzleId) {
    lastPuzzleId = puzzle.id;
    lastPuzzleClue = "";
    showPuzzleDialogue();
  }
  if (puzzle.clue && puzzle.clue !== lastPuzzleClue) {
    lastPuzzleClue = puzzle.clue;
    showPuzzleDialogue();
  }
  if (puzzle.standingRune) {
    clearTimeout(puzzleDialogueTimer);
    $("#puzzlePanel").classList.add("hidden");
  }
  const count = puzzle.partySize || room.players.length;
  $("#puzzlePath").textContent = "Rune chamber · " + count + " adventurer" + (count === 1 ? "" : "s");
  $("#puzzleClue").textContent = puzzle.clue ? "Clue for " + puzzle.clueForName + ": " + puzzle.clue :
    puzzle.cooperative ? "Find your totem for a teammate's clue. A teammate holds yours." : "Find the totem to learn which rune is yours.";
  $("#puzzleProgress").textContent = (puzzle.standingRune ? "Standing on " + puzzle.standingRune +
    (puzzle.cooperative ? " · Waiting for the group answer." : puzzle.isCorrect ? " · Correct!" : " · Try another rune.") : "Stand on the rune described by your clue.") + " On runes: " + puzzle.readyCount + " / " + count + ".";
  $("#companionClue").textContent = room.companionClue ? "Your companion’s clue for you: " + room.companionClue : "";
  $("#companionClue").classList.toggle("hidden", !room.companionClue);
  $("#puzzleNotice").textContent = puzzle.cooperative ? "Use Share clue to tell an NPC companion its answer, or party chat with teammates. The gate checks everyone's answer together." : "Solo chamber: your totem describes your own rune.";
}
function refresh() {
  if (polling || !session) return;
  polling = true;
  const requestedSession = session;
  const requestedAt = performance.now();
  api("/api/state?room=" + encodeURIComponent(session.room) + "&player=" + encodeURIComponent(session.player))
    .then((room) => { if (session === requestedSession) renderRoom(room, performance.now() - requestedAt); })
    .catch((error) => {
      if (session !== requestedSession) return;
      if (error.message === "Room or player not found.") {
        session = null;
        latestRoom = null;
        renderGuild(null);
        localStorage.removeItem("gauntlet-session");
        $("#lobby").classList.add("hidden");
        $("#entry").classList.remove("hidden");
        document.body.classList.remove("is-playing");
        $("#connection").textContent = "READY";
        $("#connection").className = "connection";
        notice($("#entryNotice"), "This run is unavailable. Runs survive a server restart after the first inn checkpoint. Create or join a room to start again.");
        notice($("#roomNotice"), "");
        return;
      }
      $("#connection").textContent = "DISCONNECTED";
      $("#connection").className = "connection offline";
      notice($("#roomNotice"), "Connection lost. Reconnecting automatically; saved runs resume at the latest inn after a server restart.");
      notice($("#combatNotice"), "Connection lost · reconnecting…");
    })
    .finally(() => { polling = false; setTimeout(refresh, Math.max(0, 50 - (performance.now() - requestedAt))); });
}
function currentMovement() {
  if (document.querySelector("dialog[open]") || latestRoom?.movementLocked) return { x: 0, y: 0, attack: false };
  let x = moveState.x, y = moveState.y;
  if (keys.has(String(keyBindings.left).toLowerCase()) || keys.has("arrowleft")) x -= 1;
  if (keys.has(String(keyBindings.right).toLowerCase()) || keys.has("arrowright")) x += 1;
  if (keys.has(String(keyBindings.up).toLowerCase()) || keys.has("arrowup")) y -= 1;
  if (keys.has(String(keyBindings.down).toLowerCase()) || keys.has("arrowdown")) y += 1;
  return { x: Math.max(-1, Math.min(1, x)), y: Math.max(-1, Math.min(1, y)), attack: moveState.attack || keys.has("attack") };
}
const keys = new Set();
function sendMovement(force) {
  if (!session || !latestRoom || !["combat", "town", "routes", "stage_exit", "puzzle", "chest", "peace"].includes(latestRoom.phase)) return;
  const now = performance.now();
  if (!force && now - lastInputSent < 90) return;
  const direction = currentMovement();
  localMotion.remember(direction, now);
  const signature = direction.x + "," + direction.y + "," + direction.attack;
  if (!force && signature === lastSentMove && now - lastInputSent < 500) return;
  lastInputSent = now;
  lastSentMove = signature;
  pendingInput = { session, direction:{...direction,targetId:localTarget} };
  flushMovement();
}
function flushMovement() {
  if (inputBusy || !pendingInput) return;
  const next = pendingInput; pendingInput = null;
  if (next.session !== session) return;
  inputBusy = true;
  api('/api/action', {room:session.room,player:session.player,action:'input',...next.direction,sequence:++inputSequence})
    .catch(() => {}).finally(() => {inputBusy=false;flushMovement();});
}
window.addEventListener("keydown", (event) => {
  if (!event.key) return;
  if (document.querySelector("dialog[open]")) return;
  const key = event.key.toLowerCase();
  if (bindingCapture) {
    event.preventDefault();
    if (/^[1-3]$/.test(key) || event.code === "Space") {
      notice($("#entryNotice"), "Space is reserved for dash; 1–3 are reserved for utilities.");
      return;
    }
    if ([...Object.entries(keyBindings)].some(([action, bound]) => action !== bindingCapture && String(bound).toLowerCase() === key)) {
      notice($("#entryNotice"), "Each action needs its own key. Choose another key.");
      return;
    }
    keyBindings[bindingCapture] = key;
    localStorage.setItem("gauntlet-keybindings", JSON.stringify(keyBindings));
    notice($("#entryNotice"), "Keybinding saved.");
    bindingCapture = null; renderKeyBindings();
    return;
  }
  if (event.target.closest("input,textarea,select")) return;
  if (latestRoom?.phase==='combat' && (key==='tab' || key==='escape')) {
    event.preventDefault();
    if (!event.repeat) {
      const list=latestRoom.enemies;
      chooseTarget(key==='escape' || !list.length ? null : list[(list.findIndex(e=>e.id===localTarget)+1)%list.length].id);
    }
    return;
  }
  if (/^[1-3]$/.test(key) || /^(Digit|Numpad)[1-3]$/.test(event.code)) {
    event.preventDefault();
    if (!event.repeat) triggerUtility(Number(/^(Digit|Numpad)[1-3]$/.test(event.code) ? event.code.slice(-1) : key) - 1);
    return;
  }
  if (event.code === "Space") {
    event.preventDefault();
    if (!event.repeat) triggerDash();
    return;
  }
  if (Object.values(keyBindings).some((bound) => String(bound).toLowerCase() === key) || ["arrowleft", "arrowright", "arrowup", "arrowdown"].includes(key)) event.preventDefault();
  if (key === String(keyBindings.special).toLowerCase()) { if (!event.repeat) triggerAbility("special"); return; }
  if (key === String(keyBindings.ultimate).toLowerCase()) { if (!event.repeat) triggerAbility("ultimate"); return; }
  if (key === String(keyBindings.revive).toLowerCase()) {
    if (!event.repeat) {
      if (latestRoom && latestRoom.phase === "combat") sendAction("revive").catch(() => {});
      else interactWithWorld().catch((error) => notice($("#combatNotice"), error.message));
    }
    return;
  }
  if (!event.repeat) { keys.add(key); sendMovement(true); }
});
window.addEventListener("keyup", (event) => {
  if (!event.key) return;
  const key = event.key.toLowerCase();
  keys.delete(key);
  if (key === String(keyBindings.revive).toLowerCase() && latestRoom && latestRoom.phase === "combat") sendAction("stopRevive").catch(() => {});
  sendMovement(true);
});
window.addEventListener("blur", () => { keys.clear(); moveState = { x: 0, y: 0, attack: false }; endHeldAttack(); sendAction("stopRevive").catch(() => {}); });
document.querySelectorAll("[data-move]").forEach((button) => {
  const vector = button.dataset.move.split(",").map(Number);
  const start = (event) => { event.preventDefault(); moveState.x = vector[0]; moveState.y = vector[1]; sendMovement(true); };
  const stop = (event) => { event.preventDefault(); moveState.x = moveState.y = 0; sendMovement(true); };
  button.addEventListener("pointerdown", start);
  button.addEventListener("pointerup", stop);
  button.addEventListener("pointerleave", stop);
  button.addEventListener("pointercancel", stop);
});
function drawRegionScenery(ctx, room, theme, w, h) {
  let seed = 2166136261;
  const seedText = [room.code, room.stage, room.region].join(":");
  for (let i = 0; i < seedText.length; i++) seed = Math.imul(seed ^ seedText.charCodeAt(i), 16777619);
  const random = () => { seed += 0x6D2B79F5; let n = seed; n = Math.imul(n ^ n >>> 15, n | 1); n ^= n + Math.imul(n ^ n >>> 7, n | 61); return ((n ^ n >>> 14) >>> 0) / 4294967296; };
  const region = room.region || "woodland";
  for (let i = 0; i < (region === "ruins" ? 18 : 16); i++) {
    let x = 34 + random() * (w - 68), y = 34 + random() * (h - 68);
    if (y < 150 || y > h - 145) x = random() < 0.5 ? 48 + random() * 90 : w - 138 + random() * 90;
    const size = 10 + Math.floor(random() * 13);
    if (region === "woodland") {
      ctx.fillStyle = "#49382b"; ctx.fillRect(x - 4, y + 4, 9, size);
      ctx.fillStyle = i % 3 ? "#37654a" : "#4d7551";
      ctx.fillRect(x - size, y - size, size * 2, size);
      ctx.fillRect(x - size + 4, y - size - 6, size + 4, 9);
      ctx.fillStyle = "#729358"; ctx.fillRect(x - 6, y - size - 4, 5, 4);
    } else if (region === "ruins") {
      ctx.fillStyle = "#282d31"; ctx.fillRect(x - 9, y + size, 20, 5);
      ctx.fillStyle = i % 2 ? "#827d6c" : "#6f746f";
      ctx.fillRect(x - 7, y - size, 14, size * 2); ctx.fillRect(x - 12, y - size, 24, 6);
      ctx.fillStyle = "#a79b7d"; ctx.fillRect(x - 4, y - size + 5, 3, size - 2);
      if (i % 3 === 0) { ctx.fillStyle = "#575b52"; ctx.fillRect(x + 13, y + 11, 13, 7); ctx.fillRect(x + 18, y + 6, 8, 5); }
    } else if (region === "cavern") {
      ctx.fillStyle = "#1b2029"; ctx.fillRect(x - size, y + 5, size * 2, 8);
      ctx.fillStyle = i % 2 ? "#576471" : "#68727c";
      ctx.fillRect(x - size, y - 3, size * 2, 11); ctx.fillRect(x - size + 5, y - 8, size, 7);
      if (i % 3 === 0) { ctx.fillStyle = "#68c8cc"; ctx.fillRect(x + 5, y - 17, 4, 17); ctx.fillRect(x + 3, y - 9, 8, 3); }
    } else {
      ctx.fillStyle = "#45616d"; ctx.fillRect(x - 2, y, 5, size + 12);
      ctx.fillStyle = "#d3e2da"; ctx.fillRect(x - size, y - size, size * 2, size + 7);
      ctx.fillRect(x - size + 4, y - size - 7, size + 1, 10);
      ctx.fillStyle = "#9cb8be"; ctx.fillRect(x + 7, y + 10, size, 5);
    }
  }
  ctx.globalAlpha = 0.55;
  for (let i = 0; i < 62; i++) {
    const x = 22 + random() * (w - 44), y = 22 + random() * (h - 44);
    ctx.fillStyle = theme.detail; ctx.fillRect(Math.round(x), Math.round(y), 2 + Math.floor(random() * 3), 2);
  }
  ctx.globalAlpha = 1;
}
function renderWorldToast(room) {
  const toast = $("#worldToast");
  if (room.privateNotice) {
    lastPrivateNotice = room.privateNotice;
    privateNoticeUntil = Date.now() + 6500;
    toast.textContent = room.privateNotice;
  }
  const showing = Date.now() < privateNoticeUntil && Boolean(lastPrivateNotice);
  if (showing && !room.privateNotice) toast.textContent = lastPrivateNotice;
  toast.classList.toggle("hidden", !showing || room.phase === "lobby");
}
function drawPuzzleRoom(ctx, puzzle, w, h) {
  ctx.fillStyle = "#17152a"; ctx.fillRect(14, 14, w - 28, h - 28);
  ctx.strokeStyle = "#c3a7eb"; ctx.lineWidth = 9; ctx.strokeRect(20, 20, w - 40, h - 40);
  ctx.strokeStyle = "#78659a"; ctx.lineWidth = 3; ctx.setLineDash([10, 9]);
  ctx.strokeRect(34, 34, w - 68, h - 68); ctx.setLineDash([]);
  const glyphs = { SUN: "☼", MOON: "☾", LEAF: "❧", FLAME: "♨", WAVE: "≋", STAR: "✦" };
  const runeColors = { SUN: "#ffe27c", MOON: "#c4d8ff", LEAF: "#a7ed9c", FLAME: "#ff9a68", WAVE: "#83dcf4", STAR: "#f4eaff" };
  puzzle.runes.forEach((rune) => {
    const active = puzzle.standingRune === rune.rune;
    const color = runeColors[rune.rune] || "#eee";
    ctx.save(); ctx.shadowColor = active ? color : "#8973b8"; ctx.shadowBlur = active ? 18 : 8;
    ctx.fillStyle = active ? (puzzle.cooperative ? "#635339" : puzzle.isCorrect ? "#526f48" : "#704742") : "#332b48";
    const runeSprite=window.GauntletCombatEnvironment.puzzleObject(ctx,rune.rune,rune.x,rune.y);
    if (!runeSprite) ctx.fillRect(rune.x - 39, rune.y - 33, 78, 66);
    ctx.strokeStyle = active ? (puzzle.cooperative ? "#ffe08a" : puzzle.isCorrect ? "#d5ed84" : "#ffae91") : "#a78dce";
    ctx.lineWidth = active ? 5 : 3; if (active || !runeSprite) ctx.strokeRect(rune.x - 39, rune.y - 33, 78, 66);
    ctx.fillStyle = color; ctx.font = "bold 29px serif"; ctx.textAlign = "center";
    if (!runeSprite) ctx.fillText(glyphs[rune.rune] || "✦", rune.x, rune.y + 5);
    ctx.restore();
    ctx.font = "bold 12px monospace"; ctx.fillStyle = "#fff4d5"; ctx.textAlign = "center";
    ctx.fillText(rune.rune, rune.x, rune.y + 49);
  });
  const totem = puzzle.totem;
  const sigilColor = runeColors[puzzle.targetSigil] || "#d6c5f0";
  ctx.save(); ctx.shadowColor = puzzle.atTotem ? sigilColor : "#aa8be3"; ctx.shadowBlur = puzzle.atTotem ? 22 : 12;
  const totemSprite=window.GauntletCombatEnvironment.puzzleObject(ctx,puzzle.targetSigil,totem.x,totem.y,true);
  if (!totemSprite) {
  ctx.fillStyle = "#211c30"; ctx.fillRect(totem.x - 34, totem.y - 36, 68, 72);
  ctx.strokeStyle = puzzle.atTotem ? sigilColor : "#c0a6e8"; ctx.lineWidth = 4; ctx.strokeRect(totem.x - 34, totem.y - 36, 68, 72);
  ctx.fillStyle = puzzle.atTotem ? "#413455" : "#352b49"; ctx.fillRect(totem.x - 25, totem.y - 27, 50, 54);
  ctx.fillStyle = puzzle.atTotem ? sigilColor : "#e7d8ff"; ctx.font = "bold 36px serif"; ctx.textAlign = "center";
  ctx.fillText(puzzle.targetSigil ? (glyphs[puzzle.targetSigil] || "✦") : "◇", totem.x, totem.y + 12);
  } else if (puzzle.atTotem) {
    ctx.strokeStyle=sigilColor;ctx.lineWidth=3;ctx.strokeRect(totem.x-36,totem.y-40,72,80);
  }
  ctx.restore();
  ctx.fillStyle = "#fff1c8"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center";
  ctx.fillText(puzzle.targetSigil ? "FOR " + puzzle.clueForName.toUpperCase() + " · " + puzzle.targetSigil : "TOTEM · FIND CLUE", totem.x, totem.y + 51);
}
function drawTownObjects(ctx, room, w, h) {
  const houses = room.townHouses || [];
  const paths = room.townPaths || [];
  const region = Object.hasOwn(villageArt, room.region) ? room.region : "woodland";
  const key = [room.code, room.townInstance, room.townSeed, region, villageArtRevision, forkArtRevision, w, h, JSON.stringify(paths)].join(":");
  if (key !== villageTerrainKey) {
    villageTerrainKey = key; villageLayer.width = w / 2; villageLayer.height = h / 2;
    const g = villageLayer.getContext("2d"); g.imageSmoothingEnabled = false;
    const ground = villageImage(room, "ground");
    if (ground) g.drawImage(ground, 0, 0, w / 2, h / 2);
    else { g.fillStyle = ({ woodland: "#35543b", ruins: "#716b50", cavern: "#273c52", frost: "#bbcbd3" })[region]; g.fillRect(0, 0, w / 2, h / 2); }
    const trail = forkArt[region];
    let pattern = null;
    if (trail?.complete && trail.naturalWidth) {
      const tile = document.createElement("canvas"); tile.width = 24; tile.height = 48;
      tile.getContext("2d").drawImage(trail, 230, 210, 24, 48, 0, 0, 24, 48);
      pattern = g.createPattern(tile, "repeat");
    }
    for (const width of [44, 30]) {
      g.strokeStyle = width === 44 ? ({woodland:"#857348",ruins:"#75664d",cavern:"#25364b",frost:"#728fa3"})[region] : pattern || "#c6ad72";
      g.lineWidth = width / 2; g.lineJoin = "round"; g.lineCap = "round";
      for (const path of paths) {
        g.beginPath(); path.forEach(([x, y], i) => i ? g.lineTo(x / 2, y / 2) : g.moveTo(x / 2, y / 2)); g.stroke();
      }
    }
  }
  ctx.imageSmoothingEnabled = false; ctx.drawImage(villageLayer, 0, 0, w, h);
  (room.townDecor?.trees || []).forEach(([x, y], i) => {
    if (drawVillageProp(ctx, room, "tree", x - 40, y - 64, 80, 104)) return;
    ctx.fillStyle = "#69452f"; ctx.fillRect(x - 5, y + 4, 10, 25);
    ctx.fillStyle = i % 2 ? "#397b49" : "#438750"; ctx.fillRect(x - 22, y - 18, 44, 29); ctx.fillRect(x - 15, y - 30, 31, 17);
    ctx.fillStyle = "#71a65b"; ctx.fillRect(x - 9, y - 25, 13, 7);
  });
  houses.forEach((house, index) => {
    const x = house.x, y = house.y, nearby = room.nearbyHouse && room.nearbyHouse.id === house.id;
    const roofs = ["#a94f3d", "#426f78", "#c56643", "#906451", "#b6773f"];
    const buildingArt = villageImage(room, "buildings");
    const row = VILLAGE_BUILDINGS.indexOf(house.id);
    const roof = Math.max(0, VILLAGE_ROOFS.indexOf(house.roof?.toLowerCase()));
    if (buildingArt && row >= 0) {
      ctx.drawImage(buildingArt, roof * 80, row * 72, 80, 72, x - 80, y - 93, 160, 144);
    } else {
    // Procedural fallback while a sprite is loading.
    ctx.fillStyle = "#18271c88"; ctx.fillRect(x - 68, y - 17, 140, 76);
    ctx.fillStyle = "#777465"; ctx.fillRect(x - 61, y - 30, 122, 73);
    ctx.fillStyle = index % 2 ? "#ead4a1" : "#e7c68b"; ctx.fillRect(x - 57, y - 47, 114, 83);
    ctx.fillStyle = "#67452e"; ctx.fillRect(x - 64, y - 53, 128, 12); ctx.fillRect(x - 62, y - 42, 8, 83); ctx.fillRect(x + 54, y - 42, 8, 83);
    ctx.fillStyle = house.roof || roofs[index % roofs.length]; ctx.fillRect(x - 70, y - 68, 140, 24); ctx.fillRect(x - 57, y - 77, 114, 13);
    ctx.fillStyle = "#eaa36a"; ctx.fillRect(x - 59, y - 45, 118, 4);
    ctx.fillStyle = "#6d9dab"; ctx.fillRect(x - 43, y - 23, 22, 19); ctx.fillRect(x + 21, y - 23, 22, 19);
    ctx.fillStyle = "#fff0c2"; ctx.fillRect(x - 34, y - 23, 3, 19); ctx.fillRect(x - 43, y - 15, 22, 3); ctx.fillRect(x + 30, y - 23, 3, 19); ctx.fillRect(x + 21, y - 15, 22, 3);
    ctx.fillStyle = "#633d32"; ctx.fillRect(x - 11, y + 2, 22, 35); ctx.fillStyle = "#e8c47b"; ctx.fillRect(x + 5, y + 19, 3, 3);
    }
    ctx.fillStyle = "#152321dd"; ctx.fillRect(x - 56, y - 94, 112, 16);
    ctx.fillStyle = "#f3e7c6"; ctx.font = "bold 9px monospace"; ctx.textAlign = "center"; ctx.fillText(house.name.toUpperCase(), x, y - 83);
    if (nearby) { ctx.strokeStyle = "#ffe389"; ctx.lineWidth = 2; ctx.strokeRect(x - 73, y - 80, 146, 137); ctx.fillStyle = "#fff0c8"; ctx.fillText("E · ENTER", x, y + 54); }
  });
  if (room.players.some((player) => player.townExitReady)) {
    ctx.fillStyle = "#fff0c8"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center";
    ctx.fillText("READY " + room.townExitVotes + " / " + room.townExitTotal, 480, 524);
  }
  drawVillagers(ctx, room);
  drawTownNpcs(ctx, room);
}
function drawVillagers(ctx, room) {
  // Scenery only: no service, interaction prompt, collision or dialogue.
  for (const [index, villager] of (room.townVillagers || []).entries()) {
    const { x, y, shirt, skin, hair, hat } = villager;
    drawCharacterShadow(ctx, x, y + 14, 12, "#17221b55");
    if (window.GauntletTownSprites?.character(ctx, "Villager" + String(index % 8 + 1).padStart(2, "0"), x, y, { direction: SPRITE_DIRECTIONS[index % 8], phase: index * 137, scale: .85 })) continue;
    ctx.fillStyle = "#393438"; ctx.fillRect(x - 7, y + 5, 5, 10); ctx.fillRect(x + 2, y + 5, 5, 10);
    ctx.fillStyle = shirt; ctx.fillRect(x - 9, y - 9, 18, 18);
    ctx.fillStyle = skin; ctx.fillRect(x - 7, y - 21, 14, 12); ctx.fillRect(x - 12, y - 5, 3, 9); ctx.fillRect(x + 9, y - 5, 3, 9);
    ctx.fillStyle = hair; ctx.fillRect(x - 8, y - 23, 16, 5);
    if (hat) { ctx.fillStyle = "#bd9c66"; ctx.fillRect(x - 11, y - 24, 22, 4); ctx.fillRect(x - 6, y - 29, 12, 5); }
  }
}
function drawTownNpcs(ctx, room) {
  const colors = { merchant: "#dfad62", alchemist: "#8ac8aa", innkeeper: "#c59478", guildmaster: "#b7a1df", gate: "#8bd2df" };
  const labels = { merchant: "MERCHANT", alchemist: "ALCHEMIST", innkeeper: "INNKEEPER", guildmaster: "GUILDMASTER", gate: "TRAIL GATE" };
  Object.entries(room.townNpcs || {}).forEach(([id, pos]) => {
    const x = pos.x, y = pos.y, color = colors[id] || "#e8d598";
    const nearby = room.nearbyNpc && room.nearbyNpc.id === id;
    if (id.startsWith("stairs_") || id.startsWith("bed_") || id.startsWith("locked_")) return;
    if (id === "gate") {
      if (!drawVillageProp(ctx, room, "gate", x - 76, y - 83, 152, 112)) {
      ctx.fillStyle = "#638c83"; ctx.fillRect(x - 48, y - 53, 13, 61); ctx.fillRect(x + 35, y - 53, 13, 61); ctx.fillRect(x - 48, y - 57, 96, 11);
      }
      ctx.fillStyle = "#152321e8"; ctx.fillRect(x - 66, y - 44, 132, 17);
      ctx.fillStyle = nearby ? "#ffe389" : "#c5ead3"; ctx.font = "10px monospace"; ctx.textAlign = "center"; ctx.fillText("EXIT · E TO VOTE", x, y - 39);
      return;
    }
    drawCharacterShadow(ctx, x, y + 18, 20, "#0e1720aa");
    const importedNpc = window.GauntletTownSprites?.character(ctx, ({ merchant: "Merchant", alchemist: "Alchemist", innkeeper: "Innkeeper", guildmaster: "Guildmaster" })[id], x, y, { mode: nearby ? "gesture" : "idle", scale: 1.15 });
    if (!importedNpc) {
    ctx.fillStyle = "#24202a"; ctx.fillRect(x - 12, y - 15, 24, 33);
    ctx.fillStyle = color; ctx.fillRect(x - 10, y - 14, 20, 25);
    ctx.fillStyle = "#f1cda1"; ctx.fillRect(x - 8, y - 25, 16, 12);
    ctx.fillStyle = "#211a25"; ctx.fillRect(x - 9, y - 28, 18, 5); ctx.fillRect(x - 5, y - 31, 10, 4);
    ctx.fillStyle = "#28202a"; ctx.fillRect(x - 8, y + 10, 6, 8); ctx.fillRect(x + 2, y + 10, 6, 8);
    if (id === "merchant") { ctx.fillStyle = "#8c593d"; ctx.fillRect(x + 11, y - 4, 10, 14); ctx.fillStyle = "#ffd166"; ctx.fillRect(x + 13, y - 1, 4, 5); }
    if (id === "alchemist") { ctx.fillStyle = "#b3efcf"; ctx.fillRect(x + 10, y - 5, 8, 10); ctx.fillStyle = "#436f6d"; ctx.fillRect(x + 12, y - 9, 4, 4); }
    if (id === "guildmaster") { ctx.fillStyle = "#e8c47b"; ctx.fillRect(x - 4, y - 8, 8, 10); ctx.fillStyle = "#cbd5df"; ctx.fillRect(x + 14, y - 18, 4, 33); ctx.fillStyle = "#e8c47b"; ctx.fillRect(x + 9, y + 6, 14, 4); }
    }
    ctx.fillStyle = nearby ? "#ffe389" : "#f5e6c9"; ctx.font = "bold 10px monospace"; ctx.textAlign = "center";
    ctx.fillText((nearby ? "E · " : "") + labels[id], x, y + 34);
    if (nearby) { ctx.strokeStyle = "#ffe389"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y - 4, 27, 0, Math.PI * 2); ctx.stroke(); }
  });
}
function drawTownInterior(ctx, room, w, h) {
  const house = (room.townHouses || []).find((entry) => entry.id === room.townInterior);
  if (drawVillageInteriorArt(ctx, room, house, w, h)) {
    if (house?.service === "innkeeper" && room.innFloor === 2) { drawInnRooms(ctx, room); return; }
    if (house?.service === "innkeeper") drawStairs(ctx, 710, 350, "UPSTAIRS", room);
    drawTownNpcs(ctx, room);
    ctx.fillStyle = "#162622e8"; ctx.fillRect(310, 58, 340, 30); ctx.fillRect(335, 506, 290, 25);
    ctx.fillStyle = "#fff1c9"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center";
    ctx.fillText(house ? house.name.toUpperCase() : "PRIVATE HOUSE", 480, 80);
    ctx.fillText(room.nearbyHouse ? "E · RETURN TO TOWN" : "WALK TO THE DOOR", 480, 522);
    return;
  }
  ctx.fillStyle = "#805f42"; ctx.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 28) { ctx.fillStyle = y % 56 ? "#916d4b" : "#9b7650"; ctx.fillRect(0, y, w, 26); ctx.fillStyle = "#634a37"; ctx.fillRect(0, y + 25, w, 3); }
  ctx.fillStyle = "#643e43"; ctx.fillRect(300, 176, 360, 225); ctx.fillStyle = "#b75c50"; ctx.fillRect(310, 186, 340, 205);
  ctx.fillStyle = "#e1bd74"; ctx.fillRect(332, 112, 82, 105); ctx.fillStyle = "#634932"; ctx.fillRect(342, 122, 62, 84);
  ctx.fillStyle = "#49706d"; ctx.fillRect(346, 126, 54, 36); ctx.fillStyle = "#c5a16c"; ctx.fillRect(346, 165, 54, 5);
  ctx.fillStyle = "#6d5039"; ctx.fillRect(590, 119, 127, 82); ctx.fillStyle = "#c7995e"; ctx.fillRect(598, 126, 111, 10); ctx.fillRect(598, 151, 111, 8); ctx.fillRect(598, 177, 111, 8);
  ctx.fillStyle = "#513a35"; ctx.fillRect(384, 272, 192, 82); ctx.fillStyle = "#dbb96f"; ctx.fillRect(394, 282, 172, 62);
  ctx.fillStyle = "#73513c"; ctx.fillRect(452, 428, 56, 112); ctx.fillStyle = "#d6b872"; ctx.fillRect(458, 435, 44, 90);
  if (house?.service === "innkeeper") {
    if (room.innFloor === 2) { drawInnRooms(ctx, room); return; }
    drawStairs(ctx, 710, 350, "UPSTAIRS", room);
    [260, 560].forEach((x) => { ctx.fillStyle = "#51372b"; ctx.fillRect(x, 310, 70, 50); ctx.fillStyle = "#b18a5e"; ctx.fillRect(x + 3, 306, 64, 38); });
  } else if (house?.service === "alchemist") {
    ["#8bdac5", "#bb83ff", "#f2a456", "#85dcf2"].forEach((color, i) => { const x = 400 + i * 46; ctx.fillStyle = "#cfdfd1"; ctx.fillRect(x, 267, 8, 8); ctx.fillStyle = color; ctx.fillRect(x - 4, 275, 16, 16); });
    ctx.fillStyle = "#1c3037"; ctx.fillRect(258, 305, 76, 56); ctx.fillStyle = "#72da9c"; ctx.fillRect(264, 299, 64, 14);
  } else if (house?.service === "merchant") {
    [260, 666].forEach((x) => { ctx.fillStyle = "#563b2e"; ctx.fillRect(x, 285, 48, 52); ctx.fillStyle = "#e1bc6a"; ctx.fillRect(x + 3, 295, 42, 7); ctx.fillRect(x + 18, 285, 10, 52); });
  } else if (house?.service === "guildmaster") {
    [260, 672].forEach((x) => {
      ctx.fillStyle = "#423451"; ctx.fillRect(x, 130, 32, 100);
      ctx.fillStyle = "#b7a1df"; ctx.fillRect(x + 4, 138, 24, 78);
      ctx.fillStyle = "#e8c47b"; ctx.fillRect(x + 13, 150, 6, 40); ctx.fillRect(x + 7, 174, 18, 5);
    });
    ctx.fillStyle = "#e8c47b"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center";
    ctx.fillText("ONE NEW PATH PER ADVENTURER", 480, 375);
  }
  drawTownNpcs(ctx, room);
  ctx.fillStyle = "#fff1c9"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center"; ctx.fillText(house ? house.name.toUpperCase() : "PRIVATE HOUSE", 480, 80);
  ctx.fillText(room.nearbyHouse ? "E · RETURN TO TOWN" : "WALK TO THE DOOR", 480, 522);
}
function drawForkBackdrop(target, room) {
  // room.region remains the area just left until _advance_stage selects a route.
  const region = Object.hasOwn(forkArt, room.region) ? room.region : "woodland";
  const image = forkArt[region];
  const w = target.canvas.width, h = target.canvas.height;
  const key = [region, forkArtRevision, fieldArtRevision, w, h].join(":");
  if (key !== forkTerrainKey) {
    forkLayer.width = w; forkLayer.height = h;
    const ctx = forkLayer.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    if (image.complete && image.naturalWidth) {
      ctx.drawImage(image, 0, 0, w, h);
    } else {
      const palette = {
        woodland: ["#304d3c", "#716040", "#b4915c", "#c4a66b"],
        ruins: ["#5b5d52", "#79796c", "#b2aa8d", "#c5bca0"],
        cavern: ["#27354b", "#2e4054", "#4d6375", "#597185"],
        frost: ["#c0d0d9", "#708a9f", "#99b5c4", "#abc5d2"]
      }[region];
      ctx.fillStyle = palette[0]; ctx.fillRect(0, 0, w, h);
      const field = fieldArt[region];
      if (field.complete && field.naturalWidth) ctx.drawImage(field, 0, 0, w, h);
      // Keep the exact server corridors visible even before fork art loads.
      const paths = [[[480, 540], [480, 320], [260, 170], [0, 170]], [[480, 540], [480, 320], [700, 170], [960, 170]]];
      ctx.save(); ctx.scale(w / 960, h / 540);
      ctx.lineJoin = "round"; ctx.lineCap = "round";
      for (const [index, width] of [116, 108, 84].entries()) {
        ctx.lineWidth = width; ctx.strokeStyle = palette[index + 1];
        for (const path of paths) {
          ctx.beginPath(); path.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke();
        }
      }
      ctx.restore();
    }
    forkTerrainKey = key;
  }
  target.save(); target.imageSmoothingEnabled = false;
  target.drawImage(forkLayer, 0, 0); target.restore();
}
function drawRouteGates(ctx, room) {
  drawForkBackdrop(ctx, room);
  const signSprite=window.GauntletCombatEnvironment.signpost(ctx,room);
  if (!signSprite) {
  ctx.fillStyle = "#704c33"; ctx.fillRect(473, 122, 14, 80); ctx.fillStyle = "#e4ca8b"; ctx.fillRect(375, 122, 210, 23); ctx.fillRect(375, 150, 210, 23);
  ctx.fillStyle = "#8b613d"; ctx.fillRect(375, 142, 210, 3); ctx.fillRect(375, 170, 210, 3);
  ctx.fillStyle = "#f4dea5"; ctx.fillRect(378, 122, 204, 2); ctx.fillRect(378, 150, 204, 2);
  ctx.fillStyle = "#704c33"; ctx.fillRect(382, 130, 3, 3); ctx.fillRect(575, 130, 3, 3); ctx.fillRect(382, 158, 3, 3); ctx.fillRect(575, 158, 3, 3);
  }
  ctx.fillStyle = "#342d25"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center";
  ctx.fillText("← " + (room.routes[0]?.name || "Left path"), 480, signSprite ? 145 : 138);
  ctx.fillText((room.routes[1]?.name || "Right path") + " →", 480, signSprite ? 215 : 166);
  (room.routes || []).forEach((route, index) => {
    const x = index === 0 ? 110 : 850, y = route.y;
    ctx.save(); ctx.globalAlpha = room.yourRouteVote === route.id ? 0.5 : 0.25; ctx.fillStyle = route.easier ? "#ffe68a" : "#a3e4c6";
    ctx.fillRect(index === 0 ? 0 : 918, y - 47, 42, 94); ctx.restore();
    ctx.fillStyle = "#17212ae6"; ctx.fillRect(x - 105, y - 81, 210, 26);
    ctx.fillRect(x - 105, y + 54, 210, route.easier ? 38 : 22);
    ctx.fillStyle = "#fff0c8"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center"; ctx.fillText(index === 0 ? "← " + route.name : route.name + " →", x, y - 63);
    ctx.font = "10px monospace"; ctx.fillText(route.votes + " / " + (room.activeVoterCount ?? room.activePartySize ?? room.players.length) + " at this edge", x, y + 69);
    if (route.easier) { ctx.fillStyle = "#ffe68a"; ctx.fillText("EASIER PATH", x, y + 85); }
  });
}
function drawBossWarnings(ctx, room) {
  for (const hazard of room.hazards || []) {
    ctx.save(); ctx.fillStyle = hazard.color; ctx.strokeStyle = hazard.active ? "#ff765e" : "#ffe389";
    ctx.globalAlpha = hazard.active ? .3 : .16;
    ctx.beginPath(); ctx.arc(hazard.x, hazard.y, hazard.radius, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = .85; ctx.lineWidth = 3; ctx.setLineDash(hazard.active ? [] : [8, 6]); ctx.stroke();
    ctx.setLineDash([]); ctx.fillStyle = "#fff0c8"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center";
    ctx.fillText(hazard.kind.toUpperCase(), hazard.x, hazard.y); ctx.restore();
  }
  for (const enemy of room.enemies || []) {
    const attack = enemy.bossAttack;
    if (!attack) continue;
    ctx.save();
    if (attack.kind === "charge") {
      ctx.strokeStyle = "#ffae5a"; ctx.globalAlpha = .22; ctx.lineWidth = 72;
      ctx.beginPath(); ctx.moveTo(enemy.x, enemy.y); ctx.lineTo(attack.x, attack.y); ctx.stroke();
      ctx.globalAlpha = .9; ctx.lineWidth = 3; ctx.setLineDash([8, 5]); ctx.stroke();
    }
    ctx.globalAlpha = 1; ctx.fillStyle = "#ffe389"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center";
    ctx.fillText(attack.kind === "rocks" ? "ROCK THROW" : attack.kind.toUpperCase(), enemy.x, enemy.y+80); ctx.restore();
  }
}
function drawStageExit(ctx, room) {
  ctx.fillStyle = "#fff0c8"; ctx.font = "bold 12px monospace"; ctx.textAlign = "center";
  ctx.beginPath(); ctx.moveTo(480, 62); ctx.lineTo(462, 80); ctx.lineTo(473, 80); ctx.lineTo(473, 94); ctx.lineTo(487, 94); ctx.lineTo(487, 80); ctx.lineTo(498, 80); ctx.closePath(); ctx.fill();
  ctx.font = "10px monospace"; ctx.fillText(room.stageExitReady + " / " + (room.activeVoterCount ?? room.activePartySize ?? room.players.length) + " gathered", 480, 100);
}
function drawTreasureChest(ctx, chest) {
  const x = chest.x, y = chest.y, pulse = 0.68 + Math.sin(Date.now() / 200) * 0.16;
  ctx.save(); ctx.globalAlpha = pulse; ctx.fillStyle = "#ffcf63"; ctx.beginPath(); ctx.arc(x, y + 3, 35, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  if (!window.GauntletTownSprites?.chest(ctx, { ...chest, opened: chest.opened })) {
  ctx.fillStyle = "#43272a"; ctx.fillRect(x - 25, y - 12, 50, 35);
  ctx.fillStyle = "#a24c32"; ctx.fillRect(x - 22, y - 9, 44, 28); ctx.fillRect(x - 25, y - 16, 50, 10);
  ctx.fillStyle = "#edb34e"; ctx.fillRect(x - 4, y - 12, 8, 27); ctx.fillRect(x - 21, y + 4, 42, 4);
  }
  ctx.fillStyle = "#fff0c8"; ctx.font = "bold 11px monospace"; ctx.textAlign = "center"; ctx.fillText("TREASURE · E", x, y + 39);
}
function drawCombatEffects(ctx, room) {
  const now = Date.now();
  (room.projectiles || []).forEach((shot) => {
    if (window.GauntletCombatEnvironment?.projectile(ctx, shot)) return;
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.drawImage(enemyGlow(shot.color), shot.x - 16, shot.y - 16, 32, 32);
    ctx.imageSmoothingEnabled = false; ctx.fillStyle = shot.color;
    if (shot.effectKind === "rock" || shot.effectKind === "boss_orb") {
      ctx.fillStyle = shot.effectKind === "rock" ? "#a8a393" : shot.color;
      ctx.beginPath(); ctx.arc(shot.x, shot.y, shot.radius || 15, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "#fff0c8"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = "#ffffff99"; ctx.fillRect(shot.x-7, shot.y-8, 7, 5);
    } else if (shot.effectKind === "lightning") {
      ctx.translate(shot.x, shot.y); ctx.rotate(Math.atan2(shot.vy || 0, shot.vx || 1));
      ctx.strokeStyle = "#fff2ad"; ctx.lineWidth = 3; ctx.beginPath();
      ctx.moveTo(-12, 3); ctx.lineTo(-3, -4); ctx.lineTo(1, 4); ctx.lineTo(12, -3); ctx.stroke();
    } else if (shot.class === "Archer") { ctx.translate(shot.x, shot.y); ctx.rotate(Math.atan2(shot.vy || 0, shot.vx || 1)); ctx.fillRect(-10, -2, 20, 4); ctx.fillRect(7, -4, 4, 8); }
    else if (["Knight", "Rogue"].includes(shot.class)) { ctx.beginPath(); ctx.arc(shot.x, shot.y, 6, 0, Math.PI * 2); ctx.fill(); }
    else { ctx.fillRect(shot.x - 5, shot.y - 5, 10, 10); ctx.fillRect(shot.x - 8, shot.y - 2, 16, 4); }
    ctx.restore();
  });
  (room.effects || []).forEach((effect) => {
    const remain = Math.max(0, Math.min(1, (effect.until * 1000 - now) / 800));
    if (!remain) return;
    if (window.GauntletCombatEnvironment?.effect(ctx, effect)) {
      if (effect.text) {
        ctx.save(); ctx.globalAlpha = Math.min(1, remain * 2); ctx.fillStyle = effect.color || "#fff";
        ctx.font = "bold 20px monospace"; ctx.textAlign = "center"; ctx.fillText(effect.text, effect.x, effect.y - 30); ctx.restore();
      }
      return;
    }
    ctx.save(); ctx.globalAlpha = remain; ctx.strokeStyle = effect.color || "#fff"; ctx.fillStyle = effect.color || "#fff"; ctx.lineWidth = 4;
    if (effect.type === "dash") {
      ctx.globalAlpha = remain * 0.6; ctx.lineWidth = 18; ctx.beginPath(); ctx.moveTo(effect.x, effect.y); ctx.lineTo(effect.targetX, effect.targetY); ctx.stroke();
      ctx.globalAlpha = remain; ctx.fillRect(effect.targetX - 7, effect.targetY - 7, 14, 14);
    } else if (effect.type === "slash" || effect.type === "cast" || effect.type === "enemy_attack") {
      const x = effect.targetX, y = effect.targetY, angle = Math.atan2(y - effect.y, x - effect.x);
      if (effect.type === "enemy_attack") { ctx.globalAlpha = remain * 0.45; ctx.strokeStyle = "#ff786b"; ctx.lineWidth = 3; ctx.setLineDash([7, 6]); ctx.beginPath(); ctx.moveTo(effect.x, effect.y); ctx.lineTo(x, y); ctx.stroke(); ctx.setLineDash([]); }
      ctx.translate(x, y); ctx.rotate(angle); ctx.beginPath(); ctx.arc(0, 0, 30, -0.8, 0.8); ctx.stroke();
      ctx.fillRect(-24, -3, 48, 6); ctx.fillRect(15, -8, 8, 16);
    } else if (effect.type === "impact" || effect.type === "burst" || effect.type === "heal" || effect.type === "aura") {
      const radius = 12 + (1 - remain) * (effect.type === "burst" ? 90 : 32);
      ctx.beginPath(); ctx.arc(effect.x, effect.y, radius, 0, Math.PI * 2); ctx.stroke();
      if (effect.type === "heal") { ctx.fillRect(effect.x - 3, effect.y - radius, 6, radius * 2); ctx.fillRect(effect.x - radius, effect.y - 3, radius * 2, 6); }
    }
    if (effect.text) { ctx.font = "bold 20px monospace"; ctx.textAlign = "center"; ctx.fillText(effect.text, effect.x, effect.y - 30); }
    ctx.restore();
  });
}
function drawArenaBackdrop(target, room, theme, w, h) {
  const region = fieldArt[room.region] ? room.region : "woodland";
  const image = fieldArt[region];
  const key = [room.code, room.stage, region, fieldArtRevision, w, h].join(":");
  if (key !== terrainKey) {
    terrainLayer.width = w; terrainLayer.height = h;
    const ctx = terrainLayer.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    if (image.complete && image.naturalWidth) {
      ctx.drawImage(image, 0, 0, w, h);
    } else {
      // Keep a playable field while the regional artwork loads.
      ctx.fillStyle = theme.base; ctx.fillRect(0, 0, w, h);
      for (let y = 0; y < h; y += 48) for (let x = 0; x < w; x += 48) {
        ctx.fillStyle = ((x / 48 + y / 48) % 2) ? theme.a : theme.b;
        ctx.fillRect(x, y, 46, 46);
        ctx.fillStyle = theme.detail; ctx.globalAlpha = 0.48;
        ctx.fillRect(x + 4, y + 5, 2, 2); ctx.globalAlpha = 1;
      }
      ctx.fillStyle = theme.trim;
      ctx.fillRect(0, 0, w, 14); ctx.fillRect(0, h - 14, w, 14);
      ctx.fillRect(0, 0, 14, h); ctx.fillRect(w - 14, 0, 14, h);
      drawRegionScenery(ctx, room, theme, w, h);
    }
    terrainKey = key;
  }
  target.imageSmoothingEnabled = false;
  target.drawImage(terrainLayer, 0, 0);
}
function enemyGlow(color) {
  if (!glowLayers.has(color)) {
    const layer = document.createElement("canvas"); layer.width = layer.height = 128;
    const ctx = layer.getContext("2d");
    const gradient = ctx.createRadialGradient(64, 64, 10, 64, 64, 64);
    gradient.addColorStop(0, color + "88"); gradient.addColorStop(0.48, color + "55"); gradient.addColorStop(1, color + "00");
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, 128, 128);
    glowLayers.set(color, layer);
  }
  return glowLayers.get(color);
}
function drawDamageTint(ctx, group, entity, x, y, draw) {
  const remaining = (damageTracks.get(group + ":" + entity.id)?.until || 0) - performance.now();
  if (remaining <= 0) { draw(ctx); return; }
  // Isolate the character's alpha mask so scenery, glows and labels keep their colors.
  const layer = damageLayer.getContext("2d");
  layer.clearRect(0, 0, 256, 256);
  layer.save();
  layer.translate(128 - x, 160 - y);
  draw(layer);
  layer.restore();
  layer.save();
  layer.globalCompositeOperation = "source-atop";
  layer.fillStyle = "rgba(255, 35, 45, " + (0.72 * Math.min(1, remaining / 100)) + ")";
  layer.fillRect(0, 0, 256, 256);
  layer.restore();
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(damageLayer, x - 128, y - 160);
  ctx.restore();
}
function drawCharacterShadow(ctx, x, y, radius, color = "#15211a99") {
  ctx.save(); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}
function drawSummon(ctx, summon) {
  const x = summon.x, y = summon.y;
  const attacking = summon.animationUntil * 1000 > Date.now();
  const stride = summon.moving ? Math.round(Math.sin(Date.now() / 90) * 2) : 0;
  ctx.save();
  drawCharacterShadow(ctx, x, y + 12, summon.kind === "bird" ? 16 : ["bear", "golem"].includes(summon.kind) ? 32 : 23, "#10231bb0");
  ctx.strokeStyle = summon.color; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(x, y + 12, 28, 12, 0, 0, Math.PI * 2); ctx.stroke();
  drawDamageTint(ctx, "summon", summon, x, y, (ctx) => {
    const summonSpriteKey = ({ lightning_bird: "LightningBird", fire_wolf: "FireWolf", ice_bear: "IceBear", nature_golem: "NatureGolem" })[summon.abilityId];
    if (summonSpriteKey) {
      const scale = summon.kind === "golem" ? 2.5 : summon.kind === "bear" ? 2.15 : summon.kind === "wolf" ? 1.15 : 1;
      ctx.save(); ctx.translate(x, y); ctx.scale(scale, scale); ctx.translate(-x, -y);
      const imported = drawImportedHero(ctx, { ...summon, status: "alive" }, x, y, summonSpriteKey);
      ctx.restore();
      if (imported) return;
    }
    ctx.save(); ctx.translate(x, y); ctx.scale(summon.facingX < 0 ? -1 : 1, 1); ctx.translate(-x, -y);
    if (summon.kind === "bird") {
      const flap = Math.round(Math.sin(Date.now() / 100) * 5);
      ctx.fillStyle = "#18374d"; ctx.fillRect(x - 9, y - 20, 18, 18);
      ctx.fillStyle = "#72d7ff"; ctx.fillRect(x - 7, y - 19, 16, 15);
      ctx.fillStyle = "#7a91ef"; ctx.fillRect(x - 26, y - 22 + flap, 20, 7); ctx.fillRect(x + 6, y - 22 - flap, 20, 7);
      ctx.fillRect(x - 30, y - 18 + flap, 14, 6); ctx.fillRect(x + 18, y - 18 - flap, 14, 6);
      ctx.fillStyle = "#c5efff"; ctx.fillRect(x + 5, y - 29, 12, 13); ctx.fillRect(x - 11, y - 6, 6, 9);
      ctx.fillStyle = "#ffe085"; ctx.fillRect(x + 17, y - 24, 8, 4); ctx.fillRect(x + 8, y - 36, 3, 10); ctx.fillRect(x + 4, y - 31, 8, 3);
      ctx.fillStyle = "#13202b"; ctx.fillRect(x + 12, y - 26, 3, 3);
    } else if (summon.kind === "wolf") {
      ctx.fillStyle = "#552e29"; ctx.fillRect(x - 20, y - 16, 34, 24);
      ctx.fillStyle = "#d25d35"; ctx.fillRect(x - 18, y - 14, 30, 20); ctx.fillRect(x + 9, y - 27, 16, 19); ctx.fillRect(x + 23, y - 18, 10, 7);
      ctx.fillRect(x - 29, y - 16, 13, 7); ctx.fillRect(x - 30, y - 23, 7, 12);
      ctx.fillStyle = "#ffad50"; ctx.fillRect(x + 12, y - 34, 5, 11); ctx.fillRect(x + 21, y - 32, 5, 10); ctx.fillRect(x - 12, y - 23, 10, 10);
      ctx.fillStyle = "#983c2c"; ctx.fillRect(x - 15 + stride, y + 3, 7, 13); ctx.fillRect(x + 6 - stride, y + 3, 7, 13);
      ctx.fillStyle = "#fff1a1"; ctx.fillRect(x + 19, y - 23, 4, 3); if (attacking) ctx.fillRect(x + 26, y - 11, 7, 3);
    } else if (summon.kind === "bear") {
      ctx.fillStyle = "#387992"; ctx.fillRect(x - 26, y - 26, 46, 36);
      ctx.fillStyle = "#b4e4ef"; ctx.fillRect(x - 23, y - 24, 42, 31); ctx.fillRect(x + 13, y - 35, 23, 25);
      ctx.fillStyle = "#e6faff"; ctx.fillRect(x + 16, y - 42, 7, 11); ctx.fillRect(x + 29, y - 41, 7, 10); ctx.fillRect(x + 27, y - 22, 13, 11);
      ctx.fillRect(x - 18 + stride, y + 3, 12, 16); ctx.fillRect(x + 8 - stride, y + 3, 12, 16);
      ctx.fillStyle = "#255975"; ctx.fillRect(x + 31, y - 23, 8, 4); ctx.fillRect(x + 26, y - 30, 3, 3);
      ctx.fillStyle = "#75bfdc"; ctx.fillRect(x - 19, y - 31, 6, 9); ctx.fillRect(x - 6, y - 34, 6, 11);
    } else {
      ctx.fillStyle = "#35483c"; ctx.fillRect(x - 21, y - 32, 42, 44);
      ctx.fillStyle = "#889786"; ctx.fillRect(x - 18, y - 30, 36, 37); ctx.fillRect(x - 11, y - 48, 24, 20);
      ctx.fillStyle = "#5d7465"; ctx.fillRect(x - 32, y - 25, 14, 31); ctx.fillRect(x + 18, y - 25 - (attacking ? 8 : 0), 14, 31);
      ctx.fillRect(x - 18 + stride, y + 5, 14, 16); ctx.fillRect(x + 4 - stride, y + 5, 14, 16);
      ctx.fillStyle = "#6bb06a"; ctx.fillRect(x - 19, y - 33, 18, 8); ctx.fillRect(x + 8, y - 20, 12, 12); ctx.fillRect(x - 9, y - 52, 13, 5);
      ctx.fillStyle = "#b9ff98"; ctx.fillRect(x - 6, y - 41, 5, 4); ctx.fillRect(x + 5, y - 41, 5, 4); ctx.fillRect(x - 4, y - 19, 9, 10);
    }
    ctx.restore();
  });
  ctx.restore();
}
function drawSummonLabel(ctx, summon) {
  const x = summon.x, y = summon.y;
  ctx.save();
  // Keep the wolf's label clear of its taller melee companion.
  const barY = summon.kind === "wolf" ? y + 24 : y - (summon.kind === "golem" ? 84 : summon.kind === "bear" ? 85 : 43);
  ctx.fillStyle = "#142c2b"; ctx.fillRect(x - 22, barY, 44, 4);
  ctx.fillStyle = "#91edb8"; ctx.fillRect(x - 21, barY + 1, 42 * summon.hp / summon.maxHp, 2);
  ctx.restore();
}
function drawWorld(room) {
  const canvas = $("#world");
  if (!canvas || !room || room.phase === "lobby") return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  const themes = {
    woodland: { base: "#243d32", a: "#294638", b: "#304d3c", detail: "#50724d", trim: "#4a4633" },
    ruins: { base: "#393b39", a: "#414440", b: "#494a43", detail: "#777465", trim: "#655b4b" },
    cavern: { base: "#242d3c", a: "#2b3545", b: "#313d4d", detail: "#56777b", trim: "#4b4e5c" },
    frost: { base: "#778d91", a: "#819a9d", b: "#8da6a5", detail: "#d4e4dc", trim: "#526f7d" }
  };
  const theme = themes[room.region] || themes.woodland;
  if (room.phase !== "town" && room.phase !== "routes") drawArenaBackdrop(ctx, room, theme, w, h);
  const ownTownInterior = room.phase === "town" && Boolean(room.townInterior);
  if (room.phase === "puzzle" && room.puzzle) drawPuzzleRoom(ctx, room.puzzle, w, h);
  if (room.phase === "town") {
    if (ownTownInterior) drawTownInterior(ctx, room, w, h);
    else drawTownObjects(ctx, room, w, h);
  }
  if (room.phase === "routes") drawRouteGates(ctx, room);
  if (room.phase === "peace") drawPeacefulClearing(ctx, room);
  if (room.phase === "town" && !ownTownInterior) drawVillageRunner(ctx, room);
  window.GauntletCombatEnvironment.draw(ctx, room);
  window.GauntletCombatEnvironment.objectives(ctx, room);
  if (room.phase === "combat") window.GauntletCombatEnvironment.warnings(ctx, room);
  if (room.phase === "stage_exit") drawStageExit(ctx, room);
  if (room.phase === "chest" && room.chest) drawTreasureChest(ctx, room.chest);
  (room.phase === "combat" ? room.enemies : []).forEach((enemy) => {
    if (enemy.kind==='rift') {window.GauntletCombatEnvironment.structure(ctx,enemy,localTarget===enemy.id,false,room.region);return;}
    const x = enemy.x, y = enemy.y, color = enemy.baseColor || "#85977a";
    const spriteScale = enemy.boss ? (enemy.bossPhase === 2 ? 3.2 : 2.3) : enemy.miniBoss ? 1.9 : enemy.kind === "draco" ? 1.25 : 1.5;
    if (localTarget===enemy.id) window.GauntletCombatEnvironment.target(ctx,x,y,enemy.boss?45:28);
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.globalAlpha=.5;
    const glowSize = (enemy.kind === "dragon" ? 128 : 68) * spriteScale;
    ctx.drawImage(enemyGlow(enemy.color), x - glowSize / 2, y - 12 - glowSize / 2, glowSize, glowSize);
    ctx.restore();
    ctx.save(); ctx.globalAlpha = 0.2; ctx.fillStyle = enemy.color;
    drawCharacterShadow(ctx, x, y + 12, (enemy.kind === "dragon" ? 24 : 18) * spriteScale, enemy.color); ctx.restore();
    ctx.save(); ctx.translate(x, y); ctx.scale(spriteScale, spriteScale); ctx.translate(-x, -y);
    let imported;
    drawDamageTint(ctx, "enemy", enemy, x, y, (ctx) => {
    const spriteKey = {serpent:"Serpent",minotaur:"Minotaur",troll:"Troll",spider:"Spider",wolf:"Wolf",draco:"Draco",dragon:"Dragon",monster:"Chimera"}[enemy.kind];
    imported = window.GauntletCombatEnvironment?.enemy(ctx, enemy, x, y) || spriteKey && drawImportedHero(ctx, { ...enemy, status: "alive" }, x, y, spriteKey);
    if (!imported) {
    ctx.fillStyle = color;
    if (enemy.kind === "wolf") {
      ctx.fillRect(x - 9, y - 5, 20, 10); ctx.fillRect(x + 5, y - 10, 8, 9);
      ctx.fillRect(x + 8, y - 13, 3, 4); ctx.fillRect(x - 7, y + 4, 4, 5); ctx.fillRect(x + 5, y + 4, 4, 5);
    } else if (enemy.kind === "serpent") {
      ctx.fillRect(x - 7, y - 8, 14, 17); ctx.fillRect(x - 3, y - 13, 12, 9); ctx.fillRect(x - 1, y + 8, 8, 5);
    } else if (enemy.kind === "spider") {
      ctx.fillRect(x - 5, y - 6, 12, 12); ctx.fillRect(x - 13, y - 9, 8, 3); ctx.fillRect(x + 7, y - 9, 8, 3); ctx.fillRect(x - 14, y + 7, 9, 3); ctx.fillRect(x + 7, y + 7, 9, 3);
    } else if (enemy.kind === "dragon" || enemy.kind === "draco") {
      ctx.fillRect(x - 11, y - 5, 24, 15); ctx.fillRect(x + 8, y - 12, 13, 11);
      ctx.fillRect(x + 17, y - 8, 8, 5); ctx.fillRect(x + 13, y - 16, 3, 6); ctx.fillRect(x + 20, y - 15, 3, 6);
      ctx.fillRect(x - 5, y - 16, 7, 12); ctx.fillRect(x - 17, y - 20, 11, 15);
      ctx.fillRect(x + 1, y - 21, 12, 15); ctx.fillRect(x - 12, y + 10, 5, 8);
      ctx.fillRect(x + 5, y + 10, 5, 8); ctx.fillRect(x - 18, y + 5, 9, 4);
    } else {
      ctx.fillRect(x - 8, y - 7, 18, 18); ctx.fillRect(x - 4, y - 12, 12, 7); ctx.fillRect(x - 7, y + 10, 5, 4); ctx.fillRect(x + 3, y + 10, 5, 4);
    }
    const mobClassColor = room.classes[enemy.class] && room.classes[enemy.class].color || "#eee0b3";
    ctx.fillStyle = "#170f18"; ctx.fillRect(x - 4, y - 2, 3, 3); ctx.fillRect(x + 4, y - 2, 3, 3);
    ctx.fillStyle = mobClassColor;
    ctx.fillRect(x - 4, y - 2, 2, 2); ctx.fillRect(x + 4, y - 2, 2, 2);
    if (enemy.class === "Knight") {
      ctx.fillStyle = "#d1dbe1"; ctx.fillRect(x + 10, y - 8, 3, 22); ctx.fillStyle = "#b3894d"; ctx.fillRect(x + 8, y + 1, 7, 6);
    } else if (enemy.class === "Wizard" || enemy.class === "Druid") {
      ctx.fillStyle = mobClassColor; ctx.fillRect(x - 8, y - 18, 16, 4); ctx.fillRect(x - 4, y - 25, 9, 8);
      ctx.fillStyle = "#fff0a5"; ctx.fillRect(x + 12, y - 11, 3, 20); ctx.fillRect(x + 9, y - 14, 9, 4);
    } else if (enemy.class === "Archer") {
      ctx.strokeStyle = mobClassColor; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x + 12, y, 11, -1.25, 1.25); ctx.stroke();
      ctx.fillStyle = "#e6d1a0"; ctx.fillRect(x + 10, y - 2, 7, 2);
    } else if (enemy.class === "Rogue") {
      ctx.fillStyle = "#20202b"; ctx.fillRect(x - 8, y - 17, 16, 5); ctx.fillStyle = "#e7e8ec"; ctx.fillRect(x + 10, y - 1, 10, 3); ctx.fillRect(x + 17, y - 4, 3, 9);
    } else if (enemy.class === "Cleric" || enemy.class === "Healer") {
      ctx.fillStyle = mobClassColor; ctx.fillRect(x - 5, y - 21, 10, 3); ctx.fillRect(x - 1, y - 25, 3, 11);
      ctx.fillRect(x - 5, y - 19, 10, 3);
    } else if (enemy.class === "Bard") {
      ctx.fillStyle = mobClassColor; ctx.fillRect(x - 8, y - 17, 16, 4); ctx.fillRect(x + 11, y - 3, 9, 10);
      ctx.fillStyle = "#fff1c4"; ctx.fillRect(x + 14, y - 1, 2, 7);
    }
    }
    });
    ctx.restore();
    const barWidth = enemy.kind === "dragon" ? (enemy.bossPhase === 2 ? 180 : 140) : enemy.boss ? (enemy.bossPhase === 2 ? 100 : 72) : enemy.miniBoss || localTarget===enemy.id ? 60 : 40;
    const barY = enemy.kind === "dragon" && imported ? Math.max(18, y - 96 * spriteScale - 12) : enemy.boss ? y - 88 : enemy.miniBoss ? y - 68 : imported ? y - 50 : y - 32;
    ctx.fillStyle = "#211720"; ctx.fillRect(x - barWidth / 2, barY, barWidth, 4);
    ctx.fillStyle = enemy.boss ? "#f0c76c" : enemy.miniBoss ? "#d99159" : "#e66e68";
    ctx.fillRect(x - barWidth / 2 + 1, barY + 1, (barWidth - 2) * Math.max(0, enemy.hp) / enemy.maxHp, 2);
    ctx.fillStyle = "#eee2d2"; ctx.font = enemy.boss ? "bold 11px monospace" : "10px monospace"; ctx.textAlign = "center";
    if (enemy.boss || localTarget===enemy.id) ctx.fillText(enemy.name, x, barY - 4);
  });
  if (room.phase === "combat") (room.summons || []).forEach((summon) => drawSummon(ctx, summon));
  const visiblePlayers = room.phase === "puzzle" || ownTownInterior ? room.players.filter((player) => player.id === room.you) : room.players.filter((player) => !player.indoors && player.connected !== false);
  visiblePlayers.forEach((player) => {
    if (room.phase === "combat" && player.id === room.you && player.status === "alive" && moveState.attack) {
      const reach = Math.min(320, Math.max(50, room.attackRange || 150));
      ctx.save(); ctx.globalAlpha = 0.18; ctx.strokeStyle = player.color; ctx.lineWidth = 1;
      ctx.setLineDash([7, 7]); ctx.beginPath(); ctx.arc(player.x, player.y, reach, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    }
    ctx.globalAlpha = player.invisible ? 0.35 : 1;
    const x = player.x, y = player.y, color = player.color, role = player.class;
    const bob = Math.sin(Date.now() / (role === "Druid" ? 550 : 180) + x) * (role === "Druid" ? .25 : 1.2);
    const characterScale = room.phase === "town" ? 0.78 : 1.65;
    const nameOffset = room.phase === "town" ? 28 : heroSprites[role]?.sheet ? 61 : 37;
    if (player.id===room.you && player.status==='alive') {
      ctx.save();ctx.strokeStyle='#fff1af';ctx.lineWidth=3;ctx.beginPath();ctx.arc(x,y+12,23,0,Math.PI*2);ctx.stroke();ctx.restore();
    }
    drawCharacterShadow(ctx, x, y + 12 * characterScale, 11 * characterScale);
    ctx.save(); ctx.translate(x, y + bob); ctx.scale(characterScale, characterScale); ctx.translate(-x, -y);
    drawDamageTint(ctx, "player", player, x, y, (ctx) => {
    if (!drawImportedHero(ctx, player, x, y)) {
    ctx.fillStyle = "#171722"; ctx.fillRect(x - 9, y - 12, 18, 25);
    ctx.fillStyle = role === "Rogue" ? "#46364f" : color; ctx.fillRect(x - 7, y - 10, 14, 17);
    ctx.fillStyle = "#fff0c9"; ctx.fillRect(x - 6, y - 9, 4, 11);
    ctx.fillStyle = "#382d32"; ctx.fillRect(x - 8, y + 6, 7, 9); ctx.fillRect(x + 1, y + 6, 7, 9);
    ctx.fillStyle = "#7b5142"; ctx.fillRect(x - 8, y + 12, 8, 3); ctx.fillRect(x + 1, y + 12, 8, 3);
    ctx.fillStyle = "#f0c49a"; ctx.fillRect(x - 6, y - 20, 12, 10);
    ctx.fillStyle = role === "Rogue" ? "#302637" : "#49343a"; ctx.fillRect(x - 7, y - 22, 14, 5);
    ctx.fillRect(x - 7, y - 18, 3, 5); ctx.fillRect(x + 4, y - 18, 3, 5);
    ctx.fillStyle = "#241f2b"; ctx.fillRect(x - 4, y - 16, 2, 2); ctx.fillRect(x + 2, y - 16, 2, 2);
    if (role === "Knight") {
      ctx.fillStyle = "#c5d0d2"; ctx.fillRect(x - 8, y - 22, 16, 6); ctx.fillRect(x - 5, y - 27, 10, 6);
      ctx.fillStyle = "#f2d87e"; ctx.fillRect(x - 2, y - 25, 4, 2);
      ctx.fillStyle = "#7595ac"; ctx.fillRect(x + 9, y - 6, 3, 20); ctx.fillRect(x + 7, y + 2, 7, 8);
      ctx.fillStyle = "#e1c978"; ctx.fillRect(x + 9, y + 4, 3, 4);
    } else if (role === "Wizard") {
      ctx.fillStyle = "#624a88"; ctx.fillRect(x - 9, y - 23, 18, 4); ctx.fillRect(x - 5, y - 34, 10, 12); ctx.fillRect(x - 8, y - 24, 16, 3);
      ctx.fillStyle = "#f2cc74"; ctx.fillRect(x - 2, y - 30, 4, 4);
      ctx.fillStyle = "#b8a0ed"; ctx.fillRect(x + 10, y - 17, 3, 31); ctx.fillStyle = "#d9c6ff"; ctx.fillRect(x + 7, y - 21, 9, 5);
    } else if (role === "Archer") {
      ctx.fillStyle = "#496e4d"; ctx.fillRect(x - 9, y - 22, 18, 5); ctx.fillRect(x - 6, y - 26, 12, 4);
      ctx.fillStyle = "#d9c38a"; ctx.fillRect(x + 10, y - 17, 2, 31); ctx.fillRect(x + 7, y - 18, 6, 3); ctx.fillRect(x + 7, y + 12, 6, 3);
    } else if (role === "Cleric") {
      ctx.fillStyle = "#eee0b3"; ctx.fillRect(x - 8, y - 22, 16, 5); ctx.fillRect(x - 5, y - 26, 10, 4); ctx.fillStyle = "#d3aa4f";
      ctx.fillRect(x - 2, y - 20, 4, 12); ctx.fillRect(x - 6, y - 16, 12, 4);
    } else if (role === "Rogue") {
      ctx.fillStyle = "#302637"; ctx.fillRect(x - 9, y - 22, 18, 7); ctx.fillRect(x - 7, y - 26, 14, 4);
      ctx.fillStyle = "#d4d0df"; ctx.fillRect(x + 10, y - 1, 3, 16); ctx.fillRect(x + 8, y - 3, 7, 3);
    } else if (role === "Druid") {
      ctx.fillStyle = "#594b39"; ctx.fillRect(x - 8, y - 24, 16, 5); ctx.fillRect(x - 4, y - 29, 8, 6);
      ctx.fillStyle = "#afd57d"; ctx.fillRect(x - 12, y - 27, 4, 8); ctx.fillRect(x + 8, y - 27, 4, 8); ctx.fillRect(x - 2, y - 33, 4, 6);
    } else if (role === "Bard") {
      ctx.fillStyle = "#b96492"; ctx.fillRect(x - 9, y - 23, 18, 4); ctx.fillRect(x - 3, y - 31, 8, 9); ctx.fillRect(x - 7, y - 24, 15, 3);
      ctx.fillStyle = "#e6ba77"; ctx.fillRect(x + 9, y - 7, 10, 10); ctx.fillRect(x + 12, y - 11, 4, 5); ctx.fillStyle = "#6b4d38"; ctx.fillRect(x + 10, y - 4, 8, 5);
    } else if (role === "Healer") {
      ctx.fillStyle = "#65b9b9"; ctx.fillRect(x - 8, y - 22, 16, 5); ctx.fillRect(x - 5, y - 26, 10, 4); ctx.fillStyle = "#f5ead8";
      ctx.fillRect(x + 10, y - 22, 3, 37); ctx.fillRect(x + 7, y - 24, 9, 4); ctx.fillRect(x + 10, y - 31, 3, 18);
    }
    }
    if (player.armorColor) { ctx.fillStyle = player.armorColor; ctx.fillRect(x - 8, y - 9, 16, 13); ctx.fillRect(x - 11, y - 7, 4, 10); ctx.fillStyle = "#ffffff55"; ctx.fillRect(x - 6, y - 8, 3, 8); }
    if (player.weaponColor) { ctx.fillStyle = "#171722"; ctx.fillRect(x + 10, y - 11, 5, 29); ctx.fillStyle = player.weaponColor; ctx.fillRect(x + 11, y - 12, 3, 28); ctx.fillRect(x + 8, y - 4, 9, 4); }
    });
    ctx.restore();
    ctx.fillStyle = "#fff4d5"; ctx.font = room.phase === "town" ? "bold 9px monospace" : "bold 12px monospace"; ctx.textAlign = "center";
    if (room.phase!=='combat' || player.status!=='alive') ctx.fillText(player.name, x, y - nameOffset);
    else if (player.id===room.you) {
      ctx.fillStyle='#fff1af';ctx.beginPath();ctx.moveTo(x-5,y-nameOffset-8);ctx.lineTo(x+5,y-nameOffset-8);ctx.lineTo(x,y-nameOffset);ctx.closePath();ctx.fill();
    }
    if (player.status !== "alive") {
      ctx.fillStyle = "#ff8585"; ctx.fillText(player.status === "downed" ? "DOWN!" : "FALLEN", x, y + nameOffset);
    }
    ctx.globalAlpha = 1;
  });
  if (room.phase === "combat") (room.summons || []).forEach((summon) => drawSummonLabel(ctx, summon));
  drawCombatEffects(ctx, room);
  if (typeof drawPings === "function") drawPings(ctx, room);
  if (room.phase === "cleared" || room.phase === "defeat") {
    ctx.fillStyle = room.phase === "defeat" ? "rgba(14, 8, 18, .82)" : "rgba(12, 20, 17, .72)";
    ctx.fillRect(0, 0, w, h);
    ctx.textAlign = "center"; ctx.fillStyle = room.phase === "defeat" ? "#e5857b" : "#f0d18a";
    ctx.font = "bold 32px monospace";
    ctx.fillText(room.phase === "defeat" ? "EVIL CLAIMS THE FIELD" : "THE DRAGON IS DEFEATED!", w / 2, h / 2);
  }
}
if (window.location.protocol === "file:") {
  $("#entry").classList.remove("hidden");
  $("#lobby").classList.add("hidden");
  document.body.classList.remove("is-playing");
  $("#connection").textContent = "OPEN SERVER PAGE";
  $("#connection").className = "connection connecting";
  notice($("#entryNotice"), "This file preview cannot reach multiplayer. Open the live server page instead.");
  $("#liveGameLink").classList.remove("hidden");
} else if (session) { enterLobby(); refresh(); }
