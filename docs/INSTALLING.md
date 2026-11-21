# Installing ss-delta

ss-delta runs **Soul Sacrifice Delta** natively on Windows, Linux (and the
Steam Deck), macOS on Apple Silicon, and Android. The downloads contain no
game files and no code derived from the game: the first start builds the
game on your computer or device from **your own dump** of it.

## Contents

* [What you need](#what-you-need)
* [Windows](#windows)
* [Linux and the Steam Deck](#linux-and-the-steam-deck)
* [macOS (Apple Silicon)](#macos-apple-silicon)
* [Android](#android)
* [The first start: building the game](#the-first-start-building-the-game)
* [Playing](#playing)
* [Saves](#saves)
* [Ad Hoc Play](#ad-hoc-play)
* [Files and folders](#files-and-folders)
* [Command-line options](#command-line-options)
* [Updating](#updating)
* [Uninstalling](#uninstalling)
* [Reporting a problem](#reporting-a-problem)

## What you need

| | |
|---|---|
| Windows | Windows 10 or 11, x64, a GPU with Vulkan |
| Linux | x64, glibc 2.30 or newer (any current distribution, SteamOS), a GPU with Vulkan |
| macOS | macOS 13.3 or newer on Apple Silicon (M1 and later) |
| Android | Android 9 or newer, 64-bit ARM, Vulkan; about 10 GB free while it builds ([Android](#android)) |
| Disk space | about 4 GB for the game's folder, and up to 2 GB more while it builds |
| Internet | the first start downloads the PS Vita firmware from Sony and a compiler |

**Your own copy of the game, at update 1.30**, either version:

| Version | Title ID |
|---|---|
| US | PCSA00152 |
| EU | PCSF00532 |

Any of these forms works:

* a decrypted dump (a folder, a `.zip` or a `.vpk`) with the 1.30 update,
  merged into the game or beside it as NoNpDrm dumps keep it (`app/` and
  `patch/`). For a NoNpDrm dump, give the `.zip` or the folder that holds
  both `app` and `patch`, not `patch/PCSA00152` alone (that is only the
  update), and don't unpack the update into the game's folder: its files
  replace the game's, and the game can't be installed from what is left;
* the PSN `.pkg` of the game with its licence (`work.bin` or a `.rif`, or a
  zRIF), plus the 1.30 update's `.pkg`.

The add-ons' content (raiments, hoods, additional pacts) is part of update
1.30; ss-delta unlocks it.

The **Japanese Voice-over Pack** is a separate add-on. If you have it, add
it as an add-on in the importer: the pack for your version
(`UP9000-PCSA00152_00-SSS000CVN0000001` for US,
`EP9000-PCSF00532_00-SSS000CVN0000001` for EU; the other region's pack
installs for the other version's title and isn't used), as a decrypted
dump (a NoNpDrm folder or `.zip`, with its licence as
`sce_sys/package/work.bin` or in `license/addcont/...`) or as its `.pkg`
with its licence (a `work.bin` or `.rif` beside the `.pkg` is found by
itself). Then choose it in the game: Options → Lang/Sub Settings → Voice
Language → Japanese.

**Mods made for rePatch**, such as the
[Undub patch](https://archive.org/details/soul_sacrifice_delta_undub_patch)
(Japanese voices from the very start, also without the pack), are added
the same way, as an add-on. Unpack the `.7z` and give its folder (the one
that holds `rePatch`), or a `.zip` of it. ss-delta keeps the mod beside the
game, in `fs/ux0/rePatch/`, so the game's own files stay as they are. A
mod made for one region (the undub's `PCSA00152` folder) also works with
the other region's game, with no renaming. **Mods (rePatch)** on the
settings menu's Game page (`[game] repatch` in `ss-delta.ini`) turns them
off. To remove a mod, delete its folder in `fs/ux0/rePatch/`.

Once the game is built, an add-on or a mod can be added on its own,
without building the game again (it takes seconds):

* PC: start the game with `--install` and add only the add-on in the
  importer (leave the game's rows empty), or run
  `ss-delta.exe --dump "<the pack>"`;
* Android: long-press the app's icon → **Add an add-on**, and pick it (a
  mod as a `.zip`);
* RecompLauncher: the game's setup has an Add-ons step for it.

Download the archive for your system from the
[latest release](https://github.com/vita-recomps/ss-delta/releases/latest)
(on Android, the `.apk`: see [Android](#android)).
Each archive unpacks to a folder `ss-delta`: that folder **is** the game. Keep it
wherever you like (not inside a folder that needs administrator rights, such
as `C:\Program Files`).

## Windows

1. Download `ss-delta-<version>-windows.zip` and unzip it.
2. Start `ss-delta.exe`. Windows may warn that it doesn't know the program
   (it isn't signed with a publisher's certificate): click "More info", then
   "Run anyway".
3. The importer opens: see [the first start](#the-first-start-building-the-game).
   On Windows, also tick that you accept Microsoft's licence for the C++
   runtime and Windows SDK the compiler uses (it downloads them from
   Microsoft).

The importer can put a shortcut on the desktop.

**Laptops with two GPUs** (an AMD Radeon built in and an NVIDIA card):
releases up to v0.3.0 can stop near the end of the build with "LoadLibrary
failed with error 87". Open Windows Settings → System → Display →
Graphics, add `ss-delta.exe`, set it to High performance, and build again.
Later releases ask for the NVIDIA GPU themselves.

## Linux and the Steam Deck

1. Download `ss-delta-<version>-linux.tar.gz` and unpack it (on a Steam
   Deck, in desktop mode: Dolphin can unpack it with a right-click).
2. Start `ss-delta.x86_64`: double-click it, or `./ss-delta.x86_64` in a
   terminal.
3. The importer opens: see [the first start](#the-first-start-building-the-game).
   Tick **Add the game to Steam** (Steam must be running) to play it from
   the Steam Deck's Game Mode, and the applications-menu box for a menu
   entry.

It is a Linux program, not a Windows one: no Proton or other compatibility
tool is needed. If the game didn't reach Steam, run
`./ss-delta.x86_64 --add-to-steam` with Steam running, or add
`ss-delta.desktop` from the folder with Steam's "Add a Non-Steam Game". On
the Deck the controls are a gamepad to the game, and the touchscreen is the
Vita's front touchscreen.

## macOS (Apple Silicon)

1. Download `ss-delta-<version>-macos.tar.gz` and open it (Archive Utility
   unpacks it).
2. Double-click **Soul Sacrifice Delta.app** in the folder. macOS refuses it
   the first time, as it does anything downloaded that isn't signed by a
   registered Apple developer: click Done, open System Settings > Privacy &
   Security, scroll down to "Soul Sacrifice Delta was blocked" and click
   **Open Anyway** (once).
3. The importer opens: see [the first start](#the-first-start-building-the-game).
   It can also put the game in Applications (Launchpad and Spotlight list it).

When you join or host Ad Hoc Play, macOS asks whether the game may "find and
connect to devices on your local network": allow it. In fullscreen the game
runs in macOS's Game Mode.

## Android

The game builds itself on the device from your dump: no PC needed. Made
for Snapdragon handhelds (tested on an AYN Thor: Snapdragon 8 Gen 2); the
device needs a 64-bit ARM chip, Vulkan, Android 9 or newer, about 10 GB of
free space (5 GB of it only while building) and preferably 12 GB of memory
or more.

1. Download `ss-delta-<version>-android.apk` from the release onto the
   device and install it (allow installing from your browser or file
   manager when Android asks).
2. Copy your dump to the device (for example into `Download`): the NoNpDrm
   `.zip` or `.vpk` (zip a dumped folder first), or the game's `.pkg` with
   its licence file (`work.bin` or `.rif`) and, if the dump lacks it, the
   1.30 update's `.pkg`.
3. Start **ss-delta**. Its setup screen asks for the files: **Add the
   game's files** (the dump; then the update's `.pkg` if needed) and, for
   a `.pkg`, **Add a licence**. Then **Build**.
4. The app downloads the PS Vita firmware from Sony, installs it and the
   game, runs the game for a moment to find its code, and builds the native
   code: about 15 minutes on a Snapdragon 8 Gen 2. Keep the device
   charging; you may leave the app meanwhile (a notification says when it
   is done).
5. **Play**. On a Snapdragon device the game offers Turnip, the
   open-source GPU driver that draws this game's fog correctly, the first
   time: Download.

After an app update the setup screen comes back and builds the native code
again (your dump isn't needed). The game's files live in
`Android/data/io.github.vitarecomps.ssdelta/files/` on the device
(`ss-delta.ini` there holds the settings, `setup.log` the setup's log);
uninstalling the app deletes them, saves included. Holding Select opens
the settings menu, as on PCs.

### From a PC instead

A PC that has built the game (as above) can copy it to the device too, for
a device too small or slow to build:

1. On the device, turn on **Developer options** (Settings > About device:
   tap the build number seven times), then in Developer options either
   **USB debugging** (and connect the cable), or **Wireless debugging**
   (the same Wi-Fi network as the PC).
2. On the PC, start the game with `--android` (Windows: `ss-delta.exe
   --android`, from a command prompt in the game's folder; Linux:
   `./ss-delta.x86_64 --android`; macOS:
   `"Soul Sacrifice Delta.app/Contents/MacOS/ss-delta" --android`). A
   window asks how the device is connected. Over Wi-Fi: on the device,
   Wireless debugging > **Pair device with pairing code**, and type the IP
   address, port and code it shows. Accept Google's licence for adb (the
   tool that copies the game) and click **Copy to the device**.
3. The PC builds the game's code for Android (a few minutes), downloads adb
   from Google, installs the app (`setup/android/ss-delta.apk`, also
   attached to each release) and copies the game's files (several GB:
   minutes over Wi-Fi) and code to the device.

Saves already on the device stay when you copy again. Without the window:
`--android --accept-android-sdk-license` and the device as `--serial <adb
serial>` or `--pair <ip:port> --code <code>`; `--push-only` copies again
what was built before.

## The first start: building the game

The importer's window asks for your dump:

1. **Game**: the game's folder, `.zip`, `.vpk` or `.pkg` (File... or
   Folder...). The importer looks inside a folder or archive: when it
   already holds the 1.30 update and the licence, it says so and doesn't ask
   for them.
2. **Update**: the 1.30 update, if the game's dump doesn't hold it.
3. **Licence** (for a `.pkg`): its `work.bin` or `.rif`, found beside it when
   it's there, or a zRIF typed in.
4. Add-ons are optional (their content is part of 1.30).

Then **Build**. The importer:

* downloads the PS Vita firmware from Sony and a compiler (Windows: about
  650 MB, LLVM's clang with Microsoft's C++ runtime and SDK; Linux and
  macOS: about 240 MB, zig);
* installs the game into the folder, starts it once unseen to read its code,
  translates that code to C++ and compiles it on your computer;
* deletes the downloads and its work files.

This takes a few minutes (about 6 on an M5 MacBook Air, 20 on a Steam
Deck). Then **Play** starts the game. From then on, starting the game goes
straight to it.

Without the window (for scripts and launchers):

```
ss-delta.exe --dump "<your dump>" --accept-microsoft-license      (Windows)
./ss-delta.x86_64 --dump "<your dump>"                            (Linux)
```

`--build-only` builds and quits instead of playing, and `--progress` adds
`progress <0-1> <text>` lines for a launcher's progress bar.

**RecompLauncher:** each release carries a `recomplauncher.json`, so
[RecompLauncher](https://recomplauncher.com/game/ss-delta) can install the game, build
it from the dump you pick (the same importer, without its window), show
the main settings of `ss-delta.ini` on the game's page, and back up the
saves. After an update it builds the game again from the same dump. Its
setup also takes the Japanese Voice-over Pack and a rePatch mod such as
the Undub patch (both optional, on its Add-ons step); adding one later
installs only that.

## Playing

* **Settings:** F1, or Select (Back/View) held for a second on a gamepad,
  opens the settings menu over the paused game. Everything is also in
  `ss-delta.ini`, which can be edited by hand (key bindings only there).
* **Exit:** the settings menu's last page, Exit: Cross (X on the keyboard)
  twice on Exit the game. Closing the window does the same. Progress since
  the game last saved is lost.
* **Fullscreen:** F11 or Alt+Enter (Option+Return on a Mac). On a Mac
  keyboard the F keys need fn held, unless they are set as standard function
  keys.
* **Touch:** the mouse (or trackpad) is the touchscreen: left button front,
  right button rear. The Black Rite icon (touch and hold) is also on F and on
  the gamepad's left trigger.
* **Frame rate:** 60 fps by default; `frame_rate = 30` under `[display]`
  gives the Vita's rate. Loading screens run at 30.
* **Intro logos:** Skip intro logos on the settings menu's Game page
  (`skip_intro = true` under `[game]`) skips the health warning and the
  company logos at start: the game opens on its title screen.
* **Cheats:** the settings menu's Cheats page (`[cheats]`), all off by
  default and switched while the game runs: Infinite health and Unlimited
  offerings in quests, Max Lacrima and Max levels (Life and Magic 99).
  Lacrima and levels are kept when the game saves, so export a save first
  (below) to be able to go back.
* **Language:** Language on the settings menu's Game page. The US game has
  English, French, Spanish and Portuguese (Brazil), the EU game English,
  French, Spanish, German and Italian.
* **Screenshots:** F12, into `ss-delta/screenshots`.
* **Both versions installed:** the US one starts; `--title-id PCSF00532`
  starts the EU one.

## Saves

Saves are in the game's folder, in the Vita file system:
`fs/ux0/user/00/savedata/PCSA00152` (`PCSF00532` for the EU game). The game
has three save slots.

To use a save from a Vita (decrypted, for example with VitaShell or Apollo),
or from another computer:

```
ss-delta.exe --import-save <folder or .zip> [--slot 2]
ss-delta.exe --export-save <folder> [--slot 2]
```

`--slot` picks the game's slot (default 1). An import keeps the previous
save in `ss-delta/save-backups`.

## Ad Hoc Play

Librom → Network → Ad Hoc Play works between copies of the game, as on a
Vita: one creates a room, the others use Search for Room.

* **Across computers** (Windows, Linux and macOS mixed, any of them as
  host): `network = lan` under `[multiplayer]` in `ss-delta.ini`, the default
  on Linux and macOS. On Windows set it, and allow `ss-delta.exe` through the
  firewall when Windows asks.
* **Several copies on one PC** (Windows and Linux): `network = local`, the
  default on Windows; start `run-player2.bat` (`run-player2.sh`) or
  `--player 2` up to `--player 4`. Each player has its own saves, copied from
  player 1's on its first start, and its own log and settings
  (`ss-delta-player<N>.ini` overrides `ss-delta.ini` for that player).
  `gamepad = 1`–`4` gives each copy a gamepad of its own.

## Files and folders

Everything the game uses is in its folder; nothing is written anywhere else
(apart from the shortcut, menu entry, Steam entry or Applications copy, if you
let the importer make one).

| In the game's folder | What |
|---|---|
| `ss-delta.exe`, `ss-delta.x86_64`, `Soul Sacrifice Delta.app` | the game: the one thing to start |
| `ss-delta.ini` | settings |
| `fs/` | the Vita file system: the installed game, the firmware, your saves |
| `ssd_aot_*.dll` / `.so` / `.dylib` | the game's code, compiled for your computer |
| `ss-delta/` | logs (`vita3k.log`, the importer's `setup.log`), save backups, screenshots, per-player data |
| `cache/` | the shader cache |
| `patch/` | Vita3K-style patches, if you add any |
| `setup/` | the importer (its Python and the recompiler kit), kept for `--install` |
| `data/`, `shaders-builtin/`, `icons/` | files from Vita3K the game reads |

Everything in `fs/`, `ssd_aot_*` and `cache/` is derived from your copy of the
game: don't share it.

## Command-line options

`--help` prints these and every setting of `ss-delta.ini`.

| Option | What |
|---|---|
| `--game <folder>` | play the game in that folder (default: the program's own) |
| `--install` | open the importer again (another dump, an update), then play |
| `--dump <file> [--license <work.bin\|.rif> \| --zrif <zRIF>]` | build from this dump without the window (repeat for the update and add-ons; also `--dump=<file>`), then play. A `.pkg` takes the licence beside it. With the game built, add-ons alone are installed without building again |
| `--build-only` | build if needed (or with `--install` / `--dump`), then quit |
| `--accept-microsoft-license` | Windows, with `--dump`: accept Microsoft's licence for the compiler's runtime and SDK |
| `--shortcut`, `--steam` | with `--dump`: a desktop shortcut, menu entry or Applications copy; add the game to Steam (Linux) |
| `--cache <folder>`, `--jobs <n>` | with `--dump`: keep the downloads there for next time; compile with n jobs |
| `--progress` | with `--dump`: also `progress <0-1> <text>` lines, for a launcher (RecompLauncher) |
| `--add-to-steam` | Linux, Steam Deck: add the game to Steam (Steam running), then quit |
| `--android` | put the game, built here, on an Android device (a window asks how it's connected), then quit; with `--dump`, build for both first |
| `--serial <s>`, `--pair <ip:port> --code <code>`, `--connect <ip:port>` | with `--android`: the device, without the window |
| `--accept-android-sdk-license`, `--push-only`, `--apk <file>` | with `--android`: accept Google's licence for adb; copy again without building; another APK |
| `--set <section.key=value>` | a setting of `ss-delta.ini` for this run only |
| `--fullscreen`, `--windowed` | the same as `--set display.fullscreen=true` / `false` |
| `--player <1-4>` | Ad Hoc Play: another player's copy |
| `--title-id <id>` | with both versions installed: that one |
| `--import-save <folder\|zip>`, `--export-save <folder>`, `--slot <1-3>` | saves, then quit |
| `--write-ini <file>` | write the default settings file there, then quit |

On macOS the program inside the app takes them:
`"Soul Sacrifice Delta.app/Contents/MacOS/ss-delta" --help`.

## Updating

To move to a newer release, unpack it over your game's folder (replace the
files), then start the game with `--install` and build again from the same
dump: saves and settings are kept. Coming from a release before 0.3.0 (a
separate setup and playable folder): build the new release, then copy the
old folder's `fs/ux0/user/00/savedata/PCSA00152` (or `PCSF00532`) and
`ss-delta.ini` into the new one.

## Uninstalling

Delete the game's folder. If you let the importer make them, also delete the
desktop shortcut (Windows), the menu entry and the Steam entry (Linux), or the
copy in Applications (macOS).

## Reporting a problem

Open an [issue](https://github.com/vita-recomps/ss-delta/issues) with your
system, the release, what you did and what happened. Attach the log,
`ss-delta/vita3k.log` in the game's folder (if the build from your dump
failed, `ss-delta/setup.log`). Never attach game files, saves you don't want public, or
anything from `fs/`.
