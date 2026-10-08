// Town character and hovering chest sprite renderer. No gameplay state changes.
(() => {
  const images = new Map();
  const directions = ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"];
  const characters = ["Merchant", "Guildmaster", "Alchemist", "Innkeeper", ...Array.from({ length: 8 }, (_, i) => "Villager" + String(i + 1).padStart(2, "0"))];
  for (const key of [...characters, "TreasureChest"]) {
    const image = new Image();
    const path = key === "TreasureChest" ? "/sprites/treasure-chest" : "/sprites/" + key.toLowerCase() + "-idle";
    const entry = { image, metadata: null };
    images.set(key, entry);
    image.src = path + ".png";
    fetch(path + ".json").then((response) => {
      if (!response.ok) throw new Error("Town sprite metadata unavailable");
      return response.json();
    }).then((metadata) => { entry.metadata = metadata; }).catch(() => { entry.metadata = null; });
  }
  function ready(key) {
    const entry = images.get(key);
    return entry?.metadata && entry.image.complete && entry.image.naturalWidth ? entry : null;
  }
  function character(ctx, key, x, y, options = {}) {
    const entry = ready(key);
    if (!entry) return false;
    const sheet = entry.metadata.spritesheet;
    const direction = directions.includes(options.direction) ? options.direction : "south";
    const row = sheet.rows.find((candidate) => candidate.type === "animation" && candidate.direction === direction);
    const frames = entry.metadata.animations[options.mode || "idle"] || entry.metadata.animations.idle;
    if (!row || !frames?.length) return false;
    const column = frames[Math.floor((Date.now() + (options.phase || 0)) / 180) % frames.length];
    const cell = sheet.cell_size;
    const scale = options.scale || 1;
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(entry.image, column * cell.width, row.row * cell.height, cell.width, cell.height,
      x - 32 * scale, y - 42 * scale, 64 * scale, 64 * scale);
    ctx.restore();
    return true;
  }
  function chest(ctx, entity) {
    const entry = ready("TreasureChest");
    if (!entry) return false;
    const sheet = entry.metadata.spritesheet;
    const mode = entity.opened ? "open_float" : "float";
    const animation = entry.metadata.animations[mode];
    if (!animation?.frames?.length) return false;
    const column = animation.frames[Math.floor(Date.now() / animation.frame_duration_ms) % animation.frames.length];
    const cell = sheet.cell_size;
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(entry.image, column * cell.width, animation.row * cell.height, cell.width, cell.height,
      entity.x - 38, entity.y - 34, 76, 76);
    ctx.restore();
    return true;
  }
  window.GauntletTownSprites = { character, chest };
})();
