# Rodina co-op — design doc

Status: **draft, pre-probe.** Nothing here is verified against a running game yet.
Written before Stage 1 so the probe can be judged against a plan rather than ad hoc.

Game identity: see [NOTES.md](NOTES.md). Steam 314230, v1.6.5, buildid 10958618,
`Rodina.exe` SHA-256 `D8E8EBEA…5ED397`. A different build invalidates this document.

Related playbook pages: [how-coop-mods-work.md](../../playbook/how-coop-mods-work.md),
[networking-steam-spacewar.md](../../playbook/networking-steam-spacewar.md),
[automated-qa.md](../../playbook/automated-qa.md).

---

## 1. Target

Two (later more) friends, each running their own Steam copy of Rodina on their own PC,
sharing one solar system: they see each other, fly together, fight the same Xeno, and
share story progress. No port forwarding; friends join from the Steam friends list.

Split screen is explicitly out of scope for now.

## 2. The constraint that shapes everything

Rodina has **no netcode at all** (evidence in NOTES.md: no network library, single-player
only on the store page, multiplayer is only a developer wish). So there is nothing to
make network-aware — a sync layer has to be built from nothing and retrofitted onto an
engine that was never designed for it.

Two things make that better than the usual closed-binary case, and both are the reason
this is worth attempting:

1. **The whole gameplay layer is Lua 5.1 source** — 105 scripts in
   `<game dir>\Scripts\Gameplay\` (`EGGame.lua`, `EGPlayer.lua`, `EGActor.lua`,
   `EGInterior.lua`, every Xeno AI behaviour, every menu). Entity, AI and story logic
   are readable and writable without touching native code.
2. **There is an official mod loader** — `<game dir>\Mods\LoadOrder.lua` and a
   `UserScript.lua` hook the exe looks for. Mods add or replace Lua classes, and 1.2.1
   notes mention "surgical modding", so mods can override narrowly.

And two things make it worse, which is why §4 is a go/no-go probe:

1. **Physics is Havok.** Determinism cannot be relied on, so lockstep is off the table;
   this must be host-authoritative state sync, the more expensive model.
2. **We do not yet know how much state Lua can see or set.** If Lua can only touch the
   local player, the work balloons into a native Lua-binding DLL plus reverse
   engineering of the entity graph — a different, much larger project.

## 3. Networking model

**Host-authoritative state sync.** Decided by evidence, not taste:

| Option | Verdict |
|---|---|
| Deterministic lockstep | **Rejected.** Requires bit-exact determinism and a fixed timestep; Havok physics plus `math.randomseed( os.time() )` in `GameplayMain.lua` rule it out. |
| Client-authoritative / per-player simulation | **Rejected for enemies.** Produces the "each player has their own Xeno" failure (HKMP-style), which is not co-op for this game. |
| **Host authority + state sync** | **Chosen.** No determinism needed, only the ability to read/write entity state — exactly what the Lua layer may provide. This is what retrofits onto closed games. |

Constraint found while checking the transport (§5): Rodina is a **32-bit** game, so every
DLL we build or load must be 32-bit.

Concretely: the host runs all AI and physics for shared entities and broadcasts state;
clients send their own player state and "I hit X" claims; the host validates and
broadcasts results. Clients apply results **as state, never by re-running the game's own
logic** — the Gothic 3 lesson, where re-running a mirrored death re-ran loot and quest
side effects a second time.

Per-entity authority:

| Entity | Owner | Notes |
|---|---|---|
| Local player | that player | clients send their own pos/rot/animation |
| Remote player | the player themselves (puppet on others) | interpolated, never reads local input |
| Xeno / alien ships | **host** | clients mirror; hits are claims |
| Projectiles | shooter, results validated by host | start simple: host-spawned |
| Interiors, doors, fires, atmosphere | host | 1.5.0 added persistence, so there is a state store to piggyback on |
| Story flags / progress | host | see §6 |
| Loot / pickups | host | spawn once, so both players cannot loot the same drop |

## 4. The go/no-go probe (do this before any netcode)

This is the cheapest experiment that can cancel the project, so it runs first. Goal: find
out whether the Lua layer is a sufficient hook point.

Questions the probe must answer, each with an observed yes/no and a log line as evidence:

1. **Does a mod load at all?** ~~Known obstruction~~ **Solved and confirmed yes
   (2026-10-20).** The gate was the exe, not the schema: `Rodina.exe` (Standalone) can
   never register; `Rodina_Steam.exe` (+ `steam_appid.txt` 314230, Steam client running)
   registers as Tier Buffet and loads mods. Schema: `ModList = { "Mods\\<dir>", … }` —
   an array of directory path strings; mod files mirror the game root tree and load
   **after** the base scripts (`Loading Mod Script:` log line). Marker executed:
   `Loading Mod Script: mods\coopprobe\Scripts\Gameplay\EGMenuRegister.lua` →
   `[CoopProbe] mod file executed`. Full evidence: NOTES.md P4/P7.
2. **What is the user-script hook really called?** The exe references
   `EG_DIR_SCRIPTS + "\UserScript.lua"`; the file does not exist in this install. The
   1.2.4 notes call it `UserScript.lua`. Determine whether the name is case- or
   path-sensitive, whether it must be created, and whether a flag is needed.
3. **Can Lua read the local player's state?** Position, rotation, world id / scene,
   current interior, velocity. `EGPlayer.lua` / `EGActor.lua` / `EGScene.lua` should
   show the accessors.
4. **Can Lua create a second player-like actor** (the puppet), set its position and
   rotation every frame, and keep the engine from culling or AI-controlling it?
   This is the make-or-break question and the one flagged in the playbook as usually
   taking the longest.
5. **Can Lua enumerate nearby actors** — Xeno, ships — with enough state to mirror them
   (id, position, health, alive/dead)?
6. **Can Lua write** health/damage/death without re-running death side effects?
7. **What does `GameplayMain.lua` do per frame?** Find the update hook we can piggyback
   on and measure its cost, so we know the frame budget for sync.
8. **Is there a debug console?** F9/F10/F11 ImGui pages and `System.EnableDebugText` are
   referenced in scripts; a console is the fastest way to poke at the API live.

How the probe is run, per ground rule 2: **copy** the install to
`local\rodina-test\`, work only there, never in `F:\SteamLibrary\...\Rodina`. The probe is
a throwaway mod plus a log reader. It modifies nothing in the shipping Lua tree unless a
reverted backup is made first.

**Decision rule, written before the result so it cannot be rationalised afterwards:**

- **Lua can create and drive a second actor** → proceed to Stage 2. This is the good
  outcome and makes the whole thing tractable.
- **Lua can read but not create** → proceed, but the puppet has to come from cloning an
  existing actor class. Narrower, still viable; document the trick.
- **Lua can do neither** → **stop and report.** A native Lua-binding DLL
  (registering new `System.*` functions) plus RE of the entity graph would be required.
  That is a different project with a much worse playbook estimate
  ("closed native engine, no loader": combat sync measured in months, full campaign
  "likely out of scope"). The owner decides then, not me.

I will not start netcode before this probe reports, and I will report a negative result
as plainly as a positive one.

## 5. Transport

Chosen: **Steam relay via Spacewar (AppID 480)**, per
[networking-steam-spacewar.md](../../playbook/networking-steam-spacewar.md). Friends join
from the friends list; Valve's relay handles NAT; nobody buys anything.

Constraints to honour from that page:

- Rodina's own `steam_api.dll` is **too old** for the flat API (the page warns about
  exactly this, citing Fallout New Vegas) — **checked and confirmed**: the install's DLL
  (859 exports) has `SteamAPI_Init` and the old-style lobby calls but **no
  `SteamAPI_InitFlat`, no `ManualDispatch`, and zero `SteamAPI_Steam<interface>_vNNN`
  getters at all** (see NOTES.md P2). So the pinned Steamworks.NET standalone x86 DLL is
  required, shipped beside our own helper rather than swapped over the game's copy, since
  the game still needs its own DLL for Cloud saves and its update check. Rodina is a
  **32-bit** game (confirmed from PE headers), so the x86 DLL and the 32-bit struct
  offsets apply (`SteamNetworkingMessage_t.size` at offset 4, sender identity at 16).
- Lobbies: friends-only, plus a lobby data key (e.g. `rodinacoop=1`) so we never join
  someone playing the real Spacewar.
- No disconnect event in `ISteamNetworkingMessages`: control channel with goodbye and a
  1 s keep-alive; 20 s silence drops a peer; answer keep-alives even before game data
  (`LobbyChatUpdate` left/disconnected and `SessionFailed` also drop).
- `LobbyCreated` arrives twice on real Steam (703 call result and 513 broadcast) —
  handle idempotently.
- No peer until `AcceptSessionWithUser`: host accepts strangers, clients accept only host.

Test transport: a `--transport udp|steam` switch, so two clients on one PC test over
localhost UDP (with built-in lag/loss simulation, or the repo's `tools/chaos` relay)
while the real path uses Steam. The same code then serves the automated tests.

Two clients on one PC: **confirmed possible without any mutex patching** — Rodina imports
no mutex APIs, and two copies launched from the same folder both reached `BEGIN GAME`
(NOTES.md P3). They do share one `UserData\` and one `RodinaLog.txt`, so automated tests
need per-instance installs (or a redirected user dir) to keep saves and logs separate.
`tools/gamepool`/`gameslot` exist for running several copies safely.

## 6. Story and world state

Rodina's story is told through books, emails and logs, with progress tracked in
`Scripts\DataGameplay\EGDataProgress.lua` and player state in `EGPlayerInfo.lua`
(`GetInventoryCount`, `SetInventoryCount` are already visible in `EGDataShipPlayer.lua`,
so inventory is script-addressable). 1.5.0 added "persistence of actors and interiors" —
the engine gained "a generalized way to store object properties", which is the promising
hook for world state.

Plan, in the order the playbook recommends:

1. Locate the actual flag/progress store rather than assuming `EGDataProgress.lua` is it.
2. Intercept writes at the lowest common function and replicate from the host.
3. Re-entrancy guard: applying a received write must not re-broadcast it.
4. Snapshot-on-join: dump the store, send, apply, then stream deltas. This doubles as the
   reconnect path and the test oracle (compare store hashes).
5. Policy decision for dialogue and cutscenes — **unknown until tested.** Default to
   "host chooses, others see the outcome as text", per the Skyrim Together pattern.

## 7. Saves and transitions

- **Canonical save is the host's.** Clients never overwrite their own saves in a session.
- Rodina saves are **EGON binary** `*.egs` in `UserData\`, synced by Steam Cloud — watch
  for Cloud pushing a modded save somewhere unexpected.
- Before risking this, check the Gothic 3 lesson: whether a save taken with a puppet in
  the world breaks on load. If so, hook the save function to strip puppets first, and keep
  the mod's own state in a sidecar file.
- Every level change / planet transition / interior entry re-syncs the full snapshot.
  Assume entity ids change across a load.
- 1.6.4 fixed a "multithreading issue with thread tasks (savegames)", so saving is
  threaded — do not assume the save path is single-threaded when hooking it.

## 8. Build order and honest scope

Stages from the playbook, with the exit test for each. No stage is "done" without its
test, and a human playtest is not a test.

| Stage | Exit test |
|---|---|
| 0. Recon | Notes written, prior art search negative, identity recorded. **Done.** |
| 1. Hook point | **Probe (§4).** Mod code logs player position each frame from inside the game. |
| 2. Puppet | Client A's script walks in a circle; host sees a puppet doing the same within tolerance. |
| 3. Authority | Both clients damage the same Xeno; same health and death on both; the drop appears once. |
| 4. World/story | Host advances a quest, client reads the same stage; a third late joiner gets an identical store hash. |
| 5. Transitions/saves | 15 scripted transitions with matching checksums after each (the Deus Ex soak number). |
| 6. Automated two-client tests | Scenario suite (walk, fight, quest, transition, reconnect) green, with loss and latency injected. |

**Honest scope statement.** The playbook's own table puts this game in "closed native
engine, no loader": players visible in *weeks*, combat in *months*, full campaign
*likely out of scope*. The Lua gameplay layer is what moves Rodina out of that column,
but it does not remove the risk. Milestones in order of realistic deliverability:

1. Two players see each other and fly together — **the goal worth committing to.**
2. Shared Xeno combat.
3. Shared story progress.
4. Full campaign — explicitly **not promised** by this document.

## 9. Open questions (kept open on purpose)

- ~~Does `steam_api.dll` in the install export the flat API?~~ **Answered: no.** See
  NOTES.md P2 — the pinned 32-bit Steamworks.NET DLL must be shipped beside our helper.
- ~~Is there a second-instance mutex?~~ **Answered: no.** Two copies ran at once from the
  same folder (NOTES.md P3). Per-instance `UserData` still needed for clean tests.
- ~~What is the correct schema for `Mods\LoadOrder.lua`?~~ **Answered.** Array of mod
  directory path strings; mods must run as `Rodina_Steam.exe` (NOTES.md P4/P7). The
  "registration is not valid" gate was the standalone exe, not the file.
- How much of the entity graph does Lua actually expose? (§4 decides the project)
- Can the engine be made to run two "player" entities, or does the player object assume
  singularity the way Bethesda's hero does?
- What exactly does `EGSL` (`.rsl`) do for interiors, and does it matter for world sync?
  (Engine-side handlers appear stripped in shipping builds.)
- Do mods need identical copies on every machine? (STALKER's server checksums its addons;
  if Rodina does something similar, versions must match or sync breaks in confusing ways.)
