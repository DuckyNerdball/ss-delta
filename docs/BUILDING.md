# Building ss-delta

For players, the [releases](https://github.com/vita-recomps/ss-delta/releases/latest)
need no building: see [INSTALLING](INSTALLING.md). This guide builds the
game's front end from source, installs a game into a development folder,
and makes a release.

## Contents

* [Requirements](#requirements)
* [Building from a fresh clone](#building-from-a-fresh-clone)
* [Installing your game into a build](#installing-your-game-into-a-build)
* [Playing a build](#playing-a-build)
* [Making a release](#making-a-release)
* [Toolchain](#toolchain)
* [Tools](#tools)

## Requirements

* Your own dump of the game and the firmware update files `PSVUPDAT.PUP`
  and `PSP2UPDAT.PUP` (as for Vita3K; `third_party/recomp/tools/fetch-firmware.py`
  downloads them from Sony), as in [INSTALLING](INSTALLING.md#what-you-need).
* Git, Python 3.12 with `capstone` and `pyyaml` (`pip install capstone
  pyyaml`; `pycryptodome` for SELF decryption in the research tools).
* **Windows:** Visual Studio 2022 or its Build Tools with "Desktop
  development with C++" (MSVC x64, the Windows SDK, CMake and Ninja), the
  Vulkan SDK, and Qt 6.11 for MSVC x64 for Vita3K's own interface (e.g. with
  `aqtinstall` into `C:\Qt`; `--games-only` builds without it).
* **Linux:** GCC 14 or newer, CMake, Ninja. Release builds use the Steam
  Runtime 3 (sniper) SDK, whose glibc 2.31 the game then needs at most
  ([07-linux](07-linux.md)).
* **macOS:** Apple's Command Line Tools (or Xcode), CMake and Ninja
  ([08-macos](08-macos.md)).

## Building from a fresh clone

```
git clone --recurse-submodules https://github.com/vita-recomps/ss-delta.git ss-delta
cd ss-delta
python -I third_party/recomp/tools/build-vita3k.py --target ss-delta
```

On Windows the script finds MSVC (vswhere) and Qt (`Qt6_ROOT`, `--qt <dir>`,
or the newest `C:\Qt\<version>\msvc20*_64`). The first build takes about ten
minutes and puts `ss-delta.exe` in `build/vita3k/bin/RelWithDebInfo/`.
`--games-only` builds the single-game executables without Qt into
`build/vita3k-games/`.

On Linux and macOS the same command builds `ss-delta.x86_64` or
`ss-delta.arm64` (the games only). The release workflow
(`.github/workflows/release.yml`) shows each platform's build exactly.

## Installing your game into a build

```
python -I third_party/recomp/tools/install-game.py --name ss-delta ^
    --firmware PSVUPDAT.PUP PSP2UPDAT.PUP ^
    --install "<your dump: folder, .zip or .vpk>"
```

(For a pkg: `--install "<game>.pkg" --license "<work.bin>" --install
"<1.30 patch>.pkg"`.) The script installs the firmware and the game into a
Vita file system, checks that `eboot.bin` is 1.30, runs the game briefly to
write its modules out, recompiles them and the firmware modules to C++ and
compiles them (this takes a while), then lays out `dist/ss-delta/`: the
front end, the recompiled `ssd_aot_*` modules, a commented `ss-delta.ini`
and the Vita file system in `fs/`. Everything in it is derived from your
copy: don't share it. `--toolchain <dir>` compiles with the downloaded
toolchain instead of MSVC (`toolchain.py fetch`), as a release's importer
does.

## Playing a build

Run `dist/ss-delta/ss-delta.exe` (Linux: `ss-delta.x86_64`; macOS:
`ss-delta.arm64`). `README.txt` in that folder, and
[INSTALLING](INSTALLING.md#playing), explain the settings, saves and Ad
Hoc Play. `--help` lists the command line.

## Making a release

A release is the game's own folder: the front end, its files, and in
`setup/` the importer (Python with Tk, and the recompiler kit), which builds
the game on the player's computer the first time it starts
([D22](decisions.md)). Nothing in it is derived from the game.

```
python -I third_party/recomp/tools/build-vita3k.py --project . --games-only
python -I third_party/recomp/tools/make-setup.py build third_party/recomp/tools/setup-windows.json ^
    --project . --bin build/vita3k-games/bin/RelWithDebInfo --out build/release/ss-delta ^
    --zip --archive build/release/ss-delta-<version>-windows
```

Linux and macOS take `setup-linux.json` and `setup-macos.json` (run there,
with Python 3.12). Pushing a tag `v*` runs `.github/workflows/release.yml`,
which builds all three archives on GitHub, with their SHA-256 and build
attestations, into a draft release.

## Toolchain

The Vita3K fork and the recompiler are git submodules, repositories of their
own ([D17](decisions.md)):

* `third_party/vita3k`: our Vita3K fork, branch `games` (the single-game
  front end `vita3k/game-frontend/` and one executable per game,
  `vita3k/games/ss-delta/` for `ss-delta.exe`);
* `third_party/recomp`: vita-recomp-kit, the recompiler (`recomp/`), the
  generic tools and the build, install and packaging scripts. `game.json`
  describes this game to those scripts.

## Tools

| Script | What |
|---|---|
| `tools/lspk.py` | list and extract the game's LSPK archives (`.pkh`/`.pk`/`.pfs`) |
| `tools/questmaps.py` | the quest map list from `quest_param.csv` |
| `tools/map-sweep.ps1` | screenshot every quest map through Stage Select (`-Frames`: at render resolution) |
| `tools/devshell.ps1` | dot-source to load MSVC x64 and point CMake at Qt 6.11.0 (a fresh configure of the fork, `recomp/run-tests.ps1`) |
| `tools/package4090.ps1` | build `dist/ss-delta-vita3k-test` (both Vita3K builds, the installed game, `run-matrix.bat`/`play.bat` from `tools/pkg4090/`) for testing on another PC |
| `tools/deck-quest.sh` | on a Steam Deck: frame rate and APU power in a quest |
| `game.json` | this game for the shared scripts: title, supported eboot, modules to recompile, the folder's README per platform |

From the shared toolchain (`third_party/recomp/`, each script's docstring
has its options):

| Script | What |
|---|---|
| `tools/build-vita3k.py` | configure and build our Vita3K fork (`third_party/vita3k`) into `build/vita3k` (MSVC found with vswhere, Qt in its default folder; `--games-only`, `--no-jit`) |
| `tools/install-game.py`, `tools/make-dist.py` | a playable folder in `dist/` from the player's dump and firmware, as `game.json` describes it |
| `tools/make-setup.py`, `tools/setup.py` | a release, and its importer |
| `tools/velf.py` | Vita SCE ELF: segments, module_info, NID-named imports/exports, exidx |
| `tools/vitaelf.py` | library: Vita ELF segments, module_info, imports/exports, exidx, EHABI exception scopes |
| `tools/inventory.py` | per-module code inventory into `generated/inventory/<module>/` (see [04-inventory](04-inventory.md)) |
| `tools/imix.py` | Capstone instruction-mix sweep over every exidx function |
| `tools/sfo.py` | print `param.sfo` fields |
| `tools/v3kdrive.py` | drive Vita3K or `ss-delta.exe` without focus: launch, `BootSequence`, buttons, touches, FPS sampling, screenshots |
| `tools/stackdump.py` | every thread's call stack of a running process, with PDB symbols (hangs) |
| `recomp/recompile.py` | recompile a module to C++ in `generated/<module>/` (see [05-recompiler](05-recompiler.md)) |
| `recomp/run-tests.ps1` | regenerate, build and run the dynarmic comparison tests for each module (`-Root .`) |
