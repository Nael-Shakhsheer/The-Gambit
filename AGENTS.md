# Project instructions

Read `PROJECT_CONTEXT.md` and `README.md` before working on this project. They
carry the handoff context for The Gauntlet between computers and new chats.

- The user prefers ordinary implementation work to proceed without repeated
  approval requests. Ask for missing information only when it materially blocks
  the task, and flag concrete unsafe actions.
- The user explicitly authorizes server restarts needed for updates without
  asking again (2026-10-07). Back up existing bed checkpoints before restarting;
  live rooms remain in memory and reset on restart.
- Preserve the existing Python server and browser client architecture.
- `GAME_DESIGN.md` contains earlier planning. The latest user instructions and
  actual implementation take precedence over its outdated sections.
- Update `PROJECT_CONTEXT.md` when a change materially affects the game or its
  setup, so the next session can continue from the correct state.
- Use paths relative to this project in the application. The original home PC's
  drive letters and Python installation path must not become requirements.
- Run `python server.py` from the project folder and use the HTTP address in
  `README.md`. Opening `static/index.html` directly causes API connection errors.
- Live rooms run in memory; upstairs inn beds set checkpoints in `data/checkpoints/`
  and restore at that bed after a restart. Talking to the innkeeper does not save.
  Progress after leaving the saved village, and runs before their first bed
  checkpoint, are not persisted. Preserve `data/` when transferring
  saved games. Static client/sprite changes need a refresh; Python changes need
  a server restart. See README.md for browser identity and reconnect details.
