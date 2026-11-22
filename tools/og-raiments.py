"""Makes the "original raiments" mod: the two collaboration raiments only the original Soul Sacrifice
has (ARKS Armor, from PSO2, and Dragonslayer / Ace of Souls, from Ragnarok Odyssey ACE), added to
Soul Sacrifice Delta as raiments 720-731 and 732-743 (GitHub issue #11; docs/01-research.md,
"The original's collaboration raiments"; docs/decisions.md D28).

The mod is a packaged mod (ss-delta-og-raiments.zip, about 1.5 MB; the format is in BUILDING,
"Packaged mods"), which ss-delta merges into the archive the game reads (its own archive_patch3,
or an Undub's), in any order with other mods:
  * the raiments' models and textures, read from the player's own copy of the original game
    (1.30): resource/data/model/CS21_*.mdl, CS22_*.mdl and resource/data/mdltex/CS21_*, CS22_*;
  * the rows to append to Delta's costume_table.csv, parts_upper_param.csv and
    parts_lower_param.csv (the whole-body model as both top and bottom, as the original drew it).
Nothing of either game is in this repository; everything is made from the player's files.

usage:
  python -I tools/og-raiments.py --original <dump> --vita-fs <folder> [--title ID] [--exe FILE]
                                 [--out DIR|FILE.zip] [--work DIR]
  python -I tools/og-raiments.py --remove --vita-fs <folder> [--title ID] [--exe FILE]

  --original  the original Soul Sacrifice with update 1.30 (US PCSA00092, EU PCSF00178, ...): an
              installed or decrypted app folder (resource/data/pack/mount/retail/archive*), a Vita
              file system with it in ux0/app/, or a NoNpDrm dump (folder or .zip with its
              licences), which is installed into --work with the game's front end (--exe) first
  --vita-fs   the Vita file system with Soul Sacrifice Delta 1.30 installed (ss-delta.ini's
              vita_fs): its tables are the template for the new rows, and the mod is installed
              there (unless --out)
  --title     PCSA00152 (US) or PCSF00532 (EU), when both are installed
  --exe       ss-delta.exe (or another front end of the fork): installs the mod, and a NoNpDrm
              dump; default: the one next to this checkout's build, or on the PATH
  --out       write the mod there (a folder, or a .zip path) instead of installing it; add it later
              with the setup's "Add an add-on or mod", Android's "Add an add-on", or
              ss-delta.exe --install-content <zip>
  --work      where a NoNpDrm dump is installed (default: a temporary folder, removed after)
  --remove    take the mod out again (ss-delta.exe --remove-mod og-raiments; also an archive built
              by the earlier version of this script)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lspk  # noqa: E402

RETAIL = ('resource', 'data', 'pack', 'mount', 'retail')
DELTA_TITLES = ('PCSA00152', 'PCSF00532')
MOD_ID = 'og-raiments'
VERSION = '1'
ZIP_NAME = 'ss-delta-og-raiments.zip'
TABLES = ('resource/boot/costume_table.csv', 'resource/boot/parts_upper_param.csv',
          'resource/boot/parts_lower_param.csv')
# the earlier version of this script (a whole archive_patch3 in rePatch) kept these in it
LEGACY_MANIFEST = 'ss-delta/og-raiments/manifest.json'
LEGACY_ORIGINALS = 'ss-delta/og-raiments/base/'

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
REMOVE_NOTE = ('A save that wears ARKS Armor or Dragonslayer shows no body until another raiment is put on '
               '(Portraiture > Appearance > Raiments).')
README = f"""ARKS Armor and Dragonslayer, the original Soul Sacrifice's collaboration raiments, for
Soul Sacrifice Delta in ss-delta (https://github.com/vita-recomps/ss-delta), version {VERSION}.

This is an ss-delta packaged mod: add this .zip as it is, without unpacking it.
  * Windows, Linux, macOS: start the game with --install and add it in the importer, or run
    ss-delta --install-content "{ZIP_NAME}"
  * Android: long-press the app's icon > Add an add-on, and pick the .zip.
It works with the US and the EU game, and with the Undub patch installed before or after it.

In the game: Portraiture > Appearance > Raiments: Top, marked NEW (Add-ons (DLC) must be on).
Wear one as both top and bottom (Triangle, "Match with Above", in the bottom list).

To remove it: put on another raiment first, then ss-delta --remove-mod {MOD_ID}.

It needs ss-delta: the game itself doesn't give raiments past its own, so on a Vita (rePatch) the
two never appear.
"""


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


def delta_tables(fs, title):
    """Delta's own three tables (from its archive_patch3, else its archive): the new rows' template."""
    retail = os.path.join(fs, 'ux0', 'app', title, *RETAIL)
    tables = []
    for t in TABLES:
        for a in ('archive_patch3', 'archive'):
            data = lspk.read_member(os.path.join(retail, a), t) if is_lspk(os.path.join(retail, a)) else None
            if data:
                tables.append(data)
                break
        else:
            sys.exit(f'{title} has no {t}')
    return tables


def new_rows(tables, params):
    """The lines to append to costume_table.csv, parts_upper_param.csv and parts_lower_param.csv."""
    costume = lines_of(tables[0])
    upper = lines_of(tables[1])
    numbered = [l for l in costume if l.split(',')[0].isdigit()]
    if len(numbered) != BASE_ROWS or numbered[-1].split(',')[0] != str(BASE_ROWS - 1):
        sys.exit(f'costume_table.csv has {len(numbered)} rows, not the {BASE_ROWS} of Delta 1.30')
    template = {int(l.split(',')[0]): l.split(',') for l in numbered}
    width = len(costume[0].split(','))
    add_costume, add_upper, add_lower = [], [], []
    for first, type_no, text_id, model, name in RAIMENTS:
        add_costume.append('#' + name + ',' * (width - 1))
        for i in range(12):
            c = list(template[TEMPLATE_FIRST + i])
            c[0], c[2], c[3], c[5] = str(first + i), str(type_no), '0', str(text_id)
            if i == 0:  # colour A: given by ss-delta (the add-on), no exchange
                c[6], c[7], c[8] = '0', '0', '0'
            c[16] = name
            add_costume.append(','.join(c))
        for sex in ('M', 'F'):
            src = params.get(f'{model}_{sex}0')
            if not src:
                sys.exit(f'the original game has no {model}_{sex}0 in parts_body_param.csv')
            for i in range(12):
                colour = row(upper, sex, TEMPLATE_FIRST + i)[6].split('：')[-1]
                comment = f'{name}{"男" if sex == "M" else "女"}：{colour}'
                # upper: TYPE, sex, number, chr, hood Head, hood Hair, comment, colours (4), SE
                add_upper.append(','.join(['body', sex, str(first + i), src[3], src[4], src[5], comment] + src[7:12]))
                # lower: TYPE, sex, number, chr, comment, colours (4), SE
                add_lower.append(','.join(['body', sex, str(first + i), src[3], comment] + src[7:12]))
    order = lambda rows: [l for l in rows if l.split(',')[1] == 'M'] + [l for l in rows if l.split(',')[1] == 'F']
    return [add_costume, order(add_upper), order(add_lower)]


def write_package(out, files, rows):
    """The packaged mod (ss-delta-mod.json, files/, tables/, README.txt) as a zip at out."""
    names = [t.rsplit('/', 1)[1] for t in TABLES]
    firsts = [str(first) for first, *_ in RAIMENTS]
    conflicts = [[f + ',' for f in firsts]] + [[f'body,{s},{f},' for s in 'MF' for f in firsts]] * 2
    manifest = {
        'ss-delta-mod': 1,
        'id': MOD_ID,
        'name': "The original Soul Sacrifice's raiments: ARKS Armor and Dragonslayer",
        'version': VERSION,
        'titles': list(DELTA_TITLES),
        'archive': '/'.join(RETAIL + ('archive_patch3',)),
        'tables_from': ['/'.join(RETAIL + ('archive',))],
        'append': [{'member': t, 'lines': 'tables/' + n, 'conflicts': c}
                   for t, n, c in zip(TABLES, names, conflicts)],
        'remove_note': REMOVE_NOTE,
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tmp = out + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('ss-delta-mod.json', json.dumps(manifest, indent=1, ensure_ascii=False))
        z.writestr('README.txt', README.replace('\n', '\r\n'))
        for n, lines in zip(names, rows):
            z.writestr('tables/' + n, encode(lines))
        for path in sorted(files):
            z.writestr('files/' + path, files[path])
    os.replace(tmp, out)


def legacy_remove(fs, title):
    """An archive_patch3 built by the earlier version of this script: the archive it was built on
    restored. False when the game reads no such archive."""
    base = os.path.join(fs, 'ux0', 'rePatch', title, *RETAIL, 'archive_patch3')
    if not is_lspk(base) or not os.path.isfile(base + '.pk'):
        return False
    data = lspk.read_member(base, LEGACY_MANIFEST)
    if not data:
        return False
    manifest = json.loads(data)
    if manifest.get('built_on') == 'game':
        for ext in ('.pk', '.pkh'):
            os.remove(base + ext)
        top = os.path.join(fs, 'ux0', 'rePatch', title)
        d = os.path.dirname(base)
        while os.path.normcase(d).startswith(os.path.normcase(top)) and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
        print(f'removed {base}.pk/.pkh (made by the earlier version of this script): the game reads its own archive_patch3 again')
    else:
        put = {p: lspk.read_member(base, LEGACY_ORIGINALS + p) for p in manifest['replaced']}
        drop = list(manifest['added']) + [LEGACY_ORIGINALS + p for p in manifest['replaced']] + [LEGACY_MANIFEST]
        lspk.pack(base, base + '.tmp', put, drop)
        for ext in ('.pk', '.pkh'):
            os.replace(base + '.tmp' + ext, base + ext)
        print(f'{base}.pk/.pkh: the raiments of the earlier version taken out, the mod it was built on kept')
    return True


def front_end(exe, fs, *args):
    if not exe:
        sys.exit('give --exe <ss-delta.exe> (the game\'s front end installs and removes the mod)')
    r = subprocess.run([exe, '--vita-fs', fs, *args])
    return r.returncode == 0


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
    exe = a.exe or default_exe()
    if a.remove:
        legacy = legacy_remove(fs, title)
        installed = os.path.isdir(os.path.join(fs, 'ux0', 'rePatch', title, 'ss-delta-mods', MOD_ID))
        if installed and not front_end(exe, fs, '--remove-mod', MOD_ID):
            sys.exit('removing the mod failed (the front end\'s log, ss-delta/vita3k.log, says why)')
        if not legacy and not installed:
            sys.exit(f'the original raiments are not installed for {title}')
        print(REMOVE_NOTE)
        return
    if not a.original:
        p.error('--original is needed (or --remove)')
    work = a.work or tempfile.mkdtemp(prefix='og-raiments-')
    try:
        app, files = find_original(os.path.abspath(a.original), exe, work)
        print(f'original game: {app} ({len(files)} model and texture files)')
        rows = new_rows(delta_tables(fs, title), body_params(app))
        if a.out:
            out = os.path.abspath(a.out)
            if not out.lower().endswith('.zip'):
                out = os.path.join(out, ZIP_NAME)
        else:
            out = os.path.join(work, ZIP_NAME)
        write_package(out, files, rows)
        print(f'{out}: {os.path.getsize(out) / 1048576:.1f} MB ({len(files)} files, {sum(map(len, rows))} table rows)')
        if a.out:
            print('add it with the setup ("Add an add-on or mod"), Android\'s "Add an add-on",'
                  ' or ss-delta.exe --install-content <the zip>')
            return
        if not front_end(exe, fs, '--install-content', out):
            sys.exit('installing the mod failed (the front end\'s log, ss-delta/vita3k.log, says why)')
        print(f'installed for {title}: ARKS Armor and Dragonslayer appear in Raiments, marked NEW')
    finally:
        if not a.work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    main()
