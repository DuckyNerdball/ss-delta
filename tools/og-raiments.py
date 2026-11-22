"""Builds the "original raiments" mod: the two collaboration raiments only the original Soul Sacrifice
has (ARKS Armor, from PSO2, and Dragonslayer / Ace of Souls, from Ragnarok Odyssey ACE), added to
Soul Sacrifice Delta as raiments 720-731 and 732-743 (GitHub issue #11; docs/01-research.md,
"The original's collaboration raiments"; docs/decisions.md D28).

The mod is a rePatch mod, like the Undub: a copy of the game's archive_patch3 (.pk, .pkh) with
  * the raiments' models and textures, read from the player's own dump of the original game
    (1.30): resource/data/model/CS21_*.mdl, CS22_*.mdl and resource/data/mdltex/CS21_*, CS22_*;
  * Delta's costume_table.csv, parts_upper_param.csv and parts_lower_param.csv with the new rows
    (the whole-body model as both top and bottom, as the original drew it).
Nothing of either game is in this repository; everything is made from the player's files.

usage:
  python -I tools/og-raiments.py --original <dump> --vita-fs <folder> [--title ID] [--exe FILE]
                                 [--out DIR] [--work DIR]
  python -I tools/og-raiments.py --remove --vita-fs <folder> [--title ID]

  --original  the original Soul Sacrifice with update 1.30 (US PCSA00092, EU PCSF00178, ...): an
              installed or decrypted app folder (resource/data/pack/mount/retail/archive*), a Vita
              file system with it in ux0/app/, or a NoNpDrm dump (folder or .zip with its
              licences), which is installed into --work with the game's front end (--exe) first
  --vita-fs   the Vita file system with Soul Sacrifice Delta installed (ss-delta.ini's vita_fs);
              the mod is built on the archive_patch3 the game reads now (an Undub's in
              ux0/rePatch/<title>/ if there is one) and installed into ux0/rePatch/<title>/
  --title     PCSA00152 (US) or PCSF00532 (EU), when both are installed
  --exe       ss-delta.exe (or another front end of the fork) for installing a NoNpDrm dump;
              default: the one next to this checkout's build, or on the PATH
  --out       write the mod as a folder (DIR/rePatch/<title>/...) instead of installing it, to
              install with the setup's "Add an add-on or mod" or copy elsewhere
  --work      where a NoNpDrm dump is installed (default: a temporary folder, removed after)
  --remove    take the mod out again: the archive it was built on is restored (the game's own:
              the rePatch files are deleted)

Build the mod again after installing or updating another mod that replaces archive_patch3 (the
Undub): that one replaces this one's archive, and building on it keeps both.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lspk  # noqa: E402

RETAIL = ('resource', 'data', 'pack', 'mount', 'retail')
DELTA_TITLES = ('PCSA00152', 'PCSF00532')
MANIFEST = 'ss-delta/og-raiments/manifest.json'
ORIGINALS = 'ss-delta/og-raiments/base/'  # the replaced members as they were, to undo the mod
TABLES = ('resource/boot/costume_table.csv', 'resource/boot/parts_upper_param.csv',
          'resource/boot/parts_lower_param.csv')

# the new raiments: 12 rows each (colours A-I and the three faction colours, as Delta's own), only
# colour A given (the original had one colour), copied from Mononofu's block (624-635), the other
# collaboration raiment of the original, which Delta has. Names: Delta's text, all languages.
TEMPLATE_FIRST = 624
RAIMENTS = (
    # first row, type number, text id, model, Japanese name for the table's comments
    (720, 51, 3954, 'CS21', 'アークス装甲衣'),
    (732, 52, 3956, 'CS22', '滅竜士の法衣'),
)
BASE_ROWS = 720  # Delta 1.30's costume_table.csv rows


def is_lspk(base):
    """True for a readable (decrypted) LSPK archive at base (.pkh, .pk)."""
    try:
        with open(base + '.pkh', 'rb') as f:
            head = f.read(4)
        count = int.from_bytes(head, 'big')
        return 0 < count < 1000000 and os.path.getsize(base + '.pkh') == 4 + 16 * count
    except OSError:
        return False


def app_dirs(root):
    """Candidate app folders (holding resource/data/pack/mount/retail/archive) under root."""
    found = []
    for base in (root, os.path.join(root, 'ux0', 'app'), os.path.join(root, 'app')):
        if os.path.isfile(os.path.join(base, *RETAIL, 'archive.pkh')):
            found.append(base)
        elif os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                if os.path.isfile(os.path.join(base, name, *RETAIL, 'archive.pkh')):
                    found.append(os.path.join(base, name))
    return found


def original_files(app):
    """The raiments' model and texture members of the original, read from its archive_patch3 (1.30)
    and archive. None when this app isn't the original with them."""
    retail = os.path.join(app, *RETAIL)
    archives = [os.path.join(retail, a) for a in ('archive_patch3', 'archive') if is_lspk(os.path.join(retail, a))]
    if not archives:
        return None
    names = set()
    for a in archives:
        if os.path.isfile(a + '.pfs'):
            with open(a + '.pfs', 'rb') as f:
                names.update(lspk.read_tree(f.read()))
    want = sorted(n for n in names if any(n.startswith(p) for p in (
        'resource/data/model/CS21_', 'resource/data/model/CS22_',
        'resource/data/mdltex/CS21_', 'resource/data/mdltex/CS22_')))
    files = {}
    for n in want:
        for a in archives:
            data = lspk.read_member(a, n)
            if data is not None:
                files[n] = data
                break
    models = [n for n in files if n.endswith('.mdl')]
    if len(models) != 4:
        return None
    return files


def find_original(path, exe, work):
    candidates = app_dirs(path) if os.path.isdir(path) else []
    for app in candidates:
        files = original_files(app)
        if files:
            return app, files
    # a NoNpDrm dump: installed (decrypted) with the front end first
    if not exe:
        sys.exit('the original game there is encrypted (a NoNpDrm dump): give --exe <ss-delta.exe> to install it')
    fs = os.path.join(work, 'fs')
    os.makedirs(fs, exist_ok=True)
    print(f'installing the original game into {fs} (decrypting it)')
    r = subprocess.run([exe, '--vita-fs', fs, '--install-content', os.path.abspath(path)])
    if r.returncode:
        sys.exit(f'installing {path} failed ({exe} returned {r.returncode})')
    for app in app_dirs(fs):
        files = original_files(app)
        if files:
            return app, files
    sys.exit(f'{path}: no original Soul Sacrifice 1.30 with the collaboration raiments found in it')


def default_exe():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for c in (os.path.join(here, 'build', 'vita3k', 'bin', 'RelWithDebInfo', 'ss-delta.exe'),
              shutil.which('ss-delta.exe'), shutil.which('ss-delta')):
        if c and os.path.isfile(c):
            return c
    return None


def delta_title(fs, title):
    installed = [t for t in DELTA_TITLES if os.path.isfile(os.path.join(fs, 'ux0', 'app', t, *RETAIL, 'archive_patch3.pkh'))]
    if title:
        if title not in installed:
            sys.exit(f'{title} (Soul Sacrifice Delta 1.30) is not installed in {fs}')
        return title
    if not installed:
        sys.exit(f'no Soul Sacrifice Delta 1.30 ({", ".join(DELTA_TITLES)}) installed in {fs}')
    if len(installed) > 1:
        sys.exit(f'both {" and ".join(installed)} are installed in {fs}: pick one with --title')
    return installed[0]


def lines_of(data):
    text = data.decode('cp932')
    return [l for l in text.replace('\r\n', '\n').split('\n') if l != '']


def encode(lines):
    return ('\r\n'.join(lines) + '\r\n').encode('cp932')


def row(lines, sex, number):
    """The part table line of a sex and row number (fields: TYPE, sex, number, ...)."""
    for l in lines:
        c = l.split(',')
        if len(c) > 3 and c[0] == 'body' and c[1] == sex and c[2] == str(number):
            return c
    sys.exit(f'part table: no row {sex} {number}')


def body_params(original_app):
    """The original's parts_body_param.csv fields for the two models (hood flags, colours)."""
    retail = os.path.join(original_app, *RETAIL)
    for a in ('archive_patch3', 'archive'):
        data = lspk.read_member(os.path.join(retail, a), 'resource/boot/parts_body_param.csv') if is_lspk(os.path.join(retail, a)) else None
        if data:
            params = {}
            for l in lines_of(data):
                c = l.split(',')
                if len(c) > 11 and c[0] == 'body':
                    params.setdefault(c[3], c)
            return params
    sys.exit('the original game has no parts_body_param.csv')


def new_tables(tables, params):
    costume = lines_of(tables[0])
    upper = lines_of(tables[1])
    lower = lines_of(tables[2])
    numbered = [l for l in costume if l.split(',')[0].isdigit()]
    if len(numbered) != BASE_ROWS or numbered[-1].split(',')[0] != str(BASE_ROWS - 1):
        sys.exit(f'costume_table.csv has {len(numbered)} rows, not the {BASE_ROWS} of Delta 1.30 (another mod?)')
    template = {int(l.split(',')[0]): l.split(',') for l in numbered}
    width = len(costume[0].split(','))
    added_upper, added_lower = [], []
    for first, type_no, text_id, model, name in RAIMENTS:
        costume.append('#' + name + ',' * (width - 1))
        for i in range(12):
            c = list(template[TEMPLATE_FIRST + i])
            c[0], c[2], c[3], c[5] = str(first + i), str(type_no), '0', str(text_id)
            if i == 0:  # colour A: given by ss-delta (the add-on), no exchange
                c[6], c[7], c[8] = '0', '0', '0'
            c[16] = name
            costume.append(','.join(c))
        for sex in ('M', 'F'):
            src = params.get(f'{model}_{sex}0')
            if not src:
                sys.exit(f'the original game has no {model}_{sex}0 in parts_body_param.csv')
            for i in range(12):
                colour = row(upper, sex, TEMPLATE_FIRST + i)[6].split('：')[-1]
                comment = f'{name}{"男" if sex == "M" else "女"}：{colour}'
                # upper: TYPE, sex, number, chr, hood Head, hood Hair, comment, colours (4), SE
                added_upper.append(','.join(['body', sex, str(first + i), src[3], src[4], src[5], comment] + src[7:12]))
                # lower: TYPE, sex, number, chr, comment, colours (4), SE
                added_lower.append(','.join(['body', sex, str(first + i), src[3], comment] + src[7:12]))
    upper += [l for l in added_upper if l.split(',')[1] == 'M'] + [l for l in added_upper if l.split(',')[1] == 'F']
    lower += [l for l in added_lower if l.split(',')[1] == 'M'] + [l for l in added_lower if l.split(',')[1] == 'F']
    return [encode(costume), encode(upper), encode(lower)]


def base_state(fs, title):
    """(archive the game reads now, its manifest if this mod built it, whether it's in rePatch)."""
    repatch = os.path.join(fs, 'ux0', 'rePatch', title, *RETAIL, 'archive_patch3')
    game = os.path.join(fs, 'ux0', 'app', title, *RETAIL, 'archive_patch3')
    base = repatch if os.path.isfile(repatch + '.pkh') and os.path.isfile(repatch + '.pk') else game
    if not is_lspk(base):
        sys.exit(f'{base}.pkh is not a readable archive')
    data = lspk.read_member(base, MANIFEST)
    return base, (json.loads(data) if data else None), base == repatch


def undo_members(base, manifest):
    """What restores the archive this mod was built on: (members to put back, paths to drop)."""
    put = {p: lspk.read_member(base, ORIGINALS + p) for p in manifest['replaced']}
    drop = list(manifest['added']) + [ORIGINALS + p for p in manifest['replaced']] + [MANIFEST]
    return put, drop


def write_archive(base, out, members, remove):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp'
    count, _ = lspk.pack(base, tmp, members, remove)
    for ext in ('.pk', '.pkh'):
        os.replace(tmp + ext, out + ext)
    return count


def remove_mod(fs, title):
    base, manifest, in_repatch = base_state(fs, title)
    if not manifest:
        sys.exit('the archive the game reads has no original raiments in it: nothing to remove')
    if manifest.get('built_on') == 'game':
        for ext in ('.pk', '.pkh'):
            os.remove(base + ext)
        # the folders up to rePatch/<title>/ that are empty now
        top = os.path.join(fs, 'ux0', 'rePatch', title)
        d = os.path.dirname(base)
        while os.path.normcase(d).startswith(os.path.normcase(top)) and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
        print(f'removed {base}.pk/.pkh: the game reads its own archive_patch3 again')
    else:
        put, drop = undo_members(base, manifest)
        write_archive(base, base, put, drop)
        print(f'{base}.pk/.pkh: the original raiments taken out, the mod it was built on kept')
    print('A save that wears ARKS Armor or Dragonslayer shows no body until another raiment is put on'
          ' (Portraiture > Appearance > Raiments).')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--original')
    p.add_argument('--vita-fs', required=True)
    p.add_argument('--title', choices=DELTA_TITLES)
    p.add_argument('--exe')
    p.add_argument('--out')
    p.add_argument('--work')
    p.add_argument('--remove', action='store_true')
    a = p.parse_args()
    fs = os.path.abspath(a.vita_fs)
    title = delta_title(fs, a.title)
    if a.remove:
        remove_mod(fs, title)
        return
    if not a.original:
        p.error('--original is needed (or --remove)')
    work = a.work or tempfile.mkdtemp(prefix='og-raiments-')
    try:
        app, files = find_original(os.path.abspath(a.original), a.exe or default_exe(), work)
        print(f'original game: {app} ({len(files)} model and texture files)')
        params = body_params(app)
        base, manifest, in_repatch = base_state(fs, title)
        game_archive = os.path.join(fs, 'ux0', 'app', title, *RETAIL, 'archive')
        put, drop = undo_members(base, manifest) if manifest else ({}, [])
        built_on = manifest['built_on'] if manifest else ('rePatch' if in_repatch else 'game')
        # the tables as the archive this is built on has them (or the game's archive behind it)
        tables, replaced, added = [], [], []
        for t in TABLES:
            data = put.get(t) if t in put else lspk.read_member(base, t)
            if data is None:
                data = lspk.read_member(game_archive, t)
                added.append(t)
            else:
                replaced.append(t)
            tables.append(data)
        members = dict(zip(TABLES, new_tables(tables, params)))
        members.update(files)
        added += sorted(files)
        for t, data in zip(TABLES, tables):
            if t in replaced:
                members[ORIGINALS + t] = data
        members[MANIFEST] = json.dumps({'version': 1, 'built_on': built_on, 'added': added,
                                        'replaced': replaced}, indent=1).encode()
        if a.out:
            out = os.path.join(os.path.abspath(a.out), 'rePatch', title, *RETAIL, 'archive_patch3')
        else:
            out = os.path.join(fs, 'ux0', 'rePatch', title, *RETAIL, 'archive_patch3')
        count = write_archive(base, out, members, [d for d in drop if d not in members])
        print(f'{out}.pk/.pkh: {count} members, the original raiments (rows 720-743) added'
              f'{" over the mod that was there" if built_on == "rePatch" else ""}')
        if a.out:
            print(f'install it with the setup ("Add an add-on or mod", the folder {os.path.abspath(a.out)})'
                  ' or ss-delta.exe --install-content')
    finally:
        if not a.work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
