# Agent House — Claude Code Visual

A fun project to build with Claude Code. Give Claude the prompt below exactly as written.

---

## The Prompt

```
I want you to build something called "Agent House" — an animated visual that opens in my browser automatically whenever you spawn sub-agents to work on a task.

Here's the concept: a top-down 2D pixel art environment styled like an old Pokemon game (think Pokemon Red/Blue overworld). Inside the house are multiple rooms, and each room has pixel-art workers (little sprites with walk animations) that represent the agents you've employed. Workers appear when an agent starts running, move around their assigned room doing their task, and fade out when the agent finishes.

Here is the full spec:

## Architecture

Three files to create, plus a hook in settings.json:

1. `~/.claude/agent-house/server.js` — A tiny Node.js HTTP server on localhost:3747 that:
   - Serves index.html at /
   - Exposes a /state endpoint that reads ~/.claude/agent-manager/state.json and returns it as JSON
   - Exposes a /ping endpoint that returns "ok"
   - Writes its PID to ~/.claude/agent-house/.pid on startup

2. `~/.claude/agent-house/launch.js` — A launcher script that:
   - Pings localhost:3747/ping with a 500ms timeout
   - If the server is NOT running: spawns server.js as a detached background process, waits 800ms, then opens http://localhost:3747 in the default browser
   - If the server IS running: does nothing (the tab is already open — no tab spam)
   - On Windows use: exec(`cmd /c start "" "http://localhost:3747"`)
   - On Mac use: exec(`open "http://localhost:3747"`)

3. `~/.claude/agent-house/index.html` — The pixel art animation (self-contained, no dependencies):

## index.html spec

Canvas: 800×600px, tile size 20px (40×30 grid), image-rendering: pixelated.
Dark navy background (#0d0d1a), pixel-font monospace UI.
Title bar: "AGENT HOUSE" with a blinking green dot and a live agent counter.
A small legend at the bottom showing active worker names with their colour dots.

### Room layout (exact pixel coords):

Row A (y 0–179, h 180):
- Garden:   x 0,   w 320, floor: grass checkerboard
- Library:  x 320, w 260, floor: wood checkerboard
- Archive:  x 580, w 220, floor: stone checkerboard

Hallway 1: y 180, h 40, full width, stone tiles

Row B (y 220–419, h 200):
- Kitchen:  x 0,   w 220, floor: tile (blue-grey)
- Office:   x 220, w 200, floor: wood
- Lab:      x 420, w 200, floor: lab (light blue)
- Workshop: x 620, w 180, floor: stone

Hallway 2: y 420, h 20, full width, stone tiles

Row C (y 440–599, h 160):
- Living Room: x 0,   w 260, floor: wood
- Security:    x 260, w 260, floor: stone
- Yard:        x 520, w 280, floor: grass

Each room has a darker inner border (3px, strokeRect inset 1.5px) and a small semi-transparent room label in the top-left corner.

### Furniture (draw as coloured rectangles + special shapes):

Garden: 5 trees (layered circle canopy + trunk rect), 4 flowers (yellow circle + stem)
Library: bookshelves along top wall (dark brown rects with coloured book strips), 2 reading tables
Archive: 7 filing cabinets (grey rects with small handle details), 1 desk
Kitchen: stove (dark rect with 2 burner circles), L-shaped counter, kitchen table
Office: 6 desks in a 3×2 grid, each with a monitor rect + green radial glow
Lab: 4 lab benches, 5 flask shapes (rect body + narrow neck, each a different colour)
Workshop: 2 long workbenches, a tool rack on the right wall with peg details
Living Room: sofa (wide purple rect), TV (black rect + screen), decorative rug
Security: wall-mounted monitor panel (5 screen tiles), single desk with monitor
Yard: 4 trees, 2 flowers, a stone path (horizontal rect)

### Worker sprites (drawn entirely with canvas primitives, no images):

Each worker is ~16px wide × 22px tall:
- Drop shadow (ellipse, rgba black)
- Legs: 2 rects (dark #253040), alternating length based on walk frame (sin wave)
- Body: 12×9 rect in the agent's colour, with a darker bottom strip for shading
- Arms: 2 small rects on the sides, swinging opposite to legs
- Head: 10×8 rect in skin tone (#f4c070)
- Hair: 2px strip at top of head in the agent's colour
- Eyes: 2×2 px dots, direction-aware (facing left = one eye, right = one eye, forward = two eyes, back = none)
- Activity dot: small green circle above head that bobs up/down when agent is "running"; hidden when "done"
- Name label: 7px monospace text above head (white when running, grey when done), with 1px dark shadow

Walk animation: 4 frames, advance every 8 game ticks when running, every 18 when done.
Workers are sorted by Y before drawing for pseudo-depth.

### Agent type → room & colour mapping (cover at minimum these types):

code-reviewer:        room=office,   color=#e05050
typescript-reviewer:  room=office,   color=#3178c6
go-reviewer:          room=office,   color=#00add8
python-reviewer:      room=lab,      color=#4b8bbe
rust-reviewer:        room=workshop, color=#ce412b
kotlin-reviewer:      room=office,   color=#e44f9c
java-reviewer:        room=office,   color=#ed8b00
csharp-reviewer:      room=office,   color=#9b4f96
cpp-reviewer:         room=workshop, color=#aa3333
flutter-reviewer:     room=lab,      color=#54c5f8
security-reviewer:    room=security, color=#cc0000
architect:            room=workshop, color=#4488ff
code-architect:       room=workshop, color=#3366ee
planner:              room=library,  color=#ff8c00
Plan:                 room=library,  color=#dd7700
tdd-guide:            room=lab,      color=#9040d0
build-error-resolver: room=workshop, color=#ffd700
e2e-runner:           room=yard,     color=#00ced1
refactor-cleaner:     room=living,   color=#32cd32
doc-updater:          room=library,  color=#87ceeb
database-reviewer:    room=archive,  color=#1e6fcc
performance-optimizer:room=workshop, color=#ff6347
a11y-architect:       room=security, color=#20b2aa
Explore:              room=garden,   color=#daa520
code-explorer:        room=garden,   color=#da70d6
general-purpose:      room=living,   color=#aaaaaa
silent-failure-hunter:room=security, color=#ff4500
type-design-analyzer: room=lab,      color=#8a2be2
pr-test-analyzer:     room=lab,      color=#20b2aa
comment-analyzer:     room=library,  color=#9acd32
healthcare-reviewer:  room=lab,      color=#ff69b4
seo-specialist:       room=garden,   color=#ff8c69
default:              room=living,   color=#cccccc

Name labels should be shortened (strip -reviewer, -resolver, -optimizer, -architect suffixes; truncate to 13 chars).

### State syncing:

The HTML polls http://localhost:3747/state every 1 second (cache: no-store).
On each poll:
- For each agent in state.agents: spawn a worker if id not yet tracked; update status if changed
- When an agent transitions to "done": slow the worker to 0.25 speed, start a fadeTick counter
- After 200 ticks of fadeTick, begin fading alpha by 0.015/frame; remove worker at alpha=0
- Workers not in state.agents at all should also be marked done
- Update the counter display and legend on every state change

### state.json format (written by the existing agent-manager/manager.js):
{
  "agents": [
    { "id": 1, "description": "...", "type": "code-reviewer", "status": "running" },
    { "id": 2, "description": "...", "type": "planner",       "status": "done"    }
  ],
  "total": 2
}

## Hook (add to ~/.claude/settings.json):

Add a second PreToolUse entry for the "Agent" matcher alongside any existing ones:
{
  "matcher": "Agent",
  "command": "node /Users/YOURUSERNAME/.claude/agent-house/launch.js"
}

Use the correct path separator for the OS. On Windows use double backslashes.

## Build order:

1. Create ~/.claude/agent-house/ directory
2. Write server.js — test that `node server.js` starts and http://localhost:3747/ping returns "ok"
3. Write index.html — open directly in browser first, confirm rooms and furniture render
4. Write launch.js
5. Add the hook to settings.json (preserve any existing hooks)
6. Test end-to-end: trigger an Agent tool call, confirm browser opens and workers appear

## Notes:
- index.html is served by the local server, not opened as file://, so fetch() to localhost works fine
- The server reads state.json on every /state request (no caching) so it always reflects current state
- The launch.js "do nothing if server is alive" pattern prevents a new browser tab on every single agent spawn
- Workers in the same room don't collide — they just pick random waypoints within the room's inner bounds (room pixel coords + 26px padding, minus 16px for sprite width and 22px for height)
- For the checkerboard floor, iterate by tile size, alternate fill color based on (tileX + tileY) % 2
```

---

## What it looks like when running

- A browser tab stays open at `http://localhost:3747` for the duration of your Claude Code session
- Each agent you spawn appears as a walking pixel character in its assigned room
- A green dot bounces above running agents; done agents fade out slowly
- The title bar shows a live count ("3 active", "idle", etc.)
- A colour-coded legend at the bottom names every visible worker

## Requirements

- Node.js installed (comes with most dev setups)
- Claude Code with an existing `~/.claude/agent-manager/manager.js` that writes `state.json` — if you don't have this, ask Claude to build the agent manager first, then come back to this
- Windows: default `.html` browser association (standard on any Windows install)
- Mac/Linux: `open` command available (standard)
