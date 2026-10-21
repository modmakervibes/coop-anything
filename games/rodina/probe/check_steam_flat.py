"""Check whether a steam_api DLL exports the flat C API the Spacewar relay needs.

Read-only. Uses ctypes so no compiler or SDK is required.
Usage: py check_steam_flat.py <path to steam_api.dll>
"""

import ctypes
import sys

# Flat API functions the relay design depends on (networking-steam-spacewar.md).
REQUIRED = [
    "SteamAPI_IsSteamRunning",
    "SteamAPI_InitFlat",
    "SteamAPI_GetHSteamPipe",
    "SteamAPI_ManualDispatch_Init",
    "SteamAPI_ManualDispatch_RunFrame",
    "SteamAPI_ManualDispatch_GetNextCallback",
    "SteamAPI_ManualDispatch_FreeLastCallback",
    "SteamAPI_ManualDispatch_GetAPICallResult",
    "SteamAPI_SteamUser_v023",
    "SteamAPI_SteamMatchmaking_v009",
    "SteamAPI_SteamFriends_v018",
    "SteamAPI_SteamNetworkingMessages_SteamAPI_v002",
    "SteamAPI_SteamNetworkingUtils_SteamAPI_v004",
    "SteamAPI_ISteamMatchmaking_CreateLobby",
    "SteamAPI_ISteamMatchmaking_JoinLobby",
    "SteamAPI_ISteamFriends_ActivateGameOverlayInviteDialog",
    "SteamAPI_ISteamNetworkingMessages_SendMessageToUser",
    "SteamAPI_ISteamNetworkingMessages_ReceiveMessagesOnChannel",
    "SteamAPI_ISteamNetworkingMessages_AcceptSessionWithUser",
    "SteamAPI_SteamNetworkingMessage_t_Release",
]

# Nice to know but not fatal.
OPTIONAL = [
    "SteamAPI_SteamNetworkingIdentity_SetSteamID64",
    "SteamAPI_ISteamFriends_SetRichPresence",
    "SteamAPI_ISteamFriends_GetFriendGamePlayed",
    "SteamAPI_ISteamNetworkingUtils_SetGlobalConfigValueInt32",
]


def pe_machine(path: str) -> int:
    """Return the PE COFF machine type (0x14c = x86, 0x8664 = x64)."""
    import struct

    with open(path, "rb") as fh:
        data = fh.read(0x400)
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off : pe_off + 4] != b"PE\0\0":
        raise ValueError("not a PE file")
    return struct.unpack_from("<H", data, pe_off + 4)[0]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]

    # A 64-bit Python cannot load a 32-bit DLL ("not a valid Win32 application").
    # Read the header first so the failure is explained instead of confusing.
    machine = pe_machine(path)
    if machine == 0x014C and ctypes.sizeof(ctypes.c_void_p) == 8:
        print(f"file: {path}")
        print("arch: x86 (32-bit) DLL")
        print("python: 64-bit -> cannot load this DLL with ctypes.")
        print("Run this check with 32-bit Python, or inspect exports with a PE tool.")
        print("NOTE: arch itself is fine; the relay DLL must be built as 32-bit too.")
        return 3

    dll = ctypes.WinDLL(path)

    def has(name: str) -> bool:
        try:
            getattr(dll, name)
            return True
        except AttributeError:
            return False

    missing_required = [n for n in REQUIRED if not has(n)]
    missing_optional = [n for n in OPTIONAL if not has(n)]

    print(f"file: {path}")
    print(f"required exported: {len(REQUIRED) - len(missing_required)}/{len(REQUIRED)}")
    print(f"optional exported: {len(OPTIONAL) - len(missing_optional)}/{len(OPTIONAL)}")
    if missing_required:
        print("\nMISSING REQUIRED (flat API unavailable -> use pinned Steamworks.NET DLL):")
        for n in missing_required:
            print(f"  - {n}")
    else:
        print("\nOK: flat API exports present.")
    if missing_optional:
        print("\nmissing optional (informational):")
        for n in missing_optional:
            print(f"  - {n}")
    return 0 if not missing_required else 1


if __name__ == "__main__":
    raise SystemExit(main())
