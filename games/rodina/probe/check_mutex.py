"""Static check for a single-instance mutex / named kernel object.

Read-only: reads the exe bytes, never runs it. If a well-known single-instance
mutex name is present, two copies of the game may refuse to run at once, which
matters for running two co-op clients on one PC.

Usage: py check_mutex.py <exe>
"""

import re
import sys

# Strings games commonly use to enforce a single instance.
PATTERNS = [
    re.compile(rb"Global\\\\[A-Za-z0-9_\-\.{}\[\]]{3,80}"),
    re.compile(rb"Local\\\\[A-Za-z0-9_\-\.{}\[\]]{3,80}"),
    re.compile(rb"[A-Za-z0-9_\-\.]{0,40}[Mm]utex[A-Za-z0-9_\-\.]{0,40}"),
    re.compile(rb"[A-Za-z0-9_\-\.]{0,30}[Ss]ingle[Ii]nstance[A-Za-z0-9_\-\.]{0,30}"),
    re.compile(rb"[A-Za-z0-9_\-\.]{0,30}Already[Rr]unning[A-Za-z0-9_\-\.]{0,30}"),
]

# Kernel APIs relevant to a mutex, as import-name strings.
APIS = [
    b"CreateMutexA",
    b"CreateMutexW",
    b"CreateMutexExA",
    b"CreateMutexExW",
    b"OpenMutexA",
    b"OpenMutexW",
    b"CreateEventA",
    b"CreateEventW",
    b"GetLastError",
]

INTERESTING_SUFFIX = re.compile(rb"\.exe|Rodina|RODINA|Elliptic", re.IGNORECASE)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "rb") as fh:
        data = fh.read()

    print(f"file: {sys.argv[1]}")
    print(f"size: {len(data)}")

    print("\n-- mutex-related API imports --")
    for api in APIS:
        print(f"  {api.decode():20} {'present' if api in data else '-'}")

    print("\n-- candidate names --")
    found = set()
    for pat in PATTERNS:
        for m in pat.finditer(data):
            s = m.group(0)
            if 3 <= len(s) <= 90:
                found.add(s)
    names = sorted(x.decode("ascii", "replace") for x in found)
    # Drop obvious substrings of longer matches to reduce noise.
    deduped = [n for n in names if not any(n != o and n in o for o in names)]
    for n in deduped:
        flag = "  <-- looks like an app name" if INTERESTING_SUFFIX.search(n.encode()) else ""
        print(f"  {n}{flag}")
    print(f"\ntotal candidates: {len(deduped)}")
    print(
        "\nNote: a name here is a lead, not proof. Confirm by running two copies\n"
        "and reading RodinaLog.txt, or by checking whether the second exits."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
