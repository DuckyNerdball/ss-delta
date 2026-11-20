# Writes the table of the game's button-icon atlases that ss-delta.exe's Xbox button labels redraw
# ([game] button_labels; the fork's games/ss-delta/button_atlases.inc). For every language copy of the
# com_001_* atlases in the archives it finds the PlayStation symbols (the US copy's boxes, moved where
# a copy's layout moved them) and prints one entry: the FNV-1a hash of the texture data as the game
# holds it, its size, and the symbol boxes. Only hashes and coordinates go out, nothing of the art.
# Needs numpy (decoding the atlases).
#   python -I tools/button-atlases.py <...>/retail <out.inc>
# <...>/retail holds archive.* and archive_patch3.* (docs/01-research.md, "Button prompts").
import os
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lspk  # noqa: E402

# The symbols' boxes (x, y, w, h) in the US copies, from their white strokes.
SQUARE, CIRCLE, CROSS, TRIANGLE, L, R = 'Square', 'Circle', 'Cross', 'Triangle', 'L', 'R'
FACE_ROW = [(SQUARE, 11, 10, 9, 9), (CIRCLE, 43, 9, 11, 11), (CROSS, 75, 9, 10, 10), (TRIANGLE, 106, 9, 12, 10)]
FAMILIES = {
    # □ ○ × △, L, R, and big L HOLD / R HOLD
    'com_001_000': [(SQUARE, 11, 11, 9, 9), (CIRCLE, 43, 10, 11, 11), (CROSS, 75, 10, 10, 10),
                    (TRIANGLE, 106, 10, 12, 10), (L, 28, 40, 8, 12), (R, 92, 41, 9, 12),
                    (L, 28, 85, 11, 16), (R, 91, 86, 12, 15)],
    # the same with HOLD under each, sticks, START (and SELECT, TOUCH in 005)
    'com_001_002': FACE_ROW + [(L, 28, 39, 8, 12), (R, 92, 40, 9, 12)],
    'com_001_005': FACE_ROW + [(L, 28, 39, 8, 12), (R, 92, 40, 9, 12)],
    # D-pad with HOLD; □ ○ △ with RELEASE
    'com_001_003': [(SQUARE, 29, 75, 9, 9), (CIRCLE, 91, 74, 11, 10), (TRIANGLE, 91, 106, 11, 10)],
    # big L HOLD / R HOLD
    'com_001_008': [(L, 58, 17, 20, 21), (R, 57, 82, 24, 21)],
}
REFERENCE = {f: f + ('_us' if f != 'com_001_002' else '') for f in FAMILIES}
MARGIN = 2      # compared around each box
SEARCH = 16     # how far a copy's symbol may have moved
TOLERANCE = 14  # mean difference (0-255) still taken as the same symbol


def fnv1a64(data):
    h = 0xcbf29ce484222325
    for b in data:
        h = ((h ^ b) * 0x100000001b3) & 0xffffffffffffffff
    return h


def morton_split(n):
    i = np.arange(n, dtype=np.uint32)
    even = np.zeros(n, np.uint32)
    odd = np.zeros(n, np.uint32)
    for b in range(16):
        even |= ((i >> (2 * b)) & 1) << b
        odd |= ((i >> (2 * b + 1)) & 1) << b
    return even, odd


def decode_bc3(data, w, h):
    """Swizzled BC3 -> (h, w, 4) uint8, as Vita3K's resolve_z_order_compressed_image + BC3 decoding."""
    bw, bh = w // 4, h // 4
    n = bw * bh
    raw = np.frombuffer(data[:n * 16], np.uint8).reshape(n, 16)
    k = min(bw, bh)
    sq, r = np.divmod(np.arange(n, dtype=np.uint32), k * k)
    even, odd = morton_split(k * k)
    bx, by = odd[r].astype(np.int64), even[r].astype(np.int64)
    if bw >= bh:
        bx += sq * k
    else:
        by += sq * k
    c0 = raw[:, 8].astype(np.int32) | raw[:, 9].astype(np.int32) << 8
    c1 = raw[:, 10].astype(np.int32) | raw[:, 11].astype(np.int32) << 8

    def rgb(c):
        return np.stack([(c >> 11 & 31) * 255 // 31, (c >> 5 & 63) * 255 // 63, (c & 31) * 255 // 31], -1)

    a, b = rgb(c0), rgb(c1)
    pal = np.stack([a, b, (2 * a + b) // 3, (a + 2 * b) // 3], 1)
    bits = raw[:, 12:16].copy().view('<u4')[:, 0]
    idx = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))[None, :]) & 3
    rows = np.arange(n)[:, None]
    px = np.empty((n, 16, 4), np.int32)
    px[:, :, :3] = pal[rows, idx]
    a0, a1 = raw[:, 0].astype(np.int32), raw[:, 1].astype(np.int32)
    s7, s5 = np.arange(1, 7), np.arange(1, 5)
    p8 = np.concatenate([a0[:, None], a1[:, None], ((7 - s7) * a0[:, None] + s7 * a1[:, None]) // 7], 1)
    p6 = np.concatenate([a0[:, None], a1[:, None], ((5 - s5) * a0[:, None] + s5 * a1[:, None]) // 5,
                         np.zeros((n, 1), np.int32), np.full((n, 1), 255)], 1)
    apal = np.where((a0 > a1)[:, None], p8, p6)
    abits = np.zeros(n, np.uint64)
    for j in range(6):
        abits |= raw[:, 2 + j].astype(np.uint64) << np.uint64(8 * j)
    aidx = (abits[:, None] >> (np.uint64(3) * np.arange(16, dtype=np.uint64))[None, :]) & np.uint64(7)
    px[:, :, 3] = apal[rows, aidx.astype(np.int64)]
    img = np.zeros((bh, 4, bw, 4, 4), np.int32)
    img[by, :, bx, :] = px.reshape(n, 4, 4, 4)
    return img.reshape(h, w, 4)


def premultiplied(img):
    return img[..., :3] * img[..., 3:4] / 255.0


def region(img, x, y, w, h):
    x0, y0 = x - MARGIN, y - MARGIN
    x1, y1 = x + w + MARGIN, y + h + MARGIN
    if x0 < 0 or y0 < 0 or x1 > img.shape[1] or y1 > img.shape[0]:
        return None
    return img[y0:y1, x0:x1]


def find(img, ref, box):
    """The box moved to where `img` has the reference's symbol, or None."""
    _, x, y, w, h = box
    want = region(ref, x, y, w, h)
    best = None
    for dy in range(-SEARCH, SEARCH + 1):
        for dx in range(-SEARCH, SEARCH + 1):
            got = region(img, x + dx, y + dy, w, h)
            if got is None:
                continue
            d = float(np.abs(got - want).mean())
            if best is None or d < best[0] or (d == best[0] and abs(dx) + abs(dy) < abs(best[1]) + abs(best[2])):
                best = (d, dx, dy)
    if best and best[0] <= TOLERANCE:
        return (box[0], x + best[1], y + best[2], w, h), best[0]
    return None, best[0] if best else None


def gxt_texture(data):
    """(width, height, format, first-mip bytes) of a one-texture GXT."""
    _, _, n = struct.unpack('<4sII', data[:12])
    if n != 1:
        return None
    off, size, _, _, ty, fmt, w, h = struct.unpack('<IIiIIIHH', data[32:60])
    if ty != 0 or fmt & 0x9f000000 != 0x87000000:
        return None
    return w, h, fmt, data[off:off + w * h]


def members(base):
    with open(base + '.pfs', 'rb') as f:
        files = lspk.read_tree(f.read())
    with open(base + '.pkh', 'rb') as f:
        index = lspk.read_index(f.read())
    out = {}
    with open(base + '.pk', 'rb') as pk:
        for p in files:
            name = p.rsplit('/', 1)[-1]
            if not (p.startswith('resource/data/texture/com_001_') and name.endswith('.gxt')):
                continue
            off, size, csize = index[lspk.path_hash(p)]
            pk.seek(off)
            data = pk.read(csize or size)
            out[name[:-4]] = zlib.decompress(data) if csize else data
    return out


def main():
    retail, out_path = sys.argv[1], sys.argv[2]
    archives = [('archive', members(os.path.join(retail, 'archive'))),
                ('archive_patch3', members(os.path.join(retail, 'archive_patch3')))]
    textures = {}
    for arc, files in archives:
        for name, data in files.items():
            t = gxt_texture(data)
            if t:
                textures[(arc, name)] = t
    refs = {}
    for fam, ref in REFERENCE.items():
        w, h, _, raw = textures[('archive', ref)]
        refs[fam] = premultiplied(decode_bc3(raw, w, h))
    entries, seen = [], {}
    for (arc, name), (w, h, fmt, raw) in sorted(textures.items()):
        fam = next((f for f in FAMILIES if name.startswith(f)), None)
        if not fam:
            continue
        img = premultiplied(decode_bc3(raw, w, h))
        slots, notes = [], []
        for box in FAMILIES[fam]:
            found, d = find(img, refs[fam], box)
            if found:
                slots.append(found)
            else:
                notes.append('%s %d,%d (best %.1f)' % (box[0], box[1], box[2], d if d is not None else -1))
        label = '%s/%s' % (arc, name)
        if notes:
            print('%s: not found: %s' % (label, ', '.join(notes)), file=sys.stderr)
        if not slots:
            continue
        h64 = fnv1a64(raw)
        # the language suffix ('-': none), and where archive_patch3 replaces the archive's copy
        copy = (name[len(fam):].lstrip('_') or '-') + (' (patch3)' if arc == 'archive_patch3' else '')
        if h64 in seen:
            seen[h64][3].append(copy)
            continue
        moved = [s for s, b in zip(slots, FAMILIES[fam]) if s[1:3] != b[1:3]]
        print('%-36s %d symbols%s' % (label, len(slots), ', %d moved' % len(moved) if moved else ''), file=sys.stderr)
        entries.append((h64, w, h, [fam, copy], slots))
        seen[h64] = entries[-1]
    lines = ['// Generated by ss-delta tools/button-atlases.py from the game\'s archives: the com_001_* button',
             '// atlases (FNV-1a 64 of the texture data, width, height) and the PlayStation symbols in them',
             '// (x, y, w, h in the atlas). Hashes and coordinates only.']
    for h64, w, h, names, slots in entries:
        name = names[0] + ' ' + '/'.join(names[1:])
        sl = ', '.join('{ Symbol::%s, %d, %d, %d, %d }' % s for s in slots)
        lines.append('{ 0x%016xull, %d, %d, "%s", { %s } },' % (h64, w, h, name, sl))
    with open(out_path, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('%d atlases -> %s' % (len(entries), out_path), file=sys.stderr)


if __name__ == '__main__':
    main()
