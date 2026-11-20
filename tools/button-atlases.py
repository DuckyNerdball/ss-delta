# Writes the table of the game's textures with PlayStation buttons in them that ss-delta.exe's Xbox
# button labels redraw ([game] button_labels; the fork's games/ss-delta/button_atlases.inc): the
# com_001_* icon atlases, the tutorial pictures with buttons drawn in, and the font page that holds
# the text's ○ △ □. For every language copy in the archives it finds the symbols (the reference
# copy's boxes, moved where a copy's layout moved them; the font's from its glyph table) and prints
# one entry: the FNV-1a hash of the texture data as the game holds it, its format and size, and the
# symbol boxes. Only hashes and coordinates go out, nothing of the art. Needs numpy.
#   python -I tools/button-atlases.py <...>/retail <out.inc>
# <...>/retail holds archive.* and archive_patch3.* (docs/01-research.md, "Button prompts").
import math
import os
import re
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lspk  # noqa: E402

SQUARE, CIRCLE, CROSS, TRIANGLE, L, R, START, SELECT = 'Square', 'Circle', 'Cross', 'Triangle', 'L', 'R', 'Start', 'Select'
UBC1, UBC3, U8 = 0x85000000, 0x87000000, 0x00000000
TEXTURE = 'resource/data/texture/'

# The symbols' boxes (x, y, w, h) in each family's reference copy (REFERENCE), from their light
# strokes. Families are the texture's name without its language suffix.
FACE_ROW = [(SQUARE, 11, 10, 9, 9), (CIRCLE, 43, 9, 11, 11), (CROSS, 75, 9, 10, 10), (TRIANGLE, 106, 9, 12, 10)]
OFFERINGS = [(CIRCLE, 152, 46, 19, 20), (TRIANGLE, 102, 108, 22, 18), (SQUARE, 55, 170, 17, 17), (R, 212, 210, 16, 22)]
FAMILIES = {
    # icon atlases. 000: □ ○ × △, L, R, and big L HOLD / R HOLD
    'com_001_000': [(SQUARE, 11, 11, 9, 9), (CIRCLE, 43, 10, 11, 11), (CROSS, 75, 10, 10, 10),
                    (TRIANGLE, 106, 10, 12, 10), (L, 28, 40, 8, 12), (R, 92, 41, 9, 12),
                    (L, 28, 85, 11, 16), (R, 91, 86, 12, 15)],
    # the same with HOLD under each, the sticks, START (and SELECT, TOUCH in 005)
    'com_001_002': FACE_ROW + [(L, 28, 39, 8, 12), (R, 92, 40, 9, 12), (START, 81, 75, 29, 9)],
    'com_001_005': FACE_ROW + [(L, 28, 39, 8, 12), (R, 92, 40, 9, 12), (START, 81, 75, 29, 9), (SELECT, 79, 106, 35, 9)],
    # D-pad with HOLD; □ ○ △ with RELEASE
    'com_001_003': [(SQUARE, 29, 75, 9, 9), (CIRCLE, 91, 74, 11, 10), (TRIANGLE, 91, 106, 11, 10)],
    # big L HOLD / R HOLD
    'com_001_008': [(L, 58, 17, 20, 21), (R, 57, 82, 24, 21)],
    # tutorial pictures: Offerings on ○ △ □ (HOLD) and R over a scene, drawn narrower in 000c
    'game_027_000c': [(CIRCLE, 458, 329, 10, 17), (TRIANGLE, 433, 384, 11, 16), (SQUARE, 409, 438, 8, 15)],
    'game_027_002c': OFFERINGS,
    'game_027_003c': [(CIRCLE, 151, 46, 20, 20), (TRIANGLE, 102, 108, 22, 18), (R, 212, 209, 16, 22)],
    'game_027_004c': [(CIRCLE, 159, 35, 20, 20), (TRIANGLE, 108, 98, 22, 19), (SQUARE, 60, 162, 17, 17), (R, 210, 208, 17, 23)],
    'game_027_005c': [(CIRCLE, 159, 34, 20, 21), (TRIANGLE, 108, 96, 22, 19), (SQUARE, 60, 163, 17, 18), (R, 210, 207, 17, 23)],
    # the Frozen Shell on □ and R; Lay the Soul to Rest □ / Sacrifice ○ on the hands
    'menu_eu_tutorial_002': [(SQUARE, 200, 158, 11, 12), (R, 227, 223, 11, 16)],
    'menu_eu_tutorial_003': [(SQUARE, 472, 199, 8, 7), (R, 491, 237, 8, 9)],
    'menu_eu_tutorial_005': [(SQUARE, 111, 170, 26, 23), (CIRCLE, 369, 172, 29, 25)],
    'menu_eu_tutorial_006': [(SQUARE, 55, 85, 13, 11), (CIRCLE, 183, 87, 15, 13)],
}
REFERENCE = {f: f + '_us' for f in FAMILIES}
REFERENCE.update({f: f for f in ('com_001_002', 'game_027_003c', 'game_027_004c', 'game_027_005c')})
# the font page whose ○ △ □ the text uses (font 1, the game's default, takes symbols from it first)
FONT = 'resource/font/elder_number_font'
FONT_SYMBOLS = {0x25A1: SQUARE, 0x25B3: TRIANGLE, 0x25CB: CIRCLE}
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


def unswizzle(bw, bh):
    """Element (block or pixel) index -> (x, y), as Vita3K's swizzled_texture_to_linear_texture."""
    n = bw * bh
    k = min(bw, bh)
    sq, r = np.divmod(np.arange(n, dtype=np.uint32), k * k)
    even, odd = morton_split(k * k)
    x, y = odd[r].astype(np.int64), even[r].astype(np.int64)
    if bw >= bh:
        x += sq * k
    else:
        y += sq * k
    return x, y


def bc1_colours(raw, four):
    c0 = raw[:, 0].astype(np.int32) | raw[:, 1].astype(np.int32) << 8
    c1 = raw[:, 2].astype(np.int32) | raw[:, 3].astype(np.int32) << 8

    def rgb(c):
        return np.stack([(c >> 11 & 31) * 255 // 31, (c >> 5 & 63) * 255 // 63, (c & 31) * 255 // 31], -1)

    a, b = rgb(c0), rgb(c1)
    four = four | (c0 > c1)
    p2 = np.where(four[:, None], (2 * a + b) // 3, (a + b) // 2)
    p3 = np.where(four[:, None], (a + 2 * b) // 3, 0)
    pal = np.stack([a, b, p2, p3], 1)
    alpha = np.where(four[:, None], 255, np.array([255, 255, 255, 0])[None, :])
    bits = raw[:, 4:8].copy().view('<u4')[:, 0]
    idx = (bits[:, None] >> (2 * np.arange(16, dtype=np.uint32))[None, :]) & 3
    rows = np.arange(len(raw))[:, None]
    px = np.empty((len(raw), 16, 4), np.int32)
    px[:, :, :3] = pal[rows, idx]
    px[:, :, 3] = alpha[rows, idx]
    return px


def bc3_alpha(raw):
    n = len(raw)
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
    return apal[np.arange(n)[:, None], aidx.astype(np.int64)]


def decode(data, fmt, w, h):
    """Swizzled UBC1 / UBC3 / U8 -> (h, w, 4) int32 RGBA (U8: white with the value as alpha)."""
    if fmt == U8:
        x, y = unswizzle(w, h)
        img = np.zeros((h, w, 4), np.int32)
        img[..., :3] = 255
        img[y, x, 3] = np.frombuffer(data[:w * h], np.uint8)
        return img
    bw, bh = w // 4, h // 4
    n = bw * bh
    bs = 8 if fmt == UBC1 else 16
    raw = np.frombuffer(data[:n * bs], np.uint8).reshape(n, bs)
    if fmt == UBC1:
        px = bc1_colours(raw, np.zeros(n, bool))
    else:
        px = bc1_colours(raw[:, 8:], np.ones(n, bool))
        px[:, :, 3] = bc3_alpha(raw[:, :8])
    bx, by = unswizzle(bw, bh)
    img = np.zeros((bh, 4, bw, 4, 4), np.int32)
    img[by, :, bx, :] = px.reshape(n, 4, 4, 4)
    return img.reshape(h, w, 4)


def level_size(fmt, w, h):
    return w * h // 2 if fmt == UBC1 else w * h


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
    if img.shape == ref.shape:
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


def components(mask):
    """Bounding boxes (x, y, w, h, pixels) of the 8-connected components of a boolean mask."""
    hgt, wid = mask.shape
    seen = np.zeros(mask.shape, bool)
    out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack, xs, ys = [(y0, x0)], [], []
        while stack:
            y, x = stack.pop()
            xs.append(x)
            ys.append(y)
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    if 0 <= ny < hgt and 0 <= nx < wid and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        out.append((min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, len(xs)))
    return out


def snap(rgba, box):
    """Where pixel matching fails (a copy compressed or drawn a little differently): the light stroke
    component near the box whose size is close to the box's, or None."""
    sym, x, y, w, h = box
    x0, y0 = max(x - SEARCH, 0), max(y - SEARCH, 0)
    x1, y1 = min(x + w + SEARCH, rgba.shape[1]), min(y + h + SEARCH, rgba.shape[0])
    win = rgba[y0:y1, x0:x1]
    lum = win[..., :3].mean(-1)
    dark = lum[(lum < 70) & (win[..., 3] > 200)]
    if not dark.size:
        return None
    best = None
    for bx, by, bw, bh, n in components((lum > dark.mean() + 60) & (win[..., 3] > 200)):
        if not (0.75 * w <= bw <= 1.3 * w + 1 and 0.75 * h <= bh <= 1.3 * h + 1) or n < 6:
            continue
        d = abs(x0 + bx + bw / 2 - (x + w / 2)) + abs(y0 + by + bh / 2 - (y + h / 2))
        if d <= SEARCH / 2 and (best is None or d < best[0]):
            best = (d, (sym, int(x0 + bx), int(y0 + by), int(bw), int(bh)))
    return best[1] if best else None


def gxt_texture(data):
    """(format, width, height, first-level bytes) of a one-texture swizzled GXT we can read, or None."""
    if len(data) < 64:
        return None
    _, _, n = struct.unpack('<4sII', data[:12])
    if n != 1:
        return None
    off, size, _, _, ty, fmt, w, h = struct.unpack('<IIiIIIHH', data[32:60])
    fmt &= 0x9f000000
    if ty != 0 or fmt not in (UBC1, UBC3, U8):
        return None
    return fmt, w, h, data[off:off + level_size(fmt, w, h)]


def family_of(name):
    for fam in FAMILIES:
        if name == fam or re.fullmatch(re.escape(fam) + r'_[a-z]{2,4}', name):
            return fam
    return None


def members(base, wanted):
    with open(base + '.pfs', 'rb') as f:
        files = lspk.read_tree(f.read())
    with open(base + '.pkh', 'rb') as f:
        index = lspk.read_index(f.read())
    out = {}
    with open(base + '.pk', 'rb') as pk:
        for p in files:
            if not wanted(p):
                continue
            off, size, csize = index[lspk.path_hash(p)]
            pk.seek(off)
            data = pk.read(csize or size)
            out[p] = zlib.decompress(data) if csize else data
    return out


def font_slots(gly):
    """The font page's □ △ ○ cells: .gly is a big-endian u16 count, a 10-byte header (cell height at
    +4, in 1/128 pixel), then 14-byte records: UTF-16 code, x, y, width (1/128 pixel), ..."""
    count = struct.unpack('>H', gly[:2])[0]
    cell = struct.unpack('>H', gly[4:6])[0] / 128
    slots = []
    for i in range(count):
        code, x, y, w = struct.unpack('>4H', gly[10 + i * 14:18 + i * 14])
        if code in FONT_SYMBOLS:
            x0, y0 = math.floor(x / 128), math.floor(y / 128)
            slots.append((FONT_SYMBOLS[code], x0, y0, math.ceil((x + w) / 128) - x0, math.ceil(y / 128 + cell) - y0))
    return slots


def main():
    retail, out_path = sys.argv[1], sys.argv[2]

    def wanted(p):
        name = p.rsplit('/', 1)[-1]
        return (p.startswith(TEXTURE) and name.endswith('.gxt') and family_of(name[:-4])) or p.startswith(FONT)

    archives = [(arc, members(os.path.join(retail, arc), wanted)) for arc in ('archive', 'archive_patch3')]
    textures, font = {}, {}
    for arc, files in archives:
        for path, data in files.items():
            if path.startswith(FONT):
                font[path[len(FONT):]] = data
                continue
            t = gxt_texture(data)
            if t:
                textures[(arc, path.rsplit('/', 1)[-1][:-4])] = t
    refs = {}
    for fam, ref in REFERENCE.items():
        fmt, w, h, raw = textures[('archive', ref)]
        refs[fam] = premultiplied(decode(raw, fmt, w, h))
    entries, seen = [], {}

    def add(h64, fmt, w, h, fam, copy, slots):
        if h64 in seen:
            seen[h64][4].append(copy)
            return
        entries.append((h64, fmt, w, h, [fam, copy], slots))
        seen[h64] = entries[-1]

    for (arc, name), (fmt, w, h, raw) in sorted(textures.items()):
        fam = family_of(name)
        rgba = decode(raw, fmt, w, h)
        img = premultiplied(rgba)
        slots, notes = [], []
        for box in FAMILIES[fam]:
            found, d = find(img, refs[fam], box)
            if not found and box[0] not in (START, SELECT):  # a word: another language's is another word
                found = snap(rgba, box)
                if found:
                    print('%s/%s: %s snapped to %d,%d %dx%d' % (arc, name, *found), file=sys.stderr)
            if found:
                slots.append(found)
            else:
                notes.append('%s %d,%d (best %s)' % (box[0], box[1], box[2], '%.1f' % d if d is not None else '-'))
        label = '%s/%s' % (arc, name)
        if notes:
            print('%s: not found: %s' % (label, ', '.join(notes)), file=sys.stderr)
        if not slots:
            continue
        moved = [s for s, b in zip(slots, FAMILIES[fam]) if s[1:3] != b[1:3]]
        print('%-36s %d symbols%s' % (label, len(slots), ', %d moved' % len(moved) if moved else ''), file=sys.stderr)
        # the language suffix ('-': none), and where archive_patch3 replaces the archive's copy
        copy = (name[len(fam):].lstrip('_') or '-') + (' (patch3)' if arc == 'archive_patch3' else '')
        add(fnv1a64(raw), fmt, w, h, fam, copy, slots)

    t = gxt_texture(font['.gxt'])
    fmt, w, h, raw = t
    slots = font_slots(font['.gly'])
    print('%-36s %d symbols' % (FONT.rsplit('/', 1)[-1], len(slots)), file=sys.stderr)
    add(fnv1a64(raw), fmt, w, h, FONT.rsplit('/', 1)[-1], '-', slots)

    lines = ['// Generated by ss-delta tools/button-atlases.py from the game\'s archives: the textures with',
             '// PlayStation buttons in them (FNV-1a 64 of the texture data, base format, width, height) and the',
             '// symbols in them (x, y, w, h). Hashes and coordinates only.']
    for h64, fmt, w, h, names, slots in entries:
        name = names[0] + ' ' + '/'.join(names[1:])
        sl = ', '.join('{ Symbol::%s, %d, %d, %d, %d }' % s for s in slots)
        lines.append('{ 0x%016xull, 0x%08xu, %d, %d, "%s", { %s } },' % (h64, fmt, w, h, name, sl))
    with open(out_path, 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('%d textures -> %s' % (len(entries), out_path), file=sys.stderr)


if __name__ == '__main__':
    main()
