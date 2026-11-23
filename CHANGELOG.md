# Changelog

The changes in each release of ss-delta. The downloads and each release's
full notes are on the [releases page](https://github.com/vita-recomps/ss-delta/releases);
[INSTALLING](docs/INSTALLING.md#updating) explains how to update.

## Unreleased

### New

* **The original game's Spirits' offerings**
  ([#11](https://github.com/vita-recomps/ss-delta/issues/11)): the 20
  pre-order offerings of the first *Soul Sacrifice* (Spirits' Flamepike
  ... Spirits' Gravelshield). Delta still has them, switched off; ss-delta
  switches them on and gives each once per save, with Add-ons (DLC) on
  (`[game] spirits_offerings`, on by default). They look and play like
  Delta's own offerings of the same kind. No copy of the original is
  needed. See [INSTALLING](docs/INSTALLING.md).

* **PS TV controls** ([#12](https://github.com/vita-recomps/ss-delta/issues/12)):
  `[game] pstv_mode` (the settings menu's Game page) runs the game as a
  PlayStation TV, which has no touchscreen. The one touch the story
  needs, pulling Librom out of the bones at the start of a new game, then
  takes L2 or R2 (the gamepad's triggers, U and O on the keyboard). AR
  mode and "near" are unavailable then.

* **All eight Blank Page slots**
  ([#15](https://github.com/vita-recomps/ss-delta/issues/15)): Librom's
  Blank Page has eight slots for created pact pages, and only three are
  open. The other five were unlocked with Memory Clods, bought on the
  PlayStation Store. With Add-ons (DLC) on, ss-delta now unlocks them in
  the loaded save, and the game keeps them when it saves.

### Fixed

* **Blitz offerings at 60 fps**
  ([#14](https://github.com/vita-recomps/ss-delta/issues/14)): after a hit,
  a Blitz offering's push-back moved the caster a fixed step every frame,
  so at 60 fps it threw you almost twice as far as on the Vita and the
  next cast of a chain fell short. The steps now follow the frame time, so
  60 fps plays like 30.
* **Loading screens run at 60 fps.** The quest-start loading screen could
  hang at 60 fps, so loading screens were kept at 30 (`frame_rate`). The
  hang was a race in the game: the loader can finish before the screen's
  opening animation ends, and its looping animation then never stops. This
  is fixed in the recompiled code, so loading screens now run at the set
  rate. A game built before this update still loads at 30 until it is
  built again.
* **Games copied straight off a Vita**
  ([#13](https://github.com/vita-recomps/ss-delta/issues/13)): their
  folders carry the PSN account's own licence, usable only on that Vita,
  and the setup stopped with "header signature is invalid". It now says
  what is wrong before its downloads, takes the NoNpDrm licence in the
  dump's `license/` folder in place of that licence, and uses a licence
  given with a folder or `.zip` (it used to be ignored). See
  [INSTALLING](docs/INSTALLING.md#what-you-need), "From your own Vita".
* **Linux and the Steam Deck: the update in the same folder as the game
  could be left out** (#13). The game and its update were installed in the
  order the file system lists them, and on Linux the update could come
  first and fail; the setup then stopped with "eboot.bin is not a build
  this port supports" (the game's 1.00). The game is now always installed
  first, and the setup says when the update is missing.
* A folder whose game failed to install while something else in it
  installed counted as installed; the setup then stopped with "no
  PCSA00152 or PCSF00532 ... after installing" instead of the reason.
* Removing a packaged mod that had added a table the game's patch archive
  lacks left a copy of the archive in `fs/ux0/rePatch/`; it is deleted now.

## 0.4.3 (2026-11-22)

### Fixed

* **The setup refused dumps decrypted by an older Vita3K**
  ([#9](https://github.com/vita-recomps/ss-delta/issues/9)): "eboot.bin is
  not a build this port supports". Vita3K versions before December 2024
  decrypted the game's files when they installed it, and folders copied out
  of such an install (often named "[vita3k]") hold those decrypted files.
  They are the same 1.30 game, US or EU, and are now accepted.

## 0.4.2 (2026-11-22)

### New

* **The add-ons PSN gave as gifts are unlocked too**
  ([#11](https://github.com/vita-recomps/ss-delta/issues/11)): the
  Soulbinder, Fox (the gift "Necky"), Slave, Great Seer ("Archsorcerer"),
  Mad Witch, Easterner, Disciple ("Saint"), Beast and White Cat raiments,
  eight hoods (Fox Hood, Demon's Horns, Golden Mask, Mind's Eyewear,
  Wizard's Hat, Magic Helm, Polytan Hood, Possessed Mask) and the Fox
  Sigil. On the Vita they came from the Claim Gift page at Cassus, which
  needs PSN; now they appear in your save, marked NEW, with `[game] dlc`
  on (the default). See them all in the [gallery](docs/GALLERY.md).
* **The raiments only Japan had**: Sylvan and Benkei, both in the game's
  data (`[game] japan_raiments`, on by default; Japan-only raiments in the
  settings menu).
* **The original game's raiments**, ARKS Armor and Dragonslayer, as a mod
  you make from your own copy of the first *Soul Sacrifice* (1.30):
  `tools/og-raiments.py` in the repository makes it, a 1.4 MB `.zip`, and
  installs it ([INSTALLING](docs/INSTALLING.md#what-you-need)).
* **Packaged mods**: a `.zip` with an `ss-delta-mod.json` is added like
  any mod (the importer, `--dump`, Android's Add an add-on), but merged
  into the game's archive instead of replacing it, so it works with the
  Undub installed before or after it. `--remove-mod <id>` takes it out
  again.
* **The logs of the last five runs are kept**: `ss-delta/vita3k.log` is
  the latest, `vita3k.1.log` to `vita3k.4.log` the runs before it. A
  report sent after the game was started again (RecompLauncher sends the
  whole log folder) still carries the run that crashed.

## 0.4.1 (2026-11-21)

### Fixed

* **Windows: the setup stopped with "msiexec failed (1639)"** when the
  temp folder's path has a space, as under a Windows user name with a
  space. Windows Installer refused the folder the setup unpacks the Windows
  SDK into. One cause of
  [#9](https://github.com/vita-recomps/ss-delta/issues/9), possibly not the
  only one. Linux, macOS and Android are the same as 0.4.0.

## 0.4.0 (2026-11-21)

### New

* **Android:** an APK for Android 9 or newer on 64-bit ARM with Vulkan, made
  for Snapdragon handhelds (tested on an AYN Thor). Its setup screen builds
  the game on the device from your dump, with no PC: it downloads the
  firmware from Sony and compiles the native code with its own compiler, in
  about 15 minutes on a Snapdragon 8 Gen 2. After an app update it builds
  again by itself, without asking for the dump. On Adreno GPUs it offers to
  download Turnip. It has on-screen controls for phones without a gamepad,
  with a LOCK toggle for the lock-on. `ss-delta.exe --android` puts a game
  built on a PC on a device. The APK is signed with the project's release
  key, so later versions install over it.
* **Cheats** ([#7](https://github.com/vita-recomps/ss-delta/issues/7)) on
  every platform, on the settings menu's Cheats page: Infinite health,
  Unlimited offerings, Lasting offerings, One-hit kills, Max Lacrima and Max
  levels.
* **The Japanese Voice-over Pack**
  ([#8](https://github.com/vita-recomps/ss-delta/issues/8)), the game's
  separate PSN add-on, installs as an add-on. Once the game is built, an
  add-on goes in on its own without building again: `--dump`, the
  importer, **Add an add-on** on Android, or RecompLauncher's Add-ons step.
* **rePatch mods, such as the Undub patch**
  ([#8](https://github.com/vita-recomps/ss-delta/issues/8)), for Japanese
  voices from the start. They are kept beside the game, and **Mods
  (rePatch)** on the settings menu turns them off.
* **Xbox button labels** in the game's prompts, tutorial pictures and text
  (Button prompts), following your gamepad bindings.
* **Mouse camera** on Windows, Linux and macOS: Tab or a middle click
  captures the cursor and the mouse turns the camera (the Mouse page:
  Sensitivity, Invert vertical).
* **Skip intro logos**
  ([#6](https://github.com/vita-recomps/ss-delta/issues/6)), off by
  default: the game opens on its title screen after about 6 seconds instead
  of 20.

### Fixed

* A dump that holds only the 1.30 update
  ([#5](https://github.com/vita-recomps/ss-delta/issues/5)): the setup
  now stops before the downloads and says what to give it, instead of
  failing at the end with "Install app before patch".
* The settings menu's page names ran into each other in its tab bar.
* The settings menu froze when opened over one of the system's dialogs
  (the save list, "Do you want to load this saved data?").

## 0.3.1 (2026-11-19)

### New

* **RecompLauncher:** every release carries a `recomplauncher.json`, so
  [RecompLauncher](https://recomplauncher.com) can install the game, build
  it from your dump, show its main settings, back up the saves and rebuild
  after an update.
* **Exit from a gamepad:** the settings menu's last page, Exit.
* **`--progress`:** progress lines while building, for a launcher's
  progress bar.

### Fixed

* Laptops with an AMD and an NVIDIA GPU
  ([#4](https://github.com/vita-recomps/ss-delta/issues/4)): the build
  could stop near the end with "LoadLibrary failed with error 87". The
  game asks for the dedicated GPU again.

## 0.3.0 (2026-11-18)

### New

* **Linux and the Steam Deck:** a native `ss-delta.x86_64`, built in the
  Steam Runtime SDK; the importer can add the game to Steam. Quests run at
  60 fps on the Deck.
* **macOS on Apple Silicon:** a native app on Metal (MoltenVK), at 60 fps
  on all 50 quest maps; Game Mode in fullscreen.
* **Ad Hoc Play across platforms:** Windows, Linux and macOS copies play
  together over a LAN, with any of them as host.
* **One program, one folder:** the download is the game's folder. It
  builds itself from your dump the first time it starts, and keeps
  everything inside its folder (the separate setup of 0.1 and 0.2 is gone).
* **A command line for everything:** `--dump`, `--install`, `--build-only`,
  `--game`, `--add-to-steam`, `--fullscreen`/`--windowed`, `--set`.
* The importer reads your dump and doesn't ask again for what it already
  holds (the 1.30 update, the licence).

### Fixed

* Keyboard diagonals ran about 1.4 times as fast as straight movement.
* A room hosted over Wi-Fi (a Steam Deck or a Mac) couldn't be joined.
* Linux and macOS: "A network error has occurred" after leaving a room,
  and menus that stopped responding on macOS.
* Windows: downloads failed on PCs where Python couldn't check a server's
  certificate.

## 0.2.1 (2026-11-17)

### New

* **Language setting**
  ([#3](https://github.com/vita-recomps/ss-delta/issues/3)) on the
  settings menu's Game page: English, French, Spanish and Portuguese
  (Brazil) in the US game; English, French, Spanish, German and Italian in
  the EU game.

## 0.2.0 (2026-11-17)

### New

* **The EU version**
  ([#2](https://github.com/vita-recomps/ss-delta/issues/2)), PCSF00532
  at update 1.30. It is the same build as the US game, so the same
  recompiled code serves both.

## 0.1.0 (2026-11-16)

The first release
([#1](https://github.com/vita-recomps/ss-delta/issues/1)), for Windows: a
setup (`setup.bat`) that builds a playable folder from your own dump of
the US game (PCSA00152, update 1.30).

* The game's code, and the firmware modules it loads, recompiled ahead of
  time to C++ and run natively, without a JIT.
* 60 fps with the game's speed kept, and the 3D at full resolution
  (960×544 times the resolution multiplier).
* Rendering fixes, among them the white floors on NVIDIA GPUs.
* Ad Hoc Play for up to four copies, on one PC or across a LAN.
* The add-ons' content unlocked.
* An in-game settings menu, a commented `ss-delta.ini`, and Vita saves
  imported and exported.
