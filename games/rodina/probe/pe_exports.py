"""Read a PE export table directly, with no ctypes and no compiler.

Needed because Rodina is a 32-bit game and this machine only has 64-bit Python,
so ctypes cannot load steam_api.dll to introspect it.

Usage: py pe_exports.py <dll> [name-prefix ...]
Prints every exported symbol, and (if prefixes given) whether each is present.
"""

import struct
import sys


def read_sections(data: bytes):
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[pe_off : pe_off + 4] == b"PE\0\0", "not a PE file"
    n_sections = struct.unpack_from("<H", data, pe_off + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe_off + 20)[0]
    magic = struct.unpack_from("<H", data, pe_off + 24)[0]
    is_64 = magic == 0x20B
    opt_off = pe_off + 24
    # Data directories start at +112 for PE32+, +96 for PE32.
    dd_off = opt_off + (112 if is_64 else 96)
    sec_off = pe_off + 24 + opt_size
    sections = []
    for i in range(n_sections):
        base = sec_off + i * 40
        va, size = struct.unpack_from("<II", data, base + 12)
        raw_ptr, raw_size = struct.unpack_from("<II", data, base + 20)
        sections.append((va, size, raw_ptr, raw_size))
    export_rva, export_size = struct.unpack_from("<II", data, dd_off)
    return sections, export_rva, export_size


def rva_to_off(rva: int, sections) -> int:
    for va, size, raw_ptr, raw_size in sections:
        if va <= rva < va + max(size, raw_size):
            return raw_ptr + (rva - va)
    return rva  # header-relative fallback


def exported_names(data: bytes):
    sections, export_rva, _ = read_sections(data)
    if export_rva == 0:
        return []
    off = rva_to_off(export_rva, sections)
    n_names = struct.unpack_from("<I", data, off + 24)[0]
    names_rva = struct.unpack_from("<I", data, off + 32)[0]
    names_off = rva_to_off(names_rva, sections)
    out = []
    for i in range(n_names):
        name_rva = struct.unpack_from("<I", data, names_off + i * 4)[0]
        p = rva_to_off(name_rva, sections)
        end = data.index(b"\0", p)
        out.append(data[p:end].decode("ascii", "replace"))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], "rb") as fh:
        data = fh.read()
    names = exported_names(data)
    prefixes = sys.argv[2:]
    print(f"file: {sys.argv[1]}")
    print(f"exports: {len(names)}")
    if prefixes:
        matches = sorted({n for n in names for p in prefixes if p in n})
        print(f"matching {prefixes}: {len(matches)}")
        for n in matches:
            print(f"  {n}")
    else:
        for n in sorted(names):
            print(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
