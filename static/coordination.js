/* Party tools stay outside the canvas renderer so they work with touch and keys. */
let enemyPingArmed = false;
let guidePage = 0;
let lastTeamSignature = "";

const gameMenu = document.createElement("details");
gameMenu.className = "game-menu";
gameMenu.innerHTML = '<summary class="secondary small">Menu</summary><div class="game-menu-items"><button class="secondary" data-guide>How to play</button><button class="secondary" data-audio-open>Sound settings</button><button id="openStats" class="secondary">Run stats</button></div>';
gameMenu.querySelector(".game-menu-items").append($("#mainMenuGame"));
$(".game-top-actions").append(gameMenu);
const pingFeed = document.createElement("div");
pingFeed.id = "pingFeed"; pingFeed.setAttribute("aria-live", "polite");
$(".coordination-tools").append(pingFeed);

function openInfo(id) {
  endHeldAttack();
  keys.clear(); moveState = { x: 0, y: 0, attack: false }; sendMovement(true);
  gameMenu.open = false;
  $("#" + id).showModal();
}
document.addEventListener("click", (event) => {
  const close = event.target.closest("[data-close]");
  if (close) $("#" + close.dataset.close).close();
  if (event.target.closest("[data-guide]")) { guidePage = 0; renderGuide(); openInfo("guideDialog"); }
});
function renderGuide() {
  const key = (name) => String(keyBindings[name]).toUpperCase();
  const pages = [
    ["Move and explore", `Move with ${key("up")}, ${key("left")}, ${key("down")}, ${key("right")} or the arrow keys. On a phone, hold the direction buttons. Space or Dash gives a short burst during combat. You can keep moving while using abilities or quick pings.`],
    ["Use your three abilities", `Choose one Light, Special and Ultimate. Hold left click on the arena or hold Attack to repeat your equipped Light; ${key("special")} for Special; ${key("ultimate")} for Ultimate. Touch players can tap the ability buttons. Ultimates recharge in 15 seconds, including at the start of every combat stage. Druid summons stay through waves, disappear at the next stage, and recharge after death.`],
    ["Read the battlefield", "Crates and rocks block movement and shots; Light attacks can break them. Traps flash before firing, poison pools hurt once per second, and ice keeps you sliding after releasing movement. Chargers rush, ambushers flank, ranged foes keep distance, supports heal and bruisers swing nearby. Bosses mark attacks before releasing them, then pause to recover. Move out of warnings and use that pause to counterattack. Some stages ask you to destroy a summoning rift, protect a ward or bait charges into rocks. Tap an enemy to prefer it; Tab cycles targets. Escape or Clear target returns to automatic targeting. Blocked or distant targets fall back to a nearby foe."],
    ["Rescue your party", `Downed heroes stay revivable while an ally is standing; there is no countdown. Move close and hold ${key("revive")} or Revive to rescue them. Most rescues take 1.8 seconds; Healers take 0.8. If everyone goes down, the party wipes. The party strip shows health and who needs help. Help marks your position, Gather requests a meeting, and Enemy lets you tap a specific foe.`],
    ["Read and share clues", "In multiplayer, your totem describes a teammate's rune. Share clue sends that inscription to party chat. A teammate holds your answer. Stand on your chosen runes together to open the gate. An NPC companion shares your answer in the HUD and waits for your Share clue before choosing its rune. Solo totems describe your own answer. A disconnected teammate's clue is reassigned to someone still present."],
    ["Towns, training and saves", `Use ${key("revive")} or Interact at doors and NPCs. Trade at the shop and change class once per run at the Guild. Speak to the first village's innkeeper to discover hunter training before leaving. Take the inn stairs upstairs and use a bed in an unlocked room to restore the party and save a checkpoint to disk. Talking to the innkeeper does not save. A restart returns you to your saved bed; progress beyond that village is lost. Use Continue saved run in this browser and keep its site data. Run stats and your dragon quest are under Menu.`]
  ];
  $("#guideStep").textContent = `${guidePage + 1} / ${pages.length}`;
  $("#guideHeading").textContent = pages[guidePage][0];
  $("#guideText").textContent = pages[guidePage][1];
  $("#guideBack").disabled = guidePage === 0;
  $("#guideNext").textContent = guidePage === pages.length - 1 ? "Done" : "Next";
}
$("#guideBack").addEventListener("click", () => { guidePage = Math.max(0, guidePage - 1); renderGuide(); });
$("#guideNext").addEventListener("click", () => {
  if (guidePage === 5) { $("#guideDialog").close(); return; }
  guidePage++; renderGuide();
});
$("#continueRun").classList.toggle("hidden", !localStorage.getItem("gauntlet-resume"));
$("#continueRun").addEventListener("click", async () => {
  try {
    const saved = JSON.parse(localStorage.getItem("gauntlet-resume"));
    if (!saved?.room || !saved?.player) throw new Error("No saved run in this browser.");
    await api("/api/state?room=" + encodeURIComponent(saved.room) + "&player=" + encodeURIComponent(saved.player));
    saveSession(saved);
  } catch (error) { notice($("#entryNotice"), error.message + " A restart can recover runs only after an inn checkpoint."); }
});

function renderCoordination(room) {
  const members = room.players.filter((p) => p.id !== room.you);
  const signature = JSON.stringify(members.map((p) => [p.id, p.name, p.hp, p.maxHp, p.status, p.connected, p.reviving]));
  if (signature !== lastTeamSignature) {
    lastTeamSignature = signature;
    $("#teamHud").replaceChildren();
    for (const p of members) {
      const row = document.createElement("div"); row.className = "teammate " + (p.connected === false ? "offline" : p.status);
      const label = document.createElement("span"); label.className = "teammate-name"; label.textContent = p.name;
      const status = document.createElement("small");
      status.textContent = p.connected === false ? "Offline" : p.status === "downed" ? "Needs revive" : p.status === "fallen" ? "Fallen" : p.reviving ? "Reviving…" : `${p.hp}/${p.maxHp}`;
      const meter = document.createElement("meter"); meter.min = 0; meter.max = p.maxHp || 1; meter.value = Math.max(0, p.hp);
      meter.setAttribute("aria-label", p.name + " health"); row.append(label, status, meter); $("#teamHud").append(row);
    }
  }
  $("#npcClueHUD").textContent = room.companionClue ? "NPC clue for you: " + room.companionClue : "";
  $("#npcClueHUD").classList.toggle("hidden", !room.companionClue);
  const share = $("#shareClue");
  share.classList.toggle("hidden", !room.puzzle?.cooperative || !room.puzzle?.clue);
  const feed = (room.pings || []).map((p) => `${p.name}: ${p.kind === "help" ? "Help!" : p.kind === "gather" ? "Gather here" : "Attack this enemy"}`).join(" · ");
  if (pingFeed.textContent !== feed) pingFeed.textContent = feed;
  if (room.phase !== "combat" && enemyPingArmed) armEnemyPing(false);
  $("[data-ping=enemy]").disabled = room.phase !== "combat" || !room.enemies.length;
}
function armEnemyPing(armed) {
  enemyPingArmed = armed;
  $("[data-ping=enemy]").setAttribute("aria-pressed", String(armed));
  $("[data-ping=enemy]").textContent = armed ? "Cancel mark" : "Enemy";
  $("#world").classList.toggle("mark-enemy", armed);
  notice($("#combatNotice"), armed ? "Tap an enemy to mark it. Tap Cancel mark to back out." : "");
}
$("#pingButtons").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-ping]"); if (!button || button.disabled) return;
  if (button.dataset.ping === "enemy") { armEnemyPing(!enemyPingArmed); return; }
  try { await sendAction("ping", { kind: button.dataset.ping }); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
});
$("#world").addEventListener("pointerdown", async (event) => {
  if (!enemyPingArmed || !latestRoom) return;
  event.preventDefault(); event.stopImmediatePropagation();
  const rect = event.currentTarget.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width * 960, y = (event.clientY - rect.top) / rect.height * 540;
  const nearest = latestRoom.enemies.reduce((best, enemy) => {
    const distance = Math.hypot((enemy.x - x) * rect.width / 960, (enemy.y - y) * rect.height / 540);
    return distance < (best?.distance ?? 55) ? { enemy, distance } : best;
  }, null);
  if (!nearest) return notice($("#combatNotice"), "Tap closer to the enemy, or cancel the mark.");
  armEnemyPing(false);
  try { await sendAction("ping", { kind: "enemy", targetId: nearest.enemy.id }); refresh(); }
  catch (error) { notice($("#combatNotice"), error.message); }
}, true);
$("#shareClue").addEventListener("click", async () => {
  const puzzle = latestRoom?.puzzle;
  if (!puzzle?.clue) return;
  try {
    await sendAction("shareClue");
    $("#chatPanel").classList.add("hud-open"); $("#toggleChat").textContent = "Close chat"; refresh();
  } catch (error) { notice($("#combatNotice"), error.message); }
});
function drawPings(ctx, room) {
  for (const ping of room.pings || []) {
    if (room.phase === "puzzle" && ping.playerId !== room.you) continue;
    if (ping.phase !== room.phase || (ping.interior || null) !== (room.townInterior || null)) continue;
    const target = room.enemies.find((e) => e.id === ping.targetId);
    if (ping.kind === "enemy" && !target) continue;
    const x = target?.x ?? ping.x, y = target?.y ?? ping.y;
    ctx.save(); ctx.strokeStyle = ping.kind === "help" ? "#ff9292" : "#ffe08a"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(x, y, 29 + 3 * Math.sin(performance.now() / 180), 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = "#101923"; ctx.fillRect(x - 54, y - 59, 108, 20);
    ctx.fillStyle = ctx.strokeStyle; ctx.textAlign = "center"; ctx.font = "bold 12px monospace";
    ctx.fillText(ping.kind.toUpperCase(), x, y - 45); ctx.restore();
  }
}
function renderStats() {
  const room = latestRoom;
  $("#saveStatus").textContent = 'This session is held in server memory. '+(room?.checkpointSavedAt ? "Disk checkpoint: inn after stage "+room.checkpointStage+' · '+new Date(room.checkpointSavedAt * 1000).toLocaleString() + ". Restart recovery returns to that bed; later progress is lost." : "No disk checkpoint yet. A server restart loses this run; rest at an upstairs inn bed to set a checkpoint.");
  const box = $("#overallStats"); box.replaceChildren();
  for (const player of cachedRunTotals) {
    const section = document.createElement("section"); section.className = "run-total";
    const title = document.createElement("h3"); title.textContent = player.name + " · " + (player.class || "Adventurer");
    const metrics = document.createElement("dl"); metrics.className = "run-metrics";
    for (const [field, label] of [["damageDealt", "Damage dealt"], ["damageTaken", "Damage taken"], ["revives", "Revives"], ["deaths", "Deaths"], ["kills", "Kills"]]) {
      const pair = document.createElement("div");
      const name = document.createElement("dt"); name.textContent = label;
      const value = document.createElement("dd"); value.textContent = player[field].toLocaleString();
      pair.append(name, value); metrics.append(pair);
    }
    section.append(title, metrics); box.append(section);
  }
}
let cachedRunTotals = [];
$("#openStats").addEventListener("click", async () => {
  try {
    const reports = await api("/api/stats?room=" + encodeURIComponent(session.room) + "&player=" + encodeURIComponent(session.player));
    if (!latestRoom) return;
    cachedRunTotals = reports;
    renderStats(); openInfo("statsDialog");
  } catch (error) { notice($("#combatNotice"), error.message); }
});
$("#downloadStats").addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(cachedRunTotals, null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url; link.download = "gauntlet-run-stats.json"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
