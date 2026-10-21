# Rodina — co-op session notes

Session date: 2026-10-20
Agent: OpenCode agent on the owner's PC (Windows). Repo cloned with git (installed this
session); working on branch `game/rodina`. Game install was read **read-only**; nothing
in it was modified. All owner-private state is kept in `local/`.

## Phase 0 — Triage: answers

### 1. Which exact game

| Field | Value | Source |
|---|---|---|
| Title | Rodina | Steam app 314230 |
| Developer / publisher | Elliptic Games (Brendan Anthony) | store page |
| Store | **Steam** (owner's copy; appmanifest_314230.acf present) | `appmanifest_314230.acf` in the Steam library |
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

## Probe results (ran 2026-10-20, read-only)

### P1. Architecture: Rodina is 32-bit

Measured from PE headers (`probe/pe_exports.py`, no toolchain needed):

| File | PE machine |
|---|---|
| `Rodina.exe` | x86 (32-bit), 0x014C |
| `steam_api.dll` | x86 (32-bit) |
| `d3dcompiler_47.dll` | x86 (32-bit) |

Consequence: every DLL we build or load must be **32-bit** (MSVC/mingw `-m32`), and any
`ctypes` probing needs 32-bit Python. This machine has only 64-bit Python 3.13
(`ctypes.WinDLL` on the game's DLL fails with "not a valid Win32 application"), so
`probe/check_steam_flat.py` detects that case and explains it instead of erroring out.

### P2. The game's own `steam_api.dll` cannot drive the Spacewar relay — CONFIRMED

This is the check `networking-steam-spacewar.md` explicitly warns about (it cites the
Fallout New Vegas copy failing for this exact reason). Read the export table directly
(`probe/pe_exports.py`; 859 exports) rather than guessing:

| Symbol | Present |
|---|---|
| `SteamAPI_Init` | YES |
| `SteamAPI_GetHSteamPipe` | YES |
| `SteamAPI_ISteamMatchmaking_CreateLobby` | YES |
| `SteamAPI_ISteamMatchmaking_JoinLobby` | YES |
| `SteamAPI_InitFlat` | **NO** |
| `SteamAPI_ManualDispatch_*` | **NO** |
| `SteamAPI_SteamUser_v023` | **NO** |
| `SteamAPI_SteamMatchmaking_v009` | **NO** |
| `SteamAPI_SteamFriends_v018` | **NO** |
| `SteamAPI_SteamNetworkingMessages_SteamAPI_v002` | **NO** |
| `SteamAPI_SteamNetworkingUtils_SteamAPI_v004` | **NO** |

There are **zero** `SteamAPI_Steam<interface>_vNNN` versioned getters in the whole export
table, so the flat API is not merely a different vintage — it is absent. The DLL is an
old-style (non-flat, C++ interface) build.

**Derived:** the relay must ship the **pinned Steamworks.NET standalone 32-bit
`steam_api.dll`** (`Windows-x86`, release 2025.164.1, SHA-256
`fdafb7c65ec7d4182b42bf92cc8671c68e4dc547cc6e613899d2618a47eb65da`) next to our helper,
per the playbook. We must **not** try to load the game's copy, and we cannot use the
game's existing Steam session through its DLL. Also note both copies cannot simply be
swapped blindly: the game loads its own `steam_api.dll` for Steam features (Cloud saves,
update check), so the relay DLL has to live beside our own helper/loader, not replace the
game's, unless a compatibility test says otherwise.

Status: this closes one open question in `DESIGN.md` §9 and one risk in §5, before any
netcode was written.

### P3. No single-instance mutex — two clients CAN run on one PC — CONFIRMED by running it

Static lead: `Rodina.exe` imports **no mutex APIs at all** (`CreateMutexA/W`,
`CreateMutexExA/W`, `OpenMutexA/W` all absent). Its only named kernel object is
`Local\{C15730E2-145C-4c5e-B005-3BC753F42475}-once-flag`, a one-time-init flag, not an
instance lock. (`probe/check_mutex.py`)

Confirmed empirically, because static evidence is only a lead: launched two copies of
`Rodina.exe` from the same folder (the test copy) and both stayed alive and reached
`BEGIN GAME`. PID 25488 held ~572 MB, PID 22784 ~22 MB; neither exited, neither reported
an already-running error. Both wrote to the same `RodinaLog.txt`.

**Derived:** the two-local-client test rig is viable without mutex patching, which
removes the Nucleus-style workaround from the critical path. Caveat: both instances
shared one `UserData\` directory and one `RodinaLog.txt`, so for clean automated tests
each instance needs its own copy of the whole install (or a redirected user dir) to
avoid save/log collisions. Also note the second instance was still light (22 MB) at the
moment of measurement — it had loaded scripts and started the game, but confirm it
renders and simulates before calling it a usable second client.

### P4. Mod-loading gate — RESOLVED 2026-10-20 (second session)

**Resolved. The gate was never the LoadOrder schema — it was the exe.** Every log that
showed `InitMods: Mods not loaded - registration is not valid` was a run of **`Rodina.exe`
("Game Variant: Standalone Version")**, the pre-Steam keyed build. Every log that showed
`Registration State: OK` / `Registration Tier: Buffet` / `InitMods: Mods\LoadOrder.lua
loaded.` was a run of **`Rodina_Steam.exe` ("Game Variant: Steam Full Version")**, which
derives registration from Steam ownership. The first session only ever ran `Rodina.exe`
directly, so its schema experiments were all tested against a build that can never
register. Observation: the two exes differ only in this (same version id 1060500).

To run `Rodina_Steam.exe` from the test folder **directly** (not via Steam's
"Play" button): create `steam_appid.txt` containing `314230` next to the exe, with the
Steam client running. Without it the exe exits with code 1 after writing exactly three
log lines (`BEGIN LOG`, `VERSION ID`). With it: `Game Variant: Steam Full Version`,
`Steam user ID: 76561197995789990`, registration OK.

### P7. The mod system's actual semantics (all observed on 1.6.5, Steam exe)

1. **Schema** — `Mods\LoadOrder.lua` defines `ModList` as a **flat array of directory
   path strings**. Not tables, not name→path maps:
   ```lua
   ModList =
   {
       "Mods\\CoopProbe",
   }
   ```
   A keyed table (`CoopProbe = { Paths = {...} }`) yields `Item count: 0`. Array of
   strings yields `Item count: N`.
2. **Entry validation** — only entries that are **existing directories** are registered.
   A direct `.lua` file entry and a nonexistent path were both silently skipped (2 of 4
   entries registered). The log line is `InitMods: Registering Mod (N): mods\<lowercased>\`
   (lowercased, trailing backslash appended — cosmetic; the FS is case-insensitive).
3. **Mirror-tree layout** — a mod folder mirrors the game's root tree. The exe exports
   `GetFilesInDirectoryIncludingMods` and knows the roots `Data\`, `Models\`,
   `Interiors\`, `UserData\`, `Scripts\`, `Mods\`. Working layout:
   `Mods\CoopProbe\Scripts\Gameplay\EGMenuRegister.lua`.
4. **Load order = override mechanism** — the log distinguishes
   `Loading Script: Scripts\Gameplay\EGMenuRegister.lua` (base, ~5 s) from
   `Loading Mod Script: mods\coopprobe\Scripts\Gameplay\EGMenuRegister.lua` (~12 s,
   after the whole base tree). Mods load **after** and therefore win — this is the
   "surgical modding" the 1.2.1 changelog describes. DESIGN.md §4 Q1 answered: **yes, a
   mod loads and its code runs.**
5. **`Valid path count:` in the summary** — semantics still unknown (labelled unknown):
   it stayed 0 while mods were registered but had no files, and became 2 when the first
   mod file existed (2 mods, 1 file → 2, so it is not a file count). It does **not**
   gate registration — `Registering Mod (` appeared even at 0. Do not chase this until
   something real depends on it.
6. **`print` is not available in mod scripts** (or at init time): a marker using
   `print(...)` never appeared and the run reported `Valid path count: 0`. The same file
   with `System.Log("...")` logged fine and validated. `System.Log` is the channel the
   shipped scripts use (`EGActionBindings.lua:371`).

Test state left behind (all in gitignored `local/rodina-test\`): `steam_appid.txt`,
`Mods\LoadOrder.lua` (candidate D, two dirs), `Mods\CoopProbe\Scripts\Gameplay\
EGMenuRegister.lua` (marker only), `Mods\CoopEmpty\` (empty control), backups
`LoadOrder.lua.orig` (pristine) and `LoadOrder.lua.candidateB.bak`.

### P5. Confirmed script pipeline and the actor API shape

From a normal launch log (`local/rodina-test/RodinaLog.txt`):

- `Generation Compile EGSL: Scripts\*.rsl` → `Generation Compile EGSL Complete`
  (EGSL compiles at runtime on the generation side after all).
- `Loading Script: Scripts\Gameplay\EGActor.lua`, `EGPlayer.lua`, `EGPlayerInfo.lua`, …
  — the whole 105-script gameplay tree loads by name.
- `Start Game` → `Current Scene: 2059` → **`Player Camera Actor: EGPlayer`** and
  **`Player Controlled Actor: EGPlayer`**.

The last two lines are the most useful thing found so far: the engine logs the entity it
treats as the camera and the entity the player controls, which tells the probe exactly
where the local player lives (`EGPlayer`), and implies the engine has the notion of
"controlled actor" that a puppet would need to be excluded from.

### P6. Test copy prepared

`local\rodina-test\` — full copy, 263 MB, `Rodina.exe` hash matches the install
(`D8E8EBEA…5ED397`). Pristine backups kept: `Mods\LoadOrder.lua.orig`,
`RodinaLog.txt.orig`. `local/` is gitignored, so none of this can be committed.
The owner's real install was never written to.

## Next actions (proposed, all need owner consent per ground rule 1)

1. Install git + gh (owner already approved) → fork, branch `game/rodina`, keep notes.
2. Copy the install to a **test folder** (never edit `F:\SteamLibrary\...\Rodina`).
3. Launch a copy with logs enabled, confirm the script/mod load path and `UserScript.lua`.
4. Read `playbook/how-coop-mods-work.md`, `networking-steam-spacewar.md`,
   `reverse-engineering.md`, then write a design doc: networking model, first slice,
   test plan (bots per `automated-qa.md`).
5. Open a "claim a game" issue on coop-anything so other agents can find this work.
