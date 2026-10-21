# Rodina — co-op session notes

Session date: 2026-10-20
Agent: OpenCode agent on the owner's PC (Windows). Repo downloaded as a zip (git not
installed yet). Game path below was read **read-only**; nothing was modified or copied
yet.

## Phase 0 — Triage: answers

### 1. Which exact game

| Field | Value | Source |
|---|---|---|
| Title | Rodina | Steam app 314230 |
| Developer / publisher | Elliptic Games (Brendan Anthony) | store page |
| Store | **Steam** (owner's copy; appmanifest_314230.acf present) | `F:\SteamLibrary\steamapps\steamapps`? → `F:\SteamLibrary\steamapps\appmanifest_314230.acf` |
| Version | **1.6.5** ("Player Stats and Power Systems + Atmospheric Lighting Patch") | `README.txt` in install |
| Steam buildid | 10958618 | appmanifest_314230.acf |
| Steam depots | 314231, 314232 | appmanifest |
| Last updated (manifest) | epoch 1792550612 | appmanifest |
| Platform | Windows, DirectX 11 required | README.txt |
| Size on disk | 240,491,486 bytes (≈240 MB) | appmanifest |
| Save format | EGON binary (since 1.5.0); saves in `UserData\*.egs` | README.txt version history |

### 2. Already done? No.

Searches run for existing co-op/multiplayer work — all negative:

1. `grep -i rodina` across the whole coop-anything repo (DIRECTORY.md, games/, data/) — 0 hits.
2. coop-anything issues search `rodina` — 0 results.
3. GitHub repository search `rodina multiplayer` — 0 results.
4. Web searches ("Rodina co-op mod", "Rodina multiplayer mod", "Rodina Elliptic
   multiplayer fan project") — only unrelated **Rodina Online** (a Russian life-sim
   mobile game on Google Play) and single-player content mods.
5. ModDB Rodina mods page — content mods only, no MP entry (page is partly JS-driven;
   automated fetch limited, noted per research.md).
6. Nexus Mods Rodina (98 mods) — content mods per index listing.

Developer status: multiplayer is a **long-term wish**, never shipped. Steam EA FAQ:
"If RODINA ever gets a major new feature like Multiplayer, I will increase the price."
Steam guide "Ultimate Rodina Guide" lists `Multiplayer` under FUTURE GOALS.
(Source lines, not a claim that it works.)

Not yet run: archive.org sweep, r/Rodina + Discord mining, Nexus comment mining.

**Path: 2 — build from zero.** Nothing to revive.

### 3. Engine

Custom engine, written from scratch by the developer (ModDB lists Engine: "Custom";
press kit: "The game and procedural engine were programmed from the ground up by
Brendan"). Not Gamebryo/Creation, not Unity, not Unreal.

Measured from the install (read-only, `Rodina.exe`, 13,221,888 bytes):

- **Native C++ / DirectX 11** — imports `d3d11.dll`, `dxgi.dll`, `d3dcompiler_47.dll`,
  `XINPUT1_3.dll`, `WSOCK32.dll`, `ole32.dll`, `urlmon.dll`, `dbghelp.dll`.
  No .NET/CLR marker (not managed, so no dnSpy/BepInEx route).
- **Lua 5.1 embedded** — string `Lua 5.1`, symbol `lua_pcall`, `luaopen` present.
- **Havok physics** — string `Havok StackTracer: hkStackTracer`.
- **SFML 2** for audio/system (`sfml-audio-2.dll`, `sfml-system-2.dll`), **OpenAL**
  (`openal32.dll`).
- **Steamworks** (`steam_api.dll`) — Steam Cloud saves + update checks.
- **Dear ImGui** — F9/F10/F11 debug pages, `imgui.ini` present.
- No SDL, no RakNet, no ENet, no PhysX/Bullet-marker beyond a single "Bullet" string.

Main exe hashes (record before following any write-up):

```
Rodina.exe        D8E8EBEAC6D45A935CB52CC105BABB5D38EB55277BAF8124702AE06B8F5ED397
Rodina_Steam.exe  C7A0AADCE10AA8612C89CBDF286DF9AF58A68555BD9304259BC1FC961F8194CE
```

Exe version resource is empty (no FileVersion/ProductName) — identify by hash + README.

### 4. How much source is there

- **105 gameplay Lua scripts** ship with the game under `<game dir>\Scripts\Gameplay\`
  (`EGGame.lua`, `EGPlayer.lua`, `EGScene.lua`, `EGShipPlayer` data, `EGActor.lua`,
  `EGInterior.lua`, all `EGMenu*`, all `EGCharBehaviorXeno*`, …), plus 36 `DataGameplay`
  data scripts, `EGCore.lua`, `EGUtility.lua`, `EGConstants.lua`, and a class system
  (`EGMakeClass( "EGShipPlayer", "EGVehicle" )`).
- Scripts are plain text, user-editable, located by walking up from the exe (no absolute
  path in the binary — the exe only stores `EG_DIR_SCRIPTS` + `\UserScript.lua`).
- **Mod system**: `<game dir>\Mods\LoadOrder.lua` with a `ModList = { }` table; the exe
  logs `InitMods: Mods\LoadOrder.lua loaded.` / `InitMods: Registering Mod (`.
  Mods add/replace Lua classes ("surgical modding", allowlist a dialogue/menu).
- **UserScript.lua**: the exe references `EG_DIR_SCRIPTS + "\UserScript.lua"`; the
  actual filename is **case-variant** (1.2.4 notes: "UserScript.lua file allows users to
  execute custom code"). Not present on disk in this install, so the real name must be
  confirmed before relying on it.
- **EGSL** (`.rsl`) production scripts exist but are generation-side; **engine-side
  handlers for them were stripped in shipping builds** — the exe only contains the
  `Error compiling EGSL: Scripts\<file>.rsl` strings, i.e. EGSL editing is not available
  to players.
- No decompilation yet. Code is native; Ghidra/IDA would be needed to read engine
  internals.

### 5. Does the engine have any multiplayer

**No.** Evidence:

- Steam store page: Features: Single-player, Steam Cloud, Family Sharing. Not
  multiplayer, not co-op, not remote play together.
- No network library in the binary (no RakNet/ENet/Steam networking strings).
  `WSOCK32.dll` is a standard Winsock 1.x import (legacy link), not evidence of netcode.
- The developer lists Multiplayer only as a future goal.
- No server browser, no master server URL, no Steam lobbies in the strings.

### 6. Shipping check

- Single-player, offline-capable game, **no anti-cheat, no online service** to stay away
  from. Steam Cloud saves only → watch out for Cloud syncing a modded save back.
- A co-op add-on can ship as **Lua mod files + a small native DLL/injector** (no game
  files, no assets) → legal per the repo rules.
- Steam relay (Spacewar appid 480) can carry the traffic → no port forwarding, friends
  buy nothing extra.

## Derived (my conclusions — labelled as derived, not observed)

- Rodina is a **host-authority + state-sync** job with **no netcode to build on**. The
  good news over most "closed binary" games: the entire **gameplay layer is Lua source**,
  so entity/AI/story/progression logic can be hooked and re-implemented in scripts
  rather than by reverse-engineering native code first.
- Cheapest first slice: **player ghost** (two players see each other and can fly
  together), then shared enemies, then world/story state. This matches the
  `how-coop-mods-work.md` staging.
- Risk to check early: how much of the entity/physics state is reachable from Lua
  (position/rotation of actors, spawn/despawn, damage, interior maps). If Lua can't see
  or set enough, a native Lua-binding DLL becomes necessary — much bigger job.
- Determinism: physics is Havok and Lua `math.randomseed(os.time())` is used on start,
  so **lockstep is out**; host authority is the right model.

## Guesses (labelled, unverified)

- guess: `WSOCK32.dll` + `urlmon.dll` are leftover/utility imports (update check, HTTP
  download via `URLDownloadToFileA`), not netcode.
- guess: the engine exposes `System.*`/`EG*` script bindings broadly enough that a Lua
  mod can move and spawn entities, based on `System.BeginStartGame()`,
  `System.SetCurrentScene()`, `System.ReloadShaders()` seen in shipped scripts.

## Unknowns (open questions)

- Exact `UserScript.lua` filename/flag (`--userscript`? case-sensitive path?) — must be
  observed, not assumed.
- Whether Lua holds a direct handle to the local player entity, and whether a second
  "player-like" actor can be created and driven by script.
- How interiors/savegames/EGON serialise actors (needed for host→client world state).
- Whether the owner's friends all own Rodina on Steam (needed for Steam relay matchmaking).
- Tooling: none installed yet (git, Python, Ghidra, VS/MSVC all unconfirmed).

## Next actions (proposed, all need owner consent per ground rule 1)

1. Install git + gh (owner already approved) → fork, branch `game/rodina`, keep notes.
2. Copy the install to a **test folder** (never edit `F:\SteamLibrary\...\Rodina`).
3. Launch a copy with logs enabled, confirm the script/mod load path and `UserScript.lua`.
4. Read `playbook/how-coop-mods-work.md`, `networking-steam-spacewar.md`,
   `reverse-engineering.md`, then write a design doc: networking model, first slice,
   test plan (bots per `automated-qa.md`).
5. Open a "claim a game" issue on coop-anything so other agents can find this work.
