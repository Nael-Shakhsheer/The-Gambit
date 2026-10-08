# The Gauntlet sound effects

"BXFR" was interpreted as **Bfxr**, verified against https://www.bfxr.net/.
This bank uses Bfxr's actual DSP, rather than a newly written approximation.
No account, editor, audio API key or external connection is needed to play.

## Rebuild and tune

Run `node art/audio/build-sounds.cjs` from the project folder. Node is needed
only for rebuilding, not for the Python server or players. The builder uses
the standard library and the retained Bfxr sources; no npm install is needed.
It resolves every path from its own location so copying the project is enough.

`sounds.json` holds explicit Bfxr parameters and individual deterministic noise
seeds. Adjust a recipe, rebuild, and refresh the HTTP game page. `metrics.json`
records duration, RMS and byte size. Exported WAVs are mono 44.1 kHz / 16 bit,
trimmed, peak bounded to 0.65 and given short fades to avoid boundary clicks.
The entire bank is about 400 KB. Sounds range from 63 to 590 milliseconds.

To refine a sound manually in the Bfxr web editor, use the corresponding
parameters as a starting point and export a WAV to `static/audio/NAME.wav`.
Retain the editor's sound data alongside this manifest. A builder run replaces
the shipped WAVs, so incorporate intentional edits into the recipe first, or
back up manually exported replacements. These recipes use Bfxr2 JSON parameter
names; they are not legacy `.bfxr` serialized files.

## Runtime feedback

`static/audio.js` owns Web Audio playback and settings. `app.js` observes each
fresh server snapshot once, independently of canvas drawing and interpolation.
Accepted hero animation timestamps distinguish class Light, Special and
Ultimate sounds. The existing damage counter (with HP fallback), status
transitions, effect IDs, chest outcome notices and town state provide the other
cues. No new gameplay action, save field, event protocol or server rule is used.
This is a snapshot-based first audio pass; extremely brief events between polls
can be missed, rather than guessed from inputs.

| Feedback | Bank cues |
| --- | --- |
| Knight / Rogue Light | blade |
| Archer / Wizard / Druid Light | bow / magic |
| Cleric / Bard / Healer Light | potion / bard / heal |
| Specials / Ultimates | special / ultimate |
| Dash / hits / local damage | dash / hit / hurt |
| Healing / downing / rescue | heal / down / revive |
| Chest outcomes / curse | loot / curse |
| UI / town / checkpoint | select / interact / heal |
| Stage clear / victory / puzzle | clear |
| Ambush / dragon phase two | warning |
| Projectile and terrain impacts | impact |

Nearby sounds attenuate with distance and pan gently where supported; local
hero damage/abilities get higher priority. Ten simultaneous voices, per-cue
rate limits and a compressor bound crowded party audio. Mute stops active
voices and the master gain ramps changes. There is no soundtrack or ambience
loop in this pass.

Sound settings are accessible from the main menu and in-game Menu. Default
effects volume is 45%; mute and volume persist per browser/site under
`gauntlet-audio`. Test sound respects mute and zero volume. A trusted pointer or
key gesture creates/resumes the audio context and loads the WAVs. Rejected
autoplay, unavailable Web Audio, storage restrictions or failed assets cannot
block gameplay. The settings report their state. Before activation, on a fresh
room/stage, after a gap over 750ms and when the page hides/loses focus, no old
sounds are queued or replayed. Browser refreshes load changed assets.

## Source and licenses

The five unchanged JavaScript files in `vendor/` were retrieved on 2026-10-07
from https://github.com/osiriswd/bfxr2-cli (main archive). They contain the
Bfxr 1.0.4 DSP, parameter model and sample-buffer code. `vendor-hashes.json`
pins the retained source contents. The Gauntlet builder uses an isolated VM
with a minimal in-memory AudioBuffer and seeded PRNG, instead of executing the
upstream CLI or installing its MP3 dependencies. It uses square, sine,
triangle and white-noise waves only; the optional sampled wave tables are
not included or used.

The upstream MIT license credits Stephen Lavelle. `Bfxr_DSP.js` also retains
Thomas Vian's Apache 2.0 notice for the ported SfxrSynth code. Both license
texts are retained in `vendor/`; source headers remain unchanged.

## Checks

`node tests/test_audio.cjs` exercises activation, confirmed attack changes,
deduplication, dash/damage/down/revive/loot, silent reconnects, hidden tabs,
mute and burst limits, and validates each WAV's format, size and peak bounds.
`node --check static/audio.js` checks syntax. Existing client and Python tests
still apply. Human headphone listening and real phone audio-policy checks are
needed for final mix decisions; automation cannot judge musical taste or
speaker loudness.
