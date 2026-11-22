# Lists, extracts and repacks members of the game's LSPK archives (.pfs directory tree, .pkh hash
# table, .pk data; docs/01-research.md "Assets").
#   python -I tools/lspk.py list <archive base path without extension> [substring...]
#   python -I tools/lspk.py extract <archive base path> <outdir> <substring>...
#   python -I tools/lspk.py pack <archive base path> <out base path> <folder>
#       a copy of the archive (.pk, .pkh) with the files under <folder> added or replacing members of
#       the same path (relative to <folder>, e.g. resource/boot/costume_table.csv). The .pfs name
#       tree isn't rewritten: the game reads only .pkh and .pk.
# Later archives override earlier ones in the game (archive_patch3 over archive); pass the one you want.
import os
import struct
import sys
import zlib


def _crc_table():
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) & 0xffffffff if c & 0x80000000 else (c << 1) & 0xffffffff
        table.append(c)
    return table


_T = _crc_table()


def path_hash(path):
    """CRC-32/BZIP2 of the lower-cased path, the .pkh key."""
    c = 0xffffffff
    for b in path.lower().encode('latin1'):
        c = ((c << 8) & 0xffffffff) ^ _T[((c >> 24) ^ b) & 0xff]
    return c ^ 0xffffffff


def read_tree(pfs):
    """Member paths from a .pfs: u32 header (0, 0, dirs, files), 24-byte dir records
    (index, parent, first child, child count, first file, file count), then one u32 name
    offset per dir and per file into the name pool that follows. All big-endian."""
    _, _, nd, nf = struct.unpack('>4I', pfs[:16])
    dirs = [struct.unpack('>6I', pfs[16 + i * 24:40 + i * 24]) for i in range(nd)]
    table = 16 + nd * 24
    offs = struct.unpack('>%dI' % (nd + nf), pfs[table:table + 4 * (nd + nf)])
    pool = table + 4 * (nd + nf)

    def name(k):
        o = pool + offs[k]
        return pfs[o:pfs.index(b'\0', o)].decode('latin1')

    path = {}
    files = []
    for i, r in enumerate(dirs):
        parent = r[1]
        path[i] = '' if parent == 0xffffffff else (path[parent] + '/' if path[parent] else '') + name(i)
        for j in range(r[4], r[4] + r[5]):
            files.append((path[i] + '/' if path[i] else '') + name(nd + j))
    return files


def read_index(pkh):
    count = struct.unpack('>I', pkh[:4])[0]
    index = {}
    for i in range(count):
        h, off, size, csize = struct.unpack('>4I', pkh[4 + i * 16:20 + i * 16])
        index[h] = (off, size, csize)
    return index


def read_member(base, path, index=None):
    """A member's bytes, or None when the archive lacks it."""
    if index is None:
        with open(base + '.pkh', 'rb') as f:
            index = read_index(f.read())
    entry = index.get(path_hash(path))
    if entry is None:
        return None
    off, size, csize = entry
    with open(base + '.pk', 'rb') as pk:
        pk.seek(off)
        data = pk.read(csize or size)
    return zlib.decompress(data) if csize else data


def pack(base, out, members, remove=()):
    """Write out.pk/out.pkh: base's members, raw, then `members` ({archive path: bytes}) added or
    replacing by path hash, zlib-compressed; the paths in `remove` are left out. Data at 16-byte
    offsets, the index sorted by hash, as the game's own archives are."""
    with open(base + '.pkh', 'rb') as f:
        index = read_index(f.read())
    for p in remove:
        index.pop(path_hash(p), None)
    new = {path_hash(p): data for p, data in members.items()}
    entries = []
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(base + '.pk', 'rb') as src, open(out + '.pk', 'wb') as dst:
        def put(h, raw, size, csize):
            pad = -dst.tell() % 16
            dst.write(b'\0' * pad)
            entries.append((h, dst.tell(), size, csize))
            dst.write(raw)
        for h, (off, size, csize) in sorted(index.items(), key=lambda kv: kv[1][0]):
            if h in new:
                continue
            src.seek(off)
            put(h, src.read(csize or size), size, csize)
        for h, data in new.items():
            packed = zlib.compress(data, 9)
            put(h, packed, len(data), len(packed))
    entries.sort()
    with open(out + '.pkh', 'wb') as f:
        f.write(struct.pack('>I', len(entries)))
        for e in entries:
            f.write(struct.pack('>4I', *e))
    return len(entries), sum(1 for h in new if h in index)


def main():
    if len(sys.argv) >= 5 and sys.argv[1] == 'pack':
        folder = sys.argv[4]
        members = {}
        for root, _, names in os.walk(folder):
            for n in names:
                full = os.path.join(root, n)
                with open(full, 'rb') as f:
                    members[os.path.relpath(full, folder).replace(os.sep, '/')] = f.read()
        count, replaced = pack(sys.argv[2], sys.argv[3], members)
        print(f'{sys.argv[3]}.pk/.pkh: {count} members, {replaced} replaced, {len(members) - replaced} added')
        return
    if len(sys.argv) < 3 or sys.argv[1] not in ('list', 'extract'):
        sys.exit(__doc__ or 'usage: lspk.py list|extract|pack <archive> ...')
    cmd, base = sys.argv[1], sys.argv[2]
    with open(base + '.pfs', 'rb') as f:
        files = read_tree(f.read())
    with open(base + '.pkh', 'rb') as f:
        index = read_index(f.read())
    missing = [p for p in files if path_hash(p) not in index]
    if missing:
        print(f'{len(missing)} of {len(files)} names have no .pkh entry', file=sys.stderr)
    if cmd == 'list':
        want = [w.lower() for w in sys.argv[3:]]
        for p in files:
            if not want or any(w in p.lower() for w in want):
                print(p)
        return
    out, want = sys.argv[3], [w.lower() for w in sys.argv[4:]]
    if not want:
        sys.exit('extract needs at least one substring')
    with open(base + '.pk', 'rb') as pk:
        for p in files:
            if not any(w in p.lower() for w in want) or path_hash(p) not in index:
                continue
            off, size, csize = index[path_hash(p)]
            pk.seek(off)
            data = pk.read(csize or size)
            if csize:
                data = zlib.decompress(data)
            dst = os.path.join(out, *p.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as f:
                f.write(data)
            print(p, len(data))


if __name__ == '__main__':
    main()
