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

### P8. Stage-1 probe, second pass (2026-10-22): hook, UserScript, player state, puppet

All observed in `local\rodina-test\` with the P4 launch recipe; each run is one
`Rodina_Steam.exe` start. **Runs are closed gracefully** (`CloseMainWindow`, i.e. WM_CLOSE,
then wait for exit) before the log is read — see item 9. The game reports exit code 1 even
on a clean close. Earlier probe runs in this pass were force-killed; that turned out to
invalidate several intermediate conclusions, corrected below.

1. **`Scripts\UserScript.lua` does not run** in 1.6.5 Steam. Two attempts: the file set a
   global and called `System.Log`. No log line at startup, and at `Start Game` the mod's
   probe read the global as `nil`. The exe still contains `\UserScript.lua` (appended to
   the scripts dir), so the string is there but the hook is not active in this build.
   **Derived: do not use UserScript; mods are the hook.** (Q2 closed as "unavailable",
   not "unknown".)
2. **A mod can wrap the per-frame update.** Overriding `GameplayMain.lua` (full-file
   mirror, appended `MainUpdate` wrapper that calls the original) logs
   `Loading Mod Script: mods\coopprobe\Scripts\Gameplay\GameplayMain.lua`, and the
   wrapper ran every frame until the process was killed. (Q7 partly answered: the frame
   hook exists and costs one Lua call per frame.)
3. **Player state is readable.** Inside `MainUpdate`, `gGame:GetPlayer().Position`
   returns an `EGVector`; logged `-470.79, 2159.24, -12005.78`. The value is byte-identical
   across launches (deterministic start position — useful for test oracles).
4. **Q4 answered: yes.** `EGPlayer:New()` + `player.Engine:AddEntitySibling(puppet)` +
   `puppet.Position = player.Position:Plus( EGVector( 2, 0, 0 ) )` every frame. Result:
   puppet survived 2,400+ frames (~40 s) of live world, no crash, and read back exactly
   the written position (`puppet = player + (2,0,0)`) at every 120-frame sample. Writing
   `Position` each frame wins over the puppet's physics for as long as it is re-set.
   **Follows a moving player: verified.** Teleporting the player +10 on X from Lua read
   back at the new X, and the puppet read `player + 2` 40 frames later. **Rotation: open.**
   `puppet.Engine:SetRotationVelocity( EGVector( 0, 1, 0 ) )` produced no measurable
   change in `Engine:GetYawPitchRollToLevel()` (~1e-9 before and after, 150 frames), so a
   direct orientation setter (or a per-frame rotation write) still has to be found.
5. **Menu bypass = bot start hook.** `EGMenuMain` is opened from
   `GameplayMain.lua:27-30` (`loadingMenu.OnLoadComplete`). Rewriting that callback in
   the mod to `MenuSystem:Open( EGMenuHUD )` (plus the `SetStage(math.huge)` branch from
   `EGMenuMain:Start()`) starts play with **no input injection**; the world then stays
   live and `MainUpdate` keeps running. This is how the automated test starts a game.
   What did *not* work: appending a wrapper to `EGMenuMain:Update` in a mod — the
   already-created menu instance never called it (no log line). Mechanism unknown
   (derived guess: instance method binding happens before mod load, or the engine calls
   the base `EGMenu` path). **Derived: override the creator, not the live menu class.**
6. **The game rewrites `Mods\LoadOrder.lua` itself** (via `EGSaveLuaDataFile`) into
   `ModList = { [1] = "coopempty", [2] = "coopprobe" }` — bare names, no `Mods\` prefix —
   and that form still loads both mods. Both forms work.
7. **Q5 answered: actors are enumerable and carry stable ids at spawn.**
   `System.GetCurrentScene():GetActors()` returns a plain array (17 entries at spawn,
   18 once the probe's puppet exists). Each entry exposes `a.Engine:GetID()` (integer),
   `a.ClassName`, `a.Health` / `a.MaxHealth`, `a:IsDead()` and `a.Position`. Full list
   from one graceful-close run:

   | # | id | class | health |
   |---|---|---|---|
   | 1 | 2172 | `EGShipPlayer` | 100 |
   | 2 | 2175 | `EGPlayer` | 100 |
   | 3–17 | 2177, 2181, 2184, 2186, 2189, 2192, 2195, 2197, 2200, 2203, 2206, 2209, 2212, 2214, 2217 | `EGShipVanguardChunk` | `1.#INF` |
   | 18 | 2239 | `EGPlayer` (probe puppet) | 100 |

   This is the mirroring substrate: id + class + transform + health per shared actor.
   Caveats: the `EGShipVanguardChunk` entries report `Health = MaxHealth = 1.#INF` and
   garbage positions (values around 1e9, likely unplaced or local-space chunks) — do not
   mirror their transforms blindly. The puppet's own id is **not stable across runs**
   (2232 in one run, 2239 in another) while the 17 scene actors kept their ids, so entity
   ids must be assigned by the host, never assumed to match across machines.
8. **Q6 answered: health is writable as state and does not re-run Lua death effects.**
   Direct `puppet.Health = 50` read back 50; `puppet:DamageHealth(10, nil, nil, nil, true)`
   then read 40; `puppet.Health = 0` made `IsDead()` true. The puppet stayed in the world
   and in `GetActors()` 1,000+ frames later. `EGCharacterActor:Update` returns early when
   `Health <= 0` (zeroes movement), but the loot/death path
   `EGCharacterActor:UpdateDead` has **no Lua caller anywhere in the shipped scripts**
   (grep: definition only). Derived: mirroring a death by writing `Health`/`IsDead` does
   not re-run loot or particles on the client. Whether the native engine invokes
   `UpdateDead` for non-player actors is **unknown** and must be tested on a real Xeno,
   not on the puppet. If it does, the client mirror must clear `LootType` (or subclass
   with `UpdateDead` stubbed) so loot is not spawned twice — the Gothic 3 lesson.
9. **Harness facts (re-verified 2026-10-22).**
   - **Never force-kill when the log is the evidence.** `Stop-Process` loses the unflushed
     log tail; the file then ends mid-line and looks like a hang. With
     `CloseMainWindow()` (WM_CLOSE) + wait for exit, the tail is present: one run that
     looked "frozen at 12.5 s" actually logged a completed download at 12.597 s, HUD at
     17.2 s, the enumeration at 23.6 s and checkpoints through f1800 at 35.3 s.
   - Corollary: the earlier interim claims of a "download stall at 12.5 s", a "log-burst
     deadlock" and a hard "~214-char line cap" were **artifacts of force-kill**, not game
     behaviour. Whether one very long log line is safe is `unknown`; keep diagnostic
     lines short (≲200 chars) as a precaution.
   - The process stays `Responding=True` with steady CPU through those apparent freezes —
     a second way to distinguish "not flushed" from "hung".
   - **Focus loss pauses the game.** Losing the foreground opens `EGMenuPause` and stops
     `MainUpdate` (observed at the moment the HUD opened). For unattended runs force the
     foreground after launch: `AttachThreadInput(ourThread, foregroundThread, true)` →
     `ShowWindow(SW_RESTORE)` → `BringWindowToTop` → `SetForegroundWindow` → detach.
     Verified `fg=[Rodina]` and no pause for the rest of the run. Plain
     `SetForegroundWindow` from the background agent process is refused by Windows.
   - `GameplayMain.lua:34-35` starts real HTTP downloads at `Start Game`
     (`Update/CurrentCredits.txt` on S3). Once connected they finish in well under a
     second (DNS → connect → request → complete all at 12.597 s), so a co-op test need
     not stub them; disabling them changes later timing and is not recommended for
     parity with a normal launch.
   - One short `System.Log` line per frame ran for hundreds of frames without issue;
     sparse logging (every 20–120 frames) remains the safest for long runs.

10. **Render: a bare `EGPlayer` puppet is invisible; native character classes render**
    (2026-10-22, **owner-confirmed**). The item-4 puppet stayed in `GetActors()`, followed
    the player for the whole run and was driven for 2,400+ frames, but the owner could not
    see it in any of six live screenshots taken while orbiting the spawn point
    (`local\rodina-test\shots\shot_08..12`). A follow-up run then spawned
    `EGRobotCharacter` and `EGXenoCharacter` with the game's own recipes
    (`Scripts\Gameplay\EGGame.lua:686-734`); the owner confirmed **both** are visible
    (`local\rodina-test\shots\npc_6.png`, `npc_8.png`). The same recipe was re-run verbatim
    later and the owner again confirmed both (`shots\npc2_montage.png`).
    **Observation** (owner's eyes in the running game), not a pixel measurement.
    **Derived:** `EGPlayer:New()` makes a logical actor with no body; visibility comes from
    the native class's engine-side mesh, which Lua never touches. The remote avatar must be
    an engine-recognised character class (or a clone of one), not a bare `EGPlayer`.
    **Unknown:** whether a native NPC can be given the player's appearance (mesh
    swap/attach); whether its animation state can be driven from Lua.

11. **Stage-1 positive: a native avatar can be spawned, driven and rotated, and it renders**
    (2026-10-22, **owner-confirmed**: "visible and rotating",
    `local\rodina-test\shots\avatar10_montage.png`). This is the recipe that works:

    ```lua
    EGMakeClass( "EGXenoAvatar", "EGXenoCharacter" )
    function EGXenoAvatar:Update( aDeltaTime, aFullUpdate ) end   -- kills AI + physics forcing
    function EGXenoAvatar:UpdateDead( aDeltaTime ) end

    local avatar = EGXenoAvatar:New()
    avatar.Position = <spawn position>
    player.Engine:AddEntitySibling( avatar )
    avatar.Engine:SetPhysicsType( EGActor.PHYSICS_DISABLED )
    avatar.Health = 1000            -- after AddEntitySibling, not before

    -- every frame:
    avatar.Position = player.Position:Plus( EGVector( 0, 0, 5 ) )
    avatar.Engine:EditorSetRotation( EGVector( yaw, 0, 0 ) )
    ```

    The owner saw the avatar facing four different directions as the logged heading
    changed 0/90/180/270°. **Observation**, owner's eyes.

    **Derived:**
    - `.Orientation` is inert. Writing it changes the field (readback follows) but does
      **not** change the entity transform. `Engine:EditorSetRotation( yaw, pitch, roll )`
      is the working absolute rotation setter; it updates the transform with ~1 frame of
      sync lag.
    - Do **not** use `EGCharacterActor:Update` on a puppet: it forces `PHYSICS_DRIVEN`
      every frame, and the actor's physics then overrides the heading we set (the base
      xeno froze at one heading after ~5 s). Stub `Update` in a subclass instead.
    - A **xeno** subclass renders. A **robot** subclass did not (`avatar5`), although the
      base robot renders (`npc2`, `bisect`); robot subclassing appears to break its body
      construction. Use the xeno as the avatar carrier.
    - `Health = 1000`, the AI stub and `ScreenshotMode` do not hide a base xeno by
      themselves (`shots\bisect_montage.png`, owner: both visible in all five panels).
    - Changes applied **before** `AddEntitySibling` are associated with the earlier
      "none visible" runs (`avatar6`); the working recipe adds the entity first, then
      modifies it. Cause not isolated.

    **Unknown / next:**
    - Why the base xeno at +5X with pre-add changes was invisible while the base robot at
      +5X and the subclass xeno at +5Z were visible. The contradiction is not fully
      explained; the working recipe avoids it.
    - The avatar is a **xeno placeholder**, not the player's appearance. The player is
      first-person (has a "Player Camera" child, no third-person body observed); whether a
      suit/human mesh can be substituted is open.
    - `+5Z` is a proof-of-render offset, not a gameplay spawn. A camera-relative offset
      (in front of the remote player) still needs to be derived.
    - No movement animation is driven; only the root position/rotation.

12. **Camera/world geometry, and a negative ground-level placement test** (2026-10-22, numeric
    + owner-confirmed negative).
    **Observations:**
    - `player.Position` and `player.Engine:EditorGetPosition()` are the same value and are
      **world/planet space** (`-470.79, 2159.24, -12005.79`); the player's parent is
      `EGStartingPlanet` ("AsteroidLarge-50").
    - `EditorGetPosition()` on a **child** entity is **parent-local**: the player's camera
      reads `0,0,1.649`, i.e. eye height above the player.
    - Camera-local **+Y is forward**. `GetScreenPosForLocalDir(+Y)` maps to the screen
      centre `(0,0,0.495)`; `+X/-X/+Z/-Z` map to infinities (perpendicular to the view
      axis). The HUD reticle code also treats `dir.y > 0` as "in front"
      (`EGMenuHUD.lua:456`).
    - Camera-local **+Z points down** (world direction ≈ `-Z`): the camera basis is rolled
      180° relative to the actor convention where +Z is up.
    - `EGVector(x,y)` is **not a valid constructor** (needs 1 or 3 components); this is why
      the first `GetLocalDirForScreenPos` call failed.
    - `GetScreenBox(entity)` exposed no `x/y/w/h` fields through Lua (`?` for every field)
      and is not a usable visibility oracle.
    - `cam:GetLocalVectorTo(entity)` + `GetScreenPosForLocalDir` did not track a 4-unit
      offset either (stuck at `-0.26,-1.27,0.49` across six avatar positions), so there is
      **no working numeric visibility oracle yet**.
    - **Negative placement result:** a visible xeno avatar placed 4 units along the
      horizontal camera forward at the player's Z (`player.Position + fwd*4`) was **not
      visible** (owner, `shots/front_montage.png`), even though the numeric placement and
      facing were exact. The view direction also starts changing on its own after ~7 s
      (no input), so the player is not perfectly static.

    **Derived / guess:** the ground-level point 4 m ahead is most likely inside a slope or
    hill at the spawn (`+5Z` clears the terrain, which is why the proof avatar showed).
    **Derived:** camera-relative placement is only a convenience for single-client probes;
    in the real mod the avatar is placed at the **remote player's transmitted position**,
    which is already on walkable ground. Do not build terrain-aware spawning for the probe.
    **Unknown:** whether the negative was occlusion, framing, or something else; why the
    view direction drifts without input.

Unknowns left by this pass:

- ~~Does the puppet render?~~ **Answered: no for a bare `EGPlayer`, yes for a native
  class. A subclassed xeno is visible, drivable and rotatable** — see items 10 and 11.
- Puppet side effects: `EGPlayer:Update` runs `UpdateDepthofFieldBlur`, which calls
  `System.SetTimeScale` and scene blur. Not measured; a real puppet should subclass
  `EGPlayer` with `Update`/`UpdateDepthofFieldBlur` stubbed.
- Does the native engine react to `Health <= 0` on a non-player actor (death animation,
  despawn, or a native call to `UpdateDead`)? The `EGPlayer` puppet did not despawn; no
  Xeno was present in the starting scene to test.
- What are the 15 `EGShipVanguardChunk` actors, and why do their positions read as
  garbage? Possibly unplaced chunks; not mirrored yet.
- Q8 (live debug console) not probed; `System.Log` + log file is the working channel.

Probe state in `local\rodina-test\`: `steam_appid.txt`; `Mods\LoadOrder.lua` (rewritten
by the game, two entries); `Mods\CoopEmpty\` (control);
`Mods\CoopProbe\Scripts\Gameplay\GameplayMain.lua` (menu bypass + puppet drive + full
actor-id enumeration, last run); `Scripts\UserScript.lua` (inert test file); screenshots
in `shots\` (puppet orbit run, native-NPC run). Probe snippets kept beside the install as
`_probe_*.lua`, logs as `RodinaLog*.txt`. All gitignored.

## Next actions (proposed, all need owner consent per ground rule 1)

1. Install git + gh (owner already approved) → fork, branch `game/rodina`, keep notes.
2. Copy the install to a **test folder** (never edit `F:\SteamLibrary\...\Rodina`).
3. Launch a copy with logs enabled, confirm the script/mod load path and `UserScript.lua`.
4. Read `playbook/how-coop-mods-work.md`, `networking-steam-spacewar.md`,
   `reverse-engineering.md`, then write a design doc: networking model, first slice,
   test plan (bots per `automated-qa.md`).
5. Open a "claim a game" issue on coop-anything so other agents can find this work.
